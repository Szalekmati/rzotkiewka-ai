// Real Chromium smoke test for mobile navigation (offline; no model changes).
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const fs = require('node:fs');
(async () => {
  const demoData = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'tips.json'), 'utf8'));
  assert.equal(demoData.mode, 'demo', 'Mobile smoke requires checked-in DEMO fixtures');
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    for (const width of [320, 360, 390, 720]) {
      const page = await browser.newPage({ viewport: { width, height: 740 }, deviceScaleFactor: 1 });
      await page.addInitScript(payload => {
        const original = window.fetch.bind(window);
        window.fetch = (input, init) => {
          const url = typeof input === 'string' ? input : input?.url;
          if (url === './tips.json') {
            return Promise.resolve(new Response(JSON.stringify(payload), {
              status: 200, headers: { 'content-type': 'application/json' }
            }));
          }
          return original(input, init);
        };
      }, demoData);
      await page.goto(pathToFileURL(path.join(__dirname, '..', 'index.html')).href, { waitUntil: 'domcontentloaded' });
      const nav = page.locator('nav.mobile-nav');
      assert.equal(await nav.isVisible(), true, 'Mobile navigation missing at ' + width);
      assert.equal(await nav.locator('a').count(), 5, 'Expected five links');
      const geometry = await nav.evaluate(el => {
        const rect = el.getBoundingClientRect();
        return {
          left: rect.left, right: rect.right, width: window.innerWidth,
          links: Array.from(el.querySelectorAll('a')).map(a => {
            const r = a.getBoundingClientRect();
            return { left: r.left, right: r.right, width: r.width };
          })
        };
      });
      assert.ok(geometry.left >= -1 && geometry.right <= geometry.width + 1, 'Nav overflows viewport: ' + width);
      for (const link of geometry.links) {
        assert.ok(link.left >= -1 && link.right <= width + 1 && link.width >= 40, 'Link overflows or too narrow: ' + width);
      }
      for (const hash of ['#mecze', '#ranking', '#sporty', '#raport', '#wiecej']) {
        const link = nav.locator('a[href="' + hash + '"]');
        await link.click();
        await page.waitForFunction(expected => location.hash === expected &&
          document.querySelector('nav.mobile-nav a[href="' + expected + '"]')?.getAttribute('aria-current') === 'page', hash, { timeout: 5000 });
        assert.equal(await link.getAttribute('aria-current'), 'page', 'Inactive tab ' + hash + ' at ' + width);
      }
      // The 18-item catalogue must distinguish actual data from the roadmap.
      await nav.locator('a[href="#sporty"]').click();
      // Hashchange routing is asynchronous: wait until the SPA reveals the
      // parent tab before inspecting visibility, not just the DOM node.
      await page.waitForFunction(() => location.hash === '#sporty' &&
        !document.getElementById('sporty').hidden, { timeout: 5000 });
      const radar = page.locator('#league-radar');
      await radar.waitFor({ state: 'visible', timeout: 5000 });
      assert.equal(await radar.isVisible(), true, 'League quality radar must be visible: ' + width);
      assert.equal(await radar.locator('.league-radar-card').count(), 4, 'Four source-quality cards: ' + width);
      assert.match(await radar.innerText(), /DANE NIEWYSTARCZAJĄCE/);
      assert.match(await radar.innerText(), /DO RĘCZNEJ OCENY/);
      assert.match(await radar.innerText(), /nie bieżący podgląd API/);
      const cards = page.locator('#sport-list .competition-card');
      const connected = page.locator('#sport-connected-only');
      assert.equal(await cards.count(), 18, 'Entire league catalogue must be visible initially: ' + width);
      assert.equal(await connected.getAttribute('aria-pressed'), 'false');
      await connected.click();
      assert.equal(await connected.getAttribute('aria-pressed'), 'true');
      assert.equal(await cards.count(), 3, 'Only three football leagues have connected data: ' + width);
      assert.equal(await page.locator('#sport-list .competition-status.active').count(), 3);
      await page.locator('#sport-filters button').filter({ hasText: 'Koszykówka' }).click();
      assert.equal(await cards.count(), 0, 'Unavailable sport must not pretend to be connected: ' + width);
      assert.match(await page.locator('#sport-list .empty').innerText(), /Brak podłączonych lig/);
      await connected.click();
      assert.equal(await connected.getAttribute('aria-pressed'), 'false');
      assert.equal(await cards.count(), 3, 'Planned basketball leagues return after reset: ' + width);
      assert.equal(await page.locator('#sport-list .competition-status.active').count(), 0);
      await page.locator('#sport-filters button').first().click();
      assert.equal(await cards.count(), 18, 'Reset must restore full catalogue: ' + width);
      // Verify actual mobile DOM labels using only checked-in DEMO fixtures;
      // the file:// test stays offline and never publishes fictional outcomes.
      await nav.locator('a[href="#wiecej"]').click();
      await page.waitForFunction(() => location.hash === '#wiecej' &&
        !document.getElementById('wiecej').hidden, { timeout: 5000 });
      await page.locator('#wiecej a[href="#typy"]').click();
      await page.waitForFunction(() => location.hash === '#typy' &&
        !document.getElementById('typy').hidden, { timeout: 5000 });
      await page.waitForFunction(() => document.getElementById('data-message')
        ?.textContent.includes('TRYB DEMO'), { timeout: 5000 });
      assert.equal(await page.locator('#tips-list article.tip').count(),
        demoData.tips.length, 'Missing actual DEMO cards: ' + width);
      const visibleCards = await page.locator('#tips-list').innerText();
      assert.match(visibleCards, /PRZYKŁAD DEMO/);
      assert.match(visibleCards, /Fikcyjny przykład · nie jest prawdziwym meczem/);
      assert.match(visibleCards, /KARTA DEMO · PREMIUM NIEAKTYWNE/);
      assert.match(visibleCards, /Fikcyjny przykład analizy/);
      assert.doesNotMatch(visibleCards, /Przed meczem|Wygrany ✓|Przegrany ✕|Zwrot ↩/);
      assert.equal(await page.locator('#stat-hit').innerText(), '—');
      assert.equal(await page.locator('#stat-profit').innerText(), '—');
      await page.screenshot({ path: 'mobile-nav-' + width + '.png' });
      await page.close();
    }
    console.log('PASS: Chromium mobile navigation (320, 360, 390, 720 px)');
  } finally {
    await browser.close();
  }
})().catch(err => { console.error(err); process.exitCode = 1; });
