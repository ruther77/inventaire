import os  # Variables d'environnement pour la configuration
from functools import lru_cache  # Cache standard pour l'engine

import pandas as pd  # Bibliothèque de manipulation de données tabulaires
from sqlalchemy import create_engine, text  # Création d'engine et requêtes SQL
from sqlalchemy.sql.elements import ClauseElement, TextClause  # Types des expressions SQLAlchemy
from sqlalchemy.engine import Engine  # Type du moteur SQLAlchemy

from .database_url import get_database_url  # Fonction pour récupérer l'URL de base de données
from .settings import AppSettings

SETTINGS = AppSettings.load()
DATABASE_URL = SETTINGS.database_url or get_database_url()  # Construit l'URL de connexion depuis l'environnement
POOL_SIZE = SETTINGS.db_pool_size
POOL_MAX_OVERFLOW = SETTINGS.db_pool_max_overflow


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Retourne le moteur SQLAlchemy, mis en cache via functools (sans dépendance Streamlit)."""
    # Certains dialectes (ex: sqlite memory) n'acceptent pas pool_size/max_overflow.
    kwargs = {"pool_pre_ping": True}
    if DATABASE_URL.startswith("sqlite"):
        # SQLite en mémoire/file -> utiliser le pool par défaut adapté.
        pass
    else:
        kwargs.update(
            {
                "pool_size": max(1, POOL_SIZE),
                "max_overflow": max(0, POOL_MAX_OVERFLOW),
            }
        )
    return create_engine(DATABASE_URL, **kwargs)


def _normalize_statement(sql: str | ClauseElement) -> ClauseElement:
    if isinstance(sql, str):  # Si la requête est une chaîne brute
        return text(sql)  # Convertit en TextClause SQLAlchemy
    if isinstance(sql, ClauseElement):  # Si c'est déjà une expression SQL
        return sql  # Renvoie telle quelle
    raise TypeError("sql must be a string or SQLAlchemy ClauseElement")  # Erreur si type invalide


def query_df(sql: str | ClauseElement, params=None) -> pd.DataFrame:
    """Exécute une requête SELECT et retourne le résultat sous forme de DataFrame Pandas."""  # Docstring de la fonction de lecture
    statement = _normalize_statement(sql)  # Normalise la requête fournie
    if params is not None and not isinstance(params, dict):  # Vérifie le type des paramètres
        raise TypeError("params must be a mapping when provided")  # Soulève une erreur en cas de mauvais type

    # Pré-lie les paramètres pour simplifier les tentatives de repli en cas d'erreur
    bound_statement = statement.bindparams(**params) if params is not None else statement  # Lie les paramètres si fournis

    eng = get_engine()  # Récupère le moteur SQL
    with eng.begin() as conn:  # Ouvre une transaction en lecture
        try:
            result = conn.execute(bound_statement)  # Exécute la requête préparée
        except TypeError as exc:  # Capture les erreurs de type liées au driver
            # Certains drivers (ex: psycopg2 via pandas) peuvent exiger une chaîne brute.
            # Dans ce cas, on recompile la requête avec valeurs littérales pour utiliser exec_driver_sql.
            if isinstance(bound_statement, TextClause):  # Si l'expression est un TextClause
                compiled = bound_statement.compile(compile_kwargs={"literal_binds": True})  # Compile avec valeurs littérales
                sql_text = str(compiled)  # Convertit la requête compilée en texte
                result = conn.exec_driver_sql(sql_text)  # Exécute via exec_driver_sql
            else:  # Sinon, on ne sait pas récupérer proprement
                raise exc  # Relance l'exception initiale

        columns = list(result.keys())  # Récupère les noms de colonnes
        rows = result.fetchall()  # Récupère toutes les lignes

        if not rows:  # Si aucune ligne n'est retournée
            return pd.DataFrame(columns=columns)  # Renvoie un DataFrame vide avec colonnes

        return pd.DataFrame([tuple(row) for row in rows], columns=columns)  # Construit le DataFrame depuis les lignes


# db_manager.py (Renommé : data_repository.py)
# ...


def exec_sql(sql: str | ClauseElement, params=None) -> None:
    """
    Exécute une requête d'écriture (INSERT, UPDATE, DELETE).
    Supporte l'exécution en lot si params est une liste.
    """  # Docstring décrivant l'exécution d'écriture
    statement = _normalize_statement(sql)  # Normalise la requête
    eng = get_engine()  # Récupère le moteur SQL
    with eng.begin() as conn:  # Ouvre une transaction
        # Si params est une liste (exécution en lot), utilise executemany
        if isinstance(params, list):  # Cas d'exécution en lot
            conn.execute(statement, params)  # Exécute avec liste de paramètres
        elif params is None:  # Aucun paramètre fourni
            conn.execute(statement)  # Exécute directement
        else:  # Paramètres fournis sous forme de mapping
            conn.execute(statement, params)  # Exécute avec binding


def exec_sql_return_id(sql: str | ClauseElement, params=None):
    """
    Exécute une requête et retourne l'ID (via RETURNING id). 
    Ne supporte pas l'exécution en lot (car une seule ID est retournée).
    """  # Docstring précisant le comportement de retour d'ID
    statement = _normalize_statement(sql)  # Normalise l'expression SQL
    eng = get_engine()  # Récupère l'engine
    with eng.begin() as conn:  # Ouvre une transaction
        # params doit être un dict ou None, non une liste pour l'insertion simple.
        result = conn.execute(statement, params)  # Exécute la requête avec paramètres
        row = result.fetchone()  # Récupère la première ligne
        return row[0] if row else None  # Retourne l'ID ou None


# ... (Vos fonctions existantes : get_engine, query_df, exec_sql, exec_sql_return_id) ...


def get_product_options(*, tenant_id: int = 1) -> list[tuple[str, int]]:
    """Retourne la liste des produits actifs (nom, id) triés par nom pour un tenant donné."""
    sql = text(
        """
        SELECT nom, id
        FROM produits
        WHERE actif = TRUE AND tenant_id = :tenant_id
        ORDER BY nom
        """
    )

    eng = get_engine()
    with eng.connect() as conn:
        result = conn.execute(sql, {"tenant_id": int(tenant_id)})
        return [(row.nom, row.id) for row in result]


def get_product_details(identifier: str | int, *, tenant_id: int = 1) -> dict | None:
    """
    Recherche les détails d'un produit par son ID ou un de ses codes-barres.

    Args:
        identifier: ID du produit (int) ou code-barres (str).

    Returns:
        Un dictionnaire contenant les détails du produit (id, nom, stock_actuel)
        ou None si le produit n'est pas trouvé.
    """  # Docstring décrivant la recherche produit
    sql_query = """
    SELECT 
        p.id, 
        p.nom, 
        p.stock_actuel AS quantite_stock
    FROM 
        produits p
    LEFT JOIN 
        produits_barcodes pb ON p.id = pb.produit_id AND pb.tenant_id = p.tenant_id
    WHERE 
        p.actif = TRUE 
        AND p.tenant_id = :tenant_id
        -- Recherche par ID du produit (si l'identifiant est numérique)
        AND (
            p.id = :identifier_int 
            -- Recherche par code-barres (si l'identifiant est une chaîne de caractères)
            OR pb.code = :identifier_str
        )
    -- Limite à un seul résultat, même si un produit a plusieurs codes-barres
    LIMIT 1;
    """  # Requête SQL paramétrée pour trouver un produit
    
    # 1. Préparation des paramètres
    params = {"tenant_id": int(tenant_id)}  # Dictionnaire des paramètres pour la requête
    identifier_str = str(identifier).strip()  # Normalise l'identifiant en chaîne
    
    # Tente de convertir en entier pour la recherche par ID
    try:
        identifier_int = int(identifier_str)  # Conversion en entier si possible
        params['identifier_int'] = identifier_int  # Stocke la valeur entière
    except ValueError:
        # Si ce n'est pas un entier, l'ID ne peut pas être utilisé, on met None.
        params['identifier_int'] = None  # Indique l'absence d'ID numérique
        
    # L'identifiant est toujours une chaîne pour la recherche par code-barres
    params['identifier_str'] = identifier_str  # Paramètre pour le code-barres
    
    # 2. Exécution de la requête
    eng = get_engine()  # Récupère l'engine
    with eng.connect() as conn:  # Ouvre une connexion
        result = conn.execute(text(sql_query), params)  # Exécute la requête avec paramètres
        row = result.fetchone()  # Récupère la première ligne
        
    # 3. Formatage du résultat
    if row:  # Si une ligne est trouvée
        # Utiliser _asdict() si la ligne est un RowProxy (standard pour SQLAlchemy)
        return row._asdict()  # Retourne le dictionnaire des valeurs
    else:  # Aucun résultat
        return None  # Indique l'absence de produit correspondant
