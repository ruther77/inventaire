"""Utilities for managing database backup files.

This module centralises backup related operations used by the Streamlit
administration dashboard.  It exposes helpers to create, inspect, restore and
remove PostgreSQL dumps stored on disk.  Each function is intentionally small
and testable so that the UI can simply call them without having to mock any
Streamlit specific behaviour.
"""  # Docstring du module backup
from __future__ import annotations  # Active les annotations différées

import gzip  # Compression/décompression des dumps
import json  # Lecture/écriture des paramètres de backup
import os  # Accès à l'environnement et au système de fichiers
import re  # Nettoyage des labels
import shutil  # Localisation de binaires et copies éventuelles
import subprocess  # Exécution de commandes externes (pg_dump/psql)
from dataclasses import dataclass  # Structures simples pour métadonnées
from datetime import datetime, timedelta, timezone  # Dates/horodatages
from pathlib import Path  # Chemins de fichiers
from statistics import mean  # Calcul de moyenne
from typing import Dict, Iterable, List, Optional, Tuple  # Typage utilitaire

from sqlalchemy.engine import URL  # Construction d'URL SQLAlchemy
from sqlalchemy.engine.url import make_url  # Parsing d'URL SQLAlchemy


class BackupError(RuntimeError):
    """Raised when a backup operation cannot be completed."""  # Exception métier pour les backups


@dataclass(frozen=True, slots=True)
class BackupMetadata:
    """Simple container describing a backup file present on disk."""  # Métadonnées d'un fichier backup

    name: str  # Nom de fichier
    path: Path  # Chemin complet
    size_bytes: int  # Taille en octets
    created_at: datetime  # Horodatage de création

    @property
    def size_mb(self) -> float:
        """Human friendly representation in megabytes."""  # Taille en Mo

        return self.size_bytes / (1024 * 1024)  # Conversion octets -> Mo


_DEFAULT_BACKUP_LOCATIONS: Tuple[Path, ...] = (
    Path("/app/backups"),
    Path("backups"),
)  # Emplacements par défaut des sauvegardes

_SETTINGS_FILENAME = "backup_settings.json"  # Nom du fichier de configuration
_DEFAULT_SETTINGS: Dict[str, object] = {
    "frequency": "daily",  # daily | weekly | manual
    "time": "02:00",
    "weekday": 0,  # lundi
    "retention_days": 30,
    "max_backups": 20,
    "notifications": [],
    "integrity_checks": True,
}  # Paramètres par défaut

_PG_DUMP_ENV_VARS: Tuple[str, ...] = ("PG_DUMP_PATH", "PG_DUMP_BIN")  # Variables pour pg_dump
_PSQL_ENV_VARS: Tuple[str, ...] = ("PSQL_PATH", "PSQL_BIN")  # Variables pour psql


@dataclass(frozen=True, slots=True)
class BinaryStatus:
    """Describe how a required external command is resolved."""  # Statut d'un binaire externe

    name: str  # Nom logique (pg_dump/psql)
    configured: str  # Chemin configuré (argument/env/default)
    resolved: Optional[str]  # Chemin résolu réel
    source: str  # Source de la résolution

    @property
    def available(self) -> bool:
        return self.resolved is not None  # Indique si le binaire est présent


def _settings_path(directory: str | os.PathLike[str] | None = None) -> Path:
    return get_backup_directory(directory, create=True) / _SETTINGS_FILENAME  # Chemin complet du fichier de config


def load_backup_settings(
    directory: str | os.PathLike[str] | None = None,
) -> Dict[str, object]:
    """Return persisted backup automation settings."""  # Docstring chargement paramètres

    # The configuration is stored as JSON next to the backup files so that
    # Streamlit sessions can recover the last saved preferences.

    path = _settings_path(directory)  # Résout le chemin du fichier
    if not path.exists():  # Si inexistant
        return dict(_DEFAULT_SETTINGS)  # Retourne les valeurs par défaut

    # Le flux principal : pg_dump écrit dans stdout, on gzippe ensuite le résultat.
    # Cette fonction est appelée par l’administration pour générer un snapshot
    # et renvoyer immédiatement les métadonnées au front.
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))  # Lit et parse le JSON
    except (OSError, json.JSONDecodeError):  # Erreur d'E/S ou JSON invalide
        return dict(_DEFAULT_SETTINGS)  # Fallback défaut

    settings: Dict[str, object] = dict(_DEFAULT_SETTINGS)  # Copie des defaults
    settings.update({k: v for k, v in payload.items() if k in _DEFAULT_SETTINGS})  # Merge des clés reconnues
    return settings  # Retourne les paramètres


def save_backup_settings(
    settings: Dict[str, object],
    directory: str | os.PathLike[str] | None = None,
) -> None:
    """Persist backup automation settings to disk."""  # Docstring sauvegarde paramètres

    payload = dict(_DEFAULT_SETTINGS)  # Base default
    payload.update({k: v for k, v in settings.items() if k in _DEFAULT_SETTINGS})  # Mise à jour des valeurs fournies
    path = _settings_path(directory)  # Chemin du fichier
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")  # Écriture JSON


def get_backup_directory(
    directory: str | os.PathLike[str] | None = None,
    *,
    create: bool = True,
) -> Path:
    """Return the directory used to store backup files."""  # Docstring répertoire backup

    # Args:
    #     directory: Optional override path.  When omitted the BACKUP_DIR
    #         environment variable is used, or ``/app/backups`` (falling back to
    #         ``./backups`` if the former cannot be created).
    #     create: Whether the directory should be created when missing.
    #
    # Returns:
    #     A :class:`~pathlib.Path` object pointing to the backup folder.

    candidates: Tuple[Path, ...]  # Liste de candidats
    if directory is not None:  # Si un répertoire est fourni
        candidates = (Path(directory),)  # Utilise uniquement celui-ci
    else:
        env_directory = os.getenv("BACKUP_DIR")  # Cherche variable d'env
        if env_directory:
            candidates = (Path(env_directory),)  # Utilise l'env
        else:
            candidates = _DEFAULT_BACKUP_LOCATIONS  # Sinon les défauts

    for candidate in candidates:  # Parcourt les candidats
        path = candidate  # Chemin courant
        if create:  # Si création autorisée
            try:
                path.mkdir(parents=True, exist_ok=True)  # Tente de créer
            except PermissionError:  # Si interdiction
                continue  # Essaie le prochain candidat
        return path  # Retourne le premier valide

    # If all automatic locations failed because of permissions, fall back to a
    # relative directory that Streamlit can create in the working tree.
    fallback = Path("backups")  # Dossier relatif fallback
    if create:
        fallback.mkdir(parents=True, exist_ok=True)  # Crée le fallback
    return fallback  # Retourne le fallback


def _select_binary(
    explicit: Optional[str],
    *,
    env_vars: Tuple[str, ...],
    default: str,
    argument_label: str,
) -> Tuple[str, str]:
    """Return the binary path and describe how it was resolved."""  # Docstring sélection binaire

    if explicit:  # Si chemin explicitement fourni
        return explicit, f"l'argument {argument_label}"  # Retourne chemin + source

    for env_var in env_vars:  # Parcourt les variables d'env
        value = os.getenv(env_var)  # Lit la variable
        if value:  # Si définie
            return value, f"la variable d'environnement {env_var}"  # Retourne valeur + source

    return default, "la valeur par défaut du système"  # Fallback sur valeur par défaut


def _format_env_var_hint(env_vars: Tuple[str, ...]) -> str:
    if not env_vars:  # Si aucune variable
        return ""  # Chaîne vide
    if len(env_vars) == 1:  # Une seule
        return env_vars[0]  # Retourne telle quelle
    return ", ".join(env_vars[:-1]) + f" ou {env_vars[-1]}"  # Format liste ou


def _resolve_binary_location(command: str) -> Optional[str]:
    """Return the absolute location of *command* if available."""  # Docstring résolution chemin

    path = Path(command)  # Convertit en Path
    if path.is_absolute() or path.parent != Path("."):  # Si absolu ou avec dossier
        if path.exists() and os.access(path, os.X_OK):  # Vérifie existence + exécutable
            return str(path.resolve())  # Retourne chemin résolu
        return None  # Sinon absent

    return shutil.which(command)  # Recherche dans le PATH


def _normalise_database_url(database_url: str) -> Tuple[str, Optional[str]]:
    """Return a ``postgresql://`` URL compatible with psql/pg_dump."""  # Docstring normalisation URL

    # SQLAlchemy URLs can embed the driver name (``postgresql+psycopg2``) which
    # is not understood by the PostgreSQL command line tools.  The function also
    # extracts the password so it can be provided via the ``PGPASSWORD``
    # environment variable instead of appearing on the command line.

    original = make_url(database_url)  # Parse l'URL fournie
    driver = original.drivername.split("+")[0]  # Retire le suffixe driver

    clean_url = URL.create(
        driver,
        username=original.username,
        password=None,
        host=original.host,
        port=original.port,
        database=original.database,
        query=original.query,
    )  # Reconstruit une URL propre sans mot de passe

    return clean_url.render_as_string(hide_password=False), original.password  # Retourne URL clean + mdp


def _prepare_env(password: Optional[str]) -> dict:
    env = os.environ.copy()  # Copie l'environnement actuel
    if password:  # Si mot de passe fourni
        env["PGPASSWORD"] = password  # Place le mdp pour pg_dump/psql
    return env  # Retourne l'environnement enrichi


def _build_backup_name(label: Optional[str]) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")  # Timestamp UTC
    if not label:  # Si aucun label
        return f"epicerie_backup_{timestamp}.sql.gz"  # Nom par défaut

    cleaned = re.sub(r"[^0-9A-Za-z_-]+", "-", label).strip("-_")  # Nettoie le label
    cleaned = cleaned.lower()  # Minuscule
    if not cleaned:  # Si après nettoyage vide
        return f"epicerie_backup_{timestamp}.sql.gz"  # Nom par défaut

    return f"epicerie_backup_{timestamp}_{cleaned}.sql.gz"  # Nom avec label


def list_backups(
    directory: str | os.PathLike[str] | None = None,
) -> List[BackupMetadata]:
    """Return backup metadata sorted from newest to oldest."""  # Docstring listage backups

    # Le flux commence par l’inspection du dossier : la liste finale est
    # triée du plus récent au plus ancien pour alimenter le tableau de bord.
    backup_dir = get_backup_directory(directory, create=False)  # Résout le dossier
    if not backup_dir.exists():  # Si inexistant
        return []  # Retourne vide

    entries: List[BackupMetadata] = []  # Collection de métadonnées
    for item in backup_dir.iterdir():  # Parcourt les fichiers du dossier
        if not item.is_file():  # Ignore les non-fichiers
            continue
        if not item.name.endswith((".sql", ".sql.gz")):  # Filtre extension
            continue

        stat = item.stat()  # Infos fichier
        created = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)  # Horodatage
        entries.append(
            BackupMetadata(
                name=item.name,
                path=item,
                size_bytes=stat.st_size,
                created_at=created,
            )
        )  # Ajoute la métadonnée

    entries.sort(key=lambda meta: meta.created_at, reverse=True)  # Trie du plus récent au plus ancien
    return entries  # Retourne la liste


def build_backup_timeline(backups: Iterable[BackupMetadata]) -> List[dict]:
    """Return a serialisable timeline structure for visualisations."""  # Docstring timeline

    return [
        {
            "name": backup.name,
            "created_at": backup.created_at,
            "size_mb": backup.size_mb,
        }
        for backup in backups
    ]  # Liste de dicts pour visualisation


def compute_backup_statistics(backups: Iterable[BackupMetadata]) -> Dict[str, float]:
    """Compute aggregate statistics (min/max/average/total sizes)."""  # Docstring statistiques

    sizes = [backup.size_mb for backup in backups]  # Liste des tailles en Mo
    if not sizes:  # Si aucune sauvegarde
        return {"total_size_mb": 0.0, "average_size_mb": 0.0, "max_size_mb": 0.0, "min_size_mb": 0.0}  # Valeurs nulles

    return {
        "total_size_mb": float(sum(sizes)),  # Somme totale
        "average_size_mb": float(mean(sizes)),  # Moyenne
        "max_size_mb": float(max(sizes)),  # Max
        "min_size_mb": float(min(sizes)),  # Min
    }  # Retourne les stats


def suggest_retention_cleanup(
    backups: Iterable[BackupMetadata],
    *,
    retention_days: int | None = None,
    max_backups: int | None = None,
) -> List[BackupMetadata]:
    """Return backups that should be pruned according to retention rules."""  # Docstring nettoyage rétention

    retention = retention_days if retention_days is not None and retention_days > 0 else None  # Rétention en jours
    maximum = max_backups if max_backups is not None and max_backups > 0 else None  # Nombre max

    backups_list = list(backups)  # Liste matérielle
    prune: List[BackupMetadata] = []  # Liste des éléments à supprimer

    if retention is not None:  # Si règle de rétention
        threshold = datetime.now(timezone.utc) - timedelta(days=int(retention))  # Date seuil
        prune.extend([b for b in backups_list if b.created_at < threshold])  # Ajoute ceux trop vieux

    if maximum is not None and len(backups_list) > maximum:  # Si limitation en nombre
        # Keep the newest entries first, drop the rest from the end
        excess = backups_list[maximum:]  # Sélectionne les plus anciens au-delà du max
        prune.extend(excess)  # Ajoute à la liste de purge

    # Deduplicate while preserving order of appearance in ``backups_list``
    seen: set[str] = set()  # Suivi des noms déjà vus
    ordered: List[BackupMetadata] = []  # Liste ordonnée sans doublon
    for item in backups_list:  # Parcourt les backups
        if item in prune and item.name not in seen:  # Si à supprimer et non déjà ajouté
            seen.add(item.name)  # Marque comme vu
            ordered.append(item)  # Ajoute dans l'ordre d'origine
    return ordered  # Retourne la liste des backups à supprimer


def plan_next_backup(
    settings: Dict[str, object],
    *,
    last_backup: Optional[BackupMetadata] = None,
    now: Optional[datetime] = None,
) -> Optional[datetime]:
    """Compute the next scheduled backup datetime in local timezone."""  # Docstring planification

    frequency = str(settings.get("frequency", "manual"))  # Fréquence choisie
    if frequency == "manual":  # Manuel => aucune planification
        return None  # Pas de prochaine date

    reference = (now or datetime.now(timezone.utc)).astimezone()  # Référence temporelle locale
    base_date = reference.date()  # Date du jour

    time_str = str(settings.get("time", "02:00"))  # Heure souhaitée
    try:
        hour, minute = [int(part) for part in time_str.split(":", 1)]  # Parse HH:MM
    except (ValueError, TypeError):
        hour, minute = 2, 0  # Fallback 02:00

    candidate = datetime.combine(base_date, datetime.min.time()).astimezone()  # Base jour courant minuit
    candidate = candidate.replace(hour=hour, minute=minute)  # Applique l'heure choisie

    if frequency == "daily":  # Fréquence quotidienne
        if candidate <= reference:  # Si heure déjà passée
            candidate = candidate + timedelta(days=1)  # Report au lendemain
    elif frequency == "weekly":  # Fréquence hebdomadaire
        weekday = int(settings.get("weekday", 0)) % 7  # Jour de la semaine (0=lundi)
        days_ahead = (weekday - candidate.weekday()) % 7  # Décalage nécessaire
        candidate = candidate + timedelta(days=days_ahead)  # Applique le décalage
        if candidate <= reference:  # Si déjà passé
            candidate = candidate + timedelta(days=7)  # Report à la semaine suivante
    else:
        return None  # Fréquence inconnue => pas de planification

    if last_backup and last_backup.created_at.astimezone() >= candidate:  # Si dernier backup après la date prévue
        increment = timedelta(days=1 if frequency == "daily" else 7)  # Incrément selon fréquence
        candidate = last_backup.created_at.astimezone() + increment  # Replanifie après le dernier backup

    return candidate  # Retourne la prochaine date planifiée


def check_backup_integrity(
    metadata: BackupMetadata,
) -> Tuple[bool, str]:
    """Perform lightweight integrity checks on a backup file."""  # Docstring check intégrité

    path = metadata.path  # Chemin du fichier
    if not path.exists():  # Fichier absent
        return False, "Fichier introuvable"  # Statut échec

    if path.stat().st_size <= 0:  # Taille nulle
        return False, "Archive vide"  # Statut échec

    if path.suffix == ".gz":  # Si archive gzip
        try:
            with gzip.open(path, "rb") as buffer:  # Ouvre en lecture
                buffer.read(1)  # Tente de lire 1 octet
        except OSError as exc:  # Erreur lecture
            return False, f"Archive corrompue: {exc}"  # Statut échec

    return True, "OK"  # Succès


def integrity_report(backups: Iterable[BackupMetadata]) -> List[dict]:
    """Return integrity status for all provided backups."""  # Docstring rapport intégrité

    report: List[dict] = []  # Liste des statuts
    for backup in backups:  # Parcourt chaque backup
        ok, message = check_backup_integrity(backup)  # Vérifie l'intégrité
        report.append(
            {
                "name": backup.name,  # Nom du fichier
                "created_at": backup.created_at,  # Date de création
                "status": "✅" if ok else "⚠️",  # Emoji statut
                "details": message,  # Détail du check
            }
        )
    return report  # Retourne le rapport


def _resolve_backup_path(
    filename: str,
    directory: str | os.PathLike[str] | None = None,
) -> Path:
    backup_dir = get_backup_directory(directory, create=False)  # Résout le répertoire
    path = backup_dir / filename  # Chemin du fichier
    if not path.exists():  # Fichier absent
        raise BackupError(f"Le fichier de sauvegarde '{filename}' est introuvable.")  # Erreur
    if not path.is_file():  # Si ce n'est pas un fichier
        raise BackupError(f"Le chemin '{filename}' n'est pas un fichier de sauvegarde valide.")  # Erreur
    return path  # Retourne le chemin validé


def create_backup(
    *,
    label: Optional[str] = None,
    database_url: Optional[str] = None,
    backup_dir: str | os.PathLike[str] | None = None,
    pg_dump_path: Optional[str] = None,
) -> BackupMetadata:
    """Create a new backup using ``pg_dump`` and return its metadata."""  # Docstring création backup

    database_url = database_url or os.getenv("DATABASE_URL")  # URL DB
    if not database_url:  # Si absent
        raise BackupError("Aucune configuration de base de données trouvée.")  # Erreur

    normalised_url, password = _normalise_database_url(database_url)  # Normalise l'URL
    env = _prepare_env(password)  # Prépare l'environnement pour pg_dump

    pg_dump_path, pg_dump_source = _select_binary(
        pg_dump_path,
        env_vars=_PG_DUMP_ENV_VARS,
        default="pg_dump",
        argument_label="pg_dump_path",
    )  # Résout le binaire pg_dump

    backup_directory = get_backup_directory(backup_dir, create=True)  # Assure le dossier backup
    filename = _build_backup_name(label)  # Génère le nom de fichier
    target_path = backup_directory / filename  # Chemin cible

    try:
        completed = subprocess.run(
            [pg_dump_path, normalised_url],  # Commande pg_dump
            check=True,  # Lève exception si échec
            stdout=subprocess.PIPE,  # Capture stdout
            env=env,  # Environnement avec PGPASSWORD
        )
    except FileNotFoundError as exc:  # Binaire introuvable
        raise BackupError(
            "L'outil 'pg_dump' est introuvable (chemin utilisé : "
            f"{pg_dump_path!r} depuis {pg_dump_source}). Assurez-vous que le "
            "client PostgreSQL est installé et que l'utilitaire est présent "
            "dans le PATH ou définissez les variables d'environnement "
            f"{_format_env_var_hint(_PG_DUMP_ENV_VARS)}."
        ) from exc
    except subprocess.CalledProcessError as exc:  # Erreur pg_dump
        raise BackupError("La commande pg_dump a échoué.") from exc

    with gzip.open(target_path, "wb") as buffer:  # Ouvre le fichier gzip en écriture
        buffer.write(completed.stdout)  # Écrit la sortie pg_dump compressée

    stat = target_path.stat()  # Récupère les stats du fichier
    return BackupMetadata(
        name=filename,
        path=target_path,
        size_bytes=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
    )  # Retourne les métadonnées du backup


def delete_backup(
    filename: str,
    *,
    backup_dir: str | os.PathLike[str] | None = None,
) -> None:
    """Delete an existing backup file."""  # Docstring suppression backup

    path = _resolve_backup_path(filename, directory=backup_dir)  # Valide le chemin
    path.unlink()  # Supprime le fichier


def restore_backup(
    filename: str,
    *,
    database_url: Optional[str] = None,
    backup_dir: str | os.PathLike[str] | None = None,
    psql_path: Optional[str] = None,
) -> None:
    """Restore the database using the provided backup file."""  # Docstring restauration

    database_url = database_url or os.getenv("DATABASE_URL")  # URL DB
    if not database_url:  # Absente
        raise BackupError("Aucune configuration de base de données trouvée.")  # Erreur

    normalised_url, password = _normalise_database_url(database_url)  # URL normalisée
    env = _prepare_env(password)  # Environnement avec PGPASSWORD

    path = _resolve_backup_path(filename, directory=backup_dir)  # Valide le fichier
    psql_path, psql_source = _select_binary(
        psql_path,
        env_vars=_PSQL_ENV_VARS,
        default="psql",
        argument_label="psql_path",
    )  # Résout le binaire psql

    if path.suffix == ".gz":  # Si gzip
        with gzip.open(path, "rb") as buffer:  # Ouvre en lecture
            payload = buffer.read()  # Lit les données
    else:
        payload = path.read_bytes()  # Lit le fichier brut

    # On injecte le fichier dans psql ; cette opération écrase la base
    # cible avec l’image compressée fournie par l’utilisateur.
    try:
        subprocess.run(
            [psql_path, normalised_url],  # Commande psql
            input=payload,  # Données du dump
            check=True,  # Vérifie le code retour
            env=env,  # Environnement avec PGPASSWORD
        )
    except FileNotFoundError as exc:  # psql introuvable
        raise BackupError(
            "L'outil 'psql' est introuvable (chemin utilisé : "
            f"{psql_path!r} depuis {psql_source}). Assurez-vous que le client "
            "PostgreSQL est installé et que l'utilitaire est présent dans le "
            "PATH ou définissez les variables d'environnement "
            f"{_format_env_var_hint(_PSQL_ENV_VARS)}."
        ) from exc
    except subprocess.CalledProcessError as exc:  # Échec psql
        raise BackupError("La commande psql a échoué lors de la restauration.") from exc


def check_backup_tools(
    *,
    pg_dump_path: Optional[str] = None,
    psql_path: Optional[str] = None,
) -> Tuple[BinaryStatus, BinaryStatus]:
    """Return diagnostic information about pg_dump and psql availability."""  # Docstring diagnostic binaires

    pg_dump, pg_dump_source = _select_binary(
        pg_dump_path,
        env_vars=_PG_DUMP_ENV_VARS,
        default="pg_dump",
        argument_label="pg_dump_path",
    )  # Résout pg_dump
    psql, psql_source = _select_binary(
        psql_path,
        env_vars=_PSQL_ENV_VARS,
        default="psql",
        argument_label="psql_path",
    )  # Résout psql

    pg_dump_resolved = _resolve_binary_location(pg_dump)  # Chemin réel pg_dump
    psql_resolved = _resolve_binary_location(psql)  # Chemin réel psql

    return (
        BinaryStatus("pg_dump", pg_dump, pg_dump_resolved, pg_dump_source),
        BinaryStatus("psql", psql, psql_resolved, psql_source),
    )  # Retourne le diagnostic des deux outils


__all__ = [
    "BackupError",
    "BackupMetadata",
    "BinaryStatus",
    "check_backup_tools",
    "create_backup",
    "delete_backup",
    "get_backup_directory",
    "list_backups",
    "restore_backup",
]  # Exporte les symboles publics
