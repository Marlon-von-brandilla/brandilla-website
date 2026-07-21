# Nav-Rollout #2: Kunden-gewinnen-Dropdown + Wissen-Dropdown + Breakpoint-Fix (1100->1260).
# Referenz fuer die NEUEN HTML-Bloecke: recruiting.html (Pilot #2 + #2b).
# Muster: strenger exakter String-Match (wie rollout-recruiting-nav.py), Dry-Run default.
#
# Aufruf:  python scripts/rollout-nav2.py           -> DRY-RUN
#          python scripts/rollout-nav2.py --apply   -> real schreiben + Verify
import sys, glob, hashlib, re, collections

APPLY = '--apply' in sys.argv
REFERENZ = 'recruiting.html'
PITCH = 'pitch.html'                                # eigene Nav, komplett raus
MOBILE_FEHLT_BEKANNT = {'artikel-template.html'}    # kein Mobile-Menue-Div

# ---------- ALT-Bloecke = exakter Stand der 27 Nicht-Referenz-Dateien ----------
ALT_DESKTOP = '''    <li class="nav-dropdown">
      <a href="recruiting.html" class="nav-dropdown-trigger">Recruiting <span class="nav-arrow">▾</span></a>
      <div class="nav-dropdown-menu">
        <a href="recruiting.html">Recruiting-Übersicht</a>
        <a href="/pflege">Pflege</a>
        <a href="/handwerk">Handwerk</a>
      </div>
    </li>
    <li><a href="gorilla-talk.html">Gorilla Talk</a></li>
    <li><a href="preise.html">Preise</a></li>
    <li><a href="marketing-wissen.html">Marketing-Wissen</a></li>
    <li><a href="partner.html">Partner</a></li>'''

ALT_MOBILE = '''  <details class="nav-mobile-group">
    <summary>Recruiting</summary>
    <a href="recruiting.html">Recruiting-Übersicht</a>
    <a href="/pflege">Pflege</a>
    <a href="/handwerk">Handwerk</a>
  </details>
  <a href="gorilla-talk.html">Gorilla Talk</a>
  <a href="preise.html">Preise</a>
  <a href="marketing-wissen.html">Marketing-Wissen</a>
  <a href="partner.html">Partner</a>'''

ALT_CSS = '''@media(max-width:1100px){
  .nav-links { gap: 20px; }
  .nav-links a { font-size: 10px; }
}'''

NEU_CSS = '''@media(max-width:1260px){
  .nav-links { gap: 20px; }
  .nav-links a { font-size: 10px; }
}'''

# Fuer Dateien OHNE Kompakt-Query: Einfuege-Anker (byte-identischer Nav-Dropdown-CSS-Abschluss,
# verifiziert exakt 1x in allen 30 Standard-Dateien). Query wird DANACH eingefuegt.
CSS_ANKER = '@media(max-width:900px){.nav-dropdown-menu{display:none!important}}'

# ---------- NEUE HTML-Bloecke aus der Referenz AUSLESEN ----------
ref = open(REFERENZ, encoding='utf-8').read()
m_d = re.search(r'    <li class="nav-dropdown">\n      <a href="recruiting\.html" class="nav-dropdown-trigger">Recruiting .*?<li><a href="partner\.html">Partner</a></li>', ref, re.S)
m_m = re.search(r'  <details class="nav-mobile-group">\n    <summary>Recruiting</summary>.*?  <a href="partner\.html">Partner</a>', ref, re.S)
if not m_d or not m_m:
    sys.exit('FEHLER: Referenzbloecke in recruiting.html nicht gefunden.')
NEU_DESKTOP, NEU_MOBILE = m_d.group(0), m_m.group(0)
for must in ['Kunden gewinnen', 'href="/kunden-gewinnen"', 'href="/neukundengewinnung"', 'href="/promotion"', 'href="/bank"',
             '>Wissen <span', 'marketing-wissen.html">Marketing-Wissen</a>', 'gorilla-talk.html">Gorilla Talk</a>']:
    assert must in NEU_DESKTOP, f'Desktop-Referenzblock unvollstaendig: {must}'
for must in ['<summary>Kunden gewinnen</summary>', '<summary>Wissen</summary>', 'href="/bank"']:
    assert must in NEU_MOBILE, f'Mobile-Referenzblock unvollstaendig: {must}'
assert '<li><a href="gorilla-talk.html">Gorilla Talk</a></li>' not in NEU_DESKTOP
assert '<li><a href="marketing-wissen.html">Marketing-Wissen</a></li>' not in NEU_DESKTOP

print(('APPLY' if APPLY else 'DRY-RUN') + f' | NEU-Desktop {len(NEU_DESKTOP)}b, NEU-Mobile {len(NEU_MOBILE)}b aus {REFERENZ}')

alle = sorted(glob.glob('*.html'))
kandidaten = [f for f in alle if f not in (REFERENZ, PITCH)]
fehler, geaendert, css_add, css_repl = [], [], [], []

# Referenz selbst: braucht evtl. noch den CSS-Fix (Pilot #2b enthielt ihn NICHT)
ref_braucht_css = ALT_CSS in ref
print(f'Referenz {REFERENZ}: CSS-Fix noetig = {ref_braucht_css}')

def bearbeite(f, src, nur_css=False):
    zeilen, ok = [], True
    if not nur_css:
        for name, alt, neu in [('Desktop', ALT_DESKTOP, NEU_DESKTOP), ('Mobile', ALT_MOBILE, NEU_MOBILE)]:
            n = src.count(alt)
            if n == 1:
                zeilen.append(f'{name}: 1 Treffer -> ersetzen'); src = src.replace(alt, neu)
            elif n == 0 and name == 'Mobile' and f in MOBILE_FEHLT_BEKANNT:
                zeilen.append('Mobile: 0 (bekannt, kein Mobile-Menue) -> skip')
            else:
                zeilen.append(f'{name}: {n} Treffer -> FEHLER'); ok = False
    # CSS: ersetzen wenn vorhanden, sonst am Anker einfuegen
    n_css = src.count(ALT_CSS)
    if n_css == 1:
        zeilen.append('CSS: 1100->1260 ersetzen'); src = src.replace(ALT_CSS, NEU_CSS); css_repl.append(f)
    elif n_css == 0:
        if NEU_CSS in src:
            zeilen.append('CSS: 1260 schon vorhanden -> skip')
        elif src.count(CSS_ANKER) == 1:
            zeilen.append('CSS: Query fehlt -> nach Nav-Dropdown-CSS EINFUEGEN'); src = src.replace(CSS_ANKER, CSS_ANKER + '\n' + NEU_CSS); css_add.append(f)
        else:
            zeilen.append(f'CSS: Query fehlt UND Anker {src.count(CSS_ANKER)}x -> FEHLER'); ok = False
    else:
        zeilen.append(f'CSS: {n_css} Treffer -> FEHLER'); ok = False
    return src, zeilen, ok

for f in kandidaten:
    src = open(f, encoding='utf-8').read()
    neu_src, zeilen, ok = bearbeite(f, src)
    tag = 'FEHLER' if not ok else ('WRITE' if APPLY else 'WUERDE')
    print(f'  [{tag}] {f}: ' + ' | '.join(zeilen))
    if not ok: fehler.append(f); continue
    geaendert.append(f)
    if APPLY: open(f, 'w', encoding='utf-8', newline='').write(neu_src)

# Referenz: nur CSS
if ref_braucht_css:
    neu_ref, zeilen, ok = bearbeite(REFERENZ, ref, nur_css=True)
    tag = 'FEHLER' if not ok else ('WRITE' if APPLY else 'WUERDE')
    print(f'  [{tag}] {REFERENZ} (nur CSS): ' + ' | '.join(zeilen))
    if ok:
        geaendert.append(REFERENZ)
        if APPLY: open(REFERENZ, 'w', encoding='utf-8', newline='').write(neu_ref)
    else:
        fehler.append(REFERENZ)

print(f'\nErgebnis: {len(geaendert)} Dateien ({len(css_repl)} CSS-Ersatz, {len(css_add)} CSS-Neueinbau), {len(fehler)} Fehler')
if css_add: print('CSS neu eingebaut in:', ', '.join(css_add))
if fehler: print('FEHLER:', ', '.join(fehler))

# ---------- Verify ----------
std = sorted(set(alle) - {PITCH})
g_d, g_m = collections.defaultdict(list), collections.defaultdict(list)
probleme = []
for f in std:
    s = open(f, encoding='utf-8').read()
    d = re.search(r'<nav[ >].*?</nav>', s, re.S)
    mm = re.search(r'<div class="nav-mobile-menu"[^>]*>.*?</div>\s*(?=\n*<!--|\n*<section|\n*<header|\n*<main|\n*<div)', s, re.S)
    g_d[hashlib.md5(d.group(0).encode()).hexdigest()[:10] if d else 'FEHLT'].append(f)
    g_m[hashlib.md5(mm.group(0).encode()).hexdigest()[:10] if mm else 'FEHLT'].append(f)
    # Alt-Eintraege NUR im Nav-Bereich pruefen (Footer-Spalten verlinken Gorilla Talk /
    # Marketing-Wissen legitim weiter — das ist kein Sweep-Gegenstand)
    navbereich = (d.group(0) if d else '') + (mm.group(0) if mm else '')
    if 'Kunden gewinnen' not in navbereich: probleme.append(f'{f}: "Kunden gewinnen" fehlt in Nav')
    if '>Wissen <span' not in navbereich: probleme.append(f'{f}: Wissen-Dropdown fehlt in Nav')
    if '<li><a href="gorilla-talk.html">Gorilla Talk</a></li>' in navbereich: probleme.append(f'{f}: alter Gorilla-Talk-Top-Level noch in Nav')
    if '<li><a href="marketing-wissen.html">Marketing-Wissen</a></li>' in navbereich: probleme.append(f'{f}: alter Marketing-Wissen-Top-Level noch in Nav')
    if ALT_CSS in s: probleme.append(f'{f}: Breakpoint noch 1100')
    if NEU_CSS not in s: probleme.append(f'{f}: Breakpoint 1260 fehlt')
print(f'\nHash-Verify Desktop-Nav: {len(g_d)} Variante(n)')
for h, fs in sorted(g_d.items(), key=lambda x: -len(x[1])):
    print(f'  {h}: {len(fs)}' + ('' if len(fs) > 4 else ' -> ' + ', '.join(fs)))
print(f'Hash-Verify Mobile-Menu: {len(g_m)} Variante(n)')
for h, fs in sorted(g_m.items(), key=lambda x: -len(x[1])):
    print(f'  {h}: {len(fs)}' + ('' if len(fs) > 4 else ' -> ' + ', '.join(fs)))
print('Grep-Checks:', 'alle OK ✓' if not probleme else f'{len(probleme)} Problem(e)')
for p in probleme[:40]: print('  -', p)
