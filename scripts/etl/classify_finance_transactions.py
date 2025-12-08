"""Recatégorise les finance_transaction_lines avec des règles détaillées (sans BANK_IN/BANK_OUT)."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Iterable

from sqlalchemy import text

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.data_repository import get_engine  # noqa: E402
from core.vendor_categories import load_vendor_category_rules  # noqa: E402

# Taxonomie cible (12 postes + encaissement)
TARGET_CATEGORIES: Dict[str, str] = {
    "encaissements": "Encaissements",
    "achats_fournisseurs": "Achats et frais fournisseurs",
    "salaires_remunerations": "Salaires & rémunérations",
    "charges_sociales": "Charges sociales",
    "impots_taxes": "Impôts & taxes",
    "frais_generaux": "Frais généraux",
    "transport_deplacement": "Transport & déplacement",
    "immobilisations_investissements": "Immobilisations & investissements",
    "loyer_immobilier": "Loyer & immobilier",
    "marketing_communication": "Marketing & communication",
    "frais_financiers": "Frais financiers",
    "informatique_telecom": "Informatique & télécom",
    "remboursements_clients": "Remboursements clients & litiges",
    "prestations_externes": "Prestations externes",
}


# Règles fines (mots-clés -> catégorie source)
BASE_CATEGORY_RULES: Tuple[Tuple[Tuple[str, ...], str, Tuple[str, ...] | None], ...] = (
    (("VERSEMENT ALS",), "Financement / Crédit", None),
    (("REMISE CB", "REM CB", "CB NO", "CB ", "CARTE"), "Encaissement", ("Entrée",)),
    (("REMISE CB NO", "REMISE CB N°"), "Encaissement", ("Entrée",)),
    (("REMISE CB", "REMISE CB NO", "REMISE CB N°"), "Frais d'encaissement", ("Sortie",)),
    (("CB12",), "Encaissement", ("Entrée",)),
    (("DEPOT", "VIR RECU", "VERSEMENT", "REMISE CHEQUE", "ALIMENTATION"), "Encaissement", ("Entrée",)),
    (("LYDIA", "PAYLIB"), "Encaissement mobile", ("Entrée",)),
    (("REAPRO",), "Approvisionnement", None),
    (("VIR SEPA M. TCHAKOUA", "VIR SEPA RECU /DE MME", "VIR SEPA RECU /DE ZOUBIR", "VIR SEPA RECU /DE TCHAKOUA", "VIR SEPA NOUTAM", "Virement entrant", "VIR INST","VIREMENT INST"), "Financement / Crédit", None),
    (("VIR INST", "VIREMENT INST", "VIR INST."), "Financement / Crédit", None),
    (("VOTRE REMISE SUR PRODUITS",), "Encaissement", ("Entrée",)),
    (("LCL A LA CARTE PRO",), "Frais bancaires", None),
    (("SALAI", "SALAIRE", "PAYE", "PAY\u00c9"), "Salaires", None),
    (("ANCIEN SOLDE", "BLOCAGE SUR PCE", "MOUVEMENT", "PARIS EUR"), "Frais bancaires", None),
    (("VIRT CPTE", "VIR CPTE A CPTE", "VIRT CPTE A CPTE", "VIR INST", "VIREMENT INST", "VIREMENT ENTRANT"), "Financement / Crédit", None),
    (("ECHEANCE PRET", "ECHEANCE PRÊT"), "Financement / Crédit", ("Sortie",)),
    (("STRIPE", "SUMUP", "ZETTLE", "PAYPAL"), "Frais d'encaissement", ("Sortie",)),
    (("SALAIRE", "PAYE"), "Salaires", ("Sortie",)),
    (("URSSAF",), "Charges sociales", ("Sortie",)),
    (("AGIRC", "ARRCO", "MALAKOFF", "KLESIA", "HUMANIS"), "Retraite / Prévoyance", ("Sortie",)),
    (("DGFIP", "IMPOTS", "TVA", "CFE", "CET"), "Fiscalité", ("Sortie",)),
    (("TOTALENERGIES", "TOTAL", "TOTAL ENERGIES", "TEF"), "Énergie", ("Sortie",)),
    (("TOTALENERGIES CHARGING", "DIGITAL CHARGING", "CHARGING"), "Carburant / Déplacements", ("Sortie",)),
    (("EDF", "E.D.F."), "Énergie", ("Sortie",)),
    (("ENGIE", "GAZ DE FRANCE"), "Énergie", ("Sortie",)),
    (("GAZEL", "GAZELENERGIE", "TOTALENERGIES", "TOTAL ENERGIES"), "Énergie", None),
    (("ENI", "ILEK", "PLANETE OUI", "MINT ENERGIE"), "Énergie", None),
    (("EAU DE PARIS", "VEOLIA EAU", "SUEZ EAU", "SAUR"), "Eau", None),
    (("RESIDENCE", "LOYER", "LOCATION", "LOCAT", "ST AN"), "Loyer/Location", None),
    (("FREE", "FREE PRO"), "Télécom", None),
    (("SFR", "SFR BUSINESS"), "Télécom", None),
    (("ORANGE", "ORANGE PRO"), "Télécom", None),
    (("BOUYGUES", "BBOX", "BYTEL", "PRLV SEPA BOUYGUES"), "Télécom", None),
    (("CANAL", "CANALSAT"), "Abonnements TV", ("Sortie",)),
    (("NETFLIX", "SPOTIFY", "ABONNEMENT"), "Abonnements", ("Sortie",)),
    (("SPB", "PACIFICA", "CREDIT AGRICOLE ASSURANCE", "AXA", "ALLIANZ", "MAIF", "MAAF", "MATMUT", "HISCOX", "ASSURANCE LCL"), "Assurance", ("Sortie",)),
    (("HMD", "AUDIT", "EXPERT COMPTABLE", "CABINET COMPTABLE", "HMD AUDIT ET CONSEIL"), "Comptabilité", ("Sortie",)),
    (("METRO", "PROMOCASH", "TRANS GOURMET", "TRANSGOURMET", "DAVIGEL", "SYSCO", "BOUCH. BVS", "BOUCH BVS", "BOUCH", "GNANAM", "EXOTI", "EUROCIEL", "KEDY PACK", "TAI YAT", "RETRAIT", "LINCONTOURNABLE", "LEADER PRICE", "LE VINCI", "ACHAT"), "Approvisionnement", None),
    (("CENTRAKOR",), "Fournitures / Matériel", ("Sortie",)),
    (("PREFILOC", "FINANCEMENT", "CREDIT"), "Financement / Crédit", ("Sortie",)),
    (("AVEM", "LOCATION TPE", "TPE AVEM"), "Frais d'encaissement", ("Sortie",)),
    (("FRANCE BOISSONS", "C10", "COCA", "COCA COLA", "COCA-COLA", "HEINEKEN FRANCE", "LES GRANDS CHAIS", "CASTEL FRERES"), "Boissons", ("Sortie",)),
    (("RAJAPACK", "RAJA", "PAREDES", "PROD'HYGIENE", "PRO HYGIENE", "HYGIAL"), "Hygiène / Emballages", ("Sortie",)),
    (("NESPRESSO", "LAVAZZA", "MAHLKOENIG", "BUNN"), "Café / Matériel bar", ("Sortie",)),
    (("BRAGARD", "ROBUR"), "Tenues / Uniformes", ("Sortie",)),
    (("KILOUTOU", "LOXAM"), "Location matériel", ("Sortie",)),
    (("UBER EATS", "DELIVEROO", "JUST EAT", "UBER "), "Plateformes / Commissions", ("Sortie",)),
    (("DPD", "CHRONOPOST", "COLISSIMO", "LA POSTE", "MONDIAL RELAY", "GLS", "UPS", "DHL"), "Logistique / Transport", ("Sortie",)),
    (("MICROSOFT", "OFFICE 365", "AZURE", "GOOGLE", "WORKSPACE", "GSUITE", "ADOBE", "CREATIVE CLOUD", "CANVA", "NOTION", "SLACK"), "SaaS / Informatique", ("Sortie",)),
    (("SACEM", "SPRE"), "Droits d’auteur / Musique d’ambiance", ("Sortie",)),
    (("AMAZON", "AMZN", "FNAC", "LDLC", "MATERIEL.NET", "DARTY", "BOULANGER"), "Fournitures / Matériel", ("Sortie",)),
    (("BRUNEAU", "LYRECO"), "Fournitures de bureau", ("Sortie",)),
    (("PAPREC", "VEOLIA PROPRETE", "SUEZ RECYCLAGE"), "Déchets / Recyclage", ("Sortie",)),
    (("VERISURE", "EPS"), "Sécurité", ("Sortie",)),
    (("ELIS", "INITIAL"), "Blanchisserie / Linge pro", ("Sortie",)),
    (("RATP", "SNCF", "IDF MOBILITES"), "Transports", ("Sortie",)),
    (("UBER", "UBER EATS", "UBER *"), "Transports", ("Sortie",)),
    (("TOTAL STATION", "ESSO", "SHELL", "AVIA", "TOTALENERGIES", "TOTAL ENERGIES"), "Carburant / Déplacements", ("Sortie",)),
    (("ABON LCL ACCESS", "COTISATION CARTE", "COTISATION MENSUELLE CARTE", "OPTION PRO", "COTISATION MENSUELLE", "LCL A LA CARTE PRO"), "Frais bancaires", ("Sortie",)),
    (("COMMISSIONS SUR REMISE CB",), "Frais bancaires", ("Sortie",)),
    (("RESULTAT ARRETE COMPTE",), "Frais bancaires", None),
    (("GNANAM", "NOUTAM", "FOURNISSEUR"), "Fournisseur", ("Sortie",)),
    (("LEROY MERLIN", "ADEO*LEROY"), "Fournitures / Matériel", ("Sortie",)),
    (("ETHAN",), "Fournitures / Matériel", ("Sortie",)),
    (("MASSA ANGELE",), "Salaires", ("Sortie",)),
    (("DRFIP",), "Fiscalité", ("Sortie",)),
    (("FRAIS", "AGIOS", "COMMISSION", "ABONNEMENT", "COTISATION CARTE"), "Frais bancaires", None),
    (("CHANTIER", "FACTURE"), "Autre", None),
)
CATEGORY_RULES = BASE_CATEGORY_RULES + load_vendor_category_rules()

# Mapping des catégories sources -> taxonomie 12 postes (+ encaissements)
SOURCE_TO_TARGET: Dict[str, str] = {
    # Recettes
    "Encaissement": "encaissements",
    "Encaissement mobile": "encaissements",
    "Revenu": "encaissements",
    "Revenu / Encaissement": "encaissements",
    "Transfert / Paiement mobile": "encaissements",
    "Transfert / Change": "encaissements",
    "Autres recettes": "encaissements",
    # Achats / fournisseurs / stocks
    "Approvisionnement": "achats_fournisseurs",
    "Fournisseur": "achats_fournisseurs",
    "Fournisseurs alimentaires": "achats_fournisseurs",
    "Boissons": "achats_fournisseurs",
    "Courses / Alimentation": "achats_fournisseurs",
    "Hygiène / Emballages": "achats_fournisseurs",
    "Hygiène / Produits entretien": "achats_fournisseurs",
    "Café / Matériel bar": "achats_fournisseurs",
    "Café / Bar": "achats_fournisseurs",
    "Tenues / Uniformes": "achats_fournisseurs",
    "Tenues professionnelles": "achats_fournisseurs",
    "Fournitures / Matériel": "achats_fournisseurs",
    "Matériel / Outillage": "achats_fournisseurs",
    "Matériel électrique": "achats_fournisseurs",
    "Plomberie / Bâtiment": "achats_fournisseurs",
    "Fournitures / Informatique": "achats_fournisseurs",
    "Fournitures de bureau": "achats_fournisseurs",
    "Matériel informatique": "achats_fournisseurs",
    "Matériel électrique": "achats_fournisseurs",
    "Matériel / Outillage": "achats_fournisseurs",
    "Matériel / Bâtiment": "achats_fournisseurs",
    "Impression / Papeterie": "frais_generaux",
    "Hygiène / Produits entretien": "achats_fournisseurs",
    "Café / Matériel bar": "achats_fournisseurs",
    "Courses / Alimentation": "achats_fournisseurs",
    "Repas / Restauration": "achats_fournisseurs",
    "Déchets / Recyclage": "frais_generaux",
    "Hygiène / Produits entretien": "achats_fournisseurs",
    "Autres charges": "frais_generaux",
    # Salaires / social / RH
    "Salaires": "salaires_remunerations",
    "Charges sociales": "charges_sociales",
    "Retraite / Prévoyance": "charges_sociales",
    "Prévoyance / Mutuelle": "charges_sociales",
    "Paie / RH": "salaires_remunerations",
    "Recrutement": "salaires_remunerations",
    # Impôts / taxes / administratif
    "Fiscalité": "impots_taxes",
    "Impôts et taxes": "impots_taxes",
    "Administratif": "impots_taxes",
    "TVA": "impots_taxes",
    # Frais généraux & prestations externes
    "Autre": "frais_generaux",
    "Déchets / Recyclage": "frais_generaux",
    "Nettoyage / Déchets": "frais_generaux",
    "Blanchisserie / Linge pro": "frais_generaux",
    "Blanchisserie / Entretien linge": "frais_generaux",
    "Assurance": "frais_generaux",
    "Sécurité": "frais_generaux",
    "Sécurité / Alarme": "frais_generaux",
    "Moyens de paiement": "frais_generaux",
    "Repas / Restauration": "frais_generaux",
    "Divers": "frais_generaux",
    "Santé / Personnel": "frais_generaux",
    "Bureaux": "loyer_immobilier",
    "Frais déplacement": "transport_deplacement",
    # Prestations et services pro
    "Comptabilité": "prestations_externes",
    "Prestations externes": "prestations_externes",
    "Légal / Conseil": "prestations_externes",
    "Signature / Gestion documentaire": "prestations_externes",
    "Maintenance / Froid": "prestations_externes",
    "Communication": "prestations_externes",
    "Formation / Sécurité": "prestations_externes",
    "Recrutement": "prestations_externes",
    # Financier / banque
    "Frais bancaires": "frais_financiers",
    "Frais d'encaissement": "frais_financiers",
    "Banque": "frais_financiers",
    "Banque en ligne": "frais_financiers",
    "Financement / Crédit": "frais_financiers",
    "Crédit / Financement": "frais_financiers",
    "Encaissement / Commission": "frais_financiers",
    "Transfert / Change": "frais_financiers",
    "Moyens de paiement": "frais_financiers",
    # Énergie / télécom / IT
    "Énergie": "frais_generaux",
    "Eau": "frais_generaux",
    "Télécom": "informatique_telecom",
    "SaaS / Informatique": "informatique_telecom",
    "Logiciels / Abonnements": "informatique_telecom",
    "Logiciels": "informatique_telecom",
    "Stockage cloud": "informatique_telecom",
    "Hébergement / Nom de domaine": "informatique_telecom",
    "Informatique / Télécom": "informatique_telecom",
    "Emailing": "marketing_communication",
    "Site web": "marketing_communication",
    "Site web / E-commerce": "marketing_communication",
    "Publicité": "marketing_communication",
    "Publicité / Réseaux sociaux": "marketing_communication",
    "Musique": "marketing_communication",
    "Abonnements TV": "marketing_communication",
    # Transport / déplacements
    "Logistique / Transport": "transport_deplacement",
    "Transports": "transport_deplacement",
    "Déplacements": "transport_deplacement",
    "Carburant / Déplacements": "transport_deplacement",
    "Carburant": "transport_deplacement",
    "Frais déplacement": "transport_deplacement",
    "Hébergement": "transport_deplacement",
    # Immobilisations / loyer
    "Location matériel": "immobilisations_investissements",
    "Loyer/Location": "loyer_immobilier",
    "Bureaux": "loyer_immobilier",
    # Marketing & communication
    "Publicité": "marketing_communication",
    "Publicité / Réseaux sociaux": "marketing_communication",
    "Emailing": "marketing_communication",
    "Site web / E-commerce": "marketing_communication",
    "Site web": "marketing_communication",
    "Musique": "marketing_communication",
    "Abonnements TV": "marketing_communication",
    "Communication": "marketing_communication",
}


def _normalize(text_: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text_.upper())


def _infer_target_from_category_name(cat: str, entry_type: str) -> str:
    """Heuristique pour mapper un libellé de catégorie (CSV vendors) vers la taxonomie cible."""
    cat_l = cat.lower()
    if entry_type == "Entrée":
        return "encaissements"
    if any(k in cat_l for k in ("banque", "frais banc", "commission", "encaissement / commission", "moyens de paiement")):
        return "frais_financiers"
    if any(k in cat_l for k in ("financement", "crédit", "credit", "prefiloc")):
        return "frais_financiers"
    if any(k in cat_l for k in ("approvisionnement", "boissons", "courses", "fournitures", "matériel", "materiel", "outillage", "plomberie", "bâtiment", "batiment", "électrique", "electrique", "emballages", "hygiène", "hygiene", "déchets", "dechets", "café", "cafe", "bar")):
        return "achats_fournisseurs"
    if any(k in cat_l for k in ("comptabilité", "compta", "prestations externes", "juridique", "signature", "documentaire", "formation", "recrutement", "communication", "maintenance")):
        return "prestations_externes"
    if any(k in cat_l for k in ("télécom", "telecom", "saas", "logiciels", "stockage", "hébergement", "hebergement", "nom de domaine", "cloud", "informatique")):
        return "informatique_telecom"
    if any(k in cat_l for k in ("publicité", "publicite", "emailing", "site web", "e-commerce", "musique", "abonnement tv", "réseaux sociaux")):
        return "marketing_communication"
    if any(k in cat_l for k in ("transports", "transport", "déplacements", "deplacements", "carburant", "frais déplacement", "frais deplacement", "logistique", "uber", "taxi", "train", "avion", "hôtel", "hotel", "hébergement", "hebergement")):
        return "transport_deplacement"
    if any(k in cat_l for k in ("assurance", "blanchisserie", "sécurité", "securite", "nettoyage", "déchets", "dechets", "hygiène", "hygiene", "frais généraux", "autres charges", "divers", "santé")):
        return "frais_generaux"
    if any(k in cat_l for k in ("charges sociales", "urssaf", "retraite", "prévoyance", "prevoyance", "mutuelle", "paie / rh", "paie", "rh")):
        return "charges_sociales"
    if any(k in cat_l for k in ("salaires", "rémunérations", "remunerations", "primes", "indemnités", "indemnites")):
        return "salaires_remunerations"
    if any(k in cat_l for k in ("impôt", "impot", "taxe", "tva", "cfe", "cvae", "fiscalité", "fiscalite", "administratif")):
        return "impots_taxes"
    if any(k in cat_l for k in ("loyer", "bureaux", "immobilier", "locatif", "copropriété", "copropriete")):
        return "loyer_immobilier"
    if any(k in cat_l for k in ("location matériel", "location materiel", "immobilisations", "investissements", "aménagement", "amenagement")):
        return "immobilisations_investissements"
    if any(k in cat_l for k in ("remboursement", "avoir", "litige", "sav")):
        return "remboursements_clients"
    return "frais_generaux"


def load_category_map(conn) -> Dict[Tuple[int, str], int]:
    rows = conn.execute(text("SELECT id, entity_id, lower(code) AS code FROM finance_categories")).fetchall()
    return {(int(r.entity_id), str(r.code)): int(r.id) for r in rows}


def ensure_target_categories(conn) -> Dict[Tuple[int, str], int]:
    # Crée les catégories de la taxonomie pour toutes les entités existantes
    entities = [int(r.entity_id) for r in conn.execute(text("SELECT DISTINCT entity_id FROM finance_accounts WHERE entity_id IS NOT NULL"))]
    for ent in entities:
        for code, name in TARGET_CATEGORIES.items():
            conn.execute(
                text(
                    "INSERT INTO finance_categories (entity_id, code, name, type) "
                    "VALUES (:e, :c, :n, :t) "
                    "ON CONFLICT (entity_id, code) DO NOTHING"
                ),
                {
                    "e": ent,
                    "c": code,
                    "n": name,
                    "t": "RECETTE" if code == "encaissements" else "DEPENSE",
                },
            )
    return load_category_map(conn)


def match_category(entity_id: int, direction: str, label: str, cat_map: Dict[Tuple[int, str], int]) -> Optional[int]:
    upper = label.upper()
    normalized = _normalize(label)
    entry_type = "Entrée" if direction == "IN" else "Sortie"
    for keywords, category_name, allowed_types in CATEGORY_RULES:
        if allowed_types and entry_type not in allowed_types:
            continue
        if any(k.upper() in upper or _normalize(k) in normalized for k in keywords):
            target_code = SOURCE_TO_TARGET.get(category_name)
            if not target_code:
                target_code = _infer_target_from_category_name(category_name, entry_type)
            cid = cat_map.get((entity_id, target_code))
            if cid:
                return cid
    # fallback : Encaissements pour IN, Frais généraux pour OUT
    if direction == "IN":
        return cat_map.get((entity_id, "encaissements"))
    return cat_map.get((entity_id, "frais_generaux"))


def main() -> None:
    eng = get_engine()
    with eng.begin() as conn:
        ensure_target_categories(conn)
        cat_map = load_category_map(conn)
        rows = conn.execute(
            text(
                """
                SELECT tl.id AS line_id, t.entity_id, t.direction, COALESCE(l.libelle_banque, t.note, '') AS label
                FROM finance_transaction_lines tl
                JOIN finance_transactions t ON t.id = tl.transaction_id
                LEFT JOIN finance_bank_statement_lines l
                  ON t.ref_externe LIKE 'stmtline:%'
                 AND l.id = CAST(substring(t.ref_externe FROM 'stmtline:(\\d+)') AS BIGINT)
                """
            )
        ).fetchall()

        updated = 0
        for r in rows:
            cid = match_category(int(r.entity_id), str(r.direction), r.label or "", cat_map)
            if not cid:
                continue
            conn.execute(
                text("UPDATE finance_transaction_lines SET category_id = :cid WHERE id = :line_id"),
                {"cid": cid, "line_id": int(r.line_id)},
            )
            updated += 1

        print(f"{updated} lignes recatégorisées (règles détaillées, sans BANK_IN/OUT).")


if __name__ == "__main__":
    main()