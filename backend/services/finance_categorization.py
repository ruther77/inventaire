"""
Regles et utilitaires pour la categorisation automatique des transactions financieres.

Contient:
- TARGET_CATEGORIES: Taxonomie a 12 postes + encaissements
- BASE_CATEGORY_RULES: ~70 regles de mots-cles pour auto-categorisation
- SOURCE_TO_TARGET: Mapping categories sources -> taxonomie cible
- Fonctions de normalisation de libelles bancaires
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Tuple

# =============================================================================
# TAXONOMIE CIBLE (12 postes + encaissements)
# =============================================================================

TARGET_CATEGORIES: Dict[str, str] = {
    "encaissements": "Encaissements",
    "achats_fournisseurs": "Achats et frais fournisseurs",
    "salaires_remunerations": "Salaires & remunerations",
    "charges_sociales": "Charges sociales",
    "impots_taxes": "Impots & taxes",
    "frais_generaux": "Frais generaux",
    "transport_deplacement": "Transport & deplacement",
    "immobilisations_investissements": "Immobilisations & investissements",
    "loyer_immobilier": "Loyer & immobilier",
    "marketing_communication": "Marketing & communication",
    "frais_financiers": "Frais financiers",
    "informatique_telecom": "Informatique & telecom",
    "remboursements_clients": "Remboursements clients & litiges",
    "prestations_externes": "Prestations externes",
}

# Liste ordonnee pour affichage
TARGET_CATEGORIES_LIST: List[str] = [
    "Achats et frais fournisseurs",
    "Salaires & remunerations",
    "Charges sociales",
    "Impots & taxes",
    "Frais generaux",
    "Transport & deplacement",
    "Immobilisations & investissements",
    "Loyer & immobilier",
    "Marketing & communication",
    "Frais financiers",
    "Informatique & telecom",
    "Remboursements clients & litiges",
    "Prestations externes",
]

# =============================================================================
# REGLES DE CATEGORISATION PAR MOTS-CLES
# Format: (tuple_keywords, categorie_source, tuple_types_autorises | None)
# Si types_autorises est None, la regle s'applique dans les deux sens
# =============================================================================

BASE_CATEGORY_RULES: Tuple[Tuple[Tuple[str, ...], str, Tuple[str, ...] | None], ...] = (
    # --- Encaissements ---
    (("REMISE CB", "REM CB", "CB NO", "CB ", "CARTE"), "Encaissement", ("Entree",)),
    (("REMISE CB NO", "REMISE CB N°"), "Encaissement", ("Entree",)),
    (("CB12",), "Encaissement", ("Entree",)),
    (("DEPOT", "VIR RECU", "VERSEMENT", "REMISE CHEQUE", "ALIMENTATION"), "Encaissement", ("Entree",)),
    (("LYDIA", "PAYLIB"), "Encaissement mobile", ("Entree",)),
    (("VOTRE REMISE SUR PRODUITS",), "Encaissement", ("Entree",)),

    # --- Financement / Credit ---
    (("VERSEMENT ALS",), "Financement / Credit", None),
    (("VIR SEPA M. TCHAKOUA", "VIR SEPA RECU /DE MME", "VIR SEPA RECU /DE ZOUBIR", "VIR SEPA RECU /DE TCHAKOUA", "VIR SEPA NOUTAM", "Virement entrant", "VIR INST", "VIREMENT INST"), "Financement / Credit", None),
    (("VIR INST", "VIREMENT INST", "VIR INST."), "Financement / Credit", None),
    (("VIRT CPTE", "VIR CPTE A CPTE", "VIRT CPTE A CPTE", "VIREMENT ENTRANT"), "Financement / Credit", None),
    (("ECHEANCE PRET", "ECHEANCE PRET"), "Financement / Credit", ("Sortie",)),
    (("PREFILOC", "FINANCEMENT", "CREDIT"), "Financement / Credit", ("Sortie",)),

    # --- Frais d'encaissement ---
    (("REMISE CB", "REMISE CB NO", "REMISE CB N°"), "Frais d'encaissement", ("Sortie",)),
    (("STRIPE", "SUMUP", "ZETTLE", "PAYPAL"), "Frais d'encaissement", ("Sortie",)),
    (("AVEM", "LOCATION TPE", "TPE AVEM"), "Frais d'encaissement", ("Sortie",)),

    # --- Salaires ---
    (("SALAI", "SALAIRE", "PAYE", "PAYE"), "Salaires", None),
    (("SALAIRE", "PAYE"), "Salaires", ("Sortie",)),
    (("MASSA ANGELE",), "Salaires", ("Sortie",)),

    # --- Charges sociales ---
    (("URSSAF",), "Charges sociales", ("Sortie",)),
    (("AGIRC", "ARRCO", "MALAKOFF", "KLESIA", "HUMANIS"), "Retraite / Prevoyance", ("Sortie",)),

    # --- Fiscalite ---
    (("DGFIP", "IMPOTS", "TVA", "CFE", "CET"), "Fiscalite", ("Sortie",)),
    (("DRFIP",), "Fiscalite", ("Sortie",)),

    # --- Energie ---
    (("TOTALENERGIES", "TOTAL", "TOTAL ENERGIES", "TEF"), "Energie", ("Sortie",)),
    (("EDF", "E.D.F."), "Energie", ("Sortie",)),
    (("ENGIE", "GAZ DE FRANCE"), "Energie", ("Sortie",)),
    (("GAZEL", "GAZELENERGIE"), "Energie", None),
    (("ENI", "ILEK", "PLANETE OUI", "MINT ENERGIE"), "Energie", None),
    (("EAU DE PARIS", "VEOLIA EAU", "SUEZ EAU", "SAUR"), "Eau", None),

    # --- Carburant / Deplacements ---
    (("TOTALENERGIES CHARGING", "DIGITAL CHARGING", "CHARGING"), "Carburant / Deplacements", ("Sortie",)),
    (("TOTAL STATION", "ESSO", "SHELL", "AVIA"), "Carburant / Deplacements", ("Sortie",)),

    # --- Loyer / Location ---
    (("RESIDENCE", "LOYER", "LOCATION", "LOCAT", "ST AN"), "Loyer/Location", None),

    # --- Telecom ---
    (("FREE", "FREE PRO"), "Telecom", None),
    (("SFR", "SFR BUSINESS"), "Telecom", None),
    (("ORANGE", "ORANGE PRO"), "Telecom", None),
    (("BOUYGUES", "BBOX", "BYTEL", "PRLV SEPA BOUYGUES"), "Telecom", None),

    # --- Abonnements ---
    (("CANAL", "CANALSAT"), "Abonnements TV", ("Sortie",)),
    (("NETFLIX", "SPOTIFY", "ABONNEMENT"), "Abonnements", ("Sortie",)),

    # --- Assurance ---
    (("SPB", "PACIFICA", "CREDIT AGRICOLE ASSURANCE", "AXA", "ALLIANZ", "MAIF", "MAAF", "MATMUT", "HISCOX", "ASSURANCE LCL"), "Assurance", ("Sortie",)),

    # --- Comptabilite ---
    (("HMD", "AUDIT", "EXPERT COMPTABLE", "CABINET COMPTABLE", "HMD AUDIT ET CONSEIL"), "Comptabilite", ("Sortie",)),

    # --- Approvisionnement ---
    (("REAPRO",), "Approvisionnement", None),
    (("METRO", "PROMOCASH", "TRANS GOURMET", "TRANSGOURMET", "DAVIGEL", "SYSCO", "BOUCH. BVS", "BOUCH BVS", "BOUCH", "GNANAM", "EXOTI", "EUROCIEL", "KEDY PACK", "TAI YAT", "RETRAIT", "LINCONTOURNABLE", "LEADER PRICE", "LE VINCI", "ACHAT"), "Approvisionnement", None),

    # --- Fournitures / Materiel ---
    (("CENTRAKOR",), "Fournitures / Materiel", ("Sortie",)),
    (("AMAZON", "AMZN", "FNAC", "LDLC", "MATERIEL.NET", "DARTY", "BOULANGER"), "Fournitures / Materiel", ("Sortie",)),
    (("LEROY MERLIN", "ADEO*LEROY"), "Fournitures / Materiel", ("Sortie",)),
    (("ETHAN",), "Fournitures / Materiel", ("Sortie",)),
    (("BRUNEAU", "LYRECO"), "Fournitures de bureau", ("Sortie",)),

    # --- Boissons ---
    (("FRANCE BOISSONS", "C10", "COCA", "COCA COLA", "COCA-COLA", "HEINEKEN FRANCE", "LES GRANDS CHAIS", "CASTEL FRERES"), "Boissons", ("Sortie",)),

    # --- Hygiene / Emballages ---
    (("RAJAPACK", "RAJA", "PAREDES", "PROD'HYGIENE", "PRO HYGIENE", "HYGIAL"), "Hygiene / Emballages", ("Sortie",)),

    # --- Cafe / Materiel bar ---
    (("NESPRESSO", "LAVAZZA", "MAHLKOENIG", "BUNN"), "Cafe / Materiel bar", ("Sortie",)),

    # --- Tenues / Uniformes ---
    (("BRAGARD", "ROBUR"), "Tenues / Uniformes", ("Sortie",)),

    # --- Location materiel ---
    (("KILOUTOU", "LOXAM"), "Location materiel", ("Sortie",)),

    # --- Plateformes / Commissions ---
    (("UBER EATS", "DELIVEROO", "JUST EAT", "UBER "), "Plateformes / Commissions", ("Sortie",)),

    # --- Logistique / Transport ---
    (("DPD", "CHRONOPOST", "COLISSIMO", "LA POSTE", "MONDIAL RELAY", "GLS", "UPS", "DHL"), "Logistique / Transport", ("Sortie",)),

    # --- SaaS / Informatique ---
    (("MICROSOFT", "OFFICE 365", "AZURE", "GOOGLE", "WORKSPACE", "GSUITE", "ADOBE", "CREATIVE CLOUD", "CANVA", "NOTION", "SLACK"), "SaaS / Informatique", ("Sortie",)),

    # --- Droits d'auteur / Musique ---
    (("SACEM", "SPRE"), "Droits d'auteur / Musique d'ambiance", ("Sortie",)),

    # --- Dechets / Recyclage ---
    (("PAPREC", "VEOLIA PROPRETE", "SUEZ RECYCLAGE"), "Dechets / Recyclage", ("Sortie",)),

    # --- Securite ---
    (("VERISURE", "EPS"), "Securite", ("Sortie",)),

    # --- Blanchisserie ---
    (("ELIS", "INITIAL"), "Blanchisserie / Linge pro", ("Sortie",)),

    # --- Transports ---
    (("RATP", "SNCF", "IDF MOBILITES"), "Transports", ("Sortie",)),
    (("UBER", "UBER EATS", "UBER *"), "Transports", ("Sortie",)),

    # --- Frais bancaires ---
    (("LCL A LA CARTE PRO",), "Frais bancaires", None),
    (("ANCIEN SOLDE", "BLOCAGE SUR PCE", "MOUVEMENT", "PARIS EUR"), "Frais bancaires", None),
    (("ABON LCL ACCESS", "COTISATION CARTE", "COTISATION MENSUELLE CARTE", "OPTION PRO", "COTISATION MENSUELLE"), "Frais bancaires", ("Sortie",)),
    (("COMMISSIONS SUR REMISE CB",), "Frais bancaires", ("Sortie",)),
    (("RESULTAT ARRETE COMPTE",), "Frais bancaires", None),
    (("FRAIS", "AGIOS", "COMMISSION", "ABONNEMENT", "COTISATION CARTE"), "Frais bancaires", None),

    # --- Fournisseur generique ---
    (("GNANAM", "NOUTAM", "FOURNISSEUR"), "Fournisseur", ("Sortie",)),

    # --- Autre ---
    (("CHANTIER", "FACTURE"), "Autre", None),
)

# =============================================================================
# MAPPING CATEGORIES SOURCES -> TAXONOMIE CIBLE
# =============================================================================

SOURCE_TO_TARGET: Dict[str, str] = {
    # Recettes
    "Encaissement": "encaissements",
    "Encaissement mobile": "encaissements",
    "Revenu": "encaissements",
    "Revenu / Encaissement": "encaissements",
    "Transfert / Paiement mobile": "encaissements",
    "Autres recettes": "encaissements",

    # Achats / fournisseurs / stocks
    "Approvisionnement": "achats_fournisseurs",
    "Fournisseur": "achats_fournisseurs",
    "Fournisseurs alimentaires": "achats_fournisseurs",
    "Boissons": "achats_fournisseurs",
    "Courses / Alimentation": "achats_fournisseurs",
    "Hygiene / Emballages": "achats_fournisseurs",
    "Hygiene / Produits entretien": "achats_fournisseurs",
    "Cafe / Materiel bar": "achats_fournisseurs",
    "Cafe / Bar": "achats_fournisseurs",
    "Tenues / Uniformes": "achats_fournisseurs",
    "Tenues professionnelles": "achats_fournisseurs",
    "Fournitures / Materiel": "achats_fournisseurs",
    "Materiel / Outillage": "achats_fournisseurs",
    "Materiel electrique": "achats_fournisseurs",
    "Plomberie / Batiment": "achats_fournisseurs",
    "Fournitures / Informatique": "achats_fournisseurs",
    "Fournitures de bureau": "achats_fournisseurs",
    "Materiel informatique": "achats_fournisseurs",
    "Materiel / Batiment": "achats_fournisseurs",
    "Repas / Restauration": "achats_fournisseurs",

    # Salaires / social / RH
    "Salaires": "salaires_remunerations",
    "Charges sociales": "charges_sociales",
    "Retraite / Prevoyance": "charges_sociales",
    "Prevoyance / Mutuelle": "charges_sociales",
    "Paie / RH": "salaires_remunerations",
    "Recrutement": "salaires_remunerations",

    # Impots / taxes / administratif
    "Fiscalite": "impots_taxes",
    "Impots et taxes": "impots_taxes",
    "Administratif": "impots_taxes",
    "TVA": "impots_taxes",

    # Frais generaux
    "Autre": "frais_generaux",
    "Dechets / Recyclage": "frais_generaux",
    "Nettoyage / Dechets": "frais_generaux",
    "Blanchisserie / Linge pro": "frais_generaux",
    "Blanchisserie / Entretien linge": "frais_generaux",
    "Assurance": "frais_generaux",
    "Securite": "frais_generaux",
    "Securite / Alarme": "frais_generaux",
    "Moyens de paiement": "frais_generaux",
    "Divers": "frais_generaux",
    "Sante / Personnel": "frais_generaux",
    "Energie": "frais_generaux",
    "Eau": "frais_generaux",
    "Autres charges": "frais_generaux",
    "Impression / Papeterie": "frais_generaux",

    # Prestations et services pro
    "Comptabilite": "prestations_externes",
    "Prestations externes": "prestations_externes",
    "Legal / Conseil": "prestations_externes",
    "Signature / Gestion documentaire": "prestations_externes",
    "Maintenance / Froid": "prestations_externes",
    "Communication": "prestations_externes",
    "Formation / Securite": "prestations_externes",

    # Financier / banque
    "Frais bancaires": "frais_financiers",
    "Frais d'encaissement": "frais_financiers",
    "Banque": "frais_financiers",
    "Banque en ligne": "frais_financiers",
    "Financement / Credit": "frais_financiers",
    "Credit / Financement": "frais_financiers",
    "Encaissement / Commission": "frais_financiers",
    "Transfert / Change": "frais_financiers",

    # Telecom / IT
    "Telecom": "informatique_telecom",
    "SaaS / Informatique": "informatique_telecom",
    "Logiciels / Abonnements": "informatique_telecom",
    "Logiciels": "informatique_telecom",
    "Stockage cloud": "informatique_telecom",
    "Hebergement / Nom de domaine": "informatique_telecom",
    "Informatique / Telecom": "informatique_telecom",

    # Marketing
    "Emailing": "marketing_communication",
    "Site web": "marketing_communication",
    "Site web / E-commerce": "marketing_communication",
    "Publicite": "marketing_communication",
    "Publicite / Reseaux sociaux": "marketing_communication",
    "Musique": "marketing_communication",
    "Abonnements TV": "marketing_communication",
    "Abonnements": "marketing_communication",
    "Droits d'auteur / Musique d'ambiance": "marketing_communication",

    # Transport / deplacements
    "Logistique / Transport": "transport_deplacement",
    "Transports": "transport_deplacement",
    "Deplacements": "transport_deplacement",
    "Carburant / Deplacements": "transport_deplacement",
    "Carburant": "transport_deplacement",
    "Frais deplacement": "transport_deplacement",
    "Hebergement": "transport_deplacement",
    "Plateformes / Commissions": "transport_deplacement",

    # Immobilisations / loyer
    "Location materiel": "immobilisations_investissements",
    "Loyer/Location": "loyer_immobilier",
    "Bureaux": "loyer_immobilier",

    # Remboursements
    "Remboursement": "remboursements_clients",
    "Avoir": "remboursements_clients",
    "Litige": "remboursements_clients",
}

# =============================================================================
# FONCTIONS DE NORMALISATION
# =============================================================================


def strip_accents(text: str) -> str:
    """Supprime les accents d'une chaine."""
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def normalize_label(label: str) -> str:
    """Normalisation legere : upper + espaces condenses."""
    label = (label or "").upper()
    label = re.sub(r"\s+", " ", label).strip()
    return label


def stem_label(label: str) -> str:
    """Forme tronquee pour regrouper les variantes (dates, montants, refs numeriques)."""
    lab = normalize_label(label)
    # retire les dates dd/mm/yy ou dd.mm.yyyy
    lab = re.sub(r"\b\d{2}[/.]\d{2}[/.]\d{2,4}\b", "", lab)
    # retire les montants type 123,45 ou 1.234,56
    lab = re.sub(r"\b\d+[.,]\d{2}\b", "", lab)
    # retire les longues sequences numeriques (>=4 chiffres)
    lab = re.sub(r"\b\d{4,}\b", "", lab)
    lab = re.sub(r"\s+", " ", lab).strip()
    return lab


def canonical(label: str) -> str:
    """
    Forme canonique pour regrouper des libelles similaires.
    - Supprime accents
    - Supprime chiffres et caracteres speciaux
    - Tronque chaque token a 6 caracteres
    - Garde les 5 premiers tokens
    """
    label = strip_accents(label.upper())
    label = re.sub(r"[0-9]", " ", label)
    label = re.sub(r"[^A-Z]+", " ", label)
    tokens = [tok[:6] for tok in label.split() if tok]
    return " ".join(tokens[:5])


def _normalize_for_matching(text: str) -> str:
    """Normalise pour le matching de mots-cles."""
    return re.sub(r"[^A-Z0-9]", "", text.upper())


# =============================================================================
# FONCTIONS DE CATEGORISATION
# =============================================================================


def match_category_rules(
    direction: str,
    label: str,
    rules: Tuple[Tuple[Tuple[str, ...], str, Tuple[str, ...] | None], ...] = BASE_CATEGORY_RULES,
) -> Optional[str]:
    """
    Applique les regles de categorisation sur un libelle.

    Args:
        direction: "IN" ou "OUT" (sens de la transaction)
        label: Libelle bancaire
        rules: Tuple de regles a appliquer

    Returns:
        Code categorie source si match, None sinon
    """
    upper = label.upper()
    normalized = _normalize_for_matching(label)
    entry_type = "Entree" if direction == "IN" else "Sortie"

    for keywords, category_name, allowed_types in rules:
        if allowed_types and entry_type not in allowed_types:
            continue
        if any(k.upper() in upper or _normalize_for_matching(k) in normalized for k in keywords):
            return category_name

    return None


def infer_target_category(category_name: str, entry_type: str = "Sortie") -> str:
    """
    Infere la categorie cible (taxonomie 12 postes) a partir d'un nom de categorie source.

    Args:
        category_name: Nom de la categorie source
        entry_type: "Entree" ou "Sortie"

    Returns:
        Code de la categorie cible
    """
    # D'abord chercher dans le mapping explicite
    if category_name in SOURCE_TO_TARGET:
        return SOURCE_TO_TARGET[category_name]

    # Sinon heuristique
    cat_l = category_name.lower()

    if entry_type == "Entree":
        return "encaissements"

    if any(k in cat_l for k in ("banque", "frais banc", "commission", "encaissement / commission", "moyens de paiement")):
        return "frais_financiers"
    if any(k in cat_l for k in ("financement", "credit")):
        return "frais_financiers"
    if any(k in cat_l for k in ("approvisionnement", "boissons", "courses", "fournitures", "materiel", "outillage", "plomberie", "batiment", "electrique", "emballages", "hygiene", "dechets", "cafe", "bar")):
        return "achats_fournisseurs"
    if any(k in cat_l for k in ("comptabilite", "compta", "prestations externes", "juridique", "signature", "documentaire", "formation", "recrutement", "communication", "maintenance")):
        return "prestations_externes"
    if any(k in cat_l for k in ("telecom", "saas", "logiciels", "stockage", "hebergement", "nom de domaine", "cloud", "informatique")):
        return "informatique_telecom"
    if any(k in cat_l for k in ("publicite", "emailing", "site web", "e-commerce", "musique", "abonnement tv", "reseaux sociaux")):
        return "marketing_communication"
    if any(k in cat_l for k in ("transports", "transport", "deplacements", "carburant", "frais deplacement", "logistique", "uber", "taxi", "train", "avion", "hotel", "hebergement")):
        return "transport_deplacement"
    if any(k in cat_l for k in ("assurance", "blanchisserie", "securite", "nettoyage", "dechets", "hygiene", "frais generaux", "autres charges", "divers", "sante")):
        return "frais_generaux"
    if any(k in cat_l for k in ("charges sociales", "urssaf", "retraite", "prevoyance", "mutuelle", "paie / rh", "paie", "rh")):
        return "charges_sociales"
    if any(k in cat_l for k in ("salaires", "remunerations", "primes", "indemnites")):
        return "salaires_remunerations"
    if any(k in cat_l for k in ("impot", "taxe", "tva", "cfe", "cvae", "fiscalite", "administratif")):
        return "impots_taxes"
    if any(k in cat_l for k in ("loyer", "bureaux", "immobilier", "locatif", "copropriete")):
        return "loyer_immobilier"
    if any(k in cat_l for k in ("location materiel", "immobilisations", "investissements", "amenagement")):
        return "immobilisations_investissements"
    if any(k in cat_l for k in ("remboursement", "avoir", "litige", "sav")):
        return "remboursements_clients"

    return "frais_generaux"


def auto_categorize(direction: str, label: str) -> Tuple[Optional[str], str]:
    """
    Categorise automatiquement une transaction.

    Args:
        direction: "IN" ou "OUT"
        label: Libelle bancaire

    Returns:
        Tuple (categorie_source, categorie_cible_code)
    """
    entry_type = "Entree" if direction == "IN" else "Sortie"

    # Essayer les regles de mots-cles
    source_cat = match_category_rules(direction, label)

    if source_cat:
        target_code = infer_target_category(source_cat, entry_type)
        return source_cat, target_code

    # Fallback
    if direction == "IN":
        return None, "encaissements"
    return None, "frais_generaux"


# =============================================================================
# REGLES SIMPLIFIEES POUR SUGGESTIONS UI
# =============================================================================

SUGGESTION_RULES: List[Tuple[List[str], str]] = [
    (["URSSAF", "KLESIA", "MALAKOFF", "MUTUELLE"], "Charges sociales"),
    (["SALAIRE", "PAYE", "PRIME", "INDEMNITE"], "Salaires & remunerations"),
    (["DGFIP", "IMPOT", "CFE", "CVAE", "TAXE", "TVA"], "Impots & taxes"),
    (["AGIOS", "FRAIS BAN", "FRAIS CB", "COMMISSION", "INTERET", "INTERETS", "TAUX"], "Frais financiers"),
    (["LOYER", "RESIDENCE", "LOCATION", "BAIL", "ST AN"], "Loyer & immobilier"),
    (["TOTAL", "ESSO", "SHELL", "AVIA", "CARBURANT", "UBER", "SNCF", "IDF", "RATP", "BOLT"], "Transport & deplacement"),
    (["SFR", "ORANGE", "FREE", "BOUYGUES", "GOOGLE", "MICROSOFT", "AZURE", "AWS", "CLOUD", "SLACK", "NOTION", "TELECOM"], "Informatique & telecom"),
    (["META", "FACEBOOK", "GOOGLE ADS", "ADS", "TIKTOK", "LINKEDIN", "MAILJET", "SENDINBLUE", "MAILCHIMP"], "Marketing & communication"),
    (["METRO", "PROMOCASH", "TRANSGOURMET", "SYSCO", "GNANAM", "EXOTI", "EUROCIEL", "RAJAPACK", "RAJA", "LYRECO", "AMAZON", "COCA", "FRANCE BOISSONS", "C10"], "Achats et frais fournisseurs"),
    (["HMD", "AUDIT", "EXPERT", "CABINET", "COMPTABLE", "PRESTATION", "SOUS-TRAITANCE", "CONSEIL"], "Prestations externes"),
    (["ASSUR", "ASSURANCE", "PACIFICA", "AXA", "ALLIANZ", "MAIF", "MATMUT"], "Frais generaux"),
    (["FACTURE", "MACHINE", "EQUIPEMENT", "MATERIEL", "AMENAGEMENT", "TRAVAUX", "ORDINATEUR", "IMPRIMANTE"], "Immobilisations & investissements"),
    (["REMBOURSEMENT", "AVOIR", "LITIGE", "SAV", "RETRO"], "Remboursements clients & litiges"),
]


def suggest_category(label: str) -> Optional[str]:
    """Suggere une categorie basee sur les mots-cles simples."""
    upper = label.upper()
    for keywords, cat in SUGGESTION_RULES:
        if any(kw in upper for kw in keywords):
            return cat
    return None
