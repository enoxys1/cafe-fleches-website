/* Grille du jour : choisit l'image du défi selon la date à Paris.
 *
 * Même calcul que l'app (home_state.dart, `_dayOfYear()`) :
 *   DateTime.now().difference(DateTime(année, 1, 1)).inDays + 1
 * `difference` mesure une durée réelle : à l'heure d'été, entre 0 h et 1 h,
 * elle compte une heure de moins que l'horloge, et l'app affiche encore le
 * défi de la veille. On reproduit ce comportement pour montrer la même
 * grille que l'application.
 *
 * Images : assets/daily/AAAA-MM-JJ.png, liste dans assets/daily/manifest.json
 * (tools/gen_daily.sh). Image absente : repli sur la dernière disponible.
 */
(function () {
  'use strict';

  var TZ = 'Europe/Paris';
  var BASE = '/cafe-fleches/assets/daily/';
  var img = document.getElementById('daily-img');
  var dateEl = document.getElementById('daily-date');
  var noteEl = document.getElementById('daily-note');
  if (!img) return;
  var lang = (document.documentElement.lang || 'fr').slice(0, 2);

  function parisParts(d) {
    var out = {};
    new Intl.DateTimeFormat('en-GB', {
      timeZone: TZ, hourCycle: 'h23',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    }).formatToParts(d).forEach(function (p) { out[p.type] = parseInt(p.value, 10); });
    return out;
  }

  // Décalage de Paris par rapport à UTC à l'instant d, en ms.
  function offsetMs(d) {
    var p = parisParts(d);
    var wall = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
    return wall - Math.floor(d.getTime() / 1000) * 1000;
  }

  function challengeDate(now) {
    var year = parisParts(now).year;
    var jan1Utc = Date.UTC(year, 0, 1);
    var jan1Instant = jan1Utc - offsetMs(new Date(jan1Utc));
    var days = Math.floor((now.getTime() - jan1Instant) / 86400000);
    return new Date(jan1Utc + days * 86400000).toISOString().slice(0, 10);
  }

  function label(iso) {
    var d = new Date(iso + 'T12:00:00Z');
    var s = new Intl.DateTimeFormat(lang === 'en' ? 'en-GB' : 'fr-FR', {
      timeZone: 'UTC', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    }).format(d);
    if (lang === 'en') return 'Challenge of ' + s;
    s = s.replace(/^(\S+) 1 /, '$1 1er ');
    return 'Défi du ' + s;
  }

  function altText(iso) {
    return lang === 'en'
      ? 'Café Fléchés arrow-word grid, daily challenge of ' + iso + ' (empty grid)'
      : 'Grille de mots fléchés Café Fléchés, ' + label(iso).toLowerCase() + ' (grille vide)';
  }

  function show(iso, today) {
    img.src = BASE + iso + '.png';
    img.alt = altText(iso);
    if (dateEl) dateEl.textContent = label(iso);
    if (noteEl) noteEl.hidden = iso === today;
  }

  var today = challengeDate(new Date());
  var fallbackSrc = img.getAttribute('src');
  img.addEventListener('error', function () {
    if (img.getAttribute('src') !== fallbackSrc) {
      img.src = fallbackSrc;
      if (noteEl) noteEl.hidden = false;
    }
  });

  function pick(dates) {
    if (!dates || !dates.length) return today;
    if (dates.indexOf(today) !== -1) return today;
    var best = null;
    dates.forEach(function (d) { if (d <= today && (!best || d > best)) best = d; });
    return best || dates[0];
  }

  if (window.fetch) {
    fetch(BASE + 'manifest.json', { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (m) { show(pick(m && m.dates), today); })
      .catch(function () { show(today, today); });
  } else {
    show(today, today);
  }

  var printBtn = document.getElementById('daily-print');
  if (printBtn) printBtn.addEventListener('click', function () { window.print(); });
})();
