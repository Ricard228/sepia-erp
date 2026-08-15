/* SEPIA — graphiques SVG autonomes (aucune bibliothèque externe requise). */
(function (global) {
  'use strict';

  const PALETTE = ['#1F4E79', '#2E75B6', '#5B9BD5', '#0F9D58', '#F9A825', '#EA8600',
                   '#D93025', '#7B1FA2', '#00838F', '#6D4C41'];

  function ech(valeur) { return global.SEPIA.echapper(valeur); }

  /* ------------------------------------------------------------ Anneau */
  function anneau(donnees, options) {
    options = options || {};
    const total = donnees.reduce((somme, d) => somme + d.valeur, 0);
    if (!total) return global.SEPIA.vide('Aucune donnée à représenter.', '📊');
    const taille = options.taille || 210;
    const rayon = taille / 2 - 6;
    const epaisseur = options.epaisseur || 30;
    let angle = -Math.PI / 2;
    const centre = taille / 2;
    const segments = donnees.map(function (donnee, index) {
      const part = donnee.valeur / total;
      const fin = angle + part * Math.PI * 2;
      const grand = part > 0.5 ? 1 : 0;
      const x1 = centre + rayon * Math.cos(angle), y1 = centre + rayon * Math.sin(angle);
      const x2 = centre + rayon * Math.cos(fin), y2 = centre + rayon * Math.sin(fin);
      const ri = rayon - epaisseur;
      const x3 = centre + ri * Math.cos(fin), y3 = centre + ri * Math.sin(fin);
      const x4 = centre + ri * Math.cos(angle), y4 = centre + ri * Math.sin(angle);
      angle = fin;
      const couleur = donnee.couleur || PALETTE[index % PALETTE.length];
      const chemin = part >= 0.9999
        ? 'M ' + (centre + rayon) + ' ' + centre + ' A ' + rayon + ' ' + rayon + ' 0 1 1 ' +
          (centre + rayon - 0.01) + ' ' + centre + ' M ' + (centre + ri) + ' ' + centre +
          ' A ' + ri + ' ' + ri + ' 0 1 0 ' + (centre + ri - 0.01) + ' ' + centre + ' Z'
        : 'M ' + x1 + ' ' + y1 + ' A ' + rayon + ' ' + rayon + ' 0 ' + grand + ' 1 ' + x2 + ' ' + y2 +
          ' L ' + x3 + ' ' + y3 + ' A ' + ri + ' ' + ri + ' 0 ' + grand + ' 0 ' + x4 + ' ' + y4 + ' Z';
      return '<path d="' + chemin + '" fill="' + couleur + '"><title>' + ech(donnee.libelle) +
        ' : ' + donnee.valeur + ' (' + Math.round(part * 100) + ' %)</title></path>';
    }).join('');
    const centreTexte = options.centre !== undefined ? options.centre : total;
    const svg = '<svg viewBox="0 0 ' + taille + ' ' + taille + '" width="' + taille +
      '" height="' + taille + '" role="img">' + segments +
      '<text x="' + centre + '" y="' + (centre - 2) + '" text-anchor="middle" font-size="26" ' +
      'font-weight="700" fill="#1F4E79">' + ech(centreTexte) + '</text>' +
      '<text x="' + centre + '" y="' + (centre + 16) + '" text-anchor="middle" font-size="10" ' +
      'fill="#5F6368">' + ech(options.legendeCentre || 'total') + '</text></svg>';
    const legende = '<div class="legende">' + donnees.map(function (donnee, index) {
      return '<span><i style="background:' + (donnee.couleur || PALETTE[index % PALETTE.length]) +
        '"></i>' + ech(donnee.libelle) + ' (' + donnee.valeur + ')</span>';
    }).join('') + '</div>';
    return '<div class="graphique" style="text-align:center">' + svg + legende + '</div>';
  }

  /* ----------------------------------------------------- Barres horizontales */
  function barres(donnees, options) {
    options = options || {};
    if (!donnees.length) return global.SEPIA.vide('Aucune donnée à représenter.', '📊');
    const max = Math.max.apply(null, donnees.map((d) => Math.abs(d.valeur)).concat([options.max || 100]));
    const hauteurLigne = 30;
    const largeurLibelle = options.largeurLibelle || 190;
    const largeur = 640;
    const hauteur = donnees.length * hauteurLigne + 18;
    const barresHtml = donnees.map(function (donnee, index) {
      const y = index * hauteurLigne + 6;
      const largeurBarre = Math.max(2, (Math.abs(donnee.valeur) / max) * (largeur - largeurLibelle - 62));
      const couleur = donnee.couleur || PALETTE[index % PALETTE.length];
      return '<g>' +
        '<text x="0" y="' + (y + 14) + '" font-size="11" fill="#1F2933">' +
        ech(String(donnee.libelle).substring(0, 34)) + '</text>' +
        '<rect x="' + largeurLibelle + '" y="' + (y + 3) + '" width="' + (largeur - largeurLibelle - 62) +
        '" height="15" fill="#EEF2F7" rx="3"/>' +
        '<rect x="' + largeurLibelle + '" y="' + (y + 3) + '" width="' + largeurBarre +
        '" height="15" fill="' + couleur + '" rx="3"><title>' + ech(donnee.libelle) + ' : ' +
        donnee.valeur + '</title></rect>' +
        '<text x="' + (largeur - 56) + '" y="' + (y + 15) + '" font-size="11" font-weight="600" ' +
        'fill="#1F4E79">' + ech(donnee.etiquette !== undefined ? donnee.etiquette : donnee.valeur) +
        '</text></g>';
    }).join('');
    return '<div class="graphique"><svg viewBox="0 0 ' + largeur + ' ' + hauteur +
      '" width="100%" role="img">' + barresHtml + '</svg></div>';
  }

  /* ------------------------------------------------------------- Courbes */
  function courbes(periodes, series, options) {
    options = options || {};
    if (!periodes.length) return global.SEPIA.vide('Aucune période renseignée.', '📈');
    const largeur = 660, hauteur = 280;
    const marge = { haut: 18, droite: 14, bas: 46, gauche: 56 };
    const largeurTracee = largeur - marge.gauche - marge.droite;
    const hauteurTracee = hauteur - marge.haut - marge.bas;
    let maximum = 0;
    series.forEach(function (serie) {
      serie.valeurs.forEach(function (v) { if (v !== null && v !== undefined && v > maximum) maximum = v; });
    });
    maximum = maximum || 1;
    const echelle = maximum * 1.15;
    const x = (index) => marge.gauche + (periodes.length === 1 ? largeurTracee / 2 :
      (index / (periodes.length - 1)) * largeurTracee);
    const y = (valeur) => marge.haut + hauteurTracee - (valeur / echelle) * hauteurTracee;

    let grille = '';
    for (let i = 0; i <= 4; i++) {
      const valeur = (echelle / 4) * i;
      const posY = y(valeur);
      grille += '<line x1="' + marge.gauche + '" y1="' + posY + '" x2="' + (largeur - marge.droite) +
        '" y2="' + posY + '" stroke="#E4E8EE" stroke-width="1"/>' +
        '<text x="' + (marge.gauche - 8) + '" y="' + (posY + 4) + '" text-anchor="end" ' +
        'font-size="10" fill="#5F6368">' + global.SEPIA.nombre(valeur, valeur < 10 ? 1 : 0) + '</text>';
    }
    const etiquettes = periodes.map(function (periode, index) {
      const pas = Math.ceil(periodes.length / 12);
      if (index % pas !== 0 && index !== periodes.length - 1) return '';
      return '<text x="' + x(index) + '" y="' + (hauteur - 22) + '" text-anchor="middle" ' +
        'font-size="10" fill="#5F6368" transform="rotate(-30 ' + x(index) + ',' +
        (hauteur - 22) + ')">' + ech(periode) + '</text>';
    }).join('');

    const tracés = series.map(function (serie, indexSerie) {
      const couleur = serie.couleur || PALETTE[indexSerie % PALETTE.length];
      const points = [];
      let chemin = '';
      serie.valeurs.forEach(function (valeur, index) {
        if (valeur === null || valeur === undefined) return;
        const px = x(index), py = y(valeur);
        chemin += (chemin ? ' L ' : 'M ') + px + ' ' + py;
        points.push('<circle cx="' + px + '" cy="' + py + '" r="3.5" fill="' + couleur +
          '"><title>' + ech(serie.nom) + ' — ' + ech(periodes[index]) + ' : ' +
          global.SEPIA.nombre(valeur, 2) + '</title></circle>');
      });
      return '<path d="' + chemin + '" fill="none" stroke="' + couleur + '" stroke-width="2.4" ' +
        (serie.pointille ? 'stroke-dasharray="6 4" ' : '') + 'stroke-linejoin="round"/>' + points.join('');
    }).join('');

    const legende = '<div class="legende">' + series.map(function (serie, index) {
      return '<span><i style="background:' + (serie.couleur || PALETTE[index % PALETTE.length]) +
        '"></i>' + ech(serie.nom) + '</span>';
    }).join('') + '</div>';

    return '<div class="graphique"><svg viewBox="0 0 ' + largeur + ' ' + hauteur +
      '" width="100%" role="img">' + grille +
      '<line x1="' + marge.gauche + '" y1="' + (hauteur - marge.bas) + '" x2="' +
      (largeur - marge.droite) + '" y2="' + (hauteur - marge.bas) + '" stroke="#9AA0A6"/>' +
      etiquettes + tracés + '</svg>' + legende + '</div>';
  }

  /* -------------------------------------------------------------- Jauge */
  function jauge(valeur, options) {
    options = options || {};
    const taille = options.taille || 190;
    const centre = taille / 2;
    const rayon = centre - 16;
    const borne = Math.max(0, Math.min(valeur === null || valeur === undefined ? 0 : valeur, 120));
    const angle = Math.PI * (borne / 120);
    const x = centre - rayon * Math.cos(angle);
    const y = centre - rayon * Math.sin(angle) + 10;
    const couleur = options.couleur || global.SEPIA.couleurStatut(
      borne >= 100 ? 'Atteint' : borne >= 85 ? 'En bonne voie' : borne >= 60 ? 'À surveiller' : 'Critique');
    const arc = (debut, fin, couleurArc) => {
      const a1 = Math.PI * (debut / 120), a2 = Math.PI * (fin / 120);
      const x1 = centre - rayon * Math.cos(a1), y1 = centre - rayon * Math.sin(a1) + 10;
      const x2 = centre - rayon * Math.cos(a2), y2 = centre - rayon * Math.sin(a2) + 10;
      return '<path d="M ' + x1 + ' ' + y1 + ' A ' + rayon + ' ' + rayon + ' 0 0 1 ' + x2 + ' ' + y2 +
        '" fill="none" stroke="' + couleurArc + '" stroke-width="13" stroke-linecap="butt"/>';
    };
    return '<div class="graphique" style="text-align:center"><svg viewBox="0 0 ' + taille + ' ' +
      (centre + 34) + '" width="' + taille + '" role="img">' +
      arc(0, 60, '#F4C7C3') + arc(60, 85, '#FCE8B2') + arc(85, 120, '#B7E1CD') +
      '<line x1="' + centre + '" y1="' + (centre + 10) + '" x2="' + x + '" y2="' + y +
      '" stroke="' + couleur + '" stroke-width="3.4" stroke-linecap="round"/>' +
      '<circle cx="' + centre + '" cy="' + (centre + 10) + '" r="5" fill="' + couleur + '"/>' +
      '<text x="' + centre + '" y="' + (centre + 30) + '" text-anchor="middle" font-size="22" ' +
      'font-weight="700" fill="' + couleur + '">' +
      (valeur === null || valeur === undefined ? '—' : global.SEPIA.nombre(valeur, 1) + ' %') +
      '</text></svg>' + (options.libelle ?
      '<div style="font-size:.76rem;color:#5F6368">' + ech(options.libelle) + '</div>' : '') + '</div>';
  }

  /* ------------------------------------------------------ Matrice des risques */
  function matriceRisques(matrice, surClic) {
    const libellesImpact = ['1 — Négligeable', '2 — Mineur', '3 — Modéré', '4 — Majeur', '5 — Catastrophique'];
    const libellesProba = ['1 — Très faible', '2 — Faible', '3 — Moyenne', '4 — Forte', '5 — Très forte'];
    let html = '<div class="tableau-conteneur"><table class="tableau" style="min-width:520px">' +
      '<thead><tr><th>Impact ↓ / Probabilité →</th>' +
      libellesProba.map((l) => '<th class="centre">' + ech(l) + '</th>').join('') + '</tr></thead><tbody>';
    for (let impact = 5; impact >= 1; impact--) {
      html += '<tr><th style="background:#2E75B6">' + ech(libellesImpact[impact - 1]) + '</th>';
      for (let proba = 1; proba <= 5; proba++) {
        const score = impact * proba;
        const couleur = score >= 15 ? '#D93025' : score >= 10 ? '#EA8600' : score >= 5 ? '#F9A825' : '#0F9D58';
        const nombreRisques = (matrice[impact - 1] || [])[proba - 1] || 0;
        html += '<td class="centre" style="background:' + couleur +
          ';color:#fff;font-weight:700;cursor:' + (nombreRisques ? 'pointer' : 'default') +
          '" data-proba="' + proba + '" data-impact="' + impact + '" title="Score ' + score + '/25">' +
          (nombreRisques || '') + '</td>';
      }
      html += '</tr>';
    }
    return html + '</tbody></table></div>';
  }

  /* ------------------------------------------------------------- Gantt SVG */
  function gantt(activites, options) {
    options = options || {};
    const avecDates = activites.filter((a) => a.start_date && a.end_date);
    if (!avecDates.length) return global.SEPIA.vide('Aucune activité datée à afficher.', '📅');
    let debut = new Date(Math.min.apply(null, avecDates.map((a) => new Date(a.start_date))));
    let fin = new Date(Math.max.apply(null, avecDates.map((a) => new Date(a.end_date))));
    debut = new Date(debut.getFullYear(), debut.getMonth(), 1);
    fin = new Date(fin.getFullYear(), fin.getMonth() + 1, 0);
    const mois = [];
    const curseur = new Date(debut);
    while (curseur <= fin && mois.length < 130) {
      mois.push(new Date(curseur));
      curseur.setMonth(curseur.getMonth() + 1);
    }
    const nomsMois = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];
    const largeurLibelle = 260;
    const largeurMois = Math.max(16, Math.min(34, Math.round(760 / mois.length)));
    const largeur = largeurLibelle + mois.length * largeurMois + 16;
    const hauteurLigne = 26;
    const hauteur = activites.length * hauteurLigne + 62;
    const aujourdhui = new Date();

    let entete = '';
    let anneeCourante = null;
    mois.forEach(function (m, index) {
      const x = largeurLibelle + index * largeurMois;
      if (m.getFullYear() !== anneeCourante) {
        anneeCourante = m.getFullYear();
        entete += '<text x="' + (x + 2) + '" y="14" font-size="11" font-weight="700" fill="#1F4E79">' +
          anneeCourante + '</text>';
      }
      entete += '<text x="' + (x + largeurMois / 2) + '" y="32" text-anchor="middle" font-size="9" ' +
        'fill="#5F6368">' + nomsMois[m.getMonth()] + '</text>' +
        '<line x1="' + x + '" y1="36" x2="' + x + '" y2="' + (hauteur - 16) +
        '" stroke="#EEF2F7" stroke-width="1"/>';
    });

    const positionX = (dateValeur) => {
      const d = new Date(dateValeur);
      const indexMois = (d.getFullYear() - debut.getFullYear()) * 12 + (d.getMonth() - debut.getMonth());
      const joursDansMois = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
      return largeurLibelle + (indexMois + (d.getDate() - 1) / joursDansMois) * largeurMois;
    };

    const barresHtml = activites.map(function (activite, index) {
      const y = 44 + index * hauteurLigne;
      const libelle = (activite.code ? activite.code + ' ' : '') + activite.name;
      let barre = '';
      if (activite.start_date && activite.end_date) {
        const x1 = positionX(activite.start_date);
        const x2 = Math.max(x1 + 3, positionX(activite.end_date));
        const enRetard = new Date(activite.end_date) < aujourdhui && (activite.progress || 0) < 100;
        const couleur = (activite.progress || 0) >= 100 ? '#0F9D58' : enRetard ? '#D93025' : '#2E75B6';
        barre = '<rect x="' + x1 + '" y="' + (y + 4) + '" width="' + (x2 - x1) + '" height="13" rx="3" ' +
          'fill="' + couleur + '" opacity=".28"/>' +
          '<rect x="' + x1 + '" y="' + (y + 4) + '" width="' + ((x2 - x1) * (activite.progress || 0) / 100) +
          '" height="13" rx="3" fill="' + couleur + '"><title>' + ech(libelle) + '\n' +
          global.SEPIA.dateFr(activite.start_date) + ' → ' + global.SEPIA.dateFr(activite.end_date) +
          '\nAvancement : ' + (activite.progress || 0) + ' %</title></rect>';
        if (activite.milestone) {
          barre += '<polygon points="' + x2 + ',' + (y + 3) + ' ' + (x2 + 6) + ',' + (y + 10) +
            ' ' + x2 + ',' + (y + 17) + ' ' + (x2 - 6) + ',' + (y + 10) + '" fill="#F9A825"/>';
        }
      }
      return '<g>' + (index % 2 ? '<rect x="0" y="' + y + '" width="' + largeur + '" height="' +
        hauteurLigne + '" fill="#F7F8FA"/>' : '') +
        '<text x="4" y="' + (y + 15) + '" font-size="10.5" fill="#1F2933">' +
        ech(libelle.length > 44 ? libelle.substring(0, 42) + '…' : libelle) + '</text>' + barre + '</g>';
    }).join('');

    let ligneAujourdhui = '';
    if (aujourdhui >= debut && aujourdhui <= fin) {
      const x = positionX(aujourdhui.toISOString().substring(0, 10));
      ligneAujourdhui = '<line x1="' + x + '" y1="36" x2="' + x + '" y2="' + (hauteur - 16) +
        '" stroke="#D93025" stroke-width="1.6" stroke-dasharray="4 3"/>' +
        '<text x="' + (x + 3) + '" y="' + (hauteur - 4) + '" font-size="9" fill="#D93025">aujourd\'hui</text>';
    }

    return '<div class="graphique"><svg viewBox="0 0 ' + largeur + ' ' + hauteur + '" width="' +
      Math.max(largeur, 700) + '" role="img">' + entete + barresHtml + ligneAujourdhui + '</svg>' +
      '<div class="legende"><span><i style="background:#2E75B6"></i>En cours / planifié</span>' +
      '<span><i style="background:#0F9D58"></i>Achevé</span>' +
      '<span><i style="background:#D93025"></i>En retard</span>' +
      '<span><i style="background:#F9A825"></i>Jalon</span></div></div>';
  }

  /* ------------------------------------------------------- Barres empilées */
  function colonnes(categories, series, options) {
    options = options || {};
    if (!categories.length) return global.SEPIA.vide('Aucune donnée à représenter.', '📊');
    const largeur = 660, hauteur = 260;
    const marge = { haut: 16, droite: 12, bas: 54, gauche: 62 };
    const largeurTracee = largeur - marge.gauche - marge.droite;
    const hauteurTracee = hauteur - marge.haut - marge.bas;
    let maximum = 0;
    series.forEach((s) => s.valeurs.forEach((v) => { if (v > maximum) maximum = v; }));
    maximum = maximum || 1;
    const echelle = maximum * 1.12;
    const largeurGroupe = largeurTracee / categories.length;
    const largeurBarre = Math.max(6, (largeurGroupe - 10) / series.length);

    let grille = '';
    for (let i = 0; i <= 4; i++) {
      const valeur = (echelle / 4) * i;
      const y = marge.haut + hauteurTracee - (valeur / echelle) * hauteurTracee;
      grille += '<line x1="' + marge.gauche + '" y1="' + y + '" x2="' + (largeur - marge.droite) +
        '" y2="' + y + '" stroke="#E4E8EE"/><text x="' + (marge.gauche - 8) + '" y="' + (y + 4) +
        '" text-anchor="end" font-size="9.5" fill="#5F6368">' +
        global.SEPIA.nombre(valeur, 0) + '</text>';
    }
    const barresHtml = categories.map(function (categorie, indexCategorie) {
      const xGroupe = marge.gauche + indexCategorie * largeurGroupe + 5;
      const barresSerie = series.map(function (serie, indexSerie) {
        const valeur = serie.valeurs[indexCategorie] || 0;
        const hauteurBarre = (valeur / echelle) * hauteurTracee;
        const x = xGroupe + indexSerie * largeurBarre;
        const y = marge.haut + hauteurTracee - hauteurBarre;
        const couleur = serie.couleur || PALETTE[indexSerie % PALETTE.length];
        return '<rect x="' + x + '" y="' + y + '" width="' + (largeurBarre - 2) + '" height="' +
          Math.max(1, hauteurBarre) + '" fill="' + couleur + '" rx="2"><title>' + ech(serie.nom) +
          ' — ' + ech(categorie) + ' : ' + global.SEPIA.nombre(valeur, 2) + '</title></rect>';
      }).join('');
      return barresSerie + '<text x="' + (xGroupe + largeurGroupe / 2 - 5) + '" y="' +
        (hauteur - marge.bas + 16) + '" text-anchor="middle" font-size="9.5" fill="#5F6368">' +
        ech(String(categorie).substring(0, 14)) + '</text>';
    }).join('');
    const legende = '<div class="legende">' + series.map(function (serie, index) {
      return '<span><i style="background:' + (serie.couleur || PALETTE[index % PALETTE.length]) +
        '"></i>' + ech(serie.nom) + '</span>';
    }).join('') + '</div>';
    return '<div class="graphique"><svg viewBox="0 0 ' + largeur + ' ' + hauteur +
      '" width="100%" role="img">' + grille + barresHtml + '</svg>' + legende + '</div>';
  }

  /* ------------------------------------------------------- Réseau PERT (AON) */
  /* Représentation « activité sur nœud » : chaque activité est une boîte portant
     ses dates au plus tôt et au plus tard ; les flèches figurent les liens
     d'antécédence. Le chemin critique est tracé en rouge et en trait épais. */
  function pert(activites) {
    if (!activites || !activites.length) {
      return global.SEPIA.vide('Aucune activité à ordonnancer.', '🔗');
    }
    const parRang = {};
    activites.forEach(function (a) {
      (parRang[a.niveau_pert] = parRang[a.niveau_pert] || []).push(a);
    });
    const rangs = Object.keys(parRang).map(Number).sort((a, b) => a - b);
    const largeurBoite = 190, hauteurBoite = 74;
    const espaceX = 78, espaceY = 22;
    const hauteurMax = Math.max.apply(null, rangs.map((r) => parRang[r].length));
    const largeur = rangs.length * (largeurBoite + espaceX) + 40;
    const hauteur = hauteurMax * (hauteurBoite + espaceY) + 70;

    const position = {};
    rangs.forEach(function (rang, indexRang) {
      const colonne = parRang[rang];
      const offset = (hauteurMax - colonne.length) * (hauteurBoite + espaceY) / 2;
      colonne.forEach(function (a, index) {
        position[a.code || String(a.id)] = {
          x: 20 + indexRang * (largeurBoite + espaceX),
          y: 46 + offset + index * (hauteurBoite + espaceY),
          activite: a
        };
      });
    });

    let fleches = '';
    activites.forEach(function (a) {
      const arrivee = position[a.code || String(a.id)];
      if (!arrivee) return;
      (a.antecedents || []).forEach(function (code) {
        const depart = position[code];
        if (!depart) return;
        const x1 = depart.x + largeurBoite, y1 = depart.y + hauteurBoite / 2;
        const x2 = arrivee.x, y2 = arrivee.y + hauteurBoite / 2;
        const critique = a.critique && (depart.activite.critique);
        const milieu = (x1 + x2) / 2;
        fleches += '<path d="M ' + x1 + ' ' + y1 + ' C ' + milieu + ' ' + y1 + ', ' +
          milieu + ' ' + y2 + ', ' + (x2 - 7) + ' ' + y2 + '" fill="none" stroke="' +
          (critique ? '#D93025' : '#9AA0A6') + '" stroke-width="' + (critique ? 2.4 : 1.3) +
          '" marker-end="url(#fleche' + (critique ? 'C' : 'N') + ')"/>';
      });
    });

    let boites = '';
    Object.keys(position).forEach(function (cle) {
      const p = position[cle];
      const a = p.activite;
      const couleur = a.critique ? '#D93025' : '#2E75B6';
      const fond = a.critique ? '#FCE8E6' : '#FFFFFF';
      const libelle = (a.name || '').length > 30 ? a.name.substring(0, 28) + '…' : (a.name || '');
      boites += '<g>' +
        '<rect x="' + p.x + '" y="' + p.y + '" width="' + largeurBoite + '" height="' +
        hauteurBoite + '" rx="6" fill="' + fond + '" stroke="' + couleur + '" stroke-width="' +
        (a.critique ? 2.2 : 1.2) + '"/>' +
        '<line x1="' + p.x + '" y1="' + (p.y + 20) + '" x2="' + (p.x + largeurBoite) + '" y2="' +
        (p.y + 20) + '" stroke="' + couleur + '" stroke-width=".8" opacity=".5"/>' +
        '<text x="' + (p.x + 6) + '" y="' + (p.y + 14) + '" font-size="10.5" font-weight="700" ' +
        'fill="' + couleur + '">' + ech(a.code || '') + '</text>' +
        '<text x="' + (p.x + largeurBoite - 6) + '" y="' + (p.y + 14) + '" font-size="9.5" ' +
        'text-anchor="end" fill="#5F6368">' + a.duree + ' j</text>' +
        '<text x="' + (p.x + 6) + '" y="' + (p.y + 34) + '" font-size="9" fill="#1F2933">' +
        ech(libelle) + '</text>' +
        '<text x="' + (p.x + 6) + '" y="' + (p.y + 50) + '" font-size="8.5" fill="#5F6368">' +
        'Tôt : ' + a.debut_tot + ' → ' + a.fin_tot + '</text>' +
        '<text x="' + (p.x + 6) + '" y="' + (p.y + 63) + '" font-size="8.5" fill="#5F6368">' +
        'Tard : ' + a.debut_tard + ' → ' + a.fin_tard + '</text>' +
        '<text x="' + (p.x + largeurBoite - 6) + '" y="' + (p.y + 63) + '" font-size="9" ' +
        'text-anchor="end" font-weight="700" fill="' + couleur + '">' +
        (a.critique ? 'critique' : 'marge ' + a.marge_totale + ' j') + '</text>' +
        '<title>' + ech(a.name) + '\nDurée : ' + a.duree + ' jours\nMarge totale : ' +
        a.marge_totale + ' jours\nAntécédents : ' + (a.antecedents.join(', ') || 'aucun') +
        '</title></g>';
    });

    let entetesRangs = '';
    rangs.forEach(function (rang, indexRang) {
      entetesRangs += '<text x="' + (20 + indexRang * (largeurBoite + espaceX) + largeurBoite / 2) +
        '" y="24" text-anchor="middle" font-size="10" font-weight="700" fill="#1F4E79">Rang ' +
        (rang + 1) + '</text>';
    });

    return '<div class="graphique"><svg viewBox="0 0 ' + largeur + ' ' + hauteur + '" width="' +
      Math.max(largeur, 700) + '" role="img"><defs>' +
      '<marker id="flecheN" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" ' +
      'markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#9AA0A6"/></marker>' +
      '<marker id="flecheC" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" ' +
      'markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#D93025"/></marker>' +
      '</defs>' + entetesRangs + fleches + boites + '</svg>' +
      '<div class="legende"><span><i style="background:#D93025"></i>Activité critique (marge nulle)</span>' +
      '<span><i style="background:#2E75B6"></i>Activité avec marge</span>' +
      '<span style="color:#5F6368">Tôt / Tard : jours écoulés depuis le début du projet</span>' +
      '</div></div>';
  }

  /* ------------------------------------------- Organigramme des tâches (WBS) */
  /* Arbre descendant : le projet en tête, puis composantes, sous-composantes et
     lots de travail. La largeur de chaque branche s'adapte au nombre de feuilles. */
  function wbs(racines, projetLibelle) {
    if (!racines || !racines.length) {
      return global.SEPIA.vide('Aucune décomposition à représenter.', '🗂️');
    }
    const largeurBoite = 152, hauteurBoite = 52, espaceX = 14, espaceY = 40;
    const couleurs = ['#1F4E79', '#2E75B6', '#5B9BD5', '#9DC3E6', '#DCE6F1'];

    function compterFeuilles(noeud) {
      if (!noeud.enfants || !noeud.enfants.length) return 1;
      return noeud.enfants.reduce((somme, e) => somme + compterFeuilles(e), 0);
    }
    const totalFeuilles = racines.reduce((s, r) => s + compterFeuilles(r), 0);
    function profondeurMax(noeud, niveau) {
      if (!noeud.enfants || !noeud.enfants.length) return niveau;
      return Math.max.apply(null, noeud.enfants.map((e) => profondeurMax(e, niveau + 1)));
    }
    const profondeur = Math.max.apply(null, racines.map((r) => profondeurMax(r, 1))) + 1;

    const largeur = totalFeuilles * (largeurBoite + espaceX) + 40;
    const hauteur = profondeur * (hauteurBoite + espaceY) + 30;
    const boites = [];
    const liens = [];

    function placer(noeud, niveau, curseurX) {
      const feuilles = compterFeuilles(noeud);
      const largeurBranche = feuilles * (largeurBoite + espaceX);
      const x = curseurX + largeurBranche / 2 - largeurBoite / 2;
      const y = 20 + niveau * (hauteurBoite + espaceY);
      let enfantX = curseurX;
      (noeud.enfants || []).forEach(function (enfant) {
        const positionEnfant = placer(enfant, niveau + 1, enfantX);
        liens.push('<path d="M ' + (x + largeurBoite / 2) + ' ' + (y + hauteurBoite) +
          ' V ' + (y + hauteurBoite + espaceY / 2) +
          ' H ' + (positionEnfant.x + largeurBoite / 2) +
          ' V ' + positionEnfant.y + '" fill="none" stroke="#9AA0A6" stroke-width="1.2"/>');
        enfantX += compterFeuilles(enfant) * (largeurBoite + espaceX);
      });
      const couleur = couleurs[Math.min(niveau, couleurs.length - 1)];
      const texteBlanc = niveau < 3;
      const libelle = (noeud.libelle || '').length > 42 ?
        noeud.libelle.substring(0, 40) + '…' : (noeud.libelle || '');
      const mots = libelle.split(' ');
      let lignes = [''], indexLigne = 0;
      mots.forEach(function (mot) {
        if ((lignes[indexLigne] + ' ' + mot).trim().length > 24) {
          indexLigne++; lignes[indexLigne] = mot;
        } else { lignes[indexLigne] = (lignes[indexLigne] + ' ' + mot).trim(); }
      });
      lignes = lignes.slice(0, 2);
      boites.push('<g><rect x="' + x + '" y="' + y + '" width="' + largeurBoite + '" height="' +
        hauteurBoite + '" rx="5" fill="' + couleur + '" stroke="#1F4E79" stroke-width=".8"/>' +
        '<text x="' + (x + 7) + '" y="' + (y + 15) + '" font-size="10" font-weight="700" fill="' +
        (texteBlanc ? '#fff' : '#1F2933') + '">' + ech(noeud.wbs) + '</text>' +
        '<text x="' + (x + largeurBoite - 7) + '" y="' + (y + 15) + '" font-size="8.5" ' +
        'text-anchor="end" fill="' + (texteBlanc ? 'rgba(255,255,255,.85)' : '#5F6368') + '">' +
        global.SEPIA.nombre(noeud.cout, 0) + '</text>' +
        lignes.map(function (texte, index) {
          return '<text x="' + (x + 7) + '" y="' + (y + 31 + index * 12) + '" font-size="8.5" ' +
            'fill="' + (texteBlanc ? '#fff' : '#1F2933') + '">' + ech(texte) + '</text>';
        }).join('') +
        '<title>' + ech(noeud.wbs + ' — ' + noeud.libelle) + '\n' + ech(noeud.type) +
        '\nCoût : ' + global.SEPIA.nombre(noeud.cout, 0) +
        '\nAvancement : ' + noeud.avancement + ' %</title></g>');
      return { x: x, y: y };
    }

    let curseur = 20;
    const positionsRacines = [];
    racines.forEach(function (racine) {
      positionsRacines.push(placer(racine, 1, curseur));
      curseur += compterFeuilles(racine) * (largeurBoite + espaceX);
    });

    // Nœud racine « projet »
    const xProjet = largeur / 2 - largeurBoite / 2;
    positionsRacines.forEach(function (p) {
      liens.push('<path d="M ' + (xProjet + largeurBoite / 2) + ' ' + (20 + hauteurBoite) +
        ' V ' + (20 + hauteurBoite + espaceY / 2) + ' H ' + (p.x + largeurBoite / 2) +
        ' V ' + p.y + '" fill="none" stroke="#9AA0A6" stroke-width="1.2"/>');
    });
    const racineHtml = '<rect x="' + xProjet + '" y="20" width="' + largeurBoite + '" height="' +
      hauteurBoite + '" rx="5" fill="#0F2C4C" stroke="#0F2C4C"/>' +
      '<text x="' + (xProjet + largeurBoite / 2) + '" y="42" text-anchor="middle" font-size="10" ' +
      'font-weight="700" fill="#fff">' + ech((projetLibelle || 'PROJET').substring(0, 22)) +
      '</text><text x="' + (xProjet + largeurBoite / 2) + '" y="56" text-anchor="middle" ' +
      'font-size="8.5" fill="rgba(255,255,255,.8)">Niveau 0</text>';

    return '<div class="graphique"><svg viewBox="0 0 ' + largeur + ' ' + (hauteur + 20) +
      '" width="' + Math.max(largeur, 700) + '" role="img">' +
      liens.join('') + racineHtml + boites.join('') + '</svg>' +
      '<div class="legende"><span style="color:#5F6368">Le montant affiché en haut à droite de ' +
      'chaque bloc est le coût consolidé de la branche.</span></div></div>';
  }

  /* --------------------------------------- Carte des zones d'intervention */
  /* Carte à symboles proportionnels : chaque zone est un cercle dont la surface
     est proportionnelle aux bénéficiaires atteints et la couleur au taux de
     couverture. La projection est celle de Mercator sphérique (EPSG:3857), la
     même que celle des fonds de carte en tuiles, ce qui permet de superposer
     facultativement un fond OpenStreetMap sans aucune bibliothèque externe. */
  const TAILLE_TUILE = 256;

  function lonVersX(lon, zoom) { return (lon + 180) / 360 * Math.pow(2, zoom); }
  function latVersY(lat, zoom) {
    const r = lat * Math.PI / 180;
    return (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * Math.pow(2, zoom);
  }

  function couleurCouverture(taux) {
    if (taux === null || taux === undefined) return '#9AA0A6';
    if (taux >= 80) return '#0F9D58';
    if (taux >= 50) return '#F9A825';
    if (taux >= 25) return '#EA8600';
    return '#D93025';
  }

  function carte(zones, options) {
    options = options || {};
    const localisees = (zones || []).filter(
      (z) => typeof z.latitude === 'number' && typeof z.longitude === 'number');
    if (!localisees.length) {
      return global.SEPIA.vide(
        'Aucune zone d\'intervention ne porte de coordonnées géographiques. Renseignez la ' +
        'latitude et la longitude de chaque zone pour afficher la carte de couverture.', '🗺️');
    }

    // Dimensions adaptées à la largeur disponible : sur téléphone la carte tient
    // dans l'écran plutôt que d'imposer un défilement horizontal.
    const largeurDisponible = Math.max(280, (global.innerWidth || 1000) - 90);
    const largeurCible = Math.min(options.largeur || 860, largeurDisponible);
    const hauteurCible = Math.min(options.hauteur || 520,
                                  Math.round(largeurCible * 0.62) + 60);
    const fondActif = options.fond !== false;

    // Cadre géographique, élargi d'une marge pour ne pas coller les symboles au bord.
    let latMin = Math.min.apply(null, localisees.map((z) => z.latitude));
    let latMax = Math.max.apply(null, localisees.map((z) => z.latitude));
    let lonMin = Math.min.apply(null, localisees.map((z) => z.longitude));
    let lonMax = Math.max.apply(null, localisees.map((z) => z.longitude));
    const margeLat = Math.max((latMax - latMin) * 0.25, 0.35);
    const margeLon = Math.max((lonMax - lonMin) * 0.25, 0.35);
    latMin -= margeLat; latMax += margeLat; lonMin -= margeLon; lonMax += margeLon;

    // Niveau de zoom : le plus grand qui laisse le cadre géographique tenir dans
    // la surface visée. Le canevas conserve ensuite les dimensions demandées et
    // les données y sont centrées, ce qui évite les cartes minuscules lorsque
    // l'emprise du projet est petite.
    let zoom = 3;
    for (let z = 3; z <= 13; z++) {
      const l = (lonVersX(lonMax, z) - lonVersX(lonMin, z)) * TAILLE_TUILE;
      const h = (latVersY(latMin, z) - latVersY(latMax, z)) * TAILLE_TUILE;
      if (l <= largeurCible && h <= hauteurCible) zoom = z; else break;
    }

    const largeur = Math.round(largeurCible);
    const hauteur = Math.round(hauteurCible);
    const centreX = (lonVersX(lonMin, zoom) + lonVersX(lonMax, zoom)) / 2 * TAILLE_TUILE;
    const centreY = (latVersY(latMin, zoom) + latVersY(latMax, zoom)) / 2 * TAILLE_TUILE;
    const xMin = centreX - largeur / 2;
    const yMin = centreY - hauteur / 2;
    const projeter = (z) => ({
      x: lonVersX(z.longitude, zoom) * TAILLE_TUILE - xMin,
      y: latVersY(z.latitude, zoom) * TAILLE_TUILE - yMin
    });
    // Le graticule est tracé sur l'emprise réellement visible du canevas.
    const lonGauche = (xMin / TAILLE_TUILE) / Math.pow(2, zoom) * 360 - 180;
    const lonDroite = ((xMin + largeur) / TAILLE_TUILE) / Math.pow(2, zoom) * 360 - 180;
    const yVersLat = (y) => {
      const n = Math.PI - 2 * Math.PI * (y / TAILLE_TUILE) / Math.pow(2, zoom);
      return 180 / Math.PI * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
    };
    const latHaut = yVersLat(yMin);
    const latBas = yVersLat(yMin + hauteur);

    // Fond de carte facultatif : tuiles OpenStreetMap chargées en simples images.
    let tuiles = '';
    if (fondActif) {
      const tuileXMin = Math.floor(xMin / TAILLE_TUILE);
      const tuileXMax = Math.floor((xMin + largeur) / TAILLE_TUILE);
      const tuileYMin = Math.floor(yMin / TAILLE_TUILE);
      const tuileYMax = Math.floor((yMin + hauteur) / TAILLE_TUILE);
      const nombreTuiles = Math.pow(2, zoom);
      let compteur = 0;
      for (let tx = tuileXMin; tx <= tuileXMax && compteur < 64; tx++) {
        for (let ty = tuileYMin; ty <= tuileYMax && compteur < 64; ty++) {
          if (tx < 0 || ty < 0 || tx >= nombreTuiles || ty >= nombreTuiles) continue;
          compteur++;
          tuiles += '<img src="https://tile.openstreetmap.org/' + zoom + '/' + tx + '/' + ty +
            '.png" alt="" loading="lazy" onerror="this.style.display=\'none\'" ' +
            'style="position:absolute;left:' + (tx * TAILLE_TUILE - xMin) + 'px;top:' +
            (ty * TAILLE_TUILE - yMin) + 'px;width:256px;height:256px">';
        }
      }
    }

    // Graticule : repères de latitude et de longitude, indispensables sans fond de carte.
    let graticule = '';
    const etendue = Math.max(lonDroite - lonGauche, latHaut - latBas);
    const pas = etendue > 8 ? 2 : etendue > 4 ? 1 : etendue > 2 ? 0.5 : 0.25;
    for (let lon = Math.ceil(lonGauche / pas) * pas; lon <= lonDroite; lon += pas) {
      const x = lonVersX(lon, zoom) * TAILLE_TUILE - xMin;
      graticule += '<line x1="' + x + '" y1="0" x2="' + x + '" y2="' + hauteur +
        '" stroke="#1F4E79" stroke-width=".5" stroke-dasharray="3 4" opacity=".28"/>' +
        '<text x="' + (x + 3) + '" y="' + (hauteur - 5) + '" font-size="9" fill="#1F4E79" ' +
        'opacity=".7">' + lon.toFixed(2).replace(/\.?0+$/, '') + '°E</text>';
    }
    for (let lat = Math.ceil(latBas / pas) * pas; lat <= latHaut; lat += pas) {
      const y = latVersY(lat, zoom) * TAILLE_TUILE - yMin;
      graticule += '<line x1="0" y1="' + y + '" x2="' + largeur + '" y2="' + y +
        '" stroke="#1F4E79" stroke-width=".5" stroke-dasharray="3 4" opacity=".28"/>' +
        '<text x="4" y="' + (y - 4) + '" font-size="9" fill="#1F4E79" opacity=".7">' +
        lat.toFixed(2).replace(/\.?0+$/, '') + '°N</text>';
    }

    // Symboles proportionnels : la surface, non le rayon, porte la quantité.
    const maxBeneficiaires = Math.max.apply(null,
      localisees.map((z) => z.beneficiaires_atteints || 0).concat([1]));
    const rayon = (valeur) => 8 + 26 * Math.sqrt(Math.max(valeur, 0) / maxBeneficiaires);

    // Liens hiérarchiques entre une zone mère et ses zones filles.
    const parId = {};
    localisees.forEach((z) => { parId[z.id] = z; });
    let liens = '';
    localisees.forEach(function (z) {
      const parent = z.parent_id ? parId[z.parent_id] : null;
      if (!parent) return;
      const a = projeter(parent), b = projeter(z);
      liens += '<line x1="' + a.x + '" y1="' + a.y + '" x2="' + b.x + '" y2="' + b.y +
        '" stroke="#1F4E79" stroke-width="1.1" stroke-dasharray="4 3" opacity=".45"/>';
    });

    // Les zones les plus étendues sont tracées en premier pour rester lisibles.
    const ordonnees = localisees.slice().sort(
      (a, b) => (b.beneficiaires_atteints || 0) - (a.beneficiaires_atteints || 0));
    let symboles = '';
    ordonnees.forEach(function (z) {
      const p = projeter(z);
      const r = rayon(z.beneficiaires_atteints || 0);
      const couleur = couleurCouverture(z.taux_couverture);
      const partFemmes = (z.equite_genre || {}).part_femmes;
      symboles += '<g>' +
        '<circle cx="' + p.x + '" cy="' + p.y + '" r="' + r + '" fill="' + couleur +
        '" fill-opacity=".62" stroke="#fff" stroke-width="2"/>' +
        (partFemmes !== undefined && partFemmes !== null ?
          '<path d="M ' + p.x + ' ' + (p.y - r) + ' A ' + r + ' ' + r + ' 0 0 0 ' + p.x + ' ' +
          (p.y + r) + ' Z" fill="#D81B60" fill-opacity=".55"/>' : '') +
        '<circle cx="' + p.x + '" cy="' + p.y + '" r="2.6" fill="#1F2933"/>' +
        '<text x="' + p.x + '" y="' + (p.y + r + 13) + '" text-anchor="middle" font-size="10.5" ' +
        'font-weight="700" fill="#1F2933" stroke="#fff" stroke-width="3" paint-order="stroke">' +
        ech(z.nom) + '</text>' +
        '<text x="' + p.x + '" y="' + (p.y + r + 25) + '" text-anchor="middle" font-size="9.5" ' +
        'fill="#1F4E79" stroke="#fff" stroke-width="3" paint-order="stroke">' +
        global.SEPIA.nombre(z.beneficiaires_atteints, 0) +
        (z.taux_couverture !== null && z.taux_couverture !== undefined ?
          ' (' + global.SEPIA.nombre(z.taux_couverture, 0) + ' %)' : '') + '</text>' +
        '<title>' + ech(z.nom) + ' — ' + ech(z.niveau || '') + '\n' +
        'Bénéficiaires atteints : ' + global.SEPIA.nombre(z.beneficiaires_atteints, 0) +
        (z.cible_beneficiaires ? ' / ' + global.SEPIA.nombre(z.cible_beneficiaires, 0) +
          ' (' + global.SEPIA.nombre(z.taux_couverture, 1) + ' %)' : '') +
        (partFemmes !== undefined && partFemmes !== null ?
          '\nPart des femmes : ' + global.SEPIA.nombre(partFemmes, 1) + ' %' : '') +
        '\nMesures collectées : ' + (z.nb_mesures || 0) +
        '\nCoordonnées : ' + z.latitude.toFixed(4) + ', ' + z.longitude.toFixed(4) +
        '</title></g>';
    });

    // Échelle métrique : la longueur d'un degré de longitude dépend de la latitude.
    const latMoyenne = (latBas + latHaut) / 2;
    const metresParPixel = 156543.03392 * Math.cos(latMoyenne * Math.PI / 180) / Math.pow(2, zoom);
    const distancesRondes = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000];
    const kmEchelle = distancesRondes.find(
      (d) => d * 1000 / metresParPixel >= Math.min(90, largeur / 6)) || 1000;
    const largeurEchelle = Math.round(kmEchelle * 1000 / metresParPixel);
    const echelle = '<g transform="translate(14,' + (hauteur - 34) + ')">' +
      '<rect x="-6" y="-16" width="' + (largeurEchelle + 46) + '" height="28" rx="4" ' +
      'fill="#fff" fill-opacity=".82"/>' +
      '<line x1="0" y1="0" x2="' + largeurEchelle + '" y2="0" stroke="#1F2933" stroke-width="2.4"/>' +
      '<line x1="0" y1="-4" x2="0" y2="4" stroke="#1F2933" stroke-width="2.4"/>' +
      '<line x1="' + largeurEchelle + '" y1="-4" x2="' + largeurEchelle + '" y2="4" ' +
      'stroke="#1F2933" stroke-width="2.4"/>' +
      '<text x="' + (largeurEchelle + 6) + '" y="4" font-size="10" fill="#1F2933">' +
      kmEchelle + ' km</text></g>';

    // Rose des vents simplifiée.
    const nord = '<g transform="translate(' + (largeur - 34) + ',26)">' +
      '<circle r="16" fill="#fff" fill-opacity=".82"/>' +
      '<path d="M 0 -12 L 5 6 L 0 2 L -5 6 Z" fill="#1F4E79"/>' +
      '<text y="16" text-anchor="middle" font-size="9" font-weight="700" fill="#1F4E79">N</text></g>';

    const nonLocalisees = (zones || []).length - localisees.length;
    return '<div class="carte-couverture">' +
      '<div class="carte-cadre" style="width:' + largeur + 'px;height:' + hauteur + 'px">' +
      tuiles +
      '<svg viewBox="0 0 ' + largeur + ' ' + hauteur + '" width="' + largeur + '" height="' +
      hauteur + '" style="position:absolute;left:0;top:0" role="img">' +
      graticule + liens + symboles + echelle + nord + '</svg>' +
      (fondActif ? '<div class="attribution-carte">© Contributeurs OpenStreetMap</div>' : '') +
      '</div>' +
      '<div class="legende">' +
      '<span><i style="background:#0F9D58"></i>Couverture ≥ 80 %</span>' +
      '<span><i style="background:#F9A825"></i>50 à 79 %</span>' +
      '<span><i style="background:#EA8600"></i>25 à 49 %</span>' +
      '<span><i style="background:#D93025"></i>moins de 25 %</span>' +
      '<span><i style="background:#9AA0A6"></i>cible non fixée</span>' +
      '<span><i style="background:#D81B60"></i>part des femmes (demi-disque)</span>' +
      '<span style="color:#5F6368">La surface du cercle est proportionnelle aux bénéficiaires atteints.</span>' +
      (nonLocalisees > 0 ? '<span style="color:#EA8600">' + nonLocalisees +
        ' zone(s) sans coordonnées ne figurent pas sur la carte.</span>' : '') +
      '</div></div>';
  }

  /* Surveillance du fond de carte : sur un réseau sans accès aux serveurs de
     tuiles, les images restent en attente indéfiniment. Au bout de quelques
     secondes sans aucune tuile chargée, le fond est désactivé et mémorisé comme
     indisponible — la carte reste entièrement lisible grâce au graticule, à
     l'échelle et aux symboles, qui ne dépendent d'aucune ressource externe. */
  function surveillerFondCarte(conteneur, surIndisponibilite) {
    const images = Array.from((conteneur || document).querySelectorAll('.carte-cadre img'));
    if (!images.length) return;
    setTimeout(function () {
      if (!document.body.contains(images[0])) return;
      const chargees = images.filter((i) => i.complete && i.naturalWidth > 0).length;
      if (chargees > 0) return;
      images.forEach((i) => { i.style.display = 'none'; });
      localStorage.setItem('sepia_fond_carte', '0');
      localStorage.setItem('sepia_fond_indisponible', '1');
      const cadre = images[0].closest('.carte-cadre');
      if (cadre && !cadre.querySelector('.avis-fond-carte')) {
        const avis = document.createElement('div');
        avis.className = 'avis-fond-carte';
        avis.textContent = 'Fond de carte indisponible sur ce réseau — la carte reste ' +
          'exploitable (graticule, échelle et symboles).';
        cadre.appendChild(avis);
      }
      if (typeof surIndisponibilite === 'function') surIndisponibilite();
    }, 6000);
  }

  global.Graphiques = {
    anneau: anneau, barres: barres, courbes: courbes, jauge: jauge,
    matriceRisques: matriceRisques, gantt: gantt, colonnes: colonnes,
    pert: pert, wbs: wbs, carte: carte, surveillerFondCarte: surveillerFondCarte,
    PALETTE: PALETTE
  };
})(window);
