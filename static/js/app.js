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
    { cle: 'activites', libelle: 'Chronogramme', icone: '📅' },
    { cle: 'budget', libelle: 'PTBA et budget', icone: '💰' },
    { groupe: 'Suivi-évaluation' },
    { cle: 'suivi', libelle: 'Cadre de suivi', icone: '📈' },
    { cle: 'risques', libelle: 'Risques et hypothèses', icone: '⚠️' },
    { cle: 'collecte', libelle: 'Fiches et questionnaires', icone: '📝' },
    { groupe: 'Données et livrables' },
    { cle: 'imports', libelle: 'Importer', icone: '⬆️' },
    { cle: 'livrables', libelle: 'Livrables', icone: '📦' },
    { cle: 'powerbi', libelle: 'Power BI', icone: '⚡' },
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

      if (S.Etat.jeton) {
        try {
          await Application.ouvrirSession();
          return;
        } catch (erreur) {
          S.deconnexion();
        }
      }
      document.getElementById('ecran-connexion').classList.remove('masque');
    },

    async connexion(evenement) {
      evenement.preventDefault();
      const erreur = document.getElementById('erreur-connexion');
      erreur.textContent = '';
      const donnees = new FormData();
      donnees.append('username', document.getElementById('champ-email').value.trim().toLowerCase());
      donnees.append('password', document.getElementById('champ-motdepasse').value);
      S.basculeChargement(true);
      try {
        const reponse = await fetch('/api/auth/login', { method: 'POST', body: donnees });
        if (!reponse.ok) {
          const detail = await reponse.json().catch(() => ({}));
          throw new Error(detail.detail || 'Connexion impossible.');
        }
        const resultat = await reponse.json();
        S.Etat.jeton = resultat.access_token;
        localStorage.setItem('sepia_jeton', resultat.access_token);
        await Application.ouvrirSession();
      } catch (exception) {
        erreur.textContent = exception.message;
      } finally {
        S.basculeChargement(false);
      }
    },

    async ouvrirSession() {
      S.Etat.utilisateur = await S.API.get('/api/auth/moi');
      S.Etat.referentiels = await S.API.get('/api/referentiels');
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
    }
  };

  global.Application = Application;
  document.addEventListener('DOMContentLoaded', Application.demarrer);
})(window);
