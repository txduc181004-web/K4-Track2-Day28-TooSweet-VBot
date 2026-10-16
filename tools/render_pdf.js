// Render slides HTML to a 16:9 PDF and per-slide PNG previews with local Chrome.
// usage: node tools/render_pdf.js slides/slides.html deliverables/G00_slide.pdf [preview_dir]
const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');
(async () => {
  const [src, out, prev] = process.argv.slice(2);
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', userDataDir: process.env.UDD });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720 });
  await page.goto('file://' + path.resolve(src), { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: out, width: '1280px', height: '720px', printBackground: true, preferCSSPageSize: true });
  if (prev) {
    fs.mkdirSync(prev, { recursive: true });
    const n = await page.evaluate(() => document.querySelectorAll('.slide').length);
    for (let i = 0; i < n; i++) {
      const el = (await page.$$('.slide'))[i];
      await el.screenshot({ path: path.join(prev, `s${String(i).padStart(2, '0')}.png`) });
    }
    // overflow check: elements extending beyond their slide
    const issues = await page.evaluate(() => {
      const res = [];
      document.querySelectorAll('.slide').forEach((s, i) => {
        const sr = s.getBoundingClientRect();
        s.querySelectorAll('*').forEach(e => {
          const r = e.getBoundingClientRect();
          if (r.width && (r.bottom > sr.bottom - 30 || r.right > sr.right + 1) && !e.closest('.foot') && !e.classList.contains('foot'))
            res.push(`slide ${i}: <${e.tagName.toLowerCase()} class=${e.className}> bottom=${Math.round(r.bottom - sr.top)} right=${Math.round(r.right - sr.left)} "${(e.innerText || '').slice(0, 40).replace(/\n/g, ' ')}"`);
        });
      });
      return res;
    });
    console.log(issues.length ? issues.slice(0, 40).join('\n') : 'no overflow');
  }
  await browser.close();
  console.log('pdf', out, fs.statSync(out).size, 'bytes');
})();
