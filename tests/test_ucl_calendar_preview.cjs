/* Offline tests: no API calls or invented fixtures in public production data. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {inspect, sourceIdentityValid, monthOptions, byMonth} = require('../research/ucl_calendar_preview.js');
const NOW = '2026-11-15T12:00:00Z';

function fixture(id, iso, home = 'Arsenal FC', away = 'Inter Milano', homeId = 21, awayId = 22,
                 finished = false, score = false) {
  return {
    matchID: id, leagueShortcut: 'ucl', leagueSeason: 2026,
    matchDateTimeUTC: iso, matchIsFinished: finished,
    team1: {teamId: homeId, teamName: home}, team2: {teamId: awayId, teamName: away},
    group: {groupName: 'Liga'},
    matchResults: score ? [{resultTypeID:2, pointsTeam1:2, pointsTeam2:1}] : []
  };
}
const upcoming = () => fixture(930001, '2026-11-25T20:00:00Z');
const past = () => fixture(930002, '2026-11-04T20:00:00Z', 'Celtic', 'Real Madrid',
  23, 24, true, true);

test('future fixtures are only research and never production-approved', () => {
  const report = inspect([past(), upcoming()], NOW);
  assert.equal(report.ok, true);
  assert.equal(report.total, 2);
  assert.equal(report.finishedWithScore, 1);
  assert.equal(report.upcoming.length, 1);
  assert.equal(report.independentVerification, false);
  assert.equal(report.productionApproved, false);
  assert.equal(report.modelApproved, false);
});

test('empty, not-array and oversized payloads fail closed', () => {
  for (const data of [null, {}, [], Array.from({length:261}, (_,i)=>fixture(i+1,'2026-11-25T20:00:00Z'))])
    assert.equal(inspect(data, NOW).ok, false);
});

test('browser preview blocks a wrong, missing or null competition / season', () => {
  assert.equal(sourceIdentityValid([upcoming()]), true);
  for (const change of [
    row => { row.leagueShortcut = 'la1'; },
    row => { row.leagueSeason = 2025; },
    row => { row.leagueShortcut = null; },
    row => { row.leagueSeason = null; },
    row => { delete row.leagueShortcut; },
    row => { delete row.leagueSeason; }
  ]) {
    const row = upcoming();
    change(row);
    const report = inspect([row], NOW);
    assert.equal(sourceIdentityValid([row]), false);
    assert.equal(report.ok, false);
    assert.deepEqual(report.upcoming, []);
    assert.match(report.reason, /sezonu 2026/);
  }
});

test('no real upcoming fixture means no test calendar', () => {
  assert.equal(inspect([past()], NOW).ok, false);
});

test('duplicate fixture IDs block the entire preview', () => {
  const bad = fixture(930001, '2026-12-11T20:00:00Z', 'Liverpool', 'Inter', 31, 32);
  assert.equal(inspect([upcoming(), bad], NOW).ok, false);
});

test('duplicate team/date pair under different IDs blocks the entire preview', () => {
  const second = fixture(930003, '2026-11-25T20:00:00Z');
  assert.equal(inspect([upcoming(), second], NOW).ok, false);
});

test('future score and completed flag block preview', () => {
  assert.equal(inspect([fixture(930001,'2026-11-25T20:00:00Z', 'A', 'B', 1,2,true,true)], NOW).ok,false);
  assert.equal(inspect([fixture(930001,'2026-11-25T20:00:00Z', 'A', 'B', 1,2,false,true)], NOW).ok,false);
});

test('unresolved old score blocks preview', () => {
  const overdue = fixture(930003, '2026-11-01T20:00:00Z', 'Liverpool', 'Bayern', 40,41);
  assert.equal(inspect([upcoming(), overdue], NOW).ok, false);
});

test('bad dates, missing UTC timezone and wrong season block preview', () => {
  for (const when of ['2026-11-25T20:00:00', '2026-02-30T20:00:00Z',
                      '2026-06-30T20:00:00Z', '2027-07-02T20:00:00Z',
                      '2026-11-25T99:00:00Z']) {
    assert.equal(inspect([fixture(1,when)],NOW).ok,false,when);
  }
});

test('missing identity or conflicting team IDs block preview', () => {
  assert.equal(inspect([fixture(1,'2026-11-25T20:00:00Z','A','B',10,10)],NOW).ok,false);
  const changingName = fixture(930004,'2026-12-02T20:00:00Z','Not Arsenal','Inter Milano',21,22);
  assert.equal(inspect([upcoming(),changingName],NOW).ok,false);
  const changingId = fixture(930004,'2026-12-02T20:00:00Z','Arsenal FC','Inter Milano',51,22);
  assert.equal(inspect([upcoming(),changingId],NOW).ok,false);
});

test('unexpected control characters in team names block preview', () => {
  assert.equal(inspect([fixture(1,'2026-11-25T20:00:00Z','Arsenal\nFC','Inter')], NOW).ok,false);
});

test('valid explicit +00:00 timezone is normalized to Z', () => {
  const report = inspect([fixture(1,'2026-11-25T20:00:00+00:00')],NOW);
  assert.equal(report.ok,true);
  assert.equal(report.upcoming[0].kickoff,'2026-11-25T20:00:00.000Z');
});

test('month filtering sorts and does not modify source data', () => {
  const r = inspect([fixture(2,'2026-12-25T20:00:00Z','Liverpool','Inter',8,9),
                     fixture(1,'2026-11-25T20:00:00Z')],NOW);
  assert.equal(r.ok,true);
  assert.deepEqual(monthOptions(r.upcoming),['2026-11','2026-12']);
  assert.deepEqual(byMonth(r.upcoming,'2026-12').map(x=>x.id),[2]);
  assert.equal(r.upcoming.length,2);
});

test('isolation: no predicted results, betting odds, auto-launch or innerHTML', () => {
  const html = fs.readFileSync(path.join(__dirname,'../research/ucl_calendar_preview.html'),'utf8');
  assert.match(html, /TYLKO BADANIA/);
  assert.match(html, /NIEOPUBLIKOWANE/);
  assert.doesNotMatch(html, /innerHTML\s*=/);
  assert.doesNotMatch(html, /predictions\.json|tips\.json|localStorage|setInterval/);
  assert.match(html, /addEventListener\('click'/);
  assert.match(html, /textContent\s*=/);
  assert.match(html, /api\.openligadb\.de\/getmatchdata\/ucl\/2026/);
});
