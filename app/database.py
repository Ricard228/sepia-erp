"""Session SQLAlchemy, déclaration de base et mise à niveau légère du schéma."""
import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL

logger = logging.getLogger("sepia.database")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Types SQL des colonnes ajoutées après la première mise en service. SQLite comme
# PostgreSQL acceptent l'ajout d'une colonne nullable sans réécriture de table.
_TYPES_SQL = {
    "INTEGER": "INTEGER", "FLOAT": "DOUBLE PRECISION", "DATE": "DATE",
    "DATETIME": "TIMESTAMP", "BOOLEAN": "BOOLEAN", "JSON": "JSON", "TEXT": "TEXT",
}


def assurer_schema() -> list:
    """Ajoute les colonnes déclarées dans le modèle mais absentes de la base.

    Évite d'imposer une migration manuelle après une mise à jour de l'application :
    les instances déjà déployées récupèrent les nouvelles colonnes au redémarrage.
    Les colonnes supprimées ou modifiées ne sont volontairement pas traitées —
    elles relèvent d'une migration explicite.
    """
    ajoutees = []
    inspecteur = inspect(engine)
    tables_existantes = set(inspecteur.get_table_names())
    dialecte = engine.dialect.name
    with engine.begin() as connexion:
        for table in Base.metadata.sorted_tables:
            if table.name not in tables_existantes:
                continue
            colonnes_presentes = {c["name"] for c in inspecteur.get_columns(table.name)}
            for colonne in table.columns:
                if colonne.name in colonnes_presentes or colonne.primary_key:
                    continue
                type_generique = colonne.type.__class__.__name__.upper()
                if type_generique.startswith("VARCHAR") or type_generique == "STRING":
                    longueur = getattr(colonne.type, "length", None) or 255
                    type_sql = f"VARCHAR({longueur})"
                else:
                    type_sql = _TYPES_SQL.get(type_generique, "TEXT")
                if dialecte == "sqlite" and type_sql == "DOUBLE PRECISION":
                    type_sql = "REAL"
                try:
                    connexion.execute(
                        text(f'ALTER TABLE {table.name} ADD COLUMN "{colonne.name}" {type_sql}'))
                    ajoutees.append(f"{table.name}.{colonne.name}")
                except Exception as exc:  # colonne déjà présente ou type non supporté
                    logger.warning("Colonne %s.%s non ajoutée : %s", table.name, colonne.name, exc)
    if ajoutees:
        logger.info("Schéma mis à niveau : %s", ", ".join(ajoutees))
    return ajoutees
