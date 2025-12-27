"""Helpers de service utilisateur avec backends de stockage injectables."""

from __future__ import annotations

import hmac
import hashlib
import secrets
import string
from dataclasses import dataclass
from typing import Any, Mapping, Protocol


PASSWORD_ITERATIONS = 390_000
HASH_ALGORITHM = "pbkdf2_sha256"
ALLOWED_ROLES: tuple[str, ...] = ("admin", "manager", "standard")
DEFAULT_PASSWORD_LENGTH = 14
MIN_PASSWORD_LENGTH = 8
DEFAULT_SYMBOLS = "!$%&*@#?"


class UserRepository(Protocol):
    """Interface de stockage requise par les helpers de service utilisateur."""

    def get_user_by_login(self, identifier: str) -> Mapping[str, Any] | None:
        ...

    def get_user_by_id(self, user_id: int) -> Mapping[str, Any] | None:
        ...

    def create_user(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        ...

    def update_user_role(self, user_id: int, role: str) -> None:
        ...

    def update_user_password(self, user_id: int, password_hash: str) -> None:
        ...

    def count_admins(self) -> int:
        ...


@dataclass(frozen=True)
class PasswordPolicy:
    """Politique de génération de mot de passe."""

    length: int = DEFAULT_PASSWORD_LENGTH
    min_length: int = MIN_PASSWORD_LENGTH
    symbols: str = DEFAULT_SYMBOLS
    require_lower: bool = True
    require_upper: bool = True
    require_digit: bool = True
    require_symbol: bool = True


def normalize_identifier(value: str | None) -> str:
    """Normalise une chaîne d'identifiant."""
    return (value or "").strip()


def generate_secure_password(policy: PasswordPolicy | None = None) -> str:
    """Génère un mot de passe robuste conforme à la politique fournie."""
    policy = policy or PasswordPolicy()

    if policy.length < policy.min_length:
        raise ValueError(f"Password length must be at least {policy.min_length}.")

    pools: list[str] = []
    if policy.require_lower:
        pools.append(string.ascii_lowercase)
    if policy.require_upper:
        pools.append(string.ascii_uppercase)
    if policy.require_digit:
        pools.append(string.digits)
    if policy.require_symbol:
        if not policy.symbols:
            raise ValueError("Symbols are required but none provided.")
        pools.append(policy.symbols)

    if not pools:
        raise ValueError("At least one character group must be required.")

    required_chars = [secrets.choice(pool) for pool in pools]
    remaining = policy.length - len(required_chars)
    all_chars = "".join(pools)

    candidate_chars = required_chars + [secrets.choice(all_chars) for _ in range(remaining)]
    secrets.SystemRandom().shuffle(candidate_chars)
    return "".join(candidate_chars)


def hash_password(password: str, *, iterations: int = PASSWORD_ITERATIONS) -> str:
    """Hache un mot de passe via PBKDF2-HMAC-SHA256."""
    if not password:
        raise ValueError("Password must not be empty.")
    if iterations <= 0:
        raise ValueError("Iterations must be positive.")

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{HASH_ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Vérifie un mot de passe par rapport à une empreinte stockée."""
    try:
        algorithm, iter_str, salt_hex, digest_hex = encoded.split("$")
    except ValueError:
        return False

    if algorithm != HASH_ALGORITHM:
        return False

    try:
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False

    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(computed, expected)


def get_user_by_login(repo: UserRepository, identifier: str) -> Mapping[str, Any] | None:
    """Retourne un utilisateur par identifiant de connexion ou None."""
    cleaned = normalize_identifier(identifier).lower()
    if not cleaned:
        return None
    return repo.get_user_by_login(cleaned)


def get_user_by_id(repo: UserRepository, user_id: int) -> Mapping[str, Any] | None:
    """Retourne un utilisateur par id numérique ou None."""
    if user_id is None:
        return None
    return repo.get_user_by_id(int(user_id))


def authenticate_user(
    repo: UserRepository,
    identifier: str,
    password: str,
) -> dict[str, Any] | None:
    """Valide les identifiants et renvoie les métadonnées utilisateur nettoyées."""
    if not identifier or not password:
        return None

    user = get_user_by_login(repo, identifier)
    if not user:
        return None

    stored_hash = user.get("password_hash")
    if not stored_hash or not verify_password(password, str(stored_hash)):
        return None

    return {
        "id": int(user.get("id")) if user.get("id") is not None else None,
        "username": user.get("username"),
        "email": user.get("email"),
        "role": user.get("role"),
        "created_at": user.get("created_at"),
    }


def create_user(
    repo: UserRepository,
    username: str,
    email: str,
    password: str,
    *,
    role: str = "standard",
) -> dict[str, Any]:
    """Crée un utilisateur via le dépôt."""
    clean_username = normalize_identifier(username)
    clean_email = normalize_identifier(email).lower()
    clean_password = normalize_identifier(password)
    clean_role = normalize_identifier(role).lower() or "standard"

    if len(clean_username) < 3:
        raise ValueError("Username must be at least 3 characters.")
    if "@" not in clean_email or len(clean_email) < 5:
        raise ValueError("Invalid email address.")
    if len(clean_password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if clean_role not in ALLOWED_ROLES:
        raise ValueError(f"Invalid role. Choose from {', '.join(ALLOWED_ROLES)}.")

    password_hash = hash_password(clean_password)
    payload = {
        "username": clean_username,
        "email": clean_email,
        "password_hash": password_hash,
        "role": clean_role,
    }
    created = repo.create_user(payload)
    return {
        "id": int(created.get("id")) if created.get("id") is not None else None,
        "username": created.get("username") or clean_username,
        "email": created.get("email") or clean_email,
        "role": created.get("role") or clean_role,
        "created_at": created.get("created_at"),
    }


def update_user_role(repo: UserRepository, user_id: int, role: str) -> None:
    """Met à jour le rôle d'un utilisateur tout en protégeant le dernier admin."""
    clean_role = normalize_identifier(role).lower()
    if clean_role not in ALLOWED_ROLES:
        raise ValueError(f"Invalid role. Choose from {', '.join(ALLOWED_ROLES)}.")

    user = get_user_by_id(repo, user_id)
    if not user:
        raise ValueError("User not found.")

    current_role = normalize_identifier(str(user.get("role", ""))).lower()
    if current_role == clean_role:
        return

    if current_role == "admin" and clean_role != "admin":
        if repo.count_admins() <= 1:
            raise ValueError("Cannot remove the last remaining admin.")

    repo.update_user_role(int(user_id), clean_role)


def reset_user_password(
    repo: UserRepository,
    user_id: int,
    *,
    new_password: str | None = None,
    policy: PasswordPolicy | None = None,
) -> str:
    """Réinitialise le mot de passe d'un utilisateur et renvoie le clair."""
    user = get_user_by_id(repo, user_id)
    if not user:
        raise ValueError("User not found.")

    password = normalize_identifier(new_password) if new_password else ""
    if not password:
        password = generate_secure_password(policy)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")

    repo.update_user_password(int(user_id), hash_password(password))
    return password


__all__ = [
    "ALLOWED_ROLES",
    "DEFAULT_PASSWORD_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "PASSWORD_ITERATIONS",
    "PasswordPolicy",
    "UserRepository",
    "authenticate_user",
    "create_user",
    "generate_secure_password",
    "get_user_by_id",
    "get_user_by_login",
    "hash_password",
    "normalize_identifier",
    "reset_user_password",
    "update_user_role",
    "verify_password",
]
