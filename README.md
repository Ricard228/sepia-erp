# SEPIA — Planification, Suivi-évaluation et Apprentissage des projets et programmes de développement

Plateforme web-mobile (ERP) de **planification, de suivi-évaluation et d'apprentissage des projets
et programmes de développement**. À partir d'un cadre logique et d'un budget — importés depuis
Excel ou Word, ou créés directement dans l'application — SEPIA génère automatiquement l'ensemble
des instruments du dispositif : cadre logique paramétré, indicateurs documentés, cadre de
rendement, cadre de suivi des indicateurs (IPTT), registre des risques et des hypothèses,
chronogramme et ordonnancement (chemin critique, PERT, WBS, RACI), PTBA, carte de couverture des
zones d'intervention, fiches de collecte et questionnaires (Word et XLSForm pour KoboToolbox/ODK),
manuel de suivi-évaluation, rapports périodiques, tableaux de bord Excel et flux Power BI.

---

## 1. Fonctionnalités

### Planification
| Module | Contenu |
|---|---|
| **Portefeuille** | Vue consolidée multi-projets : indice de santé, budgets, alertes, duplication de projet |
| **Fiche projet** | Identification, ancrage institutionnel, théorie du changement, alignement stratégique (ODD, stratégies nationales) |
| **Cadre logique** | Arborescence Impact → Effets → Produits → Activités, sources de vérification, hypothèses, responsables |
| **Bénéficiaires** | Groupes ciblés : quantification (cible et atteints, par sexe, jeunes, personnes handicapées, ménages), conditions de vie de référence, critères et méthode de sélection, besoins, contraintes, bénéfices attendus, mode de participation, degré de vulnérabilité, mécanisme de plainte |
| **Partenaires** | Registre des partenaires : type, rôle, contribution financière et technique, engagements conventionnés, décaissements, appréciation de la performance, échéances |
| **Zones d'intervention** | Découpage géographique hiérarchisé, population, cible de bénéficiaires, coordonnées, responsable de zone, et **carte de couverture** à symboles proportionnels |
| **Chronogramme et ordonnancement** | Cinq onglets : diagramme de Gantt **avec chemin critique matérialisé** · **réseau PERT et courbe en S** · **organigramme des tâches (WBS)** · **matrice RACI** éditable · liste des activités. Gantt, PERT, WBS, courbe et carte sont **exportables en PNG et en SVG** |
| **PTBA / budget** | Lignes budgétaires détaillées, ventilation trimestrielle, engagements et décaissements |

### Collecte et suivi
| Module | Contenu |
|---|---|
| **Saisie des réalisations** | Écran temps réel : période, **zone**, **activité source**, ventilation par sexe / âge / groupe cible, total calculé automatiquement, statut de validation |
| **Cadre de suivi (IPTT)** | Grille cibles/réalisations par période avec saisie directe en ligne |
| **Collecte** | Concepteur de questionnaires (sections, types, modalités, contraintes, logique de saut, calculs), export Word et XLSForm |

### Analyse et évaluation
| Module | Contenu |
|---|---|
| **Indicateurs** | Fiche métadonnée complète (définition, formule, désagrégations, référence, cible, règle d'agrégation, fréquence, source, méthode, responsable, coût) et **nature de l'indicateur** : résultat ou processus |
| **Équité et désagrégation** | Ventilation consolidée par catégorie, **indice d'équité de genre**, écart à la parité, part des femmes par indicateur et par zone, détection des désagrégations manquantes |
| **Qualité des indicateurs** | Diagnostic **SMART** critère par critère (contrôle automatique + revue manuelle), score du système, actions correctrices recommandées |
| **Risques & hypothèses** | Registre coté probabilité × impact, matrice 5×5, risque résiduel, plans de contingence, suivi de validation des hypothèses |
| **Évaluation CAD-OCDE** | Exercices évaluatifs (référence, mi-parcours, finale, ex-post) notés sur les **six critères du CAD** — pertinence, cohérence, efficacité, efficience, impact, durabilité — sur une échelle à six niveaux, avec justification écrite par critère, points d'examen guidant la notation, et suivi des recommandations (réponse du management, responsable, échéance, taux de mise en œuvre) |
| **Évaluation d'impact** | Études expérimentales et quasi-expérimentales : **9 méthodes** documentées (essai randomisé, randomisation par grappes, doubles différences, appariement, DID + PSM, régression sur discontinuité, variables instrumentales, contrôle synthétique, avant-après), hypothèse d'identification, règle d'affectation, tailles des groupes, corrélation intra-grappe, **calculateur de taille d'échantillon** et contrôle de puissance, effet estimé et signification statistique |
| **Tableaux de bord** | KPI, indice de santé pondéré, équité, couverture territoriale, qualité SMART, graphiques SVG, alertes priorisées, actualisation automatique |

### Rapportage
| Module | Contenu |
|---|---|
| **Rapports périodiques** | Génération des rapports **trimestriels, semestriels et annuels** avec aperçu à l'écran avant production |
| **Sauvegarde et transfert** | Export/import **JSON** complet d'un projet ou du **portefeuille entier**, et classeur **Excel réversible** au format d'import |
| **Livrables** | 28 documents Word / Excel / JSON / ZIP produits à la demande |
| **Power BI** | Flux temps réel et modèle en étoile, table de faits désagrégée et dimension géographique |

### Méthodologie de calcul de la performance

**Deux taux** sont produits pour chaque indicateur, conformément à la gestion axée sur les résultats :

- **Taux de la période** — `réalisé ÷ cible de la même période` : c'est lui qui détermine le statut
  de performance, car comparer une réalisation intermédiaire à la cible de fin de projet
  fausserait le diagnostic ;
- **Progression vers la cible finale** — `(réalisé − référence) ÷ (cible − référence) × 100`.

Les indicateurs à progression décroissante (taux de pauvreté, pertes post-récolte…) sont traités
symétriquement. Statuts : **Atteint** ≥ 100 %, **En bonne voie** ≥ 85 %, **À surveiller** ≥ 60 %,
**Critique** < 60 %.

**Règle d'agrégation.** Un indicateur mesuré sur plusieurs zones produit plusieurs mesures pour la
même période. La consolidation suit une règle portée par l'indicateur — `Somme` (effectifs,
volumes), `Moyenne` (taux, ratios, scores, rendements), `Dernière valeur` (stocks) ou `Maximum` —
déduite de l'unité de mesure à défaut de choix explicite. Sommer un rendement moyen ou moyenner un
effectif de bénéficiaires sont les deux erreurs que cette règle prévient.

**Indice d'équité de genre.** À partir de la ventilation par sexe : part des femmes, écart à la
parité en points et appréciation (parité atteinte si l'écart est inférieur à 5 points). Calculé au
niveau du projet, de chaque indicateur, de chaque zone et de chaque activité.

**Score SMART.** Cinq critères contrôlés automatiquement à partir des données saisies (définition,
unité et mode de calcul, référence et cible, rattachement au cadre logique, échéance et fréquence),
la revue manuelle prévalant sur le contrôle automatique. Le score du système est la moyenne des
scores individuels ; chaque critère non satisfait produit une action correctrice nommée.

L'**indice de santé du projet** est une moyenne pondérée : résultats 45 %, exécution physique 30 %,
exécution financière 25 %, comparée au pourcentage de temps écoulé.

### Indicateurs d'activité et de processus (affichage optionnel)

Un indicateur porte une **nature** : `Résultat` (il mesure un changement) ou `Processus` (il mesure
la conduite de l'action — taux d'exécution du PTBA, délai de production des rapports, taux de
participation, délai de passation des marchés). Les indicateurs de processus alourdissent la
lecture du dispositif et ne sont pertinents que sur certains projets : leur affichage est donc
commandé par une option du projet, `show_process_indicators`, activable d'une case à cocher depuis
la vue Indicateurs ou la fiche du projet.

Désactivés, ils **restent enregistrés** — mesures et cibles comprises — mais sont exclus des
tableaux de bord, des analyses d'équité et de qualité, des rapports périodiques et des livrables.
Le nombre d'indicateurs masqués reste affiché, afin que l'option ne dissimule jamais l'existence
des données.

### Bénéficiaires, partenaires et rattachement des indicateurs

Un groupe de bénéficiaires est décrit sur **deux registres complémentaires**. Le registre
*quantitatif* porte la cible et les effectifs atteints, ventilés femmes / jeunes / personnes
handicapées, le nombre de ménages et leur taille moyenne, le revenu annuel et le taux de pauvreté
de référence. Le registre *qualitatif* porte les critères et la méthode de sélection, les besoins
exprimés, les contraintes, les bénéfices attendus, le mode de participation au projet, le degré de
vulnérabilité et le mécanisme de gestion des plaintes qui leur est ouvert. Le taux d'atteinte et la
part des femmes atteintes sont calculés, jamais saisis.

Un indicateur peut être **rattaché à un groupe de bénéficiaires**. Le rattachement fait le lien
entre la population visée et la mesure du changement : la fiche d'un groupe affiche alors les
indicateurs qui le documentent, leur taux d'atteinte et leur part de femmes, et la synthèse
signale les groupes ciblés qu'aucun indicateur ne mesure — angle mort classique d'un dispositif de
suivi.

Le registre des partenaires suit les contributions **conventionnées** et **effectivement
décaissées**, ce qui donne un taux de décaissement par partenaire et pour l'ensemble du montage
financier, ainsi que les échéances de convention à renouveler.

### Évaluation selon les critères du CAD de l'OCDE

Chaque exercice évaluatif est noté sur les six critères du CAD — **pertinence** (le projet
répond-il aux besoins ?), **cohérence** (s'articule-t-il aux autres interventions ?),
**efficacité** (atteint-il ses objectifs ?), **efficience** (au meilleur coût ?), **impact**
(quels effets de portée supérieure ?), **durabilité** (les bénéfices se maintiendront-ils ?).

La notation suit une **échelle à six niveaux** (1 Très insatisfaisant → 6 Très satisfaisant),
convention retenue par les principales banques de développement, qui **écarte la note médiane
neutre** : l'évaluateur doit se prononcer du côté satisfaisant ou insatisfaisant. Chaque critère
s'accompagne de ses **points d'examen** — les questions auxquelles la note doit répondre — et
d'une justification écrite obligatoire ; une note sans justification est refusée. La note globale
est la moyenne des critères notés, la synthèse produit la moyenne par critère sur l'ensemble des
évaluations achevées, ce qui révèle la dimension sur laquelle le projet est **systématiquement**
le plus faible.

Les **recommandations** portent leur criticité, la réponse du management (acceptée, partiellement
acceptée, rejetée), le responsable, l'échéance et le taux de mise en œuvre ; celles qui sont
échues et non soldées sont signalées.

### Évaluation d'impact : méthodes expérimentales et quasi-expérimentales

Mesurer l'impact suppose de reconstituer le **contrefactuel** : ce qui serait advenu sans le
projet. La plateforme documente neuf méthodes, chacune avec son **hypothèse d'identification**,
ses conditions d'application, ses forces et ses limites.

| Approche | Méthodes | Hypothèse d'identification |
|---|---|---|
| **Expérimentale** | Essai randomisé contrôlé · Randomisation par grappes | L'affectation aléatoire rend les groupes comparables en espérance sur toutes les caractéristiques, observées comme non observées |
| **Quasi-expérimentale** | Doubles différences (DID) · Appariement par score de propension (PSM) · DID + PSM · Régression sur discontinuité (RDD) · Variables instrumentales (IV) · Contrôle synthétique | Tendances parallèles, indépendance conditionnelle aux observables, continuité au seuil, exclusion de l'instrument, ajustement pré-intervention selon la méthode |
| **Non contrefactuelle** | Avant-après | Aucune : la variation observée mélange l'effet du projet et tout ce qui a changé par ailleurs — à ne retenir qu'en dernier recours, et à interpréter comme une description, non comme un impact |

Un **calculateur de taille d'échantillon** est intégré : à partir de l'effet minimal détectable,
de l'écart-type de l'indicateur de résultat, de la puissance et du seuil de signification
recherchés, il donne l'effectif requis par bras. Lorsque la randomisation porte sur des grappes
(écoles, villages, groupements), il applique l'**effet de plan** `1 + (m − 1) · ρ` : avec des
grappes de 30 unités et une corrélation intra-grappe de 0,08, l'échantillon requis est multiplié
par 3,3 — l'oubli le plus coûteux de la conception d'une évaluation d'impact.

Le contrôle de puissance compare l'échantillon prévu à l'échantillon requis et signale une étude
**sous-dimensionnée**, c'est-à-dire une étude qui risque de conclure à l'absence d'effet alors
qu'un effet réel existe. Il n'est calculé que si l'écart-type de l'indicateur de résultat est
renseigné : sans lui, le calcul reposerait sur une hypothèse implicite et produirait un verdict
trompeur.

### Carte de couverture des zones d'intervention

La carte figure dans la vue **Zones d'intervention** et, en format réduit, sur le tableau de bord.
C'est une **carte à symboles proportionnels** : la *surface* de chaque cercle — et non son rayon —
est proportionnelle aux bénéficiaires atteints, sa *couleur* traduit le taux de couverture de la
cible de la zone, et un demi-disque signale la part des femmes. Les liens en pointillé relient
chaque zone à sa zone mère.

La projection est celle de Mercator sphérique (EPSG:3857) et le rendu comprend un graticule
gradué, une échelle métrique et une rose des vents — **sans aucune bibliothèque cartographique** :
la carte est produite en SVG par `charts.js`, comme les autres graphiques.

Un **fond de carte OpenStreetMap** peut être superposé, activable par une case à cocher. Il est
chargé en simples balises `<img>` (calcul des tuiles en une vingtaine de lignes, aucune dépendance)
et constitue le seul appel réseau externe de toute la plateforme. Si les tuiles ne répondent pas —
réseau filtrant, absence de connexion — la plateforme le détecte au bout de six secondes, désactive
le fond et le mémorise : la carte reste alors pleinement exploitable grâce au graticule, à
l'échelle et aux symboles. L'attribution « © Contributeurs OpenStreetMap » est affichée
conformément à la licence.

Les colonnes latitude et longitude figurent dans l'export « Consolidation par zone », ce qui permet
de cartographier les mêmes données dans Power BI (visuel Carte) ou dans un SIG.

### Export des graphiques en image

Le diagramme de Gantt, le réseau PERT, l'organigramme des tâches, la courbe d'avancement et la
carte de couverture s'exportent en **PNG** (rendu au double de la résolution, fond blanc, prêt à
insérer dans un rapport) et en **SVG** (vectoriel, redimensionnable sans perte, modifiable dans un
logiciel de dessin).

Aucune bibliothèque n'est nécessaire : les graphiques étant du SVG autonome — couleurs portées par
des attributs, aucune police externe —, l'export sérialise le SVG puis, pour le PNG, le rastérise
dans un canevas. L'image de la carte contient les symboles, le graticule et l'échelle, mais pas le
fond de carte OpenStreetMap, dont l'origine externe rendrait le canevas non exportable.

### Sauvegarde, transfert et restauration

| Format | Contenu | Réversible |
|---|---|---|
| **JSON projet** | Intégralité d'un projet : cadre logique, zones, indicateurs, cibles, réalisations désagrégées et localisées, activités, budget, risques, hypothèses, parties prenantes, matrice RACI, questionnaires et questions | Oui, à l'identique |
| **JSON portefeuille** | Tous les projets de l'instance dans un fichier unique | Oui, à l'identique |
| **Excel de transfert** | Toutes les données du projet dans la structure du modèle d'import, retravaillable dans un tableur | Oui, hors questionnaires |

À l'import, les identifiants sont réattribués et **toutes les références internes réécrites** —
parent d'un résultat, zone d'une mesure, activité d'une ligne budgétaire, acteur d'une affectation
RACI. Le fichier peut donc provenir d'une autre instance de la plateforme. Si le code du projet est
déjà pris, il est suffixé et l'utilisateur en est averti ; l'option « remplacer » permet à l'inverse
d'écraser le projet de même code, pour restaurer une sauvegarde.

L'aller-retour est vérifié entité par entité : sur le projet de démonstration, les 8 zones,
14 résultats, 20 indicateurs, 26 cibles, 79 réalisations, 14 activités, 18 lignes budgétaires,
8 risques, 6 hypothèses, 11 parties prenantes, 75 affectations RACI et 2 questionnaires sont
restitués à l'identique, chemin critique et analyse d'équité compris.

### Ordonnancement : chemin critique, PERT, WBS et RACI

**Chemin critique (CPM).** Les activités portent des antécédents (relation fin-début) et une durée
— imposée, ou déduite des dates. Un tri topologique détecte les circuits ; une passe avant calcule
les dates au plus tôt, une passe arrière les dates au plus tard. La **marge totale** est le retard
admissible sans décaler la fin du projet, la **marge libre** celui admissible sans décaler
l'activité suivante. Une activité de marge nulle est critique. La **durée totale du projet** est la
date de fin au plus tôt la plus tardive ; elle est comparée à la date de clôture planifiée, et
l'écart est signalé.

La plateforme signale également les **incohérences de planification** : un antécédent qui s'achève
après le début planifié de son successeur rend le calendrier saisi et le lien d'antécédence
contradictoires.

**Réseau PERT.** Représentation « activité sur nœud » : chaque activité est une boîte portant ses
dates au plus tôt et au plus tard, sa durée et sa marge ; les flèches figurent les antécédences et
le chemin critique est tracé en rouge. Les activités d'un même **rang** sont indépendantes et
peuvent être conduites en parallèle.

**Organigramme des tâches (WBS).** Décomposition hiérarchique déduite de la chaîne de résultats :
effets → composantes, produits → sous-composantes, activités → lots de travail. Codification
automatique (1, 1.1, 1.1.1), consolidation ascendante des coûts, durées et avancements, et
dictionnaire des lots. Les activités non rattachées sont regroupées dans un lot « Gestion,
coordination et suivi-évaluation ».

**Matrice RACI.** Grille activités × parties prenantes éditable directement en ligne :
**R** réalise, **A** approuve et rend compte, **C** est consulté avant la décision, **I** est
informé après. Deux règles sont contrôlées — exactement un A par activité, au moins un R — et la
charge par acteur est calculée, avec alerte sur les goulots d'étranglement décisionnels.

### Import / export

- **Import Excel** : reconnaissance souple des onglets et des intitulés de colonnes
  (Cadre logique, Indicateurs, Cibles, Réalisations, Activités, Budget, Risques, Hypothèses,
  **Zones**). Les colonnes de désagrégation sont reconnues au format `Catégorie - Modalité`
  (ex. `Sexe - Femme`, `Groupe cible - Jeune`) ou dans une colonne compacte
  `Sexe:Femme=210;Sexe:Homme=255`. Un modèle prérempli et commenté est téléchargeable depuis
  l'application.
- **Import Word** : analyse des tableaux du document, détection des matrices de cadre logique,
  extraction des niveaux, codes, énoncés, sources de vérification, hypothèses et indicateurs.
- **Import XLSForm** et **réinjection des données KoboToolbox** : les réponses alimentent
  automatiquement les indicateurs reliés (agrégation par somme ou par moyenne selon l'unité).
- **16 livrables générés** en Word, Excel et ZIP (voir § 4).

---

## 2. Architecture technique

```
sepia-erp/
├── app/
│   ├── main.py               FastAPI : montage des routeurs, service de l'interface, sonde de santé
│   ├── config.py             Configuration et référentiels métier
│   ├── database.py           Moteur SQLAlchemy (SQLite en local, PostgreSQL en production)
│   ├── models.py             24 entités : projets, cadre logique, indicateurs, cibles,
│   │                         réalisations (désagrégées et localisées), zones, risques,
│   │                         hypothèses, activités, budget, parties prenantes,
│   │                         affectations RACI, bénéficiaires, partenaires,
│   │                         évaluations, recommandations, études d'impact,
│   │                         formulaires, questions, réponses, utilisateurs,
│   │                         membres de projet, clés d'API, audit
│   ├── security.py           PBKDF2-SHA256, politique de mot de passe, jetons signés HMAC
│   │                         en cookie HttpOnly, verrouillage de compte, clés d'API
│   │                         (bibliothèque standard uniquement)
│   ├── middleware.py         En-têtes de sécurité et CSP, limitation de débit, plafond de
│   │                         taille des requêtes, journalisation corrélée des erreurs
│   ├── crud.py               Fabrique de routeurs CRUD génériques, contrôle d'accès au
│   │                         niveau de l'objet, listes blanches de champs modifiables
│   ├── seed.py               Compte administrateur et chargement des projets d'exemple
│   ├── seed_sante.py         Deuxième projet d'exemple, intégralement renseigné
│   ├── routers/              auth · projects · entities · evaluations · imports ·
│   │                         exports · powerbi
│   └── services/
│       ├── analytics.py      Moteur de performance, règles d'agrégation, équité de genre,
│       │                     consolidation par zone et par activité, qualité SMART,
│       │                     analyses périodées, alertes, portefeuille
│       ├── planning.py       Chemin critique (CPM), réseau PERT, organigramme des
│       │                     tâches (WBS) et matrice des responsabilités (RACI)
│       ├── evaluation.py     Notation CAD-OCDE, synthèses bénéficiaires et partenaires,
│       │                     méthodes d'évaluation d'impact, taille d'échantillon et
│       │                     contrôle de puissance
│       ├── portability.py    Export et import JSON complets (projet, portefeuille)
│       ├── excel_export.py   Classeurs Excel mis en forme (XlsxWriter)
│       ├── word_export.py    Documents Word (python-docx)
│       ├── evaluation_export.py  Livrables des modules d'évaluation (Excel et Word)
│       ├── xlsform.py        Génération XLSForm KoboToolbox / ODK
│       └── importer.py       Analyseurs Excel et Word tolérants
├── static/                   Interface web-mobile : HTML + CSS + JavaScript natif,
│   │                         aucune dépendance externe, aucune étape de build
│   ├── index.html
│   ├── css/app.css
│   └── js/ core.js · charts.js · views.js · views-evaluation.js · app.js
├── requirements.txt
├── render.yaml               Blueprint de déploiement Render (service web + base PostgreSQL)
└── docs/                     Documentation fonctionnelle et technique (Word)
```

**Choix structurants**

- **Zéro dépendance front-end** : les graphiques (anneau, barres, courbes, jauge, Gantt, matrice
  de risques, réseau PERT, organigramme WBS, carte de couverture) sont produits en SVG par
  `charts.js`. Aucun CDN, aucun `npm install`, aucun bundler :
  le déploiement se réduit à `pip install -r requirements.txt`.
- **Authentification sans dépendance** : hachage PBKDF2-SHA256 (240 000 itérations) et jetons
  signés HMAC-SHA256 issus de la bibliothèque standard — pas de `passlib`, `bcrypt` ni `python-jose`
  à compiler. Le jeton est déposé dans un cookie `HttpOnly` inaccessible au JavaScript.
- **Base portable** : SQLite en développement, PostgreSQL en production, via la même couche ORM.
- **Rôles hiérarchiques** : lecteur < opérateur < responsable S&E < coordonnateur < administrateur.

---

## 3. Installation locale

```bash
git clone https://github.com/Ricard228/sepia-erp.git
cd sepia-erp
python -m venv .venv && .venv\Scripts\activate      # Windows
# source .venv/bin/activate                          # Linux / macOS
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Ouvrir <http://localhost:8000>.

Pour fixer le mot de passe administrateur de développement plutôt que de le relever dans les
journaux à chaque base neuve :

```bash
SEPIA_ADMIN_PASSWORD='<votre-phrase-de-passe>' uvicorn app.main:app --reload --port 8000
```

Sous PowerShell : `$env:SEPIA_ADMIN_PASSWORD='<votre-phrase-de-passe>'` avant la commande.
Choisir une phrase de passe conforme au § 8, et **ne l'inscrire dans aucun fichier versionné** —
c'est précisément ce que ce dépôt s'interdit.

### Première connexion

**Il n'existe aucun mot de passe par défaut inscrit dans le code.** Au premier démarrage :

- si `SEPIA_ADMIN_PASSWORD` est renseignée, ce mot de passe est utilisé — il doit respecter la
  politique décrite au § 8 ;
- sinon, la plateforme **engendre un mot de passe aléatoire** et l'inscrit **une seule fois** dans
  les journaux de démarrage, encadré d'une bannière. Le relever à ce moment-là ; il ne sera plus
  affiché. Le changement du mot de passe est imposé à la première connexion.

Le compte administrateur initial est `admin@sepia.org`, modifiable par `SEPIA_ADMIN_EMAIL`.

### Projets d'exemple

Deux projets complets sont chargés, conçus pour servir de cas pratiques :

| Projet | Secteur | Contenu |
|---|---|---|
| **PADRA-2025** — Programme d'appui au développement rural et à l'agriculture | Agriculture, sécurité alimentaire | Cadre logique complet, zones, indicateurs désagrégés, activités ordonnancées, budget, risques, hypothèses, parties prenantes et RACI, instruments de collecte |
| **PASSE-2026** — Programme de santé scolaire et de scolarisation des filles | Éducation, santé | 8 zones, 3 effets et 5 produits, **5 groupes de bénéficiaires**, **6 partenaires**, 17 indicateurs dont 3 de processus, 37 cibles et 101 réalisations réparties par zone et par sexe, 13 activités enchaînées, 14 lignes budgétaires, 7 risques, 6 hypothèses, 13 parties prenantes et 75 affectations RACI, **2 évaluations CAD** avec 4 recommandations, **2 études d'impact** (essai randomisé par grappes et DID + PSM), 2 questionnaires |

Le second projet renseigne **toutes** les rubriques de la plateforme : il sert de référence pour
comprendre ce qu'un dispositif de suivi-évaluation complet contient. Mettre `SEPIA_SEED_DEMO=0`
pour démarrer sur une instance vierge.

### Variables d'environnement

| Variable | Rôle | Défaut |
|---|---|---|
| `DATABASE_URL` | Chaîne de connexion PostgreSQL | SQLite local `data/sepia.db` |
| `SEPIA_ENV` | `production` active les garde-fous bloquants (cookie `Secure`, HSTS, erreurs non détaillées) | `production` si `DATABASE_URL` est définie, sinon `developpement` |
| `SEPIA_SECRET_KEY` | Clé de signature des jetons | **obligatoire en production** (démarrage refusé sans elle) ; aléatoire à chaque démarrage en développement |
| `SEPIA_ADMIN_EMAIL` | Compte administrateur initial | `admin@sepia.org` |
| `SEPIA_ADMIN_PASSWORD` | Mot de passe initial | **aucun** — engendré aléatoirement et journalisé une fois |
| `SEPIA_ADMIN_RESET` | Réinitialise le compte d'administration au démarrage (voir § 8) | vide — aucune réinitialisation |
| `SEPIA_TOKEN_TTL` | Durée de validité des jetons (secondes) | `43200` (12 h) |
| `SEPIA_SEED_DEMO` | Charger les projets d'exemple (`0` pour désactiver) | `1` |
| `SEPIA_CORS_ORIGINS` | Origines autorisées pour les appels entre domaines, séparées par des virgules | **vide** — aucune origine tierce |

---

## 4. Livrables générés

| Livrable | Format | Contenu |
|---|---|---|
| Cadre logique | Excel + Word | Matrice complète, annexe des hypothèses critiques |
| Cadre de rendement | Excel + Word | PMF : taux de période, progression finale, statuts, sources, coûts |
| Cadre de suivi des indicateurs (IPTT) | Excel | Cibles/réalisations par période, mise en forme conditionnelle |
| Chronogramme | Excel | Gantt mensuel coloré selon l'état d'avancement |
| **Chemin critique et réseau PERT** | Excel | Ordonnancement CPM, marges, durée du projet, activités par rang |
| **Organigramme des tâches (WBS)** | Excel | Décomposition codifiée, coûts consolidés, dictionnaire des lots |
| **Matrice RACI** | Excel | Matrice activités × acteurs, charge par partie prenante, contrôle de cohérence |
| **Organisation et ordonnancement** | Word | Document réunissant WBS, chemin critique, réseau PERT et matrice RACI |
| PTBA | Excel | Budget détaillé, ventilation trimestrielle, synthèse graphique |
| Registre des risques | Excel + Word | Registre coté, matrice 5×5, plans de contingence |
| Fiches métadonnées des indicateurs | Word | Une fiche par indicateur avec séries périodiques |
| **Plan et manuel de suivi-évaluation** | Word | Document maître en 15 chapitres, alimenté par les données du projet |
| Rapport de performance | Word | Résumé exécutif, indicateurs, alertes, mesures correctrices |
| **Rapport trimestriel / semestriel / annuel** | Word | Rapport périodé en 8 parties : résumé exécutif, performance de la période, analyse d'équité, consolidation par zone, exécution physique et financière, difficultés et mesures correctrices, qualité du dispositif, bloc de validation |
| **Analyse d'équité et données désagrégées** | Excel | Ventilation par catégorie, indice d'équité de genre, détail indicateur × modalité, graphique de répartition |
| **Consolidation par zone d'intervention** | Excel | Bénéficiaires et indicateurs par zone, taux de couverture, coordonnées cartographiables, collecte par activité |
| **Revue qualité SMART** | Excel | Diagnostic critère par critère, score du système, actions correctrices |
| **Bénéficiaires : ciblage et caractérisation** | Excel | Quantification et atteinte par groupe, caractérisation qualitative, indicateurs rattachés |
| **Partenaires : engagements et performance** | Excel | Contributions conventionnées et décaissées, taux de décaissement, échéances |
| **Évaluation CAD-OCDE** | Excel | Notes et justifications par critère, moyennes consolidées, registre des recommandations |
| **Rapport d'évaluation CAD-OCDE** | Word | Rapport structuré par critère avec échelle de notation, justifications et suivi des recommandations |
| **Protocole d'évaluation d'impact** | Word | Méthode et hypothèse d'identification, groupes de traitement et de comparaison, calcul de puissance, résultats et signification statistique |
| Tableau de bord | Excel | KPI, graphiques natifs Excel, alertes, détail des indicateurs |
| Jeu de données Power BI | Excel | Modèle en étoile + dimension géographique + faits désagrégés + notice DAX |
| Questionnaires | Word | Mise en page d'administration papier |
| Questionnaires | XLSForm | Téléversable dans KoboToolbox / ODK Central |
| Modèle d'import | Excel | Classeur type commenté, 8 onglets avec exemples |
| **Dossier complet** | ZIP | L'ensemble des livrables ci-dessus |

---

## 5. Connexion Power BI

Deux méthodes, décrites dans la vue « Power BI » de l'application :

1. **Flux web temps réel** — `Obtenir des données > Web` avec l'URL
   `https://<domaine>/api/powerbi/<id_projet>/dataset?token=<jeton>`.
   Le jeton est généré à la connexion et reste valide 12 heures.
   Chaque table est également exposée individuellement en JSON et en CSV.
2. **Classeur Excel structuré** — modèle en étoile prêt à charger, avec notice de création des
   relations et des mesures DAX recommandées.

Tables exposées : `Dim_Projet`, `Dim_Resultat`, `Dim_Indicateur`, `Dim_Zone`, `Dim_Calendrier`,
`Fait_Cible`, `Fait_Realisation`, `Fait_Desagregation`, `Fait_Activite`, `Fait_Budget`,
`Fait_Risque`.

`Fait_Desagregation` est une table dépliée — une ligne par modalité — directement exploitable dans
un histogramme empilé segmenté par sexe ou par groupe cible. `Dim_Zone` porte latitude et longitude,
ce qui permet un visuel cartographique sans traitement supplémentaire.

---

## 6. Déploiement sur Render

### Option A — Blueprint (recommandée)

1. Render → **New** → **Blueprint** → sélectionner ce dépôt.
   Le fichier `render.yaml` provisionne le service web **et** la base PostgreSQL.
2. Renseigner la variable `SEPIA_ADMIN_PASSWORD` dans le tableau de bord Render.
3. Déployer. La sonde `/api/sante` confirme la disponibilité.

### Option B — Service web manuel

| Paramètre | Valeur |
|---|---|
| Environment | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/api/sante` |

Créer ensuite une base PostgreSQL Render et lier sa `connectionString` à la variable
`DATABASE_URL` du service web.

> **Note sur le plan gratuit** : le stockage disque n'est pas persistant. La base PostgreSQL
> est donc indispensable en production ; sans elle, les données SQLite seraient perdues à chaque
> redéploiement.

---

## 7. API

Documentation interactive : `/api/docs` (Swagger) et `/api/redoc`.

Principaux points d'entrée :

```
POST   /api/auth/login                     Authentification (dépose le cookie de session)
POST   /api/auth/logout                    Fermeture de la session courante
POST   /api/auth/deconnexion-globale       Invalidation de toutes les sessions du compte
GET    /api/auth/moi                       Profil de l'utilisateur connecté
GET    /api/auth/politique-mot-de-passe    Règles de mot de passe appliquées
POST   /api/auth/cles-api                  Création d'une clé d'API en lecture seule
GET    /api/projects                       Portefeuille
GET    /api/dashboard/{id}                 Tableau de bord complet
GET    /api/portefeuille                   Consolidation multi-projets
GET    /api/logframe/tree/{id}             Arborescence du cadre logique
GET    /api/indicateurs/suivi/{id}         Grille IPTT
GET    /api/saisie/contexte/{id}           Indicateurs, zones et activités pour la saisie
POST   /api/indicators/{id}/saisie         Saisie d'une réalisation désagrégée et localisée
POST   /api/actuals/{id}/valider           Validation ou rejet d'une mesure
POST   /api/projects/{id}/periodes         Génération automatique des cibles périodiques
GET    /api/analyse/desagregation/{id}     Analyse d'équité (genre, âge, groupe cible)
GET    /api/analyse/zones/{id}             Consolidation par zone et par activité
GET    /api/analyse/smart/{id}             Diagnostic SMART du système d'indicateurs
POST   /api/indicators/{id}/smart          Enregistrement d'une revue SMART
GET    /api/analyse/periode/{id}?periode=  Photographie d'une période de rapportage
GET    /api/analyse/periodes/{id}          Périodes existantes et suggérées
GET    /api/planning/chemin-critique/{id}  Ordonnancement CPM, marges, durée du projet
GET    /api/planning/wbs/{id}              Organigramme des tâches consolidé
POST   /api/planning/wbs/{id}/codifier     Inscription des codes WBS sur les activités
GET    /api/planning/raci/{id}             Matrice RACI, charge par acteur, anomalies
POST   /api/planning/raci/{id}/cellule     Attribution ou retrait d'un rôle RACI
GET    /api/planning/courbe-avancement/{id} Courbe en S : engagement planifié et réalisé
GET    /api/beneficiaires/synthese/{id}    Ciblage, atteinte et indicateurs rattachés
GET    /api/partenaires/synthese/{id}      Contributions, décaissements et échéances
GET    /api/evaluations/synthese/{id}      Notes CAD consolidées et suivi des recommandations
GET    /api/evaluations/{id}/detail        Fiche d'un exercice évaluatif, critère par critère
POST   /api/evaluations/{id}/notation      Enregistrement d'une note et de sa justification
GET    /api/impact/synthese/{id}           Portefeuille d'études d'impact du projet
GET    /api/impact/{id}/detail             Protocole, contrôle de puissance et résultats
POST   /api/impact/calcul-echantillon      Taille d'échantillon requise (avec effet de plan)
GET    /api/evaluation/referentiels        Critères CAD, échelle de notation, méthodes d'impact
GET    /api/exports/{id}/projet-json       Sauvegarde JSON complète d'un projet
GET    /api/exports/portefeuille/json      Sauvegarde JSON du portefeuille entier
POST   /api/imports/sepia-json             Restauration d'un projet ou d'un portefeuille
POST   /api/imports/excel/{id}             Import d'un classeur
POST   /api/imports/word/analyser          Analyse d'un document Word
POST   /api/imports/kobo/{form_id}         Réinjection de données collectées
GET    /api/exports/{id}/{livrable}        Téléchargement d'un livrable
GET    /api/exports/{id}/dossier-complet   Archive ZIP de tous les livrables
GET    /api/powerbi/{id}/dataset?token=…   Flux Power BI
GET    /api/sante                          Sonde de disponibilité
```

---

## 8. Sécurité

### Principes retenus

**Aucun secret dans le dépôt.** Il n'existe ni clé d'API, ni jeton, ni mot de passe inscrit dans
le code ou dans les fichiers de configuration versionnés. En production, l'absence de
`SEPIA_SECRET_KEY` **empêche le démarrage** plutôt que de retomber silencieusement sur une valeur
connue de tous. En développement, la clé est tirée au hasard à chaque démarrage — les sessions ne
survivent pas à un redémarrage, ce qui est exactement le comportement souhaitable.

**Le navigateur ne décide de rien.** L'interface masque des écrans selon le rôle, mais cette
décision est *cosmétique* : chaque appel d'API revérifie côté serveur l'authentification, le rôle
et — c'est le point décisif — l'**appartenance de l'objet manipulé à un projet auquel
l'utilisateur a accès**. Un identifiant deviné dans une URL ne donne rien. Les projets étant
énumérables par construction, un accès refusé répond **404 et non 403** : la réponse ne confirme
pas l'existence de la ressource.

**Le serveur ne fait confiance à rien de ce qu'il reçoit.** Les champs modifiables sont définis
par **liste blanche** : un client qui ajoute `role`, `is_active`, `password_hash` ou `project_id`
à sa requête voit ces champs ignorés, jamais appliqués. Aucune requête n'est construite par
concaténation de texte : tout passe par les paramètres liés de l'ORM, et les jokers `%` et `_`
des recherches sont échappés.

### Mesures détaillées

| Domaine | Mesure |
|---|---|
| **Mots de passe** | PBKDF2-SHA256, **240 000 itérations**, sel aléatoire par compte. Aucun stockage en clair, aucun chiffrement réversible. Politique imposée : **12 caractères minimum**, au moins 3 classes de caractères, refus des mots de passe courants, des suites de caractères et de tout mot de passe contenant le nom ou l'adresse électronique du compte. Un générateur de phrase de passe est proposé. |
| **Sessions** | Jeton signé HMAC-SHA256 déposé dans un cookie `HttpOnly` · `SameSite=Strict` · `Secure` en production. **Le JavaScript ne peut pas le lire** — ni un script injecté, ni une extension. Aucun jeton en `localStorage`. Chaque compte peut invalider toutes ses sessions d'un appel (`tokens_valid_from`). |
| **Force brute** | Verrouillage progressif du compte après échecs répétés, réponse `429`. Message d'échec **unique** (« Identifiants incorrects ») et comparaison à durée constante même lorsque le compte n'existe pas : l'API ne permet pas d'énumérer les comptes. |
| **Limitation de débit** | Fenêtre glissante par adresse et par catégorie d'appel, avec quotas distincts pour l'authentification, les écritures, les exports et la lecture. Plafond de taille sur le corps des requêtes. |
| **En-têtes** | `Content-Security-Policy` avec `script-src 'self'` (aucun script en ligne, aucun CDN), `frame-ancestors 'none'`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, HSTS en production, `Cache-Control: no-store` sur `/api/`. |
| **Origines** | CORS **fermé par défaut** : sans `SEPIA_CORS_ORIGINS`, aucune origine tierce n'est acceptée. L'interface, servie par le même domaine, n'en a pas besoin. |
| **Injection dans l'interface** | Tout texte issu des données est **échappé** avant insertion dans le HTML ou le SVG — libellés, noms d'activités, désagrégations, commentaires, recommandations. Un énoncé d'indicateur contenant du balisage s'affiche comme du texte. |
| **Comptes** | **Aucune inscription libre** : les comptes sont ouverts par un administrateur. L'adresse électronique doit être **confirmée** par un lien à jeton — usage unique, réponse indistincte en cas de jeton faux — avant toute connexion. Mot de passe provisoire engendré, changement imposé au premier accès. Un administrateur ne peut ni se rétrograder, ni se désactiver, ni se supprimer, ni supprimer le dernier administrateur. |
| **Accès applicatif** | Rôles hiérarchiques (lecteur < opérateur < responsable S&E < coordonnateur < administrateur) **et** appartenance projet par projet. L'administration n'est pas une simple page cachée : ses points d'entrée exigent le rôle. |
| **Clés d'API** | Le flux Power BI n'utilise plus de jeton de session dans l'URL mais des **clés d'API en lecture seule**, nominatives, limitées à un projet, datées, révocables et **stockées hachées** — seule leur empreinte est conservée, la valeur n'est affichée qu'à la création. |
| **Téléversements** | Plafond de taille, contrôle du **nombre magique** du fichier (et non de son extension), refus des archives dont le ratio de décompression dépasse le seuil (protection contre les bombes de décompression), analyse en mémoire sans écriture sur le disque. |
| **Erreurs** | Aucune trace d'exécution renvoyée au client. Une erreur produit un **identifiant de corrélation** affiché à l'utilisateur et une entrée complète dans les journaux du serveur. Le détail diagnostique n'est renvoyé qu'en développement. |
| **Dépendances** | 10 dépendances directes, toutes épinglées à une version précise et vérifiées (`requirements.txt`), aucune dépendance JavaScript. Revue trimestrielle recommandée. |
| **Traçabilité** | Créations, modifications et suppressions consignées dans le journal d'audit, consultable depuis la vue Administration. |

### Reprendre la main sur le compte d'administration

Mot de passe perdu, compte verrouillé par des tentatives infructueuses, désactivé ou rétrogradé
par erreur : la plateforme n'offre **aucun point d'entrée réseau de réinitialisation**. Un tel
point d'entrée serait une porte dérobée permanente, exposée à quiconque connaît l'adresse du
service. La reprise de main passe donc par une preuve d'autorité réelle — l'accès au tableau de
bord d'hébergement ou au serveur.

**Sur un hébergement sans accès shell (Render, plan gratuit compris)** — par variable
d'environnement :

1. Définir `SEPIA_ADMIN_RESET` à `1` dans les variables du service ;
2. facultativement, définir `SEPIA_ADMIN_PASSWORD` pour choisir le mot de passe ;
3. redéployer ou redémarrer ;
4. relever le mot de passe dans les journaux de démarrage — chercher
   `COMPTE ADMINISTRATEUR RÉINITIALISÉ` ;
5. **retirer `SEPIA_ADMIN_RESET`** : tant que la variable est présente, chaque redémarrage
   réinitialise le compte.

**Avec un accès au serveur ou à la base** :

```bash
python scripts/reinitialiser_admin.py
```

Dans les deux cas, le compte est **recréé s'il a disparu** et remis en état s'il existe : nouveau
mot de passe, rôle d'administrateur rétabli, compte réactivé, verrouillage et tentatives
infructueuses effacés, adresse considérée comme confirmée. Le changement du mot de passe est exigé
à la connexion suivante, et **toutes les sessions ouvertes sont fermées** — si le mot de passe a
été perdu, on ne peut pas exclure qu'il l'ait été au profit de quelqu'un d'autre.

Il existe une troisième voie, sans réinitialisation : donner une **nouvelle valeur** à
`SEPIA_ADMIN_EMAIL`. L'amorçage ne trouve pas ce compte et le crée. L'ancien compte reste en
place, à supprimer ensuite depuis la vue Administration. Un administrateur voyant l'ensemble du
portefeuille sans rattachement explicite, les projets restent immédiatement accessibles.

### Exploitation

- Renseigner `SEPIA_SECRET_KEY` (le blueprint Render la génère), `SEPIA_ADMIN_PASSWORD` et
  `SEPIA_CORS_ORIGINS` avant l'ouverture du service.
- Révoquer les clés d'API dès qu'un utilisateur quitte le projet ; elles survivent à la
  fermeture de sa session.
- Sauvegarder régulièrement la base PostgreSQL (Render propose des sauvegardes automatiques sur
  les plans payants).
- Relever le correctif Python et les versions des dépendances à chaque revue trimestrielle, puis
  rejouer le jeu de vérification avant de redéployer.

### Vérification

```bash
python scripts/verifier_securite.py
```

Les garde-fous ci-dessus sont éprouvés par un jeu de **51 contrôles automatisés** exécutés contre
l'application réelle, sur une base temporaire : refus des identifiants erronés avec message indistinct, attributs du cookie
de session, présence et contenu des en-têtes de sécurité, refus systématique des appels anonymes,
tentative d'élévation de privilège par le corps de la requête, cycle complet de confirmation
d'adresse (dont le rejeu d'un jeton déjà consommé), cloisonnement d'un lecteur non membre,
politique de mot de passe, téléversements piégés (mauvais nombre magique, extension interdite,
dépassement de gabarit), jokers SQL dans la recherche, champ de rattachement arbitraire, et
fermeture effective de la session.

---

## 9. Licence et crédits

Développé pour la gestion des projets et programmes de développement.
Méthodologie conforme à l'approche du cadre logique (LFA), à la gestion axée sur les résultats
(GAR) et aux critères d'évaluation du CAD de l'OCDE (pertinence, cohérence, efficacité,
efficience, impact, durabilité).
