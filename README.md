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
| **Chronogramme** | Diagramme de Gantt interactif, jalons, dépendances, détection automatique des retards |
| **PTBA / budget** | Lignes budgétaires détaillées, ventilation trimestrielle, engagements et décaissements |

### Suivi-évaluation
| Module | Contenu |
|---|---|
| **Indicateurs** | Fiche métadonnée complète (définition, formule, désagrégations, référence, cible, fréquence, source, méthode, responsable, coût, test SMART) |
| **Cadre de suivi (IPTT)** | Grille cibles/réalisations par période avec **saisie directe en ligne** |
| **Cadre de rendement** | Performance Measurement Framework avec taux calculés et statuts colorés |
| **Risques & hypothèses** | Registre coté probabilité × impact, matrice 5×5, risque résiduel, plans de contingence, suivi de validation des hypothèses |
| **Collecte** | Concepteur de questionnaires (sections, types, modalités, contraintes, logique de saut, calculs), export Word et XLSForm |
| **Tableaux de bord** | KPI, indice de santé pondéré, graphiques SVG, alertes priorisées |

### Méthodologie de calcul de la performance

Deux taux sont produits pour chaque indicateur, conformément à la gestion axée sur les résultats :

- **Taux de la période** — `réalisé ÷ cible de la même période` : c'est lui qui détermine le statut
  de performance, car comparer une réalisation intermédiaire à la cible de fin de projet
  fausserait le diagnostic ;
- **Progression vers la cible finale** — `(réalisé − référence) ÷ (cible − référence) × 100`.

Les indicateurs à progression décroissante (taux de pauvreté, pertes post-récolte…) sont traités
symétriquement. Statuts : **Atteint** ≥ 100 %, **En bonne voie** ≥ 85 %, **À surveiller** ≥ 60 %,
**Critique** < 60 %.

L'**indice de santé du projet** est une moyenne pondérée : résultats 45 %, exécution physique 30 %,
exécution financière 25 %, comparée au pourcentage de temps écoulé.

### Import / export

- **Import Excel** : reconnaissance souple des onglets et des intitulés de colonnes
  (Cadre logique, Indicateurs, Cibles, Réalisations, Activités, Budget, Risques, Hypothèses).
  Un modèle prérempli et commenté est téléchargeable depuis l'application.
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
│   ├── models.py             15 entités : projets, cadre logique, indicateurs, cibles,
│   │                         réalisations, risques, hypothèses, activités, budget,
│   │                         formulaires, questions, réponses, utilisateurs, audit
│   ├── security.py           PBKDF2 + jetons signés HMAC (bibliothèque standard uniquement)
│   ├── crud.py               Fabrique de routeurs CRUD génériques et (dé)sérialisation
│   ├── seed.py               Compte administrateur et projet de démonstration complet
│   ├── routers/              auth · projects · entities · imports · exports · powerbi
│   └── services/
│       ├── analytics.py      Moteur de performance, agrégations, alertes, portefeuille
│       ├── excel_export.py   9 classeurs Excel mis en forme (XlsxWriter)
│       ├── word_export.py    7 documents Word (python-docx)
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
| Tableau de bord | Excel | KPI, graphiques natifs Excel, alertes, détail des indicateurs |
| Jeu de données Power BI | Excel | Modèle en étoile + dimension calendrier + notice DAX |
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

Tables exposées : `Dim_Projet`, `Dim_Resultat`, `Dim_Indicateur`, `Dim_Calendrier`,
`Fait_Cible`, `Fait_Realisation`, `Fait_Activite`, `Fait_Budget`, `Fait_Risque`.

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
POST   /api/indicators/{id}/saisie         Saisie d'une réalisation
POST   /api/projects/{id}/periodes         Génération automatique des cibles périodiques
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
