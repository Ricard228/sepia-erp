/* SEPIA — amorçage, navigation et cycle de vie de l'application. */
(function (global) {
  'use strict';

  const S = global.SEPIA;

  const MENU = [
    { groupe: 'Pilotage' },
    { cle: 'tableau-de-bord', libelle: 'Tableau de bord', icone: '📊' },
    { cle: 'portefeuille', libelle: 'Portefeuille', icone: '🗂️' },
    { cle: 'projet', libelle: 'Fiche du projet', icone: '📁' },
    { groupe: 'Planification' },
    { cle: 'cadre-logique', libelle: 'Cadre logique', icone: '🧭' },
    { cle: 'indicateurs', libelle: 'Indicateurs', icone: '🎯' },
    { cle: 'beneficiaires', libelle: 'Bénéficiaires', icone: '👥' },
    { cle: 'partenaires', libelle: 'Partenaires', icone: '🤝' },
    { cle: 'zones', libelle: 'Zones d\'intervention', icone: '🗺️' },
    { cle: 'activites', libelle: 'Chronogramme', icone: '📅' },
    { cle: 'budget', libelle: 'PTBA et budget', icone: '💰' },
    { groupe: 'Collecte et suivi' },
    { cle: 'saisie', libelle: 'Saisir les réalisations', icone: '✏️' },
    { cle: 'suivi', libelle: 'Cadre de suivi', icone: '📈' },
    { cle: 'collecte', libelle: 'Fiches et questionnaires', icone: '📝' },
    { groupe: 'Analyse et évaluation' },
    { cle: 'equite', libelle: 'Équité et désagrégation', icone: '⚖️' },
    { cle: 'qualite', libelle: 'Qualité des indicateurs', icone: '🔍' },
    { cle: 'risques', libelle: 'Risques et hypothèses', icone: '⚠️' },
    { cle: 'evaluation-cad', libelle: 'Évaluation CAD-OCDE', icone: '🎓' },
    { cle: 'impact', libelle: 'Évaluation d\'impact', icone: '🔬' },
    { groupe: 'Rapportage' },
    { cle: 'rapports', libelle: 'Rapports périodiques', icone: '📑' },
    { cle: 'livrables', libelle: 'Livrables', icone: '📦' },
    { cle: 'powerbi', libelle: 'Power BI', icone: '⚡' },
    { cle: 'imports', libelle: 'Importer', icone: '⬆️' },
    { groupe: 'Système' },
    { cle: 'administration', libelle: 'Administration', icone: '⚙️' }
  ];

  const Application = {
    async demarrer() {
      document.getElementById('formulaire-connexion').addEventListener('submit', Application.connexion);
      document.getElementById('bouton-deconnexion').addEventListener('click', function () {
        S.deconnexion();
        location.hash = '';
      });
      document.getElementById('ouvrir-navigation').addEventListener('click', function () {
        document.getElementById('navigation').classList.add('ouverte');
      });
      document.getElementById('fermer-navigation').addEventListener('click', function () {
        document.getElementById('navigation').classList.remove('ouverte');
      });
      document.getElementById('select-projet').addEventListener('change', function (e) {
        Application.changerProjet(parseInt(e.target.value, 10));
        Application.rafraichir();
      });
      document.getElementById('fond-modale').addEventListener('click', function (e) {
        if (e.target.id === 'fond-modale') S.fermerModale();
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') S.fermerModale();
      });
      global.addEventListener('hashchange', function () {
        const cle = location.hash.replace('#', '') || 'tableau-de-bord';
        if (cle !== S.Etat.vue) Application.naviguer(cle);
      });

      // Lien de confirmation d'adresse : le jeton voyage dans le fragment, qui
      // n'est pas transmis au serveur dans l'URL ni inscrit dans ses journaux.
      await Application.confirmerAdresse();

      // La session est portée par un cookie inaccessible au script : on tente
      // simplement de lire le profil ; s'il répond, la session est ouverte.
      try {
        await Application.ouvrirSession();
        return;
      } catch (erreur) {
        S.Etat.connecte = false;
      }
      document.getElementById('ecran-connexion').classList.remove('masque');
    },

    async confirmerAdresse() {
      const correspondance = /^#verifier=([A-Za-z0-9_-]{16,})$/.exec(location.hash || '');
      if (!correspondance) return;
      location.hash = '';
      try {
        const reponse = await fetch('/api/auth/verifier-adresse', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin', body: JSON.stringify({ jeton: correspondance[1] })
        });
        const resultat = await reponse.json().catch(() => ({}));
        const zone = document.getElementById('erreur-connexion');
        if (zone) {
          zone.textContent = resultat.message || 'Adresse confirmée.';
          zone.classList.add('succes');
        }
      } catch (exception) {
        // Une confirmation impossible ne doit pas empêcher l'affichage de l'écran
        // de connexion : l'administrateur peut réémettre un lien.
      }
    },

    async connexion(evenement) {
      evenement.preventDefault();
      const erreur = document.getElementById('erreur-connexion');
      erreur.textContent = '';
      erreur.classList.remove('succes');
      const donnees = new FormData();
      donnees.append('username', document.getElementById('champ-email').value.trim().toLowerCase());
      donnees.append('password', document.getElementById('champ-motdepasse').value);
      S.basculeChargement(true);
      try {
        const reponse = await fetch('/api/auth/login', {
          method: 'POST', body: donnees, credentials: 'same-origin'
        });
        if (!reponse.ok) {
          const detail = await reponse.json().catch(() => ({}));
          throw new Error(detail.detail || 'Connexion impossible.');
        }
        const resultat = await reponse.json();
        S.Etat.connecte = true;
        await Application.ouvrirSession();
        if (resultat.doit_changer_mot_de_passe) {
          Application.demanderChangementMotDePasse();
        }
      } catch (exception) {
        erreur.textContent = exception.message;
      } finally {
        S.basculeChargement(false);
      }
    },

    /* Un mot de passe provisoire doit être remplacé avant tout usage : la fenêtre
       ne peut pas être fermée sans avoir défini un mot de passe conforme. */
    async demanderChangementMotDePasse() {
      const politique = await S.API.get('/api/auth/politique-mot-de-passe').catch(() => null);
      const exigences = politique ?
        '<div class="alerte alerte-info"><span>Exigences : ' +
        politique.longueur_minimale + ' caractères au minimum, ' +
        politique.classes_minimales + ' types de caractères parmi ' +
        politique.classes.join(', ') + '. Sont refusés : ' +
        politique.interdits.join(', ') + '.</span></div>' : '';
      S.formulaireModal('Définir un nouveau mot de passe', [
        { nom: 'mot_de_passe_actuel', libelle: 'Mot de passe provisoire', type: 'password',
          obligatoire: true },
        { nom: 'nouveau_mot_de_passe', libelle: 'Nouveau mot de passe', type: 'password',
          obligatoire: true,
          aide: 'Une phrase de passe de plusieurs mots est le choix le plus sûr et le plus ' +
                'simple à retenir.' },
        { nom: 'confirmation', libelle: 'Confirmer le nouveau mot de passe', type: 'password',
          obligatoire: true }
      ], {}, async function (donnees) {
        if (donnees.nouveau_mot_de_passe !== donnees.confirmation) {
          throw new Error('Les deux saisies ne correspondent pas.');
        }
        await S.API.put('/api/auth/moi', {
          mot_de_passe_actuel: donnees.mot_de_passe_actuel,
          nouveau_mot_de_passe: donnees.nouveau_mot_de_passe
        });
        S.notifier('Mot de passe modifié. Les autres sessions ont été fermées.', 'succes');
        S.Etat.utilisateur = await S.API.get('/api/auth/moi');
      });
      const zone = document.querySelector('#fond-modale .modale-corps');
      if (zone && exigences) zone.insertAdjacentHTML('afterbegin', exigences);
    },

    async ouvrirSession() {
      S.Etat.utilisateur = await S.API.get('/api/auth/moi');
      S.Etat.connecte = true;
      S.Etat.referentiels = await S.API.get('/api/referentiels');
      try {
        Object.assign(S.Etat.referentiels,
                      await S.API.get('/api/evaluation/referentiels'));
      } catch (erreur) { /* modules d'évaluation indisponibles : sans conséquence */ }
      await Application.rechargerProjets(S.Etat.projetActif);
      document.getElementById('ecran-connexion').classList.add('masque');
      document.getElementById('application').classList.remove('masque');
      document.getElementById('profil-utilisateur').innerHTML =
        '<strong>' + S.echapper(S.Etat.utilisateur.full_name) + '</strong>' +
        '<span>' + S.echapper(S.Etat.utilisateur.role_libelle || S.Etat.utilisateur.role) + '</span>';
      Application.construireMenu();
      const cle = location.hash.replace('#', '') || 'tableau-de-bord';
      Application.naviguer(global.Vues[cle] ? cle : 'tableau-de-bord');
    },

    async rechargerProjets(idSelectionne) {
      S.Etat.projets = await S.API.get('/api/projects');
      const select = document.getElementById('select-projet');
      select.innerHTML = S.Etat.projets.length ?
        S.Etat.projets.map((p) => '<option value="' + p.id + '">' + S.echapper(p.code) + ' — ' +
          S.echapper((p.acronym || p.title).substring(0, 40)) + '</option>').join('') :
        '<option value="">Aucun projet</option>';
      let cible = idSelectionne || S.Etat.projetActif;
      if (!S.Etat.projets.some((p) => p.id === cible)) {
        cible = S.Etat.projets.length ? S.Etat.projets[0].id : null;
      }
      Application.changerProjet(cible);
      if (cible) select.value = String(cible);
    },

    changerProjet(id) {
      S.Etat.projetActif = id || null;
      if (id) localStorage.setItem('sepia_projet', String(id));
      else localStorage.removeItem('sepia_projet');
      const select = document.getElementById('select-projet');
      if (id && select) select.value = String(id);
    },

    construireMenu() {
      const menu = document.getElementById('menu');
      menu.innerHTML = MENU.map(function (entree) {
        if (entree.groupe) return '<div class="menu-groupe">' + S.echapper(entree.groupe) + '</div>';
        if (entree.cle === 'administration' && S.Etat.utilisateur.role !== 'admin') return '';
        return '<a href="#' + entree.cle + '" data-vue="' + entree.cle + '">' +
          '<span class="icone">' + entree.icone + '</span>' + S.echapper(entree.libelle) + '</a>';
      }).join('');
      menu.querySelectorAll('a').forEach(function (lien) {
        lien.addEventListener('click', function () {
          document.getElementById('navigation').classList.remove('ouverte');
        });
      });
    },

    async naviguer(cle) {
      // Les vues d'évaluation sont définies dans un module distinct, fusionné ici.
      if (global.VuesEvaluation) Object.assign(global.Vues, global.VuesEvaluation);
      const vue = global.Vues[cle];
      if (!vue) return;
      S.Etat.vue = cle;
      if (location.hash.replace('#', '') !== cle) location.hash = cle;
      document.querySelectorAll('#menu a').forEach(function (lien) {
        lien.classList.toggle('actif', lien.dataset.vue === cle);
      });
      const projetCourant = S.Etat.projets.find((p) => p.id === S.Etat.projetActif);
      document.getElementById('titre-vue').textContent = vue.titre;
      document.getElementById('sous-titre-vue').textContent =
        (projetCourant && cle !== 'portefeuille' && cle !== 'administration' ?
          projetCourant.code + ' — ' : '') + vue.sousTitre;

      const barre = document.getElementById('actions-barre');
      barre.innerHTML = vue.actions ? vue.actions() : '';
      barre.querySelectorAll('[data-barre]').forEach(function (bouton) {
        bouton.addEventListener('click', function () {
          const gestionnaire = (vue.gestionnairesBarre || {})[bouton.dataset.barre];
          if (gestionnaire) gestionnaire();
        });
      });

      const conteneur = document.getElementById('vue');
      conteneur.innerHTML = '<div class="vide"><span class="icone">⏳</span>Chargement…</div>';
      S.basculeChargement(true);
      try {
        await vue.rendre(conteneur);
      } catch (erreur) {
        conteneur.innerHTML = '<div class="carte"><div class="alerte alerte-danger">' +
          '<span class="type">Erreur</span><span>' + S.echapper(erreur.message) + '</span></div></div>';
        S.notifier(erreur.message, 'erreur');
      } finally {
        S.basculeChargement(false);
        global.scrollTo(0, 0);
      }
    },

    rafraichir() {
      Application.naviguer(S.Etat.vue);
    },

    /* Actualisation périodique du tableau de bord, activable par l'utilisateur.
       Le minuteur est reprogrammé à chaque rendu et annulé hors du tableau de bord. */
    minuteur: null,
    programmerRafraichissement() {
      if (Application.minuteur) {
        clearTimeout(Application.minuteur);
        Application.minuteur = null;
      }
      if (localStorage.getItem('sepia_auto') !== '1') return;
      Application.minuteur = setTimeout(function () {
        if (S.Etat.vue === 'tableau-de-bord' && !document.hidden &&
            document.getElementById('fond-modale').classList.contains('masque')) {
          Application.naviguer('tableau-de-bord');
        } else {
          Application.programmerRafraichissement();
        }
      }, 60000);
    }
  };

  global.Application = Application;
  document.addEventListener('DOMContentLoaded', Application.demarrer);
})(window);
