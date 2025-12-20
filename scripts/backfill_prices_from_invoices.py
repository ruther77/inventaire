#!/usr/bin/env python3
"""
Backfill product prices from historical invoices.

This script:
1. Reads all stored invoice PDFs from data/processed_invoices/
2. Parses each invoice to extract product lines
3. Matches products by name using fuzzy matching
4. Updates produits.prix_achat and creates price history

Usage:
    python scripts/backfill_prices_from_invoices.py [--dry-run] [--limit N]
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import text

from core.data_repository import get_engine, query_df, exec_sql
from core.parsers import parse_invoice
from core.inventory_service import find_similar_products
from core.price_history_service import record_price_history

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
LOGGER = logging.getLogger(__name__)

INVOICE_DIR = PROJECT_ROOT / "data" / "processed_invoices"


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text content from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader  # type: ignore

    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)


def detect_supplier_from_filename(filename: str) -> str:
    """Detect supplier from filename pattern."""
    name_lower = filename.lower()
    if "euro" in name_lower or "eurociel" in name_lower:
        return "EUROCIEL"
    if "metro" in name_lower or "inv-" in name_lower:
        return "METRO"
    if "taiyat" in name_lower or "tai" in name_lower:
        return "TAIYAT"
    return "Inconnu"


def normalize_product_name(name: str) -> str:
    """Normalize product name for better matching."""
    import re
    import unicodedata

    # Normalize unicode accents
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = name.upper().strip()

    # Remove common non-essential words
    remove_words = [
        r'\bSENEGAL[EA]?\b', r'\bVIETNAM\b', r'\bCHILI\b', r'\bMEXIQUE\b',
        r'\bPORTUGAL\b', r'\bMARO[CQ]\b', r'\bINDO\b', r'\bNZ\b', r'\bCHINE\b',
        r'\bTHAILANDE\b', r'\bINDONESIE\b', r'\bESPAGNE\b', r'\bFRANCE\b',
        r'\bG&V\b', r'\bG V\b', r'\bENTIER\b', r'\bFILET\b',
        r'\bIKAGEL\b', r'\bRING\b', r'\bPROMO\b', r'\bBIO\b',
        r'\bS/TETE\b', r'\bROSE\b',
        r'\*PROMO\*', r'\*',
        r'\s+-\s+',
    ]

    for pattern in remove_words:
        name = re.sub(pattern, ' ', name, flags=re.IGNORECASE)

    # Standardize weight format
    name = re.sub(r'(\d+)\s*KG', r'\1KG', name)
    name = re.sub(r'(\d+)\s*G\b', r'\1G', name)
    name = re.sub(r'-\s*(\d+KG)', r' \1', name)

    # Remove extra whitespace
    name = ' '.join(name.split())

    return name


def extract_core_product(name: str) -> str:
    """Extract just the core product name without sizes/weights."""
    import re

    name = normalize_product_name(name)

    # Remove size ranges and weights
    name = re.sub(r'\d+[.,]?\d*/\d+[.,]?\d*', '', name)
    name = re.sub(r'\d+KG', '', name)
    name = re.sub(r'\d+G\b', '', name)
    name = re.sub(r'\d+X\d+[KG]?', '', name)

    words = name.split()
    if words:
        return words[0]
    return name


def match_products_by_name(
    invoice_df: pd.DataFrame,
    tenant_id: int = 1,
    min_similarity: float = 0.5,
) -> pd.DataFrame:
    """Match invoice lines to products using fuzzy name matching with normalization."""
    if invoice_df.empty or "nom" not in invoice_df.columns:
        return invoice_df

    result = invoice_df.copy()
    result["matched_produit_id"] = None
    result["matched_produit_nom"] = None
    result["match_score"] = None

    for idx, row in result.iterrows():
        nom = row.get("nom")
        if not nom or not str(nom).strip():
            continue

        nom_str = str(nom)
        match_found = False

        # Try normalized name first
        normalized = normalize_product_name(nom_str)
        if normalized:
            suggestions = find_similar_products(
                normalized,
                tenant_id=tenant_id,
                max_results=1,
                min_similarity=min_similarity,
            )
            if suggestions:
                best = suggestions[0]
                result.at[idx, "matched_produit_id"] = best["produit_id"]
                result.at[idx, "matched_produit_nom"] = best["produit_nom"]
                result.at[idx, "match_score"] = best["similarity_score"]
                match_found = True

        # Try core product name if no match
        if not match_found:
            core = extract_core_product(nom_str)
            if core and len(core) >= 4:
                suggestions = find_similar_products(
                    core,
                    tenant_id=tenant_id,
                    max_results=5,
                    min_similarity=0.4,
                )
                if suggestions:
                    for s in suggestions:
                        if core.lower() in s["produit_nom"].lower():
                            result.at[idx, "matched_produit_id"] = s["produit_id"]
                            result.at[idx, "matched_produit_nom"] = s["produit_nom"]
                            result.at[idx, "match_score"] = s["similarity_score"]
                            match_found = True
                            break
                    if not match_found:
                        best = suggestions[0]
                        result.at[idx, "matched_produit_id"] = best["produit_id"]
                        result.at[idx, "matched_produit_nom"] = best["produit_nom"]
                        result.at[idx, "match_score"] = best["similarity_score"]

    return result


def update_product_price(
    produit_id: int,
    new_price: float,
    invoice_date: str | None,
    supplier: str,
    tenant_id: int = 1,
    dry_run: bool = False,
) -> bool:
    """Update product prix_achat if the new price is higher."""
    if new_price <= 0:
        return False

    # Get current price
    df = query_df(
        text("SELECT prix_achat FROM produits WHERE id = :id AND tenant_id = :tenant"),
        {"id": produit_id, "tenant": tenant_id}
    )

    if df.empty:
        return False

    current_price = float(df.iloc[0]["prix_achat"] or 0)

    # Only update if new price is higher (inflation logic)
    if new_price <= current_price:
        return False

    if dry_run:
        LOGGER.info(f"  [DRY-RUN] Would update produit {produit_id}: {current_price:.2f} -> {new_price:.2f}")
        return True

    # Update the price
    exec_sql(
        text("""
            UPDATE produits
            SET prix_achat = :price, updated_at = now()
            WHERE id = :id AND tenant_id = :tenant
        """),
        {"id": produit_id, "price": new_price, "tenant": tenant_id}
    )

    # Record price history
    try:
        exec_sql(
            text("""
                INSERT INTO produits_price_history (produit_id, prix_achat, facture_date, source)
                VALUES (:produit_id, :prix, :facture_date, :source)
            """),
            {
                "produit_id": produit_id,
                "prix": new_price,
                "facture_date": invoice_date,
                "source": f"Backfill from {supplier}",
            }
        )
    except Exception as e:
        LOGGER.warning(f"Could not record price history: {e}")

    LOGGER.info(f"  Updated produit {produit_id}: {current_price:.2f} -> {new_price:.2f}")
    return True


def process_invoice_pdf(
    pdf_path: Path,
    tenant_id: int = 1,
    dry_run: bool = False,
) -> dict:
    """Process a single invoice PDF and update product prices."""
    stats = {
        "lines_parsed": 0,
        "lines_matched": 0,
        "prices_updated": 0,
        "errors": [],
    }

    LOGGER.info(f"Processing: {pdf_path.name}")

    try:
        # Extract text
        text_content = extract_text_from_pdf(pdf_path)
        if not text_content.strip():
            stats["errors"].append("Empty PDF content")
            return stats

        # Detect supplier
        supplier = detect_supplier_from_filename(pdf_path.name)

        # Parse invoice
        invoice_df = parse_invoice(
            text_content,
            supplier_hint=supplier,
            margin_rate=0.4,
            start_sequence=0,
        )
        if invoice_df.empty:
            stats["errors"].append("No lines parsed")
            return stats

        stats["lines_parsed"] = len(invoice_df)

        # Match products by name
        matched_df = match_products_by_name(invoice_df, tenant_id=tenant_id)

        # Count matches
        has_match = matched_df["matched_produit_id"].notna()
        stats["lines_matched"] = has_match.sum()

        # Extract invoice date
        invoice_date = None
        if "facture_date" in matched_df.columns:
            dates = matched_df["facture_date"].dropna()
            if not dates.empty:
                invoice_date = str(dates.iloc[0])

        # Update prices for matched products
        for idx, row in matched_df[has_match].iterrows():
            produit_id = int(row["matched_produit_id"])
            prix_achat = float(row.get("prix_achat") or 0)

            if update_product_price(
                produit_id=produit_id,
                new_price=prix_achat,
                invoice_date=invoice_date,
                supplier=supplier,
                tenant_id=tenant_id,
                dry_run=dry_run,
            ):
                stats["prices_updated"] += 1

    except Exception as e:
        stats["errors"].append(str(e))
        LOGGER.error(f"Error processing {pdf_path.name}: {e}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Backfill prices from invoices")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually update")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of PDFs to process")
    parser.add_argument("--tenant", type=int, default=1, help="Tenant ID")
    parser.add_argument("--supplier", type=str, default=None, help="Filter by supplier (METRO, EUROCIEL, TAIYAT)")
    args = parser.parse_args()

    if not INVOICE_DIR.exists():
        LOGGER.error(f"Invoice directory not found: {INVOICE_DIR}")
        sys.exit(1)

    # List all PDFs
    pdf_files = sorted(INVOICE_DIR.glob("*.pdf"))
    LOGGER.info(f"Found {len(pdf_files)} PDF files")

    # Filter by supplier if specified
    if args.supplier:
        supplier_lower = args.supplier.lower()
        if supplier_lower == "metro":
            pdf_files = [f for f in pdf_files if "inv-" in f.name.lower()]
        elif supplier_lower == "eurociel":
            pdf_files = [f for f in pdf_files if "euro" in f.name.lower()]
        elif supplier_lower == "taiyat":
            pdf_files = [f for f in pdf_files if "taiyat" in f.name.lower() or "tai" in f.name.lower()]
        LOGGER.info(f"Filtered to {len(pdf_files)} PDFs for supplier {args.supplier}")

    # Apply limit
    if args.limit > 0:
        pdf_files = pdf_files[:args.limit]
        LOGGER.info(f"Limited to {len(pdf_files)} PDFs")

    # Process each PDF
    total_stats = {
        "pdfs_processed": 0,
        "lines_parsed": 0,
        "lines_matched": 0,
        "prices_updated": 0,
        "errors": 0,
    }

    for pdf_path in pdf_files:
        stats = process_invoice_pdf(pdf_path, tenant_id=args.tenant, dry_run=args.dry_run)
        total_stats["pdfs_processed"] += 1
        total_stats["lines_parsed"] += stats["lines_parsed"]
        total_stats["lines_matched"] += stats["lines_matched"]
        total_stats["prices_updated"] += stats["prices_updated"]
        total_stats["errors"] += len(stats["errors"])

    # Summary
    LOGGER.info("=" * 50)
    LOGGER.info("BACKFILL SUMMARY")
    LOGGER.info("=" * 50)
    LOGGER.info(f"PDFs processed: {total_stats['pdfs_processed']}")
    LOGGER.info(f"Lines parsed: {total_stats['lines_parsed']}")
    LOGGER.info(f"Lines matched: {total_stats['lines_matched']} ({total_stats['lines_matched']/max(1,total_stats['lines_parsed'])*100:.1f}%)")
    LOGGER.info(f"Prices updated: {total_stats['prices_updated']}")
    LOGGER.info(f"Errors: {total_stats['errors']}")

    if args.dry_run:
        LOGGER.info("\n[DRY-RUN MODE] No actual updates were made.")


if __name__ == "__main__":
    main()
