"""Modèle de données SEPIA — ERP de planification et de suivi-évaluation.

Couverture fonctionnelle :
  * Portefeuille : projets, programmes, membres d'équipe
  * Planification : cadre logique, chaîne de résultats, théorie du changement
  * Indicateurs : métadonnées SMART, cibles périodiques, réalisations désagrégées
  * Risques & hypothèses : registre coté, matrice probabilité/impact, plan de mitigation
  * Opérationnel : activités (chronogramme/Gantt), PTBA, lignes budgétaires
  * Collecte : fiches et questionnaires (export Word + XLSForm KoboToolbox/ODK)
  * Traçabilité : journal d'audit
"""
from datetime import date, datetime

from sqlalchemy import (
    JSON, Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# Utilisateurs et droits
# ---------------------------------------------------------------------------
class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(160), unique=True, nullable=False, index=True)
    full_name = Column(String(160), nullable=False)
    password_hash = Column(String(256), nullable=False)
    # admin | coordonnateur | suivi_evaluation | operateur | lecteur
    role = Column(String(40), default="suivi_evaluation", nullable=False)
    organisation = Column(String(160))
    phone = Column(String(40))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)


class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_member"),)
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(60), default="lecteur")
    user = relationship("User")


# ---------------------------------------------------------------------------
# Portefeuille
# ---------------------------------------------------------------------------
class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    code = Column(String(40), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    acronym = Column(String(40))
    description = Column(Text)
    # Contexte institutionnel
    sector = Column(String(120))
    sub_sector = Column(String(120))
    country = Column(String(120), default="Togo")
    regions = Column(JSON, default=list)          # zones d'intervention
    donor = Column(String(200))                   # PTF / bailleur
    executing_agency = Column(String(200))        # agence d'exécution
    supervising_ministry = Column(String(200))
    beneficiaries = Column(Text)
    target_population = Column(Integer)
    # Cycle de vie
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(40), default="En cours")
    phase = Column(String(60))
    # Finances
    currency = Column(String(10), default="FCFA")
    total_budget = Column(Float, default=0.0)
    counterpart_budget = Column(Float, default=0.0)
    # Alignement stratégique
    theory_of_change = Column(Text)
    strategic_alignment = Column(JSON, default=dict)  # ODD, PND, stratégies sectorielles
    me_approach = Column(Text)                        # approche de S&E retenue
    created_by = Column(Integer, ForeignKey("users.id"))

    logframe = relationship("LogframeElement", back_populates="project", cascade="all, delete-orphan")
    indicators = relationship("Indicator", back_populates="project", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="project", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="project", cascade="all, delete-orphan")
    budget_lines = relationship("BudgetLine", back_populates="project", cascade="all, delete-orphan")
    forms = relationship("Form", back_populates="project", cascade="all, delete-orphan")
    zones = relationship("Zone", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Cadre logique / chaîne de résultats
# ---------------------------------------------------------------------------
class LogframeElement(Base, TimestampMixin):
    """Un maillon de la chaîne de résultats (Impact / Effet / Produit / Activité)."""
    __tablename__ = "logframe_elements"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("logframe_elements.id", ondelete="CASCADE"))
    level = Column(String(20), nullable=False)     # IMPACT | EFFET | PRODUIT | ACTIVITE
    code = Column(String(30))                      # ex. OS1, P1.2, A1.2.3
    statement = Column(Text, nullable=False)       # libellé du résultat
    description = Column(Text)
    means_of_verification = Column(Text)           # sources de vérification
    assumptions = Column(Text)                     # hypothèses critiques associées
    responsible = Column(String(160))
    order_index = Column(Integer, default=0)

    project = relationship("Project", back_populates="logframe")
    parent = relationship("LogframeElement", remote_side=[id], backref="children")
    indicators = relationship("Indicator", back_populates="element")


class Assumption(Base, TimestampMixin):
    """Hypothèse critique suivie dans le temps (pendant du registre des risques)."""
    __tablename__ = "assumptions"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    element_id = Column(Integer, ForeignKey("logframe_elements.id", ondelete="SET NULL"))
    code = Column(String(30))
    statement = Column(Text, nullable=False)
    level = Column(String(20))                      # niveau du cadre logique concerné
    criticality = Column(String(20), default="Moyenne")   # Faible | Moyenne | Élevée
    # Vérifiée | Partiellement vérifiée | Non vérifiée | Invalidée
    validation_status = Column(String(40), default="Non vérifiée")
    verification_method = Column(Text)
    responsible = Column(String(160))
    review_date = Column(Date)
    comment = Column(Text)


# ---------------------------------------------------------------------------
# Indicateurs
# ---------------------------------------------------------------------------
class Indicator(Base, TimestampMixin):
    """Fiche métadonnée complète d'un indicateur (norme CAD-OCDE / GAR)."""
    __tablename__ = "indicators"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    element_id = Column(Integer, ForeignKey("logframe_elements.id", ondelete="SET NULL"), index=True)
    code = Column(String(30))
    name = Column(Text, nullable=False)
    definition = Column(Text)                       # définition opérationnelle
    level = Column(String(20))                      # IMPACT | EFFET | PRODUIT | ACTIVITE
    indicator_type = Column(String(30), default="Quantitatif")
    unit = Column(String(60), default="Nombre")     # Nombre, %, Ratio, Score, FCFA...
    formula = Column(Text)                          # mode de calcul
    numerator = Column(Text)
    denominator = Column(Text)
    disaggregation = Column(JSON, default=list)     # ["Sexe", "Âge", "Région", "Milieu"]
    # Référence et cible
    baseline_value = Column(Float)
    baseline_date = Column(Date)
    baseline_source = Column(String(200))
    target_value = Column(Float)
    target_date = Column(Date)
    direction = Column(String(20), default="Croissant")   # Croissant | Décroissant | Stable
    # Collecte
    frequency = Column(String(40), default="Trimestrielle")
    # Règle de consolidation des mesures d'une même période collectées sur
    # plusieurs zones ou activités : Somme (effectifs, volumes), Moyenne (taux,
    # ratios, scores) ou Dernière valeur (stocks, états à une date).
    aggregation = Column(String(20), default="Somme")
    data_source = Column(String(300))
    collection_method = Column(String(200))         # enquête, registre, focus group...
    responsible = Column(String(160))
    reporting_level = Column(String(120))
    cost_estimate = Column(Float)
    # Qualité
    smart_check = Column(JSON, default=dict)        # {"specifique": true, ...}
    smart_score = Column(Float)                     # note sur 100, issue de la revue SMART
    smart_reviewed_at = Column(Date)
    smart_comment = Column(Text)
    quality_note = Column(Text)
    is_key = Column(Boolean, default=False)         # indicateur clé de performance
    is_active = Column(Boolean, default=True)

    project = relationship("Project", back_populates="indicators")
    element = relationship("LogframeElement", back_populates="indicators")
    targets = relationship("IndicatorTarget", back_populates="indicator", cascade="all, delete-orphan")
    actuals = relationship("IndicatorActual", back_populates="indicator", cascade="all, delete-orphan")


class IndicatorTarget(Base, TimestampMixin):
    """Cible périodique (jalon) d'un indicateur."""
    __tablename__ = "indicator_targets"
    id = Column(Integer, primary_key=True)
    indicator_id = Column(Integer, ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False, index=True)
    period_label = Column(String(40), nullable=False)   # "2025-T1", "2025", "Mi-parcours"
    year = Column(Integer)
    period_start = Column(Date)
    period_end = Column(Date)
    target_value = Column(Float)
    comment = Column(Text)
    indicator = relationship("Indicator", back_populates="targets")


class IndicatorActual(Base, TimestampMixin):
    """Valeur réalisée, désagrégée et localisée.

    Une mesure peut être rattachée à une zone d'intervention et à l'activité qui
    l'a produite : c'est ce qui permet la consolidation par zone et par activité,
    et l'analyse de l'équité (genre, groupe cible) au niveau du projet.
    """
    __tablename__ = "indicator_actuals"
    id = Column(Integer, primary_key=True)
    indicator_id = Column(Integer, ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False, index=True)
    period_label = Column(String(40), nullable=False)
    year = Column(Integer)
    reference_date = Column(Date, default=date.today)
    value = Column(Float)
    # {"Sexe": {"Femme": 120, "Homme": 95}, "Groupe cible": {"Jeune": 80, ...}}
    disaggregated_values = Column(JSON, default=dict)
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="SET NULL"), index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="SET NULL"), index=True)
    source = Column(String(300))
    collected_by = Column(String(160))
    validation_status = Column(String(30), default="Brouillon")  # Brouillon|Validé|Rejeté
    validated_by = Column(String(160))
    comment = Column(Text)
    indicator = relationship("Indicator", back_populates="actuals")
    zone = relationship("Zone")


class Zone(Base, TimestampMixin):
    """Zone d'intervention du projet (hiérarchie administrative ou opérationnelle)."""
    __tablename__ = "zones"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("zones.id", ondelete="SET NULL"))
    code = Column(String(30))
    name = Column(String(160), nullable=False)
    level = Column(String(30), default="Région")     # Région | Préfecture | Commune | Village…
    population = Column(Integer)
    beneficiaries_target = Column(Integer)           # cible de bénéficiaires sur la zone
    latitude = Column(Float)
    longitude = Column(Float)
    responsible = Column(String(160))
    comment = Column(Text)
    order_index = Column(Integer, default=0)

    parent = relationship("Zone", remote_side=[id], backref="children")


# ---------------------------------------------------------------------------
# Risques
# ---------------------------------------------------------------------------
class Risk(Base, TimestampMixin):
    __tablename__ = "risks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    element_id = Column(Integer, ForeignKey("logframe_elements.id", ondelete="SET NULL"))
    code = Column(String(30))
    title = Column(Text, nullable=False)
    category = Column(String(80))
    description = Column(Text)
    cause = Column(Text)
    consequence = Column(Text)
    probability = Column(Integer, default=3)        # 1 à 5
    impact = Column(Integer, default=3)             # 1 à 5
    mitigation = Column(Text)                       # mesures d'atténuation
    contingency = Column(Text)                      # plan de contingence
    owner = Column(String(160))
    status = Column(String(40), default="Ouvert")   # Ouvert|Maîtrisé|Clos|Survenu
    residual_probability = Column(Integer)
    residual_impact = Column(Integer)
    review_date = Column(Date)
    linked_assumption_id = Column(Integer, ForeignKey("assumptions.id", ondelete="SET NULL"))

    project = relationship("Project", back_populates="risks")

    @property
    def score(self) -> int:
        return (self.probability or 0) * (self.impact or 0)

    @property
    def severity(self) -> str:
        s = self.score
        if s >= 15:
            return "Critique"
        if s >= 10:
            return "Élevé"
        if s >= 5:
            return "Modéré"
        return "Faible"


# ---------------------------------------------------------------------------
# Activités, chronogramme et PTBA
# ---------------------------------------------------------------------------
class Activity(Base, TimestampMixin):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    element_id = Column(Integer, ForeignKey("logframe_elements.id", ondelete="SET NULL"), index=True)
    code = Column(String(30))
    name = Column(Text, nullable=False)
    description = Column(Text)
    responsible = Column(String(160))
    partners = Column(String(300))
    location = Column(String(200))
    start_date = Column(Date)
    end_date = Column(Date)
    progress = Column(Float, default=0.0)           # 0-100 %
    status = Column(String(40), default="Planifiée")  # Planifiée|En cours|Achevée|Retardée|Annulée
    dependencies = Column(String(200))              # codes d'activités prérequises
    planned_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    year = Column(Integer)
    milestone = Column(Boolean, default=False)
    deliverable = Column(Text)
    order_index = Column(Integer, default=0)

    project = relationship("Project", back_populates="activities")


class BudgetLine(Base, TimestampMixin):
    """Ligne de PTBA / budget détaillé, ventilée par trimestre."""
    __tablename__ = "budget_lines"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="SET NULL"), index=True)
    code = Column(String(40))
    label = Column(Text, nullable=False)
    category = Column(String(120))                  # Personnel, Équipement, Formation...
    unit = Column(String(60))
    quantity = Column(Float, default=1)
    unit_cost = Column(Float, default=0)
    frequency_count = Column(Float, default=1)      # nombre de répétitions
    funding_source = Column(String(160))
    year = Column(Integer)
    q1 = Column(Float, default=0)
    q2 = Column(Float, default=0)
    q3 = Column(Float, default=0)
    q4 = Column(Float, default=0)
    committed = Column(Float, default=0)            # engagé
    disbursed = Column(Float, default=0)            # décaissé
    comment = Column(Text)

    project = relationship("Project", back_populates="budget_lines")

    @property
    def total_planned(self) -> float:
        return round((self.quantity or 0) * (self.unit_cost or 0) * (self.frequency_count or 1), 2)


# ---------------------------------------------------------------------------
# Fiches de collecte et questionnaires
# ---------------------------------------------------------------------------
class Form(Base, TimestampMixin):
    __tablename__ = "forms"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(40))
    name = Column(String(300), nullable=False)
    description = Column(Text)
    form_type = Column(String(60), default="Questionnaire")  # Questionnaire|Fiche de suivi|Grille FGD|Fiche de présence
    target_respondent = Column(String(200))
    periodicity = Column(String(60))
    linked_indicators = Column(JSON, default=list)  # codes d'indicateurs renseignés
    instructions = Column(Text)
    version = Column(String(20), default="1.0")
    language = Column(String(10), default="fr")

    project = relationship("Project", back_populates="forms")
    questions = relationship("FormQuestion", back_populates="form",
                             cascade="all, delete-orphan", order_by="FormQuestion.order_index")


class FormQuestion(Base, TimestampMixin):
    __tablename__ = "form_questions"
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=0)
    section = Column(String(160))
    name = Column(String(80), nullable=False)        # nom technique XLSForm
    label = Column(Text, nullable=False)
    question_type = Column(String(40), default="text")
    choices = Column(JSON, default=list)             # [{"name": "1", "label": "Oui"}]
    required = Column(Boolean, default=False)
    constraint = Column(String(300))
    constraint_message = Column(String(300))
    relevant = Column(String(300))                   # logique de saut
    calculation = Column(String(300))
    hint = Column(Text)
    appearance = Column(String(80))
    default_value = Column(String(120))
    linked_indicator_code = Column(String(30))

    form = relationship("Form", back_populates="questions")


class FormSubmission(Base, TimestampMixin):
    """Réponse saisie directement dans la plateforme (mode web-mobile)."""
    __tablename__ = "form_submissions"
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_by = Column(String(160))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    location = Column(String(200))
    period_label = Column(String(40))
    answers = Column(JSON, default=dict)
    status = Column(String(30), default="Soumis")


# ---------------------------------------------------------------------------
# Traçabilité
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    at = Column(DateTime, default=datetime.utcnow)
    user_email = Column(String(160))
    action = Column(String(60))
    entity = Column(String(60))
    entity_id = Column(Integer)
    project_id = Column(Integer)
    detail = Column(Text)
