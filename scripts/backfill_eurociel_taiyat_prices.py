#!/usr/bin/env python3
"""
Backfill product prices from EUROCIEL and TAIYAT invoice PDFs.

This script:
1. Reads PDFs from EUROCIEL/ and TAIYAT/ folders
2. Parses each invoice to extract product lines
3. Matches products by name using fuzzy matching
4. Updates produits.prix_achat for matched products

Usage:
    python scripts/backfill_eurociel_taiyat_prices.py [--dry-run] [--supplier EUROCIEL|TAIYAT]
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import text

from core.data_repository import get_engine, query_df, exec_sql
from core.parsers import parse_invoice
from core.inventory_service import find_similar_products

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
LOGGER = logging.getLogger(__name__)

EUROCIEL_DIR = PROJECT_ROOT / "EUROCIEL"
TAIYAT_DIR = PROJECT_ROOT / "TAIYAT"


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text content from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader

    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)


def normalize_product_name(name: str) -> str:
    """Normalize product name for better matching.

    Removes extra details like origin (SENEGALE, VIETNAM),
    processing (G&V, ENTIER), and brand names (IKAGEL, RING).
    """
    import re
    import unicodedata

    # First normalize unicode accents
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = name.upper().strip()

    # Remove common non-essential words (origins, processing, brands)
    remove_words = [
        r'\bSENEGAL[EA]?\b', r'\bVIETNAM\b', r'\bCHILI\b', r'\bMEXIQUE\b',
        r'\bPORTUGAL\b', r'\bMARO[CQ]\b', r'\bINDO\b', r'\bNZ\b',
        r'\bG&V\b', r'\bG V\b', r'\bENTIER\b', r'\bFILET\b',
        r'\bIKAGEL\b', r'\bRING\b', r'\bPROMO\b',
        r'\bS/TETE\b', r'\bROSE\b',
        r'\*PROMO\*', r'\*',
        r'\s+-\s+',  # standalone dashes
    ]

    for pattern in remove_words:
        name = re.sub(pattern, ' ', name, flags=re.IGNORECASE)

    # Standardize size format: "300/500" stays as is
    # Standardize weight format: "10KG" or "10 KG" -> "10KG"
    name = re.sub(r'(\d+)\s*KG', r'\1KG', name)
    name = re.sub(r'-\s*(\d+KG)', r' \1', name)  # "- 10KG" -> " 10KG"

    # Remove extra whitespace
    name = ' '.join(name.split())

    return name


def extract_core_product(name: str) -> str:
    """Extract just the core product name without sizes/weights.

    E.g., 'BARRACUDA ENTIER 500/1000 - 10Kg' -> 'BARRACUDA'
    """
    import re

    name = normalize_product_name(name)

    # Remove size ranges like "500/1000" or "2.5/3"
    name = re.sub(r'\d+[.,]?\d*/\d+[.,]?\d*', '', name)

    # Remove weights like "10KG"
    name = re.sub(r'\d+KG', '', name)

    # Remove dimensions like "12X1KG" or "20X500G"
    name = re.sub(r'\d+X\d+[KG]?', '', name)

    # Get first word (the main product type)
    words = name.split()
    if words:
        return words[0]

    return name


def match_product_by_name(
    product_name: str,
    tenant_id: int = 1,
    min_similarity: float = 0.5,
) -> dict | None:
    """Match a product by name and return the best match.

    Uses multi-pass matching:
    1. First try with normalized name (removes origin, processing details)
    2. If no match, try core product name only (e.g., just 'BARRACUDA')
    3. Fallback to original name
    """
    if not product_name or not product_name.strip():
        return None

    # First try with normalized name
    normalized = normalize_product_name(product_name)
    if normalized:
        suggestions = find_similar_products(
            normalized,
            tenant_id=tenant_id,
            max_results=1,
            min_similarity=min_similarity,
        )
        if suggestions:
            return suggestions[0]

    # Try with core product name only (lower threshold since less specific)
    core = extract_core_product(product_name)
    if core and len(core) >= 4:
        suggestions = find_similar_products(
            core,
            tenant_id=tenant_id,
            max_results=5,
            min_similarity=0.4,
        )
        if suggestions:
            # Find the best match that contains the core name
            for s in suggestions:
                if core.lower() in s["produit_nom"].lower():
                    return s
            # Otherwise return the top match
            return suggestions[0]

    # Fallback to original name
    suggestions = find_similar_products(
        product_name,
        tenant_id=tenant_id,
        max_results=1,
        min_similarity=min_similarity,
    )

    return suggestions[0] if suggestions else None


def update_product_price(
    produit_id: int,
    new_price: float,
    supplier: str,
    tenant_id: int = 1,
    dry_run: bool = False,
) -> bool:
    """Update product prix_achat."""
    if new_price <= 0:
        return False

    # Get current price
    df = query_df(
        text("SELECT nom, prix_achat FROM produits WHERE id = :id AND tenant_id = :tenant"),
        {"id": produit_id, "tenant": tenant_id}
    )

    if df.empty:
        return False

    current_price = float(df.iloc[0]["prix_achat"] or 0)
    product_name = df.iloc[0]["nom"]

    # Only update if new price is different (tolerance 0.01)
    if abs(new_price - current_price) < 0.01:
        return False

    if dry_run:
        LOGGER.info(f"  [DRY-RUN] {product_name}: {current_price:.2f} -> {new_price:.2f}")
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
                VALUES (:produit_id, :prix, CURRENT_DATE, :source)
            """),
            {
                "produit_id": produit_id,
                "prix": new_price,
                "source": f"Backfill {supplier}",
            }
        )
    except Exception as e:
        LOGGER.warning(f"Could not record price history: {e}")

    LOGGER.info(f"  Updated {product_name}: {current_price:.2f} -> {new_price:.2f}")
    return True


def parse_eurociel_text(text_content: str) -> list[dict]:
    """Parse EUROCIEL invoice text to extract products with prices."""
    import re

    lines = []

    # Pattern for EUROCIEL product lines:
    # code  product_name  price  unit
    # Example: 10151  BARRACUDA 700/1000 10KG  45.50  KG

    patterns = [
        # Pattern 1: code + name + price
        r'(\d{5})\s+([A-Z][A-Z0-9\s/\-\+\.]+?)\s+(\d+[.,]\d{2})\s*(?:€|EUR)?',
        # Pattern 2: name + qty + price (no code)
        r'([A-Z][A-Z\s]+(?:\d+[/\-]\d+)?(?:\s+\d+KG)?)\s+\d+\s+(\d+[.,]\d{2})',
    ]

    for line in text_content.split('\n'):
        line = line.strip()
        if not line or len(line) < 10:
            continue

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    # Extract name and price
                    if len(groups) == 3:  # code + name + price
                        name = groups[1].strip()
                        price_str = groups[2]
                    else:  # name + price
                        name = groups[0].strip()
                        price_str = groups[1]

                    # Clean price
                    price = float(price_str.replace(',', '.'))

                    if price > 0 and len(name) > 3:
                        lines.append({
                            "nom": name,
                            "prix_achat": price,
                        })
                break

    return lines


def parse_taiyat_tarif(text_content: str) -> list[dict]:
    """Parse TAIYAT tarif list to extract products with prices."""
    import re

    lines = []

    # TAIYAT formats:
    # 1. Simple: "PRODUCT NAME  12.50"
    # 2. Qty + name + origin + prices: "1 Banku Mix 24x1kg 1 GHA 82.50 Co"
    # 3. Complex: "1 Gari du Togo N1 12x1kg Number One 1 TOGO 21.04 1 c 22.200 22.20 1"

    for line in text_content.split('\n'):
        line = line.strip()
        if not line or len(line) < 5:
            continue

        # Skip non-product lines
        if any(skip in line.upper() for skip in ['TOTAL', 'TVA', 'HT', 'TTC', 'FACTURE', 'DATE', 'PAGE', 'PRIX']):
            continue

        # Pattern 1: Complex format - qty + name + origin + price
        # "1 Banku Mix 24x1kg 1 GHA 82.50 Co"
        match = re.search(r'^\d+\s+(.+?)\s+\d*\s*[A-Z]{2,3}\s+(\d+[.,]\d{2})\s*(?:Co|co)?', line)
        if match:
            name = match.group(1).strip()
            price_str = match.group(2)
            price = float(price_str.replace(',', '.'))
            if price > 0 and len(name) > 3:
                lines.append({"nom": name, "prix_achat": price})
                continue

        # Pattern 2: Format with multiple prices - take the first one after product name
        # "1 Gari du Togo N1 12x1kg Number One 1 TOGO 21.04 1 c 22.200 22.20 1"
        match = re.search(r'^\d+\s+(.+?)\s+\d+\s+[A-Z\-]+\s+(\d+[.,]\d{2})', line)
        if match:
            name = match.group(1).strip()
            price_str = match.group(2)
            price = float(price_str.replace(',', '.'))
            if price > 0 and len(name) > 3:
                lines.append({"nom": name, "prix_achat": price})
                continue

        # Pattern 3: Simple format - text followed by price at end
        match = re.search(r'^(.+?)\s+(\d+[.,]\d{2})\s*(?:€|EUR|TTC)?$', line)
        if match:
            name = match.group(1).strip()
            price_str = match.group(2)
            price = float(price_str.replace(',', '.'))
            if price > 0 and len(name) > 3:
                lines.append({"nom": name, "prix_achat": price})

    return lines


def process_eurociel_folder(
    tenant_id: int = 1,
    dry_run: bool = False,
    min_similarity: float = 0.5,
) -> dict:
    """Process all PDFs in EUROCIEL folder."""
    stats = {
        "files_processed": 0,
        "lines_parsed": 0,
        "lines_matched": 0,
        "prices_updated": 0,
    }

    if not EUROCIEL_DIR.exists():
        LOGGER.warning(f"EUROCIEL folder not found: {EUROCIEL_DIR}")
        return stats

    pdf_files = list(EUROCIEL_DIR.glob("*.pdf"))
    LOGGER.info(f"Found {len(pdf_files)} EUROCIEL PDFs")

    for pdf_path in pdf_files:
        # Skip catalogue (too large, different format)
        if "catalogue" in pdf_path.name.lower():
            LOGGER.info(f"Skipping catalogue: {pdf_path.name}")
            continue

        LOGGER.info(f"Processing: {pdf_path.name}")
        stats["files_processed"] += 1

        try:
            text_content = extract_text_from_pdf(pdf_path)

            # Try standard parser first
            try:
                invoice_df = parse_invoice(
                    text_content,
                    supplier_hint="EUROCIEL",
                    margin_rate=0.4,
                    start_sequence=0,
                )
                if not invoice_df.empty and "nom" in invoice_df.columns:
                    products = invoice_df[["nom", "prix_achat"]].dropna().to_dict("records")
                else:
                    products = []
            except Exception:
                products = []

            # Fallback to custom parser if no products found
            if not products:
                products = parse_eurociel_text(text_content)

            stats["lines_parsed"] += len(products)

            for product in products:
                nom = product.get("nom", "")
                prix = float(product.get("prix_achat", 0) or 0)

                if not nom or prix <= 0:
                    continue

                match = match_product_by_name(nom, tenant_id, min_similarity)
                if match:
                    stats["lines_matched"] += 1
                    if update_product_price(
                        produit_id=match["produit_id"],
                        new_price=prix,
                        supplier="EUROCIEL",
                        tenant_id=tenant_id,
                        dry_run=dry_run,
                    ):
                        stats["prices_updated"] += 1

        except Exception as e:
            LOGGER.error(f"Error processing {pdf_path.name}: {e}")

    return stats


def process_taiyat_folder(
    tenant_id: int = 1,
    dry_run: bool = False,
    min_similarity: float = 0.5,
) -> dict:
    """Process all PDFs in TAIYAT folder."""
    stats = {
        "files_processed": 0,
        "lines_parsed": 0,
        "lines_matched": 0,
        "prices_updated": 0,
    }

    if not TAIYAT_DIR.exists():
        LOGGER.warning(f"TAIYAT folder not found: {TAIYAT_DIR}")
        return stats

    pdf_files = list(TAIYAT_DIR.glob("*.pdf"))
    LOGGER.info(f"Found {len(pdf_files)} TAIYAT PDFs")

    for pdf_path in pdf_files:
        LOGGER.info(f"Processing: {pdf_path.name}")
        stats["files_processed"] += 1

        try:
            text_content = extract_text_from_pdf(pdf_path)

            # Use tarif parser for TAIYAT (different format)
            if "tarif" in pdf_path.name.lower() or "liste" in pdf_path.name.lower():
                products = parse_taiyat_tarif(text_content)
            else:
                # Try standard parser for invoices
                try:
                    invoice_df = parse_invoice(
                        text_content,
                        supplier_hint="TAIYAT",
                        margin_rate=0.4,
                        start_sequence=0,
                    )
                    if not invoice_df.empty and "nom" in invoice_df.columns:
                        products = invoice_df[["nom", "prix_achat"]].dropna().to_dict("records")
                    else:
                        products = []
                except Exception:
                    products = []

            stats["lines_parsed"] += len(products)

            for product in products:
                nom = product.get("nom", "")
                prix = float(product.get("prix_achat", 0) or 0)

                if not nom or prix <= 0:
                    continue

                match = match_product_by_name(nom, tenant_id, min_similarity)
                if match:
                    stats["lines_matched"] += 1
                    if update_product_price(
                        produit_id=match["produit_id"],
                        new_price=prix,
                        supplier="TAIYAT",
                        tenant_id=tenant_id,
                        dry_run=dry_run,
                    ):
                        stats["prices_updated"] += 1

        except Exception as e:
            LOGGER.error(f"Error processing {pdf_path.name}: {e}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Backfill prices from EUROCIEL/TAIYAT")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually update")
    parser.add_argument("--supplier", type=str, default="all", help="EUROCIEL, TAIYAT, or all")
    parser.add_argument("--tenant", type=int, default=1, help="Tenant ID")
    parser.add_argument("--min-similarity", type=float, default=0.5, help="Min similarity score")
    args = parser.parse_args()

    total_stats = {
        "files_processed": 0,
        "lines_parsed": 0,
        "lines_matched": 0,
        "prices_updated": 0,
    }

    if args.supplier.upper() in ("EUROCIEL", "ALL"):
        LOGGER.info("=" * 50)
        LOGGER.info("PROCESSING EUROCIEL")
        LOGGER.info("=" * 50)
        stats = process_eurociel_folder(
            tenant_id=args.tenant,
            dry_run=args.dry_run,
            min_similarity=args.min_similarity,
        )
        for key in total_stats:
            total_stats[key] += stats[key]

    if args.supplier.upper() in ("TAIYAT", "ALL"):
        LOGGER.info("=" * 50)
        LOGGER.info("PROCESSING TAIYAT")
        LOGGER.info("=" * 50)
        stats = process_taiyat_folder(
            tenant_id=args.tenant,
            dry_run=args.dry_run,
            min_similarity=args.min_similarity,
        )
        for key in total_stats:
            total_stats[key] += stats[key]

    # Summary
    LOGGER.info("=" * 50)
    LOGGER.info("BACKFILL SUMMARY")
    LOGGER.info("=" * 50)
    LOGGER.info(f"Files processed: {total_stats['files_processed']}")
    LOGGER.info(f"Lines parsed: {total_stats['lines_parsed']}")
    match_rate = total_stats['lines_matched'] / max(1, total_stats['lines_parsed']) * 100
    LOGGER.info(f"Lines matched: {total_stats['lines_matched']} ({match_rate:.1f}%)")
    LOGGER.info(f"Prices updated: {total_stats['prices_updated']}")

    if args.dry_run:
        LOGGER.info("\n[DRY-RUN MODE] No actual updates were made.")


if __name__ == "__main__":
    main()
