/* SEPIA — bénéficiaires, partenaires, évaluation CAD-OCDE et évaluation d'impact. */
(function (global) {
  'use strict';

  const S = global.SEPIA;
  const G = global.Graphiques;
  const ech = S.echapper;

  function projet() { return S.Etat.projetActif; }
  function ref(cle) { return S.Etat.referentiels[cle] || []; }
  function exigeProjet() {
    return S.vide('Sélectionnez d\'abord un projet dans le menu latéral.', '📁');
  }

  function barre(valeur, couleur) {
    const v = Math.max(0, Math.min(valeur || 0, 100));
    return '<div class="barre-progression"><span style="width:' + v + '%;background:' +
      (couleur || '#2E75B6') + '"></span></div>' +
      '<div style="font-size:.7rem;color:#5F6368;margin-top:2px">' +
      S.nombre(valeur || 0, 0) + ' %</div>';
  }

  /* =================================================================== */
  /* Bénéficiaires                                                        */
  /* =================================================================== */
  function champsBeneficiaire(zones) {
    return [
      { nom: 'code', libelle: 'Code', largeur: 'courte', section: 'Identification' },
      { nom: 'category', libelle: 'Catégorie', type: 'select', largeur: 'courte',
        options: ref('categories_beneficiaires'), section: 'Identification' },
      { nom: 'name', libelle: 'Intitulé du groupe de bénéficiaires', obligatoire: true,
        section: 'Identification' },
      { nom: 'typology', libelle: 'Typologie', type: 'select',
        options: ref('typologies_beneficiaires'), largeur: 'courte', section: 'Identification' },
      { nom: 'zone_id', libelle: 'Zone principale', type: 'select', largeur: 'courte',
        options: (zones || []).map((z) => ({ valeur: z.id, libelle: z.name })),
        section: 'Identification' },
      { nom: 'vulnerability_level', libelle: 'Niveau de vulnérabilité', type: 'select',
        options: ref('niveaux_vulnerabilite'), largeur: 'courte', section: 'Identification' },

      { nom: 'target_total', libelle: 'Effectif ciblé', type: 'number', largeur: 'courte',
        section: 'Ciblage quantitatif' },
      { nom: 'target_women', libelle: 'Dont femmes ciblées', type: 'number', largeur: 'courte',
        section: 'Ciblage quantitatif' },
      { nom: 'target_youth', libelle: 'Dont jeunes ciblés', type: 'number', largeur: 'courte',
        section: 'Ciblage quantitatif' },
      { nom: 'target_disabled', libelle: 'Dont personnes handicapées ciblées', type: 'number',
        largeur: 'courte', section: 'Ciblage quantitatif' },
      { nom: 'reached_total', libelle: 'Effectif atteint', type: 'number', largeur: 'courte',
        section: 'Ciblage quantitatif' },
      { nom: 'reached_women', libelle: 'Dont femmes atteintes', type: 'number', largeur: 'courte',
        section: 'Ciblage quantitatif' },
      { nom: 'reached_youth', libelle: 'Dont jeunes atteints', type: 'number', largeur: 'courte',
        section: 'Ciblage quantitatif' },
      { nom: 'reached_disabled', libelle: 'Dont personnes handicapées atteintes', type: 'number',
        largeur: 'courte', section: 'Ciblage quantitatif' },
      { nom: 'households', libelle: 'Nombre de ménages concernés', type: 'number',
        largeur: 'courte', section: 'Ciblage quantitatif' },
      { nom: 'average_household_size', libelle: 'Taille moyenne du ménage', type: 'number',
        largeur: 'courte', section: 'Ciblage quantitatif' },
      { nom: 'baseline_income', libelle: 'Revenu moyen de référence', type: 'number',
        largeur: 'courte', section: 'Ciblage quantitatif' },
      { nom: 'poverty_rate', libelle: 'Taux de pauvreté du groupe (%)', type: 'number',
        largeur: 'courte', section: 'Ciblage quantitatif' },

      { nom: 'selection_criteria', libelle: 'Critères d\'éligibilité', type: 'textarea',
        lignes: 3, section: 'Caractérisation qualitative' },
      { nom: 'selection_method', libelle: 'Méthode de ciblage', type: 'textarea', lignes: 2,
        section: 'Caractérisation qualitative',
        aide: 'Ciblage géographique, communautaire, catégoriel, auto-ciblage…' },
      { nom: 'needs', libelle: 'Besoins exprimés lors du diagnostic', type: 'textarea',
        lignes: 3, section: 'Caractérisation qualitative' },
      { nom: 'constraints', libelle: 'Contraintes d\'accès aux services du projet',
        type: 'textarea', lignes: 3, section: 'Caractérisation qualitative' },
      { nom: 'expected_benefits', libelle: 'Bénéfices attendus', type: 'textarea', lignes: 2,
        section: 'Caractérisation qualitative' },
      { nom: 'participation_mode', libelle: 'Modalités de participation à la mise en œuvre',
        type: 'textarea', lignes: 2, section: 'Caractérisation qualitative' },
      { nom: 'grievance_mechanism', libelle: 'Mécanisme de plainte accessible au groupe',
        type: 'textarea', lignes: 2, section: 'Caractérisation qualitative' },
      { nom: 'comment', libelle: 'Observations', type: 'textarea', lignes: 2,
        section: 'Caractérisation qualitative' },
      { nom: 'order_index', libelle: 'Ordre d\'affichage', type: 'number', largeur: 'courte',
        section: 'Caractérisation qualitative' }
    ];
  }

  const beneficiaires = {
    titre: 'Bénéficiaires',
    sousTitre: 'Ciblage, atteinte et caractérisation des groupes bénéficiaires',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Groupe</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="excel">⬇️ Excel</button>',
    gestionnairesBarre: {
      ajouter: () => beneficiaires.ouvrirFormulaire(null),
      excel: () => S.API.telecharger('/api/exports/' + projet() + '/beneficiaires-excel')
    },
    ouvrirFormulaire: async function (groupe) {
      const zones = await S.API.get('/api/zones?project_id=' + projet());
      S.formulaireModal(groupe ? 'Modifier le groupe de bénéficiaires' : 'Nouveau groupe',
        champsBeneficiaire(zones), groupe || { category: 'Direct' }, async function (donnees) {
          donnees.project_id = projet();
          if (groupe) await S.API.put('/api/beneficiaires/' + groupe.id, donnees);
          else await S.API.post('/api/beneficiaires', donnees);
          S.notifier('Groupe de bénéficiaires enregistré.', 'succes');
          global.Application.rafraichir();
        }, true);
    },
    ouvrirDetail: function (groupe) {
      const rubriques = [
        ['Critères d\'éligibilité', groupe.criteres_selection],
        ['Méthode de ciblage', groupe.methode_ciblage],
        ['Besoins exprimés', groupe.besoins],
        ['Contraintes d\'accès', groupe.contraintes],
        ['Bénéfices attendus', groupe.benefices_attendus],
        ['Participation à la mise en œuvre', groupe.participation],
        ['Mécanisme de plainte', groupe.mecanisme_plainte],
        ['Observations', groupe.commentaire]
      ].filter((r) => r[1]);
      const contenu =
        '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Effectif ciblé', S.nombre(groupe.cible_total, 0), groupe.typologie || '') +
        S.kpi('Effectif atteint', S.nombre(groupe.atteint_total, 0),
          groupe.taux_atteinte === null ? 'Taux non calculable' :
            S.nombre(groupe.taux_atteinte, 1) + ' % de la cible',
          groupe.taux_atteinte !== null && groupe.taux_atteinte >= 80 ? '#0F9D58' : '#EA8600') +
        S.kpi('Part des femmes atteintes',
          groupe.part_femmes_atteintes === null ? '—' :
            S.nombre(groupe.part_femmes_atteintes, 1) + ' %',
          S.nombre(groupe.atteint_femmes, 0) + ' femmes', '#D81B60') +
        S.kpi('Ménages concernés', S.nombre(groupe.menages, 0),
          groupe.personnes_touchees_estimees ?
            '≈ ' + S.nombre(groupe.personnes_touchees_estimees, 0) + ' personnes' : '') +
        '</div>' +
        '<div class="tableau-conteneur"><table class="tableau"><tbody>' +
        rubriques.map((r) => '<tr><td style="width:32%;background:#F7F8FA"><strong>' +
          ech(r[0]) + '</strong></td><td>' + ech(r[1]) + '</td></tr>').join('') +
        '</tbody></table></div>' +
        '<h4 style="margin-top:1rem">Indicateurs rattachés à ce groupe</h4>' +
        (groupe.indicateurs.length ? S.tableau([
          { titre: 'Code', rendu: (l) => ech(l.code || '') },
          { cle: 'name', titre: 'Indicateur' },
          { titre: 'Référence', classe: 'nombre', rendu: (l) => S.nombre(l.baseline_value, 2) },
          { titre: 'Cible', classe: 'nombre', rendu: (l) => S.nombre(l.target_value, 2) },
          { titre: 'Réalisé', classe: 'nombre', rendu: (l) => S.nombre(l.actual_value, 2) },
          { titre: 'Taux', classe: 'centre',
            rendu: (l) => l.taux === null ? '—' : S.nombre(l.taux, 1) + ' %' },
          { titre: 'Statut', classe: 'centre', rendu: (l) => '<span class="etiquette" style="background:' +
            S.couleurStatut(l.statut) + '">' + ech(l.statut) + '</span>' }
        ], groupe.indicateurs) :
          S.vide('Aucun indicateur n\'est rattaché à ce groupe. Le rattachement se fait depuis ' +
                 'la fiche de l\'indicateur, champ « Groupe de bénéficiaires ».', '🔗'));
      S.ouvrirModale((groupe.code || '') + ' — ' + groupe.nom, contenu, null, true);
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/beneficiaires/synthese/' + projet());

      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Groupes documentés', d.total_groupes, 'Directs, indirects et finaux') +
        S.kpi('Effectif ciblé', S.nombre(d.cible_totale, 0), 'Toutes catégories') +
        S.kpi('Effectif atteint', S.nombre(d.atteint_total, 0),
          d.taux_atteinte_global === null ? '—' :
            S.nombre(d.taux_atteinte_global, 1) + ' % de la cible',
          d.taux_atteinte_global !== null && d.taux_atteinte_global >= 80 ? '#0F9D58' : '#EA8600') +
        S.kpi('Part des femmes atteintes',
          d.part_femmes_atteinte === null ? '—' : S.nombre(d.part_femmes_atteinte, 1) + ' %',
          d.part_femmes_ciblee === null ? '' :
            'Ciblée : ' + S.nombre(d.part_femmes_ciblee, 1) + ' %', '#D81B60') +
        S.kpi('Personnes touchées estimées', S.nombre(d.personnes_touchees_estimees, 0),
          S.nombre(d.menages, 0) + ' ménages') +
        S.kpi('Indicateurs rattachés',
          d.taux_rattachement === null ? '—' : S.nombre(d.taux_rattachement, 0) + ' %',
          d.indicateurs_rattaches + ' rattachés, ' + d.indicateurs_non_rattaches + ' sans groupe',
          d.taux_rattachement !== null && d.taux_rattachement >= 70 ? '#0F9D58' : '#EA8600') +
        '</div>';

      if (d.indicateurs_non_rattaches) {
        html += '<div class="alerte alerte-warning" style="margin-bottom:1rem">' +
          '<span class="type">Rattachement</span><span>' + d.indicateurs_non_rattaches +
          ' indicateur(s) ne sont rattachés à aucun groupe de bénéficiaires. Le rattachement ' +
          'permet de mesurer la performance groupe par groupe et d\'objectiver l\'inclusion ' +
          'des plus vulnérables.</span></div>';
      }

      if (d.groupes.length) {
        html += S.carte('Ciblage et atteinte par groupe',
          G.barres(d.groupes.filter((g) => g.cible_total).map((g) => ({
            libelle: g.nom, valeur: g.taux_atteinte || 0,
            etiquette: S.nombre(g.atteint_total, 0) + ' / ' + S.nombre(g.cible_total, 0) +
              (g.taux_atteinte === null ? '' : ' (' + S.nombre(g.taux_atteinte, 0) + ' %)'),
            couleur: (g.taux_atteinte || 0) >= 80 ? '#0F9D58' :
              (g.taux_atteinte || 0) >= 50 ? '#F9A825' : '#EA8600'
          })), { max: 100, largeurLibelle: 220 }));
      }

      html += S.carte('Groupes de bénéficiaires', S.tableau([
        { cle: 'code', titre: 'Code' },
        { cle: 'nom', titre: 'Groupe' },
        { cle: 'categorie', titre: 'Catégorie', classe: 'centre' },
        { cle: 'typologie', titre: 'Typologie' },
        { cle: 'zone', titre: 'Zone' },
        { titre: 'Vulnérabilité', classe: 'centre', rendu: (l) => l.vulnerabilite ?
          '<span class="etiquette" style="background:' +
          ({ 'Très élevée': '#D93025', 'Élevée': '#EA8600', 'Moyenne': '#F9A825',
             'Faible': '#0F9D58' }[l.vulnerabilite] || '#9AA0A6') + '">' +
          ech(l.vulnerabilite) + '</span>' : '—' },
        { titre: 'Ciblé', classe: 'nombre', rendu: (l) => S.nombre(l.cible_total, 0) },
        { titre: 'Atteint', classe: 'nombre', rendu: (l) => S.nombre(l.atteint_total, 0) },
        { titre: 'Taux', classe: 'centre', rendu: (l) => l.taux_atteinte === null ? '—' :
          barre(l.taux_atteinte, l.taux_atteinte >= 80 ? '#0F9D58' : '#EA8600') },
        { titre: 'Femmes', classe: 'centre', rendu: (l) => l.part_femmes_atteintes === null ?
          '—' : S.nombre(l.part_femmes_atteintes, 1) + ' %' },
        { titre: 'Indicateurs', classe: 'centre', rendu: (l) => l.nb_indicateurs +
          (l.taux_moyen_indicateurs !== null ?
            '<div style="font-size:.68rem;color:#5F6368">' +
            S.nombre(l.taux_moyen_indicateurs, 0) + ' % moyen</div>' : '') }
      ], d.groupes, [
        { cle: 'detail', libelle: '👁️', titre: 'Fiche détaillée', classe: 'btn-primaire' },
        { cle: 'modifier', libelle: '✏️' },
        { cle: 'supprimer', libelle: '🗑️', classe: 'btn-danger' }
      ]));

      conteneur.innerHTML = html;
      S.brancherActions(conteneur, {
        detail: (id) => beneficiaires.ouvrirDetail(d.groupes.find((g) => g.id === id)),
        modifier: async (id) => beneficiaires.ouvrirFormulaire(
          await S.API.get('/api/beneficiaires/' + id)),
        supprimer: (id) => S.confirmer(
          'Supprimer ce groupe ? Les indicateurs rattachés seront conservés sans groupe.',
          async function () {
            await S.API.supprimer('/api/beneficiaires/' + id);
            S.notifier('Groupe supprimé.', 'succes');
            global.Application.rafraichir();
          })
      });
    }
  };

  /* =================================================================== */
  /* Partenaires                                                          */
  /* =================================================================== */
  function champsPartenaire() {
    return [
      { nom: 'code', libelle: 'Code', largeur: 'courte', section: 'Identification' },
      { nom: 'partner_type', libelle: 'Type de partenaire', type: 'select',
        options: ref('types_partenaire'), largeur: 'courte', section: 'Identification' },
      { nom: 'name', libelle: 'Nom du partenaire', obligatoire: true, section: 'Identification' },
      { nom: 'country', libelle: 'Pays', largeur: 'courte', section: 'Identification' },
      { nom: 'status', libelle: 'Statut', type: 'select', options: ref('statuts_partenaire'),
        largeur: 'courte', section: 'Identification' },
      { nom: 'role', libelle: 'Rôle dans le dispositif', type: 'textarea', lignes: 3,
        section: 'Identification' },

      { nom: 'agreement_reference', libelle: 'Référence de la convention', largeur: 'courte',
        section: 'Engagement contractuel' },
      { nom: 'agreement_start', libelle: 'Début de la convention', type: 'date',
        largeur: 'courte', section: 'Engagement contractuel' },
      { nom: 'agreement_end', libelle: 'Fin de la convention', type: 'date', largeur: 'courte',
        section: 'Engagement contractuel' },
      { nom: 'contribution_type', libelle: 'Type de contribution', type: 'select',
        options: ref('types_contribution'), largeur: 'courte',
        section: 'Engagement contractuel' },
      { nom: 'financial_commitment', libelle: 'Montant engagé', type: 'number', largeur: 'courte',
        section: 'Engagement contractuel' },
      { nom: 'financial_disbursed', libelle: 'Montant versé', type: 'number', largeur: 'courte',
        section: 'Engagement contractuel' },
      { nom: 'currency', libelle: 'Devise', largeur: 'courte', section: 'Engagement contractuel' },
      { nom: 'in_kind_description', libelle: 'Contribution en nature', type: 'textarea',
        lignes: 2, section: 'Engagement contractuel' },
      { nom: 'obligations', libelle: 'Obligations contractuelles', type: 'textarea', lignes: 3,
        section: 'Engagement contractuel' },
      { nom: 'deliverables', libelle: 'Livrables attendus', type: 'textarea', lignes: 2,
        section: 'Engagement contractuel' },

      { nom: 'performance_rating', libelle: 'Appréciation (1 à 5)', type: 'number',
        largeur: 'courte', section: 'Suivi de la relation' },
      { nom: 'performance_comment', libelle: 'Commentaire d\'appréciation', type: 'textarea',
        lignes: 2, section: 'Suivi de la relation' },
      { nom: 'risks', libelle: 'Risques liés au partenariat', type: 'textarea', lignes: 2,
        section: 'Suivi de la relation' },
      { nom: 'contact_name', libelle: 'Contact', largeur: 'courte',
        section: 'Suivi de la relation' },
      { nom: 'contact_email', libelle: 'Courriel', type: 'email', largeur: 'courte',
        section: 'Suivi de la relation' },
      { nom: 'contact_phone', libelle: 'Téléphone', largeur: 'courte',
        section: 'Suivi de la relation' },
      { nom: 'order_index', libelle: 'Ordre d\'affichage', type: 'number', largeur: 'courte',
        section: 'Suivi de la relation' }
    ];
  }

  const partenaires = {
    titre: 'Partenaires',
    sousTitre: 'Engagements, contributions et performance des partenaires du projet',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Partenaire</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="excel">⬇️ Excel</button>',
    gestionnairesBarre: {
      ajouter: () => partenaires.ouvrirFormulaire(null),
      excel: () => S.API.telecharger('/api/exports/' + projet() + '/partenaires-excel')
    },
    ouvrirFormulaire: function (partenaire) {
      S.formulaireModal(partenaire ? 'Modifier le partenaire' : 'Nouveau partenaire',
        champsPartenaire(), partenaire || { status: 'Actif', currency: 'FCFA' },
        async function (donnees) {
          donnees.project_id = projet();
          if (partenaire) await S.API.put('/api/partenaires/' + partenaire.id, donnees);
          else await S.API.post('/api/partenaires', donnees);
          S.notifier('Partenaire enregistré.', 'succes');
          global.Application.rafraichir();
        }, true);
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/partenaires/synthese/' + projet());

      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Partenaires', d.total, d.actifs + ' actifs') +
        S.kpi('Engagement cumulé', S.nombre(d.engagement_total, 0), 'Toutes conventions') +
        S.kpi('Montant versé', S.nombre(d.verse_total, 0),
          d.taux_decaissement_global === null ? '—' :
            S.nombre(d.taux_decaissement_global, 1) + ' % de l\'engagement', '#0F9D58') +
        S.kpi('Appréciation moyenne',
          d.note_moyenne === null ? '—' : S.nombre(d.note_moyenne, 2) + ' / 5',
          'Performance des partenaires',
          d.note_moyenne !== null && d.note_moyenne >= 4 ? '#0F9D58' : '#EA8600') +
        '</div>';

      if (Object.keys(d.par_type).length) {
        html += '<div class="grille grille-2">' +
          S.carte('Répartition par type de partenaire',
            G.anneau(Object.keys(d.par_type).map((t) => ({ libelle: t, valeur: d.par_type[t] })),
              { centre: d.total, legendeCentre: 'partenaires' })) +
          S.carte('Engagement et versement par partenaire',
            G.barres(d.partenaires.filter((p) => p.engage).map((p) => ({
              libelle: p.nom, valeur: p.taux_decaissement || 0,
              etiquette: S.nombre(p.verse, 0) + ' / ' + S.nombre(p.engage, 0),
              couleur: (p.taux_decaissement || 0) >= 50 ? '#0F9D58' : '#EA8600'
            })), { max: 100, largeurLibelle: 200 })) +
          '</div>';
      }

      html += S.carte('Partenaires du projet', S.tableau([
        { cle: 'code', titre: 'Code' },
        { cle: 'nom', titre: 'Partenaire' },
        { cle: 'type', titre: 'Type' },
        { cle: 'role', titre: 'Rôle' },
        { cle: 'convention', titre: 'Convention' },
        { titre: 'Période', rendu: (l) => S.dateFr(l.debut) + ' → ' + S.dateFr(l.fin) },
        { titre: 'Engagé', classe: 'nombre', rendu: (l) => S.nombre(l.engage, 0) },
        { titre: 'Versé', classe: 'nombre', rendu: (l) => S.nombre(l.verse, 0) },
        { titre: 'Décaissement', classe: 'centre', rendu: (l) => l.taux_decaissement === null ?
          '—' : barre(l.taux_decaissement, l.taux_decaissement >= 50 ? '#0F9D58' : '#EA8600') },
        { titre: 'Appréciation', classe: 'centre', rendu: (l) => l.note ?
          '<span class="etiquette" style="background:' +
          (l.note >= 4 ? '#0F9D58' : l.note >= 3 ? '#F9A825' : '#D93025') + '">' +
          l.note + '/5</span>' : '—' },
        { cle: 'statut', titre: 'Statut', classe: 'centre' }
      ], d.partenaires, [
        { cle: 'modifier', libelle: '✏️' },
        { cle: 'supprimer', libelle: '🗑️', classe: 'btn-danger' }
      ]));

      const risques = d.partenaires.filter((p) => p.risques);
      if (risques.length) {
        html += S.carte('Risques liés aux partenariats',
          risques.map((p) => '<div class="alerte alerte-warning"><span class="type">' +
            ech(p.nom) + '</span><span>' + ech(p.risques) + '</span></div>').join(''));
      }

      conteneur.innerHTML = html;
      S.brancherActions(conteneur, {
        modifier: async (id) => partenaires.ouvrirFormulaire(
          await S.API.get('/api/partenaires/' + id)),
        supprimer: (id) => S.confirmer('Supprimer ce partenaire ?', async function () {
          await S.API.supprimer('/api/partenaires/' + id);
          S.notifier('Partenaire supprimé.', 'succes');
          global.Application.rafraichir();
        })
      });
    }
  };

  /* =================================================================== */
  /* Évaluation selon les critères du CAD de l'OCDE                       */
  /* =================================================================== */
  function champsEvaluation() {
    return [
      { nom: 'code', libelle: 'Code', largeur: 'courte', section: 'Identification' },
      { nom: 'evaluation_type', libelle: 'Type d\'évaluation', type: 'select',
        options: ref('types_evaluation'), largeur: 'courte', section: 'Identification' },
      { nom: 'title', libelle: 'Intitulé de l\'évaluation', obligatoire: true,
        section: 'Identification' },
      { nom: 'period_covered', libelle: 'Période couverte', largeur: 'courte',
        section: 'Identification' },
      { nom: 'status', libelle: 'Statut', type: 'select', options: ref('statuts_evaluation'),
        largeur: 'courte', section: 'Identification' },
      { nom: 'start_date', libelle: 'Date de début', type: 'date', largeur: 'courte',
        section: 'Identification' },
      { nom: 'end_date', libelle: 'Date de fin', type: 'date', largeur: 'courte',
        section: 'Identification' },
      { nom: 'evaluator', libelle: 'Évaluateur', section: 'Conduite' },
      { nom: 'independence', libelle: 'Degré d\'indépendance', type: 'select',
        options: ref('independance'), largeur: 'courte', section: 'Conduite' },
      { nom: 'budget', libelle: 'Budget de l\'évaluation', type: 'number', largeur: 'courte',
        section: 'Conduite' },
      { nom: 'methodology', libelle: 'Méthodologie', type: 'textarea', lignes: 4,
        section: 'Conduite' },
      { nom: 'data_sources', libelle: 'Sources de données', type: 'textarea', lignes: 2,
        section: 'Conduite' },
      { nom: 'sampling', libelle: 'Échantillonnage', type: 'textarea', lignes: 2,
        section: 'Conduite' },
      { nom: 'limitations', libelle: 'Limites de l\'évaluation', type: 'textarea', lignes: 3,
        section: 'Conduite',
        aide: 'Énoncer les limites est une exigence de qualité : une évaluation sans limites '
              + 'déclarées est suspecte.' },
      { nom: 'report_reference', libelle: 'Référence du rapport', largeur: 'courte',
        section: 'Conduite' }
    ];
  }

  const evaluationCad = {
    titre: 'Évaluation CAD-OCDE',
    sousTitre: 'Appréciation selon les six critères et suivi des recommandations',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Évaluation</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="word">⬇️ Rapport Word</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="excel">⬇️ Excel</button>',
    gestionnairesBarre: {
      ajouter: () => evaluationCad.ouvrirFormulaire(null),
      word: () => S.API.telecharger('/api/exports/' + projet() + '/evaluation-cad-word'),
      excel: () => S.API.telecharger('/api/exports/' + projet() + '/evaluation-cad-excel')
    },
    ouvrirFormulaire: function (evaluation) {
      S.formulaireModal(evaluation ? 'Modifier l\'évaluation' : 'Nouvelle évaluation',
        champsEvaluation(), evaluation || { evaluation_type: 'Mi-parcours', status: 'Planifiée',
          independence: 'Externe indépendante' }, async function (donnees) {
          donnees.project_id = projet();
          if (evaluation) await S.API.put('/api/evaluations/' + evaluation.id, donnees);
          else await S.API.post('/api/evaluations', donnees);
          S.notifier('Évaluation enregistrée.', 'succes');
          global.Application.rafraichir();
        }, true);
    },
    ouvrirNotation: async function (evaluationId) {
      const d = await S.API.get('/api/evaluations/' + evaluationId + '/detail');
      const echelle = ref('echelle_cad');
      const formulaire = document.createElement('form');
      formulaire.innerHTML =
        '<p style="font-size:.84rem;color:#5F6368">Notez chaque critère de 1 à 6 et justifiez ' +
        'la note. Une note sans justification n\'a aucune valeur évaluative : elle ne peut être ' +
        'ni contestée, ni reprise dans un rapport.</p>' +
        '<div class="legende" style="margin-bottom:.8rem">' +
        echelle.map((e) => '<span><i style="background:' + e.couleur + '"></i>' + e.note +
          ' — ' + ech(e.libelle) + '</span>').join('') + '</div>' +
        d.criteres.map(function (critere) {
          return '<div class="carte" style="box-shadow:none;border:1px solid var(--gris-clair);' +
            'padding:.8rem;margin-bottom:.7rem">' +
            '<strong style="color:#1F4E79">' + ech(critere.libelle) + '</strong>' +
            '<p style="font-size:.8rem;margin:.3rem 0">' + ech(critere.question) + '</p>' +
            '<p style="font-size:.74rem;color:#5F6368">Points d\'examen : ' +
            ech(critere.points_examen) + '</p>' +
            '<div class="champ"><label>Note</label><select data-note="' + ech(critere.cle) + '">' +
            '<option value="">— Non noté —</option>' +
            echelle.map((e) => '<option value="' + e.note + '"' +
              (critere.note === e.note ? ' selected' : '') + '>' + e.note + ' — ' +
              ech(e.libelle) + '</option>').join('') + '</select></div>' +
            '<div class="champ"><label>Justification</label>' +
            '<textarea rows="3" data-justification="' + ech(critere.cle) + '">' +
            ech(critere.justification || '') + '</textarea></div></div>';
        }).join('') +
        '<div class="champ"><label>Constats principaux</label>' +
        '<textarea rows="3" id="ev-constats">' + ech(d.constats || '') + '</textarea></div>' +
        '<div class="champ"><label>Leçons apprises</label>' +
        '<textarea rows="3" id="ev-lecons">' + ech(d.lecons || '') + '</textarea></div>' +
        '<div class="champ"><label>Appréciation générale</label>' +
        '<textarea rows="3" id="ev-appreciation">' + ech(d.appreciation_generale || '') +
        '</textarea></div>';
      formulaire.addEventListener('submit', (e) => e.preventDefault());

      S.ouvrirModale('Notation CAD — ' + d.titre, formulaire, [
        { libelle: 'Annuler', classe: 'btn-secondaire', action: S.fermerModale },
        { libelle: 'Enregistrer', classe: 'btn-primaire', action: async function () {
          const scores = {}, justifications = {};
          formulaire.querySelectorAll('[data-note]').forEach(function (champ) {
            scores[champ.dataset.note] = champ.value ? parseFloat(champ.value) : null;
          });
          formulaire.querySelectorAll('[data-justification]').forEach(function (champ) {
            justifications[champ.dataset.justification] = champ.value;
          });
          S.basculeChargement(true);
          try {
            await S.API.post('/api/evaluations/' + evaluationId + '/notation', {
              scores: scores, justifications: justifications,
              key_findings: formulaire.querySelector('#ev-constats').value,
              lessons_learned: formulaire.querySelector('#ev-lecons').value,
              overall_comment: formulaire.querySelector('#ev-appreciation').value
            });
            S.notifier('Notation enregistrée.', 'succes');
            S.fermerModale();
            global.Application.rafraichir();
          } catch (erreur) {
            S.notifier(erreur.message, 'erreur');
          } finally {
            S.basculeChargement(false);
          }
        } }
      ], true);
    },
    ouvrirRecommandation: function (evaluationId, recommandation) {
      S.formulaireModal(recommandation ? 'Modifier la recommandation' : 'Nouvelle recommandation', [
        { nom: 'code', libelle: 'Code', largeur: 'courte' },
        { nom: 'criterion', libelle: 'Critère concerné', type: 'select', largeur: 'courte',
          options: (ref('criteres_cad') || []).map((c) => ({ valeur: c.cle, libelle: c.libelle })) },
        { nom: 'statement', libelle: 'Énoncé de la recommandation', type: 'textarea', lignes: 3,
          obligatoire: true },
        { nom: 'priority', libelle: 'Priorité', type: 'select', options: ref('priorites'),
          largeur: 'courte' },
        { nom: 'responsible', libelle: 'Responsable', largeur: 'courte' },
        { nom: 'deadline', libelle: 'Échéance', type: 'date', largeur: 'courte' },
        { nom: 'management_response', libelle: 'Réponse de la direction', type: 'select',
          options: ref('reponses_management'), largeur: 'courte' },
        { nom: 'response_comment', libelle: 'Commentaire de la direction', type: 'textarea',
          lignes: 2 },
        { nom: 'implementation_status', libelle: 'Statut de mise en œuvre', type: 'select',
          options: ref('statuts_recommandation'), largeur: 'courte' },
        { nom: 'implementation_rate', libelle: 'Taux de mise en œuvre (%)', type: 'number',
          largeur: 'courte' },
        { nom: 'evidence', libelle: 'Élément de preuve', type: 'textarea', lignes: 2 }
      ], recommandation || { priority: 'Moyenne', management_response: 'Acceptée',
        implementation_status: 'Non démarrée', implementation_rate: 0 },
        async function (donnees) {
          donnees.evaluation_id = evaluationId;
          if (recommandation) await S.API.put('/api/recommandations/' + recommandation.id, donnees);
          else await S.API.post('/api/recommandations', donnees);
          S.notifier('Recommandation enregistrée.', 'succes');
          global.Application.rafraichir();
        }, true);
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/evaluations/synthese/' + projet());

      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Exercices évaluatifs', d.total, d.achevees + ' achevés ou validés') +
        S.kpi('Note moyenne',
          d.note_moyenne === null ? '—' : S.nombre(d.note_moyenne, 2) + ' / 6',
          'Sur les évaluations achevées',
          d.note_moyenne === null ? '#9AA0A6' :
            d.note_moyenne >= 4.5 ? '#0F9D58' : d.note_moyenne >= 3.5 ? '#F9A825' : '#D93025') +
        S.kpi('Recommandations', d.nb_recommandations,
          d.taux_mise_en_oeuvre === null ? '—' :
            S.nombre(d.taux_mise_en_oeuvre, 0) + ' % mises en œuvre') +
        S.kpi('Recommandations en retard', d.recommandations_en_retard.length,
          'Échéance dépassée',
          d.recommandations_en_retard.length ? '#D93025' : '#0F9D58') +
        '</div>';

      const notes = Object.keys(d.par_critere).filter((c) => d.par_critere[c].moyenne !== null);
      if (notes.length) {
        html += S.carte('Notes moyennes par critère du CAD de l\'OCDE',
          G.barres(notes.map((critere) => ({
            libelle: critere, valeur: (d.par_critere[critere].moyenne / 6) * 100,
            etiquette: S.nombre(d.par_critere[critere].moyenne, 2) + ' / 6',
            couleur: d.par_critere[critere].couleur
          })), { max: 100, largeurLibelle: 175 }),
          '', 'Une note inférieure à 4 signale une dimension à traiter en priorité.');
      }

      if (d.recommandations_en_retard.length) {
        html += S.carte('Recommandations dont l\'échéance est dépassée',
          d.recommandations_en_retard.map((r) =>
            '<div class="alerte alerte-danger"><span class="type">' + ech(r.code || '') +
            '</span><span>' + ech(r.enonce) + ' — échéance du ' + S.dateFr(r.echeance) +
            ', mise en œuvre à ' + S.nombre(r.taux, 0) + ' %' +
            (r.responsable ? ' (responsable : ' + ech(r.responsable) + ')' : '') +
            '</span></div>').join(''));
      }

      d.evaluations.forEach(function (evaluation) {
        const notees = evaluation.criteres.filter((c) => c.note !== null);
        html += S.carte(
          ech(evaluation.code || '') + ' — ' + ech(evaluation.titre),
          '<div class="grille grille-kpi" style="margin-bottom:.8rem">' +
          S.kpi('Type', ech(evaluation.type), ech(evaluation.periode || '')) +
          S.kpi('Note globale',
            evaluation.note_globale === null ? '—' : S.nombre(evaluation.note_globale, 2) + ' / 6',
            evaluation.globale_libelle, evaluation.globale_couleur) +
          S.kpi('Critères notés', evaluation.criteres_notes + ' / 6',
            ech(evaluation.independance || '')) +
          S.kpi('Recommandations', evaluation.nb_recommandations,
            evaluation.taux_mise_en_oeuvre === null ? '—' :
              S.nombre(evaluation.taux_mise_en_oeuvre, 0) + ' % mises en œuvre') +
          '</div>' +
          (notees.length ? S.tableau([
            { titre: 'Critère', rendu: (l) => '<strong>' + ech(l.libelle) + '</strong>' },
            { titre: 'Note', classe: 'centre', rendu: (l) => l.note === null ? '—' :
              '<span class="etiquette" style="background:' + l.couleur + '">' + l.note +
              '/6 — ' + ech(l.libelle_note || '') + '</span>' },
            { titre: 'Appréciation', classe: 'centre', rendu: (l) => ech(l.libelle_note || '') },
            { titre: 'Justification', rendu: (l) => ech(l.justification || '—') }
          ], notees) : S.vide('Cette évaluation n\'est pas encore notée.', '📝')) +
          (evaluation.constats ? '<h4 style="margin-top:.8rem">Constats principaux</h4><p>' +
            ech(evaluation.constats) + '</p>' : '') +
          (evaluation.lecons ? '<h4>Leçons apprises</h4><p>' + ech(evaluation.lecons) + '</p>' : '') +
          (evaluation.limites ? '<h4>Limites déclarées</h4><p>' + ech(evaluation.limites) +
            '</p>' : '') +
          '<h4 style="margin-top:.8rem">Recommandations et suivi</h4>' +
          S.tableau([
            { titre: 'Code', rendu: (l) => ech(l.code || '') },
            { titre: 'Critère', rendu: (l) => ech(l.critere || '—') },
            { titre: 'Recommandation', rendu: (l) => ech(l.enonce) },
            { titre: 'Priorité', classe: 'centre', rendu: (l) => '<span class="etiquette" ' +
              'style="background:' + ({ 'Élevée': '#D93025', 'Moyenne': '#F9A825',
                'Faible': '#0F9D58' }[l.priorite] || '#9AA0A6') + '">' + ech(l.priorite) +
              '</span>' },
            { titre: 'Réponse', classe: 'centre', rendu: (l) => ech(l.reponse_management) },
            { cle: 'responsable', titre: 'Responsable' },
            { titre: 'Échéance', rendu: (l) => S.dateFr(l.echeance) },
            { titre: 'Mise en œuvre', classe: 'centre', rendu: (l) => barre(l.taux,
              l.taux >= 100 ? '#0F9D58' : '#EA8600') }
          ], evaluation.recommandations, [
            { cle: 'modifier-reco', libelle: '✏️' },
            { cle: 'supprimer-reco', libelle: '🗑️', classe: 'btn-danger' }
          ]),
          '<button class="btn btn-primaire btn-petit" data-noter="' + evaluation.id +
          '">📊 Noter les critères</button>' +
          '<button class="btn btn-secondaire btn-petit" data-reco="' + evaluation.id +
          '">➕ Recommandation</button>' +
          '<button class="btn btn-secondaire btn-petit" data-modifier-ev="' + evaluation.id +
          '">✏️ Modifier</button>',
          ech(evaluation.evaluateur || ''));
      });

      if (!d.evaluations.length) {
        html += S.carte('Évaluations',
          S.vide('Aucun exercice évaluatif n\'est enregistré. Créez-en un pour apprécier le ' +
                 'projet selon les six critères du CAD de l\'OCDE.', '🎓'));
      }

      conteneur.innerHTML = html;
      conteneur.querySelectorAll('[data-noter]').forEach((b) => b.addEventListener('click',
        () => evaluationCad.ouvrirNotation(parseInt(b.dataset.noter, 10))));
      conteneur.querySelectorAll('[data-reco]').forEach((b) => b.addEventListener('click',
        () => evaluationCad.ouvrirRecommandation(parseInt(b.dataset.reco, 10), null)));
      conteneur.querySelectorAll('[data-modifier-ev]').forEach((b) => b.addEventListener('click',
        async () => evaluationCad.ouvrirFormulaire(
          await S.API.get('/api/evaluations/' + b.dataset.modifierEv))));
      S.brancherActions(conteneur, {
        'modifier-reco': async (id) => {
          const reco = await S.API.get('/api/recommandations/' + id);
          evaluationCad.ouvrirRecommandation(reco.evaluation_id, reco);
        },
        'supprimer-reco': (id) => S.confirmer('Supprimer cette recommandation ?',
          async function () {
            await S.API.supprimer('/api/recommandations/' + id);
            S.notifier('Recommandation supprimée.', 'succes');
            global.Application.rafraichir();
          })
      });
    }
  };

  /* =================================================================== */
  /* Évaluation d'impact                                                  */
  /* =================================================================== */
  function champsImpact(indicateurs) {
    return [
      { nom: 'code', libelle: 'Code', largeur: 'courte', section: 'Identification' },
      { nom: 'status', libelle: 'Statut', type: 'select', options: ref('statuts_impact'),
        largeur: 'courte', section: 'Identification' },
      { nom: 'title', libelle: 'Intitulé de l\'étude', obligatoire: true,
        section: 'Identification' },
      { nom: 'research_question', libelle: 'Question de recherche', type: 'textarea', lignes: 3,
        section: 'Identification' },
      { nom: 'hypothesis', libelle: 'Hypothèse testée', type: 'textarea', lignes: 2,
        section: 'Identification' },

      { nom: 'approach', libelle: 'Approche', type: 'select', options: ref('approches_impact'),
        largeur: 'courte', section: 'Devis d\'évaluation' },
      { nom: 'method', libelle: 'Méthode d\'identification', type: 'select', largeur: 'courte',
        options: (ref('methodes_impact') || []).map((m) => m.libelle),
        section: 'Devis d\'évaluation' },
      { nom: 'identification_assumption', libelle: 'Hypothèse d\'identification', type: 'textarea',
        lignes: 3, section: 'Devis d\'évaluation',
        aide: 'C\'est la condition sous laquelle l\'effet estimé peut être interprété comme '
              + 'causal. Elle doit être énoncée explicitement et discutée.' },
      { nom: 'assignment_rule', libelle: 'Règle d\'affectation au traitement', type: 'textarea',
        lignes: 3, section: 'Devis d\'évaluation' },
      { nom: 'unit_of_analysis', libelle: 'Unité d\'analyse', largeur: 'courte',
        section: 'Devis d\'évaluation' },
      { nom: 'outcome_indicators', libelle: 'Indicateurs de résultat', type: 'multiselect',
        options: (indicateurs || []).map((i) => i.code).filter(Boolean),
        section: 'Devis d\'évaluation' },
      { nom: 'covariates', libelle: 'Variables de contrôle', type: 'textarea', lignes: 2,
        section: 'Devis d\'évaluation' },

      { nom: 'treatment_size', libelle: 'Effectif du groupe de traitement', type: 'number',
        largeur: 'courte', section: 'Échantillon et puissance' },
      { nom: 'control_size', libelle: 'Effectif du groupe de contrôle', type: 'number',
        largeur: 'courte', section: 'Échantillon et puissance' },
      { nom: 'clusters', libelle: 'Nombre de grappes', type: 'number', largeur: 'courte',
        section: 'Échantillon et puissance' },
      { nom: 'intra_cluster_correlation', libelle: 'Corrélation intra-grappe', type: 'number',
        largeur: 'courte', section: 'Échantillon et puissance' },
      { nom: 'minimum_detectable_effect', libelle: 'Effet minimal détectable', type: 'number',
        largeur: 'courte', section: 'Échantillon et puissance' },
      { nom: 'outcome_sd', libelle: "Écart-type de l'indicateur de résultat", type: 'number',
        largeur: 'courte', section: 'Échantillon et puissance',
        aide: "Exprimé dans la même unité que l'effet minimal. Sans lui, le contrôle de "
              + 'puissance ne peut être calculé.' },
      { nom: 'power', libelle: 'Puissance visée', type: 'number', largeur: 'courte',
        section: 'Échantillon et puissance' },
      { nom: 'significance_level', libelle: 'Seuil de signification', type: 'number',
        largeur: 'courte', section: 'Échantillon et puissance' },
      { nom: 'attrition_rate', libelle: 'Attrition anticipée', type: 'number', largeur: 'courte',
        section: 'Échantillon et puissance' },

      { nom: 'baseline_date', libelle: 'Mesure de référence', type: 'date', largeur: 'courte',
        section: 'Calendrier et résultats' },
      { nom: 'midline_date', libelle: 'Mesure intermédiaire', type: 'date', largeur: 'courte',
        section: 'Calendrier et résultats' },
      { nom: 'endline_date', libelle: 'Mesure finale', type: 'date', largeur: 'courte',
        section: 'Calendrier et résultats' },
      { nom: 'effect_estimate', libelle: 'Effet estimé', type: 'number', largeur: 'courte',
        section: 'Calendrier et résultats' },
      { nom: 'standard_error', libelle: 'Erreur type', type: 'number', largeur: 'courte',
        section: 'Calendrier et résultats' },
      { nom: 'p_value', libelle: 'Valeur p', type: 'number', largeur: 'courte',
        section: 'Calendrier et résultats' },
      { nom: 'confidence_interval', libelle: 'Intervalle de confiance', largeur: 'courte',
        section: 'Calendrier et résultats' },
      { nom: 'effect_unit', libelle: 'Unité de l\'effet', largeur: 'courte',
        section: 'Calendrier et résultats' },
      { nom: 'robustness_checks', libelle: 'Tests de robustesse', type: 'textarea', lignes: 3,
        section: 'Calendrier et résultats' },
      { nom: 'threats_to_validity', libelle: 'Menaces sur la validité', type: 'textarea',
        lignes: 3, section: 'Calendrier et résultats' },
      { nom: 'conclusion', libelle: 'Conclusion', type: 'textarea', lignes: 3,
        section: 'Calendrier et résultats' },
      { nom: 'ethical_clearance', libelle: 'Avis éthique et consentement', type: 'textarea',
        lignes: 3, section: 'Calendrier et résultats' },
      { nom: 'data_repository', libelle: 'Dépôt des données', largeur: 'courte',
        section: 'Calendrier et résultats' }
    ];
  }

  const impact = {
    titre: 'Évaluation d\'impact',
    sousTitre: 'Devis expérimentaux et quasi-expérimentaux, puissance et résultats',
    actions: () => '<button class="btn btn-primaire btn-petit" data-barre="ajouter">➕ Étude</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="calcul">🧮 Calcul d\'échantillon</button>' +
      '<button class="btn btn-secondaire btn-petit" data-barre="word">⬇️ Protocole Word</button>',
    gestionnairesBarre: {
      ajouter: () => impact.ouvrirFormulaire(null),
      calcul: () => impact.ouvrirCalculateur(),
      word: () => S.API.telecharger('/api/exports/' + projet() + '/evaluation-impact-word')
    },
    ouvrirFormulaire: async function (etude) {
      const indicateurs = await S.API.get('/api/indicators?project_id=' + projet());
      S.formulaireModal(etude ? 'Modifier l\'étude d\'impact' : 'Nouvelle étude d\'impact',
        champsImpact(indicateurs),
        etude || { approach: 'Quasi-expérimentale', power: 0.8, significance_level: 0.05,
          status: 'Conçue' }, async function (donnees) {
          donnees.project_id = projet();
          if (etude) await S.API.put('/api/etudes-impact/' + etude.id, donnees);
          else await S.API.post('/api/etudes-impact', donnees);
          S.notifier('Étude d\'impact enregistrée.', 'succes');
          global.Application.rafraichir();
        }, true);
    },
    ouvrirCalculateur: function () {
      const formulaire = S.construireFormulaire([
        { nom: 'effet_minimal', libelle: 'Effet minimal détectable', type: 'number',
          obligatoire: true, largeur: 'courte',
          aide: 'Exprimé dans l\'unité de l\'indicateur, ou en écarts-types.' },
        { nom: 'ecart_type', libelle: 'Écart-type de l\'indicateur', type: 'number',
          largeur: 'courte' },
        { nom: 'puissance', libelle: 'Puissance (0,80 usuelle)', type: 'number',
          largeur: 'courte' },
        { nom: 'alpha', libelle: 'Seuil de signification', type: 'number', largeur: 'courte' },
        { nom: 'ratio', libelle: 'Ratio traitement / contrôle', type: 'number',
          largeur: 'courte' },
        { nom: 'correlation_intra', libelle: 'Corrélation intra-grappe', type: 'number',
          largeur: 'courte', aide: 'Zéro si l\'assignation est individuelle.' },
        { nom: 'taille_grappe', libelle: 'Taille moyenne d\'une grappe', type: 'number',
          largeur: 'courte' }
      ], { ecart_type: 1, puissance: 0.8, alpha: 0.05, ratio: 1, correlation_intra: 0,
        taille_grappe: 1 });
      const resultat = document.createElement('div');
      resultat.id = 'resultat-echantillon';
      formulaire.appendChild(resultat);

      S.ouvrirModale('Calcul de la taille d\'échantillon', formulaire, [
        { libelle: 'Fermer', classe: 'btn-secondaire', action: S.fermerModale },
        { libelle: 'Calculer', classe: 'btn-primaire', action: async function () {
          const valeurs = S.lireFormulaire(formulaire, [
            { nom: 'effet_minimal', type: 'number' }, { nom: 'ecart_type', type: 'number' },
            { nom: 'puissance', type: 'number' }, { nom: 'alpha', type: 'number' },
            { nom: 'ratio', type: 'number' }, { nom: 'correlation_intra', type: 'number' },
            { nom: 'taille_grappe', type: 'number' }
          ]);
          if (!valeurs.effet_minimal) {
            S.notifier('Renseignez l\'effet minimal détectable.', 'erreur');
            return;
          }
          const parametres = Object.keys(valeurs)
            .filter((k) => valeurs[k] !== null && valeurs[k] !== undefined)
            .map((k) => k + '=' + encodeURIComponent(valeurs[k])).join('&');
          try {
            const r = await S.API.get('/api/impact/calcul-echantillon?' + parametres);
            if (r.erreur) { resultat.innerHTML = '<div class="alerte alerte-danger"><span>' +
              ech(r.erreur) + '</span></div>'; return; }
            resultat.innerHTML =
              '<div class="grille grille-kpi" style="margin-top:1rem">' +
              S.kpi('Groupe de traitement', S.nombre(r.n_traitement, 0), 'unités') +
              S.kpi('Groupe de contrôle', S.nombre(r.n_controle, 0), 'unités') +
              S.kpi('Échantillon total', S.nombre(r.n_total, 0), 'unités', '#1F4E79') +
              (r.grappes_requises ? S.kpi('Grappes requises', S.nombre(r.grappes_requises, 0),
                'effet de plan ' + S.nombre(r.effet_de_plan, 2)) : '') +
              '</div>' +
              '<div class="alerte alerte-warning"><span>' + ech(r.avertissement) + '</span></div>';
          } catch (erreur) {
            resultat.innerHTML = '<div class="alerte alerte-danger"><span>' +
              ech(erreur.message) + '</span></div>';
          }
        } }
      ], true);
    },
    ouvrirDetail: function (etude) {
      const methode = etude.methode_documentee;
      const rubriques = [
        ['Question de recherche', etude.question],
        ['Hypothèse testée', etude.hypothese],
        ['Hypothèse d\'identification', etude.hypothese_identification],
        ['Règle d\'affectation', etude.regle_affectation],
        ['Unité d\'analyse', etude.unite_analyse],
        ['Variables de contrôle', etude.covariables],
        ['Tests de robustesse', etude.tests_robustesse],
        ['Menaces sur la validité', etude.menaces_validite],
        ['Conclusion', etude.conclusion],
        ['Avis éthique', etude.ethique],
        ['Dépôt des données', etude.depot_donnees]
      ].filter((r) => r[1]);

      const contenu =
        '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Approche', ech(etude.approche || '—'), ech(etude.methode || '')) +
        S.kpi('Échantillon', S.nombre(etude.echantillon_total, 0),
          S.nombre(etude.traitement, 0) + ' traités / ' + S.nombre(etude.controle, 0) +
          ' témoins') +
        S.kpi('Effet estimé',
          etude.effet_estime === null || etude.effet_estime === undefined ? '—' :
            S.nombre(etude.effet_estime, 2),
          ech(etude.unite_effet || ''),
          etude.significatif === true ? '#0F9D58' : etude.significatif === false ?
            '#EA8600' : '#9AA0A6') +
        S.kpi('Signification',
          etude.p_value === null || etude.p_value === undefined ? '—' :
            'p = ' + S.nombre(etude.p_value, 3),
          etude.significatif === true ? 'Effet statistiquement significatif' :
            etude.significatif === false ? 'Non significatif' : 'Non encore estimé',
          etude.significatif === true ? '#0F9D58' : '#9AA0A6') +
        '</div>' +
        (methode ? '<div class="carte" style="box-shadow:none;border:1px solid var(--gris-clair)">' +
          '<h4 style="color:#1F4E79">' + ech(methode.libelle) + ' — ' + ech(methode.approche) +
          '</h4>' +
          '<p style="font-size:.84rem"><strong>Hypothèse de la méthode :</strong> ' +
          ech(methode.hypothese) + '</p>' +
          '<p style="font-size:.84rem"><strong>Conditions d\'application :</strong> ' +
          ech(methode.conditions) + '</p>' +
          '<p style="font-size:.84rem;color:#0F9D58"><strong>Forces :</strong> ' +
          ech(methode.forces) + '</p>' +
          '<p style="font-size:.84rem;color:#D93025"><strong>Limites :</strong> ' +
          ech(methode.limites) + '</p></div>' : '') +
        (etude.controle_puissance && etude.controle_puissance.indisponible ?
          '<div class="alerte alerte-warning"><span class="type">Puissance</span><span>' +
          'Contrôle indisponible : ' + ech(etude.controle_puissance.indisponible) +
          '</span></div>' :
        etude.controle_puissance ? '<div class="alerte alerte-' +
          (etude.controle_puissance.suffisant ? 'info' : 'warning') + '"><span class="type">' +
          'Puissance</span><span>Échantillon prévu : ' +
          S.nombre(etude.controle_puissance.n_prevu, 0) + ' unités ; requis pour détecter ' +
          'l\'effet minimal (écart-type ' +
          S.nombre(etude.controle_puissance.ecart_type, 2) + ', grappes de ' +
          S.nombre(etude.controle_puissance.taille_grappe, 0) + ' unités) : ' +
          S.nombre(etude.controle_puissance.n_requis, 0) +
          ' — effet de plan ' + S.nombre(etude.controle_puissance.effet_de_plan, 2) + '. ' +
          (etude.controle_puissance.suffisant ? 'L\'échantillon est suffisant.' :
            'L\'échantillon est insuffisant : l\'étude risque de conclure à l\'absence d\'effet ' +
            'alors qu\'un effet réel existe.') + '</span></div>' : '') +
        '<div class="tableau-conteneur"><table class="tableau"><tbody>' +
        rubriques.map((r) => '<tr><td style="width:30%;background:#F7F8FA"><strong>' +
          ech(r[0]) + '</strong></td><td>' + ech(r[1]) + '</td></tr>').join('') +
        '</tbody></table></div>' +
        (etude.indicateurs_resultat.length ?
          '<h4 style="margin-top:1rem">Indicateurs de résultat suivis</h4>' +
          S.tableau([
            { titre: 'Code', rendu: (l) => ech(l.code || '') },
            { cle: 'name', titre: 'Indicateur' },
            { titre: 'Référence', classe: 'nombre', rendu: (l) => S.nombre(l.baseline_value, 2) },
            { titre: 'Cible', classe: 'nombre', rendu: (l) => S.nombre(l.target_value, 2) },
            { titre: 'Réalisé', classe: 'nombre', rendu: (l) => S.nombre(l.actual_value, 2) }
          ], etude.indicateurs_resultat) : '');
      S.ouvrirModale((etude.code || '') + ' — ' + etude.titre, contenu, null, true);
    },
    rendre: async function (conteneur) {
      if (!projet()) { conteneur.innerHTML = exigeProjet(); return; }
      const d = await S.API.get('/api/impact/synthese/' + projet());

      let html = '<div class="grille grille-kpi" style="margin-bottom:1rem">' +
        S.kpi('Études d\'impact', d.total, d.analysees + ' analysées ou publiées') +
        S.kpi('Échantillon cumulé', S.nombre(d.echantillon_cumule, 0), 'unités d\'observation') +
        S.kpi('Effets significatifs', d.effets_significatifs,
          'Au seuil retenu par l\'étude',
          d.effets_significatifs ? '#0F9D58' : '#9AA0A6') +
        S.kpi('Approches', Object.keys(d.par_approche).length,
          Object.keys(d.par_approche).map((a) => a + ' : ' + d.par_approche[a]).join(' · ')) +
        '</div>';

      if (!d.etudes.length) {
        html += S.carte('Évaluation d\'impact',
          S.vide('Aucune étude d\'impact n\'est enregistrée. Le devis doit être conçu avant la ' +
                 'mesure de référence : après le démarrage des activités, la constitution d\'un ' +
                 'contrefactuel crédible devient beaucoup plus difficile.', '🔬'));
      } else {
        html += S.carte('Études d\'impact du projet', S.tableau([
          { titre: 'Code', rendu: (l) => ech(l.code || '') },
          { cle: 'titre', titre: 'Étude' },
          { titre: 'Approche', classe: 'centre', rendu: (l) => '<span class="etiquette" ' +
            'style="background:' + (l.approche === 'Expérimentale' ? '#0F9D58' :
              l.approche === 'Quasi-expérimentale' ? '#2E75B6' : '#EA8600') + '">' +
            ech(l.approche || '—') + '</span>' },
          { cle: 'methode', titre: 'Méthode' },
          { titre: 'Traitement', classe: 'nombre', rendu: (l) => S.nombre(l.traitement, 0) },
          { titre: 'Contrôle', classe: 'nombre', rendu: (l) => S.nombre(l.controle, 0) },
          { titre: 'Grappes', classe: 'centre', rendu: (l) => l.grappes || '—' },
          { titre: 'Effet', classe: 'nombre', rendu: (l) => l.effet_estime === null ||
            l.effet_estime === undefined ? '—' : S.nombre(l.effet_estime, 2) },
          { titre: 'p', classe: 'centre', rendu: (l) => l.p_value === null ||
            l.p_value === undefined ? '—' : S.nombre(l.p_value, 3) },
          { titre: 'Signification', classe: 'centre', rendu: (l) => l.significatif === true ?
            '<span class="etiquette" style="background:#0F9D58">Significatif</span>' :
            l.significatif === false ?
            '<span class="etiquette" style="background:#EA8600">Non significatif</span>' : '—' },
          { cle: 'statut', titre: 'Statut', classe: 'centre' }
        ], d.etudes, [
          { cle: 'detail', libelle: '👁️', titre: 'Fiche détaillée', classe: 'btn-primaire' },
          { cle: 'modifier', libelle: '✏️' },
          { cle: 'supprimer', libelle: '🗑️', classe: 'btn-danger' }
        ]));
      }

      html += S.carte('Méthodes d\'évaluation d\'impact — aide au choix',
        '<p style="font-size:.84rem">Le choix de la méthode dépend du mode d\'affectation au ' +
        'traitement et des données disponibles. Une comparaison avant-après ne constitue pas ' +
        'une évaluation d\'impact : elle ne permet pas d\'attribuer les changements observés à ' +
        'l\'intervention.</p>' +
        S.tableau([
          { titre: 'Méthode', rendu: (l) => '<strong>' + ech(l.libelle) + '</strong>' },
          { titre: 'Approche', classe: 'centre', rendu: (l) => '<span class="etiquette" ' +
            'style="background:' + (l.approche === 'Expérimentale' ? '#0F9D58' :
              l.approche === 'Quasi-expérimentale' ? '#2E75B6' : '#EA8600') + '">' +
            ech(l.approche) + '</span>' },
          { titre: 'Hypothèse d\'identification', rendu: (l) => ech(l.hypothese) },
          { titre: 'Conditions', rendu: (l) => ech(l.conditions) },
          { titre: 'Forces', rendu: (l) => ech(l.forces) },
          { titre: 'Limites', rendu: (l) => ech(l.limites) }
        ], (d.methodes || []).map((m, i) => Object.assign({ id: i }, m))));

      conteneur.innerHTML = html;
      S.brancherActions(conteneur, {
        detail: (id) => impact.ouvrirDetail(d.etudes.find((e) => e.id === id)),
        modifier: async (id) => impact.ouvrirFormulaire(
          await S.API.get('/api/etudes-impact/' + id)),
        supprimer: (id) => S.confirmer('Supprimer cette étude d\'impact ?', async function () {
          await S.API.supprimer('/api/etudes-impact/' + id);
          S.notifier('Étude supprimée.', 'succes');
          global.Application.rafraichir();
        })
      });
    }
  };

  global.VuesEvaluation = {
    'beneficiaires': beneficiaires,
    'partenaires': partenaires,
    'evaluation-cad': evaluationCad,
    'impact': impact
  };
})(window);
