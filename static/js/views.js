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
    actions: () => '<label style="display:flex;align-items:center;gap:.3rem;font-size:.76rem;color:#5F6368">' +
      '<input type="checkbox" id="auto-rafraichir"' +
      (localStorage.getItem('sepia_auto') === '1' ? ' checked' : '') + '> Actualisation auto</label>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="actualiser">🔄 Actualiser</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="imprimer">🖨️ Imprimer</button>' +
      '<button class="btn btn-primaire btn-petit" data-barre="tdb-excel">⬇️ Tableau de bord Excel</button>',
    gestionnairesBarre: {
      imprimer: () => window.print(),
      actualiser: () => global.Application.rafraichir(),
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

      // Bandeau des dimensions ajoutées : équité, couverture territoriale, qualité
      const eg = d.desagregation.equite_genre;
      html += '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Bénéficiaires femmes', eg ? S.nombre(eg.part_femmes, 1) + ' %' : '—',
          eg ? S.nombre(eg.femmes, 0) + ' sur ' + S.nombre(eg.total, 0) + ' — ' + eg.appreciation :
            'Aucune ventilation saisie',
          eg ? (Math.abs(eg.ecart_parite) <= 5 ? '#0F9D58' : '#EA8600') : '#9AA0A6') +
        S.kpi('Taux de désagrégation',
          d.desagregation.taux_desagregation === null ? '—' :
            S.nombre(d.desagregation.taux_desagregation, 0) + ' %',
          d.desagregation.indicateurs_desagreges + ' / ' +
            d.desagregation.indicateurs_a_desagreger + ' indicateurs ventilés',
          d.desagregation.taux_desagregation !== null &&
            d.desagregation.taux_desagregation >= 80 ? '#0F9D58' : '#EA8600') +
        S.kpi('Couverture territoriale',
          d.zones.taux_couverture_zones === null ? '—' :
            S.nombre(d.zones.taux_couverture_zones, 0) + ' %',
          d.zones.zones_couvertes + ' / ' + d.zones.nb_zones + ' zones documentées', '#5B9BD5') +
        S.kpi('Qualité SMART', S.nombre(d.qualite.score_systeme, 0) + ' %',
          d.qualite.appreciation + ' — ' + d.qualite.a_reprendre + ' à reprendre',
          d.qualite.score_systeme >= 90 ? '#0F9D58' : d.qualite.score_systeme >= 75 ? '#4CAF50' :
            d.qualite.score_systeme >= 60 ? '#F9A825' : '#D93025') +
        '</div>';

      if (d.derniere_mise_a_jour) {
        html += '<p style="font-size:.74rem;color:#5F6368;margin:-.4rem 0 .8rem">Dernière donnée ' +
          'enregistrée le ' + new Date(d.derniere_mise_a_jour).toLocaleString('fr-FR') +
          ' · Affichage généré le ' + new Date().toLocaleString('fr-FR') + '</p>';
      }

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

      const zonesDocumentees = (d.zones.detail || []).filter((z) => z.nb_mesures);
      const zonesLocalisees = (d.zones.detail || []).filter(
        (z) => z.id !== null && typeof z.latitude === 'number');
      if (zonesLocalisees.length) {
        html += S.carte('Carte de couverture du projet',
          G.carte(zonesLocalisees, {
            fond: localStorage.getItem('sepia_fond_carte') !== '0',
            largeur: 760, hauteur: 420
          }),
          '<button class="btn btn-secondaire btn-petit" data-lien="zones">Voir le détail</button>',
          'Surface du cercle : bénéficiaires atteints. Couleur : taux de couverture de la cible de la zone.');
      }
      if (zonesDocumentees.length) {
        html += S.carte('Couverture par zone d\'intervention',
          G.barres(zonesDocumentees.map((z) => ({
            libelle: z.nom, valeur: z.taux_couverture === null ? 0 : Math.min(z.taux_couverture, 100),
            etiquette: S.nombre(z.beneficiaires_atteints, 0) +
              (z.taux_couverture === null ? '' : ' (' + S.nombre(z.taux_couverture, 0) + ' %)'),
            couleur: z.taux_couverture === null ? '#9AA0A6' :
              z.taux_couverture >= 80 ? '#0F9D58' : z.taux_couverture >= 50 ? '#F9A825' : '#EA8600'
          })), { max: 100, largeurLibelle: 200 }),
          '<button class="btn btn-secondaire btn-petit" data-lien="zones">Voir le détail</button>',
          'Bénéficiaires atteints rapportés à la cible de chaque zone.');
      }

      conteneur.innerHTML = html;

      conteneur.querySelectorAll('[data-lien="zones"]').forEach(function (lien) {
        lien.addEventListener('click', () => global.Application.naviguer('zones'));
      });
      G.surveillerFondCarte(conteneur);

      // Actualisation automatique : le tableau de bord reflète les saisies en continu.
      const bascule = document.getElementById('auto-rafraichir');
      if (bascule) {
        bascule.addEventListener('change', function () {
          localStorage.setItem('sepia_auto', bascule.checked ? '1' : '0');
          global.Application.programmerRafraichissement();
        });
      }
      global.Application.programmerRafraichissement();
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
    { nom: 'me_approach', libelle: 'Approche de suivi-évaluation retenue', type: 'textarea', lignes: 5, section: 'Cadrage stratégique' },
    { nom: 'show_process_indicators', libelle: 'Indicateurs d\'activité et de processus',
      type: 'checkbox', section: 'Options d\'affichage',
      texteCase: 'Afficher les indicateurs d\'activité / de processus dans les tableaux de bord, analyses et livrables',
      aide: 'Les indicateurs de processus mesurent la conduite de l\'action (taux d\'exécution, délais, participation) plutôt que le changement produit. Désactivés, ils restent enregistrés mais n\'alourdissent pas la lecture du dispositif.' }
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
      { nom: 'indicator_class', libelle: 'Nature de l\'indicateur', type: 'select',
        largeur: 'courte', section: 'Identification',
        options: ['Résultat', 'Processus'],
        aide: '« Processus » mesure la conduite de l\'action (exécution, délais, participation). Son affichage dépend de l\'option activée sur le projet.' },
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
      const [d, projetCourant] = await Promise.all([
        S.API.get('/api/dashboard/' + projet()),
        S.API.get('/api/projects/' + projet())
      ]);
      const lignes = d.indicateurs.lignes;
      const processusActifs = !!projetCourant.show_process_indicators;
      const nbProcessus = d.indicateurs.nb_processus_disponibles || 0;
      const html = '<div class="barre-outils">' +
        '<input type="search" id="recherche-indicateur" placeholder="Rechercher un indicateur…">' +
        '<select id="filtre-niveau"><option value="">Tous les niveaux</option>' +
        ref('niveaux').map((n) => '<option value="' + n.code + '">' + ech(n.libelle) + '</option>').join('') +
        '</select>' +
        '<select id="filtre-statut"><option value="">Tous les statuts</option>' +
        ['Atteint', 'En bonne voie', 'À surveiller', 'Critique', 'Non renseigné']
          .map((s) => '<option>' + s + '</option>').join('') + '</select>' +
        '<select id="filtre-classe"><option value="">Toutes natures</option>' +
        '<option value="Résultat">Indicateurs de résultat</option>' +
        '<option value="Processus">Indicateurs de processus</option></select>' +
        '<label style="display:flex;align-items:center;gap:.35rem;font-size:.78rem;color:#5F6368">' +
        '<input type="checkbox" id="bascule-processus"' + (processusActifs ? ' checked' : '') +
        '> Afficher les indicateurs d\'activité / processus' +
        (nbProcessus ? ' (' + nbProcessus + ')' : '') + '</label>' +
        '<span style="font-size:.78rem;color:#5F6368">' + lignes.length + ' indicateurs — taux moyen ' +
        (d.indicateurs.taux_moyen === null ? '—' : S.nombre(d.indicateurs.taux_moyen, 1) + ' %') + '</span>' +
        '</div>' +
        (!processusActifs && nbProcessus ?
          '<div class="alerte alerte-info"><span class="type">Masqués</span><span>' + nbProcessus +
          ' indicateur(s) d\'activité / de processus sont enregistrés mais non affichés. ' +
          'Activez la case ci-dessus pour les intégrer aux tableaux de bord, analyses et ' +
          'livrables.</span></div>' : '') +
        '<div id="liste-indicateurs"></div>';
      conteneur.innerHTML = S.carte('Liste des indicateurs', html);

      document.getElementById('bascule-processus').addEventListener('change', async function (e) {
        S.basculeChargement(true);
        try {
          await S.API.put('/api/projects/' + projet(),
            { show_process_indicators: e.target.checked });
          S.notifier(e.target.checked ?
            'Indicateurs de processus affichés dans l\'ensemble de la plateforme.' :
            'Indicateurs de processus masqués (les données restent enregistrées).', 'succes');
          global.Application.rafraichir();
        } catch (erreur) {
          S.notifier(erreur.message, 'erreur');
        } finally {
          S.basculeChargement(false);
        }
      });

      function afficher() {
        const recherche = (document.getElementById('recherche-indicateur').value || '').toLowerCase();
        const niveau = document.getElementById('filtre-niveau').value;
        const statut = document.getElementById('filtre-statut').value;
        const classe = document.getElementById('filtre-classe').value;
        const filtrees = lignes.filter(function (l) {
          if (niveau && l.level !== niveau) return false;
          if (statut && l.statut !== statut) return false;
          if (classe && (l.classe || 'Résultat') !== classe) return false;
          if (recherche && (l.name + ' ' + (l.code || '')).toLowerCase().indexOf(recherche) < 0) return false;
          return true;
        });
        const zone = document.getElementById('liste-indicateurs');
        zone.innerHTML = S.tableau([
          { titre: 'Code', rendu: (l) => (l.is_key ? '⭐ ' : '') + ech(l.code || '') },
          { cle: 'name', titre: 'Indicateur' },
          { titre: 'Nature', classe: 'centre', rendu: (l) => (l.classe === 'Processus' ?
            '<span class="etiquette" style="background:#7B1FA2">Processus</span>' :
            '<span class="etiquette pale">Résultat</span>') },
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
      ['recherche-indicateur', 'filtre-niveau', 'filtre-statut', 'filtre-classe'].forEach(
        function (id) { document.getElementById(id).addEventListener('input', afficher); });
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
      { nom: 'dependencies', libelle: 'Activités prérequises (codes séparés par des virgules)',
        aide: 'Relation fin-début : cette activité ne démarre qu\'une fois les activités citées achevées. Alimente le chemin critique et le réseau PERT.' },
      { nom: 'duration_days', libelle: 'Durée imposée (jours)', type: 'number', largeur: 'courte',
        aide: 'Laisser vide pour déduire la durée des dates de début et de fin.' },
      { nom: 'wbs_code', libelle: 'Code WBS', largeur: 'courte',
        aide: 'Renseigné automatiquement par la fonction de codification de l\'organigramme.' },
      { nom: 'milestone', libelle: 'Jalon', type: 'checkbox', texteCase: 'Cette activité constitue un jalon' },
      { nom: 'deliverable', libelle: 'Livrable attendu', type: 'textarea', lignes: 2 }
    ];
  }

  const activites = {
    titre: 'Chronogramme et ordonnancement',
    sousTitre: 'Gantt, chemin critique, réseau PERT, organigramme des tâches et matrice RACI',
    onglet: 'gantt',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Activité</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="excel">⬇️ Gantt</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="cpm">⬇️ Chemin critique</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="wbs">⬇️ WBS</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="raci">⬇️ RACI</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="organisation">⬇️ Word</button>',
    gestionnairesBarre: {
      ajouter: () => activites.ouvrirFormulaire(null),
      excel: () => S.API.telecharger('/api/exports/' + projet() + '/chronogramme-excel'),
      cpm: () => S.API.telecharger('/api/exports/' + projet() + '/chemin-critique-excel'),
      wbs: () => S.API.telecharger('/api/exports/' + projet() + '/wbs-excel'),
      raci: () => S.API.telecharger('/api/exports/' + projet() + '/raci-excel'),
      organisation: () => S.API.telecharger('/api/exports/' + projet() + '/organisation-word')
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
      const o = d.ordonnancement;

      conteneur.innerHTML =
        '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Durée du projet', S.nombre(o.duree_projet_jours, 0) + ' j',
          S.nombre(o.duree_projet_mois, 1) + ' mois — ' + S.dateFr(o.date_debut) + ' → ' +
          S.dateFr(o.date_fin_calculee), '#1F4E79') +
        S.kpi('Activités critiques', o.nb_critiques,
          S.nombre(o.part_critique, 0) + ' % des activités — marge nulle',
          o.nb_critiques ? '#D93025' : '#0F9D58') +
        S.kpi('Marge moyenne', S.nombre(o.marge_moyenne, 1) + ' j',
          'Sur les activités non critiques') +
        S.kpi('Avancement moyen', S.nombre(s.avancement_moyen, 1) + ' %',
          s.achevees + ' / ' + s.total + ' activités achevées', '#0F9D58') +
        S.kpi('Activités en retard', s.nb_en_retard, 'Échéance dépassée',
          s.nb_en_retard ? '#D93025' : '#0F9D58') +
        S.kpi('Jalons', s.jalons.length, 'Points de contrôle', '#EA8600') +
        '</div>' +
        (o.ecart_calendrier_jours !== null && Math.abs(o.ecart_calendrier_jours) > 15 ?
          '<div class="alerte alerte-' + (o.ecart_calendrier_jours > 0 ? 'danger' : 'info') +
          '"><span class="type">Calendrier</span><span>La date de fin calculée par ' +
          'l\'ordonnancement est ' + (o.ecart_calendrier_jours > 0 ? 'postérieure de ' : 'antérieure de ') +
          Math.abs(o.ecart_calendrier_jours) + ' jours à la date de clôture planifiée (' +
          S.dateFr(o.date_fin_planifiee) + ').</span></div>' : '') +
        (o.avertissements || []).map((a) => '<div class="alerte alerte-warning"><span>' +
          ech(a) + '</span></div>').join('') +
        '<div class="onglets" id="onglets-planification">' +
        [['gantt', '📅 Diagramme de Gantt'], ['cpm', '🔗 Chemin critique et PERT'],
         ['wbs', '🗂️ Organigramme des tâches'], ['raci', '👥 Matrice RACI'],
         ['liste', '📋 Liste des activités']]
          .map(([cle, libelle]) => '<button data-onglet="' + cle + '"' +
            (activites.onglet === cle ? ' class="actif"' : '') + '>' + libelle + '</button>').join('') +
        '</div><div id="contenu-planification"></div>';

      conteneur.querySelectorAll('#onglets-planification button').forEach(function (bouton) {
        bouton.addEventListener('click', function () {
          activites.onglet = bouton.dataset.onglet;
          conteneur.querySelectorAll('#onglets-planification button').forEach(
            (b) => b.classList.toggle('actif', b.dataset.onglet === activites.onglet));
          activites.afficherOnglet(d);
        });
      });
      await activites.afficherOnglet(d);
    },

    afficherOnglet: async function (d) {
      const zone = document.getElementById('contenu-planification');
      if (!zone) return;
      const o = d.ordonnancement;

      if (activites.onglet === 'gantt') {
        let html = S.carte('Diagramme de Gantt', G.gantt(d.activites));
        if (d.synthese.en_retard.length) {
          html += S.carte('Activités en retard', d.synthese.en_retard.map((a) =>
            '<div class="alerte alerte-warning"><span class="type">' + ech(a.code || '') + '</span>' +
            '<span>' + ech(a.name) + ' — échéance du ' + S.dateFr(a.end_date) + ' dépassée de ' +
            a.retard_jours + ' jours (' + S.nombre(a.progress, 0) + ' % réalisé' +
            (a.responsible ? ', responsable : ' + ech(a.responsible) : '') + ')</span></div>').join(''));
        }
        zone.innerHTML = html;
        return;
      }

      if (activites.onglet === 'cpm') {
        const critiques = o.activites.filter((a) => a.critique);
        zone.innerHTML =
          S.carte('Chemin critique',
            (o.chemin_critique.length ?
              '<p style="font-size:.9rem"><strong>Séquence critique :</strong> ' +
              o.chemin_critique.map((c) => '<span class="etiquette" style="background:#D93025">' +
                ech(c) + '</span>').join(' <span style="color:#9AA0A6">→</span> ') + '</p>' +
              '<p style="font-size:.8rem;color:#5F6368">Tout retard sur l\'une de ces activités ' +
              'décale d\'autant la date d\'achèvement du projet. Elles représentent ' +
              S.nombre(o.cout_chemin_critique, 0) + ' de budget' +
              (o.avancement_chemin_critique !== null ? ' et sont réalisées à ' +
                S.nombre(o.avancement_chemin_critique, 1) + ' % en moyenne' : '') + '.</p>'
              : S.vide('Aucun chemin critique identifié : renseignez les antécédents des activités.', '🔗')) +
            S.tableau([
              { titre: 'Code', rendu: (l) => ech(l.code || '') },
              { cle: 'name', titre: 'Activité' },
              { cle: 'responsable', titre: 'Responsable' },
              { titre: 'Durée', classe: 'centre', rendu: (l) => l.duree + ' j' },
              { titre: 'Début → fin', classe: 'centre',
                rendu: (l) => S.dateFr(l.date_debut_tot) + ' → ' + S.dateFr(l.date_fin_tot) },
              { titre: 'Avancement', classe: 'centre', rendu: (l) => barreProgression(l.progress) }
            ], critiques)) +
          S.carte('Réseau PERT (activité sur nœud)', G.pert(o.activites),
            '', 'Les activités d\'un même rang sont indépendantes et peuvent être conduites en parallèle.') +
          S.carte('Tableau d\'ordonnancement complet', S.tableau([
            { titre: 'Code', rendu: (l) => (l.critique ? '🔴 ' : '') + ech(l.code || '') },
            { cle: 'name', titre: 'Activité' },
            { titre: 'Durée', classe: 'centre', rendu: (l) => l.duree + ' j' },
            { titre: 'Antécédents', rendu: (l) => l.antecedents.join(', ') || '—' },
            { titre: 'Successeurs', rendu: (l) => l.successeurs.join(', ') || '—' },
            { titre: 'Début tôt', classe: 'centre', rendu: (l) => S.dateFr(l.date_debut_tot) },
            { titre: 'Fin tôt', classe: 'centre', rendu: (l) => S.dateFr(l.date_fin_tot) },
            { titre: 'Début tard', classe: 'centre', rendu: (l) => S.dateFr(l.date_debut_tard) },
            { titre: 'Fin tard', classe: 'centre', rendu: (l) => S.dateFr(l.date_fin_tard) },
            { titre: 'Marge totale', classe: 'centre', rendu: (l) =>
              '<span class="etiquette" style="background:' +
              (l.marge_totale <= 0 ? '#D93025' : l.marge_totale <= 15 ? '#F9A825' : '#0F9D58') +
              '">' + l.marge_totale + ' j</span>' },
            { titre: 'Marge libre', classe: 'centre', rendu: (l) => l.marge_libre + ' j' }
          ], o.activites),
          '', 'Marge totale : retard admissible sans décaler la fin du projet. Marge libre : retard admissible sans décaler l\'activité suivante.');
        return;
      }

      if (activites.onglet === 'wbs') {
        zone.innerHTML = '<div class="vide"><span class="icone">⏳</span>Construction de l\'organigramme…</div>';
        const arbre = await S.API.get('/api/planning/wbs/' + projet());
        zone.innerHTML =
          '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
          S.kpi('Niveaux de décomposition', arbre.nb_niveaux, 'Profondeur de l\'organigramme') +
          S.kpi('Lots de travail', arbre.nb_lots, 'Éléments élémentaires') +
          S.kpi('Coût consolidé', S.nombre(arbre.cout_total, 0), 'Somme remontée des lots', '#EA8600') +
          S.kpi('Activités non rattachées', arbre.activites_non_rattachees,
            'Regroupées en gestion et coordination',
            arbre.activites_non_rattachees ? '#F9A825' : '#0F9D58') +
          '</div>' +
          S.carte('Organigramme des tâches', G.wbs(arbre.racines, arbre.projet.code),
            '<button class="btn btn-secondaire btn-petit" id="codifier-wbs">🔢 Inscrire les codes WBS sur les activités</button>',
            'Décomposition du projet en composantes, sous-composantes et lots de travail.') +
          S.carte('Décomposition détaillée', S.tableau([
            { titre: 'Code WBS', classe: 'centre', rendu: (l) => '<strong>' + ech(l.wbs) + '</strong>' },
            { titre: 'Nature', rendu: (l) => '<span class="etiquette pale">' + ech(l.type) + '</span>' },
            { titre: 'Libellé', rendu: (l) => '<span style="padding-left:' +
              (l.profondeur * 14) + 'px">' + (l.profondeur <= 1 ? '<strong>' : '') +
              ech(l.libelle) + (l.profondeur <= 1 ? '</strong>' : '') + '</span>' },
            { cle: 'responsable', titre: 'Responsable' },
            { titre: 'Durée', classe: 'centre', rendu: (l) => l.duree ? l.duree + ' j' : '—' },
            { titre: 'Coût', classe: 'nombre', rendu: (l) => S.nombre(l.cout, 0) },
            { titre: 'Part', classe: 'centre', rendu: (l) => arbre.cout_total ?
              S.nombre(l.cout / arbre.cout_total * 100, 1) + ' %' : '—' },
            { titre: 'Avancement', classe: 'centre', rendu: (l) => barreProgression(l.avancement) },
            { titre: 'Livrable', rendu: (l) => ech(l.livrable || '—') }
          ], arbre.lignes));
        const bouton = document.getElementById('codifier-wbs');
        if (bouton) bouton.addEventListener('click', async function () {
          S.basculeChargement(true);
          try {
            const r = await S.API.post('/api/planning/wbs/' + projet() + '/codifier', {});
            S.notifier(r.activites_codifiees + ' activités codifiées.', 'succes');
          } catch (e) { S.notifier(e.message, 'erreur'); }
          finally { S.basculeChargement(false); }
        });
        return;
      }

      if (activites.onglet === 'raci') {
        zone.innerHTML = '<div class="vide"><span class="icone">⏳</span>Construction de la matrice…</div>';
        await activites.rendreRaci(zone);
        return;
      }

      // Onglet « liste »
      zone.innerHTML = S.carte('Liste des activités', S.tableau([
        { titre: 'Code', rendu: (l) => (l.milestone ? '◆ ' : '') + ech(l.code || '') },
        { cle: 'name', titre: 'Activité' },
        { cle: 'resultat', titre: 'Résultat rattaché' },
        { cle: 'responsible', titre: 'Responsable' },
        { titre: 'Antécédents', rendu: (l) => ech(l.dependencies || '—') },
        { titre: 'Durée', classe: 'centre', rendu: (l) => (l.duree_calculee || 0) + ' j' },
        { titre: 'Début', rendu: (l) => S.dateFr(l.start_date) },
        { titre: 'Fin', rendu: (l) => S.dateFr(l.end_date) },
        { titre: 'Avancement', classe: 'centre', rendu: (l) => barreProgression(l.progress) },
        { cle: 'status', titre: 'Statut', classe: 'centre' },
        { titre: 'Coût prévu', classe: 'nombre', rendu: (l) => S.nombre(l.planned_cost, 0) }
      ], d.activites, [
        { cle: 'modifier', libelle: '✏️' },
        { cle: 'supprimer', libelle: '🗑️', classe: 'btn-danger' }
      ]));
      S.brancherActions(zone, {
        modifier: async (id) => activites.ouvrirFormulaire(await S.API.get('/api/activities/' + id)),
        supprimer: (id) => S.confirmer('Supprimer cette activité ?', async function () {
          await S.API.supprimer('/api/activities/' + id);
          S.notifier('Activité supprimée.', 'succes');
          global.Application.rafraichir();
        })
      });
    },

    rendreRaci: async function (zone) {
      const m = await S.API.get('/api/planning/raci/' + projet());
      const roles = ['', 'R', 'A', 'C', 'I'];

      let matrice = '';
      if (!m.nb_parties) {
        matrice = S.vide('Aucune partie prenante déclarée. Commencez par recenser les acteurs du projet, puis attribuez-leur un rôle sur chaque activité.', '👥');
      } else {
        matrice = '<div class="tableau-conteneur"><table class="tableau" style="min-width:' +
          (420 + m.nb_parties * 92) + 'px"><thead><tr>' +
          '<th style="min-width:70px">Code</th><th style="min-width:250px">Activité</th>' +
          m.parties_prenantes.map((p) => '<th class="centre" style="min-width:88px">' +
            ech(p.nom) + '</th>').join('') +
          '<th class="centre">Cohérence</th></tr></thead><tbody>' +
          m.activites.map(function (a) {
            return '<tr><td>' + ech(a.code || '') + '</td><td>' + ech(a.libelle) + '</td>' +
              m.parties_prenantes.map(function (p) {
                const role = a.roles[p.id] || a.roles[String(p.id)] || '';
                return '<td class="centre"><select data-activite="' + a.id + '" data-partie="' +
                  p.id + '" style="width:66px;padding:.2rem;border-radius:5px;border:1px solid ' +
                  '#E4E8EE;font-weight:700;text-align:center;background:' +
                  (role ? m.couleurs[role] : '#fff') + ';color:' + (role ? '#fff' : '#1F2933') + '">' +
                  roles.map((r) => '<option value="' + r + '"' + (r === role ? ' selected' : '') +
                    '>' + (r || '—') + '</option>').join('') + '</select></td>';
              }).join('') +
              '<td class="centre">' + (a.conforme ?
                '<span style="color:#0F9D58;font-weight:700">✔</span>' :
                '<span class="etiquette" style="background:#EA8600">' +
                (a.nb_a === 0 ? 'sans A' : a.nb_a > 1 ? a.nb_a + ' A' : 'sans R') + '</span>') +
              '</td></tr>';
          }).join('') + '</tbody></table></div>' +
          '<div class="legende" style="margin-top:.7rem">' +
          Object.keys(m.roles).map((r) => '<span><i style="background:' + m.couleurs[r] +
            '"></i><strong>' + r + '</strong> — ' + ech(m.roles[r].description) + '</span>').join('') +
          '</div>';
      }

      zone.innerHTML =
        '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Parties prenantes', m.nb_parties, 'Acteurs recensés') +
        S.kpi('Couverture des activités', S.nombre(m.taux_couverture, 0) + ' %',
          'Activités dotées d\'au moins un rôle',
          m.taux_couverture >= 90 ? '#0F9D58' : '#EA8600') +
        S.kpi('Conformité RACI', S.nombre(m.taux_conformite, 0) + ' %',
          m.activites_conformes + ' / ' + m.nb_activites + ' activités conformes',
          m.taux_conformite >= 90 ? '#0F9D58' : m.taux_conformite >= 60 ? '#F9A825' : '#D93025') +
        S.kpi('Anomalies', m.anomalies.length, 'À corriger',
          m.anomalies.length ? '#D93025' : '#0F9D58') +
        '</div>' +
        S.carte('Matrice des responsabilités', matrice,
          '<button class="btn btn-primaire btn-petit" id="ajouter-partie">➕ Partie prenante</button>',
          'Un seul approbateur (A) par activité, au moins un réalisateur (R). Modifiez directement les cellules.') +
        (m.anomalies.length ? S.carte('Contrôle de cohérence (' + m.anomalies.length + ')',
          m.anomalies.map((a) => '<div class="alerte alerte-' + a.gravite +
            '"><span class="type">' + ech(a.activite) + '</span><span>' +
            ech(a.libelle) + ' — ' + ech(a.anomalie) + '</span></div>').join('')) : '') +
        (m.nb_parties ? S.carte('Charge par partie prenante', S.tableau([
          { cle: 'code', titre: 'Code' },
          { cle: 'nom', titre: 'Partie prenante' },
          { cle: 'organisation', titre: 'Organisation' },
          { cle: 'categorie', titre: 'Catégorie', classe: 'centre' },
          { titre: 'R', classe: 'centre', rendu: (l) => l.R },
          { titre: 'A', classe: 'centre', rendu: (l) => '<strong>' + l.A + '</strong>' },
          { titre: 'C', classe: 'centre', rendu: (l) => l.C },
          { titre: 'I', classe: 'centre', rendu: (l) => l.I },
          { titre: 'Total', classe: 'centre', rendu: (l) => l.total },
          { titre: 'Couverture', classe: 'centre', rendu: (l) => S.nombre(l.taux_couverture, 0) + ' %' }
        ], m.parties_prenantes, [
          { cle: 'modifier-pp', libelle: '✏️' },
          { cle: 'supprimer-pp', libelle: '🗑️', classe: 'btn-danger' }
        ])) : '');

      document.getElementById('ajouter-partie').addEventListener('click',
        () => activites.formulairePartiePrenante(null));

      zone.querySelectorAll('select[data-activite]').forEach(function (select) {
        select.addEventListener('change', async function () {
          select.style.background = select.value ? m.couleurs[select.value] : '#fff';
          select.style.color = select.value ? '#fff' : '#1F2933';
          try {
            await S.API.post('/api/planning/raci/' + projet() + '/cellule', {
              activity_id: parseInt(select.dataset.activite, 10),
              stakeholder_id: parseInt(select.dataset.partie, 10),
              role: select.value
            });
            await activites.rendreRaci(zone);
          } catch (erreur) {
            S.notifier(erreur.message, 'erreur');
          }
        });
      });

      S.brancherActions(zone, {
        'modifier-pp': async (id) => activites.formulairePartiePrenante(
          await S.API.get('/api/stakeholders/' + id)),
        'supprimer-pp': (id) => S.confirmer(
          'Supprimer cette partie prenante et toutes ses affectations RACI ?', async function () {
            await S.API.supprimer('/api/stakeholders/' + id);
            S.notifier('Partie prenante supprimée.', 'succes');
            await activites.rendreRaci(zone);
          })
      });
    },

    formulairePartiePrenante: function (partie) {
      S.formulaireModal(partie ? 'Modifier la partie prenante' : 'Nouvelle partie prenante', [
        { nom: 'code', libelle: 'Code', largeur: 'courte' },
        { nom: 'category', libelle: 'Catégorie', type: 'select', largeur: 'courte',
          options: ['Interne', 'Tutelle', 'Partenaire d\'exécution', 'Prestataire',
                    'Bailleur', 'Bénéficiaire', 'Collectivité'] },
        { nom: 'name', libelle: 'Fonction ou structure', obligatoire: true },
        { nom: 'organisation', libelle: 'Organisation de rattachement' },
        { nom: 'contact', libelle: 'Contact', largeur: 'courte' },
        { nom: 'order_index', libelle: 'Ordre d\'affichage', type: 'number', largeur: 'courte' }
      ], partie || { category: 'Interne' }, async function (donnees) {
        donnees.project_id = projet();
        if (partie) await S.API.put('/api/stakeholders/' + partie.id, donnees);
        else await S.API.post('/api/stakeholders', donnees);
        S.notifier('Partie prenante enregistrée.', 'succes');
        await activites.rendreRaci(document.getElementById('contenu-planification'));
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
  /* 15. Saisie rapide (temps réel, orientée mobile)                      */
  /* =================================================================== */
  const saisie = {
    titre: 'Saisie des réalisations',
    sousTitre: 'Renseignement des indicateurs en temps réel, désagrégé et localisé',
    actions: () => '<button class="btn btn-secondaire btn-petit" data-barre="suivi">📈 Vue tableau</button>',
    gestionnairesBarre: { suivi: () => global.Application.naviguer('suivi') },
    contexte: null,
    ouvrirSaisie: function (indicateurId) {
      const contexte = saisie.contexte;
      const indicateur = contexte.indicateurs.find((i) => i.id === indicateurId);
      const categories = (indicateur.disaggregation || []).filter(
        (c) => (ref('modalites_desagregation') || {})[c]);
      const modalites = S.Etat.referentiels.modalites_desagregation || {};

      const formulaire = document.createElement('form');
      formulaire.innerHTML =
        '<div class="carte" style="box-shadow:none;border:1px solid var(--gris-clair);margin-bottom:.8rem">' +
        '<strong>' + ech(indicateur.code || '') + ' — ' + ech(indicateur.name) + '</strong>' +
        '<div style="font-size:.78rem;color:#5F6368;margin-top:.3rem">Unité : ' +
        ech(indicateur.unit || '—') + ' · Fréquence : ' + ech(indicateur.frequency || '—') +
        ' · Cible finale : ' + S.nombre(indicateur.target_value, 2) +
        ' · Consolidation : ' + ech(indicateur.derniere.agregation || 'somme') + '</div></div>' +
        '<div class="champ-groupe">' +
        '<div class="champ"><label for="s-periode">Période *</label>' +
        '<input list="liste-periodes" id="s-periode" value="' +
        ech(contexte.periodes[contexte.periodes.length - 1] || '') + '" required>' +
        '<datalist id="liste-periodes">' +
        contexte.periodes.map((p) => '<option value="' + ech(p) + '">').join('') +
        '</datalist><div class="aide">Format conseillé : 2025-T3, 2025-S1 ou 2025.</div></div>' +
        '<div class="champ"><label for="s-date">Date de référence</label>' +
        '<input type="date" id="s-date" value="' + new Date().toISOString().substring(0, 10) + '"></div>' +
        '<div class="champ"><label for="s-zone">Zone d\'intervention</label><select id="s-zone">' +
        '<option value="">— Niveau projet (non localisé) —</option>' +
        contexte.zones.map((z) => '<option value="' + z.id + '">' + ech(z.name) +
          ' (' + ech(z.level) + ')</option>').join('') + '</select></div>' +
        '<div class="champ"><label for="s-activite">Activité source</label><select id="s-activite">' +
        '<option value="">— Non précisée —</option>' +
        contexte.activites.map((a) => '<option value="' + a.id + '">' + ech(a.code || '') + ' ' +
          ech(a.name.substring(0, 50)) + '</option>').join('') + '</select></div>' +
        '</div>' +
        '<div class="champ"><label for="s-valeur">Valeur réalisée' +
        (categories.length ? ' (calculée automatiquement si vous ventilez ci-dessous)' : ' *') +
        '</label><input type="number" step="any" id="s-valeur"></div>' +
        (categories.length ? '<div class="section-formulaire">Ventilation des bénéficiaires</div>' +
          categories.map(function (categorie) {
            return '<div class="champ"><label>' + ech(categorie) + '</label>' +
              '<div class="champ-groupe" data-categorie="' + ech(categorie) + '">' +
              (modalites[categorie] || []).map(function (modalite) {
                return '<div class="champ"><label style="font-weight:400;font-size:.72rem">' +
                  ech(modalite) + '</label><input type="number" step="any" ' +
                  'data-modalite="' + ech(modalite) + '"></div>';
              }).join('') + '</div>' +
              '<div class="aide" data-total="' + ech(categorie) + '">Total : 0</div></div>';
          }).join('') : '') +
        '<div class="champ-groupe">' +
        '<div class="champ"><label for="s-source">Source de la donnée</label>' +
        '<input id="s-source" placeholder="Fiche de collecte, registre, enquête…"></div>' +
        '<div class="champ"><label for="s-statut">Statut de validation</label>' +
        '<select id="s-statut"><option>Brouillon</option><option selected>Validé</option>' +
        '<option>Rejeté</option></select></div></div>' +
        '<div class="champ"><label for="s-commentaire">Commentaire</label>' +
        '<textarea id="s-commentaire" rows="2"></textarea></div>';
      formulaire.addEventListener('submit', (e) => e.preventDefault());

      // La valeur globale se déduit de la première ventilation renseignée.
      function recalculer() {
        let premiereSomme = null;
        categories.forEach(function (categorie) {
          const bloc = formulaire.querySelector('[data-categorie="' + categorie + '"]');
          if (!bloc) return;
          let somme = 0;
          bloc.querySelectorAll('input').forEach(function (champ) {
            somme += parseFloat(String(champ.value).replace(',', '.')) || 0;
          });
          formulaire.querySelector('[data-total="' + categorie + '"]').textContent =
            'Total : ' + S.nombre(somme, 2);
          if (premiereSomme === null && somme > 0) premiereSomme = somme;
        });
        if (premiereSomme !== null) formulaire.querySelector('#s-valeur').value = premiereSomme;
      }
      formulaire.querySelectorAll('[data-categorie] input').forEach(function (champ) {
        champ.addEventListener('input', recalculer);
      });

      S.ouvrirModale('Saisir une réalisation', formulaire, [
        { libelle: 'Annuler', classe: 'btn-secondaire', action: S.fermerModale },
        {
          libelle: 'Enregistrer', classe: 'btn-primaire', action: async function () {
            const periode = formulaire.querySelector('#s-periode').value.trim();
            if (!periode) { S.notifier('La période est obligatoire.', 'erreur'); return; }
            const ventilation = {};
            categories.forEach(function (categorie) {
              const bloc = formulaire.querySelector('[data-categorie="' + categorie + '"]');
              if (!bloc) return;
              const valeurs = {};
              bloc.querySelectorAll('input').forEach(function (champ) {
                const nombre = parseFloat(String(champ.value).replace(',', '.'));
                if (!isNaN(nombre)) valeurs[champ.dataset.modalite] = nombre;
              });
              if (Object.keys(valeurs).length) ventilation[categorie] = valeurs;
            });
            const valeurBrute = formulaire.querySelector('#s-valeur').value;
            if (!valeurBrute && !Object.keys(ventilation).length) {
              S.notifier('Renseignez une valeur ou une ventilation.', 'erreur');
              return;
            }
            S.basculeChargement(true);
            try {
              const resultat = await S.API.post('/api/indicators/' + indicateurId + '/saisie', {
                period_label: periode,
                year: parseInt(periode.substring(0, 4), 10) || null,
                reference_date: formulaire.querySelector('#s-date').value || null,
                value: valeurBrute === '' ? null : parseFloat(String(valeurBrute).replace(',', '.')),
                zone_id: parseInt(formulaire.querySelector('#s-zone').value, 10) || null,
                activity_id: parseInt(formulaire.querySelector('#s-activite').value, 10) || null,
                disaggregated_values: ventilation,
                source: formulaire.querySelector('#s-source').value || null,
                validation_status: formulaire.querySelector('#s-statut').value,
                comment: formulaire.querySelector('#s-commentaire').value || null
              });
              S.notifier((resultat.creee ? 'Mesure créée' : 'Mesure mise à jour') +
                ' — taux de la période : ' +
                (resultat.performance.taux === null ? '—' : S.nombre(resultat.performance.taux, 1) + ' %'),
                'succes');
              S.fermerModale();
              global.Application.rafraichir();
            } catch (erreur) {
              S.notifier(erreur.message, 'erreur');
            } finally {
              S.basculeChargement(false);
            }
          }
        }
      ], true);
      recalculer();
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const contexte = await S.API.get('/api/saisie/contexte/' + projet());
      saisie.contexte = contexte;

      conteneur.innerHTML =
        '<div class="carte"><div class="barre-outils">' +
        '<input type="search" id="recherche-saisie" placeholder="Rechercher un indicateur à renseigner…">' +
        '<select id="filtre-saisie"><option value="">Tous les indicateurs</option>' +
        '<option value="cles">Indicateurs clés uniquement</option>' +
        '<option value="vides">Non encore renseignés</option>' +
        '<option value="retard">À actualiser (statut critique ou à surveiller)</option>' +
        '</select>' +
        '<span style="font-size:.78rem;color:#5F6368">' + contexte.zones.length +
        ' zone(s) · ' + contexte.activites.length + ' activité(s) disponibles</span>' +
        '</div><div id="liste-saisie"></div></div>';

      function afficher() {
        const recherche = (document.getElementById('recherche-saisie').value || '').toLowerCase();
        const filtre = document.getElementById('filtre-saisie').value;
        const lignes = contexte.indicateurs.filter(function (i) {
          if (filtre === 'cles' && !i.is_key) return false;
          if (filtre === 'vides' && i.derniere.actual_value !== null) return false;
          if (filtre === 'retard' && ['Atteint', 'En bonne voie'].indexOf(i.derniere.statut) >= 0) return false;
          if (recherche && (i.name + ' ' + (i.code || '')).toLowerCase().indexOf(recherche) < 0) return false;
          return true;
        });
        const zone = document.getElementById('liste-saisie');
        zone.innerHTML = S.tableau([
          { titre: 'Code', rendu: (l) => (l.is_key ? '⭐ ' : '') + ech(l.code || '') },
          { cle: 'name', titre: 'Indicateur' },
          { titre: 'Niveau', classe: 'centre', rendu: (l) => badgeNiveau(l.level) },
          { cle: 'unit', titre: 'Unité', classe: 'centre' },
          { titre: 'Désagrégations', rendu: (l) => (l.disaggregation || []).join(', ') || '—' },
          { titre: 'Dernière période', classe: 'centre', rendu: (l) => ech(l.derniere.period_label || '—') },
          { titre: 'Valeur consolidée', classe: 'nombre',
            rendu: (l) => S.nombre(l.derniere.actual_value, 2) +
              (l.derniere.nb_mesures_periode > 1 ?
                '<div style="font-size:.68rem;color:#5F6368">' + l.derniere.nb_mesures_periode +
                ' mesures (' + ech(l.derniere.agregation) + ')</div>' : '') },
          { titre: 'Statut', classe: 'centre', rendu: (l) => etiquetteStatut(l.derniere.statut) }
        ], lignes, [
          { cle: 'saisir', libelle: '✏️ Saisir', titre: 'Saisir une réalisation', classe: 'btn-primaire' }
        ]);
        S.brancherActions(zone, { saisir: (id) => saisie.ouvrirSaisie(id) });
      }
      ['recherche-saisie', 'filtre-saisie'].forEach(function (id) {
        document.getElementById(id).addEventListener('input', afficher);
      });
      afficher();
    }
  };

  /* =================================================================== */
  /* 16. Équité et données désagrégées                                    */
  /* =================================================================== */
  const equite = {
    titre: 'Équité et désagrégation',
    sousTitre: 'Ventilation par sexe, âge et groupe cible — inclusivité des interventions',
    actions: () => '<select id="periode-equite" class="btn btn-secondaire btn-petit"></select>' +
      '<button class="btn btn-primaire btn-petit" data-barre="excel">⬇️ Analyse Excel</button>',
    gestionnairesBarre: {
      excel: function () {
        const select = document.getElementById('periode-equite');
        const periode = select && select.value ? '?periode=' + encodeURIComponent(select.value) : '';
        S.API.telecharger('/api/exports/' + projet() + '/desagregation-excel' + periode);
      }
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const periodes = await S.API.get('/api/analyse/periodes/' + projet());
      const select = document.getElementById('periode-equite');
      if (select && !select.options.length) {
        select.innerHTML = '<option value="">Toutes périodes</option>' +
          periodes.existantes.map((p) => '<option value="' + ech(p) + '">' + ech(p) + '</option>').join('');
        select.addEventListener('change', () => equite.rendre(conteneur));
      }
      const periode = select && select.value ? '?periode=' + encodeURIComponent(select.value) : '';
      const d = await S.API.get('/api/analyse/desagregation/' + projet() + periode);
      const g = d.equite_genre;

      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Bénéficiaires identifiés', g ? S.nombre(g.total, 0) : '—',
          'Somme des ventilations par sexe') +
        S.kpi('Dont femmes', g ? S.nombre(g.femmes, 0) : '—',
          g ? S.nombre(g.part_femmes, 1) + ' % de l\'effectif' : 'Non renseigné', '#D81B60') +
        S.kpi('Dont hommes', g ? S.nombre(g.hommes, 0) : '—',
          g ? S.nombre(100 - g.part_femmes, 1) + ' % de l\'effectif' : 'Non renseigné', '#1E88E5') +
        S.kpi('Écart à la parité', g ? (g.ecart_parite > 0 ? '+' : '') + S.nombre(g.ecart_parite, 1) + ' pts' : '—',
          g ? g.appreciation : '—',
          g ? (Math.abs(g.ecart_parite) <= 5 ? '#0F9D58' : '#EA8600') : '#9AA0A6') +
        S.kpi('Taux de désagrégation', d.taux_desagregation === null ? '—' :
          S.nombre(d.taux_desagregation, 1) + ' %',
          d.indicateurs_desagreges + ' / ' + d.indicateurs_a_desagreger + ' indicateurs',
          d.taux_desagregation !== null && d.taux_desagregation >= 80 ? '#0F9D58' : '#EA8600') +
        '</div>';

      if (d.taux_desagregation !== null && d.taux_desagregation < 100) {
        html += '<div class="alerte alerte-warning" style="margin-bottom:1rem"><span class="type">Qualité</span>' +
          '<span>' + (d.indicateurs_a_desagreger - d.indicateurs_desagreges) +
          ' indicateur(s) exigent une désagrégation mais n\'en comportent aucune. ' +
          'Utilisez l\'écran « Saisie des réalisations » pour ventiler les effectifs.</span></div>';
      }

      if (!d.par_categorie.length) {
        html += S.carte('Analyse d\'équité',
          S.vide('Aucune donnée désagrégée n\'a encore été saisie. Renseignez la ventilation lors de la saisie des réalisations, ou importez-la depuis un classeur Excel.', '⚖️'));
      } else {
        html += '<div class="grille grille-2">';
        d.par_categorie.forEach(function (bloc) {
          const couleurs = bloc.categorie === 'Sexe' ? ['#D81B60', '#1E88E5'] : null;
          html += S.carte('Ventilation par « ' + bloc.categorie + ' »',
            G.anneau(bloc.modalites.map(function (m, index) {
              return { libelle: m.modalite, valeur: m.valeur,
                       couleur: couleurs ? couleurs[index % 2] : undefined };
            }), { centre: S.nombre(bloc.total, 0), legendeCentre: 'total' }) +
            S.tableau([
              { cle: 'modalite', titre: 'Modalité' },
              { titre: 'Valeur', classe: 'nombre', rendu: (l) => S.nombre(l.valeur, 2) },
              { titre: 'Part', classe: 'centre', rendu: (l) => S.nombre(l.part, 1) + ' %' }
            ], bloc.modalites) +
            (bloc.modalites_referentielles.length > bloc.modalites.length ?
              '<p style="font-size:.72rem;color:#EA8600;margin-top:.5rem">Modalités du référentiel non renseignées : ' +
              ech(bloc.modalites_referentielles.filter(
                (m) => !bloc.modalites.some((x) => x.modalite === m)).join(', ')) + '</p>' : ''));
        });
        html += '</div>';
      }

      html += S.carte('Détail par indicateur', S.tableau([
        { titre: 'Code', rendu: (l) => ech(l.code || '') },
        { cle: 'name', titre: 'Indicateur' },
        { titre: 'Désagrégations exigées', rendu: (l) => (l.categories_attendues || []).join(', ') || '—' },
        { titre: 'Manquantes', rendu: (l) => (l.categories_manquantes || []).length ?
          '<span class="etiquette" style="background:#EA8600">' +
          ech(l.categories_manquantes.join(', ')) + '</span>' : '<span style="color:#0F9D58">✔ complet</span>' },
        { titre: 'Femmes', classe: 'nombre', rendu: (l) => l.equite_genre ? S.nombre(l.equite_genre.femmes, 0) : '—' },
        { titre: 'Hommes', classe: 'nombre', rendu: (l) => l.equite_genre ? S.nombre(l.equite_genre.hommes, 0) : '—' },
        { titre: 'Part des femmes', classe: 'centre', rendu: (l) => l.equite_genre ?
          '<span class="etiquette" style="background:' +
          (Math.abs(l.equite_genre.ecart_parite) <= 5 ? '#0F9D58' :
           l.equite_genre.part_femmes < 45 ? '#EA8600' : '#2E75B6') + '">' +
          S.nombre(l.equite_genre.part_femmes, 1) + ' %</span>' : '—' },
        { titre: 'Mesures', classe: 'centre', rendu: (l) => l.nb_mesures }
      ], d.lignes));
      conteneur.innerHTML = html;
    }
  };

  /* =================================================================== */
  /* 17. Zones d'intervention                                             */
  /* =================================================================== */
  function champsZone(zones) {
    return [
      { nom: 'code', libelle: 'Code', largeur: 'courte' },
      { nom: 'name', libelle: 'Nom de la zone', obligatoire: true },
      { nom: 'level', libelle: 'Niveau', type: 'select', options: ref('niveaux_zone'), largeur: 'courte' },
      { nom: 'parent_id', libelle: 'Zone parente', type: 'select', largeur: 'courte',
        options: (zones || []).map((z) => ({ valeur: z.id, libelle: (z.code || '') + ' ' + z.name })) },
      { nom: 'population', libelle: 'Population totale', type: 'number', largeur: 'courte' },
      { nom: 'beneficiaries_target', libelle: 'Cible de bénéficiaires', type: 'number', largeur: 'courte' },
      { nom: 'latitude', libelle: 'Latitude', type: 'number', largeur: 'courte' },
      { nom: 'longitude', libelle: 'Longitude', type: 'number', largeur: 'courte' },
      { nom: 'responsible', libelle: 'Responsable de zone', largeur: 'courte' },
      { nom: 'order_index', libelle: 'Ordre d\'affichage', type: 'number', largeur: 'courte' },
      { nom: 'comment', libelle: 'Observations', type: 'textarea', lignes: 2 }
    ];
  }

  const zonesVue = {
    titre: 'Zones d\'intervention',
    sousTitre: 'Découpage géographique et consolidation territoriale des réalisations',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Zone</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="excel">⬇️ Consolidation Excel</button>',
    gestionnairesBarre: {
      ajouter: () => zonesVue.ouvrirFormulaire(null),
      excel: () => S.API.telecharger('/api/exports/' + projet() + '/zones-excel')
    },
    ouvrirFormulaire: async function (zone) {
      const zones = await S.API.get('/api/zones?project_id=' + projet());
      S.formulaireModal(zone ? 'Modifier la zone' : 'Nouvelle zone d\'intervention',
        champsZone(zones.filter((z) => !zone || z.id !== zone.id)),
        zone || { level: 'Région' }, async function (donnees) {
          donnees.project_id = projet();
          if (zone) await S.API.put('/api/zones/' + zone.id, donnees);
          else await S.API.post('/api/zones', donnees);
          S.notifier('Zone enregistrée.', 'succes');
          global.Application.rafraichir();
        }, true);
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/analyse/zones/' + projet());
      const c = d.zones;
      const actives = c.zones.filter((z) => z.id !== null);

      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Zones d\'intervention', c.nb_zones, 'Déclarées au projet') +
        S.kpi('Zones couvertes', c.zones_couvertes,
          c.taux_couverture_zones === null ? '—' : S.nombre(c.taux_couverture_zones, 0) + ' % de couverture',
          c.taux_couverture_zones !== null && c.taux_couverture_zones >= 80 ? '#0F9D58' : '#EA8600') +
        S.kpi('Mesures localisées', c.total_mesures - c.mesures_non_localisees,
          c.mesures_non_localisees + ' mesure(s) au niveau projet') +
        S.kpi('Activités documentées', d.activites.length, 'Avec données de collecte rattachées') +
        '</div>';

      const fondActif = localStorage.getItem('sepia_fond_carte') !== '0';
      html += S.carte('Carte de couverture du projet',
        G.carte(c.zones.filter((z) => z.id !== null), { fond: fondActif }),
        '<label style="display:flex;align-items:center;gap:.35rem;font-size:.76rem;color:#5F6368">' +
        '<input type="checkbox" id="bascule-fond-carte"' + (fondActif ? ' checked' : '') +
        '> Fond de carte</label>',
        'Chaque zone est figurée par un cercle dont la surface représente les bénéficiaires atteints et la couleur le taux de couverture.');

      if (actives.length) {
        html += S.carte('Bénéficiaires atteints par zone',
          G.barres(actives.map((z) => ({
            libelle: z.nom, valeur: z.beneficiaires_atteints,
            etiquette: S.nombre(z.beneficiaires_atteints, 0) +
              (z.taux_couverture !== null ? ' (' + S.nombre(z.taux_couverture, 0) + ' %)' : ''),
            couleur: z.taux_couverture === null ? '#5B9BD5' :
              z.taux_couverture >= 80 ? '#0F9D58' : z.taux_couverture >= 50 ? '#F9A825' : '#EA8600'
          })), { largeurLibelle: 200 }));

        const avecGenre = actives.filter((z) => z.equite_genre);
        if (avecGenre.length) {
          html += S.carte('Part des femmes par zone',
            G.barres(avecGenre.map((z) => ({
              libelle: z.nom, valeur: z.equite_genre.part_femmes,
              etiquette: S.nombre(z.equite_genre.part_femmes, 1) + ' %',
              couleur: Math.abs(z.equite_genre.ecart_parite) <= 5 ? '#0F9D58' :
                z.equite_genre.part_femmes < 45 ? '#EA8600' : '#1E88E5'
            })), { max: 100, largeurLibelle: 200 }),
            '', 'La ligne de parité se situe à 50 %.');
        }
      }

      html += S.carte('Zones d\'intervention et couverture', S.tableau([
        { cle: 'code', titre: 'Code' },
        { cle: 'nom', titre: 'Zone' },
        { cle: 'niveau', titre: 'Niveau', classe: 'centre' },
        { cle: 'responsable', titre: 'Responsable' },
        { titre: 'Population', classe: 'nombre', rendu: (l) => S.nombre(l.population, 0) },
        { titre: 'Cible bénéf.', classe: 'nombre', rendu: (l) => S.nombre(l.cible_beneficiaires, 0) },
        { titre: 'Atteints', classe: 'nombre', rendu: (l) => S.nombre(l.beneficiaires_atteints, 0) },
        { titre: 'Couverture', classe: 'centre', rendu: (l) => l.taux_couverture === null ? '—' :
          barreProgression(Math.min(l.taux_couverture, 100),
            l.taux_couverture >= 80 ? '#0F9D58' : '#EA8600') },
        { titre: 'Part des femmes', classe: 'centre', rendu: (l) => l.equite_genre ?
          S.nombre(l.equite_genre.part_femmes, 1) + ' %' : '—' },
        { titre: 'Mesures', classe: 'centre', rendu: (l) => l.nb_mesures }
      ], c.zones, [
        { cle: 'modifier', libelle: '✏️', condition: (l) => l.id !== null },
        { cle: 'supprimer', libelle: '🗑️', classe: 'btn-danger', condition: (l) => l.id !== null }
      ]));

      if (d.activites.length) {
        html += S.carte('Données collectées par activité', S.tableau([
          { cle: 'code', titre: 'Code' },
          { cle: 'libelle', titre: 'Activité' },
          { cle: 'responsable', titre: 'Responsable' },
          { titre: 'Avancement', classe: 'centre', rendu: (l) => barreProgression(l.avancement) },
          { titre: 'Indicateurs renseignés', rendu: (l) => l.indicateurs.map(
            (i) => ech(i.code) + ' = ' + S.nombre(i.valeur, 2) + ' ' + ech(i.unite || '')).join('<br>') || '—' },
          { titre: 'Part des femmes', classe: 'centre', rendu: (l) => l.equite_genre ?
            S.nombre(l.equite_genre.part_femmes, 1) + ' %' : '—' },
          { titre: 'Mesures', classe: 'centre', rendu: (l) => l.nb_mesures }
        ], d.activites),
        '', 'Le rattachement d\'une mesure à une activité permet de relier la collecte de données à la mise en œuvre.');
      }

      conteneur.innerHTML = html;

      const bascule = document.getElementById('bascule-fond-carte');
      if (bascule) {
        bascule.addEventListener('change', function () {
          localStorage.setItem('sepia_fond_carte', bascule.checked ? '1' : '0');
          if (bascule.checked) localStorage.removeItem('sepia_fond_indisponible');
          global.Application.rafraichir();
        });
      }
      G.surveillerFondCarte(conteneur, function () {
        if (bascule) bascule.checked = false;
      });

      S.brancherActions(conteneur, {
        modifier: async (id) => zonesVue.ouvrirFormulaire(await S.API.get('/api/zones/' + id)),
        supprimer: (id) => S.confirmer('Supprimer cette zone ? Les mesures qui y sont rattachées seront conservées sans localisation.',
          async function () {
            await S.API.supprimer('/api/zones/' + id);
            S.notifier('Zone supprimée.', 'succes');
            global.Application.rafraichir();
          })
      });
    }
  };

  /* =================================================================== */
  /* 18. Qualité SMART des indicateurs                                    */
  /* =================================================================== */
  const qualite = {
    titre: 'Qualité des indicateurs',
    sousTitre: 'Diagnostic SMART du système de mesure et actions correctrices',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="excel">⬇️ Revue Excel</button>',
    gestionnairesBarre: {
      excel: () => S.API.telecharger('/api/exports/' + projet() + '/qualite-smart-excel')
    },
    ouvrirRevue: async function (indicateurId, diagnostic) {
      const criteres = diagnostic.criteres;
      const formulaire = document.createElement('form');
      formulaire.innerHTML =
        '<p style="font-size:.82rem;color:#5F6368">Le contrôle automatique s\'appuie sur les ' +
        'informations saisies dans la fiche de l\'indicateur. Votre revue manuelle prévaut sur ce ' +
        'contrôle : cochez le critère si vous l\'estimez satisfait malgré le constat automatique.</p>' +
        criteres.map(function (critere) {
          return '<div class="carte" style="box-shadow:none;border:1px solid var(--gris-clair);padding:.7rem;margin-bottom:.6rem">' +
            '<label style="display:flex;gap:.6rem;align-items:flex-start;font-weight:400">' +
            '<input type="checkbox" data-critere="' + ech(critere.cle) + '"' +
            (critere.satisfait ? ' checked' : '') + ' style="margin-top:.25rem">' +
            '<span><strong>' + ech(critere.libelle) + '</strong><br>' +
            '<span style="font-size:.8rem">' + ech(critere.question) + '</span><br>' +
            '<span style="font-size:.74rem;color:#5F6368">Contrôle automatique : ' +
            ech(critere.controle) + ' → ' +
            (critere.automatique ? '<span style="color:#0F9D58">satisfait</span>' :
              '<span style="color:#D93025">non satisfait</span>') + '</span></span></label></div>';
        }).join('') +
        '<div class="champ"><label for="q-commentaire">Commentaire de revue</label>' +
        '<textarea id="q-commentaire" rows="3">' + ech(diagnostic.commentaire || '') + '</textarea></div>' +
        (diagnostic.recommandations.length ?
          '<div class="section-formulaire">Actions correctrices recommandées</div>' +
          diagnostic.recommandations.map((r) => '<div class="alerte alerte-warning"><span>' +
            ech(r) + '</span></div>').join('') : '');
      formulaire.addEventListener('submit', (e) => e.preventDefault());

      S.ouvrirModale('Revue SMART — ' + (diagnostic.code || '') + ' ' + diagnostic.name,
        formulaire, [
          { libelle: 'Fermer', classe: 'btn-secondaire', action: S.fermerModale },
          {
            libelle: 'Enregistrer la revue', classe: 'btn-primaire', action: async function () {
              const smart = {};
              formulaire.querySelectorAll('[data-critere]').forEach(function (champ) {
                smart[champ.dataset.critere] = champ.checked;
              });
              S.basculeChargement(true);
              try {
                const r = await S.API.post('/api/indicators/' + indicateurId + '/smart', {
                  smart_check: smart,
                  smart_comment: formulaire.querySelector('#q-commentaire').value || null
                });
                S.notifier('Revue enregistrée — score : ' + r.score + ' %', 'succes');
                S.fermerModale();
                global.Application.rafraichir();
              } catch (erreur) {
                S.notifier(erreur.message, 'erreur');
              } finally {
                S.basculeChargement(false);
              }
            }
          }
        ], true);
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/analyse/smart/' + projet());
      const couleurScore = d.score_systeme >= 90 ? '#0F9D58' : d.score_systeme >= 75 ? '#4CAF50' :
        d.score_systeme >= 60 ? '#F9A825' : '#D93025';

      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Score du système', S.nombre(d.score_systeme, 1) + ' %', d.appreciation, couleurScore) +
        S.kpi('Indicateurs évalués', d.total, 'Actifs dans le projet') +
        S.kpi('Pleinement conformes', d.conformes, 'Score ≥ 90 %', '#0F9D58') +
        S.kpi('À reprendre', d.a_reprendre, 'Score < 60 %', d.a_reprendre ? '#D93025' : '#0F9D58') +
        '</div>';

      html += '<div class="grille grille-2">' +
        S.carte('Score global du système d\'indicateurs',
          G.jauge(d.score_systeme, { libelle: 'Moyenne des scores SMART individuels' })) +
        S.carte('Conformité par critère SMART',
          G.barres(Object.keys(d.par_critere).map(function (critere) {
            const v = d.par_critere[critere];
            return { libelle: critere, valeur: v.taux,
                     etiquette: v.satisfaits + '/' + v.total + ' (' + S.nombre(v.taux, 0) + ' %)',
                     couleur: v.taux >= 90 ? '#0F9D58' : v.taux >= 70 ? '#F9A825' : '#D93025' };
          }), { max: 100, largeurLibelle: 175 })) +
        '</div>';

      html += S.carte('Diagnostic indicateur par indicateur', S.tableau([
        { titre: 'Code', rendu: (l) => (l.is_key ? '⭐ ' : '') + ech(l.code || '') },
        { cle: 'name', titre: 'Indicateur' },
        { titre: 'Niveau', classe: 'centre', rendu: (l) => badgeNiveau(l.level) },
        { titre: 'S', classe: 'centre', rendu: (l) => marqueCritere(l, 'specifique') },
        { titre: 'M', classe: 'centre', rendu: (l) => marqueCritere(l, 'mesurable') },
        { titre: 'A', classe: 'centre', rendu: (l) => marqueCritere(l, 'atteignable') },
        { titre: 'R', classe: 'centre', rendu: (l) => marqueCritere(l, 'pertinent') },
        { titre: 'T', classe: 'centre', rendu: (l) => marqueCritere(l, 'temporel') },
        { titre: 'Score', classe: 'centre', rendu: (l) => '<span class="etiquette" style="background:' +
          l.couleur + '">' + S.nombre(l.score, 0) + ' %</span>' },
        { titre: 'Actions recommandées', rendu: (l) => l.recommandations.length ?
          '<ul style="margin:0;padding-left:1rem">' +
          l.recommandations.map((r) => '<li style="font-size:.76rem">' + ech(r) + '</li>').join('') +
          '</ul>' : '<span style="color:#0F9D58">Aucune</span>' },
        { titre: 'Revue', classe: 'centre', rendu: (l) => l.revue_le ? S.dateFr(l.revue_le) : '—' }
      ], d.lignes, [
        { cle: 'revoir', libelle: '🔍', titre: 'Réaliser la revue SMART', classe: 'btn-primaire' },
        { cle: 'corriger', libelle: '✏️', titre: 'Corriger la fiche de l\'indicateur' }
      ]),
      '', 'S = Spécifique · M = Mesurable · A = Atteignable · R = Pertinent (Relevant) · T = Temporellement défini');

      conteneur.innerHTML = html;
      S.brancherActions(conteneur, {
        revoir: (id) => qualite.ouvrirRevue(id, d.lignes.find((l) => l.id === id)),
        corriger: async (id) => indicateurs.ouvrirFormulaire(await S.API.get('/api/indicators/' + id), null)
      });
    }
  };

  function marqueCritere(ligne, cle) {
    const critere = ligne.criteres.find((c) => c.cle === cle);
    if (!critere) return '—';
    return critere.satisfait ? '<span style="color:#0F9D58;font-weight:700">✔</span>' :
      '<span style="color:#D93025;font-weight:700">✘</span>';
  }

  /* =================================================================== */
  /* 19. Rapports périodiques                                             */
  /* =================================================================== */
  const rapports = {
    titre: 'Rapports périodiques',
    sousTitre: 'Production automatisée des rapports trimestriels, semestriels et annuels',
    actions: () => '',
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const periodes = await S.API.get('/api/analyse/periodes/' + projet());
      const trimestres = periodes.suggerees.filter((p) => p.indexOf('-T') > 0);
      const semestres = periodes.suggerees.filter((p) => p.indexOf('-S') > 0);
      const annees = periodes.suggerees.filter((p) => p.indexOf('-') < 0);
      const defautT = [...trimestres].reverse().find((p) => periodes.existantes.indexOf(p) >= 0) ||
        trimestres[0] || '';
      const defautS = [...semestres].reverse().find((p) => periodes.existantes.indexOf(p) >= 0) ||
        semestres[0] || '';
      const defautA = [...annees].reverse().find((p) => periodes.existantes.indexOf(p) >= 0) ||
        annees[0] || '';

      function selecteur(id, liste, defaut) {
        return '<select id="' + id + '">' + liste.map((p) => '<option value="' + ech(p) + '"' +
          (p === defaut ? ' selected' : '') + '>' + ech(p) +
          (periodes.existantes.indexOf(p) >= 0 ? ' — données disponibles' : '') +
          '</option>').join('') + '</select>';
      }

      conteneur.innerHTML =
        S.carte('Générer un rapport de suivi-évaluation',
          '<p style="font-size:.85rem">Chaque rapport est produit à partir des données de la ' +
          'période choisie : performance des indicateurs, analyse d\'équité, consolidation par ' +
          'zone, exécution physique et financière, difficultés et mesures correctrices, qualité ' +
          'du dispositif, et bloc de validation à signer.</p>' +
          '<div class="grille grille-3">' +
          '<div class="livrable"><span class="format format-Word">Word</span>' +
          '<h4>Rapport trimestriel de suivi</h4>' +
          '<p>Suivi rapproché des produits et de l\'exécution.</p>' +
          selecteur('periode-trimestre', trimestres, defautT) +
          '<button class="btn btn-primaire btn-petit" data-rapport="trimestriel">⬇️ Générer</button></div>' +
          '<div class="livrable"><span class="format format-Word">Word</span>' +
          '<h4>Rapport semestriel d\'avancement</h4>' +
          '<p>Bilan intermédiaire destiné au comité technique.</p>' +
          selecteur('periode-semestre', semestres, defautS) +
          '<button class="btn btn-primaire btn-petit" data-rapport="semestriel">⬇️ Générer</button></div>' +
          '<div class="livrable"><span class="format format-Word">Word</span>' +
          '<h4>Rapport annuel de performance</h4>' +
          '<p>Bilan consolidé pour le comité de pilotage et le bailleur.</p>' +
          selecteur('periode-annee', annees, defautA) +
          '<button class="btn btn-primaire btn-petit" data-rapport="annuel">⬇️ Générer</button></div>' +
          '</div>') +
        '<div id="apercu-periode"></div>';

      conteneur.querySelectorAll('[data-rapport]').forEach(function (bouton) {
        bouton.addEventListener('click', function () {
          const type = bouton.dataset.rapport;
          const select = document.getElementById('periode-' +
            { trimestriel: 'trimestre', semestriel: 'semestre', annuel: 'annee' }[type]);
          S.API.telecharger('/api/exports/' + projet() + '/rapport-' + type + '-word?periode=' +
            encodeURIComponent(select.value));
        });
      });

      ['periode-trimestre', 'periode-semestre', 'periode-annee'].forEach(function (id) {
        const select = document.getElementById(id);
        if (select) select.addEventListener('change', () => rapports.apercu(select.value));
      });
      rapports.apercu(defautT || defautA);
    },
    apercu: async function (periode) {
      const zone = document.getElementById('apercu-periode');
      if (!zone || !periode) return;
      zone.innerHTML = '<div class="vide"><span class="icone">⏳</span>Calcul de la période…</div>';
      try {
        const d = await S.API.get('/api/analyse/periode/' + projet() +
          '?periode=' + encodeURIComponent(periode));
        const g = d.equite_genre;
        let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
          S.kpi('Période analysée', ech(d.periode), d.total_indicateurs + ' indicateurs concernés') +
          S.kpi('Taux moyen d\'atteinte', d.taux_moyen === null ? '—' : S.nombre(d.taux_moyen, 1) + ' %',
            d.renseignes + ' indicateur(s) renseignés',
            d.taux_moyen === null ? '#9AA0A6' : S.couleurStatut(
              d.taux_moyen >= 100 ? 'Atteint' : d.taux_moyen >= 85 ? 'En bonne voie' :
              d.taux_moyen >= 60 ? 'À surveiller' : 'Critique')) +
          S.kpi('Bénéficiaires de la période', g ? S.nombre(g.total, 0) : '—',
            g ? S.nombre(g.part_femmes, 1) + ' % de femmes' : 'Ventilation non renseignée', '#D81B60') +
          S.kpi('Exécution financière', S.nombre(d.budget.taux_execution, 1) + ' %',
            'Exercice ' + (d.budget.annee || '—'), '#EA8600') +
          S.kpi('Écarts à traiter', d.alertes.length, 'Statut critique ou à surveiller',
            d.alertes.length ? '#D93025' : '#0F9D58') +
          '</div>';

        html += S.carte('Aperçu du rapport — performance de la période ' + d.periode,
          S.tableau([
            { titre: 'Code', rendu: (l) => (l.is_key ? '⭐ ' : '') + ech(l.code || '') },
            { cle: 'name', titre: 'Indicateur' },
            { titre: 'Niveau', classe: 'centre', rendu: (l) => badgeNiveau(l.level) },
            { titre: 'Période mesurée', classe: 'centre', rendu: (l) => ech(l.periode_mesure || '—') },
            { titre: 'Cible', classe: 'nombre', rendu: (l) => S.nombre(l.cible_periode, 2) },
            { titre: 'Réalisé', classe: 'nombre', rendu: (l) => S.nombre(l.realise_periode, 2) },
            { titre: 'Taux', classe: 'centre', rendu: (l) => l.taux === null ? '—' : S.nombre(l.taux, 1) + ' %' },
            { titre: 'Statut', classe: 'centre', rendu: (l) => etiquetteStatut(l.statut) },
            { titre: 'Part des femmes', classe: 'centre', rendu: (l) => l.equite_genre ?
              S.nombre(l.equite_genre.part_femmes, 1) + ' %' : '—' }
          ], d.lignes));

        const zonesActives = (d.zones.zones || []).filter((z) => z.nb_mesures && z.id !== null);
        if (zonesActives.length) {
          html += S.carte('Consolidation par zone sur la période',
            G.barres(zonesActives.map((z) => ({
              libelle: z.nom, valeur: z.beneficiaires_atteints,
              etiquette: S.nombre(z.beneficiaires_atteints, 0)
            })), { largeurLibelle: 200 }));
        }
        zone.innerHTML = html;
      } catch (erreur) {
        zone.innerHTML = '<div class="carte"><div class="alerte alerte-danger"><span>' +
          ech(erreur.message) + '</span></div></div>';
      }
    }
  };

  /* =================================================================== */
  global.Vues = {
    'saisie': saisie,
    'equite': equite,
    'zones': zonesVue,
    'qualite': qualite,
    'rapports': rapports,
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
