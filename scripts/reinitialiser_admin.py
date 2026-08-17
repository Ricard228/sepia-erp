"""Reprise de la main sur le compte d'administration de SEPIA.

À utiliser lorsque le mot de passe de l'administrateur est perdu, que le compte
a été verrouillé par des tentatives infructueuses, désactivé, ou rétrogradé par
erreur. Le compte est recréé s'il a disparu.

    python scripts/reinitialiser_admin.py
    python scripts/reinitialiser_admin.py --adresse pilotage@exemple.org
    SEPIA_ADMIN_PASSWORD='<phrase de passe>' python scripts/reinitialiser_admin.py

Sans mot de passe fourni, un mot de passe conforme à la politique est engendré et
affiché une seule fois. Dans tous les cas, son changement est exigé à la première
connexion et les sessions ouvertes sont fermées.

Le script agit directement sur la base désignée par DATABASE_URL — donc sur la
base de production si cette variable y pointe. Il n'expose aucun point d'entrée
réseau : la reprise de main suppose un accès au serveur ou à sa base, ce qui est
la seule preuve d'autorité acceptable ici. Sur un hébergement sans accès shell,
utiliser plutôt la variable SEPIA_ADMIN_RESET (voir le README, § 8).
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Réinitialise le compte d'administration de SEPIA.")
    analyseur.add_argument("--adresse", help="Adresse du compte à réinitialiser ou à créer "
                                             "(par défaut : SEPIA_ADMIN_EMAIL).")
    analyseur.add_argument("--sans-confirmation", action="store_true",
                           help="N'attend pas de confirmation interactive.")
    arguments = analyseur.parse_args()

    if arguments.adresse:
        import os
        os.environ["SEPIA_ADMIN_EMAIL"] = arguments.adresse.strip().lower()

    from app import config
    from app.database import Base, SessionLocal, engine
    from app import models  # noqa: F401  — enregistre les tables sur Base
    from app.seed import reinitialiser_administrateur

    cible = "PostgreSQL" if config.DATABASE_URL.startswith("postgresql") else "SQLite"
    print(f"Base        : {cible}")
    print(f"Compte visé : {config.ADMIN_EMAIL}")
    if not arguments.sans_confirmation:
        reponse = input("Confirmer la réinitialisation ? [oui/non] ").strip().lower()
        if reponse not in ("oui", "o", "yes", "y"):
            print("Abandon : aucune modification.")
            return 1

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        mot_de_passe = reinitialiser_administrateur(db)
    finally:
        db.close()

    barre = "=" * 78
    print(f"\n{barre}\n  COMPTE ADMINISTRATEUR RÉINITIALISÉ")
    print(f"  Adresse      : {config.ADMIN_EMAIL}")
    print(f"  Mot de passe : {mot_de_passe}")
    print("  Changement exigé à la connexion ; les sessions ouvertes ont été fermées.")
    print(barre)
    return 0


if __name__ == "__main__":
    sys.exit(main())
