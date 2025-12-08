from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

SOURCE = Path("data/eurociel_catalogue_cleaned.csv")
OUTPUT = Path("docs/eurociel_catalogue_ready_for_db.csv")

# 28 catégories de référence
CATEGORIES = [
    "Apéritifs / Fortifiés",
    "Apéro salé / Graines",
    "Bières",
    "Boulangerie / Viennoiserie",
    "Café / Thé / Infusion",
    "Confiserie / Desserts",
    "Conserves / Tomates",
    "Eaux",
    "Effervescents / Champagne",
    "Emballages / Jetables",
    "Frais laitier / Fromages",
    "Fruits / Légumes frais",
    "Huiles / Condiments",
    "Hygiène / Entretien",
    "Laits / Crèmes",
    "Mer / Viandes base",
    "Panés / Apéro salé",
    "Pâtes / Riz / Semoule / Farine",
    "Sauces sucrées cuisine",
    "Softs / Énergisants",
    "Spiritueux",
    "Surgelés légumes",
    "Viandes / Poisson / Charcut",
    "Vins blancs",
    "Vins rosés",
    "Vins rouges",
    "Épicerie sucrée",
    "Épices / Herbes / Bouillons",
]


def word_re(words: list[str]) -> str:
    return r"(" + r"|".join(words) + r")"


def normalize(text: str) -> str:
    norm = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    norm = norm.upper()
    norm = norm.replace(",", ".")
    norm = re.sub(r"[^A-Z0-9.]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


# Règles succinctes pour catégoriser le catalogue
RULES = [
    ("Spiritueux", word_re(["WHISKY", "VODKA", "RUM", "RHUM", "GIN", "TEQUILA", "PASTIS", "COGNAC", "APERITIF", "LIQUEUR", "CAMPARI", "BAILEYS"])),
    ("Effervescents / Champagne", word_re(["CHAMPAGNE", "CREMANT", "PROSECCO", "CAVA", "MO[ËE]T", "VEUVE", "BRUT"])),
    ("Vins rouges", word_re(["VIN ROUGE", "BORDEAUX", "MERLOT", "CABERNET", "SYRAH", "MALBEC", "PINOT", "RGE", r" R\\b"])),
    ("Vins blancs", word_re(["VIN BLANC", "BLANC", "CHARDONNAY", "SAUVIGNON", "RIESLING", "GEWURZ"])),
    ("Vins rosés", word_re(["ROSE", "ROS[ÉE]"])),
    ("Bières", word_re(["BI[ÈE]RE", "BEER", "LAGER", "IPA", "STOUT", "DESPERADOS", "HEINEKEN", "1664", "KRO"])),
    ("Softs / Énergisants", word_re(["SODA", "COCA", "COLA", "FANTA", "SPRITE", "PEPSI", "OASIS", "SCHWEPPES", "TONIC", "LIMONADE", "ICE TEA", "JUS", "NECTAR", "SIROP", "GINGER BEER", "ENERGY", "RED BULL", "MONSTER", "BURN", "MALTA", "VIMTO"])),
    ("Eaux", word_re(["EAU", "WATER", "PERRIER", "CRISTALINE", "EVIAN", "VOLVIC", "BADOIT", "VITTEL"])),
    ("Mer / Viandes base", word_re(["BOEUF", "B[ŒO]UF", "VEAU", "MOUTON", "AGNEAU", "CHEVRE", "POULET", "DINDE", "PINTADE", "VIANDE", "POISSON", "MAQUEREAU", "SARDINE", "CHINCHARD", "BONITE", "MERLU", "MORUE", "STOCKFISH", "TILAPIA", "SAUMON", "CREVETTE", "CRABE", "CALAMAR", "POULPE"])),
    ("Viandes / Poisson / Charcut", word_re(["SAUCISSE", "CHARCUT", "JAMBON", "SALAMI", "BACON", "CHORIZO"])),
    ("Emballages / Jetables", word_re(["GOBELET", "ASSIETTE", "COUVERT", "PAILLE", "SAC", "SACHET", "BARQUETTE", "PLATEAU", "BOITE", "BOX", "CARTON", "FILM", "ALU", "PAPIER", "SERVIETTE", "NAPKIN", "GANT", "OPERCULE", "COUVERCLE", "KRAFT", "RIOBA", "M PRO", "MPRO"])),
    ("Hygiène / Entretien", word_re(["SAVON", "SHAMPOO", "SHAMPOING", "DENTIFRICE", "LINGETTE", "LESSIVE", "DETERGENT", "DESINFECTANT", "JAVEL", "GEL DOUCHE", "BOLDAIR"])),
    ("Huiles / Condiments", word_re(["HUILE", "MAYO", "MAYONNAISE", "KETCHUP", "MOUTARDE", "VINAIGRE", "SOJA", "TERIYAKI", "SAUCE", "CONDIMENT", "HARISSA", "TABASCO", "HEINZ", "AMORA", "MAILLE"])),
    ("Conserves / Tomates", word_re(["CONSERVE", "TOMATE", "PULPE", "COULIS", "CONCENTR", "SARDINE", "THON", "MAQUEREAU", "PILCHARD", "MUTTI", "CIRIO"])),
    ("Épices / Herbes / Bouillons", word_re(["PIMENT", "CHILI", "POIVRE", "SEL", "CURRY", "CURCUMA", "PAPRIKA", "GINGEMBRE", "AIL", "OIGNON", "MUSCADE", "CANNELLE", "GIROFLE", "HERBES", "THYM", "LAURIER", "EPICE", "BOUILLON", "CUBE", "MAGGI", "VEGETA", "JUMBO", "KNORR"])),
    ("Pâtes / Riz / Semoule / Farine", word_re(["RIZ", "SEMOULE", "COUSCOUS", "BULGUR", "FARINE", "FUFU", "GARI", "SPAGHETTI", "MACARONI", "PENNE", "NOUILLE", "VERMICELLE"])),
    ("Huiles / Condiments", word_re(["HUILE"])),  # doublon léger pour attraper les huiles simples
    ("Épicerie sucrée", word_re(["SUCRE", "MIEL", "CONFITURE", "CACAO", "CHOCOLAT EN POUDRE", "NUTELLA", "PATE A TARTINER", "DESSERT", "GELATINE", "ENTREMETS", "VANIL"])),
    ("Confiserie / Desserts", word_re(["BONBON", "BISCUIT", "COOKIE", "GAUFRE", "CARAMEL", "SUCETTE", "CHEWING", "HARIBO", "GLACE", "SORBET", "ESQUIMAU", "MAGNUM", "MR FREEZE", "CHOCOLAT"])),
    ("Boulangerie / Viennoiserie", word_re(["PAIN", "BAGUETTE", "BRIOCHE", "CROISSANT", "VIENNOISERIE", "BUN", "WRAP", "TORTILLA", "NAAN", "PITA"])),
    ("Café / Thé / Infusion", word_re(["CAFE", "CAFÉ", "NESCAFE", "NESPRESSO", "THE", "THÉ", "INFUSION", "TISANE", "CAPPUCCINO"])),
    ("Softs / Énergisants", word_re(["MALTA"])),
    ("Fruits / Légumes frais", word_re(["FRAIS", "LÉGUME", "LEGUME", "FRUIT", "BANANE", "PLANTAIN", "OIGNON", "AUBERGINE", "COURGETTE", "POMME DE TERRE"])),
    ("Surgelés légumes", word_re(["SURGEL", "CONGE", "FROZEN"])),
]


def categorize(label: str) -> str:
    for cat, pattern in RULES:
        if re.search(pattern, label, re.I):
            return cat
    return "Épicerie sucrée"


def build_barcodes(df: pd.DataFrame) -> pd.Series:
    cats = sorted(df["categorie"].unique().tolist())
    prefix = {cat: f"{i+1:02d}" for i, cat in enumerate(cats)}
    counters = {cat: 0 for cat in cats}
    codes = []
    for _, row in df.iterrows():
        cat = row["categorie"]
        counters[cat] += 1
        codes.append(prefix[cat] + f"{counters[cat]:03d}")
    return pd.Series(codes, index=df.index)


def is_noise(label: str) -> bool:
    # Rejette les lignes purement numériques, adresses, pages, mentions hors produits
    if not re.search(r"[A-Z]", label):
        return True
    if re.fullmatch(r"[0-9X/ .+-]+", label):
        return True
    if re.fullmatch(r"[0-9X/ .+-]+KG", label):
        return True
    noise_tokens = ["AVENUE", "GARGES", "TEL", "SITE", "EMAIL", "WWW", "INFO", "FACEBOOK", "PAGE", "TARIF", "STANDARD", "NOUTAM", "INCONTOURNABLE", "DOCUMENTS"]
    if any(tok in label for tok in noise_tokens):
        return True
    # Lignes très courtes (1 token de 2 lettres) : souvent du bruit
    tokens = label.split()
    if len(tokens) == 1 and len(tokens[0]) <= 3:
        return True
    # Exiger au moins un token alphabétique de longueur >=3
    if not any(re.search(r"[A-Z]{3,}", t) for t in tokens):
        return True
    packaging = {"SACHET", "CARTON", "VRAC", "OUVERT", "OUVERTE", "IWP", "SURGELE", "SURGEL", "CONGELE", "FROZEN", "PACK", "SACS", "PCS"}
    letter_only = [t for t in tokens if re.fullmatch(r"[A-Z]+", t)]
    if letter_only and all(t in packaging for t in letter_only):
        return True
    meaningful = [t for t in tokens if re.search(r"[A-Z]{3,}", t) and t not in packaging and not re.fullmatch(r"[0-9X]+PCS?", t)]
    if not meaningful:
        return True
    return False


def main():
    df = pd.read_csv(SOURCE)
    df["nom_clean"] = df["nom"].apply(normalize)
    df = df[~df["nom_clean"].apply(is_noise)].reset_index(drop=True)
    df["categorie"] = df["nom_clean"].apply(categorize)
    df["tva"] = 5.5  # défaut
    df["prix_ttc"] = 0  # pas de prix catalogue fourni
    df["barcode_placeholder"] = build_barcodes(df)

    out_cols = [
        "nom",
        "nom_clean",
        "categorie",
        "tva",
        "prix_ttc",
        "barcode_placeholder",
        "ref_catalogue",
        "format_suggere",
        "code_ean_provisoire",
        "source",
    ]
    df[out_cols].to_csv(OUTPUT, index=False)
    print(f"Fichier généré: {OUTPUT} ({len(df)} lignes)")


if __name__ == "__main__":
    main()
