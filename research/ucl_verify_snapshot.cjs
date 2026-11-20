#!/usr/bin/env node
'use strict';
// Explicit read-only comparison of real UCL fixture JSON to a dated UEFA reference.
// No network access on import; "--live" must be explicitly requested.
// Never permits publication, predictions, or changes to production files.
const fs = require('node:fs/promises');
const {inspect, sourceIdentityValid} = require('./ucl_calendar_preview.js');
const {verifyAllUpcoming, allOfficial, matchName} = require('./ucl_official_matchday5.js');

const URL = 'https://api.openligadb.de/getmatchdata/ucl/2026';
const LIMIT_BYTES = 3_000_000;
const OFFICIAL_REFERENCE_AS_OF = '2026-11-04';
// Internal research safeguard: aged references require a new manual UEFA check.
const REFERENCE_REVIEW_MAX_DAYS = 7;
const PHASE5_START = Date.parse('2026-11-05T00:00:00Z');
const MAX_DIAGNOSTIC_EXAMPLES = 30;

// Research-only, exact pair/kickoff comparison; no fuzzy identity guesses.
// A mismatch does not prove the source is wrong: names, timezone or real
// rescheduling may be involved. Print only bounded, public fixture metadata.
function compareReferenceTriples(rows) {
  const available = Array.isArray(rows) && rows.length <= 260 ? rows.filter(row =>
    row && typeof row === 'object' &&
    typeof row.matchDateTimeUTC === 'string' &&
    Number.isFinite(Date.parse(row.matchDateTimeUTC)) &&
    Date.parse(row.matchDateTimeUTC) >= PHASE5_START) : [];
  const equal = (row, expected) => row.team1 && row.team2 &&
    typeof row.team1.teamName === 'string' &&
    typeof row.team2.teamName === 'string' &&
    matchName(row.team1.teamName, expected.home) &&
    matchName(row.team2.teamName, expected.away) &&
    Date.parse(row.matchDateTimeUTC) === Date.parse(expected.kickoffUtc);
  const missing = allOfficial.filter(expected => !available.some(row => equal(row, expected)));
  const extra = available.filter(row => !allOfficial.some(expected => equal(row, expected)));
  const clean = value => typeof value === 'string'
    ? value.replace(/[\u0000-\u001f\u007f]/g, '').slice(0, 100) : '';
  return {
    missingOfficialCount: missing.length,
    unmatchedSourceCount: extra.length,
    missingOfficialExamples: missing.slice(0, MAX_DIAGNOSTIC_EXAMPLES)
      .map(row => ({kickoffUtc: row.kickoffUtc, home: row.home, away: row.away})),
    unmatchedSourceExamples: extra.slice(0, MAX_DIAGNOSTIC_EXAMPLES)
      .map(row => ({kickoffUtc: clean(row.matchDateTimeUTC),
        home: clean(row.team1 && row.team1.teamName),
        away: clean(row.team2 && row.team2.teamName)}))
  };
}

function compareRows(rows, observedAt) {
  const official = verifyAllUpcoming(rows);
  const structure = inspect(rows, observedAt);
  // Reject mixed competition, season or provider league IDs even if pairs
  // match the dated UEFA reference. A shared provider ID is not proof of identity.
  const hasCorrectSourceIdentity = sourceIdentityValid(rows);
  const detailedComparison = compareReferenceTriples(rows);
  const observedInstant = Date.parse(observedAt);
  const referenceInstant = Date.parse(OFFICIAL_REFERENCE_AS_OF + 'T00:00:00Z');
  const referenceAgeDays = Number.isFinite(observedInstant)
    ? Math.floor((observedInstant - referenceInstant) / 86400000) : null;
  const referenceReviewRequired = referenceAgeDays === null ||
    referenceAgeDays < 0 || referenceAgeDays >= REFERENCE_REVIEW_MAX_DAYS;
  const matched = official.ok === true && structure.ok === true &&
    hasCorrectSourceIdentity && !referenceReviewRequired;
  const issues = [
    ...(referenceReviewRequired ? [
      'Datowana referencja UEFA ' + OFFICIAL_REFERENCE_AS_OF +
      ' wymaga ponownej weryfikacji; kontrola badawcza wstrzymana.'
    ] : []),
    ...(hasCorrectSourceIdentity ? [] : ['Brak lub niezgodność leagueShortcut=ucl / leagueSeason=2026 / leagueId']),
    ...(official.issues || []),
    ...(structure.issues || []),
    ...(structure.ok ? [] : [structure.reason])
  ].filter(Boolean);
  return {
    kind: 'RZOTKIEWKA_UCL_2026_MANUAL_RESEARCH_GATE',
    status: matched ? 'MATCHED_RESEARCH_ONLY' : 'STOP',
    observedAt,
    source: URL,
    referenceAsOf: OFFICIAL_REFERENCE_AS_OF,
    referenceAgeDays,
    referenceReviewMaxDays: REFERENCE_REVIEW_MAX_DAYS,
    referenceReviewRequired,
    records: Array.isArray(rows) ? rows.length : null,
    officialCompared: official.checked || 0,
    officialExpected: official.expected || 72,
    structureAccepted: structure.ok === true,
    sourceIdentityValid: hasCorrectSourceIdentity,
    scheduledFuture: structure.ok ? structure.upcoming.length : null,
    ...detailedComparison,
    findings: issues.slice(0, 10),
    totalFindings: Math.max(issues.length, official.issueCount || 0, structure.issueCount || 0),
    independentlyVerifiedClubIds: false,
    publicationAllowed: false,
    predictionsAllowed: false,
    premiumAllowed: false
  };
}

async function fetchLive(fetchFn = globalThis.fetch, timeoutMs = 14000) {
  if (typeof fetchFn !== 'function') throw new Error('No fetch implementation');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetchFn(URL, {
      method: 'GET', headers: {accept: 'application/json'},
      cache: 'no-store', redirect: 'error', signal: controller.signal
    });
    if (!res || !res.ok) throw new Error('Source returned HTTP ' + (res && res.status));
    const declared = Number(res.headers && res.headers.get('content-length') || 0);
    if (!Number.isFinite(declared) || declared > LIMIT_BYTES)
      throw new Error('Source response size is not acceptable');
    let raw;
    if (res.body && typeof res.body.getReader === 'function') {
      const reader = res.body.getReader();
      const chunks = [];
      let size = 0;
      while (true) {
        const part = await reader.read();
        if (part.done) break;
        size += part.value.byteLength;
        if (size > LIMIT_BYTES) {
          await reader.cancel();
          throw new Error('Source exceeds 3 MB limit');
        }
        chunks.push(Buffer.from(part.value));
      }
      raw = Buffer.concat(chunks).toString('utf8');
    } else {
      raw = await res.text();
      if (Buffer.byteLength(raw, 'utf8') > LIMIT_BYTES)
        throw new Error('Source exceeds 3 MB limit');
    }
    return JSON.parse(raw);
  } finally {
    clearTimeout(timer);
  }
}

async function main(args = process.argv.slice(2)) {
  if (args.length === 1 && args[0] === '--help') {
    process.stdout.write('Usage: node research/ucl_verify_snapshot.cjs --file path.json | --live\n');
    return 0;
  }
  const fileMode = args.length === 2 && args[0] === '--file' && args[1];
  const liveMode = args.length === 1 && args[0] === '--live';
  if (!fileMode && !liveMode) {
    process.stderr.write('STOP: supply --file path.json or explicit --live\n');
    return 2;
  }
  try {
    let rows;
    if (liveMode) rows = await fetchLive();
    else {
      const stat = await fs.stat(args[1]);
      if (!stat.isFile() || stat.size > LIMIT_BYTES)
        throw new Error('Input file is not an acceptable JSON snapshot');
      rows = JSON.parse(await fs.readFile(args[1], 'utf8'));
    }
    const report = compareRows(rows, new Date().toISOString());
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
    return report.status === 'MATCHED_RESEARCH_ONLY' ? 0 : 1;
  } catch (error) {
    process.stderr.write('STOP: cannot verify source (' + error.name + ')\n');
    return 2;
  }
}

if (require.main === module) {
  main().then(code => { process.exitCode = code; }).catch(() => { process.exitCode = 2; });
}
module.exports = {compareRows, compareReferenceTriples, fetchLive, main, URL, LIMIT_BYTES};
