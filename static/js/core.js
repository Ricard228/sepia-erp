/* SEPIA — noyau : état applicatif, appels API et composants d'interface. */
(function (global) {
  'use strict';

  /* Le jeton de session n'est plus conservé côté navigateur : il réside dans un
     cookie « HttpOnly » que le JavaScript ne peut pas lire, et que le navigateur
     joint automatiquement à chaque requête de même origine. Un script injecté
     dans la page ne peut donc pas le dérober. */
  const Etat = {
    connecte: false,
    utilisateur: null,
    projets: [],
    projetActif: parseInt(localStorage.getItem('sepia_projet') || '0', 10) || null,
    referentiels: {},
    vue: 'tableau-de-bord'
  };

  /* ------------------------------------------------------------------ API */
  async function appel(chemin, options) {
    options = options || {};
    const entetes = options.headers || {};
    if (options.body && !(options.body instanceof FormData)) {
      entetes['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }
    const reponse = await fetch(chemin, Object.assign({}, options, {
      headers: entetes, credentials: 'same-origin'
    }));
    if (reponse.status === 401) {
      deconnexion();
      throw new Error('Session expirée. Veuillez vous reconnecter.');
    }
    if (reponse.status === 429) {
      let message = 'Trop de requêtes. Patientez quelques instants.';
      try { const d = await reponse.json(); if (d.detail) message = d.detail; } catch (e) {}
      notifier(message, 'erreur');
      throw new Error(message);
    }
    if (!reponse.ok) {
      let message = 'Erreur ' + reponse.status;
      try {
        const donnees = await reponse.json();
        message = typeof donnees.detail === 'string' ? donnees.detail : JSON.stringify(donnees.detail);
      } catch (e) { /* réponse non JSON */ }
      throw new Error(message);
    }
    if (reponse.status === 204) return null;
    const type = reponse.headers.get('content-type') || '';
    return type.indexOf('application/json') >= 0 ? reponse.json() : reponse.text();
  }

  const API = {
    get: (chemin) => appel(chemin),
    post: (chemin, body) => appel(chemin, { method: 'POST', body: body }),
    put: (chemin, body) => appel(chemin, { method: 'PUT', body: body }),
    supprimer: (chemin) => appel(chemin, { method: 'DELETE' }),
    televerser: (chemin, formData) => appel(chemin, { method: 'POST', body: formData }),
    telecharger: async function (chemin, nomDefaut) {
      basculeChargement(true);
      try {
        const reponse = await fetch(chemin, { credentials: 'same-origin' });
        if (!reponse.ok) {
          let message = 'Téléchargement impossible (' + reponse.status + ').';
          try { const d = await reponse.json(); if (d.detail) message = d.detail; } catch (e) {}
          throw new Error(message);
        }
        const entete = reponse.headers.get('content-disposition') || '';
        const correspondance = entete.match(/filename="?([^";]+)"?/);
        const nom = correspondance ? correspondance[1] : (nomDefaut || 'sepia-export');
        const blob = await reponse.blob();
        const url = URL.createObjectURL(blob);
        const lien = document.createElement('a');
        lien.href = url; lien.download = nom;
        document.body.appendChild(lien); lien.click(); lien.remove();
        setTimeout(() => URL.revokeObjectURL(url), 4000);
        notifier('Fichier « ' + nom + ' » téléchargé.', 'succes');
      } catch (erreur) {
        notifier(erreur.message, 'erreur');
      } finally {
        basculeChargement(false);
      }
    }
  };

  function deconnexion() {
    Etat.connecte = false;
    Etat.utilisateur = null;
    // Nettoyage des reliquats d'anciennes versions qui stockaient le jeton.
    localStorage.removeItem('sepia_jeton');
    fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' }).catch(() => {});
    document.getElementById('application').classList.add('masque');
    document.getElementById('ecran-connexion').classList.remove('masque');
  }

  /* --------------------------------------------------------------- Outils */
  function echapper(valeur) {
    if (valeur === null || valeur === undefined) return '';
    return String(valeur).replace(/[&<>"']/g, (c) => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function nombre(valeur, decimales) {
    if (valeur === null || valeur === undefined || valeur === '') return '—';
    const n = Number(valeur);
    if (isNaN(n)) return echapper(valeur);
    return n.toLocaleString('fr-FR', {
      minimumFractionDigits: decimales === undefined ? 0 : decimales,
      maximumFractionDigits: decimales === undefined ? 2 : decimales
    });
  }

  function pourcent(valeur) {
    if (valeur === null || valeur === undefined) return '—';
    return nombre(valeur, 1) + ' %';
  }

  function dateFr(valeur) {
    if (!valeur) return '—';
    const d = new Date(valeur);
    if (isNaN(d.getTime())) return echapper(valeur);
    return d.toLocaleDateString('fr-FR');
  }

  function couleurStatut(statut) {
    return {
      'Atteint': '#0F9D58', 'En bonne voie': '#4CAF50', 'À surveiller': '#F9A825',
      'Critique': '#D93025', 'Non renseigné': '#9AA0A6'
    }[statut] || '#9AA0A6';
  }

  function notifier(message, type) {
    const conteneur = document.getElementById('conteneur-notifications');
    const element = document.createElement('div');
    element.className = 'notification ' + (type || 'info');
    element.textContent = message;
    conteneur.appendChild(element);
    setTimeout(() => {
      element.style.opacity = '0';
      element.style.transition = 'opacity .3s';
      setTimeout(() => element.remove(), 320);
    }, type === 'erreur' ? 6000 : 3600);
  }

  function basculeChargement(actif) {
    document.getElementById('chargement').classList.toggle('masque', !actif);
  }

  /* -------------------------------------------------------------- Modales */
  function fermerModale() {
    const fond = document.getElementById('fond-modale');
    fond.classList.add('masque');
    fond.innerHTML = '';
  }

  function ouvrirModale(titre, contenuHtml, boutons, large) {
    const fond = document.getElementById('fond-modale');
    fond.innerHTML = '';
    const modale = document.createElement('div');
    modale.className = 'modale' + (large ? ' large' : '');
    modale.innerHTML =
      '<div class="modale-entete"><h3>' + echapper(titre) + '</h3>' +
      '<button class="btn-icone" data-fermer aria-label="Fermer">✕</button></div>' +
      '<div class="modale-corps"></div>' +
      '<div class="modale-pied"></div>';
    const corps = modale.querySelector('.modale-corps');
    if (typeof contenuHtml === 'string') corps.innerHTML = contenuHtml;
    else corps.appendChild(contenuHtml);
    const pied = modale.querySelector('.modale-pied');
    (boutons || [{ libelle: 'Fermer', classe: 'btn-secondaire', action: fermerModale }])
      .forEach(function (bouton) {
        const element = document.createElement('button');
        element.className = 'btn ' + (bouton.classe || 'btn-secondaire');
        element.textContent = bouton.libelle;
        element.addEventListener('click', function () { bouton.action(modale); });
        pied.appendChild(element);
      });
    modale.querySelector('[data-fermer]').addEventListener('click', fermerModale);
    fond.appendChild(modale);
    fond.classList.remove('masque');
    const premier = corps.querySelector('input, select, textarea');
    if (premier) setTimeout(() => premier.focus(), 60);
    return modale;
  }

  function confirmer(message, action) {
    ouvrirModale('Confirmation', '<p>' + echapper(message) + '</p>', [
      { libelle: 'Annuler', classe: 'btn-secondaire', action: fermerModale },
      { libelle: 'Confirmer', classe: 'btn-danger', action: function () { fermerModale(); action(); } }
    ]);
  }

  /* ----------------------------------------------------------- Formulaires */
  /* Un champ : {nom, libelle, type, options, aide, obligatoire, section, largeur} */
  function construireFormulaire(champs, valeurs) {
    valeurs = valeurs || {};
    const formulaire = document.createElement('form');
    formulaire.className = 'formulaire-genere';
    let sectionCourante = null;
    let groupe = null;

    champs.forEach(function (champ) {
      if (champ.section && champ.section !== sectionCourante) {
        sectionCourante = champ.section;
        const titre = document.createElement('div');
        titre.className = 'section-formulaire';
        titre.textContent = champ.section;
        formulaire.appendChild(titre);
        groupe = null;
      }
      const bloc = document.createElement('div');
      bloc.className = 'champ';
      const identifiant = 'champ-' + champ.nom;
      const valeur = valeurs[champ.nom];
      let controle = '';
      const commun = 'id="' + identifiant + '" name="' + champ.nom + '" data-type="' +
        (champ.type || 'text') + '"' + (champ.obligatoire ? ' required' : '');

      if (champ.type === 'select') {
        controle = '<select ' + commun + '>' +
          (champ.obligatoire ? '' : '<option value="">— Sélectionner —</option>') +
          (champ.options || []).map(function (option) {
            const v = typeof option === 'object' ? option.valeur : option;
            const l = typeof option === 'object' ? option.libelle : option;
            return '<option value="' + echapper(v) + '"' +
              (String(valeur) === String(v) ? ' selected' : '') + '>' + echapper(l) + '</option>';
          }).join('') + '</select>';
      } else if (champ.type === 'textarea') {
        controle = '<textarea ' + commun + ' rows="' + (champ.lignes || 3) + '">' +
          echapper(valeur) + '</textarea>';
      } else if (champ.type === 'checkbox') {
        controle = '<label style="font-weight:400;display:flex;gap:.4rem;align-items:center">' +
          '<input type="checkbox" ' + commun + (valeur ? ' checked' : '') +
          ' style="width:auto"> ' + echapper(champ.texteCase || 'Oui') + '</label>';
      } else if (champ.type === 'multiselect') {
        const selectionnees = Array.isArray(valeur) ? valeur : [];
        controle = '<div class="champ-cases" data-multiselect="' + champ.nom + '">' +
          (champ.options || []).map(function (option) {
            return '<label><input type="checkbox" value="' + echapper(option) + '"' +
              (selectionnees.indexOf(option) >= 0 ? ' checked' : '') + '> ' +
              echapper(option) + '</label>';
          }).join('') + '</div>';
      } else {
        const type = champ.type || 'text';
        const val = (type === 'date' && valeur) ? String(valeur).substring(0, 10) : valeur;
        controle = '<input type="' + type + '" ' + commun +
          (type === 'number' ? ' step="any"' : '') +
          ' value="' + echapper(val === null || val === undefined ? '' : val) + '">';
      }

      bloc.innerHTML = (champ.type === 'checkbox' ? '' :
        '<label for="' + identifiant + '">' + echapper(champ.libelle) +
        (champ.obligatoire ? ' *' : '') + '</label>') + controle +
        (champ.aide ? '<div class="aide">' + echapper(champ.aide) + '</div>' : '');

      if (champ.largeur === 'courte') {
        if (!groupe) { groupe = document.createElement('div'); groupe.className = 'champ-groupe'; formulaire.appendChild(groupe); }
        groupe.appendChild(bloc);
      } else {
        groupe = null;
        formulaire.appendChild(bloc);
      }
    });
    formulaire.addEventListener('submit', (e) => e.preventDefault());
    return formulaire;
  }

  function lireFormulaire(formulaire, champs) {
    const donnees = {};
    champs.forEach(function (champ) {
      if (champ.type === 'multiselect') {
        const conteneur = formulaire.querySelector('[data-multiselect="' + champ.nom + '"]');
        donnees[champ.nom] = conteneur ?
          Array.prototype.slice.call(conteneur.querySelectorAll('input:checked')).map((c) => c.value) : [];
        return;
      }
      const controle = formulaire.querySelector('[name="' + champ.nom + '"]');
      if (!controle) return;
      if (champ.type === 'checkbox') { donnees[champ.nom] = controle.checked; return; }
      let valeur = controle.value;
      if (valeur === '') { donnees[champ.nom] = null; return; }
      if (champ.type === 'number') {
        const n = parseFloat(String(valeur).replace(',', '.'));
        donnees[champ.nom] = isNaN(n) ? null : n;
        return;
      }
      donnees[champ.nom] = valeur;
    });
    return donnees;
  }

  function formulaireModal(titre, champs, valeurs, surValidation, large) {
    const formulaire = construireFormulaire(champs, valeurs);
    const modale = ouvrirModale(titre, formulaire, [
      { libelle: 'Annuler', classe: 'btn-secondaire', action: fermerModale },
      {
        libelle: 'Enregistrer', classe: 'btn-primaire', action: async function () {
          const manquants = champs.filter(function (champ) {
            if (!champ.obligatoire) return false;
            const controle = formulaire.querySelector('[name="' + champ.nom + '"]');
            return controle && !controle.value;
          });
          if (manquants.length) {
            notifier('Champs obligatoires à renseigner : ' +
              manquants.map((c) => c.libelle).join(', '), 'erreur');
            return;
          }
          basculeChargement(true);
          try {
            await surValidation(lireFormulaire(formulaire, champs));
            fermerModale();
          } catch (erreur) {
            notifier(erreur.message, 'erreur');
          } finally {
            basculeChargement(false);
          }
        }
      }
    ], large);
    return modale;
  }

  /* ---------------------------------------------------------------- Tables */
  /* colonnes : {cle, titre, classe, rendu(ligne), largeur} */
  function tableau(colonnes, lignes, actions) {
    if (!lignes || !lignes.length) {
      return '<div class="vide"><span class="icone">📭</span>Aucune donnée à afficher pour le moment.</div>';
    }
    const entete = colonnes.map((c) => '<th class="' + (c.classe || '') + '">' +
      echapper(c.titre) + '</th>').join('') + (actions ? '<th class="actions">Actions</th>' : '');
    const corps = lignes.map(function (ligne, index) {
      const cellules = colonnes.map(function (colonne) {
        const contenu = colonne.rendu ? colonne.rendu(ligne, index) : echapper(ligne[colonne.cle]);
        return '<td class="' + (colonne.classe || '') + '">' + contenu + '</td>';
      }).join('');
      const boutons = actions ? '<td class="actions">' + actions.map(function (action) {
        if (action.condition && !action.condition(ligne)) return '';
        return '<button class="btn btn-petit ' + (action.classe || 'btn-secondaire') +
          '" data-action="' + action.cle + '" data-id="' + ligne.id + '" title="' +
          echapper(action.titre || action.libelle) + '">' + action.libelle + '</button> ';
      }).join('') + '</td>' : '';
      return '<tr data-id="' + ligne.id + '">' + cellules + boutons + '</tr>';
    }).join('');
    return '<div class="tableau-conteneur"><table class="tableau"><thead><tr>' + entete +
      '</tr></thead><tbody>' + corps + '</tbody></table></div>';
  }

  function brancherActions(conteneur, gestionnaires) {
    conteneur.querySelectorAll('[data-action]').forEach(function (bouton) {
      bouton.addEventListener('click', function () {
        const gestionnaire = gestionnaires[bouton.dataset.action];
        if (gestionnaire) gestionnaire(parseInt(bouton.dataset.id, 10), bouton);
      });
    });
  }

  function kpi(libelle, valeur, detail, couleur) {
    return '<div class="kpi" style="border-left-color:' + (couleur || '#2E75B6') + '">' +
      '<div class="libelle">' + echapper(libelle) + '</div>' +
      '<div class="valeur" style="color:' + (couleur || '#1F4E79') + '">' + valeur + '</div>' +
      (detail ? '<div class="detail">' + detail + '</div>' : '') + '</div>';
  }

  function carte(titre, contenu, actionsHtml, sousTitre) {
    return '<section class="carte"><div class="carte-entete"><div><h3>' + echapper(titre) + '</h3>' +
      (sousTitre ? '<p>' + echapper(sousTitre) + '</p>' : '') + '</div>' +
      '<div style="display:flex;gap:.4rem;flex-wrap:wrap">' + (actionsHtml || '') + '</div></div>' +
      contenu + '</section>';
  }

  /* --------------------------------------------- Export des graphiques en image */
  /* Les graphiques étant produits en SVG autonome — couleurs en attributs, aucune
     police externe —, ils sont exportables sans bibliothèque : soit tels quels en
     .svg (vectoriel, redimensionnable sans perte), soit rastérisés dans un canevas
     pour produire un .png directement insérable dans un rapport. */
  function exporterGraphique(source, nomFichier, format) {
    const svg = typeof source === 'string' ? document.querySelector(source) :
      (source && source.tagName === 'svg' ? source : source && source.querySelector('svg'));
    if (!svg) { notifier('Aucun graphique à exporter dans cette section.', 'erreur'); return; }

    const clone = svg.cloneNode(true);
    const rect = svg.getBoundingClientRect();
    const boite = svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width
      ? { largeur: svg.viewBox.baseVal.width, hauteur: svg.viewBox.baseVal.height }
      : { largeur: rect.width || 900, hauteur: rect.height || 500 };
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    clone.setAttribute('width', boite.largeur);
    clone.setAttribute('height', boite.hauteur);
    clone.setAttribute('style', 'background:#ffffff;font-family:Segoe UI,Roboto,Arial,sans-serif');
    // Fond blanc explicite : sans lui, le PNG hérite d'un fond transparent qui
    // rend le texte sombre illisible dans un document imprimé.
    const fond = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    fond.setAttribute('width', '100%');
    fond.setAttribute('height', '100%');
    fond.setAttribute('fill', '#ffffff');
    clone.insertBefore(fond, clone.firstChild);

    const texte = new XMLSerializer().serializeToString(clone);
    const horodatage = new Date().toISOString().substring(0, 10);
    const nom = (nomFichier || 'graphique') + '_' + horodatage;

    if (format === 'svg') {
      const blob = new Blob([texte], { type: 'image/svg+xml;charset=utf-8' });
      telechargerBlob(blob, nom + '.svg');
      return;
    }

    const image = new Image();
    const donnees = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(texte);
    basculeChargement(true);
    image.onload = function () {
      try {
        const echelle = 2;   // rendu au double pour rester net à l'impression
        const canevas = document.createElement('canvas');
        canevas.width = Math.round(boite.largeur * echelle);
        canevas.height = Math.round(boite.hauteur * echelle);
        const contexte = canevas.getContext('2d');
        contexte.fillStyle = '#ffffff';
        contexte.fillRect(0, 0, canevas.width, canevas.height);
        contexte.setTransform(echelle, 0, 0, echelle, 0, 0);
        contexte.drawImage(image, 0, 0);
        canevas.toBlob(function (blob) {
          basculeChargement(false);
          if (!blob) { notifier('La conversion en image a échoué.', 'erreur'); return; }
          telechargerBlob(blob, nom + '.png');
        }, 'image/png');
      } catch (erreur) {
        basculeChargement(false);
        notifier('Export impossible : ' + erreur.message, 'erreur');
      }
    };
    image.onerror = function () {
      basculeChargement(false);
      notifier('Le graphique n\'a pas pu être converti en image. Essayez l\'export SVG.', 'erreur');
    };
    image.src = donnees;
  }

  function telechargerBlob(blob, nom) {
    const url = URL.createObjectURL(blob);
    const lien = document.createElement('a');
    lien.href = url;
    lien.download = nom;
    document.body.appendChild(lien);
    lien.click();
    lien.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    notifier('Image « ' + nom + ' » téléchargée.', 'succes');
  }

  /* Boutons d'export à placer dans l'en-tête d'une carte contenant un graphique. */
  function boutonsImage(cle, libelle) {
    return '<button class="btn btn-secondaire btn-petit" data-image="' + cle +
      '" data-format="png" title="Télécharger ' + echapper(libelle) +
      ' en image PNG">🖼️ PNG</button>' +
      '<button class="btn btn-secondaire btn-petit" data-image="' + cle +
      '" data-format="svg" title="Télécharger ' + echapper(libelle) +
      ' en image vectorielle SVG">📐 SVG</button>';
  }

  function brancherBoutonsImage(conteneur, cibles) {
    conteneur.querySelectorAll('[data-image]').forEach(function (bouton) {
      bouton.addEventListener('click', function () {
        const cible = cibles[bouton.dataset.image];
        if (!cible) return;
        exporterGraphique(typeof cible === 'string' ? document.querySelector(cible) : cible.element,
          typeof cible === 'string' ? bouton.dataset.image : cible.nom,
          bouton.dataset.format);
      });
    });
  }

  function vide(message, icone) {
    return '<div class="vide"><span class="icone">' + (icone || '📭') + '</span>' +
      echapper(message) + '</div>';
  }

  global.SEPIA = {
    Etat: Etat, API: API, echapper: echapper, nombre: nombre, pourcent: pourcent, dateFr: dateFr,
    couleurStatut: couleurStatut, notifier: notifier, basculeChargement: basculeChargement,
    ouvrirModale: ouvrirModale, fermerModale: fermerModale, confirmer: confirmer,
    construireFormulaire: construireFormulaire, lireFormulaire: lireFormulaire,
    formulaireModal: formulaireModal, tableau: tableau, brancherActions: brancherActions,
    kpi: kpi, carte: carte, vide: vide, deconnexion: deconnexion,
    exporterGraphique: exporterGraphique, boutonsImage: boutonsImage,
    brancherBoutonsImage: brancherBoutonsImage, telechargerBlob: telechargerBlob
  };
})(window);
