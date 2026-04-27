#!/usr/bin/env node
/**
 * Idempotent nav patcher: ensures the configured product-nav entries appear
 * in order in every HTML page (both desktop dropdown and mobile menu).
 *
 * Each entry is { marker, insert }: when `marker` is found in a line, `insert`
 * is added on the line immediately after — but only if `insert` isn't already
 * there. Indentation of the marker line is preserved.
 *
 * Add a new product by appending to ENTRIES below and re-running the script.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

const ENTRIES = [
  {
    marker: '<a href="baeckertueten-werbung.html">Bäckertüten Werbung</a>',
    insert: '<a href="pizzaschachtel-werbung.html">Pizzaschachtel Werbung</a>',
  },
  {
    marker: '<a href="pizzaschachtel-werbung.html">Pizzaschachtel Werbung</a>',
    insert: '<a href="bierdeckel-werbung.html">Bierdeckel Werbung</a>',
  },
];

const files = fs.readdirSync(ROOT).filter(f => f.endsWith('.html'));

let touched = 0, skipped = 0;
for (const file of files) {
  const full = path.join(ROOT, file);
  let src = fs.readFileSync(full, 'utf8');
  let fileChanged = false;

  for (const { marker, insert } of ENTRIES) {
    if (!src.includes(marker)) continue;
    const lines = src.split(/\r?\n/);
    const out = [];
    let entryChanged = false;
    for (let i = 0; i < lines.length; i++) {
      out.push(lines[i]);
      if (lines[i].includes(marker)) {
        const indent = lines[i].match(/^\s*/)[0];
        const next = lines[i + 1] || '';
        if (!next.includes(insert)) {
          out.push(indent + insert);
          entryChanged = true;
        }
      }
    }
    if (entryChanged) {
      src = out.join('\n');
      fileChanged = true;
    }
  }

  if (fileChanged) {
    fs.writeFileSync(full, src);
    touched++;
    console.log('patched:', file);
  } else {
    skipped++;
  }
}
console.log(`\nDone — patched ${touched}, skipped ${skipped}`);
