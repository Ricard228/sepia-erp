"""Initialisation de la base : compte administrateur et projets de démonstration."""
import logging
from datetime import date, datetime

from sqlalchemy.orm import Session

from .config import ADMIN_EMAIL, ADMIN_NAME, ADMIN_PASSWORD, ADMIN_RESET
from .models import (Activity, Assumption, BudgetLine, Form, FormQuestion, Indicator,
                     IndicatorActual, IndicatorTarget, LogframeElement, Project, ProjectMember,
                     RaciAssignment, Risk, Stakeholder, User, Zone)
from .security import engendrer_mot_de_passe, hash_password
from .seed_sante import projet_sante_education

logger = logging.getLogger("sepia.amorcage")


def _annoncer(titre: str, mot_de_passe: str, consigne: str) -> None:
    """Inscrit une seule fois le mot de passe dans les journaux du serveur."""
    logger.warning(
        "\n%s\n  %s\n  Adresse      : %s\n  Mot de passe : %s\n%s\n%s",
        "=" * 78, titre, ADMIN_EMAIL, mot_de_passe, consigne, "=" * 78)


def reinitialiser_administrateur(db: Session) -> str:
    """Rend la main sur le compte d'administration et retourne son mot de passe.

    Le compte est recréé s'il a disparu, et sinon remis en état de marche :
    nouveau mot de passe, rôle d'administrateur rétabli, compte réactivé,
    verrouillage et tentatives infructueuses effacés, adresse considérée comme
    confirmée, et invalidation de toutes les sessions ouvertes — car si le mot de
    passe a été perdu, on ne peut pas exclure qu'il ait été perdu au profit de
    quelqu'un d'autre.
    """
    mot_de_passe = ADMIN_PASSWORD or engendrer_mot_de_passe()
    maintenant = datetime.utcnow()
    administrateur = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if not administrateur:
        administrateur = User(email=ADMIN_EMAIL, full_name=ADMIN_NAME,
                              organisation="Unité de gestion de projet")
        db.add(administrateur)
    administrateur.password_hash = hash_password(mot_de_passe)
    administrateur.role = "admin"
    administrateur.is_active = True
    administrateur.email_verified = True
    administrateur.verification_token = None
    administrateur.failed_attempts = 0
    administrateur.locked_until = None
    administrateur.password_changed_at = maintenant
    administrateur.must_change_password = True
    administrateur.tokens_valid_from = maintenant
    db.commit()
    db.refresh(administrateur)
    return mot_de_passe


def initialiser(db: Session, avec_demo: bool = True) -> None:
    """Crée le compte d'administration et, au premier démarrage, les projets d'exemple."""
    administrateur = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if not administrateur:
        # Aucun mot de passe n'est inscrit dans le code : celui fourni par
        # l'environnement est utilisé, sinon un mot de passe aléatoire est
        # engendré et affiché une seule fois dans les journaux du serveur.
        mot_de_passe = ADMIN_PASSWORD or engendrer_mot_de_passe()
        administrateur = User(
            email=ADMIN_EMAIL, full_name=ADMIN_NAME,
            password_hash=hash_password(mot_de_passe), role="admin",
            organisation="Unité de gestion de projet",
            email_verified=True, must_change_password=True,
            password_changed_at=datetime.utcnow())
        db.add(administrateur)
        db.commit()
        if not ADMIN_PASSWORD:
            _annoncer("COMPTE ADMINISTRATEUR CRÉÉ", mot_de_passe,
                      "  Ce mot de passe n'est affiché qu'une seule fois et devra être changé à "
                      "la\n  première connexion. Définissez SEPIA_ADMIN_PASSWORD pour en fixer "
                      "un autre.")
    elif ADMIN_RESET:
        # Demandée explicitement par l'exploitant, la réinitialisation s'applique
        # à chaque démarrage tant que la variable est présente : d'où l'avertissement.
        mot_de_passe = reinitialiser_administrateur(db)
        _annoncer("COMPTE ADMINISTRATEUR RÉINITIALISÉ",
                  mot_de_passe if not ADMIN_PASSWORD else "celui de SEPIA_ADMIN_PASSWORD",
                  "  Le changement sera exigé à la connexion et toutes les sessions ouvertes ont\n"
                  "  été fermées. RETIREZ MAINTENANT SEPIA_ADMIN_RESET : tant qu'elle est\n"
                  "  présente, chaque redémarrage réinitialise ce compte.")
        administrateur = db.query(User).filter(User.email == ADMIN_EMAIL).first()

    if avec_demo and not db.query(Project).first():
        _projet_demonstration(db)
        projet_sante_education(db)
        # L'administrateur est rattaché à tous les projets : le contrôle d'accès
        # par projet ne doit pas le priver des jeux de démonstration.
        for projet in db.query(Project).all():
            if not db.query(ProjectMember).filter(
                    ProjectMember.project_id == projet.id,
                    ProjectMember.user_id == administrateur.id).first():
                db.add(ProjectMember(project_id=projet.id, user_id=administrateur.id,
                                     role="responsable"))
        db.commit()


def _projet_demonstration(db: Session) -> None:
    projet = Project(
        code="PADRA-2025",
        title="Projet d'Appui au Développement Rural et à l'Amélioration de la Sécurité "
              "Alimentaire dans les régions septentrionales",
        acronym="PADRA",
        description="Le PADRA vise à accroître durablement les revenus et la sécurité alimentaire "
                    "de 25 000 ménages agricoles vulnérables des régions des Savanes et de la Kara, "
                    "par l'intensification durable de la production, la structuration des chaînes "
                    "de valeur prioritaires (maïs, riz, soja) et le renforcement de la résilience "
                    "climatique des exploitations familiales.",
        sector="Agriculture et développement rural",
        sub_sector="Production végétale et sécurité alimentaire",
        country="Togo",
        regions=["Savanes", "Kara"],
        donor="Fonds International de Développement Agricole (FIDA)",
        executing_agency="Ministère de l'Agriculture, de l'Élevage et du Développement Rural",
        supervising_ministry="Ministère de l'Agriculture, de l'Élevage et du Développement Rural",
        beneficiaries="Ménages agricoles vulnérables, organisations de producteurs, "
                      "jeunes et femmes rurales",
        target_population=25000,
        start_date=date(2025, 1, 1),
        end_date=date(2029, 12, 31),
        status="En cours",
        phase="Mise en œuvre",
        currency="FCFA",
        total_budget=18_500_000_000,
        counterpart_budget=2_200_000_000,
        theory_of_change=(
            "Si les producteurs bénéficient d'un accès accru aux technologies améliorées, aux "
            "intrants de qualité et au conseil agricole de proximité, et si les organisations de "
            "producteurs sont structurées et connectées aux marchés, alors les rendements et les "
            "volumes commercialisés augmenteront, ce qui accroîtra les revenus agricoles et "
            "améliorera durablement la sécurité alimentaire des ménages, à condition que les "
            "conditions climatiques restent dans la normale et que les infrastructures de "
            "désenclavement soient opérationnelles."),
        strategic_alignment={
            "ODD 1": "Éliminer la pauvreté sous toutes ses formes",
            "ODD 2": "Faim zéro — sécurité alimentaire et agriculture durable",
            "ODD 5": "Égalité entre les sexes et autonomisation des femmes rurales",
            "ODD 13": "Mesures relatives à la lutte contre les changements climatiques",
            "Cadre national": "Feuille de route gouvernementale — axe transformation agricole",
        },
        me_approach=(
            "Le dispositif combine un suivi interne continu (exécution physique et financière, "
            "produits) assuré par l'unité de gestion, un suivi externe des effets fondé sur des "
            "enquêtes annuelles auprès d'un panel de ménages, et un dispositif d'évaluation en "
            "trois temps (référence, mi-parcours, finale). La collecte primaire est numérisée "
            "sous KoboToolbox et centralisée dans la plateforme SEPIA."),
    )
    db.add(projet)
    db.flush()

    # --- Zones d'intervention ---------------------------------------------
    definitions_zones = [
        ("SAV", "Région des Savanes", "Région", None, 1_050_000, 15_000, 10.85, 0.20,
         "Coordonnateur régional Nord"),
        ("SAV-TON", "Préfecture de Tône", "Préfecture", "SAV", 350_000, 6_000, 10.87, 0.21,
         "Animateur de zone Tône"),
        ("SAV-KPD", "Préfecture de Kpendjal", "Préfecture", "SAV", 280_000, 5_000, 11.04, 0.42,
         "Animateur de zone Kpendjal"),
        ("SAV-OTI", "Préfecture de l'Oti", "Préfecture", "SAV", 420_000, 4_000, 10.43, 0.36,
         "Animateur de zone Oti"),
        ("KAR", "Région de la Kara", "Région", None, 980_000, 10_000, 9.55, 1.19,
         "Coordonnateur régional Kara"),
        ("KAR-KOZ", "Préfecture de la Kozah", "Préfecture", "KAR", 320_000, 4_500, 9.55, 1.19,
         "Animateur de zone Kozah"),
        ("KAR-BIN", "Préfecture de Binah", "Préfecture", "KAR", 210_000, 3_000, 9.85, 1.32,
         "Animateur de zone Binah"),
        ("KAR-DOU", "Préfecture de Doufelgou", "Préfecture", "KAR", 180_000, 2_500, 9.75, 1.10,
         "Animateur de zone Doufelgou"),
    ]
    objets_zones = {}
    for position, (code, nom, niveau, parent, population, cible, latitude, longitude,
                   responsable) in enumerate(definitions_zones):
        zone = Zone(project_id=projet.id, code=code, name=nom, level=niveau,
                    population=population, beneficiaries_target=cible, latitude=latitude,
                    longitude=longitude, responsible=responsable, order_index=position,
                    parent_id=objets_zones[parent].id if parent else None)
        db.add(zone)
        db.flush()
        objets_zones[code] = zone

    # --- Cadre logique ----------------------------------------------------
    impact = LogframeElement(
        project_id=projet.id, level="IMPACT", code="OG", order_index=0,
        statement="Contribuer à la réduction durable de la pauvreté et de l'insécurité "
                  "alimentaire des ménages ruraux des régions des Savanes et de la Kara",
        means_of_verification="Enquête harmonisée sur les conditions de vie des ménages (EHCVM), "
                              "enquêtes nationales de sécurité alimentaire",
        assumptions="La stabilité politique et macroéconomique du pays est maintenue ; les "
                    "politiques agricoles nationales restent favorables à l'agriculture familiale.",
        responsible="Coordination nationale")
    db.add(impact)
    db.flush()

    effet1 = LogframeElement(
        project_id=projet.id, level="EFFET", code="OS1", parent_id=impact.id, order_index=1,
        statement="La productivité et la production agricole des exploitations familiales "
                  "ciblées sont durablement accrues",
        means_of_verification="Enquête agricole annuelle du projet, mesures de rendement en "
                              "parcelles témoins",
        assumptions="La pluviométrie reste dans la normale saisonnière ; les intrants de qualité "
                    "sont disponibles sur les marchés locaux aux périodes utiles.",
        responsible="Chef de composante Production")
    effet2 = LogframeElement(
        project_id=projet.id, level="EFFET", code="OS2", parent_id=impact.id, order_index=2,
        statement="Les revenus tirés de la commercialisation des produits agricoles par les "
                  "organisations de producteurs sont augmentés",
        means_of_verification="Registres de commercialisation des coopératives, enquête revenus",
        assumptions="Les prix aux producteurs ne connaissent pas d'effondrement ; les pistes "
                    "rurales de desserte restent praticables.",
        responsible="Chef de composante Chaînes de valeur")
    db.add_all([effet1, effet2])
    db.flush()

    produits = [
        ("P1.1", effet1.id, "Les producteurs sont formés et accompagnés dans l'adoption "
                            "d'itinéraires techniques performants et résilients",
         "Rapports de formation, fiches de suivi des champs-écoles", "Les animateurs recrutés "
         "restent en poste sur la durée du projet.", "Responsable Formation"),
        ("P1.2", effet1.id, "L'accès des exploitations aux semences améliorées et aux intrants "
                            "de qualité est facilité",
         "Bordereaux de livraison, registres des boutiques d'intrants", "Les fournisseurs "
         "respectent les délais contractuels de livraison.", "Responsable Intrants"),
        ("P1.3", effet1.id, "Des aménagements hydro-agricoles et des ouvrages de maîtrise de "
                            "l'eau sont réalisés et fonctionnels",
         "Procès-verbaux de réception des travaux, rapports de supervision technique",
         "Les entreprises adjudicataires disposent des capacités techniques requises.",
         "Ingénieur Génie rural"),
        ("P2.1", effet2.id, "Les organisations de producteurs sont structurées, professionnalisées "
                            "et disposent de capacités de gestion renforcées",
         "Statuts et agréments, rapports d'audit organisationnel, plans d'affaires",
         "Les membres des coopératives adhèrent à la démarche de professionnalisation.",
         "Responsable Organisation paysanne"),
        ("P2.2", effet2.id, "Des infrastructures de stockage, de conditionnement et de mise en "
                            "marché sont opérationnelles",
         "Rapports de réception, taux d'utilisation des magasins",
         "Les collectivités mettent à disposition les emprises foncières nécessaires.",
         "Responsable Infrastructures"),
    ]
    elements_produits = {}
    for position, (code, parent, enonce, mov, hypothese, responsable) in enumerate(produits, start=3):
        element = LogframeElement(project_id=projet.id, level="PRODUIT", code=code,
                                  parent_id=parent, statement=enonce, means_of_verification=mov,
                                  assumptions=hypothese, responsible=responsable,
                                  order_index=position)
        db.add(element)
        db.flush()
        elements_produits[code] = element

    activites_cadre = [
        ("A1.1.1", "P1.1", "Mettre en place et animer 250 champs-écoles paysans"),
        ("A1.1.2", "P1.1", "Former 5 000 producteurs relais aux itinéraires techniques améliorés"),
        ("A1.2.1", "P1.2", "Mettre en place un dispositif de multiplication de semences certifiées"),
        ("A1.3.1", "P1.3", "Aménager 800 hectares de bas-fonds rizicoles"),
        ("A2.1.1", "P2.1", "Accompagner 120 coopératives dans leur structuration juridique"),
        ("A2.2.1", "P2.2", "Construire 40 magasins de stockage de 100 tonnes"),
    ]
    for position, (code, parent_code, enonce) in enumerate(activites_cadre, start=10):
        db.add(LogframeElement(project_id=projet.id, level="ACTIVITE", code=code,
                               parent_id=elements_produits[parent_code].id, statement=enonce,
                               order_index=position))
    db.flush()

    # --- Indicateurs ------------------------------------------------------
    definitions = [
        # (code, élément, niveau, libellé, unité, réf, cible, sens, fréquence, source,
        #  méthode, responsable, clé, désagrégation)
        ("IOG1", impact, "IMPACT", "Incidence de la pauvreté monétaire dans la zone d'intervention",
         "%", 58.8, 45.0, "Décroissant", "Annuelle", "EHCVM / enquête panel du projet",
         "Enquête auprès des ménages", "INSEED / Expert S&E", True, ["Sexe", "Milieu"]),
        ("IOG2", impact, "IMPACT", "Prévalence de l'insécurité alimentaire modérée ou sévère "
                                   "chez les ménages bénéficiaires",
         "%", 42.0, 25.0, "Décroissant", "Annuelle", "Enquête FIES annuelle",
         "Échelle FIES (FAO)", "Expert S&E", True, ["Sexe", "Milieu", "Niveau de vulnérabilité"]),
        ("IOG3", impact, "IMPACT", "Score de diversité alimentaire des ménages (HDDS)",
         "Score", 4.2, 6.5, "Croissant", "Annuelle", "Enquête ménages",
         "Questionnaire de rappel 24 heures", "Expert S&E", False, ["Sexe", "Milieu"]),
        ("IOS1.1", effet1, "EFFET", "Rendement moyen du maïs sur les parcelles accompagnées",
         "t/ha", 1.15, 2.50, "Croissant", "Annuelle", "Enquête agricole du projet",
         "Mesure de carrés de rendement", "Agronome S&E", True, ["Sexe"]),
        ("IOS1.2", effet1, "EFFET", "Rendement moyen du riz paddy en bas-fonds aménagés",
         "t/ha", 1.80, 4.00, "Croissant", "Annuelle", "Enquête agricole du projet",
         "Mesure de carrés de rendement", "Agronome S&E", True, ["Sexe"]),
        ("IOS1.3", effet1, "EFFET", "Proportion de producteurs appliquant au moins trois "
                                    "pratiques agricoles intelligentes face au climat",
         "%", 12.0, 60.0, "Croissant", "Annuelle", "Enquête d'adoption",
         "Observation directe et entretien", "Agronome S&E", False, ["Sexe", "Âge"]),
        ("IOS2.1", effet2, "EFFET", "Revenu agricole annuel moyen par exploitation accompagnée",
         "FCFA", 385000, 750000, "Croissant", "Annuelle", "Enquête revenus des ménages",
         "Questionnaire budget-consommation", "Économiste S&E", True, ["Sexe", "Groupe cible"]),
        ("IOS2.2", effet2, "EFFET", "Volume de production commercialisé par les organisations "
                                    "de producteurs appuyées",
         "Tonne", 4200, 22000, "Croissant", "Semestrielle", "Registres des coopératives",
         "Dépouillement des registres", "Responsable chaînes de valeur", True, ["Groupe cible"]),
        ("IP1.1", elements_produits["P1.1"], "PRODUIT", "Nombre de producteurs formés aux "
                                                        "itinéraires techniques améliorés",
         "Nombre", 0, 15000, "Croissant", "Trimestrielle", "Fiches de présence aux formations",
         "Registre de formation", "Responsable Formation", True, ["Sexe", "Âge", "Groupe cible"]),
        ("IP1.2", elements_produits["P1.2"], "PRODUIT", "Quantité de semences certifiées "
                                                        "distribuées aux producteurs",
         "Tonne", 0, 950, "Croissant", "Trimestrielle", "Bordereaux de livraison",
         "Dépouillement documentaire", "Responsable Intrants", False, ["Sexe"]),
        ("IP1.3", elements_produits["P1.3"], "PRODUIT", "Superficie de bas-fonds aménagée et "
                                                        "réceptionnée",
         "Hectare", 0, 800, "Croissant", "Trimestrielle", "PV de réception des travaux",
         "Contrôle technique", "Ingénieur Génie rural", True, []),
        ("IP2.1", elements_produits["P2.1"], "PRODUIT", "Nombre de coopératives disposant d'un "
                                                        "plan d'affaires validé et opérationnel",
         "Nombre", 8, 120, "Croissant", "Semestrielle", "Rapports d'accompagnement",
         "Grille d'évaluation organisationnelle", "Responsable OP", False, ["Sexe"]),
        ("IP2.2", elements_produits["P2.2"], "PRODUIT", "Nombre de magasins de stockage construits "
                                                        "et fonctionnels",
         "Nombre", 0, 40, "Croissant", "Trimestrielle", "PV de réception et rapports de suivi",
         "Visite de terrain", "Responsable Infrastructures", False, []),
        ("IP2.3", elements_produits["P2.2"], "PRODUIT", "Taux de pertes post-récolte au niveau "
                                                        "des exploitations appuyées",
         "%", 28.0, 10.0, "Décroissant", "Annuelle", "Enquête post-récolte",
         "Pesée et estimation en exploitation", "Agronome S&E", False, ["Milieu"]),
    ]
    indicateurs = {}
    for (code, element, niveau, libelle, unite, reference, cible, sens, frequence, source,
         methode, responsable, cle, desagregation) in definitions:
        indicateur = Indicator(
            project_id=projet.id, element_id=element.id, code=code, name=libelle, level=niveau,
            indicator_type="Quantitatif", unit=unite, baseline_value=reference,
            baseline_date=date(2024, 12, 31), baseline_source="Étude de référence 2024",
            target_value=cible, target_date=date(2029, 12, 31), direction=sens,
            frequency=frequence, data_source=source, collection_method=methode,
            responsible=responsable, is_key=cle, disaggregation=desagregation,
            definition=f"Mesure de « {libelle.lower()} » sur le périmètre d'intervention du projet.",
            formula="Voir manuel de suivi-évaluation, section 5.",
            cost_estimate=2_500_000 if niveau in ("IMPACT", "EFFET") else 600_000,
            reporting_level="Comité de pilotage" if cle else "Comité technique")
        db.add(indicateur)
        db.flush()
        indicateurs[code] = indicateur

    # Règle de consolidation : un revenu moyen par exploitation se moyenne, il ne
    # s'additionne pas. Les taux, scores et rendements sont déduits de leur unité.
    indicateurs["IOS2.1"].aggregation = "Moyenne"
    for code in ("IOG1", "IOG2", "IOG3", "IOS1.1", "IOS1.2", "IOS1.3", "IP2.3"):
        indicateurs[code].aggregation = "Moyenne"

    # Trois indicateurs sont volontairement laissés incomplets : ils illustrent le
    # diagnostic de qualité SMART et les actions correctrices qu'il recommande.
    indicateurs["IOG3"].definition = None
    indicateurs["IOG3"].formula = None
    indicateurs["IOG3"].collection_method = None
    indicateurs["IP1.2"].formula = None
    indicateurs["IP1.2"].definition = None
    indicateurs["IP2.3"].target_date = None
    indicateurs["IP2.3"].frequency = None
    db.flush()

    # --- Activités et chronogramme ---------------------------------------
    activites = [
        ("A1.1.1", "P1.1", "Mettre en place et animer 250 champs-écoles paysans",
         "Responsable Formation", date(2025, 1, 15), date(2027, 12, 31), 42, "En cours",
         620_000_000, True, "250 champs-écoles fonctionnels"),
        ("A1.1.2", "P1.1", "Former 15 000 producteurs aux itinéraires techniques améliorés",
         "Responsable Formation", date(2025, 2, 1), date(2028, 6, 30), 35, "En cours",
         890_000_000, False, "Rapports de formation semestriels"),
        ("A1.1.3", "P1.1", "Produire et diffuser des supports de vulgarisation en langues locales",
         "Chargé de communication", date(2025, 3, 1), date(2025, 9, 30), 100, "Achevée",
         85_000_000, False, "5 000 fiches techniques diffusées"),
        ("A1.2.1", "P1.2", "Mettre en place un dispositif de multiplication de semences certifiées",
         "Responsable Intrants", date(2025, 1, 1), date(2026, 12, 31), 55, "En cours",
         1_150_000_000, True, "Réseau de 60 multiplicateurs opérationnel"),
        ("A1.2.2", "P1.2", "Appuyer l'installation de 30 boutiques d'intrants de proximité",
         "Responsable Intrants", date(2025, 4, 1), date(2026, 6, 30), 20, "Retardée",
         420_000_000, False, "30 boutiques agréées"),
        ("A1.3.1", "P1.3", "Réaliser les études techniques d'aménagement des bas-fonds",
         "Ingénieur Génie rural", date(2025, 1, 1), date(2025, 6, 30), 100, "Achevée",
         180_000_000, True, "Dossiers d'appel d'offres validés"),
        ("A1.3.2", "P1.3", "Aménager 800 hectares de bas-fonds rizicoles",
         "Ingénieur Génie rural", date(2025, 7, 1), date(2028, 12, 31), 12, "En cours",
         4_800_000_000, True, "800 ha réceptionnés"),
        ("A2.1.1", "P2.1", "Accompagner 120 coopératives dans leur structuration juridique",
         "Responsable OP", date(2025, 3, 1), date(2027, 12, 31), 28, "En cours",
         540_000_000, False, "120 coopératives agréées"),
        ("A2.1.2", "P2.1", "Former les responsables de coopératives à la gestion et au "
                           "leadership féminin",
         "Responsable OP", date(2028, 1, 1), date(2029, 6, 30), 0, "Planifiée",
         310_000_000, False, "480 responsables formés"),
        ("A2.2.1", "P2.2", "Construire 40 magasins de stockage de 100 tonnes",
         "Responsable Infrastructures", date(2025, 7, 1), date(2028, 6, 30), 15, "En cours",
         2_600_000_000, True, "40 magasins réceptionnés"),
        ("A2.2.2", "P2.2", "Doter les coopératives d'équipements de conditionnement",
         "Responsable Infrastructures", date(2028, 7, 1), date(2029, 12, 31), 0, "Planifiée",
         980_000_000, False, "40 lots d'équipements livrés"),
        ("A3.1.1", None, "Mettre en place le dispositif de suivi-évaluation et former les acteurs",
         "Responsable S&E", date(2025, 1, 1), date(2025, 5, 31), 100, "Achevée",
         120_000_000, True, "Manuel de S&E validé et plateforme opérationnelle"),
        ("A3.1.2", None, "Réaliser l'étude de référence (baseline)",
         "Responsable S&E", date(2025, 6, 1), date(2025, 11, 30), 100, "Achevée",
         210_000_000, True, "Rapport de baseline validé"),
        ("A3.1.3", None, "Conduire les enquêtes annuelles de suivi des effets",
         "Responsable S&E", date(2025, 12, 1), date(2029, 12, 31), 25, "En cours",
         640_000_000, False, "Rapports d'enquête annuels"),
    ]
    # Antécédents (relations fin-début) alimentant le chemin critique et le réseau PERT.
    antecedents = {
        "A1.3.2": "A1.3.1",        # les travaux suivent les études techniques
        "A2.2.1": "A1.3.1",        # les magasins suivent les mêmes études
        "A2.2.2": "A2.2.1",        # l'équipement suit la construction
        "A2.1.2": "A2.1.1",        # la formation suit la structuration juridique
        "A3.1.2": "A3.1.1",        # la baseline suit la mise en place du dispositif
        "A3.1.3": "A3.1.2",        # les enquêtes de suivi suivent la baseline
    }
    objets_activites = {}
    for position, (code, parent_code, libelle, responsable, debut, fin, avancement, statut,
                   cout, jalon, livrable) in enumerate(activites):
        activite = Activity(
            project_id=projet.id, code=code, name=libelle,
            element_id=elements_produits[parent_code].id if parent_code else None,
            responsible=responsable, start_date=debut, end_date=fin, progress=avancement,
            status=statut, planned_cost=cout, actual_cost=round(cout * avancement / 100, 0),
            year=debut.year, milestone=jalon, deliverable=livrable, order_index=position,
            dependencies=antecedents.get(code),
            location="Savanes / Kara", partners="ICAT, ITRA, collectivités territoriales")
        db.add(activite)
        db.flush()
        objets_activites[code] = activite

    _parties_prenantes_et_raci(db, projet, objets_activites)

    # --- Cibles trimestrielles et réalisations ---------------------------
    jalons_produits = {
        "IP1.1": [(f"2025-T{t}", v) for t, v in zip((1, 2, 3, 4), (900, 2100, 3400, 4800))],
        "IP1.2": [(f"2025-T{t}", v) for t, v in zip((1, 2, 3, 4), (40, 110, 180, 260))],
        "IP1.3": [(f"2025-T{t}", v) for t, v in zip((1, 2, 3, 4), (0, 60, 140, 210))],
        "IP2.1": [("2025-S1", 25), ("2025-S2", 48)],
        "IP2.2": [(f"2025-T{t}", v) for t, v in zip((1, 2, 3, 4), (2, 6, 11, 15))],
    }
    realisations = {
        "IP1.1": [("2025-T1", 845), ("2025-T2", 1980), ("2025-T3", 3260)],
        "IP1.2": [("2025-T1", 38), ("2025-T2", 104), ("2025-T3", 166)],
        "IP1.3": [("2025-T1", 0), ("2025-T2", 45), ("2025-T3", 96)],
        "IP2.1": [("2025-S1", 22)],
        "IP2.2": [("2025-T1", 1), ("2025-T2", 4), ("2025-T3", 6)],
    }
    # Jalons annuels 2025 des indicateurs d'effet et d'impact (issus du PTBA)
    jalons_annuels = {"IOG1": 58.0, "IOG2": 40.0, "IOG3": 4.6, "IOS1.1": 1.50, "IOS1.2": 2.20,
                      "IOS1.3": 25.0, "IOS2.1": 450000, "IOS2.2": 8000}
    for code, valeur in jalons_annuels.items():
        db.add(IndicatorTarget(indicator_id=indicateurs[code].id, period_label="2025",
                               year=2025, target_value=valeur))
    for code, jalons in jalons_produits.items():
        for periode, valeur in jalons:
            db.add(IndicatorTarget(indicator_id=indicateurs[code].id, period_label=periode,
                                   year=2025, target_value=valeur))
    mois_fin = {"T1": (3, 31), "T2": (6, 30), "T3": (9, 30), "T4": (12, 31),
                "S1": (6, 30), "S2": (12, 31)}
    # Répartition des réalisations entre les préfectures d'intervention et part
    # de femmes observée : les mesures sont enregistrées zone par zone, ce qui
    # alimente la consolidation géographique et l'analyse d'équité.
    repartition_zones = {"SAV-TON": 0.22, "SAV-KPD": 0.16, "SAV-OTI": 0.14,
                         "KAR-KOZ": 0.20, "KAR-BIN": 0.15, "KAR-DOU": 0.13}
    part_femmes_zone = {"SAV-TON": 0.46, "SAV-KPD": 0.41, "SAV-OTI": 0.38,
                        "KAR-KOZ": 0.52, "KAR-BIN": 0.49, "KAR-DOU": 0.44}
    activite_source = {"IP1.1": "A1.1.2", "IP1.2": "A1.2.1", "IP1.3": "A1.3.2",
                       "IP2.1": "A2.1.1", "IP2.2": "A2.2.1"}
    # Indicateurs portant sur des personnes : ils sont ventilés par sexe, âge et groupe cible.
    indicateurs_personnes = {"IP1.1", "IP2.1"}
    parts_age = {"Moins de 18 ans": 0.03, "18 à 35 ans": 0.47,
                 "36 à 59 ans": 0.40, "60 ans et plus": 0.10}
    parts_groupe = {"Producteur": 0.70, "Jeune": 0.22, "Femme cheffe de ménage": 0.08}

    for code, mesures in realisations.items():
        activite = objets_activites.get(activite_source.get(code))
        for periode, valeur_totale in mesures:
            suffixe = periode.split("-")[1]
            mois, jour = mois_fin[suffixe]
            reste = valeur_totale
            zones_ordonnees = list(repartition_zones.items())
            for position, (code_zone, part) in enumerate(zones_ordonnees):
                derniere = position == len(zones_ordonnees) - 1
                valeur = round(reste if derniere else valeur_totale * part, 2)
                if valeur_totale >= 20:      # effectifs entiers pour les grands nombres
                    valeur = float(int(valeur))
                reste = round(reste - valeur, 2)
                if valeur <= 0:
                    continue
                ventilation = {}
                if code in indicateurs_personnes:
                    femmes = float(int(valeur * part_femmes_zone[code_zone]))
                    ventilation = {
                        "Sexe": {"Femme": femmes, "Homme": valeur - femmes},
                        "Âge": {libelle: float(int(valeur * p))
                                for libelle, p in parts_age.items()},
                        "Groupe cible": {libelle: float(int(valeur * p))
                                         for libelle, p in parts_groupe.items()},
                    }
                db.add(IndicatorActual(
                    indicator_id=indicateurs[code].id, period_label=periode, year=2025,
                    reference_date=date(2025, mois, jour), value=valeur,
                    zone_id=objets_zones[code_zone].id,
                    activity_id=activite.id if activite else None,
                    disaggregated_values=ventilation,
                    source="Fiches de collecte terrain consolidées",
                    collected_by="Assistant S&E", validated_by="Responsable S&E",
                    validation_status="Validé"))
    # Premières mesures d'effet (enquête annuelle 2025)
    for code, valeur in (("IOS1.1", 1.42), ("IOS1.2", 2.05), ("IOS1.3", 21.0),
                         ("IOS2.1", 431000), ("IOS2.2", 5600), ("IOG1", 57.1), ("IOG2", 39.5)):
        db.add(IndicatorActual(indicator_id=indicateurs[code].id, period_label="2025",
                               year=2025, reference_date=date(2025, 12, 31), value=valeur,
                               source="Enquête annuelle 2025", collected_by="Cabinet d'études",
                               validation_status="Validé"))

    # --- Budget / PTBA ----------------------------------------------------
    lignes_budget = [
        ("B1.1.1", "A1.1.1", "Honoraires des animateurs de champs-écoles", "Prestations",
         "Homme/mois", 24, 350_000, 10, "FIDA"),
        ("B1.1.2", "A1.1.1", "Intrants de démonstration des champs-écoles", "Fonctionnement",
         "Kit", 250, 45_000, 1, "FIDA"),
        ("B1.1.3", "A1.1.2", "Organisation des sessions de formation", "Formations",
         "Session", 300, 850_000, 1, "FIDA"),
        ("B1.1.4", "A1.1.3", "Édition des supports de vulgarisation", "Communication",
         "Forfait", 1, 85_000_000, 1, "Contrepartie nationale"),
        ("B1.2.1", "A1.2.1", "Appui aux multiplicateurs de semences", "Investissements",
         "Producteur", 60, 1_200_000, 1, "FIDA"),
        ("B1.2.2", "A1.2.2", "Fonds de démarrage des boutiques d'intrants", "Investissements",
         "Boutique", 30, 8_000_000, 1, "FIDA"),
        ("B1.3.1", "A1.3.1", "Études techniques et dossiers d'appel d'offres", "Prestations",
         "Forfait", 1, 180_000_000, 1, "FIDA"),
        ("B1.3.2", "A1.3.2", "Travaux d'aménagement des bas-fonds", "Investissements",
         "Hectare", 800, 5_500_000, 1, "FIDA"),
        ("B1.3.3", "A1.3.2", "Contrôle et supervision des travaux", "Prestations",
         "Forfait", 1, 400_000_000, 1, "Contrepartie nationale"),
        ("B2.1.1", "A2.1.1", "Accompagnement juridique des coopératives", "Prestations",
         "Coopérative", 120, 3_500_000, 1, "FIDA"),
        ("B2.1.2", "A2.1.2", "Ateliers de formation à la gestion coopérative", "Formations",
         "Atelier", 48, 6_400_000, 1, "FIDA"),
        ("B2.2.1", "A2.2.1", "Construction des magasins de stockage", "Investissements",
         "Magasin", 40, 62_000_000, 1, "FIDA"),
        ("B2.2.2", "A2.2.2", "Acquisition des équipements de conditionnement", "Équipements",
         "Lot", 40, 24_500_000, 1, "FIDA"),
        ("B3.1.1", "A3.1.1", "Développement et hébergement de la plateforme de S&E", "Suivi-évaluation",
         "Forfait", 1, 45_000_000, 1, "FIDA"),
        ("B3.1.2", "A3.1.2", "Étude de référence (cabinet externe)", "Suivi-évaluation",
         "Étude", 1, 210_000_000, 1, "FIDA"),
        ("B3.1.3", "A3.1.3", "Enquêtes annuelles de suivi des effets", "Suivi-évaluation",
         "Enquête", 4, 160_000_000, 1, "FIDA"),
        ("B4.1.1", None, "Salaires de l'unité de gestion du projet", "Personnel",
         "Mois", 60, 18_500_000, 1, "Contrepartie nationale"),
        ("B4.1.2", None, "Fonctionnement et missions de supervision", "Missions et déplacements",
         "Mois", 60, 4_200_000, 1, "FIDA"),
    ]
    for code, code_activite, libelle, categorie, unite, quantite, cout_unitaire, nombre, source \
            in lignes_budget:
        total = quantite * cout_unitaire * nombre
        activite = objets_activites.get(code_activite) if code_activite else None
        db.add(BudgetLine(
            project_id=projet.id, code=code, label=libelle, category=categorie, unit=unite,
            quantity=quantite, unit_cost=cout_unitaire, frequency_count=nombre,
            funding_source=source, year=2025,
            q1=round(total * 0.15, 0), q2=round(total * 0.25, 0),
            q3=round(total * 0.30, 0), q4=round(total * 0.30, 0),
            committed=round(total * 0.42, 0), disbursed=round(total * 0.28, 0),
            activity_id=activite.id if activite else None))

    # --- Risques ----------------------------------------------------------
    risques = [
        ("R1", "Environnemental / Climatique",
         "Sécheresse prolongée ou mauvaise répartition des pluies pendant la campagne agricole",
         "Variabilité et changement climatiques dans la bande soudano-sahélienne",
         "Chute des rendements, non-atteinte des cibles d'effet 1 et démotivation des producteurs",
         4, 5, "Promotion de variétés à cycle court et tolérantes au stress hydrique ; "
               "développement de l'irrigation d'appoint dans les bas-fonds ; diffusion des "
               "bulletins agro-météorologiques décadaires",
         "Réallocation budgétaire vers un appui d'urgence en semences de contre-saison et "
         "activation du fonds de résilience",
         "Coordonnateur national", "Ouvert", 3, 4, date(2026, 3, 31)),
        ("R2", "Financier / Budgétaire",
         "Retard de mobilisation des fonds de contrepartie nationale",
         "Tensions de trésorerie de l'État et procédures budgétaires longues",
         "Blocage des travaux d'aménagement et report du calendrier d'exécution",
         3, 4, "Inscription anticipée des crédits dans la loi de finances ; suivi mensuel "
               "conjoint avec la direction du budget ; échelonnement contractuel des paiements",
         "Recours au préfinancement du bailleur sur les lignes critiques",
         "Responsable administratif et financier", "Ouvert", 2, 3, date(2026, 1, 31)),
        ("R3", "Opérationnel",
         "Défaillance technique ou financière des entreprises adjudicataires des travaux",
         "Capacités limitées du tissu local d'entreprises de génie rural",
         "Malfaçons, retards de livraison et surcoûts sur les 800 hectares à aménager",
         3, 4, "Renforcement des critères de qualification technique ; allotissement des marchés ; "
               "supervision indépendante et retenue de garantie",
         "Résiliation et relance des lots défaillants avec entreprise de substitution",
         "Ingénieur Génie rural", "Ouvert", 2, 3, date(2026, 6, 30)),
        ("R4", "Social / Genre",
         "Faible participation des femmes et des jeunes aux activités et aux instances "
         "de gouvernance des coopératives",
         "Normes sociales limitant l'accès des femmes au foncier et à la parole publique",
         "Non-atteinte des cibles de désagrégation par sexe et affaiblissement de l'impact social",
         3, 3, "Quotas de participation de 40 % de femmes dans les formations ; sessions dédiées "
               "au leadership féminin ; sensibilisation des chefs traditionnels",
         "Mise en place d'activités spécifiquement dédiées aux groupements féminins",
         "Spécialiste genre et inclusion sociale", "Ouvert", 2, 2, date(2026, 3, 31)),
        ("R5", "Sécuritaire",
         "Dégradation de la situation sécuritaire dans la région des Savanes",
         "Pression des groupes armés sur la bande frontalière septentrionale",
         "Suspension des interventions, déplacement de populations et perte de données de suivi",
         3, 5, "Protocole de sécurité et plan de contingence ; suivi hebdomadaire de la situation ; "
               "recours à des relais communautaires pour la collecte",
         "Repli temporaire sur les zones accessibles et collecte à distance par téléphone",
         "Coordonnateur national", "Ouvert", 3, 4, date(2026, 2, 28)),
        ("R6", "Institutionnel / Capacités",
         "Rotation élevée du personnel de suivi-évaluation et des animateurs de terrain",
         "Conditions salariales peu compétitives et durée déterminée des contrats",
         "Perte de mémoire institutionnelle et dégradation de la qualité des données",
         3, 3, "Plan de rétention et primes de performance ; documentation systématique des "
               "procédures dans la plateforme ; formation continue d'une équipe élargie",
         "Recours à une assistance technique externe de transition",
         "Responsable des ressources humaines", "Maîtrisé", 2, 2, date(2026, 5, 31)),
        ("R7", "Technique",
         "Qualité insuffisante des données collectées sur le terrain",
         "Formation insuffisante des enquêteurs et absence de contrôles de cohérence",
         "Décisions de pilotage fondées sur des informations erronées",
         3, 4, "Contraintes de saisie intégrées aux formulaires XLSForm ; double saisie sur 10 % "
               "de l'échantillon ; audit annuel de la qualité des données",
         "Reprise de la collecte sur les zones concernées aux frais du prestataire",
         "Responsable suivi-évaluation", "Maîtrisé", 2, 2, date(2026, 4, 30)),
        ("R8", "Politique / Gouvernance",
         "Changement d'orientation des politiques agricoles nationales",
         "Alternance institutionnelle et révision des priorités sectorielles",
         "Perte d'alignement stratégique et de portage institutionnel du projet",
         2, 4, "Dialogue politique continu avec la tutelle ; ancrage du projet dans les documents "
               "de stratégie sectorielle ; communication régulière sur les résultats",
         "Reformulation du cadre logique lors de la revue à mi-parcours",
         "Coordonnateur national", "Ouvert", 2, 3, date(2026, 12, 31)),
    ]
    for (code, categorie, titre, cause, consequence, probabilite, impact, attenuation,
         contingence, porteur, statut, proba_res, impact_res, revue) in risques:
        db.add(Risk(project_id=projet.id, code=code, category=categorie, title=titre, cause=cause,
                    consequence=consequence, probability=probabilite, impact=impact,
                    mitigation=attenuation, contingency=contingence, owner=porteur, status=statut,
                    residual_probability=proba_res, residual_impact=impact_res, review_date=revue))

    # --- Hypothèses -------------------------------------------------------
    hypotheses = [
        ("H1", "IMPACT", "La stabilité politique et macroéconomique du pays est maintenue sur "
                         "toute la durée du projet", "Élevée", "Vérifiée",
         "Veille institutionnelle et revue documentaire semestrielle", "Coordonnateur"),
        ("H2", "EFFET", "La pluviométrie reste dans la normale saisonnière", "Élevée",
         "Partiellement vérifiée", "Analyse des bulletins agro-météorologiques trimestriels",
         "Agronome S&E"),
        ("H3", "EFFET", "Les prix aux producteurs des filières ciblées ne connaissent pas "
                        "d'effondrement supérieur à 30 %", "Moyenne", "Non vérifiée",
         "Suivi mensuel des mercuriales sur les marchés de référence", "Économiste S&E"),
        ("H4", "PRODUIT", "Les intrants de qualité sont disponibles sur les marchés locaux aux "
                          "périodes utiles de la campagne", "Élevée", "Partiellement vérifiée",
         "Enquête trimestrielle auprès des distributeurs d'intrants", "Responsable Intrants"),
        ("H5", "PRODUIT", "Les collectivités territoriales mettent à disposition les emprises "
                          "foncières nécessaires aux infrastructures", "Moyenne", "Vérifiée",
         "Vérification des conventions de mise à disposition", "Responsable Infrastructures"),
        ("H6", "PRODUIT", "Les pistes rurales de desserte des zones de production restent "
                          "praticables en saison des pluies", "Moyenne", "Non vérifiée",
         "Mission d'observation en saison des pluies", "Ingénieur Génie rural"),
    ]
    for code, niveau, enonce, criticite, statut, methode, responsable in hypotheses:
        db.add(Assumption(project_id=projet.id, code=code, level=niveau, statement=enonce,
                          criticality=criticite, validation_status=statut,
                          verification_method=methode, responsible=responsable,
                          review_date=date(2026, 6, 30)))

    # --- Indicateurs de processus (masqués par défaut) --------------------
    _indicateurs_processus(db, projet, elements_produits)

    # --- Formulaires de collecte -----------------------------------------
    _formulaires_demonstration(db, projet)
    db.commit()


def _parties_prenantes_et_raci(db: Session, projet: Project, activites: dict) -> None:
    """Recense les acteurs du projet et construit la matrice des responsabilités."""
    definitions = [
        ("CP", "Comité de pilotage", "Ministère de tutelle", "Tutelle"),
        ("COORD", "Coordonnateur national", "Unité de gestion du projet", "Interne"),
        ("RSE", "Responsable suivi-évaluation", "Unité de gestion du projet", "Interne"),
        ("RAF", "Responsable administratif et financier", "Unité de gestion du projet", "Interne"),
        ("CCP", "Chef de composante Production", "Unité de gestion du projet", "Interne"),
        ("CCV", "Chef de composante Chaînes de valeur", "Unité de gestion du projet", "Interne"),
        ("GR", "Ingénieur génie rural", "Unité de gestion du projet", "Interne"),
        ("ICAT", "Service de vulgarisation agricole", "ICAT", "Partenaire d'exécution"),
        ("ENT", "Entreprises de travaux", "Secteur privé", "Prestataire"),
        ("OP", "Organisations de producteurs", "Coopératives", "Bénéficiaire"),
        ("PTF", "Bailleur de fonds", "FIDA", "Bailleur"),
    ]
    objets = {}
    for position, (code, nom, organisation, categorie) in enumerate(definitions):
        partie = Stakeholder(project_id=projet.id, code=code, name=nom,
                             organisation=organisation, category=categorie, order_index=position)
        db.add(partie)
        db.flush()
        objets[code] = partie

    # Chaque activité : un approbateur unique (A), un ou plusieurs réalisateurs (R),
    # les consultés (C) et les informés (I).
    affectations = {
        "A1.1.1": {"A": "CCP", "R": ["ICAT"], "C": ["RSE"], "I": ["COORD", "OP"]},
        "A1.1.2": {"A": "CCP", "R": ["ICAT"], "C": ["RSE", "OP"], "I": ["COORD"]},
        "A1.1.3": {"A": "CCP", "R": ["ICAT"], "C": ["RSE"], "I": ["COORD"]},
        "A1.2.1": {"A": "CCP", "R": ["ICAT", "OP"], "C": ["RAF"], "I": ["COORD", "RSE"]},
        "A1.2.2": {"A": "CCP", "R": ["OP"], "C": ["RAF"], "I": ["COORD", "RSE"]},
        "A1.3.1": {"A": "GR", "R": ["ENT"], "C": ["RAF", "COORD"], "I": ["CP"]},
        "A1.3.2": {"A": "GR", "R": ["ENT"], "C": ["RAF", "OP"], "I": ["COORD", "CP", "PTF"]},
        "A2.1.1": {"A": "CCV", "R": ["ICAT"], "C": ["OP"], "I": ["COORD", "RSE"]},
        "A2.1.2": {"A": "CCV", "R": ["ICAT"], "C": ["OP"], "I": ["COORD"]},
        "A2.2.1": {"A": "GR", "R": ["ENT"], "C": ["CCV", "RAF"], "I": ["COORD", "CP"]},
        "A2.2.2": {"A": "CCV", "R": ["ENT"], "C": ["RAF", "OP"], "I": ["COORD"]},
        "A3.1.1": {"A": "COORD", "R": ["RSE"], "C": ["RAF"], "I": ["CP", "PTF"]},
        "A3.1.2": {"A": "COORD", "R": ["RSE"], "C": ["CCP", "CCV"], "I": ["CP", "PTF"]},
        "A3.1.3": {"A": "COORD", "R": ["RSE"], "C": ["CCP", "CCV", "OP"], "I": ["CP", "PTF"]},
    }
    for code_activite, roles in affectations.items():
        activite = activites.get(code_activite)
        if activite is None:
            continue
        couples = [(roles["A"], "A")] + [(c, "R") for c in roles.get("R", [])] + \
                  [(c, "C") for c in roles.get("C", [])] + [(c, "I") for c in roles.get("I", [])]
        deja = set()
        for code_partie, role in couples:
            partie = objets.get(code_partie)
            if partie is None or partie.id in deja:
                continue
            deja.add(partie.id)
            db.add(RaciAssignment(project_id=projet.id, activity_id=activite.id,
                                  stakeholder_id=partie.id, role=role))
    db.flush()


def _indicateurs_processus(db: Session, projet: Project, elements: dict) -> None:
    """Indicateurs d'activité et de processus, masqués tant que l'option n'est pas activée."""
    definitions = [
        ("IPR1", "Taux d'exécution du plan de travail annuel", "%", 0, 100, "Trimestrielle",
         "Rapports d'activité trimestriels", "Suivi du PTBA", "Responsable S&E",
         "Activités achevées / activités programmées × 100", "Moyenne"),
        ("IPR2", "Délai moyen de production des rapports trimestriels", "Jour", 45, 15,
         "Trimestrielle", "Registre de transmission des rapports", "Décompte administratif",
         "Responsable S&E", "Moyenne des écarts entre échéance et date de transmission", "Moyenne"),
        ("IPR3", "Taux de participation aux sessions de formation programmées", "%", 0, 90,
         "Trimestrielle", "Fiches de présence", "Registre de formation", "Responsable Formation",
         "Participants effectifs / participants attendus × 100", "Moyenne"),
        ("IPR4", "Nombre de missions de supervision réalisées", "Nombre", 0, 60, "Trimestrielle",
         "Rapports de mission", "Décompte documentaire", "Coordonnateur",
         "Somme des missions effectuées", "Somme"),
        ("IPR5", "Délai moyen de passation des marchés", "Jour", 120, 75, "Semestrielle",
         "Dossiers de passation", "Décompte administratif", "Responsable administratif et financier",
         "Moyenne des délais entre lancement et attribution", "Moyenne"),
        ("IPR6", "Taux de complétude des données de suivi transmises dans les délais", "%", 0, 95,
         "Trimestrielle", "Plateforme SEPIA", "Contrôle automatique", "Responsable S&E",
         "Fiches transmises dans les délais / fiches attendues × 100", "Moyenne"),
    ]
    element = elements.get("P1.1")
    for code, libelle, unite, reference, cible, frequence, source, methode, responsable, \
            formule, agregation in definitions:
        db.add(Indicator(
            project_id=projet.id, element_id=element.id if element else None,
            code=code, name=libelle, level="ACTIVITE", indicator_class="Processus",
            indicator_type="Quantitatif", unit=unite, baseline_value=reference,
            baseline_date=date(2024, 12, 31), target_value=cible, target_date=date(2029, 12, 31),
            direction="Décroissant" if unite == "Jour" else "Croissant", frequency=frequence,
            data_source=source, collection_method=methode, responsible=responsable,
            formula=formule, aggregation=agregation, is_key=False,
            definition=f"Indicateur de processus : {libelle.lower()}.",
            disaggregation=[], cost_estimate=150_000,
            reporting_level="Comité technique"))
    db.flush()


def _formulaires_demonstration(db: Session, projet: Project) -> None:
    fiche = Form(
        project_id=projet.id, code="F01", name="Fiche de suivi des sessions de formation",
        form_type="Fiche de suivi", target_respondent="Animateur / formateur",
        periodicity="À chaque session", version="1.0",
        description="Fiche renseignée à l'issue de chaque session de formation ; elle alimente "
                    "l'indicateur IP1.1 (nombre de producteurs formés).",
        instructions="Remplir la fiche immédiatement après la session, en présence du président "
                     "du groupement. Vérifier que le nombre de participants correspond bien à la "
                     "liste de présence signée.",
        linked_indicators=["IP1.1"])
    db.add(fiche)
    db.flush()
    questions_fiche = [
        ("A. Identification", "code_session", "Code de la session de formation", "text", [], True,
         None, None, None),
        ("A. Identification", "date_session", "Date de la session", "date", [], True, None, None, None),
        ("A. Identification", "region", "Région", "select_one",
         [{"name": "savanes", "label": "Savanes"}, {"name": "kara", "label": "Kara"}], True,
         None, None, None),
        ("A. Identification", "prefecture", "Préfecture", "text", [], True, None, None, None),
        ("A. Identification", "village", "Village / localité", "text", [], True, None, None, None),
        ("B. Contenu", "theme", "Thème principal de la formation", "select_one",
         [{"name": "1", "label": "Itinéraire technique maïs"},
          {"name": "2", "label": "Itinéraire technique riz"},
          {"name": "3", "label": "Agriculture intelligente face au climat"},
          {"name": "4", "label": "Gestion post-récolte"},
          {"name": "5", "label": "Gestion coopérative"}], True, None, None, None),
        ("B. Contenu", "duree_heures", "Durée effective de la session (en heures)", "decimal", [],
         True, ". > 0 and . <= 12", "La durée doit être comprise entre 0 et 12 heures.", None),
        ("C. Participation", "nb_participants_h", "Nombre de participants hommes", "integer", [],
         True, ". >= 0", "Valeur positive attendue.", "IP1.1"),
        ("C. Participation", "nb_participants_f", "Nombre de participantes femmes", "integer", [],
         True, ". >= 0", "Valeur positive attendue.", "IP1.1"),
        ("C. Participation", "nb_jeunes", "Dont jeunes de moins de 35 ans", "integer", [], False,
         None, None, None),
        ("D. Appréciation", "satisfaction", "Niveau de satisfaction déclaré des participants",
         "select_one", [{"name": "1", "label": "Très satisfaisant"},
                        {"name": "2", "label": "Satisfaisant"},
                        {"name": "3", "label": "Peu satisfaisant"},
                        {"name": "4", "label": "Non satisfaisant"}], True, None, None, None),
        ("D. Appréciation", "difficultes", "Principales difficultés rencontrées", "text", [],
         False, None, None, None),
        ("D. Appréciation", "photo_seance", "Photographie de la séance", "image", [], False,
         None, None, None),
        ("D. Appréciation", "gps", "Coordonnées GPS du lieu de formation", "geopoint", [], False,
         None, None, None),
    ]
    for position, (section, nom, libelle, type_question, choix, obligatoire, contrainte,
                   message, code_indicateur) in enumerate(questions_fiche):
        db.add(FormQuestion(form_id=fiche.id, order_index=position, section=section, name=nom,
                            label=libelle, question_type=type_question, choices=choix,
                            required=obligatoire, constraint=contrainte,
                            constraint_message=message, linked_indicator_code=code_indicateur))

    enquete = Form(
        project_id=projet.id, code="F02", name="Questionnaire ménage — enquête annuelle de suivi",
        form_type="Questionnaire", target_respondent="Chef de ménage bénéficiaire",
        periodicity="Annuelle", version="2.0",
        description="Questionnaire administré au panel de ménages ; il alimente les indicateurs "
                    "d'effet et d'impact (rendements, revenus, sécurité alimentaire).",
        instructions="Se présenter, expliquer l'objet de l'enquête et recueillir le consentement "
                     "éclairé avant toute question. L'entretien dure environ 45 minutes. En cas "
                     "d'absence du chef de ménage, reporter la visite ; ne jamais interroger un "
                     "mineur.",
        linked_indicators=["IOS1.1", "IOS2.1", "IOG2", "IOG3"])
    db.add(enquete)
    db.flush()
    questions_enquete = [
        ("A. Consentement", "consentement", "Le ménage accepte-t-il de participer à l'enquête ?",
         "select_one", [{"name": "1", "label": "Oui"}, {"name": "0", "label": "Non"}], True,
         None, None, None),
        ("B. Caractéristiques du ménage", "sexe_cm", "Sexe du chef de ménage", "select_one",
         [{"name": "1", "label": "Masculin"}, {"name": "2", "label": "Féminin"}], True,
         None, None, None),
        ("B. Caractéristiques du ménage", "age_cm", "Âge du chef de ménage (années révolues)",
         "integer", [], True, ". >= 15 and . <= 110", "Âge attendu entre 15 et 110 ans.", None),
        ("B. Caractéristiques du ménage", "taille_menage", "Nombre de personnes vivant dans le "
                                                           "ménage", "integer", [], True,
         ". >= 1 and . <= 40", "Taille de ménage attendue entre 1 et 40.", None),
        ("B. Caractéristiques du ménage", "niveau_instruction", "Niveau d'instruction du chef "
                                                                "de ménage", "select_one",
         [{"name": "0", "label": "Aucun"}, {"name": "1", "label": "Primaire"},
          {"name": "2", "label": "Secondaire"}, {"name": "3", "label": "Supérieur"}], True,
         None, None, None),
        ("C. Production agricole", "superficie_mais", "Superficie emblavée en maïs (hectares)",
         "decimal", [], True, ". >= 0 and . <= 50", "Superficie attendue entre 0 et 50 ha.", None),
        ("C. Production agricole", "production_mais", "Production de maïs de la dernière campagne "
                                                      "(kg)", "decimal", [], True, ". >= 0",
         "Valeur positive attendue.", None),
        ("C. Production agricole", "rendement_mais", "Rendement calculé (t/ha)", "calculate", [],
         False, None, None, "IOS1.1"),
        ("C. Production agricole", "adoption_pratiques", "Pratiques agricoles améliorées "
                                                         "appliquées la dernière campagne",
         "select_multiple",
         [{"name": "1", "label": "Semences améliorées"},
          {"name": "2", "label": "Fumure organique"},
          {"name": "3", "label": "Semis en ligne"},
          {"name": "4", "label": "Association / rotation des cultures"},
          {"name": "5", "label": "Cordons pierreux / lutte antiérosive"},
          {"name": "6", "label": "Aucune"}], True, None, None, None),
        ("D. Commercialisation et revenus", "quantite_vendue", "Quantité de maïs vendue (kg)",
         "decimal", [], True, ". >= 0", "Valeur positive attendue.", None),
        ("D. Commercialisation et revenus", "prix_moyen", "Prix moyen de vente (FCFA/kg)",
         "decimal", [], False, ". >= 0", "Valeur positive attendue.", None),
        ("D. Commercialisation et revenus", "revenu_agricole", "Revenu agricole total de la "
                                                               "campagne (FCFA)", "decimal", [],
         True, ". >= 0", "Valeur positive attendue.", "IOS2.1"),
        ("E. Sécurité alimentaire (FIES)", "fies_inquietude", "Au cours des 12 derniers mois, "
                                                              "avez-vous été inquiet de ne pas "
                                                              "avoir assez à manger ?",
         "select_one", [{"name": "1", "label": "Oui"}, {"name": "0", "label": "Non"}], True,
         None, None, "IOG2"),
        ("E. Sécurité alimentaire (FIES)", "fies_saute_repas", "Avez-vous dû sauter un repas "
                                                               "faute de moyens ?", "select_one",
         [{"name": "1", "label": "Oui"}, {"name": "0", "label": "Non"}], True, None, None, None),
        ("E. Sécurité alimentaire (FIES)", "nb_groupes_alimentaires", "Nombre de groupes "
                                                                      "alimentaires consommés "
                                                                      "au cours des 24 dernières "
                                                                      "heures", "integer", [],
         True, ". >= 0 and . <= 12", "Valeur attendue entre 0 et 12.", "IOG3"),
        ("F. Appréciation du projet", "appui_recu", "Types d'appui reçus du projet",
         "select_multiple",
         [{"name": "1", "label": "Formation"}, {"name": "2", "label": "Semences"},
          {"name": "3", "label": "Aménagement"}, {"name": "4", "label": "Équipement"},
          {"name": "5", "label": "Accès au marché"}], True, None, None, None),
        ("F. Appréciation du projet", "changement_percu", "Selon vous, quel changement principal "
                                                          "le projet a-t-il apporté à votre "
                                                          "exploitation ?", "text", [], False,
         None, None, None),
    ]
    for position, (section, nom, libelle, type_question, choix, obligatoire, contrainte,
                   message, code_indicateur) in enumerate(questions_enquete):
        question = FormQuestion(form_id=enquete.id, order_index=position, section=section,
                                name=nom, label=libelle, question_type=type_question,
                                choices=choix, required=obligatoire, constraint=contrainte,
                                constraint_message=message, linked_indicator_code=code_indicateur)
        if nom == "rendement_mais":
            question.calculation = "if(${superficie_mais} > 0, ${production_mais} div " \
                                   "(${superficie_mais} * 1000), 0)"
        if nom in ("sexe_cm", "age_cm"):
            question.relevant = "${consentement} = '1'"
        db.add(question)
