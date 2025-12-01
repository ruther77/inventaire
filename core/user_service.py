import os  # Accès aux variables d'environnement
import hmac  # Comparaison sécurisée des hash
import hashlib  # Fonctions de hachage (PBKDF2)
import secrets  # Génération de secrets cryptographiques
import string  # Ensembles de caractères pour mots de passe
import logging  # Journalisation
from typing import Optional  # Typage optionnel

from sqlalchemy import text  # Construction de requêtes SQL textuelles
from sqlalchemy.exc import IntegrityError  # Gestion des erreurs d'intégrité SQL

from .data_repository import query_df, exec_sql, exec_sql_return_id  # Fonctions d'accès base


_PASSWORD_ITERATIONS = 390_000  # Nombre d'itérations PBKDF2
_HASH_ALGO = "pbkdf2_sha256"  # Identifiant de l'algorithme utilisé
ALLOWED_ROLES: tuple[str, ...] = ("admin", "manager", "standard")  # Rôles autorisés
_USER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS app_users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'standard',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""  # SQL de création de la table des utilisateurs


logger = logging.getLogger(__name__)


def ensure_user_table() -> None:
    """Crée la table des utilisateurs si nécessaire."""  # Docstring création table

    # Les endpoints admin repose sur cette table (liste, création, rôles, reset password).

    if os.getenv("SKIP_TENANT_INIT") or os.getenv("SKIP_USER_INIT") or (os.getenv("APP_ENV", "").lower() == "test"):
        return  # Sort si demandé

    exec_sql(text(_USER_TABLE_SQL))  # Exécute le SQL de création idempotente


def _hash_password(password: str) -> str:
    """Hache via PBKDF2 et fournit un format compatible avec `django-style`."""  # Docstring hash
    salt = secrets.token_bytes(16)  # Génère un sel aléatoire de 16 octets
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS
    )  # Calcule PBKDF2-HMAC-SHA256
    return f"{_HASH_ALGO}${_PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"  # Concatène dans un format lisible


def _verify_password(password: str, encoded: str) -> bool:
    try:  # Tente de découper le format encodé
        algorithm, iter_str, salt_hex, digest_hex = encoded.split("$")
    except ValueError:  # Format incorrect
        return False  # Échec de vérification

    if algorithm != _HASH_ALGO:  # Vérifie l'algorithme attendu
        return False  # Échec

    try:  # Convertit les paramètres
        iterations = int(iter_str)  # Nombre d'itérations
        salt = bytes.fromhex(salt_hex)  # Sel décodé
        expected = bytes.fromhex(digest_hex)  # Digest stocké
    except ValueError:  # Erreur de conversion
        return False  # Échec

    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)  # Recalcule le hash
    return hmac.compare_digest(computed, expected)  # Compare en timing-safe


def _normalize_identifier(value: str) -> str:
    return (value or "").strip()  # Nettoie un identifiant (email/username)


def generate_secure_password(length: int = 14) -> str:
    """Génère un mot de passe robuste conforme à la politique de l’entreprise."""  # Docstring génération

    if length < 8:  # Vérifie la longueur minimale
        raise ValueError("La longueur minimale est de 8 caractères.")  # Erreur si trop court

    alphabet = string.ascii_letters + string.digits  # Lettres et chiffres autorisés
    symbols = "!$%&*@#?"  # Symboles autorisés

    while True:  # Boucle jusqu'à produire un mot de passe conforme
        candidate = "".join(secrets.choice(alphabet + symbols) for _ in range(length))  # Génère une chaîne aléatoire
        if (
            any(c.islower() for c in candidate)
            and any(c.isupper() for c in candidate)
            and any(c.isdigit() for c in candidate)
            and any(c in symbols for c in candidate)
        ):  # Vérifie présence de minuscule, majuscule, chiffre, symbole
            return candidate  # Retourne le mot de passe validé


def get_user_by_login(identifier: str) -> Optional[dict]:
    """Retourne un utilisateur à partir de son email ou nom d'utilisateur."""  # Docstring lookup par login

    cleaned = _normalize_identifier(identifier).lower()  # Normalise l'identifiant en minuscules
    sql = text(
        """
        SELECT id, username, email, role, password_hash, created_at
        FROM app_users
        WHERE LOWER(username) = :identifier OR LOWER(email) = :identifier
        LIMIT 1
        """
    )  # Requête de sélection par username ou email
    df = query_df(sql, {"identifier": cleaned})  # Exécute la requête
    if df.empty:  # Aucun résultat
        return None  # Retourne None
    return df.iloc[0].to_dict()  # Retourne le premier enregistrement sous forme de dict


def get_user_by_id(user_id: int) -> Optional[dict]:
    sql = text(
        """
        SELECT id, username, email, role, password_hash, created_at
        FROM app_users
        WHERE id = :user_id
        LIMIT 1
        """
    )  # Requête de sélection par identifiant
    df = query_df(sql, {"user_id": int(user_id)})  # Exécute la requête
    if df.empty:  # Aucun utilisateur trouvé
        return None  # Retourne None
    return df.iloc[0].to_dict()  # Retourne le dictionnaire utilisateur


def list_users():
    """Retourne l'ensemble des utilisateurs ordonnés par date de création."""  # Docstring listing

    sql = text(
        """
        SELECT id, username, email, role, created_at
        FROM app_users
        ORDER BY created_at ASC, username ASC
        """
    )  # Requête listant tous les utilisateurs
    return query_df(sql)  # Retourne le DataFrame complet


def authenticate_user(identifier: str, password: str) -> Optional[dict]:
    """Valide les identifiants et retourne l'utilisateur sans le hash."""  # Docstring authentification

    if not identifier or not password:  # Vérifie que l'entrée est fournie
        return None  # Échec

    user = get_user_by_login(identifier)  # Charge l'utilisateur par login
    if not user:  # Pas trouvé
        return None  # Échec

    if not _verify_password(password, user["password_hash"]):  # Vérifie le mot de passe
        return None  # Échec

    return {
        "id": int(user["id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"],
    }  # Retourne les métadonnées sans hash


def create_user(username: str, email: str, password: str, role: str = "standard") -> dict:
    """Crée un utilisateur et retourne ses métadonnées (sans hash)."""  # Docstring création utilisateur

    username = _normalize_identifier(username)  # Nettoie le username
    email = _normalize_identifier(email).lower()  # Nettoie et met l'email en minuscules
    password = (password or "").strip()  # Nettoie le mot de passe fourni
    role = (role or "standard").strip().lower()  # Nettoie le rôle

    if len(username) < 3:  # Vérifie la longueur minimale du username
        raise ValueError("Le nom d'utilisateur doit contenir au moins 3 caractères.")  # Erreur si trop court
    if "@" not in email or len(email) < 5:  # Validation simple de l'email
        raise ValueError("Adresse e-mail invalide.")  # Erreur si email incorrect
    if len(password) < 8:  # Longueur minimale du mot de passe
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")  # Erreur si trop court
    if role not in ALLOWED_ROLES:  # Validation du rôle
        raise ValueError(f"Rôle invalide. Choisissez parmi {', '.join(ALLOWED_ROLES)}.")  # Erreur explicite

    password_hash = _hash_password(password)  # Hache le mot de passe

    sql = text(
        """
        INSERT INTO app_users (username, email, password_hash, role)
        VALUES (:username, :email, :password_hash, :role)
        RETURNING id
        """
    )  # Requête d'insertion avec retour de l'ID
    try:
        user_id = exec_sql_return_id(
            sql,
            {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "role": role,
            },
        )  # Exécute l'insertion et récupère l'ID
    except IntegrityError as exc:  # En cas de violation d'unicité
        message = str(exc).lower()  # Message d'erreur en minuscules
        if "username" in message:  # Conflit sur le username
            raise ValueError("Ce nom d'utilisateur est déjà utilisé.") from exc  # Erreur spécifique
        if "email" in message:  # Conflit sur l'email
            raise ValueError("Cette adresse e-mail est déjà utilisée.") from exc  # Erreur spécifique
        raise  # Relance l'exception pour autres cas

    created = get_user_by_id(user_id)  # Recharge l'utilisateur créé
    if not created:  # Si introuvable
        raise RuntimeError("Impossible de retrouver l'utilisateur fraîchement créé.")  # Erreur système
    return {
        "id": int(created["id"]),
        "username": created["username"],
        "email": created["email"],
        "role": created["role"],
        "created_at": created["created_at"],
    }  # Retourne les métadonnées


def _count_admins() -> int:
    df = query_df(text("SELECT COUNT(*) AS total FROM app_users WHERE role = 'admin'"))  # Compte les admins
    if df.empty:  # Si aucune ligne
        return 0  # Retourne zéro
    return int(df.iloc[0]["total"])  # Convertit le total en entier


def update_user_role(user_id: int, role: str) -> None:
    """Modifie le rôle d'un utilisateur tout en protégeant le dernier admin."""  # Docstring modification rôle

    role = (role or "").strip().lower()  # Nettoie le rôle demandé
    if role not in ALLOWED_ROLES:  # Vérifie la validité
        raise ValueError(f"Rôle invalide. Choisissez parmi {', '.join(ALLOWED_ROLES)}.")  # Erreur explicite

    user = get_user_by_id(user_id)  # Charge l'utilisateur
    if not user:  # Si introuvable
        raise ValueError("Utilisateur introuvable.")  # Erreur

    current_role = (user["role"] or "").strip().lower()  # Rôle actuel
    if current_role == role:  # Aucun changement
        return  # Sort sans action

    if current_role == "admin" and role != "admin":  # On retire un admin
        if _count_admins() <= 1:  # Vérifie s'il reste au moins un autre admin
            raise ValueError("Impossible de retirer le dernier administrateur restant.")  # Protège le dernier admin

    exec_sql(
        text("UPDATE app_users SET role = :role WHERE id = :user_id"),
        {"role": role, "user_id": int(user_id)},
    )  # Met à jour le rôle en base


def reset_user_password(user_id: int, new_password: Optional[str] = None) -> str:
    """Réinitialise le mot de passe et retourne sa valeur en clair."""  # Docstring reset

    user = get_user_by_id(user_id)  # Charge l'utilisateur
    if not user:  # Si introuvable
        raise ValueError("Utilisateur introuvable.")  # Erreur explicite

    password = (new_password or "").strip() or generate_secure_password()  # Utilise le mot de passe fourni ou en génère un
    if len(password) < 8:  # Vérifie la longueur minimale
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")  # Erreur si trop court

    password_hash = _hash_password(password)  # Hache le mot de passe
    exec_sql(
        text("UPDATE app_users SET password_hash = :password_hash WHERE id = :user_id"),
        {"password_hash": password_hash, "user_id": int(user_id)},
    )  # Met à jour le hash en base
    return password  # Retourne le mot de passe en clair (pour communication)


def bootstrap_default_admin() -> None:
    """Crée un compte admin par défaut si aucun utilisateur n'existe."""  # Docstring bootstrap admin

    # Permet de lancer le système avec un utilisateur admin connu (utile en dev/CI).

    if os.getenv("SKIP_USER_BOOTSTRAP") or os.getenv("SKIP_USER_INIT") or os.getenv("APP_ENV", "").lower() == "test":  # Permet de désactiver la création automatique
        return  # Sort si demandé

    df = query_df(text("SELECT COUNT(*) AS total FROM app_users"))  # Vérifie le nombre d'utilisateurs
    if not df.empty and int(df.iloc[0]["total"]) > 0:  # Si des utilisateurs existent déjà
        return  # Ne rien faire

    default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")  # Valeur par défaut pour l'admin
    default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")  # Email par défaut
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "InventaireAdmin123")  # Mot de passe par défaut

    create_user(default_username, default_email, default_password, role="admin")  # Crée l'utilisateur admin


def bootstrap_users_if_enabled() -> None:
    """Initialise la table utilisateurs et l'admin par défaut si autorisé."""

    if os.getenv("SKIP_USER_INIT") or os.getenv("APP_ENV", "").lower() == "test":
        return

    try:
        ensure_user_table()
        bootstrap_default_admin()
    except Exception as exc:  # pragma: no cover - on journalise pour éviter de bloquer un import
        logger.warning("Bootstrap utilisateurs ignoré (erreur DB): %s", exc)


# Le bootstrap est déclenché explicitement depuis l'application (backend/main.py) pour éviter les écritures à l'import.
