// Regression of the actual DEMO card renderer, not just string matching.
// Test runs entirely offline against index.html; does not change archive, LAB, or wagers.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';

const page = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const start = page.indexOf('  function badge(tip) {');
const end = page.indexOf('  async function loadTips() {', start);
assert.ok(start >= 0 && end > start, 'DEMOs renderer anchors have changed');

function element(tag, cls = '', content = '') {
  return {
    tag, cls, textContent: String(content), href: '', children: [],
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = children; },
  };
}
function visible(node) {
  return [node.textContent, ...node.children.map(visible)].join(' ');
}
function harness() {
  const state = {mode: 'demo', filter: 'all', tips: []};
  const elements = Object.fromEntries(
    ['tips-list', 'stat-count', 'stat-hit', 'stat-profit'].map(id => [id, element('section')])
  );
  const api = vm.runInNewContext(
    page.slice(start, end) + '\n({badge, renderCard, render});',
    {
      state, el: element, $: id => {
        assert.ok(elements[id], 'Unexpected DOM id ' + id);
        return elements[id];
      },
      str: (value, max = 180) => String(value ?? '').slice(0, max),
      formatDate: value => String(value),
    },
    {timeout: 5000}
  );
  return {state, elements, ...api};
}
function tip(tier = 'free', status = 'upcoming', id = 'demo') {
  return {tier, status, id, league:'DEMO', date:'2026-11-08', time:'18:00',
    home:'Drużyna A', away:'Drużyna B', market:'1X2', odds:1.5, reason:'Tylko przykład'};
}

test('DEMO always labels fictional examples, irrespective of fake result state', () => {
  const h = harness();
  for (const status of ['upcoming', 'won', 'lost', 'void']) {
    const item = tip('free', status);
    assert.equal(h.badge(item)[0], 'PRZYKŁAD DEMO');
    const text = visible(h.renderCard(item));
    assert.match(text, /PRZYKŁAD DEMO/);
    assert.match(text, /Fikcyjny przykład · nie jest prawdziwym meczem/);
    assert.doesNotMatch(text, /Przed meczem|Wygrany ✓|Przegrany ✕|Zwrot ↩/);
  }
});

test('DEMO premium cards do not imply paid analysis is available', () => {
  const h = harness();
  const text = visible(h.renderCard(tip('premium', 'won')));
  assert.match(text, /KARTA DEMO · PREMIUM NIEAKTYWNE/);
  assert.match(text, /Fikcyjny przykład analizy/);
  assert.match(text, /Fikcyjny przykład · nie jest prawdziwym meczem/);
  assert.doesNotMatch(text, /Analiza dostępna po uruchomieniu usługi|Wygrany ✓/);
});

test('DEMO result-like records cannot create fake performance or profit metrics', () => {
  const h = harness();
  h.state.tips = [tip('free', 'won', 'w'), tip('free', 'lost', 'l'), tip('premium', 'won', 'p')];
  h.render();
  assert.equal(h.elements['stat-count'].textContent, '3');
  assert.equal(h.elements['stat-hit'].textContent, '—');
  assert.equal(h.elements['stat-profit'].textContent, '—');
});

test('genuine live mode still renders outcome labels and existing calculations', () => {
  const h = harness();
  h.state.mode = 'live';
  const item = tip('free', 'won');
  assert.equal(h.badge(item)[0], 'Wygrany ✓');
  assert.match(visible(h.renderCard(item)), /Wygrany/);
  assert.doesNotMatch(visible(h.renderCard(item)), /PRZYKŁAD DEMO/);
  h.state.tips = [item, tip('free', 'lost', 'l')];
  h.render();
  assert.equal(h.elements['stat-hit'].textContent, '50,0%');
  assert.equal(h.elements['stat-profit'].textContent, '-0,50 j.');
});
