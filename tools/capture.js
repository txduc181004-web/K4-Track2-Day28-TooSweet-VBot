// Capture evidence screenshots of official pricing pages with local Chrome.
// For each spec: open URL, optionally click a tab, locate the smallest table/block containing all
// `find` strings, switch the nearest region combobox above it to `region`, outline rows that
// contain a `mark` string in red, then screenshot from the combobox (if any) to the block bottom.
// usage: node tools/capture.js [ID ...]     (default: all)  -> evidence/screenshots/<ID>.png
const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');
const SPECS = require('./capture_specs.js');
const OUT = path.join(__dirname, '..', 'evidence', 'screenshots');
fs.mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function locate(page, spec) {
  return page.evaluate((find, kinds, index) => {
    const has = el => find.every(f => (el.innerText || '').includes(f));
    const cands = [...document.querySelectorAll(kinds)].filter(e => e.offsetParent !== null && has(e));
    if (!cands.length) return null;
    let el;
    if (index !== undefined && index !== null) el = cands[Math.min(index, cands.length - 1)];
    else { cands.sort((a, b) => (a.innerText.length - b.innerText.length)); el = cands[0]; }
    document.querySelectorAll('[data-ev-target]').forEach(e => e.removeAttribute('data-ev-target'));
    el.setAttribute('data-ev-target', '1');
    return true;
  }, spec.find, spec.kinds || 'table', spec.index);
}

async function setRegion(page, region) {
  // nearest combobox before target in document order
  const handle = await page.evaluateHandle(() => {
    const t = document.querySelector('[data-ev-target]');
    const boxes = [...document.querySelectorAll('[role=combobox]')].filter(b => b.offsetParent !== null &&
      (b.compareDocumentPosition(t) & Node.DOCUMENT_POSITION_FOLLOWING));
    const b = boxes[boxes.length - 1] || null;
    document.querySelectorAll('[data-ev-box]').forEach(e => e.removeAttribute('data-ev-box'));
    if (b) b.setAttribute('data-ev-box', '1');
    return b;
  });
  const box = handle.asElement();
  if (!box) return 'no-combobox';
  const cur = await page.evaluate(b => b.innerText, box);
  if (cur.includes(region)) return 'already';
  await box.evaluate(b => b.scrollIntoView({ block: 'center' }));
  await box.click();
  await sleep(700);
  const ok = await page.evaluate((region) => {
    const opts = [...document.querySelectorAll('li[role=option]')].filter(o => o.offsetParent !== null && o.innerText.replace(/[\u200e\u200f\u202a-\u202e]/g, '').trim() === region);
    if (!opts.length) return false;
    opts[0].click();
    return true;
  }, region);
  await sleep(2500);
  return ok ? 'set' : 'option-not-found';
}

async function shoot(browser, spec) {
  const page = await browser.newPage();
  await page.setViewport({ width: 2300, height: 1000, deviceScaleFactor: 1 });
  await page.setExtraHTTPHeaders({ 'Accept-Language': 'en-US,en;q=0.9' });
  const url = spec.url + (spec.url.includes('?') ? '&' : '?') + 'hl=en';
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 90000 });
  await sleep(1500);
  for (let i = 0; i < 30; i++) { await page.evaluate(() => window.scrollBy(0, 1500)); await sleep(150); }
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(500);
  if (spec.tab) {
    await page.evaluate((tab, near) => {
      const tabs = [...document.querySelectorAll('[role=tab], button, a')].filter(t => t.offsetParent !== null && t.innerText.trim() === tab);
      const pick = near ? tabs.find(t => (t.closest('section, div[class]')?.parentElement?.innerText || '').includes(near)) || tabs[0] : tabs[0];
      if (pick) pick.click();
    }, spec.tab, spec.tabNear || null);
    await sleep(1200);
  }
  if (!(await locate(page, spec))) { await page.close(); return `${spec.id}: target not found`; }
  let reg = '';
  if (spec.region && spec.tryIndexes) {
    for (let i = 0; i < 8; i++) {
      if (!(await locate(page, Object.assign({}, spec, { index: i })))) break;
      reg = await setRegion(page, spec.region);
      if (reg === 'set' || reg === 'already') { await locate(page, Object.assign({}, spec, { index: i })); break; }
      await page.keyboard.press('Escape'); await sleep(400);
    }
  } else if (spec.region) {
    reg = await setRegion(page, spec.region);
    await locate(page, spec);  // content may re-render after region change
  }
  await page.evaluate(() => {
    for (const e of document.querySelectorAll('body *')) {
      const pos = getComputedStyle(e).position;
      if (pos === 'fixed' || pos === 'sticky') {
        if (e.closest('table') || e.querySelector('[role=combobox], table') || e.closest('[role=listbox]')) e.style.position = 'static';
        else e.style.display = 'none';
      }
    }
  });
  await page.evaluate((marks) => {
    const t = document.querySelector('[data-ev-target]');
    for (let p = t.parentElement, i = 0; p && i < 8; p = p.parentElement, i++) { p.style.overflow = 'visible'; p.style.maxWidth = 'none'; }
    if (t.tagName === 'TABLE') { t.style.width = 'max-content'; t.style.maxWidth = 'none'; }
    const rows = t.tagName === 'TABLE' ? [...t.querySelectorAll('tr')] : [t];
    for (const r of rows) if (marks.some(m => (r.innerText || '').includes(m))) { r.style.outline = '3px solid #d0021b'; r.style.outlineOffset = '-2px'; }
    t.scrollIntoView({ block: 'start' });
  }, spec.mark || []);
  await sleep(500);
  const clip = await page.evaluate((useBox, maxH) => {
    const t = document.querySelector('[data-ev-target]').getBoundingClientRect();
    const b = useBox ? document.querySelector('[data-ev-box]') : null;
    const bb = b ? b.getBoundingClientRect() : null;
    const top = Math.min(t.top, bb && t.top - bb.bottom < 900 ? bb.top : t.top) + window.scrollY - 110;
    const left = Math.max(0, Math.min(t.left, bb ? bb.left : t.left) - 16);
    const right = Math.min(document.documentElement.scrollWidth, Math.max(t.right, bb ? bb.right : t.right) + 16);
    const h = Math.min(t.bottom + window.scrollY + 16 - top, maxH);
    return { x: left, y: Math.max(0, top), width: right - left, height: h };
  }, !!spec.region, spec.maxH || 2600);
  // banner with URL so the reviewer sees the source in the image
  const clip_w = clip.width;
  await page.evaluate((y, url, x, clip_w) => {
    const d = document.createElement('div');
    d.textContent = url + '  ·  chụp 2026-10-16';
    Object.assign(d.style, { position: 'absolute', left: x + 'px', top: (y) + 'px', zIndex: 99999, background: '#202124', color: '#fff',
      font: '13px/24px monospace', padding: '0 10px', width: (clip_w - 20) + 'px' });
    document.body.appendChild(d);
  }, clip.y, spec.url, clip.x, clip_w);
  const file = path.join(OUT, `${spec.id}.png`);
  await page.screenshot({ path: file, clip, captureBeyondViewport: true });
  await page.close();
  return `${spec.id}: ok ${Math.round(clip.width)}x${Math.round(clip.height)} region=${reg}`;
}

(async () => {
  const want = process.argv.slice(2);
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', userDataDir: process.env.UDD, args: ['--no-first-run', '--lang=en-US'] });
  for (const spec of SPECS.filter(s => !want.length || want.includes(s.id))) {
    try { console.log(await shoot(browser, spec)); } catch (e) { console.log(`${spec.id}: ERROR ${e.message.split('\n')[0]}`); }
  }
  await browser.close();
})();
