from __future__ import annotations

from pathlib import Path

import pandas as pd


PREPARED_PATH = Path("docs/articles_prix_ttc_cond_inclus_prepared.csv")
OUTPUT_PATH = Path("docs/articles_prix_ttc_ready_for_db.csv")

# Catégories master (28)
CATEGORIES_MASTER = [
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

# Règles de mapping (ordre prioritaire)
CATEGORY_RULES = [
    ("Spiritueux", ["WHISKY", "VODKA", "RHUM", "RUM", "GIN", "TEQUILA", "COGNAC", "ARMAGNAC", "PASTIS", "MARTINI", "VERMOUTH", "RICARD", "APERITIF"]),
    ("Effervescents / Champagne", ["CHAMPAGNE", "CREMANT", "CREMANT", "PROSECCO", "CAVA", "MOET", "MOËT", "VEUVE", "BRUT"]),
    ("Vins rouges", ["VIN ROUGE", "BORDEAUX", "BOURGOGNE", "MEDOC", "MÉDOC", "MERLOT", "CABERNET", "MALBEC", "SYRAH", "PINOT", "ROUGE"]),
    ("Vins blancs", ["VIN BLANC", "BLANC", "CHARDONNAY", "SAUVIGNON", "RIESLING", "GEWURZ", "GEWURZTRAMINER"]),
    ("Vins rosés", ["ROSE", "ROSÉ"]),
    ("Bières", ["BIERE", "BIÈRE", "BEER", "LAGER", "IPA", "STOUT", "BLONDE", "BRUNE", "AMBRE", "DESPERADOS", "HEINEKEN", "1664", "KRO"]),
    ("Apéritifs / Fortifiés", ["PORTO", "SHERRY", "MUSCAT", "APEROL", "CAMPARI"]),
    ("Softs / Énergisants", ["COCA", "COLA", "FANTA", "SPRITE", "SEVEN UP", "7UP", "PEPSI", "GINGER BEER", "SODA", "ENERGY", "RED BULL", "MONSTER", "BURN", "SIROP", "JUS", "NECTAR", "JUS", "TAMPICO", "MALTA", "MALTA GUINNESS"]),
    ("Eaux", ["EAU", "WATER", "PERIER", "PERRIER", "CRISTALINE", "VITTEL", "EVIAN", "VOLVIC"]),
    ("Café / Thé / Infusion", ["CAFE", "CAFÉ", "NESCAFE", "NESCafe", "NESPRESSO", "THE", "THÉ", "INFUSION", "TISANE", "CAPPUCCINO", "MILO"]),
    ("Boulangerie / Viennoiserie", ["PAIN", "BAGUETTE", "BRIOCHE", "CROISSANT", "VIENNOISERIE", "BUN", "WRAP", "TORTILLA", "NAAN"]),
    ("Confiserie / Desserts", ["BONBON", "BISCUIT", "COOKIE", "CHOCOLAT", "CARAMEL", "GATEAU", "GÂTEAU", "CONFITURE", "MIEL", "DESSERT", "GLACE", "SORBET", "CANDY", "GAUFRE"]),
    ("Épicerie sucrée", ["SUCRE", "SIROP DE CANNE", "CACAO", "CHOCOLAT EN POUDRE", "NUTELLA", "DULCE"]),
    ("Apéro salé / Graines", ["CHIPS", "ARACHIDE", "ARACHIDES", "CACAHUETE", "CACAHUETE", "PISTACHE", "NOIX DE CAJOU", "GRAINE"]),
    ("Panés / Apéro salé", ["NUGGET", "PANE", "PANÉ", "CORDON BLEU"]),
    ("Emballages / Jetables", ["GOBELET", "ASSIETTE", "COUVERT", "SAC", "PAPIER", "ALU", "BARQUETTE", "BOITE", "BOÎTE", "FILM", "JETABLE", "PAILLE", "BOBINE", "M PRO", "MPRO", "ARO"]),
    ("Hygiène / Entretien", ["SAVON", "SHAMPOO", "SHAMPOING", "DENTIFRICE", "LINGETTE", "DEO", "DEODORANT", "LESSIVE", "DETERGENT", "ECLAIRCISSANT", "LAIT DE BEAUTE", "CREME", "PAPIER TOILETTE", "MOUCHOIR", "SERVIETTE", "JAVEL", "DESINFECTANT", "NETTOYANT"]),
    ("Fruits / Légumes frais", ["FRAIS", "LEGUME", "LÉGUME", "GOMBO", "PIMENT FRAIS", "OIGNON", "TOMATE FRAICHE", "BANANE", "PLANTAIN"]),
    ("Pâtes / Riz / Semoule / Farine", ["RIZ", "SEMOULE", "COUSCOUS", "PATE", "PÂTE", "PATES", "PÂTES", "SPAGHETTI", "FARINE", "BULGUR", "FONIO"]),
    ("Huiles / Condiments", ["HUILE", "MAYONNAISE", "KETCHUP", "MOUTARDE", "VINAIGRE", "SAUCE SOJA", "SAUCE PIMENT", "CONDIMENT"]),
    ("Conserves / Tomates", ["CONSERVE", "TOMATE", "PULPE", "COULIS", "CONCENTRE", "SARDINE", "THON", "MAQUEREAU"]),
    ("Épices / Herbes / Bouillons", ["MAGGI", "CUBE", "BOUILLON", "PIMENT", "POIVRE", "CURRY", "THYME", "THYM", "HERBES", "EPICE", "ÉPICE", "OGBONO", "SOUBALA"]),
    ("Laits / Crèmes", ["LAIT", "CREME", "CRÈME", "LAIT CONCENTRE", "LAIT EVAPORE"]),
    ("Frais laitier / Fromages", ["FROMAGE", "YAOURT", "CHEESE"]),
    ("Mer / Viandes base", ["BOEUF", "BŒUF", "MOUTON", "AGNEAU", "PINTADE", "POULE", "POULET", "DINDE", "POISSON", "CREVETTE", "CRABE"]),
    ("Viandes / Poisson / Charcut", ["SAUCISSE", "CHARCUT", "JAMBON", "SALAMI"]),
    ("Surgelés légumes", ["SURGELE", "SURGELÉ", "FROZEN"]),
    ("Sauces sucrées cuisine", ["CARAMEL", "CHOCOLAT SAUCE", "SIROP D"]),
]

# Corrections manuelles si besoin (nom_clean -> (categorie, tva))
MANUAL_OVERRIDES: dict[str, tuple[str, float]] = {
    "POULE FUMEE": ("Mer / Viandes base", 5.5),
}


def infer_category(label: str) -> str:
    upper = label.upper()
    for categorie, keywords in CATEGORY_RULES:
        if any(token in upper for token in keywords):
            return categorie
    return "Pâtes / Riz / Semoule / Farine"


def infer_tva(categorie: str) -> float:
    tva20 = {
        "Spiritueux",
        "Effervescents / Champagne",
        "Vins rouges",
        "Vins blancs",
        "Vins rosés",
        "Bières",
        "Apéritifs / Fortifiés",
        "Softs / Énergisants",
    }
    return 20.0 if categorie in tva20 else 5.5


def prepare():
    df = pd.read_csv(PREPARED_PATH)
    new_df = df[df["is_new"] == True].copy()  # noqa: E712

    categories = []
    tvas = []
    for _, row in new_df.iterrows():
        override = MANUAL_OVERRIDES.get(row["nom_clean"])
        if override:
            cat, tva = override
        else:
            cat = infer_category(row["nom_clean"])
            tva = infer_tva(cat)
        categories.append(cat)
        tvas.append(tva)

    new_df["categorie"] = categories
    new_df["tva"] = tvas
    new_df["prix_vente"] = new_df["prix_ttc"]  # pas de décomposition HT ici

    # Déduplique sur le nom_clean en conservant le prix le plus élevé
    new_df = (
        new_df.sort_values("prix_vente", ascending=False)
        .drop_duplicates(subset=["nom_clean"], keep="first")
        .reset_index(drop=True)
    )

    output_cols = [
        "nom_original",
        "nom_clean",
        "categorie",
        "prix_vente",
        "tva",
        "prix_ttc",
        "base_key",
    ]
    new_df[output_cols].to_csv(OUTPUT_PATH, index=False)
    print("Fichier insertion:", OUTPUT_PATH, "->", len(new_df), "lignes")


if __name__ == "__main__":
    prepare()
