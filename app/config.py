"""Configuration centrale de la plateforme SEPIA."""
import os

APP_NAME = "SEPIA"
APP_LONG_NAME = "Système d'Évaluation, de Planification, d'Indicateurs et d'Apprentissage"
APP_VERSION = "1.0.0"

# --- Base de données -------------------------------------------------------
# Render fournit DATABASE_URL pour PostgreSQL ; en local on retombe sur SQLite.
_raw_url = os.getenv("DATABASE_URL", "").strip()
if _raw_url.startswith("postgres://"):  # normalisation pour SQLAlchemy 2.x
    _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif _raw_url.startswith("postgresql://"):
    _raw_url = _raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

DATA_DIR = os.getenv("SEPIA_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = _raw_url or f"sqlite:///{os.path.join(DATA_DIR, 'sepia.db')}"

# --- Sécurité --------------------------------------------------------------
SECRET_KEY = os.getenv("SEPIA_SECRET_KEY", "sepia-dev-secret-change-me-in-production")
TOKEN_TTL_SECONDS = int(os.getenv("SEPIA_TOKEN_TTL", str(60 * 60 * 12)))  # 12 h

ADMIN_EMAIL = os.getenv("SEPIA_ADMIN_EMAIL", "admin@sepia.org")
ADMIN_PASSWORD = os.getenv("SEPIA_ADMIN_PASSWORD", "sepia2024")
ADMIN_NAME = os.getenv("SEPIA_ADMIN_NAME", "Administrateur SEPIA")

SEED_DEMO = os.getenv("SEPIA_SEED_DEMO", "1") not in ("0", "false", "False")

# --- Référentiels métier ---------------------------------------------------
NIVEAUX_CADRE_LOGIQUE = ["IMPACT", "EFFET", "PRODUIT", "ACTIVITE"]
LIBELLES_NIVEAUX = {
    "IMPACT": "Impact / Objectif global",
    "EFFET": "Effet / Objectif spécifique (Outcome)",
    "PRODUIT": "Produit / Extrant (Output)",
    "ACTIVITE": "Activité",
}
FREQUENCES = ["Mensuelle", "Trimestrielle", "Semestrielle", "Annuelle", "Ponctuelle", "Mi-parcours", "Finale"]
TYPES_INDICATEUR = ["Quantitatif", "Qualitatif", "Composite", "Proxy"]
STATUTS_PROJET = ["Identification", "Formulation", "En cours", "Suspendu", "Clôturé"]
CATEGORIES_RISQUE = [
    "Politique / Gouvernance", "Sécuritaire", "Financier / Budgétaire", "Opérationnel",
    "Technique", "Environnemental / Climatique", "Social / Genre", "Sanitaire",
    "Institutionnel / Capacités", "Réputationnel",
]
TYPES_QUESTION = [
    "text", "integer", "decimal", "select_one", "select_multiple", "date",
    "time", "geopoint", "note", "calculate", "image", "barcode",
]
