"""Second projet de démonstration : toutes les parties de la plateforme renseignées.

Ce jeu de données sert de cas pratique complet. Il illustre notamment ce que le
projet PADRA ne couvre pas : la caractérisation détaillée des bénéficiaires et
des partenaires, l'évaluation selon les six critères du CAD de l'OCDE avec suivi
des recommandations, et deux devis d'évaluation d'impact — l'un expérimental,
l'autre quasi-expérimental.
"""
from datetime import date

from sqlalchemy.orm import Session

from .models import (Activity, Assumption, Beneficiary, BudgetLine, Evaluation,
                     EvaluationRecommendation, Form, FormQuestion, ImpactStudy, Indicator,
                     IndicatorActual, IndicatorTarget, LogframeElement, Partner, Project,
                     RaciAssignment, Risk, Stakeholder, Zone)


def projet_sante_education(db: Session) -> Project:
    projet = Project(
        code="PASSE-2026",
        title="Programme d'Appui à la Santé Scolaire et à l'Éducation des filles dans les "
              "zones rurales défavorisées",
        acronym="PASSE",
        description="Le PASSE vise à améliorer la rétention scolaire et l'état nutritionnel des "
                    "élèves du primaire dans 180 écoles rurales, par un ensemble intégré de "
                    "cantines scolaires, de déparasitage, de bourses conditionnelles pour les "
                    "filles et de renforcement de la gouvernance scolaire. Le programme intègre "
                    "dès sa conception un dispositif d'évaluation d'impact expérimental destiné "
                    "à mesurer l'effet propre des bourses conditionnelles sur la scolarisation "
                    "des filles.",
        sector="Éducation et santé",
        sub_sector="Éducation de base et nutrition scolaire",
        country="Togo",
        regions=["Centrale", "Plateaux"],
        donor="Partenariat mondial pour l'éducation et Banque mondiale",
        executing_agency="Ministère des Enseignements primaire et secondaire",
        supervising_ministry="Ministère des Enseignements primaire et secondaire",
        beneficiaries="Élèves du primaire, filles en âge scolaire déscolarisées, enseignants, "
                      "comités de gestion scolaire, groupements de femmes fournisseurs de "
                      "cantines",
        target_population=54000,
        start_date=date(2026, 1, 1),
        end_date=date(2030, 12, 31),
        status="En cours",
        phase="Mise en œuvre",
        currency="FCFA",
        total_budget=12_400_000_000,
        counterpart_budget=1_860_000_000,
        show_process_indicators=True,
        theory_of_change=(
            "Si les élèves reçoivent un repas quotidien équilibré et un traitement de "
            "déparasitage semestriel, alors leur état nutritionnel et leur assiduité "
            "s'amélioreront. Si, en outre, les familles les plus pauvres reçoivent une bourse "
            "conditionnée à la présence effective des filles, alors le coût d'opportunité de "
            "leur scolarisation diminuera et leur maintien à l'école augmentera. La combinaison "
            "de ces deux leviers, adossée à une gouvernance scolaire renforcée, doit se traduire "
            "par une hausse du taux d'achèvement du primaire et une réduction de l'écart de "
            "réussite entre filles et garçons — à condition que l'offre scolaire reste "
            "disponible et que les prix alimentaires demeurent accessibles."),
        strategic_alignment={
            "ODD 2": "Faim zéro — nutrition scolaire",
            "ODD 3": "Bonne santé et bien-être — santé scolaire et déparasitage",
            "ODD 4": "Éducation de qualité — achèvement du cycle primaire",
            "ODD 5": "Égalité entre les sexes — scolarisation des filles",
            "Plan sectoriel de l'éducation": "Axe 2 — accès équitable et rétention",
        },
        me_approach=(
            "Le dispositif articule trois niveaux. Le suivi de routine, mensuel, s'appuie sur les "
            "registres scolaires numérisés et les fiches de cantine. Le suivi des effets repose "
            "sur une enquête annuelle auprès d'un panel de 3 600 ménages et sur des mesures "
            "anthropométriques semestrielles. L'évaluation d'impact, expérimentale sur le volet "
            "des bourses conditionnelles et quasi-expérimentale sur le volet cantines, permet "
            "d'attribuer causalement les changements observés. Les données sont désagrégées par "
            "sexe, âge, niveau de vulnérabilité et zone."),
    )
    db.add(projet)
    db.flush()

    # --- Zones -----------------------------------------------------------
    zones = {}
    for position, (code, nom, niveau, parent, population, cible, lat, lon, responsable) in enumerate([
        ("CEN", "Région Centrale", "Région", None, 780_000, 28_000, 8.98, 1.14,
         "Directeur régional de l'éducation Centrale"),
        ("CEN-TCH", "Préfecture de Tchaoudjo", "Préfecture", "CEN", 320_000, 12_000, 8.98, 1.14,
         "Inspecteur de Tchaoudjo"),
        ("CEN-SOT", "Préfecture de Sotouboua", "Préfecture", "CEN", 260_000, 9_000, 8.56, 0.98,
         "Inspecteur de Sotouboua"),
        ("CEN-BLI", "Préfecture de Blitta", "Préfecture", "CEN", 200_000, 7_000, 8.32, 0.98,
         "Inspecteur de Blitta"),
        ("PLA", "Région des Plateaux", "Région", None, 1_400_000, 26_000, 7.40, 1.05,
         "Directeur régional de l'éducation Plateaux"),
        ("PLA-OGO", "Préfecture d'Ogou", "Préfecture", "PLA", 380_000, 11_000, 7.53, 1.13,
         "Inspecteur d'Ogou"),
        ("PLA-HAH", "Préfecture de Haho", "Préfecture", "PLA", 290_000, 9_000, 6.94, 1.14,
         "Inspecteur de Haho"),
        ("PLA-WAW", "Préfecture de Wawa", "Préfecture", "PLA", 210_000, 6_000, 7.10, 0.62,
         "Inspecteur de Wawa"),
    ]):
        zone = Zone(project_id=projet.id, code=code, name=nom, level=niveau,
                    population=population, beneficiaries_target=cible, latitude=lat,
                    longitude=lon, responsible=responsable, order_index=position,
                    parent_id=zones[parent].id if parent else None)
        db.add(zone)
        db.flush()
        zones[code] = zone

    # --- Cadre logique ---------------------------------------------------
    impact = LogframeElement(
        project_id=projet.id, level="IMPACT", code="OG", order_index=0,
        statement="Contribuer à l'amélioration du capital humain des enfants des zones rurales "
                  "défavorisées, en particulier des filles",
        means_of_verification="Annuaire statistique de l'éducation, enquête MICS, enquête panel "
                              "du programme",
        assumptions="L'offre scolaire publique reste disponible et gratuite ; aucune crise "
                    "majeure n'interrompt l'année scolaire.",
        responsible="Coordination nationale du programme")
    db.add(impact)
    db.flush()

    effets = {}
    for code, enonce, mov, hypothese, responsable, position in [
        ("OS1", "L'état nutritionnel et sanitaire des élèves du primaire des écoles ciblées "
                "est amélioré",
         "Mesures anthropométriques semestrielles, registres de déparasitage",
         "Les prix des denrées de base restent accessibles aux groupements fournisseurs.",
         "Chef de composante Santé et nutrition scolaire", 1),
        ("OS2", "La rétention et l'achèvement scolaire des filles dans les écoles ciblées "
                "sont accrus",
         "Registres scolaires numérisés, enquête panel de ménages",
         "Les familles maintiennent leur adhésion au dispositif de bourses conditionnelles.",
         "Chef de composante Éducation et genre", 2),
        ("OS3", "La gouvernance des établissements et la redevabilité envers les communautés "
                "sont renforcées",
         "Grilles d'évaluation des comités de gestion, procès-verbaux d'assemblées",
         "Les autorités locales soutiennent la fonctionnalité des comités de gestion.",
         "Chef de composante Gouvernance scolaire", 3),
    ]:
        effet = LogframeElement(project_id=projet.id, level="EFFET", code=code,
                                parent_id=impact.id, statement=enonce, means_of_verification=mov,
                                assumptions=hypothese, responsible=responsable,
                                order_index=position)
        db.add(effet)
        db.flush()
        effets[code] = effet

    produits = {}
    for code, parent, enonce, mov, hypothese, responsable, position in [
        ("P1.1", "OS1", "Des cantines scolaires approvisionnées localement fonctionnent dans "
                        "les écoles ciblées",
         "Fiches de cantine quotidiennes, bordereaux de livraison",
         "Les groupements de femmes fournisseurs honorent les livraisons.",
         "Responsable Cantines", 4),
        ("P1.2", "OS1", "Les élèves bénéficient d'un déparasitage et d'un suivi sanitaire "
                        "semestriels",
         "Registres de campagne, fiches individuelles de santé scolaire",
         "Les intrants médicaux sont disponibles à temps.", "Responsable Santé scolaire", 5),
        ("P2.1", "OS2", "Des bourses conditionnelles sont versées aux familles des filles "
                        "les plus vulnérables",
         "Registre des bénéficiaires, relevés de paiement mobile",
         "Le réseau de paiement mobile couvre les zones ciblées.",
         "Responsable Transferts monétaires", 6),
        ("P2.2", "OS2", "Les enseignants sont formés à la pédagogie sensible au genre et aux "
                        "violences en milieu scolaire",
         "Attestations de formation, grilles d'observation de classe",
         "Les enseignants formés restent affectés dans les écoles ciblées.",
         "Responsable Formation", 7),
        ("P3.1", "OS3", "Les comités de gestion scolaire sont formés, outillés et rendent compte "
                        "publiquement",
         "Plans d'action des comités, procès-verbaux de restitution",
         "Les communautés participent aux assemblées de restitution.",
         "Responsable Gouvernance", 8),
    ]:
        produit = LogframeElement(project_id=projet.id, level="PRODUIT", code=code,
                                  parent_id=effets[parent].id, statement=enonce,
                                  means_of_verification=mov, assumptions=hypothese,
                                  responsible=responsable, order_index=position)
        db.add(produit)
        db.flush()
        produits[code] = produit

    # --- Bénéficiaires ---------------------------------------------------
    beneficiaires = {}
    definitions_beneficiaires = [
        dict(code="B1", name="Élèves du primaire des écoles ciblées", category="Direct",
             typology="Élève", zone="CEN", vulnerability_level="Élevée",
             target_total=54000, target_women=27500, target_youth=54000, target_disabled=1620,
             reached_total=41300, reached_women=21100, reached_youth=41300, reached_disabled=1150,
             households=27000, average_household_size=6.4, baseline_income=310000,
             poverty_rate=62.4,
             selection_criteria="Élèves inscrits dans l'une des 180 écoles retenues, situées "
                                "dans les cantons dont le taux d'achèvement du primaire est "
                                "inférieur à la moyenne régionale.",
             selection_method="Ciblage géographique : sélection des cantons sur la base de "
                              "l'indice de pauvreté scolaire, puis recensement exhaustif des "
                              "élèves inscrits.",
             needs="Repas quotidien, déparasitage, fournitures scolaires, latrines "
                   "fonctionnelles séparées par sexe, point d'eau potable.",
             constraints="Distance domicile-école supérieure à cinq kilomètres pour un tiers des "
                         "élèves ; travaux champêtres en période de récolte ; coût des "
                         "fournitures.",
             expected_benefits="Amélioration de l'état nutritionnel, hausse de l'assiduité, "
                               "réduction du redoublement et de l'abandon.",
             participation_mode="Participation aux clubs scolaires d'hygiène et aux comités "
                                "d'élèves ; consultation lors des évaluations annuelles.",
             grievance_mechanism="Boîte à doléances dans chaque école et numéro vert géré par "
                                 "l'inspection, avec traitement sous quinze jours."),
        dict(code="B2", name="Filles bénéficiaires de bourses conditionnelles", category="Direct",
             typology="Élève", zone="PLA", vulnerability_level="Très élevée",
             target_total=9000, target_women=9000, target_youth=9000, target_disabled=280,
             reached_total=6420, reached_women=6420, reached_youth=6420, reached_disabled=190,
             households=6100, average_household_size=6.9, baseline_income=248000,
             poverty_rate=78.5,
             selection_criteria="Filles inscrites du CE2 au CM2, appartenant à un ménage classé "
                                "dans les deux quintiles les plus pauvres selon un test "
                                "multidimensionnel de moyens, et présentant un risque d'abandon "
                                "identifié par le comité de gestion.",
             selection_method="Ciblage catégoriel par test multidimensionnel de moyens, validé "
                              "en assemblée communautaire pour prévenir les exclusions "
                              "arbitraires.",
             needs="Compensation du coût d'opportunité du travail domestique, fournitures, "
                   "protection contre les violences sur le trajet scolaire, hygiène menstruelle.",
             constraints="Charge de travail domestique, mariages précoces, réticence de certains "
                         "chefs de ménage, absence de pièce d'identité pour le paiement mobile.",
             expected_benefits="Maintien à l'école jusqu'à l'achèvement du primaire et "
                               "transition vers le collège.",
             participation_mode="Les mères sont réceptionnaires des transferts et membres du "
                                "comité de suivi communautaire.",
             grievance_mechanism="Point focal genre dans chaque inspection, saisine confidentielle "
                                 "possible auprès d'une médiatrice communautaire."),
        dict(code="B3", name="Groupements féminins fournisseurs des cantines", category="Direct",
             typology="Micro-entreprise", zone="CEN-TCH", vulnerability_level="Moyenne",
             target_total=360, target_women=342, target_youth=98, target_disabled=12,
             reached_total=284, reached_women=270, reached_youth=76, reached_disabled=9,
             households=284, average_household_size=7.1, baseline_income=420000,
             poverty_rate=48.0,
             selection_criteria="Groupements légalement constitués, implantés à moins de dix "
                                "kilomètres de l'école, comptant au moins 70 % de femmes.",
             selection_method="Appel à manifestation d'intérêt local, sélection par le comité de "
                              "gestion scolaire sous supervision de l'inspection.",
             needs="Fonds de roulement, équipements de cuisine, formation en hygiène "
                   "alimentaire et en gestion.",
             constraints="Trésorerie insuffisante pour préfinancer les approvisionnements ; "
                         "délais de paiement.",
             expected_benefits="Revenu régulier, structuration économique, valorisation de la "
                               "production locale.",
             participation_mode="Signature d'un contrat d'approvisionnement et participation aux "
                                "revues trimestrielles de cantine.",
             grievance_mechanism="Procédure de réclamation contractuelle auprès de l'inspection, "
                                 "avec délai de réponse de dix jours."),
        dict(code="B4", name="Enseignants et directeurs d'école", category="Direct",
             typology="Enseignant", zone="PLA-OGO", vulnerability_level="Faible",
             target_total=1800, target_women=640, target_youth=720, target_disabled=30,
             reached_total=1345, reached_women=498, reached_youth=560, reached_disabled=22,
             households=1345, average_household_size=5.2,
             selection_criteria="Enseignants titulaires et volontaires en poste dans les écoles "
                                "ciblées au premier jour de l'année scolaire.",
             selection_method="Recensement exhaustif à partir des états de service de "
                              "l'inspection.",
             needs="Formation continue, guides pédagogiques, appui à la gestion des classes "
                   "à effectifs multiples.",
             constraints="Rotation annuelle élevée, éloignement des lieux de formation.",
             expected_benefits="Pratiques pédagogiques sensibles au genre, meilleure prise en "
                               "charge des élèves en difficulté.",
             participation_mode="Communautés d'apprentissage entre pairs, une séance mensuelle "
                                "par école.",
             grievance_mechanism="Voie hiérarchique de l'inspection, complétée par un formulaire "
                                 "en ligne anonyme."),
        dict(code="B5", name="Communautés des villages d'implantation", category="Indirect",
             typology="Collectivité territoriale", zone="PLA-HAH", vulnerability_level="Élevée",
             target_total=180, reached_total=180, households=27000, average_household_size=6.4,
             selection_criteria="Villages abritant l'une des 180 écoles ciblées.",
             selection_method="Ciblage géographique dérivé de la sélection des écoles.",
             needs="Transparence sur l'utilisation des fonds scolaires, implication dans les "
                   "décisions de l'école.",
             constraints="Faible alphabétisation des membres de comité, disponibilité limitée "
                         "en période agricole.",
             expected_benefits="Amélioration de la redevabilité et de la qualité du service "
                               "éducatif de proximité.",
             participation_mode="Assemblées de restitution semestrielles ouvertes à tous les "
                                "parents d'élèves.",
             grievance_mechanism="Registre communal de doléances, examiné en session du conseil "
                                 "de la collectivité."),
    ]
    for position, definition in enumerate(definitions_beneficiaires):
        code_zone = definition.pop("zone", None)
        groupe = Beneficiary(project_id=projet.id, order_index=position,
                             zone_id=zones[code_zone].id if code_zone else None, **definition)
        db.add(groupe)
        db.flush()
        beneficiaires[groupe.code] = groupe

    # --- Partenaires -----------------------------------------------------
    for position, definition in enumerate([
        dict(code="PTF1", name="Partenariat mondial pour l'éducation",
             partner_type="Bailleur de fonds", country="International",
             role="Financement principal du programme et participation au comité de pilotage.",
             agreement_reference="GPE-TG-2025-014", agreement_start=date(2025, 11, 1),
             agreement_end=date(2031, 3, 31), financial_commitment=7_900_000_000,
             financial_disbursed=2_370_000_000, currency="FCFA",
             contribution_type="Financière",
             obligations="Décaissement semestriel sur présentation du rapport de performance et "
                         "du rapport financier audité.",
             deliverables="Avis de non-objection sur les PTBA et les marchés au-dessus du seuil.",
             performance_rating=5,
             performance_comment="Décaissements conformes au calendrier ; exigences de "
                                 "rapportage élevées mais anticipées.",
             risks="Suspension des décaissements en cas de réserve majeure de l'audit annuel.",
             contact_name="Chargé de programme éducation", contact_email="programme@ptf.example",
             status="Actif"),
        dict(code="PTF2", name="Banque mondiale — cofinancement", partner_type="Bailleur de fonds",
             country="International",
             role="Cofinancement du volet transferts monétaires et appui à l'évaluation d'impact.",
             agreement_reference="IDA-TG-6842", agreement_start=date(2026, 1, 1),
             agreement_end=date(2030, 12, 31), financial_commitment=2_600_000_000,
             financial_disbursed=624_000_000, currency="FCFA",
             contribution_type="Mixte",
             in_kind_description="Assistance technique de l'unité d'évaluation d'impact, prise "
                                 "en charge directement par le bailleur.",
             obligations="Revue technique semestrielle et validation du protocole d'évaluation "
                         "d'impact avant la collecte de référence.",
             deliverables="Rapport d'analyse de l'évaluation d'impact, jeu de données anonymisé.",
             performance_rating=5,
             performance_comment="Appui méthodologique déterminant pour la qualité du devis "
                                 "expérimental.",
             risks="Exigences méthodologiques susceptibles de retarder le déploiement des "
                   "bourses dans les écoles du groupe témoin.",
             contact_name="Économiste principal", contact_email="impact@bm.example",
             status="Actif"),
        dict(code="MIN1", name="Ministère des Enseignements primaire et secondaire",
             partner_type="Ministère de tutelle", country="Togo",
             role="Maîtrise d'ouvrage, mise à disposition des inspections et des données "
                  "scolaires.",
             agreement_reference="Décret d'ancrage 2025-118", agreement_start=date(2025, 12, 1),
             agreement_end=date(2031, 6, 30), financial_commitment=1_860_000_000,
             financial_disbursed=372_000_000, currency="FCFA",
             contribution_type="Institutionnelle",
             in_kind_description="Locaux des inspections, personnel d'encadrement, accès au "
                                 "système d'information de l'éducation.",
             obligations="Mobilisation de la contrepartie nationale inscrite en loi de finances ; "
                         "affectation stable des enseignants formés.",
             deliverables="Annuaire statistique annuel, arrêtés d'affectation.",
             performance_rating=3,
             performance_comment="Contrepartie nationale mobilisée avec retard sur les deux "
                                 "premiers trimestres.",
             risks="Tension budgétaire de l'État ; rotation des cadres de l'inspection.",
             contact_name="Directeur de la planification", contact_email="dpee@education.example",
             status="Actif"),
        dict(code="ONG1", name="ONG nationale de mise en œuvre — volet cantines",
             partner_type="ONG nationale", country="Togo",
             role="Accompagnement des groupements féminins et supervision des cantines.",
             agreement_reference="CONV-PASSE-2026-003", agreement_start=date(2026, 2, 1),
             agreement_end=date(2029, 12, 31), financial_commitment=980_000_000,
             financial_disbursed=294_000_000, currency="FCFA", contribution_type="Technique",
             obligations="Présence d'un animateur pour vingt écoles ; rapport mensuel de "
                         "supervision.",
             deliverables="Rapports de supervision, plans de renforcement des groupements.",
             performance_rating=4,
             performance_comment="Bonne couverture terrain ; qualité des rapports à homogénéiser.",
             risks="Capacité limitée à absorber une extension géographique rapide.",
             contact_name="Directrice des programmes", contact_email="programmes@ong.example",
             status="Actif"),
        dict(code="REC1", name="Institut national de recherche en santé publique",
             partner_type="Institution de recherche", country="Togo",
             role="Conception et conduite des mesures anthropométriques et du protocole "
                  "d'évaluation d'impact.",
             agreement_reference="PROTO-REC-2026-07", agreement_start=date(2026, 1, 15),
             agreement_end=date(2031, 6, 30), financial_commitment=540_000_000,
             financial_disbursed=189_000_000, currency="FCFA", contribution_type="Technique",
             obligations="Obtention de l'avis du comité d'éthique avant toute collecte ; dépôt "
                         "des données anonymisées.",
             deliverables="Protocole d'évaluation, rapports de mesure, articles scientifiques.",
             performance_rating=5,
             performance_comment="Protocole approuvé sans réserve par le comité national "
                                 "d'éthique.",
             risks="Dépendance à un petit nombre de chercheurs seniors.",
             contact_name="Directeur de recherche", contact_email="recherche@insp.example",
             status="Actif"),
        dict(code="PRI1", name="Opérateur de paiement mobile", partner_type="Secteur privé",
             country="Togo",
             role="Versement des bourses conditionnelles par transfert mobile.",
             agreement_reference="CONV-PAY-2026-01", agreement_start=date(2026, 3, 1),
             agreement_end=date(2030, 12, 31), financial_commitment=0,
             financial_disbursed=0, currency="FCFA", contribution_type="Technique",
             in_kind_description="Réduction des frais de transfert pour les comptes du programme.",
             obligations="Taux de réussite des transferts supérieur à 98 % ; relevé mensuel "
                         "rapproché.",
             deliverables="Relevés de paiement, tableau de bord des transferts échoués.",
             performance_rating=4,
             performance_comment="Taux de réussite de 96,8 %, sous l'objectif contractuel.",
             risks="Couverture réseau insuffisante dans trois cantons de Wawa.",
             contact_name="Responsable des partenariats", contact_email="partenariats@pay.example",
             status="Actif"),
    ]):
        db.add(Partner(project_id=projet.id, order_index=position, **definition))
    db.flush()

    # --- Indicateurs -----------------------------------------------------
    indicateurs = {}
    definitions_indicateurs = [
        # (code, élément, bénéficiaire, niveau, classe, libellé, unité, réf, cible,
        #  sens, fréquence, source, méthode, responsable, clé, désagrégation, agrégation)
        ("IOG1", impact, "B1", "IMPACT", "Résultat",
         "Taux d'achèvement du cycle primaire dans les écoles ciblées", "%", 58.2, 78.0,
         "Croissant", "Annuelle", "Annuaire statistique de l'éducation", "Exploitation des "
         "registres scolaires", "Directeur de la planification", True,
         ["Sexe", "Milieu"], "Moyenne"),
        ("IOG2", impact, "B2", "IMPACT", "Résultat",
         "Écart de taux d'achèvement entre filles et garçons", "%", 14.6, 4.0,
         "Décroissant", "Annuelle", "Annuaire statistique de l'éducation", "Calcul dérivé",
         "Expert S&E", True, ["Milieu"], "Moyenne"),
        ("IOG3", impact, "B1", "IMPACT", "Résultat",
         "Prévalence du retard de croissance chez les élèves de 6 à 11 ans", "%", 27.4, 18.0,
         "Décroissant", "Semestrielle", "Mesures anthropométriques", "Mesure taille et âge",
         "Institut de recherche", True, ["Sexe", "Âge"], "Moyenne"),
        ("IOS1.1", effets["OS1"], "B1", "EFFET", "Résultat",
         "Taux d'assiduité moyen des élèves", "%", 71.5, 90.0, "Croissant", "Trimestrielle",
         "Registres de présence numérisés", "Dépouillement automatisé", "Expert S&E", True,
         ["Sexe", "Âge"], "Moyenne"),
        ("IOS1.2", effets["OS1"], "B1", "EFFET", "Résultat",
         "Proportion d'élèves ayant reçu deux déparasitages dans l'année", "%", 12.0, 95.0,
         "Croissant", "Semestrielle", "Registres de campagne", "Registre nominatif",
         "Responsable Santé scolaire", False, ["Sexe"], "Moyenne"),
        ("IOS2.1", effets["OS2"], "B2", "EFFET", "Résultat",
         "Taux de maintien scolaire des filles boursières", "%", 68.0, 92.0, "Croissant",
         "Annuelle", "Registres scolaires et registre des bourses", "Appariement des registres",
         "Chef de composante Éducation et genre", True, ["Âge", "Niveau de vulnérabilité"],
         "Moyenne"),
        ("IOS2.2", effets["OS2"], "B2", "EFFET", "Résultat",
         "Taux de transition du primaire vers le collège des filles ciblées", "%", 46.3, 70.0,
         "Croissant", "Annuelle", "Enquête panel de ménages", "Questionnaire ménage",
         "Expert S&E", True, ["Niveau de vulnérabilité"], "Moyenne"),
        ("IOS3.1", effets["OS3"], "B5", "EFFET", "Résultat",
         "Proportion de comités de gestion tenant deux restitutions publiques par an", "%",
         18.0, 85.0, "Croissant", "Annuelle", "Procès-verbaux d'assemblée", "Vérification "
         "documentaire", "Responsable Gouvernance", False, [], "Moyenne"),
        ("IP1.1", produits["P1.1"], "B1", "PRODUIT", "Résultat",
         "Nombre d'élèves recevant un repas quotidien à l'école", "Nombre", 0, 54000,
         "Croissant", "Trimestrielle", "Fiches de cantine", "Comptage quotidien",
         "Responsable Cantines", True, ["Sexe", "Âge"], "Somme"),
        ("IP1.2", produits["P1.2"], "B1", "PRODUIT", "Résultat",
         "Nombre d'élèves déparasités", "Nombre", 0, 51300, "Croissant", "Semestrielle",
         "Registres de campagne", "Registre nominatif", "Responsable Santé scolaire", False,
         ["Sexe"], "Somme"),
        ("IP2.1", produits["P2.1"], "B2", "PRODUIT", "Résultat",
         "Nombre de filles recevant effectivement la bourse conditionnelle", "Nombre", 0, 9000,
         "Croissant", "Trimestrielle", "Relevés de paiement mobile", "Rapprochement des "
         "relevés", "Responsable Transferts monétaires", True,
         ["Âge", "Niveau de vulnérabilité"], "Somme"),
        ("IP2.2", produits["P2.2"], "B4", "PRODUIT", "Résultat",
         "Nombre d'enseignants formés à la pédagogie sensible au genre", "Nombre", 0, 1800,
         "Croissant", "Trimestrielle", "Attestations de formation", "Registre de formation",
         "Responsable Formation", False, ["Sexe", "Âge"], "Somme"),
        ("IP3.1", produits["P3.1"], "B5", "PRODUIT", "Résultat",
         "Nombre de comités de gestion scolaire formés et outillés", "Nombre", 12, 180,
         "Croissant", "Semestrielle", "Rapports de formation", "Registre de formation",
         "Responsable Gouvernance", False, [], "Somme"),
        ("IP1.3", produits["P1.1"], "B3", "PRODUIT", "Résultat",
         "Nombre de groupements féminins sous contrat d'approvisionnement", "Nombre", 0, 360,
         "Croissant", "Trimestrielle", "Contrats d'approvisionnement", "Dépouillement "
         "documentaire", "Responsable Cantines", False, [], "Somme"),
        # Indicateurs de processus, affichés car l'option est activée sur ce projet
        ("IPR1", produits["P1.1"], None, "ACTIVITE", "Processus",
         "Taux de jours de classe avec cantine effectivement servie", "%", 0, 95.0, "Croissant",
         "Mensuelle", "Fiches de cantine", "Comptage", "Responsable Cantines", False, [],
         "Moyenne"),
        ("IPR2", produits["P2.1"], None, "ACTIVITE", "Processus",
         "Taux de réussite des transferts monétaires", "%", 0, 98.0, "Croissant", "Trimestrielle",
         "Relevés de l'opérateur", "Rapprochement automatisé",
         "Responsable Transferts monétaires", False, [], "Moyenne"),
        ("IPR3", produits["P3.1"], None, "ACTIVITE", "Processus",
         "Délai moyen de traitement des doléances reçues", "Jour", 30, 15, "Décroissant",
         "Trimestrielle", "Registre des doléances", "Décompte administratif",
         "Responsable Gouvernance", False, [], "Moyenne"),
    ]
    for (code, element, code_beneficiaire, niveau, classe, libelle, unite, reference, cible,
         sens, frequence, source, methode, responsable, cle, desagregation,
         agregation) in definitions_indicateurs:
        indicateur = Indicator(
            project_id=projet.id, element_id=element.id,
            beneficiary_id=beneficiaires[code_beneficiaire].id if code_beneficiaire else None,
            code=code, name=libelle, level=niveau, indicator_class=classe,
            indicator_type="Quantitatif", unit=unite, baseline_value=reference,
            baseline_date=date(2025, 10, 31), baseline_source="Étude de référence 2025",
            target_value=cible, target_date=date(2030, 12, 31), direction=sens,
            frequency=frequence, data_source=source, collection_method=methode,
            responsible=responsable, is_key=cle, disaggregation=desagregation,
            aggregation=agregation,
            definition=f"Mesure de « {libelle.lower()} » sur le périmètre des 180 écoles ciblées.",
            formula="Voir la fiche métadonnée détaillée et le manuel de suivi-évaluation.",
            cost_estimate=1_800_000 if niveau in ("IMPACT", "EFFET") else 450_000,
            reporting_level="Comité de pilotage" if cle else "Comité technique")
        db.add(indicateur)
        db.flush()
        indicateurs[code] = indicateur

    # --- Cibles et réalisations ------------------------------------------
    jalons = {
        "IP1.1": [("2026-T1", 12000), ("2026-T2", 26000), ("2026-T3", 38000), ("2026-T4", 46000)],
        "IP2.1": [("2026-T1", 1800), ("2026-T2", 4200), ("2026-T3", 6300), ("2026-T4", 7600)],
        "IP2.2": [("2026-T1", 320), ("2026-T2", 760), ("2026-T3", 1180), ("2026-T4", 1500)],
        "IP1.3": [("2026-T1", 90), ("2026-T2", 190), ("2026-T3", 268), ("2026-T4", 320)],
        "IP3.1": [("2026-S1", 70), ("2026-S2", 130)],
        "IP1.2": [("2026-S1", 24000), ("2026-S2", 44000)],
    }
    realisations = {
        "IP1.1": [("2026-T1", 11400), ("2026-T2", 25300), ("2026-T3", 41300)],
        "IP2.1": [("2026-T1", 1650), ("2026-T2", 4050), ("2026-T3", 6420)],
        "IP2.2": [("2026-T1", 298), ("2026-T2", 742), ("2026-T3", 1345)],
        "IP1.3": [("2026-T1", 84), ("2026-T2", 186), ("2026-T3", 284)],
        "IP3.1": [("2026-S1", 66)],
        "IP1.2": [("2026-S1", 22800)],
    }
    annuels = {"IOG1": 62.0, "IOG2": 12.8, "IOG3": 25.1, "IOS1.1": 78.0, "IOS1.2": 60.0,
               "IOS2.1": 74.0, "IOS2.2": 51.0, "IOS3.1": 40.0}
    realises_annuels = {"IOG1": 61.4, "IOG2": 12.1, "IOG3": 25.6, "IOS1.1": 79.3,
                        "IOS1.2": 44.5, "IOS2.1": 76.2, "IOS2.2": 52.8, "IOS3.1": 36.7}
    processus = {"IPR1": [("2026-T1", 88.0), ("2026-T2", 92.5), ("2026-T3", 94.1)],
                 "IPR2": [("2026-T1", 94.2), ("2026-T2", 96.1), ("2026-T3", 96.8)],
                 "IPR3": [("2026-T1", 26.0), ("2026-T2", 21.0), ("2026-T3", 17.5)]}
    cibles_processus = {"IPR1": 95.0, "IPR2": 98.0, "IPR3": 18.0}

    for code, valeur in annuels.items():
        db.add(IndicatorTarget(indicator_id=indicateurs[code].id, period_label="2026",
                               year=2026, target_value=valeur))
    for code, liste in jalons.items():
        for periode, valeur in liste:
            db.add(IndicatorTarget(indicator_id=indicateurs[code].id, period_label=periode,
                                   year=2026, target_value=valeur))
    for code, cible in cibles_processus.items():
        for periode in ("2026-T1", "2026-T2", "2026-T3"):
            db.add(IndicatorTarget(indicator_id=indicateurs[code].id, period_label=periode,
                                   year=2026, target_value=cible))

    repartition = {"CEN-TCH": 0.21, "CEN-SOT": 0.16, "CEN-BLI": 0.13,
                   "PLA-OGO": 0.22, "PLA-HAH": 0.17, "PLA-WAW": 0.11}
    part_filles = {"CEN-TCH": 0.51, "CEN-SOT": 0.48, "CEN-BLI": 0.46,
                   "PLA-OGO": 0.53, "PLA-HAH": 0.49, "PLA-WAW": 0.45}
    fin_periode = {"T1": (3, 31), "T2": (6, 30), "T3": (9, 30), "T4": (12, 31),
                   "S1": (6, 30), "S2": (12, 31)}
    ventiles = {"IP1.1", "IP2.1", "IP2.2"}

    for code, mesures in realisations.items():
        for periode, total in mesures:
            mois, jour = fin_periode[periode.split("-")[1]]
            reste = total
            elements_zones = list(repartition.items())
            for position, (code_zone, part) in enumerate(elements_zones):
                derniere = position == len(elements_zones) - 1
                valeur = float(int(reste if derniere else total * part))
                reste = round(reste - valeur, 2)
                if valeur <= 0:
                    continue
                ventilation = {}
                if code in ventiles:
                    filles = float(int(valeur * part_filles[code_zone]))
                    ventilation = {
                        "Sexe": {"Femme": filles, "Homme": valeur - filles},
                        "Âge": {"Moins de 18 ans": valeur},
                    }
                    if code == "IP2.1":
                        ventilation["Niveau de vulnérabilité"] = {
                            "Très vulnérable": float(int(valeur * 0.62)),
                            "Vulnérable": float(int(valeur * 0.38))}
                db.add(IndicatorActual(
                    indicator_id=indicateurs[code].id, period_label=periode, year=2026,
                    reference_date=date(2026, mois, jour), value=valeur,
                    zone_id=zones[code_zone].id, disaggregated_values=ventilation,
                    source="Système de suivi de routine", collected_by="Assistant S&E",
                    validated_by="Responsable S&E", validation_status="Validé"))

    for code, valeur in realises_annuels.items():
        db.add(IndicatorActual(indicator_id=indicateurs[code].id, period_label="2026", year=2026,
                               reference_date=date(2026, 12, 31), value=valeur,
                               source="Enquête panel annuelle 2026",
                               collected_by="Institut de recherche",
                               validated_by="Responsable S&E", validation_status="Validé"))
    for code, mesures in processus.items():
        for periode, valeur in mesures:
            mois, jour = fin_periode[periode.split("-")[1]]
            db.add(IndicatorActual(indicator_id=indicateurs[code].id, period_label=periode,
                                   year=2026, reference_date=date(2026, mois, jour),
                                   value=valeur, source="Suivi de routine",
                                   collected_by="Assistant S&E", validation_status="Validé"))
    db.flush()

    _activites_budget_risques(db, projet, produits, indicateurs)
    _evaluations_et_impact(db, projet)
    _formulaires(db, projet)
    db.commit()
    return projet


def _activites_budget_risques(db: Session, projet: Project, produits, indicateurs) -> None:
    activites = {}
    definitions = [
        ("A0.1", None, "Mettre en place l'unité de gestion et le dispositif de suivi-évaluation",
         "Coordonnateur", date(2026, 1, 1), date(2026, 4, 30), 100, "Achevée", 180_000_000,
         True, "Manuel de S&E validé", None),
        ("A0.2", None, "Réaliser l'étude de référence et le protocole d'évaluation d'impact",
         "Responsable S&E", date(2026, 5, 1), date(2026, 10, 31), 100, "Achevée", 320_000_000,
         True, "Rapport de baseline et protocole approuvés", "A0.1"),
        ("A1.1.1", "P1.1", "Équiper et mettre en service 180 cantines scolaires",
         "Responsable Cantines", date(2026, 11, 1), date(2028, 6, 30), 46, "En cours",
         2_150_000_000, True, "180 cantines fonctionnelles", "A0.2"),
        ("A1.1.2", "P1.1", "Contractualiser et accompagner 360 groupements féminins fournisseurs",
         "Responsable Cantines", date(2026, 11, 1), date(2029, 12, 31), 38, "En cours",
         890_000_000, False, "360 contrats actifs", "A0.2"),
        ("A1.2.1", "P1.2", "Conduire les campagnes semestrielles de déparasitage",
         "Responsable Santé scolaire", date(2026, 11, 1), date(2030, 12, 31), 22, "En cours",
         640_000_000, False, "Dix campagnes conduites", "A0.2"),
        ("A2.1.1", "P2.1", "Recenser et enrôler les familles éligibles aux bourses",
         "Responsable Transferts monétaires", date(2026, 11, 1), date(2027, 6, 30), 72,
         "En cours", 410_000_000, True, "9 000 filles enrôlées", "A0.2"),
        ("A2.1.2", "P2.1", "Verser les bourses conditionnelles trimestrielles",
         "Responsable Transferts monétaires", date(2027, 7, 1), date(2030, 12, 31), 12,
         "En cours", 3_600_000_000, True, "Quatorze cycles de paiement", "A2.1.1"),
        ("A2.2.1", "P2.2", "Former 1 800 enseignants à la pédagogie sensible au genre",
         "Responsable Formation", date(2026, 11, 1), date(2029, 6, 30), 41, "En cours",
         720_000_000, False, "1 800 enseignants formés", "A0.2"),
        ("A3.1.1", "P3.1", "Former et outiller les 180 comités de gestion scolaire",
         "Responsable Gouvernance", date(2027, 1, 1), date(2029, 12, 31), 28, "En cours",
         480_000_000, False, "180 comités opérationnels", "A0.2"),
        ("A3.1.2", "P3.1", "Organiser les assemblées semestrielles de restitution communautaire",
         "Responsable Gouvernance", date(2027, 7, 1), date(2030, 12, 31), 18, "En cours",
         260_000_000, False, "Sept vagues de restitution", "A3.1.1"),
        ("A4.1.1", None, "Conduire les enquêtes annuelles de suivi des effets",
         "Responsable S&E", date(2026, 11, 1), date(2030, 12, 31), 24, "En cours", 780_000_000,
         False, "Cinq rapports d'enquête", "A0.2"),
        ("A4.1.2", None, "Réaliser l'évaluation à mi-parcours",
         "Coordonnateur", date(2028, 7, 1), date(2028, 12, 31), 0, "Planifiée", 190_000_000,
         True, "Rapport de mi-parcours validé", "A4.1.1"),
        ("A4.1.3", None, "Réaliser l'évaluation finale et l'analyse d'impact",
         "Coordonnateur", date(2031, 1, 1), date(2031, 6, 30), 0, "Planifiée", 280_000_000,
         True, "Rapport final et article scientifique", "A4.1.2"),
    ]
    for position, (code, parent, libelle, responsable, debut, fin, avancement, statut, cout,
                   jalon, livrable, antecedent) in enumerate(definitions):
        activite = Activity(
            project_id=projet.id, code=code, name=libelle,
            element_id=produits[parent].id if parent else None,
            responsible=responsable, start_date=debut, end_date=fin, progress=avancement,
            status=statut, planned_cost=cout, actual_cost=round(cout * avancement / 100, 0),
            year=debut.year, milestone=jalon, deliverable=livrable, dependencies=antecedent,
            order_index=position, location="Centrale et Plateaux",
            partners="Inspections, ONG de mise en œuvre, institut de recherche")
        db.add(activite)
        db.flush()
        activites[code] = activite

    lignes_budget = [
        ("B0.1", "A0.1", "Salaires de l'unité de gestion", "Personnel", "Mois", 60, 2_400_000, 1),
        ("B0.2", "A0.2", "Étude de référence et protocole d'évaluation", "Suivi-évaluation",
         "Étude", 1, 320_000_000, 1),
        ("B1.1", "A1.1.1", "Équipement des cantines", "Équipements", "Cantine", 180, 6_800_000, 1),
        ("B1.2", "A1.1.1", "Denrées alimentaires", "Fonctionnement", "Élève/an", 54000, 16_500, 1),
        ("B1.3", "A1.1.2", "Accompagnement des groupements", "Prestations", "Groupement", 360,
         2_470_000, 1),
        ("B1.4", "A1.2.1", "Intrants de déparasitage", "Fonctionnement", "Campagne", 10,
         64_000_000, 1),
        ("B2.1", "A2.1.1", "Recensement et enrôlement", "Prestations", "Forfait", 1, 410_000_000, 1),
        ("B2.2", "A2.1.2", "Bourses conditionnelles", "Transferts", "Fille/an", 9000, 40_000, 10),
        ("B2.3", "A2.2.1", "Sessions de formation des enseignants", "Formations", "Session", 90,
         8_000_000, 1),
        ("B3.1", "A3.1.1", "Formation et outillage des comités", "Formations", "Comité", 180,
         2_670_000, 1),
        ("B3.2", "A3.1.2", "Assemblées de restitution", "Communication", "Assemblée", 1260,
         206_000, 1),
        ("B4.1", "A4.1.1", "Enquêtes annuelles de suivi", "Suivi-évaluation", "Enquête", 5,
         156_000_000, 1),
        ("B4.2", "A4.1.2", "Évaluation à mi-parcours", "Suivi-évaluation", "Étude", 1,
         190_000_000, 1),
        ("B4.3", "A4.1.3", "Évaluation finale et analyse d'impact", "Suivi-évaluation", "Étude",
         1, 280_000_000, 1),
    ]
    for code, code_activite, libelle, categorie, unite, quantite, cout_unitaire, nombre in lignes_budget:
        total = quantite * cout_unitaire * nombre
        db.add(BudgetLine(
            project_id=projet.id, code=code, label=libelle, category=categorie, unit=unite,
            quantity=quantite, unit_cost=cout_unitaire, frequency_count=nombre,
            funding_source="Partenariat mondial pour l'éducation" if categorie != "Transferts"
            else "Banque mondiale", year=2026,
            q1=round(total * 0.18, 0), q2=round(total * 0.24, 0),
            q3=round(total * 0.29, 0), q4=round(total * 0.29, 0),
            committed=round(total * 0.38, 0), disbursed=round(total * 0.24, 0),
            activity_id=activites[code_activite].id if code_activite else None))

    risques = [
        ("R1", "Sanitaire", "Épidémie entraînant la fermeture prolongée des écoles",
         "Circulation d'un agent pathogène en milieu scolaire",
         "Interruption des cantines et du suivi de présence, invalidation des mesures d'effet",
         3, 5, "Protocole d'hygiène renforcé, stock tampon d'intrants, dispositif de continuité "
              "pédagogique à distance",
         "Report de la collecte de données et ajustement du calendrier d'évaluation",
         "Coordonnateur", "Ouvert", 2, 4, date(2027, 6, 30)),
        ("R2", "Financier / Budgétaire", "Retard de mobilisation de la contrepartie nationale",
         "Tensions de trésorerie de l'État",
         "Interruption du versement des bourses et perte de confiance des familles",
         4, 4, "Inscription anticipée en loi de finances, suivi mensuel avec la direction du "
               "budget, fonds de roulement constitué sur la première tranche du bailleur",
         "Préfinancement par le bailleur principal sur autorisation exceptionnelle",
         "Responsable administratif et financier", "Ouvert", 3, 3, date(2027, 3, 31)),
        ("R3", "Technique", "Échec des transferts monétaires par défaut de couverture réseau",
         "Zones blanches dans trois cantons de Wawa",
         "Exclusion de bénéficiaires éligibles et biais dans l'évaluation d'impact",
         3, 4, "Points de paiement itinérants, convention avec un second opérateur, suivi "
               "hebdomadaire du taux d'échec",
         "Paiement en espèces sécurisé sur les zones non couvertes",
         "Responsable Transferts monétaires", "Maîtrisé", 2, 3, date(2027, 1, 31)),
        ("R4", "Social / Genre", "Résistance familiale à la scolarisation prolongée des filles",
         "Normes sociales et mariages précoces",
         "Abandon en cours d'année malgré la bourse, non-atteinte de l'effet 2",
         3, 4, "Dialogue communautaire avec les chefs traditionnels et religieux, médiatrices "
               "communautaires, conditionnalité assortie d'un accompagnement",
         "Renforcement du volet de sensibilisation et allongement de la durée d'appui",
         "Spécialiste genre", "Ouvert", 2, 3, date(2027, 6, 30)),
        ("R5", "Opérationnel", "Défaillance d'approvisionnement des cantines",
         "Trésorerie insuffisante des groupements fournisseurs",
         "Ruptures de service, chute de l'assiduité",
         3, 3, "Avance de démarrage aux groupements, paiement sous quinze jours, stock tampon "
               "de céréales",
         "Recours temporaire à un fournisseur de substitution",
         "Responsable Cantines", "Maîtrisé", 2, 2, date(2027, 3, 31)),
        ("R6", "Institutionnel / Capacités",
         "Rotation des enseignants formés vers d'autres établissements",
         "Mouvement annuel du personnel enseignant",
         "Dilution de l'effet des formations sur les écoles ciblées",
         4, 3, "Convention avec le ministère sur la stabilité des affectations, formation d'un "
               "référent par école, ressources pédagogiques laissées sur place",
         "Sessions de rattrapage pour les enseignants nouvellement affectés",
         "Responsable Formation", "Ouvert", 3, 2, date(2027, 9, 30)),
        ("R7", "Technique", "Contamination entre groupe de traitement et groupe témoin",
         "Proximité géographique des écoles et circulation de l'information",
         "Sous-estimation de l'effet mesuré par l'évaluation d'impact",
         3, 4, "Randomisation par grappes au niveau de l'école, distance minimale entre écoles "
               "de statuts différents, mesure explicite des effets de diffusion",
         "Analyse de sensibilité excluant les paires d'écoles contiguës",
         "Institut de recherche", "Maîtrisé", 2, 3, date(2027, 6, 30)),
    ]
    for (code, categorie, titre, cause, consequence, proba, impact_note, attenuation,
         contingence, porteur, statut, proba_res, impact_res, revue) in risques:
        db.add(Risk(project_id=projet.id, code=code, category=categorie, title=titre,
                    cause=cause, consequence=consequence, probability=proba, impact=impact_note,
                    mitigation=attenuation, contingency=contingence, owner=porteur,
                    status=statut, residual_probability=proba_res, residual_impact=impact_res,
                    review_date=revue))

    for code, niveau, enonce, criticite, statut, methode, responsable in [
        ("H1", "IMPACT", "L'offre scolaire publique reste disponible et gratuite dans les zones "
                         "ciblées", "Élevée", "Vérifiée",
         "Revue annuelle de la carte scolaire", "Directeur de la planification"),
        ("H2", "EFFET", "Les prix des denrées de base restent accessibles aux groupements "
                        "fournisseurs", "Élevée", "Partiellement vérifiée",
         "Suivi mensuel des mercuriales sur les marchés de référence", "Responsable Cantines"),
        ("H3", "EFFET", "Les familles maintiennent leur adhésion au dispositif de bourses "
                        "conditionnelles", "Élevée", "Partiellement vérifiée",
         "Enquête de satisfaction semestrielle auprès des ménages bénéficiaires",
         "Spécialiste genre"),
        ("H4", "PRODUIT", "Le réseau de paiement mobile couvre les zones ciblées", "Moyenne",
         "Invalidée", "Cartographie de couverture réseau et taux d'échec des transferts",
         "Responsable Transferts monétaires"),
        ("H5", "PRODUIT", "Les enseignants formés restent affectés dans les écoles ciblées",
         "Élevée", "Non vérifiée", "Rapprochement annuel des états d'affectation",
         "Responsable Formation"),
        ("H6", "PRODUIT", "Les intrants médicaux de déparasitage sont disponibles à temps",
         "Moyenne", "Vérifiée", "Suivi du calendrier d'approvisionnement de la centrale d'achat",
         "Responsable Santé scolaire"),
    ]:
        db.add(Assumption(project_id=projet.id, code=code, level=niveau, statement=enonce,
                          criticality=criticite, validation_status=statut,
                          verification_method=methode, responsible=responsable,
                          review_date=date(2027, 6, 30)))

    # --- Parties prenantes et matrice RACI --------------------------------
    parties = {}
    for position, (code, nom, organisation, categorie) in enumerate([
        ("CP", "Comité de pilotage", "Ministère des Enseignements primaire et secondaire",
         "Tutelle"),
        ("COORD", "Coordonnateur national", "Unité de gestion du programme", "Interne"),
        ("RSE", "Responsable suivi-évaluation", "Unité de gestion du programme", "Interne"),
        ("RAF", "Responsable administratif et financier", "Unité de gestion du programme",
         "Interne"),
        ("CANT", "Responsable Cantines", "Unité de gestion du programme", "Interne"),
        ("TRANS", "Responsable Transferts monétaires", "Unité de gestion du programme", "Interne"),
        ("GENRE", "Spécialiste genre et inclusion", "Unité de gestion du programme", "Interne"),
        ("INSP", "Inspections de l'enseignement primaire", "Ministère", "Partenaire d'exécution"),
        ("ONG", "ONG de mise en œuvre", "Société civile", "Partenaire d'exécution"),
        ("REC", "Institut de recherche", "Institut national de santé publique",
         "Partenaire d'exécution"),
        ("PAY", "Opérateur de paiement mobile", "Secteur privé", "Prestataire"),
        ("CGS", "Comités de gestion scolaire", "Communautés", "Bénéficiaire"),
        ("PTF", "Bailleurs de fonds", "PME et Banque mondiale", "Bailleur"),
    ]):
        partie = Stakeholder(project_id=projet.id, code=code, name=nom,
                             organisation=organisation, category=categorie, order_index=position)
        db.add(partie)
        db.flush()
        parties[code] = partie

    affectations = {
        "A0.1": {"A": "COORD", "R": ["RSE"], "C": ["RAF"], "I": ["CP", "PTF"]},
        "A0.2": {"A": "COORD", "R": ["RSE", "REC"], "C": ["PTF"], "I": ["CP", "INSP"]},
        "A1.1.1": {"A": "CANT", "R": ["ONG"], "C": ["INSP", "RAF"], "I": ["COORD", "CGS"]},
        "A1.1.2": {"A": "CANT", "R": ["ONG"], "C": ["CGS"], "I": ["COORD", "RSE"]},
        "A1.2.1": {"A": "COORD", "R": ["REC", "INSP"], "C": ["RAF"], "I": ["CP", "CGS"]},
        "A2.1.1": {"A": "TRANS", "R": ["INSP", "CGS"], "C": ["GENRE", "RSE"], "I": ["COORD"]},
        "A2.1.2": {"A": "TRANS", "R": ["PAY"], "C": ["RAF", "GENRE"], "I": ["COORD", "CP", "PTF"]},
        "A2.2.1": {"A": "GENRE", "R": ["INSP"], "C": ["RSE"], "I": ["COORD"]},
        "A3.1.1": {"A": "COORD", "R": ["ONG", "INSP"], "C": ["CGS"], "I": ["RSE"]},
        "A3.1.2": {"A": "COORD", "R": ["CGS"], "C": ["INSP", "GENRE"], "I": ["RSE", "CP"]},
        "A4.1.1": {"A": "COORD", "R": ["RSE", "REC"], "C": ["GENRE"], "I": ["CP", "PTF"]},
        "A4.1.2": {"A": "CP", "R": ["RSE"], "C": ["COORD", "PTF"], "I": ["INSP", "ONG"]},
        "A4.1.3": {"A": "CP", "R": ["REC"], "C": ["RSE", "COORD", "PTF"], "I": ["INSP", "CGS"]},
    }
    for code_activite, roles in affectations.items():
        activite = activites.get(code_activite)
        if activite is None:
            continue
        couples = [(roles["A"], "A")] + [(c, "R") for c in roles.get("R", [])] + \
                  [(c, "C") for c in roles.get("C", [])] + [(c, "I") for c in roles.get("I", [])]
        deja = set()
        for code_partie, role in couples:
            partie = parties.get(code_partie)
            if partie is None or partie.id in deja:
                continue
            deja.add(partie.id)
            db.add(RaciAssignment(project_id=projet.id, activity_id=activite.id,
                                  stakeholder_id=partie.id, role=role))
    db.flush()


def _evaluations_et_impact(db: Session, projet: Project) -> None:
    """Évaluations selon les critères du CAD et devis d'évaluation d'impact."""
    baseline = Evaluation(
        project_id=projet.id, code="EV1", title="Étude de référence du programme PASSE",
        evaluation_type="Référence", period_covered="Situation à octobre 2025",
        start_date=date(2026, 5, 1), end_date=date(2026, 10, 31), status="Validée",
        evaluator="Institut national de recherche en santé publique",
        independence="Externe indépendante", budget=320_000_000,
        methodology="Enquête transversale auprès de 3 600 ménages tirés au sort dans les 180 "
                    "écoles ciblées et dans 60 écoles témoins, complétée par des mesures "
                    "anthropométriques sur 5 400 élèves et par 24 entretiens de groupe.",
        data_sources="Questionnaire ménage, registres scolaires, mesures anthropométriques, "
                     "entretiens de groupe avec les parents et les enseignants.",
        sampling="Échantillonnage aléatoire stratifié à deux degrés : tirage des écoles avec "
                 "probabilité proportionnelle à la taille, puis tirage systématique des élèves. "
                 "Marge d'erreur de 2,5 points au seuil de 95 %.",
        limitations="Les données de présence antérieures à 2025 sont incomplètes dans un tiers "
                    "des écoles, ce qui limite l'analyse rétrospective des tendances.",
        scores={"pertinence": 6, "coherence": 5},
        justifications={
            "pertinence": "Le diagnostic confirme que le coût d'opportunité du travail "
                          "domestique et la faim en classe sont les deux premiers déterminants "
                          "de l'abandon scolaire des filles dans les zones ciblées : les leviers "
                          "retenus par le programme y répondent directement.",
            "coherence": "Le programme s'articule avec le plan sectoriel de l'éducation et ne "
                         "double aucune intervention en cours ; une coordination reste à "
                         "formaliser avec le programme national de nutrition."},
        key_findings="Le taux d'achèvement du primaire s'établit à 58,2 % dans les écoles "
                     "ciblées, contre 71,4 % au niveau national. L'écart filles-garçons atteint "
                     "14,6 points. La prévalence du retard de croissance touche 27,4 % des "
                     "élèves.",
        lessons_learned="La qualité des registres scolaires conditionne l'ensemble du dispositif "
                        "de suivi : leur numérisation doit précéder toute autre activité.",
        overall_comment="L'étude confirme la pertinence du ciblage et fournit une base de "
                        "comparaison solide pour l'évaluation d'impact.",
        report_reference="PASSE-BASELINE-2026-V2")
    db.add(baseline)

    mi_parcours = Evaluation(
        project_id=projet.id, code="EV2", title="Évaluation à mi-parcours du programme PASSE",
        evaluation_type="Mi-parcours", period_covered="Janvier 2026 – juin 2028",
        start_date=date(2028, 7, 1), end_date=date(2028, 12, 31), status="Planifiée",
        evaluator="Cabinet indépendant à recruter", independence="Externe indépendante",
        budget=190_000_000,
        methodology="Approche mixte : analyse des données de suivi et de l'enquête panel, "
                    "enquête de satisfaction, études de cas dans douze écoles, entretiens avec "
                    "les parties prenantes.",
        data_sources="Base de suivi de la plateforme, enquête panel, registres scolaires, "
                     "entretiens semi-directifs.",
        sampling="Douze écoles retenues de façon raisonnée pour couvrir les deux régions et les "
                 "trois niveaux de performance observés.",
        limitations="L'évaluation intervient avant que les effets sur l'achèvement du cycle ne "
                    "puissent être observés : elle portera principalement sur l'efficacité "
                    "opérationnelle et l'efficience.",
        scores={}, justifications={},
        report_reference="À produire")
    db.add(mi_parcours)
    db.flush()

    for code, critere, enonce, priorite, responsable, echeance, reponse, statut, taux in [
        ("R1", "coherence", "Formaliser un protocole de coordination avec le programme national "
                            "de nutrition afin d'éviter les doublons de couverture sur les "
                            "cantines.", "Élevée", "Coordonnateur", date(2027, 3, 31),
         "Acceptée", "En cours", 60.0),
        ("R2", "pertinence", "Étendre le test multidimensionnel de moyens aux ménages "
                             "nouvellement installés, aujourd'hui exclus du recensement initial.",
         "Moyenne", "Responsable Transferts monétaires", date(2027, 6, 30), "Acceptée",
         "Non démarrée", 0.0),
        ("R3", "pertinence", "Numériser les registres scolaires des soixante écoles où ils sont "
                             "incomplets avant la prochaine campagne de collecte.", "Élevée",
         "Responsable suivi-évaluation", date(2026, 12, 31), "Acceptée", "Achevée", 100.0),
        ("R4", "coherence", "Aligner le calendrier des campagnes de déparasitage sur celui du "
                            "ministère de la Santé.", "Faible", "Responsable Santé scolaire",
         date(2027, 9, 30), "Partiellement acceptée", "En cours", 35.0),
    ]:
        db.add(EvaluationRecommendation(
            evaluation_id=baseline.id, code=code, criterion=critere, statement=enonce,
            priority=priorite, responsible=responsable, deadline=echeance,
            management_response=reponse, implementation_status=statut, implementation_rate=taux,
            response_comment="Réponse de la coordination consignée au procès-verbal du comité "
                             "technique du 15 janvier 2027.",
            evidence="Protocole signé et versé au dossier" if taux >= 100 else None))

    # --- Devis d'évaluation d'impact -------------------------------------
    db.add(ImpactStudy(
        project_id=projet.id, evaluation_id=baseline.id, code="EI1",
        title="Effet des bourses conditionnelles sur le maintien scolaire des filles",
        research_question="Le versement d'une bourse trimestrielle conditionnée à la présence "
                          "effective augmente-t-il le taux de maintien scolaire des filles des "
                          "ménages les plus pauvres, et de combien ?",
        hypothesis="La bourse compense le coût d'opportunité du travail domestique et accroît le "
                   "taux de maintien d'au moins 8 points de pourcentage à l'issue de deux années "
                   "scolaires.",
        approach="Expérimentale", method="Randomisation par grappes",
        identification_assumption="L'assignation aléatoire des écoles au traitement rend les "
                                  "deux groupes comparables en espérance sur l'ensemble des "
                                  "caractéristiques, observées comme non observées. L'unité "
                                  "d'assignation est l'école, ce qui limite la contamination "
                                  "entre élèves d'un même établissement.",
        assignment_rule="Les 240 écoles éligibles ont été appariées par strates (région, taille, "
                        "taux d'achèvement initial) puis, au sein de chaque paire, une école a "
                        "été tirée au sort pour le traitement. Le tirage a été effectué "
                        "publiquement en présence des inspections et consigné par procès-verbal.",
        unit_of_analysis="Élève fille inscrite du CE2 au CM2",
        outcome_indicators=["IOS2.1", "IOS2.2", "IOG2"],
        covariates="Âge de l'élève, niveau scolaire, taille du ménage, niveau d'instruction de "
                   "la mère, distance domicile-école, indice de richesse, statut matrimonial des "
                   "parents.",
        treatment_size=4500, control_size=4500, clusters=240,
        intra_cluster_correlation=0.08, minimum_detectable_effect=0.08, outcome_sd=0.46,
        power=0.8,
        significance_level=0.05, attrition_rate=0.12,
        baseline_date=date(2026, 10, 31), midline_date=date(2028, 6, 30),
        endline_date=date(2030, 6, 30), status="Baseline réalisée",
        robustness_checks="Estimation en intention de traiter et en traitement effectif ; "
                          "correction des erreurs types par grappe ; test d'équilibre des "
                          "covariables à la baseline ; analyse de sensibilité à l'attrition "
                          "différentielle par bornes de Lee.",
        threats_to_validity="Contamination par diffusion de l'information entre écoles voisines ; "
                            "attrition différentielle si les familles non bénéficiaires migrent ; "
                            "effet Hawthorne lié à la présence répétée des enquêteurs.",
        ethical_clearance="Avis favorable du comité national d'éthique pour la recherche en "
                          "santé, référence CNE-2026-041. Consentement éclairé écrit des tuteurs "
                          "et assentiment oral des élèves. Les écoles témoins bénéficieront du "
                          "dispositif à l'issue de l'évaluation.",
        data_repository="Dépôt national de données de recherche, accès sur demande motivée",
        effect_unit="points de pourcentage"))

    db.add(ImpactStudy(
        project_id=projet.id, evaluation_id=baseline.id, code="EI2",
        title="Effet des cantines scolaires sur l'assiduité et l'état nutritionnel",
        research_question="La mise en service d'une cantine scolaire améliore-t-elle l'assiduité "
                          "et réduit-elle la prévalence du retard de croissance chez les élèves ?",
        hypothesis="La cantine accroît l'assiduité d'au moins 6 points et réduit la prévalence "
                   "du retard de croissance d'au moins 3 points après deux années.",
        approach="Quasi-expérimentale", method="Doubles différences appariées (DID + PSM)",
        identification_assumption="En l'absence du programme, l'assiduité et l'état nutritionnel "
                                  "des écoles traitées et des écoles de comparaison appariées "
                                  "auraient suivi des trajectoires parallèles. L'appariement sur "
                                  "score de propension réduit les écarts initiaux observables, "
                                  "les doubles différences neutralisant ensuite les différences "
                                  "invariantes dans le temps.",
        assignment_rule="Le déploiement des cantines s'est fait par vagues, selon l'ordre "
                        "d'équipement des écoles ; les écoles de la seconde vague servent de "
                        "groupe de comparaison pour la première.",
        unit_of_analysis="École, avec mesures répétées au niveau de l'élève",
        outcome_indicators=["IOS1.1", "IOG3"],
        covariates="Effectif de l'école, ratio élèves-enseignant, distance au chef-lieu, indice "
                   "de pauvreté du canton, présence d'un point d'eau, taux d'achèvement initial.",
        treatment_size=2700, control_size=2700, clusters=120,
        intra_cluster_correlation=0.11, minimum_detectable_effect=0.06, outcome_sd=0.45,
        power=0.8,
        significance_level=0.05, attrition_rate=0.15,
        baseline_date=date(2026, 10, 31), midline_date=date(2028, 6, 30),
        endline_date=date(2030, 6, 30), status="Collecte en cours",
        effect_estimate=5.8, standard_error=2.1, p_value=0.006,
        confidence_interval="[1,7 ; 9,9]", effect_unit="points de pourcentage d'assiduité",
        robustness_checks="Test de tendances parallèles sur les trois trimestres précédant le "
                          "déploiement ; vérification du support commun et de l'équilibre des "
                          "covariables après appariement ; estimation alternative par pondération "
                          "sur l'inverse de la probabilité de traitement.",
        threats_to_validity="L'ordre de déploiement n'est pas aléatoire : si les écoles les plus "
                            "faciles d'accès ont été équipées en premier, l'effet serait "
                            "surestimé. Le test de tendances parallèles et l'appariement "
                            "atténuent ce risque sans l'éliminer.",
        conclusion="Résultat intermédiaire : l'assiduité augmente de 5,8 points de pourcentage "
                   "dans les écoles équipées, effet statistiquement significatif au seuil de 1 %. "
                   "L'effet sur le retard de croissance sera mesurable à la collecte finale.",
        ethical_clearance="Avis favorable du comité national d'éthique, référence CNE-2026-042.",
        data_repository="Dépôt national de données de recherche"))
    db.flush()


def _formulaires(db: Session, projet: Project) -> None:
    formulaire = Form(
        project_id=projet.id, code="F01",
        name="Fiche mensuelle de suivi de cantine scolaire", form_type="Fiche de suivi",
        target_respondent="Directeur d'école et président du comité de gestion",
        periodicity="Mensuelle", version="1.0",
        description="Fiche renseignée en fin de mois dans chaque école : elle alimente les "
                    "indicateurs IP1.1 et IPR1.",
        instructions="Renseigner la fiche le dernier jour ouvré du mois, en présence du "
                     "président du comité de gestion. Le nombre de jours servis doit être "
                     "rapproché du registre de cantine avant transmission.",
        linked_indicators=["IP1.1", "IPR1"])
    db.add(formulaire)
    db.flush()
    questions = [
        ("A. Identification", "code_ecole", "Code de l'école", "text", [], True, None, None, None),
        ("A. Identification", "mois", "Mois de référence", "date", [], True, None, None, None),
        ("A. Identification", "region", "Région", "select_one",
         [{"name": "cen", "label": "Centrale"}, {"name": "pla", "label": "Plateaux"}],
         True, None, None, None),
        ("B. Service", "jours_ouvrables", "Nombre de jours de classe dans le mois", "integer",
         [], True, ". > 0 and . <= 23", "Valeur attendue entre 1 et 23.", None),
        ("B. Service", "jours_servis", "Nombre de jours où la cantine a été servie", "integer",
         [], True, ". >= 0 and . <= ${jours_ouvrables}",
         "Le nombre de jours servis ne peut dépasser le nombre de jours de classe.", "IPR1"),
        ("C. Fréquentation", "eleves_filles", "Nombre de filles ayant pris le repas (moyenne "
                                              "journalière)", "integer", [], True, ". >= 0",
         "Valeur positive attendue.", "IP1.1"),
        ("C. Fréquentation", "eleves_garcons", "Nombre de garçons ayant pris le repas (moyenne "
                                               "journalière)", "integer", [], True, ". >= 0",
         "Valeur positive attendue.", "IP1.1"),
        ("D. Approvisionnement", "groupement", "Groupement fournisseur", "text", [], True,
         None, None, None),
        ("D. Approvisionnement", "ruptures", "Nombre de jours de rupture d'approvisionnement",
         "integer", [], True, ". >= 0", "Valeur positive attendue.", None),
        ("D. Approvisionnement", "cause_rupture", "Cause principale des ruptures", "select_one",
         [{"name": "1", "label": "Retard de paiement"},
          {"name": "2", "label": "Indisponibilité des denrées"},
          {"name": "3", "label": "Problème de transport"},
          {"name": "4", "label": "Aucune rupture"}], False, None, None, None),
        ("E. Observation", "hygiene", "État d'hygiène du lieu de préparation", "select_one",
         [{"name": "1", "label": "Satisfaisant"}, {"name": "2", "label": "Acceptable"},
          {"name": "3", "label": "Insuffisant"}], True, None, None, None),
        ("E. Observation", "photo", "Photographie du lieu de préparation", "image", [], False,
         None, None, None),
        ("E. Observation", "gps", "Coordonnées GPS de l'école", "geopoint", [], False,
         None, None, None),
        ("E. Observation", "observations", "Observations du directeur", "text", [], False,
         None, None, None),
    ]
    for position, (section, nom, libelle, type_question, choix, obligatoire, contrainte,
                   message, code_indicateur) in enumerate(questions):
        db.add(FormQuestion(form_id=formulaire.id, order_index=position, section=section,
                            name=nom, label=libelle, question_type=type_question, choices=choix,
                            required=obligatoire, constraint=contrainte,
                            constraint_message=message, linked_indicator_code=code_indicateur))

    enquete = Form(
        project_id=projet.id, code="F02",
        name="Questionnaire ménage — enquête panel annuelle", form_type="Questionnaire",
        target_respondent="Chef de ménage ou tuteur de l'élève", periodicity="Annuelle",
        version="1.0",
        description="Questionnaire administré au panel de 3 600 ménages ; il alimente les "
                    "indicateurs d'effet et sert de support à l'évaluation d'impact.",
        instructions="Recueillir le consentement éclairé écrit du tuteur avant toute question. "
                     "Ne jamais interroger un mineur sans la présence d'un adulte responsable. "
                     "Respecter strictement l'identifiant du panel : il conditionne "
                     "l'appariement entre les vagues d'enquête.",
        linked_indicators=["IOS2.1", "IOS2.2", "IOG2"])
    db.add(enquete)
    db.flush()
    questions_enquete = [
        ("A. Consentement", "consentement", "Le tuteur accepte-t-il de participer à l'enquête ?",
         "select_one", [{"name": "1", "label": "Oui"}, {"name": "0", "label": "Non"}], True,
         None, None, None),
        ("A. Consentement", "id_panel", "Identifiant du ménage dans le panel", "text", [], True,
         None, None, None),
        ("B. Ménage", "sexe_cm", "Sexe du chef de ménage", "select_one",
         [{"name": "1", "label": "Masculin"}, {"name": "2", "label": "Féminin"}], True,
         None, None, None),
        ("B. Ménage", "instruction_mere", "Niveau d'instruction de la mère", "select_one",
         [{"name": "0", "label": "Aucun"}, {"name": "1", "label": "Primaire"},
          {"name": "2", "label": "Secondaire"}, {"name": "3", "label": "Supérieur"}], True,
         None, None, None),
        ("B. Ménage", "taille_menage", "Nombre de personnes vivant dans le ménage", "integer",
         [], True, ". >= 1 and . <= 30", "Taille attendue entre 1 et 30.", None),
        ("C. Scolarisation", "enfants_scolarises_f", "Nombre de filles scolarisées dans le "
                                                     "ménage", "integer", [], True, ". >= 0",
         "Valeur positive attendue.", None),
        ("C. Scolarisation", "enfants_scolarises_g", "Nombre de garçons scolarisés dans le "
                                                     "ménage", "integer", [], True, ". >= 0",
         "Valeur positive attendue.", None),
        ("C. Scolarisation", "fille_maintenue", "La fille bénéficiaire est-elle toujours "
                                                "inscrite cette année ?", "select_one",
         [{"name": "1", "label": "Oui"}, {"name": "0", "label": "Non"}], True, None, None,
         "IOS2.1"),
        ("C. Scolarisation", "motif_abandon", "Motif principal de l'abandon", "select_one",
         [{"name": "1", "label": "Travail domestique"}, {"name": "2", "label": "Coût"},
          {"name": "3", "label": "Mariage"}, {"name": "4", "label": "Distance"},
          {"name": "5", "label": "Maladie"}, {"name": "6", "label": "Autre"}], False,
         None, None, None),
        ("C. Scolarisation", "transition_college", "La fille est-elle inscrite au collège cette "
                                                   "année ?", "select_one",
         [{"name": "1", "label": "Oui"}, {"name": "0", "label": "Non"},
          {"name": "9", "label": "Non concernée"}], True, None, None, "IOS2.2"),
        ("D. Programme", "bourse_recue", "Le ménage a-t-il reçu la bourse au dernier "
                                         "trimestre ?", "select_one",
         [{"name": "1", "label": "Oui"}, {"name": "0", "label": "Non"}], True, None, None, None),
        ("D. Programme", "delai_reception", "Délai de réception après la date annoncée (jours)",
         "integer", [], False, ". >= 0 and . <= 120", "Valeur attendue entre 0 et 120.", None),
        ("D. Programme", "usage_bourse", "Principaux usages de la bourse", "select_multiple",
         [{"name": "1", "label": "Fournitures scolaires"}, {"name": "2", "label": "Alimentation"},
          {"name": "3", "label": "Santé"}, {"name": "4", "label": "Transport"},
          {"name": "5", "label": "Épargne"}], False, None, None, None),
        ("E. Perception", "satisfaction", "Satisfaction générale à l'égard du programme",
         "select_one", [{"name": "1", "label": "Très satisfait"},
                        {"name": "2", "label": "Satisfait"},
                        {"name": "3", "label": "Peu satisfait"},
                        {"name": "4", "label": "Non satisfait"}], True, None, None, None),
        ("E. Perception", "changement", "Quel changement principal le programme a-t-il apporté "
                                        "au ménage ?", "text", [], False, None, None, None),
    ]
    for position, (section, nom, libelle, type_question, choix, obligatoire, contrainte,
                   message, code_indicateur) in enumerate(questions_enquete):
        question = FormQuestion(form_id=enquete.id, order_index=position, section=section,
                                name=nom, label=libelle, question_type=type_question,
                                choices=choix, required=obligatoire, constraint=contrainte,
                                constraint_message=message, linked_indicator_code=code_indicateur)
        if nom in ("sexe_cm", "instruction_mere", "taille_menage"):
            question.relevant = "${consentement} = '1'"
        if nom == "motif_abandon":
            question.relevant = "${fille_maintenue} = '0'"
        db.add(question)
    db.flush()
