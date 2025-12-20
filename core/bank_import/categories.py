"""Unified and cleaned category keywords for bank transaction classification.

This module contains the validated keyword list after analysis to remove:
- Misplaced keywords
- Redundant keywords
- Overly generic keywords that cause false positives

Each category has:
- A unique code
- A display name
- A list of specific keywords (uppercase, sorted)
- Direction hints (IN/OUT/BOTH)

Supports bank-specific keywords for LCL and BNP formats.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class CategoryDefinition:
    """Definition of a transaction category."""
    code: str
    name: str
    keywords: Tuple[str, ...]
    direction: str  # "IN", "OUT", "BOTH"
    priority: int = 0  # Higher = more specific = matches first
    # Bank-specific keywords (override generic if bank_type matches)
    keywords_lcl: Tuple[str, ...] = field(default_factory=tuple)
    keywords_bnp: Tuple[str, ...] = field(default_factory=tuple)


# =============================================================================
# UNIFIED CATEGORY DEFINITIONS
# =============================================================================

CATEGORIES: Dict[str, CategoryDefinition] = {
    # -------------------------------------------------------------------------
    # ENTREES (IN)
    # -------------------------------------------------------------------------
    "encaissements": CategoryDefinition(
        code="encaissements",
        name="Encaissements",
        keywords=(
            # CB/TPE encaissements
            "REM CB", "REMISE CB", "CB NO", "CB12",
            # Versements
            "VERSEMENT ESPECES", "DEPOT ESPECES",
            # Virements reçus
            "VIR RECU", "VIREMENT RECU",
            # Chèques
            "REMISE CHEQUE", "REMISE CHQ",
            # Mobile
            "LYDIA RECU", "PAYLIB RECU",
            # Plateformes
            "STRIPE PAYOUT", "SUMUP PAYOUT", "ZETTLE PAYOUT",
        ),
        direction="IN",
        priority=10,
        # LCL specific
        keywords_lcl=(
            "REMISE CB NO", "VERSEMENT ALS",
        ),
        # BNP specific
        keywords_bnp=(
            "VIR SEPA RECU", "VIR INST RECU", "VIR SCT INST RECU",
            "VRST ESPECES", "VERSEMENT ESPECES AUTOMATE",
            "VIR CPTE A CPTE RECU",
        ),
    ),

    # -------------------------------------------------------------------------
    # SORTIES (OUT) - Par importance métier
    # -------------------------------------------------------------------------
    "achats_fournisseurs": CategoryDefinition(
        code="achats_fournisseurs",
        name="Achats / Fournisseurs",
        keywords=(
            # Grossistes alimentaires
            "METRO", "PROMOCASH", "TRANSGOURMET", "TRANS GOURMET",
            "DAVIGEL", "SYSCO", "BRAKE", "POMONA",
            # Boucheries
            "BOUCH. BVS", "BOUCH BVS", "BOUCHERIE",
            # Fournisseurs spécifiques
            "GNANAM", "EXOTI", "EUROCIEL", "TAI YAT",
            "LEADER PRICE", "LINCONTOURNABLE", "LE VINCI",
            # Boissons
            "FRANCE BOISSONS", "C10", "COCA COLA", "COCA-COLA",
            "HEINEKEN FRANCE", "LES GRANDS CHAIS", "CASTEL FRERES",
            # Emballages/Hygiène
            "RAJAPACK", "RAJA", "PAREDES", "PROD'HYGIENE",
            "PRO HYGIENE", "HYGIAL", "KEDY PACK",
            # Café
            "NESPRESSO", "LAVAZZA",
        ),
        direction="OUT",
        priority=20,
    ),

    "salaires_remunerations": CategoryDefinition(
        code="salaires_remunerations",
        name="Salaires et Rémunérations",
        keywords=(
            "SALAIRE", "PAYE", "PAIE",
            "VIR SALAIRE", "VIREMENT SALAIRE",
            "REMUNERATION", "PRIME",
            "ACOMPTE SALAIRE",
        ),
        direction="OUT",
        priority=25,
    ),

    "charges_sociales": CategoryDefinition(
        code="charges_sociales",
        name="Charges Sociales",
        keywords=(
            "URSSAF",
            "AGIRC", "ARRCO", "AGIRC-ARRCO",
            "MALAKOFF", "MALAKOFF HUMANIS",
            "KLESIA", "HUMANIS", "AG2R",
            "MUTUELLE", "PREVOYANCE",
            "CPAM", "POLE EMPLOI",
        ),
        direction="OUT",
        priority=25,
    ),

    "impots_taxes": CategoryDefinition(
        code="impots_taxes",
        name="Impôts et Taxes",
        keywords=(
            "DGFIP", "IMPOT", "IMPOTS",
            "TVA", "IS ", "IR ",
            "CFE", "CET", "CVAE",
            "TAXE FONCIERE", "TAXE PROFESSIONNELLE",
            "TRESOR PUBLIC",
        ),
        direction="OUT",
        priority=25,
    ),

    "loyer_immobilier": CategoryDefinition(
        code="loyer_immobilier",
        name="Loyer et Immobilier",
        keywords=(
            "LOYER", "LOCATION LOCAL",
            "RESIDENCE", "ST AN",
            "BAIL", "FERMAGE",
            "SCI ", "FONCIERE",
            "SYNDIC", "CHARGES LOCATIVES",
        ),
        direction="OUT",
        priority=20,
    ),

    "energie_fluides": CategoryDefinition(
        code="energie_fluides",
        name="Énergie et Fluides",
        keywords=(
            # Électricité
            "EDF", "E.D.F.", "ENEDIS",
            # Gaz
            "ENGIE", "GAZ DE FRANCE", "GAZEL", "GAZELENERGIE",
            # Multi-énergies
            "TOTALENERGIES", "TOTAL ENERGIES",
            "ENI", "ILEK", "PLANETE OUI", "MINT ENERGIE",
            # Eau
            "EAU DE PARIS", "VEOLIA EAU", "SUEZ EAU", "SAUR",
            "LYONNAISE DES EAUX",
        ),
        direction="OUT",
        priority=20,
    ),

    "telecom_informatique": CategoryDefinition(
        code="telecom_informatique",
        name="Télécom et Informatique",
        keywords=(
            # Télécom
            "FREE MOBILE", "FREE PRO", "FREE TELECOM",
            "SFR BUSINESS", "SFR PRO",
            "ORANGE PRO", "ORANGE BUSINESS",
            "BOUYGUES TELECOM", "BYTEL",
            # SaaS / Cloud
            "MICROSOFT 365", "OFFICE 365", "AZURE",
            "GOOGLE WORKSPACE", "GSUITE",
            "ADOBE", "CREATIVE CLOUD",
            "CANVA", "NOTION", "SLACK",
            "OVH", "AWS", "AMAZON WEB",
            # Matériel
            "LDLC", "MATERIEL.NET",
        ),
        direction="OUT",
        priority=15,
        # BNP specific
        keywords_bnp=(
            "ORANGE SA", "PRLV SEPA ORANGE",
        ),
    ),

    "assurances": CategoryDefinition(
        code="assurances",
        name="Assurances",
        keywords=(
            "AXA", "ALLIANZ", "GENERALI",
            "MAIF", "MAAF", "MATMUT",
            "PACIFICA", "CREDIT AGRICOLE ASSURANCE",
            "HISCOX", "SPB", "MMA", "GROUPAMA",
            "COVEA", "GMF",
        ),
        direction="OUT",
        priority=20,
        # LCL specific
        keywords_lcl=(
            "ASSURANCE LCL",
            "LCL ASSURANCE MULTIRISQUE",
        ),
        # BNP specific
        keywords_bnp=(
            "CARDIF ASSURANCE VIE",
            "CARDIF IARD",
            "APRIL PARTENAIRES",
            "SWISSLIFE",
            "ABEILLE VIE",
        ),
    ),

    "frais_bancaires": CategoryDefinition(
        code="frais_bancaires",
        name="Frais Bancaires",
        keywords=(
            "COTISATION CARTE", "COTISATION MENSUELLE", "OPTION PRO",
            "AGIOS", "FRAIS TENUE COMPTE", "INTERETS DEBITEURS",
        ),
        direction="OUT",
        priority=15,
        # LCL specific
        keywords_lcl=(
            "ABON LCL", "ABON LCL ACCESS",
            "COMMISSIONS SUR REMISE CB",
            "RESULTAT ARRETE COMPTE",
            "TRAIT.IRREG.FONCT.CTE",
        ),
        # BNP specific
        keywords_bnp=(
            "*COMMISSIONS COTISATION",
            "COMMISSIONS COTISATION A UNE OFFRE",
            "ESPRIT LIBRE",
            "COTISATION FORFAIT",
            "ECHEANCE PRET",  # Loan payments
            "CARREFOUR BANQUE",  # Crédits Carrefour
        ),
    ),

    "services_professionnels": CategoryDefinition(
        code="services_professionnels",
        name="Services Professionnels",
        keywords=(
            # Comptabilité
            "HMD", "HMD AUDIT", "EXPERT COMPTABLE",
            "CABINET COMPTABLE", "FIDUCIAIRE",
            # Juridique
            "AVOCAT", "NOTAIRE", "HUISSIER",
            # Autres
            "CONSULTANT", "AUDIT",
        ),
        direction="OUT",
        priority=15,
    ),

    "transport_deplacement": CategoryDefinition(
        code="transport_deplacement",
        name="Transport et Déplacements",
        keywords=(
            # Carburant
            "TOTAL STATION", "ESSO", "SHELL", "AVIA", "BP ",
            "TOTALENERGIES STATION",
            # Bornes électriques
            "TOTALENERGIES CHARGING", "DIGITAL CHARGING", "IONITY",
            # Transport
            "RATP", "SNCF", "IDF MOBILITES",
            "TAXI", "UBER RIDE", "BOLT",
            # Location
            "KILOUTOU", "LOXAM", "HERTZ", "AVIS", "EUROPCAR",
        ),
        direction="OUT",
        priority=15,
        # BNP specific
        keywords_bnp=(
            "IMAGINE R", "GIE COMUTITRES",  # Navigo pass
        ),
    ),

    "frais_encaissement": CategoryDefinition(
        code="frais_encaissement",
        name="Frais d'Encaissement",
        keywords=(
            "STRIPE FEE", "SUMUP FEE",
            "ZETTLE FEE", "PAYPAL FEE",
            "AVEM", "LOCATION TPE", "TPE AVEM",
            "COMMISSION CARTE",
        ),
        direction="OUT",
        priority=15,
    ),

    # -------------------------------------------------------------------------
    # CATÉGORIE PAR DÉFAUT
    # -------------------------------------------------------------------------
    "a_categoriser": CategoryDefinition(
        code="a_categoriser",
        name="À Catégoriser",
        keywords=(),  # No keywords - fallback category
        direction="BOTH",
        priority=0,
    ),
}


# =============================================================================
# KEYWORD INDEX (for fast lookup)
# =============================================================================

def build_keyword_index() -> Dict[str, str]:
    """Build a keyword -> category_code index.

    Returns:
        Dict mapping each keyword to its category code
    """
    index: Dict[str, str] = {}
    for cat_code, cat_def in CATEGORIES.items():
        for keyword in cat_def.keywords:
            index[keyword.upper()] = cat_code
    return index


KEYWORD_INDEX = build_keyword_index()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_category(code: str) -> Optional[CategoryDefinition]:
    """Get category definition by code."""
    return CATEGORIES.get(code)


def get_all_categories() -> List[CategoryDefinition]:
    """Get all category definitions sorted by priority (highest first)."""
    return sorted(
        CATEGORIES.values(),
        key=lambda c: c.priority,
        reverse=True
    )


def get_categories_for_direction(direction: str) -> List[CategoryDefinition]:
    """Get categories matching a direction (IN, OUT, or BOTH)."""
    return [
        cat for cat in CATEGORIES.values()
        if cat.direction == direction or cat.direction == "BOTH"
    ]
