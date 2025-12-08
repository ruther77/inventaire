from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Paramètres DB via docker compose
DOCKER_SERVICE = "db"
DB_USER = "postgres"
DB_NAME = "epicerie"
TENANT_ID = 1

OUTPUT_CSV = Path("docs/reclassified_preview.csv")
OUTPUT_SQL = Path("docs/reclassified_update.sql")


def run_psql(query: str) -> str:
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        DOCKER_SERVICE,
        "psql",
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
        "-v",
        "ON_ERROR_STOP=1",
        "-At",
        "-c",
        query,
    ]
    res = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return res.stdout


@dataclass
class Rule:
    category: str
    include: list[str]
    exclude: list[str] | None = None

    def matches(self, text: str) -> bool:
        for inc in self.include:
            if re.search(inc, text, re.I):
                if self.exclude:
                    for exc in self.exclude:
                        if re.search(exc, text, re.I):
                            return False
                return True
        return False


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


def normalize_label(text: str) -> str:
    import unicodedata

    norm = unicodedata.normalize("NFKD", str(text))
    norm = norm.encode("ascii", "ignore").decode("ascii")
    norm = norm.upper()
    norm = re.sub(r"[^A-Z0-9]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


# Règles renforcées (ordre = priorité stricte)
RULES: list[Rule] = [
    # Alcool
    Rule("Apéritifs / Fortifiés", [word_re([
        "PORTO","SHERRY","VERMOUTH","MARTINI","MUSCAT","MUSCATEL","MAD[ÈE]RE","MARSALA","LILLET","APERITIF DOUX","NOILLY","QUINA","BYRRH","PINEAU","MISTELLE","MUTÉ",
    ])]),
    Rule("Spiritueux", [word_re([
        "WHISKY","VODKA","RUM","RHUM","GIN","TEQUILA","PASTIS","COGNAC","ARMAGNAC",
        "MARTINI","RICARD","APERITIF","LIQUEUR","APEROL","CAMPARI","BAILEYS","GET ?27","GET ?31",
        "GLENFIDDICH","GLENLIVET","JACK DANIEL","BALLANTINE","CHIVAS","J&B","J & B","LABEL","JAGER","SAINT JAMES","LA MAUNY",
        "RHUM|RUM","CACHACA","AGUARDIENTE","BOISSON ALCOOLISEE","ALCOOLISE","VODKAMIX",
        "ABSO[Ll]UT","SMIRNOFF","GREY GOOSE","HAVANA","CAPTAIN MORGAN","SAILOR JERRY","BEEFEATER","BOMBAY","TANQUERAY",
    ])]),
    Rule("Effervescents / Champagne", [word_re([
        "CHAMPAGNE","CREMANT","CR[ÉE]MANT","PROSECCO","CAVA","MO[ËE]T","VEUVE","BRUT","MUSCAT SPARKLING","MOUSSANT","EFFERVESCENT",
        "PIPER","MUMM","TATTINGER","TAITTINGER","BOLLINGER","RUINART","POMMERY","DEUTZ","LANSON","DRAPPIER","AYALA","CANARD-DUCHENE",
    ])]),
    Rule("Vins rouges", [word_re([
        "VIN ROUGE","ROUGE\\b","BORDEAUX","BOURGOGNE","MERLOT","CABERNET","SYRAH","MALBEC","PINOT","C[ÔO]TES? DU RH[ÔO]NE","CDR","RIOJA","LANGUEDOC","MEDOC","M[ÉE]DOC","COTES DU RHONE","POMEROL","PAUILLAC",
    ])], exclude=[r"BLANC|WHITE|ROS[ÉE]|ROSE|BLC|BLANCHE"]),
    Rule("Vins blancs", [word_re([
        "VIN BLANC","BLANC\\b","BLC","CHARDONNAY","SAUVIGNON","RIESLING","GEWURZ","GEWURZTRAMINER","CHENIN","MOELLEUX","VIOGNIER","MUSCADET","GROS PLANT",
    ])], exclude=[r"ROS[ÉE]|ROSE|ROUGE|RGE"]),
    Rule("Vins rosés", [word_re([
        "ROS[ÉE]","ROSE","RSE",
    ])]),
    Rule("Bières", [word_re([
        "BI[ÈE]RE","BEER","LAGER","IPA","STOUT","BLONDE","BRUNE","AMBR[ÉE]","DESPERADOS","HEINEKEN","1664","KRO","CARLSBERG","GRIMBERGEN","CORONA","DUVEL","JUPILER","GUINNESS","PUNK IPA","QUILMES",
    ])]),

    # Boissons non alcoolisées
    Rule("Softs / Énergisants", [word_re([
        "SODA","COCA","COLA","FANTA","SPRITE","7UP","PEPSI","OASIS","SCHWEPPES","TONIC","LIMONADE",
        "ICE ?TEA","ICED TEA","LIPTON","JUS","NECTAR","SIROP","GINGER BEER","TAMPICO","MALTA","VIMTO",
        "ENERGY","RED ?BULL","MONSTER","BURN","POWER ADE","CAPRI[- ]?SUN","MOGU MOGU","MIRINDA","MOUNTAIN DEW","TROPICO","TANG","ARIZONA","PULCO","ORANGINA","RIBENA","SHANI","OASIS",
    ])], exclude=[r"%|ALCOOL|WHISKY|VODKA|GIN|RHUM|RUM|BI[ÈE]RE|BEER|VIN|PORTO|APERITIF|WH GLENFIDDICH|RH LA MAUNY|WH\\b"]),
    Rule("Eaux", [word_re([
        "EAU","WATER","PERRIER","CRISTALINE","VITTEL","EVIAN","VOLVIC","BADOIT","ST[. ]?YORRE","VICHY","SAN PEL","MONT ROUCOUS","ROCHE DES ECRINS","ROCHE",
    ])], exclude=[r"SODA|SIROP|JUS|COLA|FANTA|MOGU|OASIS|TAMPICO"]),

    # Chaud / boissons chaudes
    Rule("Café / Thé / Infusion", [word_re([
        "CAF[ÉE]","NESCAFE","NESPRESSO","CAPSULE","DOSETTE","THE","TH[ÉE]","INFUSION","TISANE","NESQUIK","RICORE","JACOBS","MAXWELL","LAVAZZA",
        "CAPPUCCINO","MOKA","EXPRESSO","ESPRESSO","DOLCE GUSTO","SENSEO",
    ])]),

    # Boulangerie
    Rule("Boulangerie / Viennoiserie", [word_re([
        "PAIN","BAGUETTE","BRIOCHE","CROISSANT","VIENNOISERIE","BUN","WRAP","TORTILLA","NAAN","PITA","FOCACCIA","TAPIOCA",
        "BURGER BUN","HOT DOG","PAV[EÉ]","PAVOT","BRIOCHETTE",
    ])]),

    # Snacks salés
    Rule("Apéro salé / Graines", [word_re([
        "CHIPS","ARACHIDE","ARACHIDES","CACAHU[ÈE]TE","PISTACHE","NOIX DE CAJOU","GRAINE","GRAINES","SNACK","CRACKER","TAFFEL","PRINGLES",
        "MEGA CHIPS","CRISP","GAUFRETTE SALEE","BRETZEL","TORTILLA CHIP","TUC","CROUTON","TAPAS","APERITIF SALE",
    ])], exclude=[r"CHOCOLAT|SUCRE|BONBON|FUME|FUMEE|SAUCISSE|CHARCUT"]),
    Rule("Panés / Apéro salé", [word_re([
        "NUGGET","PAN[ÉE]","CORDON BLEU","PANELLE","PANE","NEMS","SAMOUSA","SPRING ROLL","ROULEAU PRINTEMPS",
    ])]),

    # Confiserie / sucré
    Rule("Confiserie / Desserts", [word_re([
        "BISCUIT","COOKIE","GAUFRETTE","GAUFRE","MADELEINE","CAKE","BROWNIE","BARRE CHOCOLAT",
        "KINDER","TWIX","SNICKERS","MARS","BOUNTY","LION","M&M","SMARTIES","PRINCE","OREO","SPECULOOS",
        "HARIBO","BONBON","CARAMEL","SUCETTE","CHEWING GUM","DRAGEE","MARSHMALLOW","TAGADA","SKITTLES","TETES BRULEES","SURFIZZ","BUBBLE",
        "GLACE","SORBET","ESQUIMAU","CORNETTO","MAGNUM","MR FREEZE","ESQUI",
    ])], exclude=[r"SAC|SACHET|PAILLE|GOBELET|PLATEAU|BOITE|BOX|FUME|FUMEE|FUME|SALE|SEC|CONGE|SURGEL"]),
    Rule("Épicerie sucrée", [word_re([
        "SUCRE","CASSONADE","VERGEOISE","SUCRE DE CANNE","MIEL","CONFITURE","SIROP DE SUCRE","SIROP D'AGAVE",
        "CACAO","CHOCOLAT EN POUDRE","NUTELLA","PATE A TARTINER","LAIT CONCENTR[ÉE] SUCRE",
        "DESSERT POUDRE","GELATINE","ENTREMETS","VANILLINE","LEVURE CHIMIQUE","AR[ÔO]ME SUCRE","FLEUR D'ORANGER","SUCRE GLACE",
    ])], exclude=[r"VIANDE|POISSON|STOCKFISH|MAQUEREAU|BOEUF|POULET|DINDE|CREVETTE|CRABE|RHUM|WHISKY|VODKA|BI[ÈE]RE|VIN|FROMAGE|CHARCUT|SAUCISSE|SAC |SACHET |GOBELET|PAILLE|BARQUETTE|BO[ÎI]TE|CARTON|POT|BOUTEILLE|D[ÉE]ODORANT|DETERGENT|JAVEL|FUME|FUMEE|SALE\\b|SEC\\b|CONGE|SURGEL|OIGNON|PERSIL|CORIANDRE|CITRON|POIREAUX|AUBERGINE|CAROTTE|CHOU|POIVRON"]),

    # Fruits / légumes
    Rule("Fruits / Légumes frais", [word_re([
        "FRAIS\\b","L[ÉE]GUME","L[ÉE]GUMES","FRUIT","BANANE","PLANTAIN","OIGNON","TOMATE FRA[IÎ]CHE","PIMENT FRAIS","POMME","MANGUE","ANANAS","ORANGE","CITRON",
        "CIBOULETTE","BASILIC","CORIANDRE","OSEILLE","CAROTTE","PDT","POMME DE TERRE","PATATE","AUBERGINE","COURGETTE","CHOU","POIVRON","HARICOT VERT","AILETTE",
        "MANIOC","GNAM","IGNAME","PATATE DOUCE","BISSAP FRAIS","PERSIL","MENTHE","CHAMPIGNON","SALADES?",
    ])], exclude=[r"SURGEL|CONGE|FROZEN|SODA|JUS|CANDY|BONBON|PRINGLES|FANTA|COCA|CAPRI|SACHET|PAILLE|GOBELET|PAQUET|BTE"]),
    Rule("Surgelés légumes", [word_re([
        "SURGEL","CONGE","FROZEN","SURGELE","CONGEL",
    ])], exclude=[r"VIANDE|POISSON|BOEUF|POULET"]),

    # Emballages / Jetables
    Rule("Emballages / Jetables", [word_re([
        "GOBELET","ASSIETTE","COUVERT","FOURCHETTE","COUTEAU","CUILL[ÈE]RE","PAILLE",
        "SAC","SACHET","SAC POUBELLE","BARQUETTE","PLATEAU","RAMEQUIN","BO[ÎI]TE","BOX","CARTON","FILM","ALU","CELLOPHANE",
        "PAPIER CUISSON","PAPIER SULFURIS[ÉE]","BOBINE","ROULEAU","SERVIETTE","NAPKIN","SPATULE","BAGUETTE BOIS","POT SAUCE","OPERCULE","COUVERCLE",
        "JETABLE","M ?PRO","ARO","AGITATEUR","GANT","GOB","POT","OPER","COUV","BARQ","CIERGE","DECOR","SERV",
        "M PRO","MPRO","M-PRO","RIOBA","METRO","GOB CART","KRAFT","BOITE KRAFT","BTE KRAFT","SACHET KRAFT","SAC KRAFT","BTE BURGER","BOITE BURGER",
        "SET GAUFFRE","PLATEAU BURGER","ASSIETTE PATES","GOB CHAUD","GOB FROID","BTE KRAFT","SAC POI",
    ])], exclude=[r"AR[ÔO]ME|AROME|SAUCE|HUILE|SUCRE|FARINE|CITRON|CITR|OIGNON|OIG|CAROT|CIBOULETTE|CORIANDRE|BASILIC|OSEILLE|POMME|ANANAS|BANAN|PLANTAIN|PDT|POMME DE TERRE|POIVRON|FRUIT|LEGUME|L[ÉE]GUME|SARDINE|THON|POISSON|MAQUEREAU|PIMENT|PERSIL|MENTHE|TOMATE|LAIT|COCO|ARACHIDE|PINDAKA|SUCRE DE CANNE|SAUCE TOMATE"]),

    # Hygiène / Entretien
    Rule("Hygiène / Entretien", [word_re([
        "SAVON","GEL DOUCHE","SHAMPOO","SHAMPOING","D[ÉE]ODORANT","DENTIFRICE","BROSSE A DENTS","LESSIVE","ADOUCISSANT",
        "LIQUIDE VAISSELLE","D[ÉE]TERGENT","D[ÉE]SINFECTANT","LINGETTE","[ÉE]PONGE","SOPALIN","PAPIER TOILETTE","MOUCHOIR","ESSUIE[- ]TOUT","JAVEL","D[ÉE]GRAISSANT","NETTOYANT","LAVE VITRE",
        "BOLDAIR","DESODO","PHYTOSANITAIRE","CREME LAVANTE","GANT LATEX","SERVIETTE HYGIENIQUE",
    ])], exclude=[r"BONBON|AR[ÔO]ME|AROME|SUCRE|CHOCOLAT|PAIN"]),

    # Huiles / Condiments
    Rule("Huiles / Condiments", [word_re([
        "HUILE","MAYO","MAYONNAISE","KETCHUP","MOUTARDE","VINAIGRE","SAUCE SOJA","TERIYAKI","NUOC MAM","WORCESTERSHIRE",
        "PIMENT SAUCE","HARISSA SAUCE","RELISH","PICKLES","CONDIMENT","TABASCO","PEPPER SAUCE","MOUTARDE","SAUCE PIMENT",
        "LESIEUR","PUGET","ISIO4","AYAM SAUCE","HEINZ","AMORA","MAILLE","DIAMA","AICHA","ALPRO SAUCE",
    ])], exclude=[r"SUCRE|BONBON|AR[ÔO]ME|CHOCOLAT"]),

    # Conserves / Tomates
    Rule("Conserves / Tomates", [word_re([
        "CONSERVE","TOMATE","PULPE","COULIS","CONCENTR[ÉE]","SARDINE","THON","MAQUEREAU","PILCHARD","LATTA","TOMATO PASTE","PATE TOMATE",
        "MUTTI","CIRIO","AYAM","GLENRYCK","CONNETABLE","RIO MARE","PANZANI SAUCE",
    ])], exclude=[r"FRAIS|SURGE|CONGE|FRAICHE|FRAICHEUR"]),

    # Épices / Herbes / Bouillons
    Rule("Épices / Herbes / Bouillons", [word_re([
        "PIMENT","CHILI","HARISSA","POIVRE","SEL","CURRY","CURCUMA","PAPRIKA","GINGEMBRE","AIL","OIGNON EN POUDRE","MUSCADE","CANNELLE","CLOU DE GIROFLE","BADIANE",
        "HERBES","THYM","ROMARIN","ORIGAN","BASILIC","LAURIER","BOUQUET GARNI","[ÉE]PICE","[ÉE]PICES","BOUILLON","CUBE","MAGGI","KUB","AR[ÔO]ME","FOND DE VEAU",
        "VEGETA","JUMBO","AR[ÔO]ME VANILLE","AROME VANILLE","AR[ÔO]ME FLEUR","VANILINE","ARIOSTO","KNORR","ROYCO","ARI[O]STO",
    ])], exclude=[r"POULET|POISSON|BOEUF|CREVETTE|CRABE|MAQUEREAU|MORUE|STOCKFISH|SARDINE|THON|DINDE|AILE|AILERON|VIANDE|CHARCUT|VIN|BORDEAUX|MERLOT|CABERNET|SYRAH|PINOT|CHARDONNAY|SAUVIGNON|CRABE BLEU|POULET WILKI|POULE WILKY"]),

    # Mer / viandes
    Rule("Mer / Viandes base", [word_re([
        "BOEUF","B[ŒO]UF","VEAU","MOUTON","AGNEAU","CHEVRE","POULET","POULE","DINDE","PINTADE","VIANDE","CHARAL",
        "STEAK","PALERON","BAVETTE","ENTREC[ÔO]TE","JARRET","RUMSTEAK","BOURGUIGNON","FAUX FILET","ONGLET","JOUES","QUEUE","PANS",
        "POISSON","MAQUEREAU","SARDINE","CHINCHARD","BONITE","MERLU","CABILLAUD","MORUE","STOCKFISH","TILAPIA","CARPE","TRUITE","SAUMON","BARACOUDA","BARRACUDA",
        "CREVETTE","CRABE","LANGOUSTINE","HOMARD","CALAMAR","SEICHE","POULPE","COQUILLE","CRABE BLEU","SCYLLA",
    ])], exclude=[r"SAUCE|AR[ÔO]ME|P[ÂA]TE|RIZ|FARINE|SEMOULE|PAIN|CHIPS|CUBE|MAGGI|SWEET|CHOCOLAT|SUCRE|FROMAGE|CAMEMBERT|COMTE|BRIE|GOUDA|CHEDDAR|NUGGET|CRISP"]),

    Rule("Viandes / Poisson / Charcut", [word_re([
        "SAUCISSE","CHARCUT","JAMBON","SALAMI","BACON","LARD","CHORIZO","MORTADELLE","PANCETTA","ROSETTE","COPPA",
    ])]),

    # Féculents
    Rule("Pâtes / Riz / Semoule / Farine", [word_re([
        "RIZ","BASMATI","THAI","BRISURE","SEMOULE","COUSCOUS","BULGUR","FONIO","GARI","FUFU","FARINE","MA[IÏ]ZENA","AMIDON",
        "SPAGHETTI","MACARONI","PENNE","FUSILLI","TORSADE","TAGLIATELLE","NOUILLE","VERMICELLE","P[ÂA]TE","PATES","PÂTES","RAMEN","LINGUINE","LASAGNE","RAVIOLI","GNOCCHI","TORTI",
    ])], exclude=[r"POISSON|MAQUEREAU|MORUE|CREVETTE|CRABE|POULET|BOEUF|STOCKFISH|SAUCE TOMATE"]),

    # Laits / Crèmes
    Rule("Laits / Crèmes", [word_re([
        "LAIT","CR[ÈE]ME","EVAPOR[ÉE]|[ÉE]VAPOR[ÉE]","CONCENTR[ÉE]","CREME FRAICHE","CREME LIQUIDE","CREME CHANTILLY","CONDENSED MILK","EVAPORATED MILK",
    ])], exclude=[r"CHOCOLAT|POUDRE CACAO|SUCRE|BONBON"]),
    Rule("Frais laitier / Fromages", [word_re([
        "FROMAGE","YAOURT","CHEESE","CAMEMBERT","BRIE","COMTE","GOUDA","CHEDDAR","MOZZARELLA","GRUYERE","EMMENTAL","ROQUEFORT","BLEU",
    ])], exclude=[r"SAUCISSE|CHARCUT"]),

    # Sauces sucrées cuisine
    Rule("Sauces sucrées cuisine", [word_re([
        "CARAMEL","CHOCOLAT SAUCE","SIROP SUCR[ÉE]|SIROP SUCRE","DULCE","SAUCE DESSERT","TOPPING","COULIS SUCRE","SAUCE FRAISE","SAUCE CHOCOLAT",
    ])]),
]


def pick_category(text: str) -> str:
    text_norm = normalize_label(text)
    for rule in RULES:
        if rule.matches(text_norm):
            return rule.category
    return "Épicerie sucrée"


def main():
    raw = run_psql(f"SELECT id, nom, categorie FROM produits WHERE tenant_id={TENANT_ID};")
    rows = []
    for line in raw.strip().splitlines():
        parts = line.split("|")
        if len(parts) < 3:
            continue
        pid, nom, old_cat = parts[0].strip(), parts[1].strip(), (parts[2] or "").strip()
        new_cat = pick_category(nom)
        rows.append({"id": int(pid), "nom": nom, "old_categorie": old_cat, "new_categorie": new_cat})

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False)
    counts = df["new_categorie"].value_counts()
    print("Répartition nouvelle:\n", counts)

    values_list = []
    for r in rows:
        cat_sql = r["new_categorie"].replace("'", "''")
        values_list.append(f"({r['id']}, '{cat_sql}')")
    values = ",\n".join(values_list)
    sql = f"""-- Mise à jour des catégories (tenant {TENANT_ID})
WITH data(id, new_cat) AS (
  VALUES
{values}
)
UPDATE produits p
SET categorie = d.new_cat,
    updated_at = now()
FROM data d
WHERE p.id = d.id AND p.tenant_id = {TENANT_ID};
"""
    OUTPUT_SQL.write_text(sql)
    print("Fichiers générés:", OUTPUT_CSV, OUTPUT_SQL)


if __name__ == "__main__":
    main()
