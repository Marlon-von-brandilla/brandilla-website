# Cookie-Einwilligung & lokale Schriften

**Was geändert wurde**
- Google Fonts → lokal (`/assets/fonts/`), keine Verbindung mehr zu Google beim Seitenaufruf
- Google Analytics lädt erst nach Klick auf „Alle akzeptieren“ bzw. Häkchen bei „Statistik“
- YouTube (nur /marketing-wissen): Platzhalter mit „Video laden“, danach youtube-nocookie.com
- three.js im Shop lokal statt cdnjs
- Footer: Link „Cookie-Einstellungen“ (Widerruf); auf gorilla-talk und artikel-template fehlte zudem der Datenschutz-Link
- Datenschutzerklärung: Abschnitte Cookies, Google Analytics, YouTube, Schriftarten neu (Stand November 2026)

**Dateien**
- `consent-config.js` – Texte des Banners, GA-ID, Kategorien
- `consent.css` – brandilla-Look
- `cookieconsent.umd.js / .css` – Bibliothek vanilla-cookieconsent 3.3.0 (MIT)

**Später etwas ändern**
- Neuer Dienst (z. B. Meta Pixel, Google Ads)? → in `consent-config.js` Kategorie ergänzen, `REVISION` erhöhen (alle werden neu gefragt) und Datenschutzerklärung ergänzen.
- Nach Änderungen an CSS/JS: in `scripts/rollout-consent.py` `V` erhöhen und das Skript laufen lassen
  (netlify.toml cached .js/.css ein Jahr; ohne neues `?v=` sehen Besucher die alte Version).
- Neue HTML-Seite: `python3 scripts/rollout-consent.py` einmal ausführen, das bindet alles ein.

**Einmalig in Google Analytics prüfen**
- Verwaltung → Kontoeinstellungen: „Datenverarbeitungsbedingungen“ akzeptiert (= Auftragsverarbeitungsvertrag)
- Verwaltung → Datenerfassung → Datenaufbewahrung: auf 14 Monate stellen (Standard ist 2)
