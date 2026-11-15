'use strict';
// Fully offline tests: only synthetic research records; no live API calls.
const test = require('node:test');
const assert = require('node:assert/strict');
const {allOfficial} = require('../research/ucl_official_matchday5.js');
const {compareRows, fetchLive, main, URL} = require('../research/ucl_verify_snapshot.cjs');
const NOW = '2026-11-15T18:00:00Z';
function sample() {
  const known = new Map();
  const teamId = name => {
    if (!known.has(name)) known.set(name, 1000 + known.size);
    return known.get(name);
  };
  return allOfficial.map((row, i) => ({
    matchID: 700000 + i,
    leagueShortcut: 'ucl', leagueSeason: 2026, leagueId: 2800,
    matchDateTimeUTC: row.kickoffUtc,
    team1: {teamId: teamId(row.home), teamName: row.home},
    team2: {teamId: teamId(row.away), teamName: row.away},
    matchIsFinished: false, matchResults: []
  }));
}

test('valid synthetic fixture comparison is research-only, never release', () => {
  const report = compareRows(sample(), NOW);
  assert.equal(report.status, 'MATCHED_RESEARCH_ONLY');
  assert.equal(report.records, 72);
  assert.equal(report.officialCompared, 72);
  assert.equal(report.officialExpected, 72);
  assert.equal(report.structureAccepted, true);
  assert.equal(report.sourceIdentityValid, true);
  assert.equal(report.scheduledFuture, 72);
  assert.equal(report.publicationAllowed, false);
  assert.equal(report.predictionsAllowed, false);
  assert.equal(report.premiumAllowed, false);
});
test('missing, extra and incorrectly dated fixtures block', () => {
  const rows = sample();
  assert.equal(compareRows(rows.slice(1), NOW).status, 'STOP');
  const unknown = {...rows[0], matchID: 899999, matchDateTimeUTC: '2026-11-20T20:00:00Z',
    team1: {teamId: 9999, teamName:'Unknown FC'}, team2:{teamId:9998,teamName:'Other FC'}};
  assert.equal(compareRows([...rows, unknown], NOW).status, 'STOP');
  const wrong = sample();
  wrong[1].matchDateTimeUTC = '2026-11-24T20:01:00Z';
  assert.equal(compareRows(wrong, NOW).status, 'STOP');
});
test('duplicated ID and contradiction in club identity block', () => {
  const rows = sample();
  rows[1].matchID = rows[0].matchID;
  assert.equal(compareRows(rows, NOW).status, 'STOP');
  const second = sample();
  second[1].team1.teamId = second[0].team1.teamId;
  assert.equal(compareRows(second, NOW).status, 'STOP');
});
test('wrong or missing league or season metadata blocks an otherwise matching source', () => {
  for (const change of [
    row => { row.leagueShortcut = 'la1'; },
    row => { row.leagueSeason = 2025; },
    row => { delete row.leagueShortcut; },
    row => { delete row.leagueSeason; }
  ]) {
    const rows = sample();
    change(rows[0]);
    const report = compareRows(rows, NOW);
    assert.equal(report.status, 'STOP');
    assert.equal(report.sourceIdentityValid, false);
    assert.match(report.findings.join(' '), /leagueShortcut=ucl/);
    assert.equal(report.publicationAllowed, false);
  }
});

test('snapshot rejects missing or inconsistent OpenLigaDB league IDs', () => {
  for (const badId of [undefined, null, '2800', 0, -7, true, 2801]) {
    const rows = sample();
    rows[1].leagueId = badId;
    const report = compareRows(rows, NOW);
    assert.equal(report.status, 'STOP');
    assert.equal(report.sourceIdentityValid, false);
    assert.equal(report.publicationAllowed, false);
    assert.match(report.findings.join(' '), /leagueId/);
  }
});

test('no input and malformed input never approve publication', () => {
  for (const rows of [null, {}, [], 'bad']) {
    const report = compareRows(rows, NOW);
    assert.equal(report.status, 'STOP');
    assert.equal(report.publicationAllowed, false);
  }
});
test('explicit live fetch is a fixed, read-only URL and bounds response size', async () => {
  let urlSeen, optionsSeen;
  const mock = async (url, options) => {
    urlSeen = url; optionsSeen = options;
    return {ok: true, headers: {get: () => null}, text: async () => JSON.stringify(sample())};
  };
  const rows = await fetchLive(mock);
  assert.equal(urlSeen, URL);
  assert.equal(optionsSeen.method, 'GET');
  assert.equal(optionsSeen.redirect, 'error');
  assert.equal(rows.length, 72);
  await assert.rejects(fetchLive(async () => ({
    ok: true, headers: {get: () => String(3_000_001)}
  })), /size/);
});
test('CLI without explicit mode is blocked; --help is non-networked', async () => {
  assert.equal(await main([]), 2);
  assert.equal(await main(['--help']), 0);
});
