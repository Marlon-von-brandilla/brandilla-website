#!/usr/bin/env node
/**
 * Idempotent nav patcher: adds "Pizzaschachtel Werbung" under "Bäckertüten Werbung"
 * in both the desktop dropdown and the mobile menu of every HTML page.
 *
 * Marker:  <a href="baeckertueten-werbung.html">Bäckertüten Werbung</a>
 * Insert:  <a href="pizzaschachtel-werbung.html">Pizzaschachtel Werbung</a>  (preserves leading whitespace of marker line)
 *
 * Skips files where the insert line already follows the marker.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const MARKER = '<a href="baeckertueten-werbung.html">Bäckertüten Werbung</a>';
const INSERT = '<a href="pizzaschachtel-werbung.html">Pizzaschachtel Werbung</a>';

const files = fs.readdirSync(ROOT).filter(f => f.endsWith('.html'));

let touched = 0, skipped = 0;
for (const file of files) {
  const full = path.join(ROOT, file);
  const src = fs.readFileSync(full, 'utf8');
  if (!src.includes(MARKER)) { skipped++; continue; }

  const lines = src.split(/\r?\n/);
  const out = [];
  let changed = false;

  for (let i = 0; i < lines.length; i++) {
    out.push(lines[i]);
    if (lines[i].includes(MARKER)) {
      const indent = lines[i].match(/^\s*/)[0];
      const next = lines[i + 1] || '';
      if (!next.includes(INSERT)) {
        out.push(indent + INSERT);
        changed = true;
      }
    }
  }

  if (changed) {
    fs.writeFileSync(full, out.join('\n'));
    touched++;
    console.log('patched:', file);
  } else {
    skipped++;
  }
}
console.log(`\nDone — patched ${touched}, skipped ${skipped}`);
