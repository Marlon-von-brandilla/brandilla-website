# Nav-Rollout: Recruiting-Dropdown mit Pflege+Handwerk auf alle Standard-Nav-Seiten.
# Muster: strenger exakter String-Match wie scripts/add-product-nav.js.
# Referenz fuer die NEUEN Bloecke ist recruiting.html (bereits umgebaut, Pilot).
#
# Aufruf:  python scripts/rollout-recruiting-nav.py           -> DRY-RUN (nichts schreiben)
#          python scripts/rollout-recruiting-nav.py --apply   -> real ersetzen + Hash-Verify
import sys, glob, hashlib, re, io

APPLY = '--apply' in sys.argv
ROOT = '.'

REFERENZ = 'recruiting.html'
AUSGESCHLOSSEN = {REFERENZ, 'pitch.html'}          # Referenz fertig, pitch = eigene Nav
MOBILE_FEHLT_BEKANNT = {'artikel-template.html'}   # kein Mobile-Menue-Div (bekannter Zustand)

# --- ALTE Bloecke (Stand aller 26 Bestandsdateien, byte-identisch verifiziert) ---
ALT_DESKTOP = '''    <li class="nav-dropdown">
      <a href="recruiting.html" class="nav-dropdown-trigger">Recruiting <span class="nav-arrow">▾</span></a>
      <div class="nav-dropdown-menu">
        <a href="recruiting.html">Recruiting-Übersicht</a>
      </div>
    </li>'''

ALT_MOBILE = '''  <details class="nav-mobile-group">
    <summary>Recruiting</summary>
    <a href="recruiting.html">Recruiting-Übersicht</a>
  </details>'''

# --- NEUE Bloecke: aus der Referenzdatei AUSLESEN (nicht neu tippen) ---
ref = open(REFERENZ, encoding='utf-8').read()
m_d = re.search(r'    <li class="nav-dropdown">\n      <a href="recruiting\.html" class="nav-dropdown-trigger">Recruiting .*?\n    </li>', ref, re.S)
m_m = re.search(r'  <details class="nav-mobile-group">\n    <summary>Recruiting</summary>.*?\n  </details>', ref, re.S)
if not m_d or not m_m:
    sys.exit('FEHLER: Neuer Desktop-/Mobile-Block in Referenz recruiting.html nicht gefunden.')
NEU_DESKTOP, NEU_MOBILE = m_d.group(0), m_m.group(0)
# Sicherheitscheck: Referenzbloecke muessen die 3 Eintraege enthalten und keine Labels
for must in ['Recruiting-Übersicht', 'href="/pflege"', 'href="/handwerk"']:
    assert must in NEU_DESKTOP and must in NEU_MOBILE, f'Referenzblock unvollstaendig: {must}'
assert 'group-label' not in NEU_DESKTOP + NEU_MOBILE and 'href="/bank"' not in NEU_DESKTOP + NEU_MOBILE

out = io.StringIO()
def log(s): print(s); out.write(s + '\n')

files = sorted(f for f in glob.glob('*.html') if f not in AUSGESCHLOSSEN)
log(('APPLY' if APPLY else 'DRY-RUN') + f' — {len(files)} Kandidaten (ohne {", ".join(sorted(AUSGESCHLOSSEN))})')

fehler, geaendert = [], []
for f in files:
    src = open(f, encoding='utf-8').read()
    zeilen = []
    ok = True
    for name, alt, neu in [('Desktop', ALT_DESKTOP, NEU_DESKTOP), ('Mobile', ALT_MOBILE, NEU_MOBILE)]:
        n = src.count(alt)
        if n == 1:
            zeilen.append(f'{name}: 1 Treffer -> ersetzen')
            src = src.replace(alt, neu)
        elif n == 0 and name == 'Mobile' and f in MOBILE_FEHLT_BEKANNT:
            zeilen.append('Mobile: 0 Treffer (bekannt, kein Mobile-Menue) -> ueberspringen')
        else:
            zeilen.append(f'{name}: {n} Treffer -> FEHLER, Datei wird NICHT angefasst')
            ok = False
    if not ok:
        fehler.append(f)
        log(f'  [FEHLER] {f}: ' + ' | '.join(zeilen))
        continue
    log(f'  [{"WRITE" if APPLY else "WUERDE"}] {f}: ' + ' | '.join(zeilen))
    geaendert.append(f)
    if APPLY:
        open(f, 'w', encoding='utf-8', newline='').write(src)

log(f'\nErgebnis: {len(geaendert)} Dateien {"geschrieben" if APPLY else "wuerden ersetzt"}, {len(fehler)} Fehler')
if fehler: log('FEHLER-Dateien: ' + ', '.join(fehler))

# --- Hash-Verifikation (nach APPLY; im Dry-Run nur Ist-Stand-Info) ---
import collections
std = sorted(set(glob.glob('*.html')) - {'pitch.html'})
g_d, g_m = collections.defaultdict(list), collections.defaultdict(list)
for f in std:
    s = open(f, encoding='utf-8').read()
    d = re.search(r'<nav[ >].*?</nav>', s, re.S)
    mm = re.search(r'<div class="nav-mobile-menu"[^>]*>.*?</div>\s*(?=\n*<!--|\n*<section|\n*<header|\n*<main|\n*<div)', s, re.S)
    g_d[hashlib.md5(d.group(0).encode()).hexdigest()[:10] if d else 'FEHLT'].append(f)
    g_m[hashlib.md5(mm.group(0).encode()).hexdigest()[:10] if mm else 'FEHLT'].append(f)
log(f'\nHash-Verify Desktop-Nav: {len(g_d)} Variante(n)')
for h, fs in sorted(g_d.items(), key=lambda x: -len(x[1])):
    log(f'  {h}: {len(fs)} Dateien' + ('' if len(fs) > 4 else ' -> ' + ', '.join(fs)))
log(f'Hash-Verify Mobile-Menu: {len(g_m)} Variante(n)')
for h, fs in sorted(g_m.items(), key=lambda x: -len(x[1])):
    log(f'  {h}: {len(fs)} Dateien' + ('' if len(fs) > 4 else ' -> ' + ', '.join(fs)))

# --- Label-Klassen duerfen nirgends mehr vorkommen ---
reste = [f for f in glob.glob('*.html') if 'nav-dropdown-group-label' in open(f, encoding='utf-8').read()
         or 'nav-mobile-group-label' in open(f, encoding='utf-8').read()]
log('Label-Klassen-Reste: ' + (', '.join(reste) if reste else 'keine ✓'))
