# Breadcrumb-Rollout: BreadcrumbList-JSON-LD auf alle Standard-Seiten.
# Muster/Referenz: pflege.html (Commit 0d3d78c, Rich-Results-Test 0 Fehler).
# Hierarchie = Nav-Struktur (Hub > Spoke), Namen woertlich aus den Nav-Labels.
# Canonical wird pro Seite aus <link rel="canonical"> der Seite selbst gelesen
# und gegen die erwartete Pretty-URL geprueft (Artikel: .html laut Canonical).
#
# Einfuegestelle: direkt nach dem LETZTEN vorhandenen ld+json-Block im <head>;
# hat eine Seite keinen ld+json-Block, direkt vor </head>.
#
# Aufruf:  python scripts/rollout-breadcrumbs.py           -> DRY-RUN (nichts schreiben)
#          python scripts/rollout-breadcrumbs.py --apply   -> real einfuegen + Verify
import sys, re, json, io, hashlib

APPLY = '--apply' in sys.argv
BASE = 'https://brandilla.de'

# Hubs: Name = Label des Nav-Dropdown-Triggers, URL = Trigger-Ziel
HUB = {
    'produkte':        ('Produkte',        '/produkte'),
    'recruiting':      ('Recruiting',      '/recruiting'),
    'kunden-gewinnen': ('Kunden gewinnen', '/kunden-gewinnen'),
    'wissen':          ('Marketing-Wissen', '/marketing-wissen'),
}

# Datei -> (Hub-Key oder None, Seitenname, erwarteter Canonical-Pfad)
SEITEN = {
    # Ebene 2 (Hubs und Einzelseiten)
    'produkte.html':               (None, 'Produkte',        '/produkte'),
    'recruiting.html':             (None, 'Recruiting',      '/recruiting'),
    'kunden-gewinnen.html':        (None, 'Kunden gewinnen', '/kunden-gewinnen'),
    'marketing-wissen.html':       (None, 'Marketing-Wissen', '/marketing-wissen'),
    'kampagnen.html':              (None, 'Kampagnen',       '/kampagnen'),
    'preise.html':                 (None, 'Preise',          '/preise'),
    'partner.html':                (None, 'Partner',         '/partner'),
    'shop.html':                   (None, 'Cup Shop',        '/shop'),
    'kontakt.html':                (None, 'Kontakt',         '/kontakt'),
    # Ebene 3: Produkte
    'coffee-cup-werbung.html':     ('produkte', 'Coffee Cup Werbung',     '/coffee-cup-werbung'),
    'baeckertueten-werbung.html':  ('produkte', 'Bäckertüten Werbung',    '/baeckertueten-werbung'),
    'pizzaschachtel-werbung.html': ('produkte', 'Pizzaschachtel Werbung', '/pizzaschachtel-werbung'),
    'bierdeckel-werbung.html':     ('produkte', 'Bierdeckel Werbung',     '/bierdeckel-werbung'),
    # Ebene 3: Recruiting (pflege.html = Referenz, bereits fertig)
    'handwerk.html':               ('recruiting', 'Handwerk', '/handwerk'),
    # Ebene 3: Kunden gewinnen
    'neukundengewinnung.html':     ('kunden-gewinnen', 'Neukundengewinnung',   '/neukundengewinnung'),
    'promotion.html':              ('kunden-gewinnen', 'Produkt & Promotion',  '/promotion'),
    'bank.html':                   ('kunden-gewinnen', 'Banken & Sparkassen',  '/bank'),
    # Ebene 3: Wissen
    'gorilla-talk.html':           ('wissen', 'Gorilla Talk', '/gorilla-talk'),
    'artikel-wahrnehmungen.html':    ('wissen', '6–8 Wahrnehmungen pro Cup', '/artikel-wahrnehmungen.html'),
    'artikel-recruiting-cups.html':  ('wissen', 'Recruiting auf Coffee Cups', '/artikel-recruiting-cups.html'),
    'artikel-qr-tracking.html':      ('wissen', 'QR-Code pro POS', '/artikel-qr-tracking.html'),
    'artikel-nachhaltigkeit.html':   ('wissen', 'Wasserlack & ESG-Reporting', '/artikel-nachhaltigkeit.html'),
    'artikel-haptik.html':           ('wissen', 'Haptik im TakeAway Marketing', '/artikel-haptik.html'),
    'artikel-geomarketing.html':     ('wissen', 'Geomarketing', '/artikel-geomarketing.html'),
}
# Artikel haben kein Nav-Label -> Kurznamen von Sven festgelegt (2026-09-07);
# Fallback aus <title> nur falls ein Name None ist.
def artikel_name(src):
    m = re.search(r'<title>(.*?)</title>', src, re.S)
    if not m: return None
    return re.sub(r'\s*\|\s*brandilla\s*$', '', m.group(1).strip())

LD_RE = re.compile(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', re.S)

def build_block(items):
    rows = []
    for i, (name, url) in enumerate(items, 1):
        rows.append('    { "@type": "ListItem", "position": %d, "name": %s, "item": %s }'
                    % (i, json.dumps(name, ensure_ascii=False), json.dumps(url)))
    return ('<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n'
            '  "@type": "BreadcrumbList",\n  "itemListElement": [\n' + ',\n'.join(rows) +
            '\n  ]\n}\n</script>\n')

out = io.StringIO()
def log(s): print(s); out.write(s + '\n')
log(('APPLY' if APPLY else 'DRY-RUN') + f' — {len(SEITEN)} Seiten')

fehler, plan = [], []
for f, (hub, name, exp_path) in SEITEN.items():
    src = open(f, encoding='utf-8').read()
    # 1) Canonical aus der Seite selbst
    m = re.search(r'<link rel="canonical" href="([^"]+)"', src)
    canon = m.group(1) if m else None
    if canon != BASE + exp_path:
        fehler.append(f'{f}: Canonical "{canon}" != erwartet "{BASE + exp_path}"'); continue
    # 2) Name
    if name is None:
        name = artikel_name(src)
        if not name: fehler.append(f'{f}: kein <title> fuer Artikelnamen'); continue
    # 3) Bereits vorhanden?
    types = [json.loads(b).get('@type') for b in LD_RE.findall(src)]
    if 'BreadcrumbList' in types:
        fehler.append(f'{f}: hat bereits BreadcrumbList -> ueberspringen'); continue
    # 4) Hierarchie
    items = [('Start', BASE + '/')]
    if hub: items.append((HUB[hub][0], BASE + HUB[hub][1]))
    items.append((name, canon))
    # 5) Einfuegestelle
    head_end = src.find('</head>')
    if head_end < 0: fehler.append(f'{f}: kein </head>'); continue
    last = None
    for mm in LD_RE.finditer(src):
        if mm.end() <= head_end: last = mm
    if last:
        pos = last.end(); anker = 'nach letztem ld+json-Block (' + str(types) + ')'
        neu = src[:pos] + '\n\n' + build_block(items).rstrip('\n') + src[pos:]
    else:
        pos = head_end; anker = 'vor </head> (kein ld+json vorhanden)'
        neu = src[:pos] + build_block(items) + src[pos:]
    plan.append((f, items, anker, neu))
    log(f'{f:32s} ' + ' > '.join(n for n, _ in items))
    log(f'{"":32s} items: ' + ' | '.join(u for _, u in items))
    log(f'{"":32s} anker: {anker}')

for e in fehler: log('FEHLER/SKIP: ' + e)
log(f'geplant: {len(plan)} Seiten, Fehler/Skip: {len(fehler)}')

if APPLY:
    if fehler: sys.exit('ABBRUCH: erst Fehler klaeren.')
    for f, items, anker, neu in plan:
        # Verify: alle ld+json-Bloecke der neuen Datei parsebar, genau 1 BreadcrumbList
        blocks = [json.loads(b) for b in LD_RE.findall(neu)]
        assert sum(1 for b in blocks if b.get('@type') == 'BreadcrumbList') == 1, f
        open(f, 'w', encoding='utf-8', newline='\n').write(neu)
        log(f'GESCHRIEBEN {f} sha256={hashlib.sha256(neu.encode("utf-8")).hexdigest()[:12]}')
open('scripts/rollout-breadcrumbs.log', 'w', encoding='utf-8').write(out.getvalue())
