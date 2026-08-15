# SEPIA — Système d'Évaluation, de Planification, d'Indicateurs et d'Apprentissage

Plateforme web-mobile (ERP) de **planification et de suivi-évaluation des projets et programmes
de développement**. À partir d'un cadre logique et d'un budget — importés depuis Excel ou Word,
ou créés directement dans l'application — SEPIA génère automatiquement l'ensemble des instruments
du dispositif de S&E : cadre logique paramétré, indicateurs documentés, cadre de rendement,
cadre de suivi des indicateurs (IPTT), registre des risques et des hypothèses, chronogramme,
PTBA, fiches de collecte et questionnaires (Word et XLSForm pour KoboToolbox/ODK), manuel de
suivi-évaluation, tableaux de bord Excel et flux Power BI.

---

## 1. Fonctionnalités

### Planification
| Module | Contenu |
|---|---|
| **Portefeuille** | Vue consolidée multi-projets : indice de santé, budgets, alertes, duplication de projet |
| **Fiche projet** | Identification, ancrage institutionnel, théorie du changement, alignement stratégique (ODD, stratégies nationales) |
| **Cadre logique** | Arborescence Impact → Effets → Produits → Activités, sources de vérification, hypothèses, responsables |
| **Zones d'intervention** | Découpage géographique hiérarchisé, population, cible de bénéficiaires, coordonnées, responsable de zone |
| **Chronogramme** | Diagramme de Gantt interactif, jalons, dépendances, détection automatique des retards |
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
| **Indicateurs** | Fiche métadonnée complète (définition, formule, désagrégations, référence, cible, règle d'agrégation, fréquence, source, méthode, responsable, coût) |
| **Équité et désagrégation** | Ventilation consolidée par catégorie, **indice d'équité de genre**, écart à la parité, part des femmes par indicateur et par zone, détection des désagrégations manquantes |
| **Qualité des indicateurs** | Diagnostic **SMART** critère par critère (contrôle automatique + revue manuelle), score du système, actions correctrices recommandées |
| **Risques & hypothèses** | Registre coté probabilité × impact, matrice 5×5, risque résiduel, plans de contingence, suivi de validation des hypothèses |
| **Tableaux de bord** | KPI, indice de santé pondéré, équité, couverture territoriale, qualité SMART, graphiques SVG, alertes priorisées, actualisation automatique |

### Rapportage
| Module | Contenu |
|---|---|
| **Rapports périodiques** | Génération des rapports **trimestriels, semestriels et annuels** avec aperçu à l'écran avant production |
| **Livrables** | 22 documents Word / Excel / ZIP produits à la demande |
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
│   ├── models.py             16 entités : projets, cadre logique, indicateurs, cibles,
│   │                         réalisations (désagrégées et localisées), zones, risques,
│   │                         hypothèses, activités, budget, formulaires, questions,
│   │                         réponses, utilisateurs, audit
│   ├── security.py           PBKDF2 + jetons signés HMAC (bibliothèque standard uniquement)
│   ├── crud.py               Fabrique de routeurs CRUD génériques et (dé)sérialisation
│   ├── seed.py               Compte administrateur et projet de démonstration complet
│   ├── routers/              auth · projects · entities · imports · exports · powerbi
│   └── services/
│       ├── analytics.py      Moteur de performance, règles d'agrégation, équité de genre,
│       │                     consolidation par zone et par activité, qualité SMART,
│       │                     analyses périodées, alertes, portefeuille
│       ├── excel_export.py   12 classeurs Excel mis en forme (XlsxWriter)
│       ├── word_export.py    8 documents Word (python-docx)
│       ├── xlsform.py        Génération XLSForm KoboToolbox / ODK
│       └── importer.py       Analyseurs Excel et Word tolérants
├── static/                   Interface web-mobile : HTML + CSS + JavaScript natif,
│   │                         aucune dépendance externe, aucune étape de build
│   ├── index.html
│   ├── css/app.css
│   └── js/ core.js · charts.js · views.js · app.js
├── requirements.txt
├── render.yaml               Blueprint de déploiement Render (service web + base PostgreSQL)
└── docs/                     Documentation fonctionnelle et technique (Word)
```

**Choix structurants**

- **Zéro dépendance front-end** : les graphiques (anneau, barres, courbes, jauge, Gantt, matrice
  de risques) sont produits en SVG par `charts.js`. Aucun CDN, aucun `npm install`, aucun bundler :
  le déploiement se réduit à `pip install -r requirements.txt`.
- **Authentification sans dépendance** : hachage PBKDF2-SHA256 (180 000 itérations) et jetons
  signés HMAC-SHA256 issus de la bibliothèque standard — pas de `passlib`, `bcrypt` ni `python-jose`
  à compiler.
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

**Compte de démonstration** : `admin@sepia.org` / `sepia2024`

Au premier démarrage, la base est créée et un projet de démonstration complet est chargé
(PADRA-2025 : 14 résultats, 14 indicateurs, 26 cibles, 20 réalisations, 14 activités,
18 lignes budgétaires, 8 risques, 6 hypothèses, 2 instruments de collecte).

### Variables d'environnement

| Variable | Rôle | Défaut |
|---|---|---|
| `DATABASE_URL` | Chaîne de connexion PostgreSQL | SQLite local `data/sepia.db` |
| `SEPIA_SECRET_KEY` | Clé de signature des jetons | valeur de développement |
| `SEPIA_ADMIN_EMAIL` | Compte administrateur initial | `admin@sepia.org` |
| `SEPIA_ADMIN_PASSWORD` | Mot de passe initial | `sepia2024` |
| `SEPIA_TOKEN_TTL` | Durée de validité des jetons (secondes) | `43200` (12 h) |
| `SEPIA_SEED_DEMO` | Charger le projet de démonstration (`0` pour désactiver) | `1` |
| `SEPIA_CORS_ORIGINS` | Origines autorisées, séparées par des virgules | `*` |

---

## 4. Livrables générés

| Livrable | Format | Contenu |
|---|---|---|
| Cadre logique | Excel + Word | Matrice complète, annexe des hypothèses critiques |
| Cadre de rendement | Excel + Word | PMF : taux de période, progression finale, statuts, sources, coûts |
| Cadre de suivi des indicateurs (IPTT) | Excel | Cibles/réalisations par période, mise en forme conditionnelle |
| Chronogramme | Excel | Gantt mensuel coloré selon l'état d'avancement |
| PTBA | Excel | Budget détaillé, ventilation trimestrielle, synthèse graphique |
| Registre des risques | Excel + Word | Registre coté, matrice 5×5, plans de contingence |
| Fiches métadonnées des indicateurs | Word | Une fiche par indicateur avec séries périodiques |
| **Plan et manuel de suivi-évaluation** | Word | Document maître en 15 chapitres, alimenté par les données du projet |
| Rapport de performance | Word | Résumé exécutif, indicateurs, alertes, mesures correctrices |
| **Rapport trimestriel / semestriel / annuel** | Word | Rapport périodé en 8 parties : résumé exécutif, performance de la période, analyse d'équité, consolidation par zone, exécution physique et financière, difficultés et mesures correctrices, qualité du dispositif, bloc de validation |
| **Analyse d'équité et données désagrégées** | Excel | Ventilation par catégorie, indice d'équité de genre, détail indicateur × modalité, graphique de répartition |
| **Consolidation par zone d'intervention** | Excel | Bénéficiaires et indicateurs par zone, taux de couverture, collecte par activité, graphique atteints/cible |
| **Revue qualité SMART** | Excel | Diagnostic critère par critère, score du système, actions correctrices |
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
POST   /api/auth/login                     Authentification (OAuth2 password flow)
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
POST   /api/imports/excel/{id}             Import d'un classeur
POST   /api/imports/word/analyser          Analyse d'un document Word
POST   /api/imports/kobo/{form_id}         Réinjection de données collectées
GET    /api/exports/{id}/{livrable}        Téléchargement d'un livrable
GET    /api/exports/{id}/dossier-complet   Archive ZIP de tous les livrables
GET    /api/powerbi/{id}/dataset?token=…   Flux Power BI
GET    /api/sante                          Sonde de disponibilité
```

---

## 8. Sécurité et exploitation

- Modifier `SEPIA_ADMIN_PASSWORD` et `SEPIA_SECRET_KEY` avant toute mise en production.
- Restreindre `SEPIA_CORS_ORIGINS` au domaine de l'application.
- Les jetons Power BI portent les droits de l'utilisateur qui les a générés : ils ne doivent pas
  être partagés.
- Toutes les créations, modifications et suppressions sont tracées dans le journal d'audit,
  consultable depuis la vue Administration.
- Sauvegarder régulièrement la base PostgreSQL (Render propose des sauvegardes automatiques sur
  les plans payants).

---

## 9. Licence et crédits

Développé pour la gestion des projets et programmes de développement.
Méthodologie conforme à l'approche du cadre logique (LFA), à la gestion axée sur les résultats
(GAR) et aux critères d'évaluation du CAD de l'OCDE (pertinence, cohérence, efficacité,
efficience, impact, durabilité).
