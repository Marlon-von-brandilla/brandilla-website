#!/usr/bin/env python3
"""
Rollout: DSGVO-konforme Einbindung von Fonts, Google Analytics und YouTube.

- Google Fonts (fonts.googleapis.com) -> lokale Schriften /assets/fonts/fonts.css
- Google Analytics direkt im <head> -> entfernt; GA lädt erst nach Einwilligung
  über /assets/consent/consent-config.js
- Cookie-Banner (vanilla-cookieconsent, lokal) in jede Seite einbinden
- "Cookie-Einstellungen"-Link im Footer neben "Datenschutz"
- YouTube-Embeds -> youtube-nocookie.com, Laden erst nach Einwilligung
- three.js von cdnjs -> lokal /assets/vendor/

Idempotent: kann mehrfach laufen. Aufruf im Repo-Root:  python3 scripts/rollout-consent.py
"""
import glob
import re
import sys

V = "1"  # Cache-Buster: bei Änderungen an den Assets erhöhen (netlify.toml cached js/css 1 Jahr)

HEAD_INCLUDE = (
    f'<link rel="stylesheet" href="/assets/fonts/fonts.css?v={V}">\n'
    f'<link rel="stylesheet" href="/assets/consent/cookieconsent.css?v={V}">\n'
    f'<link rel="stylesheet" href="/assets/consent/consent.css?v={V}">\n'
    f'<script defer src="/assets/consent/cookieconsent.umd.js?v={V}"></script>\n'
    f'<script defer src="/assets/consent/consent-config.js?v={V}"></script>\n'
)
MARKER = "/assets/consent/consent-config.js"

RE_PRECONNECT = re.compile(
    r'[ \t]*<link rel="preconnect" href="https://(fonts\.googleapis\.com|fonts\.gstatic\.com|cdnjs\.cloudflare\.com)"[^>]*>[ \t]*\n?'
)
RE_GFONTS = re.compile(r'[ \t]*<link href="https://fonts\.googleapis\.com/css2\?[^"]*" rel="stylesheet">[ \t]*\n?')
RE_GA = re.compile(
    r'[ \t]*(<!--\s*Google Analytics\s*-->\s*)?'
    r'<script async src="https://www\.googletagmanager\.com/gtag/js\?id=G-02C7GTHDB3"></script>\s*'
    r'<script>[^<]*?gtag\(\s*\'config\'\s*,\s*\'G-02C7GTHDB3\'\s*(,\s*\{[^}]*\})?\s*\);?\s*</script>[ \t]*\n?'
)
RE_FOOTER_DS = re.compile(r'([ \t]*)(<li>\s*<a href="[^"]*datenschutz[^"]*">Datenschutz</a>\s*</li>)')
COOKIE_LI = '<li><a href="#" data-cc="show-preferencesModal">Cookie-Einstellungen</a></li>'
# Footer ohne Datenschutz-Link (z. B. gorilla-talk): Datenschutz + Cookie-Einstellungen hinter Impressum ergänzen
RE_FOOTER_IMP = re.compile(r'(<li><a href="impressum\.html">Impressum</a></li>)')
DS_LI = '<li><a href="datenschutz.html">Datenschutz</a></li>'
# Seiten ohne Tracking/Embeds und ohne Footer: kein Banner nötig
NO_CONSENT = {"pitch.html"}


def process(path):
    src = open(path, encoding="utf-8").read()
    s = src
    notes = []

    s, n = RE_PRECONNECT.subn("", s)
    if n: notes.append(f"preconnect -{n}")
    s, n = RE_GFONTS.subn("", s)
    if n: notes.append("google-fonts -> lokal")
    s, n = RE_GA.subn("", s)
    if n: notes.append("GA aus <head> entfernt")

    if path in NO_CONSENT:
        if "/assets/fonts/fonts.css" not in s:
            s = s.replace("</head>", f'<link rel="stylesheet" href="/assets/fonts/fonts.css?v={V}">\n</head>', 1)
        if s != src:
            open(path, "w", encoding="utf-8").write(s)
        return notes + ["(ohne Banner)"]

    if MARKER not in s:
        s = s.replace("</head>", HEAD_INCLUDE + "</head>", 1)
        notes.append("consent eingebunden")

    if COOKIE_LI not in s:
        s, n = RE_FOOTER_DS.subn(lambda m: m.group(1) + m.group(2) + "\n" + m.group(1) + COOKIE_LI, s, count=1)
        if n: notes.append("footer-link")
        else:
            s, n = RE_FOOTER_IMP.subn(lambda m: m.group(1) + DS_LI + COOKIE_LI, s, count=1)
            notes.append("footer: Datenschutz + Cookie-Link ergänzt" if n else "!! KEIN footer-link gefunden")

    # YouTube: erst nach Einwilligung laden, erweiterter Datenschutzmodus
    s, n = re.subn(r'\ssrc="https://www\.youtube\.com/embed/', ' data-cc-src="https://www.youtube-nocookie.com/embed/', s)
    if n: notes.append(f"youtube x{n}")

    # three.js lokal statt cdnjs
    s, n = re.subn(r'https://cdnjs\.cloudflare\.com/ajax/libs/three\.js/r128/three\.min\.js', '/assets/vendor/three-r128.min.js', s)
    if n: notes.append("three.js lokal")

    if s != src:
        open(path, "w", encoding="utf-8").write(s)
    return notes


def main():
    files = sorted(glob.glob("*.html"))
    problems = 0
    for f in files:
        notes = process(f)
        print(f"{f:32s} {', '.join(notes) or 'unverändert'}")
        txt = open(f, encoding="utf-8").read()
        for bad in ("fonts.googleapis.com", "fonts.gstatic.com", "googletagmanager.com/gtag", "youtube.com/embed", "cdnjs.cloudflare.com"):
            if bad in txt:
                print(f"   !! {bad} noch enthalten"); problems += 1
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
