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
    # --- Sécurité du compte
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(80))
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)            # verrouillage temporaire après échecs
    password_changed_at = Column(DateTime)
    must_change_password = Column(Boolean, default=False)
    # Invalide tous les jetons émis avant cette date (déconnexion globale).
    tokens_valid_from = Column(DateTime)


class ApiKey(Base, TimestampMixin):
    """Clé d'accès en lecture seule, destinée aux connecteurs de business intelligence.

    Une clé dédiée évite de faire circuler le jeton de session dans une URL
    Power BI : elle est révocable individuellement, limitée à la lecture et
    traçable, et son empreinte seule est conservée.
    """
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(120), nullable=False)
    prefix = Column(String(12), nullable=False, index=True)   # partie visible, pour retrouver la clé
    key_hash = Column(String(256), nullable=False)            # empreinte du secret
    scope = Column(String(40), default="lecture")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    revoked = Column(Boolean, default=False)

    user = relationship("User")


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
    # Options d'affichage : le suivi des processus alourdit le dispositif et
    # n'est pertinent que sur certains projets ; il est donc activable projet
    # par projet, sans jamais supprimer les données déjà saisies.
    show_process_indicators = Column(Boolean, default=False)
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
    # Groupe de bénéficiaires dont l'indicateur mesure la situation : il relie la
    # mesure à la population concernée et permet d'agréger la performance par groupe.
    beneficiary_id = Column(Integer, ForeignKey("beneficiaries.id", ondelete="SET NULL"), index=True)
    code = Column(String(30))
    name = Column(Text, nullable=False)
    definition = Column(Text)                       # définition opérationnelle
    level = Column(String(20))                      # IMPACT | EFFET | PRODUIT | ACTIVITE
    # Nature de l'indicateur : « Résultat » mesure un changement, « Processus »
    # mesure la conduite de l'action (taux d'exécution, délais, participation,
    # respect du calendrier). L'affichage des indicateurs de processus est
    # commandé par l'option correspondante du projet.
    indicator_class = Column(String(20), default="Résultat")
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
    # Antécédents pour l'ordonnancement : codes d'activités séparés par des
    # virgules, relation fin-début (l'activité ne peut démarrer qu'une fois
    # ses antécédents achevés).
    dependencies = Column(String(200))
    duration_days = Column(Integer)                 # durée imposée ; sinon déduite des dates
    wbs_code = Column(String(40))                   # code d'organigramme des tâches
    planned_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    year = Column(Integer)
    milestone = Column(Boolean, default=False)
    deliverable = Column(Text)
    order_index = Column(Integer, default=0)

    project = relationship("Project", back_populates="activities")


class Beneficiary(Base, TimestampMixin):
    """Groupe de bénéficiaires : ciblage, effectifs désagrégés et caractérisation qualitative.

    Un projet ne s'adresse jamais à une population indifférenciée : il cible des
    groupes dont les besoins, les contraintes et les critères d'éligibilité
    diffèrent. Cette entité les documente et permet de rattacher chaque
    indicateur au groupe dont il mesure la situation.
    """
    __tablename__ = "beneficiaries"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(30))
    name = Column(String(200), nullable=False)
    category = Column(String(80))              # Direct | Indirect | Final
    typology = Column(String(120))             # Ménage, producteur, élève, structure…
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="SET NULL"), index=True)

    # --- Quantitatif : ciblage et atteinte, désagrégés
    target_total = Column(Integer)             # effectif ciblé
    target_women = Column(Integer)
    target_youth = Column(Integer)
    target_disabled = Column(Integer)
    reached_total = Column(Integer)            # effectif effectivement atteint
    reached_women = Column(Integer)
    reached_youth = Column(Integer)
    reached_disabled = Column(Integer)
    households = Column(Integer)               # nombre de ménages concernés
    average_household_size = Column(Float)
    baseline_income = Column(Float)            # revenu moyen de référence
    poverty_rate = Column(Float)               # taux de pauvreté du groupe (%)

    # --- Qualitatif : ciblage, besoins, participation
    selection_criteria = Column(Text)          # critères d'éligibilité
    selection_method = Column(Text)            # ciblage géographique, communautaire, auto-ciblage…
    needs = Column(Text)                       # besoins exprimés lors du diagnostic
    constraints = Column(Text)                 # contraintes d'accès aux services du projet
    expected_benefits = Column(Text)
    participation_mode = Column(Text)          # modalités d'implication dans la mise en œuvre
    vulnerability_level = Column(String(40))   # Très élevée | Élevée | Moyenne | Faible
    grievance_mechanism = Column(Text)         # mécanisme de plainte accessible au groupe
    comment = Column(Text)
    order_index = Column(Integer, default=0)

    zone = relationship("Zone")

    @property
    def taux_atteinte(self):
        if not self.target_total:
            return None
        return round((self.reached_total or 0) / self.target_total * 100, 1)

    @property
    def part_femmes_atteintes(self):
        if not self.reached_total:
            return None
        return round((self.reached_women or 0) / self.reached_total * 100, 1)


class Partner(Base, TimestampMixin):
    """Partenaire du projet : nature de la collaboration, engagement et performance."""
    __tablename__ = "partners"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(30))
    name = Column(String(200), nullable=False)
    partner_type = Column(String(80))          # Bailleur, ONG, État, secteur privé, recherche…
    role = Column(Text)                        # rôle dans le dispositif
    country = Column(String(120))
    # --- Engagement contractuel
    agreement_reference = Column(String(120))  # référence de la convention
    agreement_start = Column(Date)
    agreement_end = Column(Date)
    financial_commitment = Column(Float)       # montant engagé
    financial_disbursed = Column(Float)        # montant effectivement versé
    currency = Column(String(10))
    contribution_type = Column(String(120))    # Financière, technique, en nature, mixte
    in_kind_description = Column(Text)
    # --- Suivi de la relation
    obligations = Column(Text)
    deliverables = Column(Text)
    performance_rating = Column(Integer)       # appréciation 1 à 5
    performance_comment = Column(Text)
    risks = Column(Text)                       # risques liés au partenariat
    contact_name = Column(String(160))
    contact_email = Column(String(160))
    contact_phone = Column(String(60))
    status = Column(String(40), default="Actif")
    order_index = Column(Integer, default=0)

    @property
    def taux_decaissement(self):
        if not self.financial_commitment:
            return None
        return round((self.financial_disbursed or 0) / self.financial_commitment * 100, 1)


class Evaluation(Base, TimestampMixin):
    """Exercice évaluatif apprécié selon les six critères du CAD de l'OCDE."""
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(30))
    title = Column(String(300), nullable=False)
    # Référence | Mi-parcours | Finale | Ex post | Thématique | Impact
    evaluation_type = Column(String(60), default="Mi-parcours")
    period_covered = Column(String(80))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(40), default="Planifiée")   # Planifiée|En cours|Achevée|Validée
    evaluator = Column(String(200))
    independence = Column(String(60))          # Interne | Externe indépendante | Mixte
    budget = Column(Float)
    methodology = Column(Text)
    data_sources = Column(Text)
    sampling = Column(Text)
    limitations = Column(Text)
    # Notes sur 6 et justifications, un couple par critère du CAD
    scores = Column(JSON, default=dict)        # {"pertinence": 5, ...}
    justifications = Column(JSON, default=dict)
    key_findings = Column(Text)
    lessons_learned = Column(Text)
    overall_comment = Column(Text)
    report_reference = Column(String(200))

    recommendations = relationship("EvaluationRecommendation", cascade="all, delete-orphan",
                                   back_populates="evaluation")

    @property
    def note_globale(self):
        valeurs = [v for v in (self.scores or {}).values()
                   if isinstance(v, (int, float)) and v > 0]
        return round(sum(valeurs) / len(valeurs), 2) if valeurs else None


class EvaluationRecommendation(Base, TimestampMixin):
    """Recommandation issue d'une évaluation, suivie jusqu'à sa mise en œuvre."""
    __tablename__ = "evaluation_recommendations"
    id = Column(Integer, primary_key=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    code = Column(String(30))
    criterion = Column(String(60))             # critère du CAD concerné
    statement = Column(Text, nullable=False)
    priority = Column(String(20), default="Moyenne")   # Élevée | Moyenne | Faible
    responsible = Column(String(160))
    deadline = Column(Date)
    # Acceptée | Partiellement acceptée | Rejetée
    management_response = Column(String(60), default="Acceptée")
    response_comment = Column(Text)
    implementation_status = Column(String(40), default="Non démarrée")
    implementation_rate = Column(Float, default=0.0)
    evidence = Column(Text)

    evaluation = relationship("Evaluation", back_populates="recommendations")


class ImpactStudy(Base, TimestampMixin):
    """Devis d'évaluation d'impact : méthode d'identification, échantillon, résultats.

    L'évaluation d'impact vise à isoler l'effet propre de l'intervention en
    reconstituant le contrefactuel — ce qui serait advenu en son absence. Le
    choix de la méthode dépend du mode d'affectation au traitement et de la
    disponibilité de données avant/après.
    """
    __tablename__ = "impact_studies"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="SET NULL"))
    code = Column(String(30))
    title = Column(String(300), nullable=False)
    research_question = Column(Text)
    hypothesis = Column(Text)
    # --- Devis
    approach = Column(String(40), default="Quasi-expérimentale")  # Expérimentale | Quasi | Non
    method = Column(String(80))                # RCT, DID, PSM, RDD, IV, Contrôle synthétique…
    identification_assumption = Column(Text)   # hypothèse d'identification de la méthode
    assignment_rule = Column(Text)             # règle d'affectation au traitement
    unit_of_analysis = Column(String(120))     # ménage, exploitation, école, village…
    outcome_indicators = Column(JSON, default=list)   # codes d'indicateurs de résultat
    covariates = Column(Text)                  # variables de contrôle
    # --- Échantillon et puissance
    treatment_size = Column(Integer)
    control_size = Column(Integer)
    clusters = Column(Integer)
    intra_cluster_correlation = Column(Float)
    minimum_detectable_effect = Column(Float)
    # Écart-type de l'indicateur de résultat, exprimé dans la même unité que
    # l'effet minimal. Sans lui, aucun calcul de puissance n'a de sens : le
    # contrôle est alors signalé comme indisponible plutôt que calculé sur une
    # valeur implicite.
    outcome_sd = Column(Float)
    power = Column(Float, default=0.8)
    significance_level = Column(Float, default=0.05)
    attrition_rate = Column(Float)
    # --- Calendrier
    baseline_date = Column(Date)
    midline_date = Column(Date)
    endline_date = Column(Date)
    status = Column(String(40), default="Conçue")   # Conçue|Baseline|En cours|Analysée|Publiée
    # --- Résultats
    effect_estimate = Column(Float)            # effet moyen du traitement
    standard_error = Column(Float)
    p_value = Column(Float)
    confidence_interval = Column(String(80))
    effect_unit = Column(String(60))
    robustness_checks = Column(Text)
    threats_to_validity = Column(Text)
    conclusion = Column(Text)
    ethical_clearance = Column(Text)
    data_repository = Column(String(300))

    @property
    def significatif(self):
        if self.p_value is None:
            return None
        return self.p_value <= (self.significance_level or 0.05)

    @property
    def taille_echantillon(self):
        return (self.treatment_size or 0) + (self.control_size or 0)


class Stakeholder(Base, TimestampMixin):
    """Partie prenante du projet, colonne de la matrice RACI."""
    __tablename__ = "stakeholders"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(30))
    name = Column(String(160), nullable=False)      # fonction ou structure
    organisation = Column(String(160))
    category = Column(String(60))                   # Interne | Partenaire | Prestataire | Tutelle…
    contact = Column(String(160))
    order_index = Column(Integer, default=0)


class RaciAssignment(Base, TimestampMixin):
    """Affectation RACI : rôle d'une partie prenante sur une activité.

    R (Responsible) exécute, A (Accountable) rend compte et approuve,
    C (Consulted) est consulté avant décision, I (Informed) est informé après.
    Règle de cohérence : exactement un A par activité, au moins un R.
    """
    __tablename__ = "raci_assignments"
    __table_args__ = (UniqueConstraint("activity_id", "stakeholder_id", name="uq_raci"),)
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    stakeholder_id = Column(Integer, ForeignKey("stakeholders.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(1), nullable=False)        # R | A | C | I
    comment = Column(Text)


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
