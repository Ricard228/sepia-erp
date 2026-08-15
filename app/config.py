"""Configuration centrale de la plateforme SEPIA."""
import os

APP_NAME = "SEPIA"
APP_LONG_NAME = ("Planification, Suivi-évaluation et Apprentissage des projets et programmes "
                 "de développement")
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

# --- Désagrégation des indicateurs -----------------------------------------
# Chaque catégorie de désagrégation porte ses modalités : la saisie et les
# agrégations s'appuient sur ces listes pour garantir la comparabilité des
# données d'une période et d'une zone à l'autre.
MODALITES_DESAGREGATION = {
    "Sexe": ["Femme", "Homme"],
    "Âge": ["Moins de 18 ans", "18 à 35 ans", "36 à 59 ans", "60 ans et plus"],
    "Milieu": ["Urbain", "Rural"],
    "Groupe cible": ["Producteur", "Transformatrice", "Jeune", "Femme cheffe de ménage",
                     "Personne en situation de handicap", "Personne déplacée", "Autre"],
    "Situation de handicap": ["Avec handicap", "Sans handicap"],
    "Niveau de vulnérabilité": ["Très vulnérable", "Vulnérable", "Non vulnérable"],
    "Statut d'occupation": ["Propriétaire", "Locataire", "Usufruitier"],
}
CATEGORIES_DESAGREGATION = list(MODALITES_DESAGREGATION.keys())

# Catégorie servant au calcul de l'indice d'équité de genre.
CATEGORIE_GENRE = "Sexe"
MODALITE_FEMME = "Femme"

# --- Zones d'intervention --------------------------------------------------
NIVEAUX_ZONE = ["Pays", "Région", "Préfecture", "Commune", "Canton", "Village", "Site"]

# --- Qualité des indicateurs : critères SMART ------------------------------
CRITERES_SMART = [
    {"cle": "specifique", "libelle": "Spécifique",
     "question": "L'indicateur mesure-t-il sans ambiguïté un aspect précis du résultat ?",
     "controle": "Un libellé précis et une définition opérationnelle sont renseignés."},
    {"cle": "mesurable", "libelle": "Mesurable",
     "question": "L'indicateur est-il quantifiable ou objectivement appréciable ?",
     "controle": "Une unité de mesure et un mode de calcul sont renseignés."},
    {"cle": "atteignable", "libelle": "Atteignable",
     "question": "La cible est-elle réaliste au regard des moyens mobilisés ?",
     "controle": "Une valeur de référence et une cible cohérentes sont renseignées."},
    {"cle": "pertinent", "libelle": "Pertinent",
     "question": "L'indicateur rend-il compte du changement recherché ?",
     "controle": "L'indicateur est rattaché à un résultat du cadre logique."},
    {"cle": "temporel", "libelle": "Temporellement défini",
     "question": "L'indicateur est-il assorti d'une échéance et d'une fréquence ?",
     "controle": "Une échéance de cible et une fréquence de collecte sont renseignées."},
]

SEUILS_QUALITE = [(90, "Excellente"), (75, "Bonne"), (60, "Acceptable"), (0, "Insuffisante")]

# --- Rapportage périodique -------------------------------------------------
TYPES_RAPPORT = [
    {"cle": "trimestriel", "libelle": "Rapport trimestriel de suivi", "granularite": "T"},
    {"cle": "semestriel", "libelle": "Rapport semestriel d'avancement", "granularite": "S"},
    {"cle": "annuel", "libelle": "Rapport annuel de performance", "granularite": "A"},
]
