/* SEPIA — définition des vues fonctionnelles de la plateforme. */
(function (global) {
  'use strict';

  const S = global.SEPIA;
  const G = global.Graphiques;
  const ech = S.echapper;

  function projet() { return S.Etat.projetActif; }
  function ref(cle) { return S.Etat.referentiels[cle] || []; }

  function badgeNiveau(niveau) {
    if (!niveau) return '';
    return '<span class="badge-niveau niveau-' + ech(niveau) + '">' + ech(niveau) + '</span>';
  }

  function etiquetteStatut(statut) {
    return '<span class="etiquette" style="background:' + S.couleurStatut(statut) + '">' +
      ech(statut) + '</span>';
  }

  function barreProgression(valeur, couleur) {
    const v = Math.max(0, Math.min(valeur || 0, 100));
    return '<div class="barre-progression"><span style="width:' + v + '%;background:' +
      (couleur || '#2E75B6') + '"></span></div>' +
      '<div style="font-size:.7rem;color:#5F6368;margin-top:2px">' + S.nombre(valeur || 0, 0) + ' %</div>';
  }

  function exigeProjet() {
    return S.vide('Sélectionnez d\'abord un projet dans le menu latéral, ou créez-en un depuis la vue Portefeuille.', '📁');
  }

  /* =================================================================== */
  /* 1. Tableau de bord                                                   */
  /* =================================================================== */
  const tableauDeBord = {
    titre: 'Tableau de bord',
    sousTitre: 'Pilotage de la performance du projet',
    actions: () => '<button class="btn btn-secondaire btn-petit" data-barre="imprimer">🖨️ Imprimer</button>' +
      '<button class="btn btn-primaire btn-petit" data-barre="tdb-excel">⬇️ Tableau de bord Excel</button>',
    gestionnairesBarre: {
      imprimer: () => window.print(),
      'tdb-excel': () => S.API.telecharger('/api/exports/' + projet() + '/tableau-de-bord-excel')
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/dashboard/' + projet());
      const sante = d.sante_globale;
      const devise = d.projet.currency || 'FCFA';

      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Santé globale du projet', S.nombre(sante.score, 1) + ' %', sante.statut, sante.couleur) +
        S.kpi('Indicateurs suivis', d.indicateurs.total,
          d.indicateurs.renseignes + ' renseignés (' + S.nombre(d.indicateurs.taux_couverture, 0) + ' %)') +
        S.kpi('Taux moyen de réalisation',
          d.indicateurs.taux_moyen === null ? '—' : S.nombre(d.indicateurs.taux_moyen, 1) + ' %',
          'Sur les indicateurs renseignés') +
        S.kpi('Avancement physique', S.nombre(d.activites.avancement_moyen, 1) + ' %',
          d.activites.achevees + ' / ' + d.activites.total + ' activités achevées', '#0F9D58') +
        S.kpi('Exécution budgétaire', S.nombre(d.budget.taux_execution, 1) + ' %',
          S.nombre(d.budget.decaisse, 0) + ' ' + devise + ' décaissés', '#EA8600') +
        S.kpi('Risques critiques', d.risques.critiques,
          d.risques.total + ' risques recensés, ' + d.risques.ouverts + ' ouverts',
          d.risques.critiques ? '#D93025' : '#0F9D58') +
        '</div>';

      html += '<div class="grille grille-2">';
      html += S.carte('Indice de santé du projet',
        G.jauge(sante.score, { libelle: 'Moyenne pondérée : résultats 45 %, exécution physique 30 %, exécution financière 25 %' }) +
        '<div class="tableau-conteneur"><table class="tableau" style="min-width:auto">' +
        '<thead><tr><th>Composante</th><th class="centre">Valeur</th><th class="centre">Poids</th></tr></thead><tbody>' +
        sante.composantes.map((c) => '<tr><td>' + ech(c.libelle) + '</td><td class="centre">' +
          S.nombre(c.valeur, 1) + ' %</td><td class="centre">' + S.nombre(c.poids * 100, 0) +
          ' %</td></tr>').join('') +
        (d.temps.taux_temps !== null ? '<tr><td><strong>Temps écoulé</strong></td><td class="centre">' +
          S.nombre(d.temps.taux_temps, 1) + ' %</td><td class="centre">—</td></tr>' : '') +
        '</tbody></table></div>' +
        (sante.ecart_calendrier !== null && sante.ecart_calendrier !== undefined ?
          '<p style="margin-top:.6rem;font-size:.8rem;color:' +
          (sante.ecart_calendrier >= -5 ? '#0F9D58' : '#D93025') + '">Écart performance / calendrier : ' +
          (sante.ecart_calendrier > 0 ? '+' : '') + S.nombre(sante.ecart_calendrier, 1) + ' points</p>' : ''));

      const parStatut = Object.keys(d.indicateurs.par_statut).map((statut) => ({
        libelle: statut, valeur: d.indicateurs.par_statut[statut], couleur: S.couleurStatut(statut)
      }));
      html += S.carte('Répartition des indicateurs par statut',
        G.anneau(parStatut, { centre: d.indicateurs.total, legendeCentre: 'indicateurs' }));
      html += '</div>';

      const niveaux = Object.keys(d.indicateurs.par_niveau);
      if (niveaux.length) {
        html += S.carte('Performance moyenne par niveau de résultat',
          G.barres(niveaux.map((niveau) => ({
            libelle: niveau, valeur: d.indicateurs.par_niveau[niveau].taux_moyen || 0,
            etiquette: (d.indicateurs.par_niveau[niveau].taux_moyen === null ? '—' :
              S.nombre(d.indicateurs.par_niveau[niveau].taux_moyen, 1) + ' %'),
            couleur: { IMPACT: '#1F4E79', EFFET: '#2E75B6', PRODUIT: '#5B9BD5', ACTIVITE: '#9DC3E6' }[niveau]
          })), { max: 100, largeurLibelle: 110 }));
      }

      html += '<div class="grille grille-2">';
      html += S.carte('Programmation budgétaire trimestrielle',
        G.colonnes(Object.keys(d.budget.par_trimestre),
          [{ nom: 'Budget planifié (' + devise + ')', valeurs: Object.values(d.budget.par_trimestre), couleur: '#2E75B6' }]));
      html += S.carte('Exécution financière',
        G.barres([
          { libelle: 'Planifié', valeur: d.budget.planifie, etiquette: S.nombre(d.budget.planifie, 0), couleur: '#5B9BD5' },
          { libelle: 'Engagé', valeur: d.budget.engage, etiquette: S.nombre(d.budget.engage, 0), couleur: '#F9A825' },
          { libelle: 'Décaissé', valeur: d.budget.decaisse, etiquette: S.nombre(d.budget.decaisse, 0), couleur: '#0F9D58' }
        ], { max: d.budget.planifie || 1, largeurLibelle: 100 }) +
        '<p style="font-size:.78rem;color:#5F6368;margin-top:.6rem">Taux d\'engagement : ' +
        S.nombre(d.budget.taux_engagement, 1) + ' % — Solde disponible : ' +
        S.nombre(d.budget.solde, 0) + ' ' + devise + '</p>');
      html += '</div>';

      const alertes = d.alertes.length ? d.alertes.slice(0, 20).map((a) =>
        '<div class="alerte alerte-' + a.niveau + '"><span class="type">' + ech(a.type) + '</span>' +
        '<span>' + ech(a.message) + '</span></div>').join('') :
        '<div class="alerte alerte-info"><span>✅ Aucune alerte : le projet ne présente pas d\'écart critique.</span></div>';
      html += S.carte('Alertes et points de vigilance (' + d.alertes.length + ')', alertes);

      html += S.carte('Indicateurs clés de performance',
        S.tableau([
          { cle: 'code', titre: 'Code' },
          { cle: 'name', titre: 'Indicateur' },
          { titre: 'Niveau', classe: 'centre', rendu: (l) => badgeNiveau(l.level) },
          { titre: 'Référence', classe: 'nombre', rendu: (l) => S.nombre(l.baseline_value, 2) },
          { titre: 'Cible finale', classe: 'nombre', rendu: (l) => S.nombre(l.target_value, 2) },
          { titre: 'Période', classe: 'centre', rendu: (l) => ech(l.period_label || '—') },
          { titre: 'Cible période', classe: 'nombre', rendu: (l) => S.nombre(l.period_target, 2) },
          { titre: 'Réalisé', classe: 'nombre', rendu: (l) => S.nombre(l.actual_value, 2) },
          { titre: 'Taux', classe: 'centre', rendu: (l) => l.taux === null ? '—' : S.nombre(l.taux, 1) + ' %' },
          { titre: 'Progr. finale', classe: 'centre', rendu: (l) => l.taux_final === null ? '—' : S.nombre(l.taux_final, 1) + ' %' },
          { titre: 'Statut', classe: 'centre', rendu: (l) => etiquetteStatut(l.statut) }
        ], d.indicateurs.lignes.filter((l) => l.is_key),
        null) +
        '<p style="font-size:.74rem;color:#5F6368;margin-top:.5rem">Le taux mesure l\'atteinte du jalon de la période évaluée ; la progression finale indique le chemin parcouru depuis la référence vers la cible de fin de projet.</p>');

      conteneur.innerHTML = html;
    }
  };

  /* =================================================================== */
  /* 2. Portefeuille                                                      */
  /* =================================================================== */
  const CHAMPS_PROJET = [
    { nom: 'code', libelle: 'Code du projet', obligatoire: true, largeur: 'courte', section: 'Identification' },
    { nom: 'acronym', libelle: 'Acronyme', largeur: 'courte', section: 'Identification' },
    { nom: 'title', libelle: 'Intitulé complet', obligatoire: true, section: 'Identification' },
    { nom: 'description', libelle: 'Description', type: 'textarea', lignes: 4, section: 'Identification' },
    { nom: 'sector', libelle: 'Secteur', largeur: 'courte', section: 'Ancrage institutionnel' },
    { nom: 'sub_sector', libelle: 'Sous-secteur', largeur: 'courte', section: 'Ancrage institutionnel' },
    { nom: 'country', libelle: 'Pays', largeur: 'courte', section: 'Ancrage institutionnel' },
    { nom: 'donor', libelle: 'Bailleur / partenaire financier', largeur: 'courte', section: 'Ancrage institutionnel' },
    { nom: 'executing_agency', libelle: 'Agence d\'exécution', largeur: 'courte', section: 'Ancrage institutionnel' },
    { nom: 'supervising_ministry', libelle: 'Ministère de tutelle', largeur: 'courte', section: 'Ancrage institutionnel' },
    { nom: 'beneficiaries', libelle: 'Bénéficiaires', type: 'textarea', lignes: 2, section: 'Ancrage institutionnel' },
    { nom: 'target_population', libelle: 'Population cible (effectif)', type: 'number', largeur: 'courte', section: 'Ancrage institutionnel' },
    { nom: 'start_date', libelle: 'Date de démarrage', type: 'date', largeur: 'courte', section: 'Cycle de vie et finances' },
    { nom: 'end_date', libelle: 'Date de clôture', type: 'date', largeur: 'courte', section: 'Cycle de vie et finances' },
    { nom: 'status', libelle: 'Statut', type: 'select', options: [], largeur: 'courte', section: 'Cycle de vie et finances' },
    { nom: 'currency', libelle: 'Devise', largeur: 'courte', section: 'Cycle de vie et finances' },
    { nom: 'total_budget', libelle: 'Budget total', type: 'number', largeur: 'courte', section: 'Cycle de vie et finances' },
    { nom: 'counterpart_budget', libelle: 'Contrepartie nationale', type: 'number', largeur: 'courte', section: 'Cycle de vie et finances' },
    { nom: 'theory_of_change', libelle: 'Théorie du changement', type: 'textarea', lignes: 5, section: 'Cadrage stratégique' },
    { nom: 'me_approach', libelle: 'Approche de suivi-évaluation retenue', type: 'textarea', lignes: 5, section: 'Cadrage stratégique' }
  ];

  function champsProjet() {
    return CHAMPS_PROJET.map(function (champ) {
      if (champ.nom === 'status') return Object.assign({}, champ, { options: ref('statuts_projet') });
      return champ;
    });
  }

  const portefeuille = {
    titre: 'Portefeuille de projets',
    sousTitre: 'Vue consolidée de l\'ensemble des projets et programmes',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="nouveau">➕ Nouveau projet</button>',
    gestionnairesBarre: {
      nouveau: function () {
        S.formulaireModal('Créer un projet', champsProjet(), { country: 'Togo', currency: 'FCFA', status: 'En cours' },
          async function (donnees) {
            const cree = await S.API.post('/api/projects', donnees);
            S.notifier('Projet « ' + cree.code + ' » créé.', 'succes');
            await global.Application.rechargerProjets(cree.id);
            global.Application.naviguer('projet');
          }, true);
      }
    },
    rendre: async function (conteneur) {
      const d = await S.API.get('/api/portefeuille');
      const c = d.consolidation;
      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Projets suivis', c.nb_projets, 'Portefeuille consolidé') +
        S.kpi('Budget cumulé', S.nombre(c.budget_total, 0), 'Toutes devises confondues') +
        S.kpi('Santé moyenne', S.nombre(c.sante_moyenne, 1) + ' %', 'Indice pondéré',
          S.couleurStatut(c.sante_moyenne >= 85 ? 'En bonne voie' : c.sante_moyenne >= 60 ? 'À surveiller' : 'Critique')) +
        S.kpi('Risques critiques', c.nb_risques_critiques, 'Tous projets', c.nb_risques_critiques ? '#D93025' : '#0F9D58') +
        S.kpi('Alertes actives', c.nb_alertes, 'À traiter', '#EA8600') +
        '</div>';

      if (d.projets.length) {
        html += S.carte('Indice de santé par projet',
          G.barres(d.projets.map((p) => ({
            libelle: p.acronym || p.code, valeur: p.sante,
            etiquette: S.nombre(p.sante, 1) + ' %', couleur: p.couleur
          })), { max: 100, largeurLibelle: 130 }));
      }

      html += S.carte('Détail du portefeuille', S.tableau([
        { cle: 'code', titre: 'Code' },
        { titre: 'Projet', rendu: (l) => '<strong>' + ech(l.acronym || '') + '</strong> ' + ech(l.title) },
        { cle: 'donor', titre: 'Bailleur' },
        { cle: 'status', titre: 'Statut', classe: 'centre' },
        { titre: 'Budget', classe: 'nombre', rendu: (l) => S.nombre(l.total_budget, 0) + ' ' + ech(l.currency || '') },
        { titre: 'Indicateurs', classe: 'centre', rendu: (l) => l.nb_indicateurs },
        { titre: 'Taux indic.', classe: 'centre', rendu: (l) => l.taux_indicateurs === null ? '—' : S.nombre(l.taux_indicateurs, 1) + ' %' },
        { titre: 'Avancement', classe: 'centre', rendu: (l) => barreProgression(l.avancement) },
        { titre: 'Exéc. budget', classe: 'centre', rendu: (l) => S.nombre(l.taux_execution, 1) + ' %' },
        { titre: 'Santé', classe: 'centre', rendu: (l) => '<span class="etiquette" style="background:' + l.couleur + '">' + S.nombre(l.sante, 0) + ' %</span>' }
      ], d.projets, [
        { cle: 'ouvrir', libelle: '📂', titre: 'Ouvrir ce projet', classe: 'btn-primaire' },
        { cle: 'dupliquer', libelle: '📋', titre: 'Dupliquer la structure' },
        { cle: 'supprimer', libelle: '🗑️', titre: 'Supprimer', classe: 'btn-danger' }
      ]));
      conteneur.innerHTML = html;

      S.brancherActions(conteneur, {
        ouvrir: function (id) {
          global.Application.changerProjet(id);
          global.Application.naviguer('tableau-de-bord');
        },
        dupliquer: function (id) {
          const source = d.projets.find((p) => p.id === id);
          S.formulaireModal('Dupliquer le projet', [
            { nom: 'code', libelle: 'Code du nouveau projet', obligatoire: true },
            { nom: 'title', libelle: 'Intitulé du nouveau projet', obligatoire: true }
          ], { code: source.code + '-V2', title: source.title + ' (phase 2)' }, async function (donnees) {
            const cree = await S.API.post('/api/projects/' + id + '/dupliquer', donnees);
            S.notifier('Projet dupliqué : ' + cree.code, 'succes');
            await global.Application.rechargerProjets(cree.id);
            global.Application.rafraichir();
          });
        },
        supprimer: function (id) {
          const cible = d.projets.find((p) => p.id === id);
          S.confirmer('Supprimer définitivement le projet « ' + cible.code +
            ' » et toutes ses données (cadre logique, indicateurs, budget, risques) ?', async function () {
            await S.API.supprimer('/api/projects/' + id);
            S.notifier('Projet supprimé.', 'succes');
            await global.Application.rechargerProjets();
            global.Application.rafraichir();
          });
        }
      });
    }
  };

  /* =================================================================== */
  /* 3. Fiche projet                                                      */
  /* =================================================================== */
  const ficheProjet = {
    titre: 'Fiche du projet',
    sousTitre: 'Identification, ancrage institutionnel et cadrage stratégique',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="modifier">✏️ Modifier</button>',
    gestionnairesBarre: {
      modifier: async function () {
        const p = await S.API.get('/api/projects/' + projet());
        S.formulaireModal('Modifier le projet', champsProjet(), p, async function (donnees) {
          await S.API.put('/api/projects/' + projet(), donnees);
          S.notifier('Projet mis à jour.', 'succes');
          await global.Application.rechargerProjets(projet());
          global.Application.rafraichir();
        }, true);
      }
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const p = await S.API.get('/api/projects/' + projet());
      const rubriques = [
        ['Code', p.code], ['Intitulé', p.title], ['Acronyme', p.acronym],
        ['Secteur', p.sector], ['Sous-secteur', p.sub_sector], ['Pays', p.country],
        ['Zones d\'intervention', (p.regions || []).join(', ')],
        ['Bailleur / PTF', p.donor], ['Agence d\'exécution', p.executing_agency],
        ['Ministère de tutelle', p.supervising_ministry],
        ['Bénéficiaires', p.beneficiaries],
        ['Population cible', S.nombre(p.target_population, 0)],
        ['Période d\'exécution', S.dateFr(p.start_date) + ' → ' + S.dateFr(p.end_date)],
        ['Statut', p.status],
        ['Budget total', S.nombre(p.total_budget, 0) + ' ' + (p.currency || '')],
        ['Contrepartie nationale', S.nombre(p.counterpart_budget, 0) + ' ' + (p.currency || '')]
      ];
      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Résultats du cadre logique', p.compteurs.resultats, 'Impact, effets, produits, activités') +
        S.kpi('Indicateurs', p.compteurs.indicateurs, 'Paramétrés') +
        S.kpi('Activités', p.compteurs.activites, 'Au chronogramme') +
        S.kpi('Risques', p.compteurs.risques, p.compteurs.hypotheses + ' hypothèses suivies') +
        S.kpi('Lignes budgétaires', p.compteurs.lignes_budgetaires, 'PTBA') +
        S.kpi('Instruments de collecte', p.compteurs.formulaires, 'Fiches et questionnaires') +
        '</div>';

      html += S.carte('Identification', '<div class="tableau-conteneur"><table class="tableau">' +
        '<tbody>' + rubriques.map((r) => '<tr><td style="width:34%;background:#F7F8FA"><strong>' +
        ech(r[0]) + '</strong></td><td>' + ech(r[1] || '—') + '</td></tr>').join('') +
        '</tbody></table></div>');

      if (p.description) html += S.carte('Description', '<p>' + ech(p.description) + '</p>');
      if (p.theory_of_change) html += S.carte('Théorie du changement', '<p>' + ech(p.theory_of_change) + '</p>');
      if (p.me_approach) html += S.carte('Approche de suivi-évaluation', '<p>' + ech(p.me_approach) + '</p>');
      if (p.strategic_alignment && Object.keys(p.strategic_alignment).length) {
        html += S.carte('Alignement stratégique', '<ul>' + Object.keys(p.strategic_alignment)
          .map((cle) => '<li><strong>' + ech(cle) + '</strong> — ' + ech(p.strategic_alignment[cle]) + '</li>')
          .join('') + '</ul>');
      }
      conteneur.innerHTML = html;
    }
  };

  /* =================================================================== */
  /* 4. Cadre logique                                                     */
  /* =================================================================== */
  function champsResultat() {
    return [
      { nom: 'level', libelle: 'Niveau du cadre logique', type: 'select', obligatoire: true,
        options: ref('niveaux').map((n) => ({ valeur: n.code, libelle: n.libelle })), largeur: 'courte' },
      { nom: 'code', libelle: 'Code (ex. OS1, P1.2)', largeur: 'courte' },
      { nom: 'statement', libelle: 'Énoncé du résultat', type: 'textarea', lignes: 3, obligatoire: true },
      { nom: 'description', libelle: 'Précisions', type: 'textarea', lignes: 2 },
      { nom: 'means_of_verification', libelle: 'Sources de vérification', type: 'textarea', lignes: 2 },
      { nom: 'assumptions', libelle: 'Hypothèses critiques associées', type: 'textarea', lignes: 2 },
      { nom: 'responsible', libelle: 'Responsable', largeur: 'courte' },
      { nom: 'order_index', libelle: 'Ordre d\'affichage', type: 'number', largeur: 'courte' }
    ];
  }

  const cadreLogique = {
    titre: 'Cadre logique',
    sousTitre: 'Chaîne de résultats, indicateurs, sources de vérification et hypothèses',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Résultat</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="excel">⬇️ Excel</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="word">⬇️ Word</button>',
    gestionnairesBarre: {
      ajouter: () => cadreLogique.ouvrirFormulaire(null, null),
      excel: () => S.API.telecharger('/api/exports/' + projet() + '/cadre-logique-excel'),
      word: () => S.API.telecharger('/api/exports/' + projet() + '/cadre-logique-word')
    },
    ouvrirFormulaire: function (element, parentId) {
      const champs = champsResultat();
      const valeurs = element || { level: parentId ? 'PRODUIT' : 'IMPACT' };
      S.formulaireModal(element ? 'Modifier le résultat' : 'Nouveau résultat', champs, valeurs,
        async function (donnees) {
          donnees.project_id = projet();
          if (parentId) donnees.parent_id = parentId;
          if (element) await S.API.put('/api/logframe/' + element.id, donnees);
          else await S.API.post('/api/logframe', donnees);
          S.notifier('Cadre logique mis à jour.', 'succes');
          global.Application.rafraichir();
        });
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/logframe/tree/' + projet());
      if (!d.total) {
        conteneur.innerHTML = S.carte('Cadre logique',
          S.vide('Aucun résultat n\'est encore défini. Créez-les un à un, ou importez un cadre logique existant depuis un fichier Excel ou Word (menu « Importer »).', '🗂️'));
        return;
      }

      function rendreNoeud(noeud, profondeur) {
        const indicateurs = (noeud.indicateurs || []).map(function (i) {
          return '<div class="arbre-indicateur"><strong>' + ech(i.code || '') + '</strong>' +
            '<span style="flex:1;min-width:160px">' + ech(i.name) + '</span>' +
            '<span style="color:#5F6368">Réf. ' + S.nombre(i.baseline_value, 2) + ' → Cible ' +
            S.nombre(i.target_value, 2) + ' ' + ech(i.unit || '') + '</span>' +
            (i.taux !== null ? etiquetteStatut(i.statut) + '<span>' + S.nombre(i.taux, 1) + ' %</span>' :
              '<span class="etiquette pale">Non renseigné</span>') + '</div>';
        }).join('');
        return '<div class="arbre-noeud" style="border-left-color:' +
          ({ IMPACT: '#1F4E79', EFFET: '#2E75B6', PRODUIT: '#5B9BD5', ACTIVITE: '#9DC3E6' }[noeud.level] || '#E4E8EE') + '">' +
          '<div class="arbre-carte">' +
          '<div class="entete">' + badgeNiveau(noeud.level) +
          '<strong style="color:#1F4E79">' + ech(noeud.code || '') + '</strong>' +
          '<div class="enonce">' + ech(noeud.statement) + '</div>' +
          '<div style="display:flex;gap:.25rem">' +
          '<button class="btn btn-petit btn-secondaire" data-action="ajouter-enfant" data-id="' + noeud.id + '" title="Ajouter un résultat de niveau inférieur">➕</button>' +
          '<button class="btn btn-petit btn-secondaire" data-action="indicateur" data-id="' + noeud.id + '" title="Ajouter un indicateur">📊</button>' +
          '<button class="btn btn-petit btn-secondaire" data-action="modifier" data-id="' + noeud.id + '" title="Modifier">✏️</button>' +
          '<button class="btn btn-petit btn-danger" data-action="supprimer" data-id="' + noeud.id + '" title="Supprimer">🗑️</button>' +
          '</div></div>' +
          (noeud.means_of_verification ? '<div class="meta"><strong>Sources de vérification :</strong> ' +
            ech(noeud.means_of_verification) + '</div>' : '') +
          (noeud.assumptions ? '<div class="meta"><strong>Hypothèses :</strong> ' +
            ech(noeud.assumptions) + '</div>' : '') +
          (noeud.responsible ? '<div class="meta"><strong>Responsable :</strong> ' +
            ech(noeud.responsible) + '</div>' : '') +
          indicateurs + '</div>' +
          (noeud.enfants || []).map((enfant) => rendreNoeud(enfant, profondeur + 1)).join('') +
          '</div>';
      }

      conteneur.innerHTML = S.carte('Chaîne de résultats (' + d.total + ' éléments)',
        d.racines.map((noeud) => rendreNoeud(noeud, 0)).join('') +
        (d.orphelins.length ? '<p style="font-size:.78rem;color:#EA8600;margin-top:.8rem">⚠️ ' +
          d.orphelins.length + ' élément(s) rattaché(s) à un parent supprimé.</p>' : ''));

      S.brancherActions(conteneur, {
        'ajouter-enfant': (id) => cadreLogique.ouvrirFormulaire(null, id),
        modifier: async function (id) {
          cadreLogique.ouvrirFormulaire(await S.API.get('/api/logframe/' + id), null);
        },
        indicateur: (id) => indicateurs.ouvrirFormulaire(null, id),
        supprimer: function (id) {
          S.confirmer('Supprimer ce résultat ? Les éléments rattachés perdront leur parent.',
            async function () {
              await S.API.supprimer('/api/logframe/' + id);
              S.notifier('Résultat supprimé.', 'succes');
              global.Application.rafraichir();
            });
        }
      });
    }
  };

  /* =================================================================== */
  /* 5. Indicateurs                                                       */
  /* =================================================================== */
  function champsIndicateur(elements) {
    return [
      { nom: 'code', libelle: 'Code', largeur: 'courte', section: 'Identification' },
      { nom: 'level', libelle: 'Niveau', type: 'select', largeur: 'courte', section: 'Identification',
        options: ref('niveaux').map((n) => ({ valeur: n.code, libelle: n.libelle })) },
      { nom: 'name', libelle: 'Libellé de l\'indicateur', obligatoire: true, section: 'Identification' },
      { nom: 'element_id', libelle: 'Résultat rattaché', type: 'select', section: 'Identification',
        options: (elements || []).map((e) => ({ valeur: e.id, libelle: (e.code || '') + ' — ' + e.statement.substring(0, 70) })) },
      { nom: 'definition', libelle: 'Définition opérationnelle', type: 'textarea', lignes: 3, section: 'Identification' },
      { nom: 'indicator_type', libelle: 'Type', type: 'select', options: ref('types_indicateur'), largeur: 'courte', section: 'Mesure' },
      { nom: 'unit', libelle: 'Unité de mesure', type: 'select', options: ref('unites'), largeur: 'courte', section: 'Mesure' },
      { nom: 'formula', libelle: 'Mode de calcul / formule', type: 'textarea', lignes: 2, section: 'Mesure' },
      { nom: 'numerator', libelle: 'Numérateur', largeur: 'courte', section: 'Mesure' },
      { nom: 'denominator', libelle: 'Dénominateur', largeur: 'courte', section: 'Mesure' },
      { nom: 'disaggregation', libelle: 'Désagrégations exigées', type: 'multiselect', options: ref('desagregations'), section: 'Mesure' },
      { nom: 'baseline_value', libelle: 'Valeur de référence', type: 'number', largeur: 'courte', section: 'Référence et cible' },
      { nom: 'baseline_date', libelle: 'Date de référence', type: 'date', largeur: 'courte', section: 'Référence et cible' },
      { nom: 'baseline_source', libelle: 'Source de la référence', largeur: 'courte', section: 'Référence et cible' },
      { nom: 'target_value', libelle: 'Valeur cible finale', type: 'number', largeur: 'courte', section: 'Référence et cible' },
      { nom: 'target_date', libelle: 'Échéance de la cible', type: 'date', largeur: 'courte', section: 'Référence et cible' },
      { nom: 'direction', libelle: 'Sens de progression', type: 'select', options: ref('sens_progression'), largeur: 'courte', section: 'Référence et cible' },
      { nom: 'frequency', libelle: 'Fréquence de collecte', type: 'select', options: ref('frequences'), largeur: 'courte', section: 'Collecte' },
      { nom: 'data_source', libelle: 'Source de données', largeur: 'courte', section: 'Collecte' },
      { nom: 'collection_method', libelle: 'Méthode de collecte', largeur: 'courte', section: 'Collecte' },
      { nom: 'responsible', libelle: 'Responsable de la collecte', largeur: 'courte', section: 'Collecte' },
      { nom: 'reporting_level', libelle: 'Niveau de rapportage', largeur: 'courte', section: 'Collecte' },
      { nom: 'cost_estimate', libelle: 'Coût estimé de la collecte', type: 'number', largeur: 'courte', section: 'Collecte' },
      { nom: 'is_key', libelle: 'Indicateur clé', type: 'checkbox', texteCase: 'Indicateur clé de performance (KPI)', section: 'Qualité' },
      { nom: 'quality_note', libelle: 'Observations qualité', type: 'textarea', lignes: 2, section: 'Qualité' }
    ];
  }

  const indicateurs = {
    titre: 'Indicateurs',
    sousTitre: 'Paramétrage complet et fiches métadonnées',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Indicateur</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="rendement">⬇️ Cadre de rendement</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="fiches">⬇️ Fiches Word</button>',
    gestionnairesBarre: {
      ajouter: () => indicateurs.ouvrirFormulaire(null, null),
      rendement: () => S.API.telecharger('/api/exports/' + projet() + '/cadre-rendement-excel'),
      fiches: () => S.API.telecharger('/api/exports/' + projet() + '/fiches-indicateurs-word')
    },
    ouvrirFormulaire: async function (indicateur, elementId) {
      const elements = await S.API.get('/api/logframe?project_id=' + projet());
      const champs = champsIndicateur(elements);
      const valeurs = indicateur || { direction: 'Croissant', frequency: 'Trimestrielle',
        indicator_type: 'Quantitatif', unit: 'Nombre', element_id: elementId };
      if (elementId && !indicateur) {
        const parent = elements.find((e) => e.id === elementId);
        if (parent) valeurs.level = parent.level;
      }
      S.formulaireModal(indicateur ? 'Modifier l\'indicateur' : 'Nouvel indicateur', champs, valeurs,
        async function (donnees) {
          donnees.project_id = projet();
          if (indicateur) await S.API.put('/api/indicators/' + indicateur.id, donnees);
          else await S.API.post('/api/indicators', donnees);
          S.notifier('Indicateur enregistré.', 'succes');
          global.Application.rafraichir();
        }, true);
    },
    ouvrirDetail: async function (id) {
      const d = await S.API.get('/api/indicators/' + id + '/serie');
      const i = d.indicateur, p = d.performance;
      const contenu = document.createElement('div');
      contenu.innerHTML =
        '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Référence', S.nombre(i.baseline_value, 2), S.dateFr(i.baseline_date)) +
        S.kpi('Cible', S.nombre(i.target_value, 2), S.dateFr(i.target_date)) +
        S.kpi('Dernier réalisé', S.nombre(p.actual_value, 2), p.period_label || '—') +
        S.kpi('Taux de réalisation', p.taux === null ? '—' : S.nombre(p.taux, 1) + ' %', p.statut, p.couleur) +
        '</div>' +
        (d.serie.periodes.length ? G.courbes(d.serie.periodes, [
          { nom: 'Cible', valeurs: d.serie.cibles, couleur: '#EA8600', pointille: true },
          { nom: 'Réalisé', valeurs: d.serie.reels, couleur: '#0F9D58' }
        ]) : S.vide('Aucune cible périodique n\'est définie pour cet indicateur.', '📈')) +
        '<div class="barre-outils" style="margin-top:1rem">' +
        '<button class="btn btn-primaire btn-petit" data-detail="saisir">➕ Saisir une réalisation</button>' +
        '<button class="btn btn-secondaire btn-petit" data-detail="cible">🎯 Ajouter une cible</button>' +
        '<button class="btn btn-secondaire btn-petit" data-detail="generer">⚙️ Générer les cibles périodiques</button>' +
        '<button class="btn btn-secondaire btn-petit" data-detail="fiche">⬇️ Fiche Word</button>' +
        '</div>' +
        '<h4 style="margin-top:1rem">Réalisations enregistrées</h4>' +
        S.tableau([
          { cle: 'period_label', titre: 'Période' },
          { titre: 'Valeur', classe: 'nombre', rendu: (l) => S.nombre(l.value, 2) },
          { titre: 'Date', rendu: (l) => S.dateFr(l.reference_date) },
          { cle: 'source', titre: 'Source' },
          { cle: 'validation_status', titre: 'Validation', classe: 'centre' }
        ], d.realisations, [{ cle: 'suppr-reel', libelle: '🗑️', classe: 'btn-danger' }]) +
        '<h4 style="margin-top:1rem">Cibles périodiques</h4>' +
        S.tableau([
          { cle: 'period_label', titre: 'Période' },
          { titre: 'Cible', classe: 'nombre', rendu: (l) => S.nombre(l.target_value, 2) },
          { cle: 'year', titre: 'Année', classe: 'centre' }
        ], d.cibles, [{ cle: 'suppr-cible', libelle: '🗑️', classe: 'btn-danger' }]);

      S.ouvrirModale((i.code || '') + ' — ' + i.name, contenu, [
        { libelle: 'Fermer', classe: 'btn-secondaire', action: S.fermerModale }
      ], true);

      contenu.querySelectorAll('[data-detail]').forEach(function (bouton) {
        bouton.addEventListener('click', function () {
          const action = bouton.dataset.detail;
          if (action === 'fiche') { S.API.telecharger('/api/exports/indicators/' + id + '/fiche'); return; }
          if (action === 'saisir') {
            S.formulaireModal('Saisir une réalisation', [
              { nom: 'period_label', libelle: 'Période (ex. 2025-T2)', obligatoire: true, largeur: 'courte' },
              { nom: 'year', libelle: 'Année', type: 'number', largeur: 'courte' },
              { nom: 'value', libelle: 'Valeur réalisée', type: 'number', obligatoire: true, largeur: 'courte' },
              { nom: 'reference_date', libelle: 'Date de référence', type: 'date', largeur: 'courte' },
              { nom: 'source', libelle: 'Source de la donnée' },
              { nom: 'validation_status', libelle: 'Statut', type: 'select', options: ['Brouillon', 'Validé', 'Rejeté'], largeur: 'courte' },
              { nom: 'comment', libelle: 'Commentaire', type: 'textarea', lignes: 2 }
            ], { validation_status: 'Validé', reference_date: new Date().toISOString().substring(0, 10) },
              async function (donnees) {
                await S.API.post('/api/indicators/' + id + '/saisie', donnees);
                S.notifier('Réalisation enregistrée.', 'succes');
                S.fermerModale();
                indicateurs.ouvrirDetail(id);
              });
          }
          if (action === 'cible') {
            S.formulaireModal('Ajouter une cible périodique', [
              { nom: 'period_label', libelle: 'Période (ex. 2025-T2)', obligatoire: true, largeur: 'courte' },
              { nom: 'year', libelle: 'Année', type: 'number', largeur: 'courte' },
              { nom: 'target_value', libelle: 'Valeur cible', type: 'number', obligatoire: true, largeur: 'courte' }
            ], {}, async function (donnees) {
              donnees.indicator_id = id;
              await S.API.post('/api/targets', donnees);
              S.notifier('Cible ajoutée.', 'succes');
              S.fermerModale();
              indicateurs.ouvrirDetail(id);
            });
          }
          if (action === 'generer') {
            S.formulaireModal('Générer les cibles périodiques', [
              { nom: 'granularite', libelle: 'Granularité', type: 'select',
                options: [{ valeur: 'trimestre', libelle: 'Trimestrielle' },
                          { valeur: 'semestre', libelle: 'Semestrielle' },
                          { valeur: 'annee', libelle: 'Annuelle' }], largeur: 'courte' },
              { nom: 'annee_debut', libelle: 'Année de début', type: 'number', largeur: 'courte' },
              { nom: 'annee_fin', libelle: 'Année de fin', type: 'number', largeur: 'courte' },
              { nom: 'cumulatif', libelle: 'Progression', type: 'checkbox',
                texteCase: 'Cible cumulative (progression linéaire de la référence vers la cible)' }
            ], { granularite: 'trimestre', cumulatif: true }, async function (donnees) {
              donnees.indicator_id = id;
              const r = await S.API.post('/api/projects/' + projet() + '/periodes', donnees);
              S.notifier(r.periodes_creees + ' cibles générées.', 'succes');
              S.fermerModale();
              indicateurs.ouvrirDetail(id);
            });
          }
        });
      });

      S.brancherActions(contenu, {
        'suppr-reel': async function (idReel) {
          await S.API.supprimer('/api/actuals/' + idReel);
          S.notifier('Réalisation supprimée.', 'succes');
          indicateurs.ouvrirDetail(id);
        },
        'suppr-cible': async function (idCible) {
          await S.API.supprimer('/api/targets/' + idCible);
          S.notifier('Cible supprimée.', 'succes');
          indicateurs.ouvrirDetail(id);
        }
      });
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/dashboard/' + projet());
      const lignes = d.indicateurs.lignes;
      const html = '<div class="barre-outils">' +
        '<input type="search" id="recherche-indicateur" placeholder="Rechercher un indicateur…">' +
        '<select id="filtre-niveau"><option value="">Tous les niveaux</option>' +
        ref('niveaux').map((n) => '<option value="' + n.code + '">' + ech(n.libelle) + '</option>').join('') +
        '</select>' +
        '<select id="filtre-statut"><option value="">Tous les statuts</option>' +
        ['Atteint', 'En bonne voie', 'À surveiller', 'Critique', 'Non renseigné']
          .map((s) => '<option>' + s + '</option>').join('') + '</select>' +
        '<span style="font-size:.78rem;color:#5F6368">' + lignes.length + ' indicateurs — taux moyen ' +
        (d.indicateurs.taux_moyen === null ? '—' : S.nombre(d.indicateurs.taux_moyen, 1) + ' %') + '</span>' +
        '</div><div id="liste-indicateurs"></div>';
      conteneur.innerHTML = S.carte('Liste des indicateurs', html);

      function afficher() {
        const recherche = (document.getElementById('recherche-indicateur').value || '').toLowerCase();
        const niveau = document.getElementById('filtre-niveau').value;
        const statut = document.getElementById('filtre-statut').value;
        const filtrees = lignes.filter(function (l) {
          if (niveau && l.level !== niveau) return false;
          if (statut && l.statut !== statut) return false;
          if (recherche && (l.name + ' ' + (l.code || '')).toLowerCase().indexOf(recherche) < 0) return false;
          return true;
        });
        const zone = document.getElementById('liste-indicateurs');
        zone.innerHTML = S.tableau([
          { titre: 'Code', rendu: (l) => (l.is_key ? '⭐ ' : '') + ech(l.code || '') },
          { cle: 'name', titre: 'Indicateur' },
          { titre: 'Niveau', classe: 'centre', rendu: (l) => badgeNiveau(l.level) },
          { cle: 'unit', titre: 'Unité', classe: 'centre' },
          { titre: 'Référence', classe: 'nombre', rendu: (l) => S.nombre(l.baseline_value, 2) },
          { titre: 'Cible finale', classe: 'nombre', rendu: (l) => S.nombre(l.target_value, 2) },
          { titre: 'Période', classe: 'centre', rendu: (l) => ech(l.period_label || '—') },
          { titre: 'Cible période', classe: 'nombre', rendu: (l) => S.nombre(l.period_target, 2) },
          { titre: 'Réalisé', classe: 'nombre', rendu: (l) => S.nombre(l.actual_value, 2) },
          { titre: 'Taux', classe: 'centre', rendu: (l) => l.taux === null ? '—' : S.nombre(l.taux, 1) + ' %' },
          { titre: 'Progr. finale', classe: 'centre', rendu: (l) => l.taux_final === null ? '—' : S.nombre(l.taux_final, 1) + ' %' },
          { titre: 'Statut', classe: 'centre', rendu: (l) => etiquetteStatut(l.statut) },
          { cle: 'frequency', titre: 'Fréquence', classe: 'centre' },
          { cle: 'responsible', titre: 'Responsable' }
        ], filtrees, [
          { cle: 'detail', libelle: '📈', titre: 'Suivi et saisie', classe: 'btn-primaire' },
          { cle: 'modifier', libelle: '✏️', titre: 'Modifier' },
          { cle: 'supprimer', libelle: '🗑️', titre: 'Supprimer', classe: 'btn-danger' }
        ]);
        S.brancherActions(zone, {
          detail: (id) => indicateurs.ouvrirDetail(id),
          modifier: async (id) => indicateurs.ouvrirFormulaire(await S.API.get('/api/indicators/' + id), null),
          supprimer: (id) => S.confirmer('Supprimer cet indicateur et toutes ses mesures ?', async function () {
            await S.API.supprimer('/api/indicators/' + id);
            S.notifier('Indicateur supprimé.', 'succes');
            global.Application.rafraichir();
          })
        });
      }
      ['recherche-indicateur', 'filtre-niveau', 'filtre-statut'].forEach(function (id) {
        document.getElementById(id).addEventListener('input', afficher);
      });
      afficher();
    }
  };

  /* =================================================================== */
  /* 6. Cadre de suivi des indicateurs (IPTT)                             */
  /* =================================================================== */
  const suiviIndicateurs = {
    titre: 'Cadre de suivi des indicateurs',
    sousTitre: 'Cibles et réalisations par période (IPTT) — saisie directe',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="enregistrer">💾 Enregistrer les saisies</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="iptt">⬇️ IPTT Excel</button>',
    gestionnairesBarre: {
      iptt: () => S.API.telecharger('/api/exports/' + projet() + '/iptt-excel'),
      enregistrer: async function () {
        const modifiees = document.querySelectorAll('#grille-iptt input.modifie');
        if (!modifiees.length) { S.notifier('Aucune modification à enregistrer.', 'info'); return; }
        S.basculeChargement(true);
        let compteur = 0;
        try {
          for (const champ of modifiees) {
            await S.API.post('/api/indicators/' + champ.dataset.indicateur + '/saisie', {
              period_label: champ.dataset.periode,
              value: parseFloat(String(champ.value).replace(',', '.')),
              year: parseInt(String(champ.dataset.periode).substring(0, 4), 10) || null,
              validation_status: 'Validé'
            });
            compteur++;
          }
          S.notifier(compteur + ' valeur(s) enregistrée(s).', 'succes');
          global.Application.rafraichir();
        } catch (erreur) {
          S.notifier(erreur.message, 'erreur');
        } finally {
          S.basculeChargement(false);
        }
      }
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/indicateurs/suivi/' + projet());
      if (!d.lignes.length) {
        conteneur.innerHTML = S.carte('Cadre de suivi', S.vide('Aucun indicateur paramétré.', '📊'));
        return;
      }
      if (!d.periodes.length) {
        conteneur.innerHTML = S.carte('Cadre de suivi',
          S.vide('Aucune période n\'est définie. Ouvrez un indicateur et utilisez « Générer les cibles périodiques ».', '🗓️'));
        return;
      }
      let entete = '<th style="min-width:70px">Code</th><th style="min-width:230px">Indicateur</th>' +
        '<th class="centre">Unité</th><th class="centre">Réf.</th><th class="centre">Cible</th>';
      d.periodes.forEach((p) => { entete += '<th class="centre" colspan="2">' + ech(p) + '</th>'; });
      entete += '<th class="centre">Progression vers la cible finale</th>';
      let sousEntete = '<th></th><th></th><th></th><th></th><th></th>';
      d.periodes.forEach(() => { sousEntete += '<th class="centre" style="font-size:.66rem">Cible</th>' +
        '<th class="centre" style="font-size:.66rem">Réalisé</th>'; });
      sousEntete += '<th></th>';

      const corps = d.lignes.map(function (l) {
        let cellules = '<td>' + (l.is_key ? '⭐ ' : '') + ech(l.code || '') + '</td>' +
          '<td>' + ech(l.name) + '</td><td class="centre">' + ech(l.unit || '') + '</td>' +
          '<td class="nombre">' + S.nombre(l.baseline_value, 2) + '</td>' +
          '<td class="nombre">' + S.nombre(l.target_value, 2) + '</td>';
        d.periodes.forEach(function (periode) {
          const cible = l.cibles[periode];
          const reel = l.realisations[periode];
          cellules += '<td class="centre cellule-cible">' + (cible === null || cible === undefined ? '—' : S.nombre(cible, 2)) + '</td>' +
            '<td class="centre"><input type="number" step="any" value="' +
            (reel === null || reel === undefined ? '' : reel) + '" data-indicateur="' + l.id +
            '" data-periode="' + ech(periode) + '" data-initial="' +
            (reel === null || reel === undefined ? '' : reel) + '"></td>';
        });
        cellules += '<td class="centre">' + (l.taux === null ? '—' : etiquetteStatut(l.statut) +
          '<div style="font-size:.72rem;margin-top:2px">' +
          (l.taux_final === null ? '—' : S.nombre(l.taux_final, 1) + ' %') + '</div>') + '</td>';
        return '<tr>' + cellules + '</tr>';
      }).join('');

      conteneur.innerHTML = S.carte('Cadre de suivi des indicateurs',
        '<p style="font-size:.78rem;color:#5F6368;margin-bottom:.7rem">Saisissez directement les valeurs réalisées dans les cellules blanches, puis cliquez sur « Enregistrer les saisies ». Les cellules modifiées apparaissent en orange.</p>' +
        '<div class="tableau-conteneur grille-saisie" id="grille-iptt"><table class="tableau"><thead><tr>' +
        entete + '</tr><tr>' + sousEntete + '</tr></thead><tbody>' + corps + '</tbody></table></div>');

      conteneur.querySelectorAll('#grille-iptt input').forEach(function (champ) {
        champ.addEventListener('input', function () {
          champ.classList.toggle('modifie', champ.value !== champ.dataset.initial);
        });
      });
    }
  };

  /* =================================================================== */
  /* 7. Risques                                                           */
  /* =================================================================== */
  function champsRisque() {
    return [
      { nom: 'code', libelle: 'Code', largeur: 'courte' },
      { nom: 'category', libelle: 'Catégorie', type: 'select', options: ref('categories_risque'), largeur: 'courte' },
      { nom: 'title', libelle: 'Risque identifié', obligatoire: true },
      { nom: 'cause', libelle: 'Cause', type: 'textarea', lignes: 2 },
      { nom: 'consequence', libelle: 'Conséquence sur les résultats', type: 'textarea', lignes: 2 },
      { nom: 'probability', libelle: 'Probabilité (1 à 5)', type: 'number', largeur: 'courte' },
      { nom: 'impact', libelle: 'Impact (1 à 5)', type: 'number', largeur: 'courte' },
      { nom: 'mitigation', libelle: 'Mesures d\'atténuation', type: 'textarea', lignes: 3 },
      { nom: 'contingency', libelle: 'Plan de contingence', type: 'textarea', lignes: 2 },
      { nom: 'residual_probability', libelle: 'Probabilité résiduelle', type: 'number', largeur: 'courte' },
      { nom: 'residual_impact', libelle: 'Impact résiduel', type: 'number', largeur: 'courte' },
      { nom: 'owner', libelle: 'Responsable du risque', largeur: 'courte' },
      { nom: 'status', libelle: 'Statut', type: 'select', options: ref('statuts_risque'), largeur: 'courte' },
      { nom: 'review_date', libelle: 'Date de revue', type: 'date', largeur: 'courte' }
    ];
  }

  const risques = {
    titre: 'Risques et hypothèses',
    sousTitre: 'Registre coté, matrice de criticité et suivi des hypothèses critiques',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Risque</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="hypothese">➕ Hypothèse</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="excel">⬇️ Excel</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="word">⬇️ Word</button>',
    gestionnairesBarre: {
      ajouter: () => risques.ouvrirFormulaire(null),
      hypothese: () => risques.ouvrirFormulaireHypothese(null),
      excel: () => S.API.telecharger('/api/exports/' + projet() + '/risques-excel'),
      word: () => S.API.telecharger('/api/exports/' + projet() + '/risques-word')
    },
    ouvrirFormulaire: function (risque) {
      S.formulaireModal(risque ? 'Modifier le risque' : 'Nouveau risque', champsRisque(),
        risque || { probability: 3, impact: 3, status: 'Ouvert' }, async function (donnees) {
          donnees.project_id = projet();
          if (risque) await S.API.put('/api/risks/' + risque.id, donnees);
          else await S.API.post('/api/risks', donnees);
          S.notifier('Registre des risques mis à jour.', 'succes');
          global.Application.rafraichir();
        });
    },
    ouvrirFormulaireHypothese: function (hypothese) {
      S.formulaireModal(hypothese ? 'Modifier l\'hypothèse' : 'Nouvelle hypothèse', [
        { nom: 'code', libelle: 'Code', largeur: 'courte' },
        { nom: 'level', libelle: 'Niveau concerné', type: 'select', largeur: 'courte',
          options: ref('niveaux').map((n) => ({ valeur: n.code, libelle: n.libelle })) },
        { nom: 'statement', libelle: 'Énoncé de l\'hypothèse', type: 'textarea', lignes: 3, obligatoire: true },
        { nom: 'criticality', libelle: 'Criticité', type: 'select', options: ref('criticites'), largeur: 'courte' },
        { nom: 'validation_status', libelle: 'Statut de validation', type: 'select', options: ref('statuts_hypothese'), largeur: 'courte' },
        { nom: 'verification_method', libelle: 'Méthode de vérification', type: 'textarea', lignes: 2 },
        { nom: 'responsible', libelle: 'Responsable', largeur: 'courte' },
        { nom: 'review_date', libelle: 'Date de revue', type: 'date', largeur: 'courte' },
        { nom: 'comment', libelle: 'Commentaire', type: 'textarea', lignes: 2 }
      ], hypothese || { criticality: 'Moyenne', validation_status: 'Non vérifiée' }, async function (donnees) {
        donnees.project_id = projet();
        if (hypothese) await S.API.put('/api/assumptions/' + hypothese.id, donnees);
        else await S.API.post('/api/assumptions', donnees);
        S.notifier('Hypothèse enregistrée.', 'succes');
        global.Application.rafraichir();
      });
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const [liste, hypotheses, tdb] = await Promise.all([
        S.API.get('/api/risks?project_id=' + projet()),
        S.API.get('/api/assumptions?project_id=' + projet()),
        S.API.get('/api/dashboard/' + projet())
      ]);
      const synthese = tdb.risques;

      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Risques recensés', synthese.total, synthese.ouverts + ' ouverts') +
        S.kpi('Risques critiques', synthese.critiques, 'Score ≥ 15/25', synthese.critiques ? '#D93025' : '#0F9D58') +
        S.kpi('Score moyen', S.nombre(synthese.score_moyen, 1) + ' / 25', 'Probabilité × impact') +
        S.kpi('Hypothèses suivies', hypotheses.length,
          hypotheses.filter((h) => h.validation_status === 'Invalidée').length + ' invalidée(s)') +
        '</div>';

      html += '<div class="grille grille-2">' +
        S.carte('Matrice de criticité', G.matriceRisques(synthese.matrice)) +
        S.carte('Répartition par catégorie',
          Object.keys(synthese.par_categorie).length ?
            G.anneau(Object.keys(synthese.par_categorie).map((c) => ({
              libelle: c, valeur: synthese.par_categorie[c]
            })), { centre: synthese.total, legendeCentre: 'risques' }) :
            S.vide('Aucune catégorie renseignée.', '🏷️')) +
        '</div>';

      html += S.carte('Registre des risques', S.tableau([
        { cle: 'code', titre: 'Code' },
        { cle: 'category', titre: 'Catégorie' },
        { cle: 'title', titre: 'Risque' },
        { titre: 'P', classe: 'centre', rendu: (l) => l.probability },
        { titre: 'I', classe: 'centre', rendu: (l) => l.impact },
        { titre: 'Score', classe: 'centre', rendu: (l) => '<strong>' + l.score + '</strong>' },
        { titre: 'Niveau', classe: 'centre', rendu: (l) => '<span class="etiquette" style="background:' +
          ({ Critique: '#D93025', 'Élevé': '#EA8600', 'Modéré': '#F9A825', Faible: '#0F9D58' }[l.severity] || '#9AA0A6') +
          '">' + ech(l.severity) + '</span>' },
        { cle: 'mitigation', titre: 'Atténuation' },
        { cle: 'owner', titre: 'Responsable' },
        { cle: 'status', titre: 'Statut', classe: 'centre' },
        { titre: 'Revue', rendu: (l) => S.dateFr(l.review_date) }
      ], liste, [
        { cle: 'modifier', libelle: '✏️' },
        { cle: 'supprimer', libelle: '🗑️', classe: 'btn-danger' }
      ]));

      html += S.carte('Suivi des hypothèses critiques', S.tableau([
        { cle: 'code', titre: 'Code' },
        { titre: 'Niveau', classe: 'centre', rendu: (l) => badgeNiveau(l.level) },
        { cle: 'statement', titre: 'Énoncé' },
        { cle: 'criticality', titre: 'Criticité', classe: 'centre' },
        { titre: 'Validation', classe: 'centre', rendu: (l) => '<span class="etiquette" style="background:' +
          ({ 'Vérifiée': '#0F9D58', 'Partiellement vérifiée': '#F9A825',
             'Non vérifiée': '#9AA0A6', 'Invalidée': '#D93025' }[l.validation_status] || '#9AA0A6') +
          '">' + ech(l.validation_status) + '</span>' },
        { cle: 'verification_method', titre: 'Vérification' },
        { cle: 'responsible', titre: 'Responsable' },
        { titre: 'Revue', rendu: (l) => S.dateFr(l.review_date) }
      ], hypotheses, [
        { cle: 'modifier-h', libelle: '✏️' },
        { cle: 'supprimer-h', libelle: '🗑️', classe: 'btn-danger' }
      ]));

      conteneur.innerHTML = html;
      S.brancherActions(conteneur, {
        modifier: async (id) => risques.ouvrirFormulaire(await S.API.get('/api/risks/' + id)),
        supprimer: (id) => S.confirmer('Supprimer ce risque ?', async function () {
          await S.API.supprimer('/api/risks/' + id);
          S.notifier('Risque supprimé.', 'succes');
          global.Application.rafraichir();
        }),
        'modifier-h': async (id) => risques.ouvrirFormulaireHypothese(await S.API.get('/api/assumptions/' + id)),
        'supprimer-h': (id) => S.confirmer('Supprimer cette hypothèse ?', async function () {
          await S.API.supprimer('/api/assumptions/' + id);
          S.notifier('Hypothèse supprimée.', 'succes');
          global.Application.rafraichir();
        })
      });
    }
  };

  /* =================================================================== */
  /* 8. Activités et chronogramme                                         */
  /* =================================================================== */
  function champsActivite(elements) {
    return [
      { nom: 'code', libelle: 'Code', largeur: 'courte' },
      { nom: 'name', libelle: 'Libellé de l\'activité', obligatoire: true },
      { nom: 'element_id', libelle: 'Résultat rattaché', type: 'select',
        options: (elements || []).map((e) => ({ valeur: e.id, libelle: (e.code || '') + ' — ' + e.statement.substring(0, 70) })) },
      { nom: 'description', libelle: 'Description', type: 'textarea', lignes: 2 },
      { nom: 'responsible', libelle: 'Responsable', largeur: 'courte' },
      { nom: 'partners', libelle: 'Partenaires', largeur: 'courte' },
      { nom: 'location', libelle: 'Lieu d\'exécution', largeur: 'courte' },
      { nom: 'start_date', libelle: 'Date de début', type: 'date', largeur: 'courte' },
      { nom: 'end_date', libelle: 'Date de fin', type: 'date', largeur: 'courte' },
      { nom: 'progress', libelle: 'Avancement (%)', type: 'number', largeur: 'courte' },
      { nom: 'status', libelle: 'Statut', type: 'select', options: ref('statuts_activite'), largeur: 'courte' },
      { nom: 'planned_cost', libelle: 'Coût prévu', type: 'number', largeur: 'courte' },
      { nom: 'actual_cost', libelle: 'Coût réel', type: 'number', largeur: 'courte' },
      { nom: 'year', libelle: 'Année de programmation', type: 'number', largeur: 'courte' },
      { nom: 'dependencies', libelle: 'Activités prérequises (codes)', largeur: 'courte' },
      { nom: 'milestone', libelle: 'Jalon', type: 'checkbox', texteCase: 'Cette activité constitue un jalon' },
      { nom: 'deliverable', libelle: 'Livrable attendu', type: 'textarea', lignes: 2 }
    ];
  }

  const activites = {
    titre: 'Chronogramme et activités',
    sousTitre: 'Planification opérationnelle et suivi de l\'exécution physique',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Activité</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="excel">⬇️ Gantt Excel</button>',
    gestionnairesBarre: {
      ajouter: () => activites.ouvrirFormulaire(null),
      excel: () => S.API.telecharger('/api/exports/' + projet() + '/chronogramme-excel')
    },
    ouvrirFormulaire: async function (activite) {
      const elements = await S.API.get('/api/logframe?project_id=' + projet());
      S.formulaireModal(activite ? 'Modifier l\'activité' : 'Nouvelle activité',
        champsActivite(elements), activite || { status: 'Planifiée', progress: 0 },
        async function (donnees) {
          donnees.project_id = projet();
          if (activite) await S.API.put('/api/activities/' + activite.id, donnees);
          else await S.API.post('/api/activities', donnees);
          S.notifier('Chronogramme mis à jour.', 'succes');
          global.Application.rafraichir();
        }, true);
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/activities/gantt/' + projet());
      const s = d.synthese;
      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Activités programmées', s.total, s.achevees + ' achevées') +
        S.kpi('Avancement moyen', S.nombre(s.avancement_moyen, 1) + ' %', 'Exécution physique', '#0F9D58') +
        S.kpi('Activités en retard', s.nb_en_retard, 'Échéance dépassée', s.nb_en_retard ? '#D93025' : '#0F9D58') +
        S.kpi('Jalons', s.jalons.length, 'Points de contrôle', '#EA8600') +
        '</div>';

      html += S.carte('Diagramme de Gantt', G.gantt(d.activites));

      if (s.en_retard.length) {
        html += S.carte('Activités en retard', s.en_retard.map((a) =>
          '<div class="alerte alerte-warning"><span class="type">' + ech(a.code || '') + '</span>' +
          '<span>' + ech(a.name) + ' — échéance du ' + S.dateFr(a.end_date) + ' dépassée de ' +
          a.retard_jours + ' jours (' + S.nombre(a.progress, 0) + ' % réalisé' +
          (a.responsible ? ', responsable : ' + ech(a.responsible) : '') + ')</span></div>').join(''));
      }

      html += S.carte('Liste des activités', S.tableau([
        { titre: 'Code', rendu: (l) => (l.milestone ? '◆ ' : '') + ech(l.code || '') },
        { cle: 'name', titre: 'Activité' },
        { cle: 'resultat', titre: 'Résultat rattaché' },
        { cle: 'responsible', titre: 'Responsable' },
        { titre: 'Début', rendu: (l) => S.dateFr(l.start_date) },
        { titre: 'Fin', rendu: (l) => S.dateFr(l.end_date) },
        { titre: 'Avancement', classe: 'centre', rendu: (l) => barreProgression(l.progress) },
        { cle: 'status', titre: 'Statut', classe: 'centre' },
        { titre: 'Coût prévu', classe: 'nombre', rendu: (l) => S.nombre(l.planned_cost, 0) }
      ], d.activites, [
        { cle: 'modifier', libelle: '✏️' },
        { cle: 'supprimer', libelle: '🗑️', classe: 'btn-danger' }
      ]));

      conteneur.innerHTML = html;
      S.brancherActions(conteneur, {
        modifier: async (id) => activites.ouvrirFormulaire(await S.API.get('/api/activities/' + id)),
        supprimer: (id) => S.confirmer('Supprimer cette activité ?', async function () {
          await S.API.supprimer('/api/activities/' + id);
          S.notifier('Activité supprimée.', 'succes');
          global.Application.rafraichir();
        })
      });
    }
  };

  /* =================================================================== */
  /* 9. PTBA / budget                                                     */
  /* =================================================================== */
  function champsLigneBudget(listeActivites) {
    return [
      { nom: 'code', libelle: 'Code', largeur: 'courte' },
      { nom: 'label', libelle: 'Libellé de la ligne', obligatoire: true },
      { nom: 'activity_id', libelle: 'Activité rattachée', type: 'select',
        options: (listeActivites || []).map((a) => ({ valeur: a.id, libelle: (a.code || '') + ' — ' + a.name.substring(0, 60) })) },
      { nom: 'category', libelle: 'Catégorie', type: 'select', options: ref('categories_budget'), largeur: 'courte' },
      { nom: 'unit', libelle: 'Unité', largeur: 'courte' },
      { nom: 'quantity', libelle: 'Quantité', type: 'number', largeur: 'courte' },
      { nom: 'unit_cost', libelle: 'Coût unitaire', type: 'number', largeur: 'courte' },
      { nom: 'frequency_count', libelle: 'Nombre de répétitions', type: 'number', largeur: 'courte' },
      { nom: 'year', libelle: 'Exercice', type: 'number', largeur: 'courte' },
      { nom: 'q1', libelle: 'Trimestre 1', type: 'number', largeur: 'courte' },
      { nom: 'q2', libelle: 'Trimestre 2', type: 'number', largeur: 'courte' },
      { nom: 'q3', libelle: 'Trimestre 3', type: 'number', largeur: 'courte' },
      { nom: 'q4', libelle: 'Trimestre 4', type: 'number', largeur: 'courte' },
      { nom: 'funding_source', libelle: 'Source de financement', largeur: 'courte' },
      { nom: 'committed', libelle: 'Montant engagé', type: 'number', largeur: 'courte' },
      { nom: 'disbursed', libelle: 'Montant décaissé', type: 'number', largeur: 'courte' },
      { nom: 'comment', libelle: 'Observations', type: 'textarea', lignes: 2 }
    ];
  }

  const budget = {
    titre: 'PTBA et budget',
    sousTitre: 'Plan de travail et budget annuel, suivi de l\'exécution financière',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Ligne budgétaire</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="excel">⬇️ PTBA Excel</button>',
    gestionnairesBarre: {
      ajouter: () => budget.ouvrirFormulaire(null),
      excel: () => S.API.telecharger('/api/exports/' + projet() + '/ptba-excel')
    },
    ouvrirFormulaire: async function (ligne) {
      const listeActivites = await S.API.get('/api/activities?project_id=' + projet());
      S.formulaireModal(ligne ? 'Modifier la ligne budgétaire' : 'Nouvelle ligne budgétaire',
        champsLigneBudget(listeActivites), ligne || { quantity: 1, frequency_count: 1,
          year: new Date().getFullYear() }, async function (donnees) {
          donnees.project_id = projet();
          if (ligne) await S.API.put('/api/budget/' + ligne.id, donnees);
          else await S.API.post('/api/budget', donnees);
          S.notifier('Budget mis à jour.', 'succes');
          global.Application.rafraichir();
        }, true);
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const [lignes, tdb] = await Promise.all([
        S.API.get('/api/budget?project_id=' + projet()),
        S.API.get('/api/dashboard/' + projet())
      ]);
      const b = tdb.budget;
      const devise = tdb.projet.currency || 'FCFA';
      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Budget planifié', S.nombre(b.planifie, 0), devise) +
        S.kpi('Engagé', S.nombre(b.engage, 0), S.nombre(b.taux_engagement, 1) + ' % du planifié', '#F9A825') +
        S.kpi('Décaissé', S.nombre(b.decaisse, 0), S.nombre(b.taux_execution, 1) + ' % du planifié', '#0F9D58') +
        S.kpi('Solde disponible', S.nombre(b.solde, 0), devise, '#EA8600') +
        S.kpi('Lignes budgétaires', b.nb_lignes, 'Au PTBA') +
        '</div>';

      html += '<div class="grille grille-2">' +
        S.carte('Répartition par catégorie',
          Object.keys(b.par_categorie).length ?
            G.barres(Object.keys(b.par_categorie).map((c) => ({
              libelle: c, valeur: b.par_categorie[c].planifie,
              etiquette: S.nombre(b.par_categorie[c].planifie, 0)
            })), { largeurLibelle: 175 }) : S.vide('Aucune catégorie renseignée.', '💰')) +
        S.carte('Programmation trimestrielle',
          G.colonnes(Object.keys(b.par_trimestre), [
            { nom: 'Programmé (' + devise + ')', valeurs: Object.values(b.par_trimestre), couleur: '#2E75B6' }
          ])) +
        '</div>';

      if (Object.keys(b.par_annee).length > 1) {
        html += S.carte('Exécution par exercice', G.colonnes(Object.keys(b.par_annee), [
          { nom: 'Planifié', valeurs: Object.values(b.par_annee).map((a) => a.planifie), couleur: '#5B9BD5' },
          { nom: 'Engagé', valeurs: Object.values(b.par_annee).map((a) => a.engage), couleur: '#F9A825' },
          { nom: 'Décaissé', valeurs: Object.values(b.par_annee).map((a) => a.decaisse), couleur: '#0F9D58' }
        ]));
      }

      html += S.carte('Lignes du plan de travail et budget annuel', S.tableau([
        { cle: 'code', titre: 'Code' },
        { cle: 'label', titre: 'Ligne budgétaire' },
        { cle: 'category', titre: 'Catégorie' },
        { cle: 'unit', titre: 'Unité', classe: 'centre' },
        { titre: 'Qté', classe: 'nombre', rendu: (l) => S.nombre(l.quantity, 0) },
        { titre: 'Coût unit.', classe: 'nombre', rendu: (l) => S.nombre(l.unit_cost, 0) },
        { titre: 'Total', classe: 'nombre', rendu: (l) => '<strong>' + S.nombre(l.total_planned, 0) + '</strong>' },
        { titre: 'T1', classe: 'nombre', rendu: (l) => S.nombre(l.q1, 0) },
        { titre: 'T2', classe: 'nombre', rendu: (l) => S.nombre(l.q2, 0) },
        { titre: 'T3', classe: 'nombre', rendu: (l) => S.nombre(l.q3, 0) },
        { titre: 'T4', classe: 'nombre', rendu: (l) => S.nombre(l.q4, 0) },
        { titre: 'Décaissé', classe: 'nombre', rendu: (l) => S.nombre(l.disbursed, 0) },
        { titre: 'Exéc.', classe: 'centre', rendu: (l) => l.total_planned ?
          S.nombre((l.disbursed || 0) / l.total_planned * 100, 1) + ' %' : '—' },
        { cle: 'funding_source', titre: 'Financement' },
        { cle: 'year', titre: 'Exercice', classe: 'centre' }
      ], lignes, [
        { cle: 'modifier', libelle: '✏️' },
        { cle: 'supprimer', libelle: '🗑️', classe: 'btn-danger' }
      ]));

      conteneur.innerHTML = html;
      S.brancherActions(conteneur, {
        modifier: async (id) => budget.ouvrirFormulaire(await S.API.get('/api/budget/' + id)),
        supprimer: (id) => S.confirmer('Supprimer cette ligne budgétaire ?', async function () {
          await S.API.supprimer('/api/budget/' + id);
          S.notifier('Ligne supprimée.', 'succes');
          global.Application.rafraichir();
        })
      });
    }
  };

  /* =================================================================== */
  /* 10. Collecte : fiches et questionnaires                              */
  /* =================================================================== */
  const collecte = {
    titre: 'Fiches et questionnaires',
    sousTitre: 'Conception des instruments de collecte et export Word / XLSForm',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Instrument</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="importer-xlsform">⬆️ Importer un XLSForm</button>',
    gestionnairesBarre: {
      ajouter: () => collecte.ouvrirFormulaire(null),
      'importer-xlsform': function () {
        const champ = document.createElement('input');
        champ.type = 'file';
        champ.accept = '.xlsx';
        champ.addEventListener('change', async function () {
          if (!champ.files.length) return;
          const donnees = new FormData();
          donnees.append('fichier', champ.files[0]);
          S.basculeChargement(true);
          try {
            const r = await S.API.televerser('/api/imports/xlsform/' + projet(), donnees);
            S.notifier(r.questions_importees + ' questions importées.', 'succes');
            global.Application.rafraichir();
          } catch (erreur) { S.notifier(erreur.message, 'erreur'); }
          finally { S.basculeChargement(false); }
        });
        champ.click();
      }
    },
    ouvrirFormulaire: function (form) {
      S.formulaireModal(form ? 'Modifier l\'instrument' : 'Nouvel instrument de collecte', [
        { nom: 'code', libelle: 'Code', largeur: 'courte' },
        { nom: 'version', libelle: 'Version', largeur: 'courte' },
        { nom: 'name', libelle: 'Intitulé', obligatoire: true },
        { nom: 'form_type', libelle: 'Type d\'instrument', type: 'select', options: ref('types_formulaire'), largeur: 'courte' },
        { nom: 'periodicity', libelle: 'Périodicité de collecte', type: 'select', options: ref('frequences'), largeur: 'courte' },
        { nom: 'target_respondent', libelle: 'Population cible / répondant' },
        { nom: 'description', libelle: 'Description', type: 'textarea', lignes: 3 },
        { nom: 'instructions', libelle: 'Consignes à l\'enquêteur', type: 'textarea', lignes: 4 },
        { nom: 'language', libelle: 'Langue (code)', largeur: 'courte' }
      ], form || { version: '1.0', language: 'fr', form_type: 'Questionnaire' }, async function (donnees) {
        donnees.project_id = projet();
        if (form) await S.API.put('/api/forms/' + form.id, donnees);
        else await S.API.post('/api/forms', donnees);
        S.notifier('Instrument enregistré.', 'succes');
        global.Application.rafraichir();
      });
    },
    ouvrirConcepteur: async function (formId) {
      const d = await S.API.get('/api/forms/' + formId + '/complet');
      const contenu = document.createElement('div');

      function rendreQuestions() {
        contenu.querySelector('#liste-questions').innerHTML = S.tableau([
          { titre: '#', classe: 'centre', rendu: (l, i) => i + 1 },
          { cle: 'section', titre: 'Section' },
          { cle: 'name', titre: 'Nom technique' },
          { cle: 'label', titre: 'Question' },
          { cle: 'question_type', titre: 'Type', classe: 'centre' },
          { titre: 'Modalités', classe: 'centre', rendu: (l) => (l.choices || []).length || '—' },
          { titre: 'Oblig.', classe: 'centre', rendu: (l) => l.required ? '✔' : '' },
          { cle: 'linked_indicator_code', titre: 'Indicateur', classe: 'centre' }
        ], d.questions, [
          { cle: 'modifier-q', libelle: '✏️' },
          { cle: 'supprimer-q', libelle: '🗑️', classe: 'btn-danger' }
        ]);
        S.brancherActions(contenu.querySelector('#liste-questions'), {
          'modifier-q': (id) => collecte.formulaireQuestion(formId, d.questions.find((q) => q.id === id)),
          'supprimer-q': (id) => S.confirmer('Supprimer cette question ?', async function () {
            await S.API.supprimer('/api/questions/' + id);
            S.notifier('Question supprimée.', 'succes');
            S.fermerModale();
            collecte.ouvrirConcepteur(formId);
          })
        });
      }

      contenu.innerHTML =
        '<p style="font-size:.82rem;color:#5F6368">' + ech(d.formulaire.description || '') + '</p>' +
        '<div class="barre-outils">' +
        '<button class="btn btn-primaire btn-petit" data-concepteur="question">➕ Ajouter une question</button>' +
        '<button class="btn btn-secondaire btn-petit" data-concepteur="word">⬇️ Questionnaire Word</button>' +
        '<button class="btn btn-secondaire btn-petit" data-concepteur="xlsform">⬇️ XLSForm (Kobo/ODK)</button>' +
        '<button class="btn btn-secondaire btn-petit" data-concepteur="kobo">⬆️ Importer des réponses</button>' +
        '</div><div id="liste-questions"></div>';
      S.ouvrirModale('Concepteur — ' + d.formulaire.name, contenu, [
        { libelle: 'Fermer', classe: 'btn-secondaire', action: S.fermerModale }
      ], true);
      rendreQuestions();

      contenu.querySelectorAll('[data-concepteur]').forEach(function (bouton) {
        bouton.addEventListener('click', function () {
          const action = bouton.dataset.concepteur;
          if (action === 'question') collecte.formulaireQuestion(formId, null, d.questions.length);
          if (action === 'word') S.API.telecharger('/api/exports/forms/' + formId + '/word');
          if (action === 'xlsform') S.API.telecharger('/api/exports/forms/' + formId + '/xlsform');
          if (action === 'kobo') {
            const champ = document.createElement('input');
            champ.type = 'file';
            champ.accept = '.xlsx';
            champ.addEventListener('change', async function () {
              if (!champ.files.length) return;
              const donnees = new FormData();
              donnees.append('fichier', champ.files[0]);
              S.basculeChargement(true);
              try {
                const r = await S.API.televerser('/api/imports/kobo/' + formId, donnees);
                S.notifier(r.reponses_importees + ' réponses importées, ' +
                  r.indicateurs_alimentes.length + ' indicateur(s) alimenté(s).', 'succes');
              } catch (erreur) { S.notifier(erreur.message, 'erreur'); }
              finally { S.basculeChargement(false); }
            });
            champ.click();
          }
        });
      });
    },
    formulaireQuestion: function (formId, question, position) {
      const champs = [
        { nom: 'section', libelle: 'Section', largeur: 'courte' },
        { nom: 'order_index', libelle: 'Ordre', type: 'number', largeur: 'courte' },
        { nom: 'name', libelle: 'Nom technique (variable)', obligatoire: true, largeur: 'courte',
          aide: 'Minuscules, sans espace ni accent — utilisé dans XLSForm.' },
        { nom: 'question_type', libelle: 'Type de question', type: 'select',
          options: ref('types_question'), largeur: 'courte' },
        { nom: 'label', libelle: 'Libellé de la question', type: 'textarea', lignes: 2, obligatoire: true },
        { nom: 'choix_texte', libelle: 'Modalités de réponse', type: 'textarea', lignes: 4,
          aide: 'Une modalité par ligne, au format « code|libellé » (ex. 1|Oui). Uniquement pour les questions à choix.' },
        { nom: 'hint', libelle: 'Consigne / aide', type: 'textarea', lignes: 2 },
        { nom: 'required', libelle: 'Obligatoire', type: 'checkbox', texteCase: 'Réponse obligatoire' },
        { nom: 'constraint', libelle: 'Contrainte de saisie', largeur: 'courte',
          aide: 'Syntaxe XLSForm, ex. . >= 0 and . <= 100' },
        { nom: 'constraint_message', libelle: 'Message si contrainte violée', largeur: 'courte' },
        { nom: 'relevant', libelle: 'Condition d\'affichage (saut)', largeur: 'courte',
          aide: 'Ex. ${consentement} = \'1\'' },
        { nom: 'calculation', libelle: 'Calcul (type calculate)', largeur: 'courte' },
        { nom: 'appearance', libelle: 'Apparence', largeur: 'courte' },
        { nom: 'linked_indicator_code', libelle: 'Code de l\'indicateur alimenté', largeur: 'courte' }
      ];
      const valeurs = Object.assign({}, question || { question_type: 'text', order_index: position || 0 });
      valeurs.choix_texte = (question && question.choices || []).map(
        (c) => (c.name || '') + '|' + (c.label || '')).join('\n');
      S.formulaireModal(question ? 'Modifier la question' : 'Nouvelle question', champs, valeurs,
        async function (donnees) {
          donnees.choices = (donnees.choix_texte || '').split('\n').map(function (ligne) {
            const morceaux = ligne.split('|');
            if (!ligne.trim()) return null;
            return morceaux.length > 1 ?
              { name: morceaux[0].trim(), label: morceaux.slice(1).join('|').trim() } :
              { name: morceaux[0].trim(), label: morceaux[0].trim() };
          }).filter(Boolean);
          delete donnees.choix_texte;
          donnees.form_id = formId;
          if (question) await S.API.put('/api/questions/' + question.id, donnees);
          else await S.API.post('/api/questions', donnees);
          S.notifier('Question enregistrée.', 'succes');
          S.fermerModale();
          collecte.ouvrirConcepteur(formId);
        }, true);
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const formulaires = await S.API.get('/api/forms?project_id=' + projet());
      conteneur.innerHTML = S.carte('Instruments de collecte',
        S.tableau([
          { cle: 'code', titre: 'Code' },
          { cle: 'name', titre: 'Intitulé' },
          { cle: 'form_type', titre: 'Type' },
          { cle: 'target_respondent', titre: 'Population cible' },
          { cle: 'periodicity', titre: 'Périodicité', classe: 'centre' },
          { cle: 'version', titre: 'Version', classe: 'centre' },
          { titre: 'Indicateurs', rendu: (l) => (l.linked_indicators || []).join(', ') || '—' }
        ], formulaires, [
          { cle: 'concevoir', libelle: '🧩', titre: 'Concevoir les questions', classe: 'btn-primaire' },
          { cle: 'word', libelle: '📄', titre: 'Questionnaire Word' },
          { cle: 'xlsform', libelle: '📱', titre: 'XLSForm KoboToolbox' },
          { cle: 'modifier', libelle: '✏️' },
          { cle: 'supprimer', libelle: '🗑️', classe: 'btn-danger' }
        ]),
        '', 'Chaque instrument peut être exporté en Word (administration papier) et en XLSForm (collecte mobile hors ligne avec KoboToolbox ou ODK Collect).');

      S.brancherActions(conteneur, {
        concevoir: (id) => collecte.ouvrirConcepteur(id),
        word: (id) => S.API.telecharger('/api/exports/forms/' + id + '/word'),
        xlsform: (id) => S.API.telecharger('/api/exports/forms/' + id + '/xlsform'),
        modifier: async (id) => collecte.ouvrirFormulaire(await S.API.get('/api/forms/' + id)),
        supprimer: (id) => S.confirmer('Supprimer cet instrument et ses questions ?', async function () {
          await S.API.supprimer('/api/forms/' + id);
          S.notifier('Instrument supprimé.', 'succes');
          global.Application.rafraichir();
        })
      });
    }
  };

  /* =================================================================== */
  /* 11. Import                                                           */
  /* =================================================================== */
  const imports = {
    titre: 'Importer un projet',
    sousTitre: 'Chargement d\'un cadre logique et d\'un budget depuis Excel ou Word',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="modele">⬇️ Télécharger le modèle Excel</button>',
    gestionnairesBarre: {
      modele: () => S.API.telecharger('/api/exports/modele-import')
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      conteneur.innerHTML =
        S.carte('1. Import depuis Excel',
          '<p style="font-size:.84rem">Chargez un classeur contenant tout ou partie des onglets suivants : ' +
          '<strong>Cadre logique</strong>, <strong>Indicateurs</strong>, <strong>Cibles</strong>, ' +
          '<strong>Réalisations</strong>, <strong>Activités</strong>, <strong>Budget</strong>, ' +
          '<strong>Risques</strong>, <strong>Hypothèses</strong>. Les intitulés de colonnes sont ' +
          'reconnus automatiquement, même s\'ils diffèrent légèrement du modèle.</p>' +
          '<div class="zone-depot" id="depot-excel"><span class="icone">📊</span>' +
          'Cliquez ou déposez ici votre fichier Excel (.xlsx)</div>' +
          '<label style="display:flex;gap:.4rem;align-items:center;margin-top:.8rem;font-size:.82rem">' +
          '<input type="checkbox" id="remplacer-donnees"> Remplacer les données existantes du projet ' +
          '(sinon, les enregistrements sont ajoutés ou mis à jour)</label>' +
          '<div id="rapport-excel" style="margin-top:1rem"></div>',
          '<button class="btn btn-secondaire btn-petit" id="btn-modele">⬇️ Modèle</button>') +
        S.carte('2. Import depuis Word',
          '<p style="font-size:.84rem">Chargez un document contenant une matrice de cadre logique sous ' +
          'forme de tableau. La plateforme analyse le document, identifie les tableaux exploitables ' +
          'et vous laisse choisir celui à importer.</p>' +
          '<div class="zone-depot" id="depot-word"><span class="icone">📄</span>' +
          'Cliquez ou déposez ici votre document Word (.docx)</div>' +
          '<div id="rapport-word" style="margin-top:1rem"></div>');

      document.getElementById('btn-modele').addEventListener('click',
        () => S.API.telecharger('/api/exports/modele-import'));

      function brancherDepot(idZone, accept, surFichier) {
        const zone = document.getElementById(idZone);
        const champ = document.createElement('input');
        champ.type = 'file';
        champ.accept = accept;
        champ.addEventListener('change', function () {
          if (champ.files.length) surFichier(champ.files[0]);
        });
        zone.addEventListener('click', () => champ.click());
        zone.addEventListener('dragover', function (e) { e.preventDefault(); zone.classList.add('survol'); });
        zone.addEventListener('dragleave', () => zone.classList.remove('survol'));
        zone.addEventListener('drop', function (e) {
          e.preventDefault();
          zone.classList.remove('survol');
          if (e.dataTransfer.files.length) surFichier(e.dataTransfer.files[0]);
        });
      }

      brancherDepot('depot-excel', '.xlsx', async function (fichier) {
        const donnees = new FormData();
        donnees.append('fichier', fichier);
        donnees.append('remplacer', document.getElementById('remplacer-donnees').checked ? 'true' : 'false');
        S.basculeChargement(true);
        try {
          const r = await S.API.televerser('/api/imports/excel/' + projet(), donnees);
          document.getElementById('rapport-excel').innerHTML =
            '<div class="alerte alerte-info"><span class="type">Import réussi</span><span>Feuilles traitées : ' +
            ech((r.feuilles_traitees || []).join(', ') || 'aucune') + '</span></div>' +
            '<div class="tableau-conteneur"><table class="tableau"><thead><tr><th>Catégorie</th>' +
            '<th class="centre">Enregistrements créés</th></tr></thead><tbody>' +
            Object.keys(r.crees || {}).map((cle) => '<tr><td>' + ech(cle) + '</td><td class="centre">' +
              r.crees[cle] + '</td></tr>').join('') + '</tbody></table></div>' +
            (r.avertissements || []).map((a) => '<div class="alerte alerte-warning"><span>' +
              ech(a) + '</span></div>').join('');
          S.notifier('Import Excel terminé.', 'succes');
        } catch (erreur) {
          document.getElementById('rapport-excel').innerHTML =
            '<div class="alerte alerte-danger"><span class="type">Échec</span><span>' +
            ech(erreur.message) + '</span></div>';
        } finally { S.basculeChargement(false); }
      });

      brancherDepot('depot-word', '.docx', async function (fichier) {
        const donneesAnalyse = new FormData();
        donneesAnalyse.append('fichier', fichier);
        S.basculeChargement(true);
        try {
          const analyse = await S.API.televerser('/api/imports/word/analyser', donneesAnalyse);
          const exploitables = analyse.tableaux.filter((t) => t.nature !== 'inconnu');
          document.getElementById('rapport-word').innerHTML =
            '<p style="font-size:.84rem">' + analyse.nb_tableaux + ' tableau(x) détecté(s), dont ' +
            exploitables.length + ' exploitable(s).</p>' +
            S.tableau([
              { cle: 'index', titre: 'N°', classe: 'centre' },
              { cle: 'nature', titre: 'Nature détectée' },
              { cle: 'lignes', titre: 'Lignes', classe: 'centre' },
              { cle: 'colonnes', titre: 'Colonnes', classe: 'centre' },
              { titre: 'En-têtes', rendu: (l) => ech((l.entetes || []).join(' | ').substring(0, 120)) }
            ], analyse.tableaux, [{ cle: 'importer-tableau', libelle: '⬆️ Importer', classe: 'btn-primaire' }])
              .replace(/data-id="undefined"/g, '');
          const zone = document.getElementById('rapport-word');
          zone.querySelectorAll('[data-action="importer-tableau"]').forEach(function (bouton, position) {
            bouton.addEventListener('click', async function () {
              const donneesImport = new FormData();
              donneesImport.append('fichier', fichier);
              donneesImport.append('index_tableau', analyse.tableaux[position].index);
              S.basculeChargement(true);
              try {
                const r = await S.API.televerser('/api/imports/word/' + projet(), donneesImport);
                S.notifier(r.resultats_crees + ' résultats, ' + r.indicateurs_crees +
                  ' indicateurs et ' + r.risques_crees + ' risques importés.', 'succes');
                (r.avertissements || []).forEach((a) => S.notifier(a, 'info'));
              } catch (erreur) { S.notifier(erreur.message, 'erreur'); }
              finally { S.basculeChargement(false); }
            });
          });
        } catch (erreur) {
          document.getElementById('rapport-word').innerHTML =
            '<div class="alerte alerte-danger"><span>' + ech(erreur.message) + '</span></div>';
        } finally { S.basculeChargement(false); }
      });
    }
  };

  /* =================================================================== */
  /* 12. Livrables                                                        */
  /* =================================================================== */
  const livrables = {
    titre: 'Livrables de suivi-évaluation',
    sousTitre: 'Génération automatique des documents Word et Excel du dispositif',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="dossier">📦 Dossier complet (ZIP)</button>',
    gestionnairesBarre: {
      dossier: () => S.API.telecharger('/api/exports/' + projet() + '/dossier-complet')
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const catalogue = await S.API.get('/api/exports/catalogue');
      conteneur.innerHTML = S.carte('Catalogue des livrables',
        '<div class="liste-livrables">' + catalogue.map(function (l) {
          return '<div class="livrable"><span class="format format-' + l.format + '">' + l.format + '</span>' +
            '<h4>' + ech(l.libelle) + '</h4><p>' + ech(l.description) + '</p>' +
            '<button class="btn btn-primaire btn-petit" data-livrable="' + l.cle + '">⬇️ Générer</button></div>';
        }).join('') + '</div>',
        '', 'Tous les documents sont produits à partir des données saisies dans la plateforme et sont modifiables après téléchargement.');

      conteneur.querySelectorAll('[data-livrable]').forEach(function (bouton) {
        bouton.addEventListener('click', function () {
          const cle = bouton.dataset.livrable;
          if (cle === 'modele-import') { S.API.telecharger('/api/exports/modele-import'); return; }
          S.API.telecharger('/api/exports/' + projet() + '/' + cle);
        });
      });
    }
  };

  /* =================================================================== */
  /* 13. Power BI                                                         */
  /* =================================================================== */
  const powerbi = {
    titre: 'Connexion Power BI',
    sousTitre: 'Flux de données temps réel et modèle en étoile pour la business intelligence',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="dataset">⬇️ Classeur Power BI</button>',
    gestionnairesBarre: {
      dataset: () => S.API.telecharger('/api/exports/' + projet() + '/powerbi-dataset')
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/powerbi/' + projet() + '/lien');
      const origine = window.location.origin;
      const jeton = S.Etat.jeton;
      const urlDataset = origine + '/api/powerbi/' + projet() + '/dataset?token=' + jeton;

      conteneur.innerHTML =
        S.carte('Méthode 1 — Connexion directe (actualisation à la demande)',
          '<ol style="font-size:.86rem;line-height:1.7">' +
          '<li>Ouvrir <strong>Power BI Desktop</strong> puis <em>Accueil &gt; Obtenir des données &gt; Web</em>.</li>' +
          '<li>Coller l\'URL ci-dessous dans le champ « URL ».</li>' +
          '<li>Dans l\'éditeur Power Query, développer la colonne <code>tables</code> puis chaque table souhaitée.</li>' +
          '<li>Créer les relations entre <code>Dim_*</code> et <code>Fait_*</code> dans la vue Modèle.</li>' +
          '</ol>' +
          '<pre class="code">' + ech(urlDataset) + '</pre>' +
          '<button class="btn btn-secondaire btn-petit" id="copier-url">📋 Copier l\'URL</button>' +
          '<p style="font-size:.76rem;color:#EA8600;margin-top:.7rem">⚠️ Ce lien contient votre jeton d\'accès personnel, valable 12 heures. Ne le partagez pas.</p>') +
        S.carte('Méthode 2 — Classeur Excel structuré',
          '<p style="font-size:.86rem">Le classeur « Jeu de données Power BI » contient le modèle en étoile ' +
          'complet (dimensions et tables de faits), une dimension calendrier et une notice détaillée ' +
          'des relations et mesures DAX à créer. Il convient lorsque la plateforme n\'est pas accessible ' +
          'depuis le poste d\'analyse.</p>' +
          '<button class="btn btn-primaire btn-petit" id="btn-dataset">⬇️ Télécharger le classeur</button>') +
        S.carte('Tables disponibles',
          '<div class="tableau-conteneur"><table class="tableau"><thead><tr><th>Table</th>' +
          '<th>URL JSON</th><th class="centre">CSV</th></tr></thead><tbody>' +
          d.tables.map(function (chemin) {
            const nom = chemin.split('/table/')[1].split('?')[0];
            return '<tr><td><strong>' + ech(nom) + '</strong></td>' +
              '<td style="font-size:.72rem;word-break:break-all">' + ech(origine + chemin) + '</td>' +
              '<td class="centre"><button class="btn btn-petit btn-secondaire" data-csv="' + nom +
              '">⬇️ CSV</button></td></tr>';
          }).join('') + '</tbody></table></div>') +
        S.carte('Mesures DAX recommandées',
          '<pre class="code">Taux de réalisation = \n' +
          'DIVIDE(SUM(Fait_Realisation[ValeurRealisee]), SUM(Fait_Cible[ValeurCible]))\n\n' +
          'Taux d\'exécution budgétaire = \n' +
          'DIVIDE(SUM(Fait_Budget[Decaisse]), SUM(Fait_Budget[TotalPlanifie]))\n\n' +
          'Avancement physique moyen = AVERAGE(Fait_Activite[Avancement])\n\n' +
          'Risques critiques = \n' +
          'CALCULATE(COUNTROWS(Fait_Risque), Fait_Risque[Niveau] = "Critique")</pre>');

      document.getElementById('copier-url').addEventListener('click', function () {
        navigator.clipboard.writeText(urlDataset).then(
          () => S.notifier('URL copiée dans le presse-papiers.', 'succes'),
          () => S.notifier('Copie impossible : sélectionnez et copiez l\'URL manuellement.', 'erreur'));
      });
      document.getElementById('btn-dataset').addEventListener('click',
        () => S.API.telecharger('/api/exports/' + projet() + '/powerbi-dataset'));
      conteneur.querySelectorAll('[data-csv]').forEach(function (bouton) {
        bouton.addEventListener('click', function () {
          window.open('/api/powerbi/' + projet() + '/csv/' + bouton.dataset.csv + '?token=' + jeton, '_blank');
        });
      });
    }
  };

  /* =================================================================== */
  /* 14. Administration                                                   */
  /* =================================================================== */
  const administration = {
    titre: 'Administration',
    sousTitre: 'Comptes utilisateurs, droits d\'accès et journal des opérations',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="utilisateur">➕ Utilisateur</button>',
    gestionnairesBarre: {
      utilisateur: () => administration.ouvrirFormulaire(null)
    },
    ouvrirFormulaire: async function (utilisateur) {
      const roles = await S.API.get('/api/auth/roles');
      S.formulaireModal(utilisateur ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur', [
        { nom: 'full_name', libelle: 'Nom complet', obligatoire: true },
        { nom: 'email', libelle: 'Adresse électronique', type: 'email', obligatoire: !utilisateur },
        { nom: 'role', libelle: 'Rôle', type: 'select',
          options: roles.map((r) => ({ valeur: r.code, libelle: r.libelle })) },
        { nom: 'organisation', libelle: 'Organisation', largeur: 'courte' },
        { nom: 'phone', libelle: 'Téléphone', largeur: 'courte' },
        { nom: 'password', libelle: utilisateur ? 'Nouveau mot de passe (laisser vide pour conserver)' : 'Mot de passe', type: 'password' },
        { nom: 'is_active', libelle: 'Compte actif', type: 'checkbox', texteCase: 'Le compte peut se connecter' }
      ], utilisateur || { role: 'lecteur', is_active: true }, async function (donnees) {
        if (utilisateur) await S.API.put('/api/auth/utilisateurs/' + utilisateur.id, donnees);
        else await S.API.post('/api/auth/utilisateurs', donnees);
        S.notifier('Compte enregistré.', 'succes');
        global.Application.rafraichir();
      });
    },
    rendre: async function (conteneur) {
      if (S.Etat.utilisateur.role !== 'admin') {
        conteneur.innerHTML = S.vide('Cette section est réservée aux administrateurs.', '🔒');
        return;
      }
      const [utilisateurs, journal] = await Promise.all([
        S.API.get('/api/auth/utilisateurs'),
        S.API.get('/api/journal?limit=120')
      ]);
      conteneur.innerHTML =
        S.carte('Comptes utilisateurs', S.tableau([
          { cle: 'full_name', titre: 'Nom' },
          { cle: 'email', titre: 'Adresse électronique' },
          { cle: 'role', titre: 'Rôle', classe: 'centre' },
          { cle: 'organisation', titre: 'Organisation' },
          { titre: 'Actif', classe: 'centre', rendu: (l) => l.is_active ? '✔' : '✖' },
          { titre: 'Dernière connexion', rendu: (l) => S.dateFr(l.last_login) }
        ], utilisateurs, [
          { cle: 'modifier', libelle: '✏️' },
          { cle: 'supprimer', libelle: '🗑️', classe: 'btn-danger' }
        ])) +
        S.carte('Journal des opérations', S.tableau([
          { titre: 'Date', rendu: (l) => new Date(l.at).toLocaleString('fr-FR') },
          { cle: 'user_email', titre: 'Utilisateur' },
          { cle: 'action', titre: 'Action', classe: 'centre' },
          { cle: 'entity', titre: 'Entité' },
          { cle: 'entity_id', titre: 'Réf.', classe: 'centre' },
          { cle: 'detail', titre: 'Détail' }
        ], journal)) +
        S.carte('Rôles et droits',
          '<div class="tableau-conteneur"><table class="tableau"><thead><tr><th>Rôle</th>' +
          '<th>Droits</th></tr></thead><tbody>' +
          '<tr><td><strong>Lecteur</strong></td><td>Consultation et téléchargement des livrables.</td></tr>' +
          '<tr><td><strong>Opérateur de saisie</strong></td><td>Consultation + création et modification des données (indicateurs, activités, budget, risques).</td></tr>' +
          '<tr><td><strong>Responsable S&E</strong></td><td>Droits précédents + création et paramétrage de projets, consultation du journal.</td></tr>' +
          '<tr><td><strong>Coordonnateur</strong></td><td>Droits précédents, pilotage du projet.</td></tr>' +
          '<tr><td><strong>Administrateur</strong></td><td>Accès complet, gestion des comptes utilisateurs.</td></tr>' +
          '</tbody></table></div>');

      S.brancherActions(conteneur, {
        modifier: (id) => administration.ouvrirFormulaire(utilisateurs.find((u) => u.id === id)),
        supprimer: (id) => S.confirmer('Supprimer ce compte utilisateur ?', async function () {
          await S.API.supprimer('/api/auth/utilisateurs/' + id);
          S.notifier('Compte supprimé.', 'succes');
          global.Application.rafraichir();
        })
      });
    }
  };

  /* =================================================================== */
  global.Vues = {
    'tableau-de-bord': tableauDeBord,
    'portefeuille': portefeuille,
    'projet': ficheProjet,
    'cadre-logique': cadreLogique,
    'indicateurs': indicateurs,
    'suivi': suiviIndicateurs,
    'risques': risques,
    'activites': activites,
    'budget': budget,
    'collecte': collecte,
    'imports': imports,
    'livrables': livrables,
    'powerbi': powerbi,
    'administration': administration
  };
})(window);
