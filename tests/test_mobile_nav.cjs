// Real Chromium smoke test for mobile navigation (offline; no model changes).
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    for (const width of [320, 360, 390, 720]) {
      const page = await browser.newPage({ viewport: { width, height: 740 }, deviceScaleFactor: 1 });
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
      // The 17-item catalogue must distinguish actual data from the roadmap.
      await nav.locator('a[href="#sporty"]').click();
      const cards = page.locator('#sport-list .competition-card');
      const connected = page.locator('#sport-connected-only');
      assert.equal(await cards.count(), 17, 'Entire league catalogue must be visible initially: ' + width);
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
      assert.equal(await cards.count(), 17, 'Reset must restore full catalogue: ' + width);
      await page.screenshot({ path: 'mobile-nav-' + width + '.png' });
      await page.close();
    }
    console.log('PASS: Chromium mobile navigation (320, 360, 390, 720 px)');
  } finally {
    await browser.close();
  }
})().catch(err => { console.error(err); process.exitCode = 1; });
