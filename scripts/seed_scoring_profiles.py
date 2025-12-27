#!/usr/bin/env python3
"""
Script pour initialiser les profils de scoring fournisseur.

Usage:
    python scripts/seed_scoring_profiles.py --tenant-id 1
    python scripts/seed_scoring_profiles.py --tenant-id 4
    python scripts/seed_scoring_profiles.py --all
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.finance.supplier_scoring_profiles import seed_default_profiles, ScoringProfileManager


def seed_for_tenant(tenant_id: int):
    """Initialise les profils pour un tenant."""
    print(f"\nInitialisation des profils de scoring pour tenant_id={tenant_id}")
    print("=" * 70)

    try:
        profiles = seed_default_profiles(tenant_id)

        print(f"\n{len(profiles)} profils créés avec succès:\n")

        for name, profile in profiles.items():
            print(f"  [{profile.id}] {name}")
            print(f"      Description: {profile.description}")
            print(f"      Défaut: {'Oui' if profile.is_default else 'Non'}")
            print(f"      Poids:")
            for dim, weight in profile.weights_dict.items():
                print(f"        - {dim}: {weight}%")
            print()

    except Exception as e:
        print(f"Erreur lors de l'initialisation: {e}")
        raise


def list_profiles(tenant_id: int):
    """Liste les profils existants."""
    print(f"\nProfils existants pour tenant_id={tenant_id}")
    print("=" * 70)

    manager = ScoringProfileManager(tenant_id)
    profiles = manager.list_profiles()

    if not profiles:
        print("  Aucun profil trouvé.")
        return

    for profile in profiles:
        print(f"\n  [{profile.id}] {profile.name}")
        print(f"      Description: {profile.description}")
        print(f"      Défaut: {'Oui' if profile.is_default else 'Non'}")
        print(f"      Poids:")
        for dim, weight in profile.weights_dict.items():
            print(f"        - {dim}: {weight}%")


def main():
    parser = argparse.ArgumentParser(
        description="Initialise les profils de scoring fournisseur"
    )
    parser.add_argument(
        "--tenant-id",
        type=int,
        help="ID du tenant pour lequel créer les profils"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Créer les profils pour tous les tenants (1 et 4)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lister les profils existants au lieu de les créer"
    )

    args = parser.parse_args()

    if args.list:
        if args.tenant_id:
            list_profiles(args.tenant_id)
        elif args.all:
            list_profiles(1)
            list_profiles(4)
        else:
            print("Erreur: Spécifiez --tenant-id ou --all")
            sys.exit(1)
    else:
        if args.all:
            seed_for_tenant(1)
            seed_for_tenant(4)
        elif args.tenant_id:
            seed_for_tenant(args.tenant_id)
        else:
            print("Erreur: Spécifiez --tenant-id ou --all")
            sys.exit(1)

    print("\nTerminé!")


if __name__ == "__main__":
    main()
