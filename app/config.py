"""Configuration centrale de la plateforme SEPIA."""
import os
import secrets

APP_NAME = "SEPIA"
APP_LONG_NAME = ("Planification, Suivi-évaluation et Apprentissage des projets et programmes "
                 "de développement")
APP_VERSION = "1.0.0"

# --- Base de données -------------------------------------------------------
# Render fournit DATABASE_URL pour PostgreSQL ; en local on retombe sur SQLite.
# Le pilote retenu est psycopg 3 : psycopg2 n'est plus maintenu activement et ne
# publie pas de roues pour les versions récentes de Python.
_raw_url = os.getenv("DATABASE_URL", "").strip()
if _raw_url.startswith("postgres://"):  # normalisation pour SQLAlchemy 2.x
    _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg://", 1)
elif _raw_url.startswith("postgresql://"):
    _raw_url = _raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

DATA_DIR = os.getenv("SEPIA_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = _raw_url or f"sqlite:///{os.path.join(DATA_DIR, 'sepia.db')}"

# --- Environnement ---------------------------------------------------------
# En production, plusieurs garde-fous deviennent bloquants plutôt que simplement
# signalés : clé de signature imposée, mot de passe administrateur imposé,
# origines restreintes, messages d'erreur non détaillés.
ENVIRONNEMENT = os.getenv("SEPIA_ENV", "production" if _raw_url else "developpement").lower()
EST_PRODUCTION = ENVIRONNEMENT.startswith("prod")

# --- Sécurité --------------------------------------------------------------
_secret = os.getenv("SEPIA_SECRET_KEY", "").strip()
if not _secret:
    if EST_PRODUCTION:
        raise RuntimeError(
            "SEPIA_SECRET_KEY doit être défini en production : sans clé de signature propre, "
            "les jetons de session de toutes les instances seraient interchangeables.")
    # En développement, une clé aléatoire par démarrage : aucune valeur ne traîne
    # dans le code source, et les sessions ne survivent pas à un redémarrage.
    _secret = secrets.token_urlsafe(48)
SECRET_KEY = _secret

TOKEN_TTL_SECONDS = int(os.getenv("SEPIA_TOKEN_TTL", str(60 * 60 * 8)))       # 8 h
TOKEN_INACTIVITE_SECONDS = int(os.getenv("SEPIA_TOKEN_INACTIVITE", str(60 * 60)))  # 1 h

ADMIN_EMAIL = os.getenv("SEPIA_ADMIN_EMAIL", "admin@sepia.org").strip().lower()
ADMIN_NAME = os.getenv("SEPIA_ADMIN_NAME", "Administrateur SEPIA")
# Aucun mot de passe par défaut dans le code : s'il n'est pas fourni, un mot de
# passe aléatoire est engendré au premier démarrage et affiché une seule fois
# dans les journaux, avec obligation de changement à la première connexion.
ADMIN_PASSWORD = os.getenv("SEPIA_ADMIN_PASSWORD", "").strip()

# Reprise de la main sur le compte d'administration lorsque son mot de passe est
# perdu. Le déclencheur est une variable d'environnement, donc accessible au seul
# détenteur du tableau de bord d'hébergement : la réinitialisation ne peut pas
# être provoquée depuis le réseau, contrairement à un point d'entrée HTTP de
# secours — qui serait, lui, une porte dérobée permanente.
ADMIN_RESET = os.getenv("SEPIA_ADMIN_RESET", "").strip().lower() in (
    "1", "true", "vrai", "oui", "yes", "on")

SEED_DEMO = os.getenv("SEPIA_SEED_DEMO", "1") not in ("0", "false", "False")

# --- Politique de mot de passe --------------------------------------------
MOT_DE_PASSE_LONGUEUR_MIN = int(os.getenv("SEPIA_MDP_LONGUEUR_MIN", "12"))
MOT_DE_PASSE_CLASSES_MIN = int(os.getenv("SEPIA_MDP_CLASSES_MIN", "3"))
# Mots de passe notoirement compromis, refusés quelle que soit leur longueur.
MOTS_DE_PASSE_INTERDITS = {
    "motdepasse", "password", "passw0rd", "azertyuiop", "qwertyuiop", "123456789",
    "administrateur", "administrator", "changeme", "letmein", "bienvenue",
    "sepia2024", "sepia2025", "projet2024", "motdepasse123", "admin1234",
}

# --- Limitation du débit ---------------------------------------------------
LIMITE_REQUETES_PAR_MINUTE = int(os.getenv("SEPIA_LIMITE_REQUETES", "240"))
LIMITE_CONNEXIONS_PAR_MINUTE = int(os.getenv("SEPIA_LIMITE_CONNEXIONS", "8"))
LIMITE_EXPORTS_PAR_MINUTE = int(os.getenv("SEPIA_LIMITE_EXPORTS", "20"))
VERROU_APRES_ECHECS = int(os.getenv("SEPIA_VERROU_ECHECS", "5"))
VERROU_DUREE_MINUTES = int(os.getenv("SEPIA_VERROU_MINUTES", "15"))

# --- Téléversement ---------------------------------------------------------
TAILLE_MAX_TELEVERSEMENT = int(os.getenv("SEPIA_TAILLE_MAX_MO", "20")) * 1024 * 1024
# Rapport de décompression au-delà duquel une archive est jugée piégée.
RATIO_DECOMPRESSION_MAX = 120
TAILLE_DECOMPRESSEE_MAX = 300 * 1024 * 1024
SIGNATURES_FICHIERS = {
    ".xlsx": [b"PK\x03\x04"], ".xlsm": [b"PK\x03\x04"], ".docx": [b"PK\x03\x04"],
    ".json": [b"{", b"[", b"\xef\xbb\xbf"],
}

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

# --- Bénéficiaires et partenaires -----------------------------------------
CATEGORIES_BENEFICIAIRES = ["Direct", "Indirect", "Final"]
TYPOLOGIES_BENEFICIAIRES = [
    "Ménage agricole", "Producteur individuel", "Organisation de producteurs",
    "Femme cheffe de ménage", "Jeune en insertion", "Élève", "Enseignant",
    "Patient", "Agent de santé", "Micro-entreprise", "Collectivité territoriale",
    "Service technique déconcentré", "Personne déplacée", "Autre",
]
NIVEAUX_VULNERABILITE = ["Très élevée", "Élevée", "Moyenne", "Faible"]
MODES_CIBLAGE = [
    "Ciblage géographique", "Ciblage communautaire participatif",
    "Ciblage catégoriel (proxy means test)", "Auto-ciblage", "Ciblage administratif",
    "Recensement exhaustif", "Ciblage mixte",
]
TYPES_PARTENAIRE = [
    "Bailleur de fonds", "Agence d'exécution", "Ministère de tutelle",
    "Collectivité territoriale", "ONG internationale", "ONG nationale",
    "Organisation de producteurs", "Secteur privé", "Institution de recherche",
    "Agence des Nations unies", "Institution financière", "Société civile",
]
TYPES_CONTRIBUTION = ["Financière", "Technique", "En nature", "Mixte", "Institutionnelle"]

# --- Évaluation : critères du CAD de l'OCDE --------------------------------
CRITERES_CAD = [
    {"cle": "pertinence", "libelle": "Pertinence",
     "question": "L'intervention répond-elle aux besoins, aux politiques et aux priorités des "
                 "bénéficiaires, du pays et des partenaires ?",
     "points_examen": "Adéquation aux besoins diagnostiqués, alignement sur les stratégies "
                      "nationales et sectorielles, qualité du ciblage, capacité d'adaptation aux "
                      "évolutions du contexte."},
    {"cle": "coherence", "libelle": "Cohérence",
     "question": "L'intervention est-elle compatible avec les autres interventions du secteur, "
                 "de l'institution et du pays ?",
     "points_examen": "Cohérence interne entre composantes, cohérence externe avec les autres "
                      "projets, complémentarité et absence de doublon, respect des normes "
                      "internationales."},
    {"cle": "efficacite", "libelle": "Efficacité",
     "question": "L'intervention atteint-elle ses objectifs et ses résultats attendus ?",
     "points_examen": "Taux d'atteinte des cibles par niveau de résultat, facteurs explicatifs "
                      "des écarts, différenciation des résultats selon les groupes de "
                      "bénéficiaires."},
    {"cle": "efficience", "libelle": "Efficience",
     "question": "Les ressources sont-elles converties en résultats de façon économique et dans "
                 "les délais ?",
     "points_examen": "Coût unitaire par bénéficiaire, rapport coût-efficacité, respect du "
                      "calendrier, qualité de la gestion financière et des procédures."},
    {"cle": "impact", "libelle": "Impact",
     "question": "Quels effets de grande ampleur, positifs ou négatifs, intentionnels ou non, "
                 "l'intervention a-t-elle produits ?",
     "points_examen": "Changements durables observés, effets attribuables établis par une "
                      "méthode contrefactuelle, effets non intentionnels, effets "
                      "transformationnels."},
    {"cle": "durabilite", "libelle": "Durabilité",
     "question": "Les bénéfices vont-ils perdurer après la fin de l'intervention ?",
     "points_examen": "Appropriation par les acteurs nationaux, viabilité financière et "
                      "institutionnelle, capacités transférées, durabilité environnementale."},
]
ECHELLE_NOTATION_CAD = [
    {"note": 6, "libelle": "Très satisfaisant", "couleur": "#0F9D58"},
    {"note": 5, "libelle": "Satisfaisant", "couleur": "#4CAF50"},
    {"note": 4, "libelle": "Plutôt satisfaisant", "couleur": "#9CCC65"},
    {"note": 3, "libelle": "Plutôt insatisfaisant", "couleur": "#F9A825"},
    {"note": 2, "libelle": "Insatisfaisant", "couleur": "#EA8600"},
    {"note": 1, "libelle": "Très insatisfaisant", "couleur": "#D93025"},
]
TYPES_EVALUATION = ["Référence", "Mi-parcours", "Finale", "Ex post", "Thématique", "Impact"]

# --- Évaluation d'impact : méthodes ---------------------------------------
METHODES_IMPACT = [
    {"cle": "rct", "libelle": "Essai contrôlé randomisé (RCT)", "approche": "Expérimentale",
     "hypothese": "L'assignation aléatoire rend les groupes de traitement et de contrôle "
                  "comparables en espérance sur toutes les caractéristiques, observables ou non.",
     "conditions": "Affectation aléatoire maîtrisée par l'évaluateur, taille d'échantillon "
                   "suffisante, absence de contamination entre groupes.",
     "forces": "Validité interne la plus élevée ; l'effet estimé est causal sans hypothèse "
               "supplémentaire.",
     "limites": "Coût et délais élevés, questions éthiques liées à l'exclusion, validité externe "
                "parfois limitée, difficilement applicable à un programme déjà déployé."},
    {"cle": "rct_grappes", "libelle": "Randomisation par grappes", "approche": "Expérimentale",
     "hypothese": "Même hypothèse que le RCT, l'unité d'assignation étant la grappe (village, "
                  "école, centre de santé) et non l'individu.",
     "conditions": "Nombre de grappes suffisant, corrélation intra-grappe estimée, prise en "
                   "compte de l'effet de grappe dans le calcul de puissance.",
     "forces": "Limite la contamination entre bénéficiaires et non-bénéficiaires ; adaptée aux "
               "interventions collectives.",
     "limites": "Perte de puissance statistique proportionnelle à la corrélation intra-grappe ; "
                "exige beaucoup plus d'unités."},
    {"cle": "did", "libelle": "Doubles différences (DID)", "approche": "Quasi-expérimentale",
     "hypothese": "Tendances parallèles : en l'absence d'intervention, les deux groupes auraient "
                  "évolué de façon identique.",
     "conditions": "Données avant et après pour les deux groupes ; idéalement plusieurs périodes "
                   "avant l'intervention pour tester le parallélisme.",
     "forces": "Neutralise les différences initiales constantes entre groupes et les chocs "
               "communs ; applicable rétrospectivement.",
     "limites": "L'hypothèse de tendances parallèles n'est pas testable sur la période post ; "
                "sensible aux chocs différenciés concomitants."},
    {"cle": "psm", "libelle": "Appariement sur score de propension (PSM)",
     "approche": "Quasi-expérimentale",
     "hypothese": "Indépendance conditionnelle : conditionnellement aux variables observées, la "
                  "participation est indépendante des résultats potentiels.",
     "conditions": "Richesse des variables observées, support commun suffisant entre traités et "
                   "non-traités, équilibre des covariables après appariement.",
     "forces": "Applicable sans données antérieures ; construit un groupe de comparaison "
               "statistiquement proche.",
     "limites": "Ne corrige que la sélection sur observables ; un biais de sélection sur des "
                "caractéristiques non observées demeure."},
    {"cle": "did_psm", "libelle": "Doubles différences appariées (DID + PSM)",
     "approche": "Quasi-expérimentale",
     "hypothese": "Combinaison : tendances parallèles au sein du support commun apparié.",
     "conditions": "Données de panel et variables d'appariement disponibles.",
     "forces": "Corrige simultanément la sélection sur observables et les différences initiales "
               "invariantes dans le temps.",
     "limites": "Exigences en données cumulées des deux méthodes."},
    {"cle": "rdd", "libelle": "Régression sur discontinuité (RDD)",
     "approche": "Quasi-expérimentale",
     "hypothese": "Continuité : au voisinage immédiat du seuil d'éligibilité, les unités situées "
                  "de part et d'autre sont comparables.",
     "conditions": "Règle d'éligibilité fondée sur un score continu et un seuil strict, densité "
                   "continue au seuil, absence de manipulation du score.",
     "forces": "Validité interne proche de l'expérimentation au voisinage du seuil ; exploite "
               "une règle administrative existante.",
     "limites": "L'effet estimé n'est valide qu'au voisinage du seuil ; exige un effectif "
                "important autour de celui-ci."},
    {"cle": "iv", "libelle": "Variables instrumentales (IV)", "approche": "Quasi-expérimentale",
     "hypothese": "L'instrument influence la participation sans affecter directement le résultat "
                  "autrement que par elle (restriction d'exclusion).",
     "conditions": "Instrument pertinent (corrélation forte avec la participation) et exogène.",
     "forces": "Traite l'endogénéité de la participation, y compris sur des caractéristiques non "
               "observées.",
     "limites": "La restriction d'exclusion n'est pas testable ; l'effet estimé ne vaut que pour "
                "les unités sensibles à l'instrument."},
    {"cle": "controle_synthetique", "libelle": "Contrôle synthétique",
     "approche": "Quasi-expérimentale",
     "hypothese": "Une combinaison pondérée d'unités non traitées reproduit la trajectoire "
                  "antérieure de l'unité traitée.",
     "conditions": "Longue série avant l'intervention, petit nombre d'unités traitées, réservoir "
                   "d'unités de comparaison.",
     "forces": "Adaptée aux interventions territoriales portant sur peu d'unités.",
     "limites": "Inférence statistique délicate ; dépend de la qualité de l'ajustement "
                "antérieur."},
    {"cle": "avant_apres", "libelle": "Comparaison avant-après", "approche": "Non expérimentale",
     "hypothese": "Absence de tendance et de choc externe entre les deux mesures — hypothèse "
                  "rarement défendable.",
     "conditions": "Mesures avant et après sur le groupe traité.",
     "forces": "Simple et peu coûteuse ; utile pour un suivi descriptif.",
     "limites": "Ne permet pas d'attribuer causalement les changements observés : à ne pas "
                "présenter comme une évaluation d'impact."},
]
APPROCHES_IMPACT = ["Expérimentale", "Quasi-expérimentale", "Non expérimentale"]
STATUTS_IMPACT = ["Conçue", "Baseline réalisée", "Collecte en cours", "Analysée", "Publiée"]
