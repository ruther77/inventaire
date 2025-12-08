"""
Analyseur de mots-clés par catégorie pour les relevés bancaires.

Algorithme 2: Parcourt les transactions et compte les occurrences de mots-clés
pour chaque catégorie parmi les 12 catégories définies.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bank_statement_parsers import (
    ParsedStatement,
    Transaction,
    parse_statement,
    detect_bank_type,
)


# =============================================================================
# LES 12 CATÉGORIES ET LEURS MOTS-CLÉS ASSOCIÉS
# =============================================================================

CATEGORIES = {
    "encaissements": {
        "name": "Encaissements",
        "code": "encaissements",
        "keywords": [
            # Encaissements CB/Carte
            "REMISE CB", "REMISE CARTE", "ENCAISSEMENT",
            "VERSEMENT ALS", "VERSEMENT ESPECES", "VERSEMENT",
            "VRSTESPECESAUTOMATE", "VRST ESPECES",
            # Virements reçus
            "VIREMENT RECU", "VIR SEPA RECU", "VIRSEPARECU", "VIR INST",
            "VIRCPTEACPTERECU", "Virement entrant",
            # SumUp
            "Paiement entrant", "SUMUP PID", "PAYOUT",
            # Autres
            "REGLEMENT CLIENT", "CREDIT", "AVOIR",
            "REMBT", "REMBTPRLV",  # Remboursement de prélèvement
            # Remises de chèques
            "REM CHQ", "REMISECHEQUES", "REM CHQ CAE",
        ],
    },
    "achats_fournisseurs": {
        "name": "Achats et frais fournisseurs",
        "code": "achats_fournisseurs",
        "keywords": [
            # Grossistes alimentaires
            "METRO", "METRO CASH", "METRO FRANCE", "PROMOCASH", "CARREFOUR", "TRANSGOURMET",
            "BRAKE FRANCE", "SYSCO", "DAVIGEL", "POMONA",
            "EUROCIEL", "TAIYAT", "HAUDECOEUR", "ETSHAUDECOEUR",
            "PRLV SEPA METRO",  # METRO via prélèvement
            # Commerces alimentaires / Fournisseurs
            "GNANAM", "EXOTI", "ETHAN",
            "BOUCH", "BVS", "BOUCH BVS", "BOUCHERIE",  # Boucher
            "PRIMEUR", "POISSONNIER", "FROMAGERIE", "BOULANGERIE",
            # Achats CB génériques
            "CB55", "CB12", "CB1755",  # Préfixes CB LCL
            "PAIEMENT POS", "PAIEMENT CB",
            "FACTURE(S)CARTE", "FACTURECARTE",  # BNP factures carte
            "Paiement en ligne",  # SumUp achats
            # Magasins
            "CENTRAKOR", "SAINT MAXIMO", "PICARD", "LIDL", "ALDI",
            "LECLERC", "AUCHAN", "INTERMARCHE",
            "PRIMARKO", "PRIMARK",  # Achats vestimentaire
            "H&M", "ZARA", "ACTION", "ELCORTEINGLES", "CETA",  # Autres magasins
            "SUMUP *LINCONT",  # Paiements SumUp internes
            "BRICO",  # Bricolage
            # Restauration rapide / commerces
            "KFC", "MACDONALDS", "MCDONALDS", "BURGER KING",
            "MARIONNAUD", "IKEA", "LEROYMERLIN", "LEROY MERLIN",
            "MERCADONA", "ROYALAIRMAROC",
            # Fitness
            "NEONESS", "PRLVSEPANEONESS",
            # Voyages/Loisirs
            "PALAISDURIRE", "ADAMAX", "APRR", "AVIA",
            # Virements étrangers
            "VIRETRANGERRECU",
            # Remboursements CB
            "REMBOURSTCB",
            # Services en ligne
            "PAYPAL", "PAYPALEUROPE",
            "AMAZON", "AMAZON PAYMENTS",
            # Fitness/Autres achats
            "BASICFIT", "BASIC-FIT",
            # Énergie/Gaz pro
            "GAZELENERGIE", "GAZEL",
            "ENGIE", "GAZPROM", "TOTALE ELEC",  # Énergie
            "TAI YAT",  # Fournisseur
            "dhgate",  # Achats en ligne
            "CARREFOURBANQUE",  # Services bancaires Carrefour
        ],
    },
    "salaires_remunerations": {
        "name": "Salaires & rémunérations",
        "code": "salaires_remunerations",
        "keywords": [
            "SALAIRE", "REMUNERATION", "PAIE", "VIR SALAIRE",
            "PRIME", "AVANCE", "ACOMPTE", "INDEMNITE", "CONGES",
            "VIREMENT PERMANENT", "VIRPERM",
        ],
    },
    "charges_sociales": {
        "name": "Charges sociales",
        "code": "charges_sociales",
        "keywords": [
            "URSSAF", "URSSAF D ILE", "URSSAF D'ILE", "COTISATION SOCIALE", "CHARGES SOCIALES",
            "RETRAITE", "PREVOYANCE", "MUTUELLE SANTE",
            "CPAM", "POLE EMPLOI", "ASSEDIC",
            "FORMATION PRO", "OPCO", "ORGANISME FORMATION",
            "PRLV SEPA URSSAF",  # URSSAF via prélèvement
            "KLESIA",  # Caisse retraite
        ],
    },
    "impots_taxes": {
        "name": "Impôts & taxes",
        "code": "impots_taxes",
        "keywords": [
            "IMPOT", "TAXE", "TVA", "CFE", "CVAE",
            "TRESOR PUBLIC", "DGFIP", "DIRECTION GENERALE FINANCES",
            "CONTRIBUTION", "PRELEVEMENT SOURCE", "PAS ",
            "TAXE FONCIERE", "TAXE HABITATION",
        ],
    },
    "frais_generaux": {
        "name": "Frais généraux",
        "code": "frais_generaux",
        "keywords": [
            # Frais bancaires
            "COMMISSION", "FRAIS TENUE", "FRAIS GESTION",
            "AGIOS", "ABON LCL", "LCL ACCESS", "ABONNEMENT",
            "RESULTAT ARRETE", "ARRETE COMPTE",
            "COTISATION CARTE", "COTISATION CB",
            "COTISATION MENSUELLE", "COTISATION DE VOTRE",
            "TRAIT.IRREG", "LCL A LA CARTE",
            "OPTION PRO",
            # Fournitures
            "FOURNITURES", "BUREAU VALLEE", "STAPLES", "OFFICE DEPOT",
            # Nettoyage/Entretien
            "NETTOYAGE", "ENTRETIEN", "HYGIENE", "MENAGE",
            # Restauration
            "RESTAURANT", "DEJEUNER", "REPAS",
            # Sécurité
            "SPB", "SECTOR ALARM",
            # Chèques
            "CHQ.", "CHEQUE", "REM CHQ",
            # Opérations bancaires
            "BLOCAGE", "DEBLOC", "FRAIS CODE SECRET",
            "FRAIS SAISIE", "FRAIS DOSSIER",
            "COTIS CARTE", "DEPOT", "REAPRO",
            "COTISATION", "PAIEMENT",
        ],
    },
    "transport_deplacement": {
        "name": "Transport & déplacement",
        "code": "transport_deplacement",
        "keywords": [
            # Transport public
            "SNCF", "RATP", "NAVIGO", "TRANSILIEN",
            # VTC/Taxi
            "UBER", "BOLT", "KAPTEN", "TAXI", "FREE NOW",
            # Carburant / Recharge électrique
            "TOTAL", "TOTALENERGIES", "SHELL", "BP ", "ESSO",
            "CARBURANT", "ESSENCE", "GASOIL", "DIESEL",
            "ELECTRA", "IONITY", "CHARGING",  # Bornes recharge
            # Parking/Péage
            "PARKING", "PEAGE", "AUTOROUTE", "VINCI", "SANEF",
            "ASF", "COFIROUTE", "DYNEFF", "CEDIP",  # Péages/Stations autoroute
            # Livraison
            "RELAIS COLIS", "CHRONOPOST", "COLISSIMO", "LA POSTE",
            "DHL", "UPS", "FEDEX", "TNT",
            # Location véhicule
            "HERTZ", "AVIS", "EUROPCAR", "SIXT",
            # Hôtels
            "HOTEL", "IBIS", "HOTELIBIS",
        ],
    },
    "immobilisations_investissements": {
        "name": "Immobilisations & investissements",
        "code": "immobilisations_investissements",
        "keywords": [
            "EQUIPEMENT", "MATERIEL", "MACHINE", "MOBILIER",
            "AMENAGEMENT", "TRAVAUX", "INSTALLATION", "RENOVATION",
            "CAISSE ENREGISTREUSE", "ORDINATEUR", "ECRAN", "IMPRIMANTE",
            "ELECTROMENAGER", "REFRIGERATEUR", "CONGELATEUR",
        ],
    },
    "loyer_immobilier": {
        "name": "Loyer & immobilier",
        "code": "loyer_immobilier",
        "keywords": [
            "LOYER", "BAIL", "LOCATION LOCAL",
            "CHARGES LOCATIVES", "SYNDIC", "COPROPRIETE",
            "FONCIER", "RESIDENCE",
            "PREFILOC", "CREDIT BAIL",
            "ECHEANCE PRET", "ECHEANCEPRET", "PRET IMMOBILIER", "EMPRUNT IMMO",
        ],
    },
    "marketing_communication": {
        "name": "Marketing & communication",
        "code": "marketing_communication",
        "keywords": [
            "PUBLICITE", "PUB ", "MARKETING", "COMMUNICATION",
            "FLYER", "AFFICHE", "CARTE VISITE", "IMPRIMERIE",
            "SITE WEB", "GOOGLE ADS", "FACEBOOK", "INSTAGRAM", "META",
            "RESEAUX SOCIAUX", "INFLUENCEUR",
        ],
    },
    "frais_financiers": {
        "name": "Frais financiers",
        "code": "frais_financiers",
        "keywords": [
            "INTERET", "INTERETS DEBITEURS", "AGIOS",
            "FRAIS FINANCIERS", "DECOUVERT",
            "PRLV IMPAYE", "REJET", "COM PRLV IMPAYE",
            "COMMISSIONS SUR REMISE",  # Commissions CB
            "FRAIS BANCAIRES",
            "SAISIEADMINISTRATIVE", "SAISIE ADMINISTRATIVE",  # Saisies/blocages
            "REGUL", "REG ",  # Régularisations bancaires
            "*COMMISSIONS",  # Commissions BNP
            "FRAIS",  # Frais génériques
        ],
    },
    "informatique_telecom": {
        "name": "Informatique & télécom",
        "code": "informatique_telecom",
        "keywords": [
            # Opérateurs
            "ORANGE", "SFR", "BOUYGUES TELECOM", "FREE MOBILE", "FREE TELECOM",
            "TELEPHONE", "MOBILE", "INTERNET", "FIBRE",
            # FAI/Services
            "IMAGINER", "OVH", "AMAZON WEB", "AWS",
            # Logiciels
            "MICROSOFT", "GOOGLE", "APPLE", "ADOBE",
            "LOGICIEL", "LICENCE", "SAAS",
            # Streaming (usage pro possible)
            "LEBARA", "CRUNCHYROLL", "NETFLIX", "SPOTIFY",
        ],
    },
    "remboursements_clients": {
        "name": "Remboursements clients & litiges",
        "code": "remboursements_clients",
        "keywords": [
            "REMBOURSEMENT", "REMBOURSER", "REMB ",
            "AVOIR CLIENT", "ANNULATION",
            "LITIGE", "CONTENTIEUX", "REFUND",
            "RETOUR MARCHANDISE",
        ],
    },
    "prestations_externes": {
        "name": "Prestations externes",
        "code": "prestations_externes",
        "keywords": [
            "PRESTATION", "HONORAIRES", "COMPTABLE", "EXPERT COMPTABLE",
            "AVOCAT", "NOTAIRE", "HUISSIER",
            "CONSULTANT", "CONSEIL", "AUDIT",
            "SECURITE", "GARDIENNAGE", "SURVEILLANCE",
            "HMD AUDIT",  # Spécifique trouvé dans les relevés
        ],
    },
    "assurance_vehicule": {
        "name": "Assurance véhicule & vie",
        "code": "assurance_vehicule",
        "keywords": [
            "ASSURANCE VEHICULE", "ASSURANCE AUTO", "ASSURANCE VOITURE",
            "CARDIF", "CARDIFASSURANCEVIE", "CARDIFIARD",
            "MACIF", "MAIF", "MATMUT", "ALLIANZ",
            "APRIL", "APRILPARTENAIRES",
            "ABEILLE", "ABEILLEVIE",
            "SWISSLIFE", "SWISS LIFE",
            "PRLVSEPACARDIF",  # Prélèvement Cardif
            "ASSURANCE LCL", "PACIFICA", "MULTIRISQUE",  # Assurances LCL
        ],
    },
    "virements_internes": {
        "name": "Virements internes & transferts",
        "code": "virements_internes",
        "keywords": [
            "VIRTCPTEACPTE", "VIR CPTE A CPTE",
            "VIREMENT INTERNE", "TRANSFERT",
            "Virement sortant", "VIREMENT EMIS",
            "VIR SEPA", "VIRSEPARECU",  # Virements SEPA
            "L INCONTOURNABLE", "NOUTAM", "LINCONTOURNABL",  # Entités internes
            "Retrait au distributeur",  # Retraits DAB
            "RETRAITCARTEESPECES", "RETRAIT CARTE", "RETRAITDAB",  # Retraits BNP
            "CB1755 RETRAIT", "RETRAIT",  # Retraits CB LCL
            "VIRSCTINSTRECU", "VIRSCTINSTEMIS",  # Virements instantanés
            "VIRCPTEACPTEEMIS", "VIREMENTSEPAEMIS",  # Virements BNP émis
            "LIVRETA", "EPARGNE",  # Virements épargne
            "ALIMENTATION COMPTE",  # Approvisionnement compte
            "VERSEMENT", "VRSTESPECESAUTOMATE", "VRST ESPECES",  # Versements espèces
            "VIR ", "VIREMENT",  # Virements génériques
            "CHQ.",  # Chèques émis
            "BLOCAGE", "DEBLOC",  # Blocages/déblocages sur compte
            "PRELEVEMENT",  # Prélèvements génériques
        ],
    },
}


@dataclass
class KeywordMatch:
    """Représente une correspondance mot-clé/catégorie."""

    keyword: str
    category_code: str
    category_name: str
    count: int = 0
    examples: list[str] = field(default_factory=list)


@dataclass
class CategoryStats:
    """Statistiques pour une catégorie."""

    code: str
    name: str
    total_matches: int = 0
    keyword_counts: dict[str, int] = field(default_factory=dict)
    total_debit: float = 0.0
    total_credit: float = 0.0
    transaction_count: int = 0
    examples: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Résultat complet de l'analyse."""

    source_files: list[str] = field(default_factory=list)
    total_transactions: int = 0
    categorized_transactions: int = 0
    uncategorized_transactions: int = 0
    categories: dict[str, CategoryStats] = field(default_factory=dict)
    uncategorized_keywords: Counter = field(default_factory=Counter)
    all_keywords: Counter = field(default_factory=Counter)


class KeywordAnalyzer:
    """Analyseur de mots-clés pour catégoriser les transactions."""

    def __init__(self):
        self.categories = CATEGORIES
        # Compiler les patterns pour performance
        self._compiled_patterns: dict[str, list[tuple[re.Pattern, str]]] = {}
        for cat_code, cat_info in self.categories.items():
            patterns = []
            for kw in cat_info["keywords"]:
                # Créer un pattern insensible à la casse
                pattern = re.compile(re.escape(kw), re.IGNORECASE)
                patterns.append((pattern, kw))
            self._compiled_patterns[cat_code] = patterns

    def analyze_transaction(
        self, transaction: Transaction
    ) -> tuple[str | None, list[str]]:
        """
        Analyse une transaction et retourne la catégorie détectée et les mots-clés trouvés.

        Returns:
            (category_code, [matched_keywords]) ou (None, []) si non catégorisé
        """
        text = transaction.libelle.upper()
        matches: dict[str, list[str]] = defaultdict(list)

        for cat_code, patterns in self._compiled_patterns.items():
            for pattern, keyword in patterns:
                if pattern.search(text):
                    matches[cat_code].append(keyword)

        if not matches:
            return None, []

        # Prendre la catégorie avec le plus de correspondances
        best_cat = max(matches.keys(), key=lambda c: len(matches[c]))
        return best_cat, matches[best_cat]

    def analyze_statement(self, statement: ParsedStatement) -> AnalysisResult:
        """Analyse un relevé complet et retourne les statistiques."""
        result = AnalysisResult(source_files=[statement.source_file])

        # Initialiser les stats par catégorie
        for cat_code, cat_info in self.categories.items():
            result.categories[cat_code] = CategoryStats(
                code=cat_code,
                name=cat_info["name"],
            )

        for tx in statement.transactions:
            result.total_transactions += 1

            # Extraire tous les mots significatifs du libellé
            words = re.findall(r"\b[A-Z]{3,}\b", tx.libelle.upper())
            for word in words:
                result.all_keywords[word] += 1

            # Catégoriser
            cat_code, keywords = self.analyze_transaction(tx)

            if cat_code:
                result.categorized_transactions += 1
                stats = result.categories[cat_code]
                stats.transaction_count += 1
                stats.total_matches += len(keywords)

                for kw in keywords:
                    stats.keyword_counts[kw] = stats.keyword_counts.get(kw, 0) + 1

                if tx.debit:
                    stats.total_debit += float(tx.debit)
                if tx.credit:
                    stats.total_credit += float(tx.credit)

                # Garder quelques exemples
                if len(stats.examples) < 5:
                    stats.examples.append(f"{tx.date}: {tx.libelle[:60]}")
            else:
                result.uncategorized_transactions += 1
                # Compter les mots non catégorisés
                for word in words:
                    result.uncategorized_keywords[word] += 1

        return result

    def analyze_multiple_statements(
        self, statements: list[ParsedStatement]
    ) -> AnalysisResult:
        """Analyse plusieurs relevés et agrège les résultats."""
        combined = AnalysisResult()

        # Initialiser les stats
        for cat_code, cat_info in self.categories.items():
            combined.categories[cat_code] = CategoryStats(
                code=cat_code,
                name=cat_info["name"],
            )

        for statement in statements:
            combined.source_files.append(statement.source_file)
            result = self.analyze_statement(statement)

            combined.total_transactions += result.total_transactions
            combined.categorized_transactions += result.categorized_transactions
            combined.uncategorized_transactions += result.uncategorized_transactions

            # Fusionner les stats par catégorie
            for cat_code, stats in result.categories.items():
                combined_stats = combined.categories[cat_code]
                combined_stats.transaction_count += stats.transaction_count
                combined_stats.total_matches += stats.total_matches
                combined_stats.total_debit += stats.total_debit
                combined_stats.total_credit += stats.total_credit

                for kw, count in stats.keyword_counts.items():
                    combined_stats.keyword_counts[kw] = (
                        combined_stats.keyword_counts.get(kw, 0) + count
                    )

                combined_stats.examples.extend(stats.examples[:3])

            # Fusionner les compteurs
            combined.all_keywords.update(result.all_keywords)
            combined.uncategorized_keywords.update(result.uncategorized_keywords)

        return combined


def analyze_releve_folder(folder_path: str | Path) -> AnalysisResult:
    """
    Analyse tous les relevés PDF dans un dossier.

    Args:
        folder_path: Chemin vers le dossier contenant les PDFs

    Returns:
        AnalysisResult avec toutes les statistiques agrégées
    """
    folder = Path(folder_path)
    pdf_files = list(folder.glob("*.pdf"))

    statements = []
    for pdf_file in pdf_files:
        try:
            statement = parse_statement(pdf_file)
            statements.append(statement)
            print(f"✓ Parsé: {pdf_file.name} ({len(statement.transactions)} transactions)")
        except Exception as e:
            print(f"✗ Erreur {pdf_file.name}: {e}")

    analyzer = KeywordAnalyzer()
    return analyzer.analyze_multiple_statements(statements)


def print_analysis_report(result: AnalysisResult) -> None:
    """Affiche un rapport détaillé de l'analyse."""
    print("\n" + "=" * 80)
    print("RAPPORT D'ANALYSE DES RELEVÉS BANCAIRES")
    print("=" * 80)

    print(f"\n📁 Fichiers analysés: {len(result.source_files)}")
    for f in result.source_files:
        print(f"   - {Path(f).name}")

    print(f"\n📊 STATISTIQUES GLOBALES")
    print(f"   Total transactions: {result.total_transactions}")
    print(f"   Catégorisées: {result.categorized_transactions} ({result.categorized_transactions/max(1,result.total_transactions)*100:.1f}%)")
    print(f"   Non catégorisées: {result.uncategorized_transactions} ({result.uncategorized_transactions/max(1,result.total_transactions)*100:.1f}%)")

    print(f"\n📋 RÉPARTITION PAR CATÉGORIE (12 catégories)")
    print("-" * 80)

    # Trier par nombre de transactions
    sorted_cats = sorted(
        result.categories.items(),
        key=lambda x: x[1].transaction_count,
        reverse=True,
    )

    for cat_code, stats in sorted_cats:
        if stats.transaction_count == 0:
            continue

        print(f"\n🏷️  {stats.name} ({stats.code})")
        print(f"    Transactions: {stats.transaction_count}")
        print(f"    Débits: {stats.total_debit:,.2f} €")
        print(f"    Crédits: {stats.total_credit:,.2f} €")

        if stats.keyword_counts:
            print("    Mots-clés détectés:")
            for kw, count in sorted(
                stats.keyword_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]:
                print(f"      - {kw}: {count}")

        if stats.examples:
            print("    Exemples:")
            for ex in stats.examples[:3]:
                print(f"      • {ex}")

    print(f"\n⚠️  MOTS-CLÉS NON CATÉGORISÉS (top 30)")
    print("-" * 80)
    for word, count in result.uncategorized_keywords.most_common(30):
        if count >= 2:  # Au moins 2 occurrences
            print(f"   {word}: {count}")

    print("\n" + "=" * 80)


# =============================================================================
# FONCTION PRINCIPALE POUR EXÉCUTION DIRECTE
# =============================================================================


def main():
    """Point d'entrée pour l'analyse des relevés."""
    import sys

    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = "releve"

    print(f"Analyse du dossier: {folder}")
    result = analyze_releve_folder(folder)
    print_analysis_report(result)

    return result


if __name__ == "__main__":
    main()
