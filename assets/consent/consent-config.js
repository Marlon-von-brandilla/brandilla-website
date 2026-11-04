/*
 * brandilla – Cookie-Einwilligung (DSGVO / § 25 TDDDG)
 *
 * - Google Analytics 4 wird erst NACH Zustimmung geladen (kein Request an Google vorher).
 * - YouTube-Videos laden erst nach Zustimmung zu "Externe Medien" (youtube-nocookie.com).
 * - Widerruf jederzeit über jeden Link mit data-cc="show-preferencesModal".
 *
 * Bibliothek: vanilla-cookieconsent v3 (MIT, lokal gehostet unter /assets/consent/).
 * Bei inhaltlichen Änderungen (neue Dienste) REVISION erhöhen → alle Besucher werden neu gefragt.
 */
(function () {
  'use strict';

  var GA_ID = 'G-02C7GTHDB3';
  var REVISION = 1;
  var gaLoaded = false;

  /* ---------- Google Analytics (nur nach Einwilligung) ---------- */
  function loadGA() {
    if (gaLoaded) return;
    gaLoaded = true;
    window['ga-disable-' + GA_ID] = false;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('consent', 'default', {
      analytics_storage: 'granted',
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied'
    });
    window.gtag('js', new Date());
    window.gtag('config', GA_ID);
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
  }

  function disableGA() {
    window['ga-disable-' + GA_ID] = true;
    if (window.gtag) {
      window.gtag('consent', 'update', { analytics_storage: 'denied' });
    }
    // GA-Cookies auf allen möglichen Domains entfernen
    var host = location.hostname;
    var domains = ['', host, '.' + host, '.' + host.replace(/^www\./, '')];
    document.cookie.split(';').forEach(function (c) {
      var name = c.split('=')[0].trim();
      if (/^_ga/.test(name) || name === '_gid' || name === '_gat') {
        domains.forEach(function (d) {
          document.cookie = name + '=; Max-Age=0; path=/' + (d ? '; domain=' + d : '');
        });
      }
    });
  }

  /* ---------- YouTube (Externe Medien) ---------- */
  var mediaPlaceholderText =
    'Hier ist ein YouTube-Video eingebettet. Beim Abspielen werden Daten (u. a. Ihre IP-Adresse) ' +
    'an Google/YouTube übertragen.';

  function activateMedia() {
    document.querySelectorAll('iframe[data-cc-src]').forEach(function (f) {
      if (!f.getAttribute('src')) f.setAttribute('src', f.getAttribute('data-cc-src'));
      var ph = f.parentNode && f.parentNode.querySelector('.cc-media-ph');
      if (ph) ph.remove();
    });
  }

  function addPlaceholders() {
    document.querySelectorAll('iframe[data-cc-src]').forEach(function (f) {
      if (f.getAttribute('src')) return;
      var parent = f.parentNode;
      if (!parent || parent.querySelector('.cc-media-ph')) return;
      if (getComputedStyle(parent).position === 'static') parent.style.position = 'relative';
      var ph = document.createElement('div');
      ph.className = 'cc-media-ph';
      ph.innerHTML =
        '<div class="cc-media-ph__inner">' +
        '<p>' + mediaPlaceholderText + '</p>' +
        '<button type="button" class="cc-media-ph__btn">Video laden</button>' +
        '<button type="button" class="cc-media-ph__link" data-cc="show-preferencesModal">Einstellungen</button>' +
        '</div>';
      ph.querySelector('.cc-media-ph__btn').addEventListener('click', function () {
        var accepted = CookieConsent.getUserPreferences().acceptedCategories || [];
        if (accepted.indexOf('media') === -1) accepted.push('media');
        CookieConsent.acceptCategory(accepted);
      });
      parent.appendChild(ph);
    });
  }

  /* ---------- Zustand anwenden ---------- */
  function applyConsent() {
    if (CookieConsent.acceptedCategory('analytics')) loadGA(); else disableGA();
    if (CookieConsent.acceptedCategory('media')) activateMedia(); else addPlaceholders();
  }

  function onChange(ctx) {
    // Analytics widerrufen → Seite neu laden, damit bereits geladenes GA sicher entfernt ist
    var changed = (ctx && ctx.changedCategories) || [];
    if (changed.indexOf('analytics') !== -1 && !CookieConsent.acceptedCategory('analytics') && gaLoaded) {
      disableGA();
      location.reload();
      return;
    }
    applyConsent();
  }

  function init() {
    if (!window.CookieConsent) return;

    CookieConsent.run({
      revision: REVISION,
      cookie: { name: 'cc_brandilla', expiresAfterDays: 182 },
      guiOptions: {
        consentModal: { layout: 'box', position: 'bottom left', equalWeightButtons: true, flipButtons: false },
        preferencesModal: { layout: 'box', equalWeightButtons: true, flipButtons: false }
      },
      onFirstConsent: applyConsent,
      onConsent: applyConsent,
      onChange: onChange,
      categories: {
        necessary: { enabled: true, readOnly: true },
        analytics: {},
        media: {}
      },
      language: {
        default: 'de',
        translations: {
          de: {
            consentModal: {
              title: 'Kurz zu Cookies 🍪',
              description:
                'Wir möchten mit Google Analytics verstehen, wie unsere Website genutzt wird, und YouTube-Videos einbinden. ' +
                'Dafür brauchen wir Ihre Einwilligung. Dabei können Daten in die USA übertragen werden. ' +
                'Sie können Ihre Auswahl jederzeit über „Cookie-Einstellungen“ im Footer ändern.',
              acceptAllBtn: 'Alle akzeptieren',
              acceptNecessaryBtn: 'Nur notwendige',
              showPreferencesBtn: 'Einstellungen',
              footer: '<a href="/datenschutz">Datenschutz</a> <a href="/impressum">Impressum</a>'
            },
            preferencesModal: {
              title: 'Cookie-Einstellungen',
              acceptAllBtn: 'Alle akzeptieren',
              acceptNecessaryBtn: 'Nur notwendige',
              savePreferencesBtn: 'Auswahl speichern',
              closeIconLabel: 'Schließen',
              sections: [
                {
                  description:
                    'Hier entscheiden Sie, welche Dienste wir nutzen dürfen. Ihre Einwilligung ist freiwillig ' +
                    'und kann jederzeit mit Wirkung für die Zukunft widerrufen werden. Mehr in unserer ' +
                    '<a href="/datenschutz">Datenschutzerklärung</a>.'
                },
                {
                  title: 'Notwendig',
                  description:
                    'Speichert Ihre Cookie-Auswahl (Cookie „cc_brandilla“, 6 Monate). Ohne diese Speicherung ' +
                    'müssten wir Sie bei jedem Besuch neu fragen.',
                  linkedCategory: 'necessary'
                },
                {
                  title: 'Statistik – Google Analytics',
                  description:
                    'Google Analytics 4 (Google Ireland Ltd.) hilft uns zu verstehen, welche Seiten besucht werden ' +
                    'und woher Besucher kommen. Cookies: _ga, _ga_* (bis 14 Monate). Eine Übermittlung in die USA ' +
                    'ist möglich (EU-US Data Privacy Framework).',
                  linkedCategory: 'analytics'
                },
                {
                  title: 'Externe Medien – YouTube',
                  description:
                    'Lädt eingebettete YouTube-Videos (Google Ireland Ltd.) im erweiterten Datenschutzmodus. ' +
                    'Beim Laden wird u. a. Ihre IP-Adresse an YouTube übertragen.',
                  linkedCategory: 'media'
                }
              ]
            }
          }
        }
      }
    }).then(applyConsent);

    // Für dynamisch nachgeladene Videos (z. B. Video-Grid auf /marketing-wissen)
    new MutationObserver(function () {
      if (CookieConsent.acceptedCategory('media')) activateMedia(); else addPlaceholders();
    }).observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
