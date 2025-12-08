"""Constants for restaurant services - category rules, regex patterns, presets."""

from __future__ import annotations

import re
from typing import Any, Dict

from core.vendor_categories import load_vendor_category_rules


# Regex patterns for parsing bank statements
TRANSACTION_LINE_RE = re.compile(
    r'^(?P<op>\d{2}\.\d{2})\s+(?P<val>\d{2}\.\d{2}\.\d{2})\s+(?P<body>.+)$'
)
AMOUNT_RE = re.compile(r'(\d[\d\s]*,\d{2})')

CREDIT_KEYWORDS = [
    "VERSEMENT",
    "REMISE",
    "DEPOT",
    "BRUT",
]

DEBIT_KEYWORDS = [
    "PRLV",
    "VIR",
    "TRAIT",
    "CB ",
    "CB",
    "ABON",
    "LOYER",
    "URSSAF",
    "ENGIE",
    "SFR",
    "CANAL",
]

IGNORED_PREFIXES = (
    "PAGE ",
    "ECRITURES DE LA PERIODE",
    "DATE LIBELLE VALEUR",
    "ANCIEN SOLDE",
    "SOLDE INTERMEDIAIRE",
    "Titulaire du compte",
    "Votreconseiller",
    "Credit Lyonnais",
    "RELEVE D'IDENTITE",
)
IGNORED_PREFIXES_UPPER = tuple(prefix.upper() for prefix in IGNORED_PREFIXES)

HEADER_START_PREFIXES = (
    "PRLV",
    "VIR",
    "VIREMENT",
    "VERSEMENT",
    "VERSEMENTS",
    "REMISE",
    "REM CB",
    "CB",
    "CHEQUE",
    "CHQ",
    "DEPOT",
    "DEBLOC",
    "DEBLOCSUR",
    "DEBLOC SUR",
    "FRAIS",
    "AGIOS",
    "PAIEMENT",
    "PREFILOC",
    "LOYER",
    "RESIDENCE",
    "METRO",
    "GNANAM",
    "NOUTAM",
    "ENGIE",
    "GAZ",
    "GAZELENERGIE",
    "SFR",
    "CANAL",
    "ASSURANCE",
    "AVEM",
    "SPB",
    "URSSAF",
    "KLESIA",
    "HMD",
    "FACTURE",
    "INT",
    "AVIS",
    "SALAIRE",
)

DETAIL_PREFIXES = (
    "LIBELLE",
    "REF",
    "ID",
    "BRUT",
    "COM",
    "PCE",
    "REG",
    "N",
    "NO",
    "NUMERO",
    "NUMERO",
    "BIC",
    "IBAN",
    "CLIENT",
    "RIB",
    "DUPLICATA",
    "COTIS",
    "HEANCE",
)

STOP_PREFIXES = tuple(
    s.upper()
    for s in (
        "PAGE",
        "ECRITURES",
        "DATE LIBELLE",
        "ANCIEN SOLDE",
        "SOLDE INTERMEDIAIRE",
        "TITULAIRE DU COMPTE",
        "VOTRECONSEILLER",
        "CREDIT",
        "CREDIT",
        "RELEVE",
        "L INCONTOURNABLE",
        "DOMICILIATION",
        "REFERENCES",
        "REFERENCES",
        "PRENEZ",
        "IBAN",
        "BIC",
        "BETTY",
        "COMPTE :",
    )
)

# Category rules for automatic classification
CATEGORY_RULES: tuple[tuple[tuple[str, ...], str, tuple[str, ...] | None], ...] = (
    (("VERSEMENT ALS",), "Encaissement", ("Entree",)),
    (("REMISE CB", "REM CB", "CB NO", "CB ", "CARTE"), "Encaissement", ("Entree",)),
    (("CB12",), "Encaissement", ("Entree",)),
    (("DEPOT", "VIR RECU", "VERSEMENT", "REMISE CHEQUE", "ALIMENTATION"), "Encaissement", ("Entree",)),
    (("LYDIA", "PAYLIB"), "Encaissement mobile", ("Entree",)),
    (("STRIPE", "SUMUP", "ZETTLE", "PAYPAL"), "Frais d'encaissement", ("Sortie",)),
    (("SALAIRE", "PAYE"), "Salaires", ("Sortie",)),
    (("URSSAF",), "Charges sociales", ("Sortie",)),
    (("AGIRC", "ARRCO", "MALAKOFF", "KLESIA", "HUMANIS"), "Retraite / Prevoyance", ("Sortie",)),
    (("DGFIP", "IMPOTS", "TVA", "CFE", "CET"), "Fiscalite", ("Sortie",)),
    (("TOTALENERGIES", "TOTAL", "TOTAL ENERGIES", "TEF"), "Energie", ("Sortie",)),
    (("TOTALENERGIES CHARGING", "DIGITAL CHARGING", "CHARGING"), "Carburant / Deplacements", ("Sortie",)),
    (("EDF", "E.D.F."), "Energie", ("Sortie",)),
    (("ENGIE", "GAZ DE FRANCE"), "Energie", ("Sortie",)),
    (("GAZEL", "GAZELENERGIE"), "Energie", ("Sortie",)),
    (("ENI", "ILEK", "PLANETE OUI", "MINT ENERGIE"), "Energie", ("Sortie",)),
    (("EAU DE PARIS", "VEOLIA EAU", "SUEZ EAU", "SAUR"), "Eau", ("Sortie",)),
    (("RESIDENCE", "LOYER", "LOCATION", "LOCAT", "ST AN"), "Loyer/Location", ("Sortie",)),
    (("FREE", "FREE PRO"), "Telecom", ("Sortie",)),
    (("SFR", "SFR BUSINESS"), "Telecom", ("Sortie",)),
    (("ORANGE", "ORANGE PRO"), "Telecom", ("Sortie",)),
    (("BOUYGUES", "BBOX", "BYTEL"), "Telecom", ("Sortie",)),
    (("CANAL", "CANALSAT"), "Abonnements TV", ("Sortie",)),
    (("NETFLIX", "SPOTIFY", "ABONNEMENT"), "Abonnements", ("Sortie",)),
    (
        (
            "SPB",
            "PACIFICA",
            "CREDIT AGRICOLE ASSURANCE",
            "AXA",
            "ALLIANZ",
            "MAIF",
            "MAAF",
            "MATMUT",
            "HISCOX",
            "ASSURANCE LCL",
        ),
        "Assurance",
        ("Sortie",),
    ),
    (("HMD", "AUDIT", "EXPERT COMPTABLE", "CABINET COMPTABLE", "HMD AUDIT ET CONSEIL"), "Comptabilite", ("Sortie",)),
    (
        (
            "METRO",
            "PROMOCASH",
            "TRANS GOURMET",
            "TRANSGOURMET",
            "DAVIGEL",
            "SYSCO",
            "BOUCH. BVS",
            "BOUCH BVS",
            "BOUCH",
            "GNANAM",
            "EXOTI",
            "EUROCIEL",
            "KEDY PACK",
            "TAI YAT",
            "RETRAIT",
            "LINCONTOURNABLE",
            "LEADER PRICE",
            "LE VINCI",
        ),
        "Approvisionnement",
        ("Sortie",),
    ),
    (("CENTRAKOR",), "Fournitures / Materiel", ("Sortie",)),
    (("PREFILOC", "FINANCEMENT", "CREDIT"), "Financement / Credit", ("Sortie",)),
    (("AVEM", "LOCATION TPE", "TPE AVEM"), "Frais d'encaissement", ("Sortie",)),
    (("FRANCE BOISSONS", "C10", "COCA", "COCA COLA", "COCA-COLA", "HEINEKEN FRANCE", "LES GRANDS CHAIS", "CASTEL FRERES"), "Boissons", ("Sortie",)),
    (("RAJAPACK", "RAJA", "PAREDES", "PROD'HYGIENE", "PRO HYGIENE", "HYGIAL"), "Hygiene / Emballages", ("Sortie",)),
    (("NESPRESSO", "LAVAZZA", "MAHLKOENIG", "BUNN"), "Cafe / Materiel bar", ("Sortie",)),
    (("BRAGARD", "ROBUR"), "Tenues / Uniformes", ("Sortie",)),
    (("KILOUTOU", "LOXAM"), "Location materiel", ("Sortie",)),
    (("UBER EATS", "DELIVEROO", "JUST EAT", "UBER "), "Plateformes / Commissions", ("Sortie",)),
    (("DPD", "CHRONOPOST", "COLISSIMO", "LA POSTE", "MONDIAL RELAY", "GLS", "UPS", "DHL"), "Logistique / Transport", ("Sortie",)),
    (("MICROSOFT", "OFFICE 365", "AZURE", "GOOGLE", "WORKSPACE", "GSUITE", "ADOBE", "CREATIVE CLOUD", "CANVA", "NOTION", "SLACK"), "SaaS / Informatique", ("Sortie",)),
    (("SACEM", "SPRE"), "Droits d'auteur / Musique d'ambiance", ("Sortie",)),
    (("AMAZON", "AMZN", "FNAC", "LDLC", "MATERIEL.NET", "DARTY", "BOULANGER"), "Fournitures / Materiel", ("Sortie",)),
    (("BRUNEAU", "LYRECO"), "Fournitures de bureau", ("Sortie",)),
    (("PAPREC", "VEOLIA PROPRETE", "SUEZ RECYCLAGE"), "Dechets / Recyclage", ("Sortie",)),
    (("VERISURE", "EPS"), "Securite", ("Sortie",)),
    (("ELIS", "INITIAL"), "Blanchisserie / Linge pro", ("Sortie",)),
    (("RATP", "SNCF", "IDF MOBILITES"), "Transports", ("Sortie",)),
    (("UBER", "UBER EATS", "UBER *"), "Transports", ("Sortie",)),
    (("TOTAL STATION", "ESSO", "SHELL", "AVIA", "TOTALENERGIES", "TOTAL ENERGIES"), "Carburant / Deplacements", ("Sortie",)),
    (("SPB", "PACIFICA", "ASSUR", "ASSURANCE", "ASSURANCE LCL"), "Assurance", ("Sortie",)),
    (("PREFILOC", "FINANCEMENT", "CREDIT"), "Financement / Credit", ("Sortie",)),
    (("ABON LCL ACCESS", "COTISATION CARTE", "COTISATION MENSUELLE CARTE", "OPTION PRO", "COTISATION MENSUELLE"), "Frais bancaires", None),
    (("COMMISSIONS SUR REMISE CB",), "Frais bancaires", None),
    (("RESULTAT ARRETE COMPTE",), "Frais bancaires", None),
    (("RESIDENCE", "LOYER", "ST AN", "LOCATION", "LOCAT"), "Loyer/Location", ("Sortie",)),
    (("GNANAM", "NOUTAM", "FOURNISSEUR"), "Fournisseur", ("Sortie",)),
    (("FRAIS", "AGIOS", "COMMISSION", "ABONNEMENT", "COTISATION CARTE"), "Frais bancaires", None),
    (("CHANTIER", "FACTURE"), "Autre", None),
) + load_vendor_category_rules()

# Group presets for dashboard summaries
CATEGORY_GROUP_PRESETS: Dict[str, Dict[str, Any]] = {
    "default": {
        "label": "Vue standard",
        "groups": {
            "Recettes": {"categories": ("Encaissement",), "types": ("Entree",)},
            "Encaissement & commissions": {
                "categories": ("Encaissement / Commission", "Encaissement mobile", "Frais d'encaissement"),
                "types": None,
            },
            "Transferts & change": {
                "categories": ("Transfert / Paiement mobile", "Transfert / Change"),
                "types": None,
            },
            "Banque & Financement": {
                "categories": ("Banque", "Banque en ligne", "Financement / Credit", "Credit / Financement"),
                "types": ("Sortie",),
            },
            "Fournisseurs alimentaires": {"categories": ("Fournisseur alimentaire",), "types": ("Sortie",)},
            "Fournisseurs": {"categories": ("Fournisseur",), "types": ("Sortie",)},
            "Approvisionnement": {"categories": ("Approvisionnement",), "types": ("Sortie",)},
            "Charge salariale et sociale": {
                "categories": ("Salaires", "Charges sociales", "Retraite / Prevoyance"),
                "types": ("Sortie",),
            },
            "Charges fixes": {
                "categories": ("Loyer/Location", "Telecom", "Abonnements", "Services professionnels"),
                "types": ("Sortie",),
            },
            "Energie & eau": {"categories": ("Energie", "Gaz", "Eau"), "types": ("Sortie",)},
            "Telecom & SaaS": {
                "categories": ("Telecom", "Abonnements", "Abonnements TV", "SaaS / Informatique"),
                "types": ("Sortie",),
            },
            "Assurances": {"categories": ("Assurance",), "types": ("Sortie",)},
            "Fiscalite": {"categories": ("Fiscalite", "Impots et taxes"), "types": ("Sortie",)},
            "Logistique & plateau": {
                "categories": ("Logistique / Transport", "Plateformes / Commissions"),
                "types": ("Sortie",),
            },
            "Boissons & hygiene": {
                "categories": ("Boissons", "Hygiene / Emballages", "Dechets / Recyclage"),
                "types": ("Sortie",),
            },
            "Bar & cafe": {"categories": ("Cafe / Materiel bar",), "types": ("Sortie",)},
            "Tenues & location": {"categories": ("Tenues / Uniformes", "Location materiel"), "types": ("Sortie",)},
            "Fournitures & materiel": {
                "categories": ("Fournitures / Materiel", "Fournitures de bureau"),
                "types": ("Sortie",),
            },
            "Securite & entretien": {
                "categories": ("Securite", "Blanchisserie / Linge pro"),
                "types": ("Sortie",),
            },
            "Transports & deplacements": {
                "categories": ("Transports", "Carburant / Deplacements"),
                "types": ("Sortie",),
            },
            "Financement": {"categories": ("Financement",), "types": ("Sortie",)},
            "Services pro & comptabilite": {
                "categories": ("Comptabilite", "Services professionnels"),
                "types": ("Sortie",),
            },
            "Autres charges": {"categories": ("Autre",), "types": ("Sortie",)},
        },
        "fallback": {"Entree": "Autres recettes", "Sortie": "Autres charges", "default": "Autres"},
    }
}

# SumUp PDF parsing patterns
SUMUP_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
SUMUP_TIME_RE = re.compile(r"^\d{2}:\d{2}$")
SUMUP_STATUS_PREFIXES = (
    "APPROUV",
    "ENTRANT",
    "REMBOURS",
    "ANNUL",
    "REFUS",
)

# Forecast granularity options
ALLOWED_FORECAST_GRANULARITY = {"daily", "weekly", "monthly"}
