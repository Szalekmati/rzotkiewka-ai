#!/usr/bin/env node
'use strict';
// Isolated local research cache prototype for the UEFA Champions League 2026/27.
// No network access, no workflow scheduling, no changes to index.html or Pages.
const fs = require('node:fs/promises');
const crypto = require('node:crypto');
const {compareRows, LIMIT_BYTES} = require('./ucl_verify_snapshot.cjs');
const {inspect} = require('./ucl_calendar_preview.js');

const MAX_AGE_MS = 6 * 60 * 60 * 1000;
const SCHEMA_VERSION = 1;
const SOURCE = 'https://api.openligadb.de/getmatchdata/ucl/2026';

function digestFixtures(fixtures) {
  // Detect accidental changes; not a signature or proof of provenance.
  return crypto.createHash('sha256').update(JSON.stringify(fixtures)).digest('hex');
}
function buildResearchSnapshot(rows, observedAt) {
  const instant = Date.parse(observedAt);
  if (!Number.isFinite(instant)) return {ok:false, reason:'Invalid observation timestamp'};
  const iso = new Date(instant).toISOString();
  const report = compareRows(rows, iso);
  if (report.status !== 'MATCHED_RESEARCH_ONLY') {
    return {ok:false, reason:'STOP: reference or structural gate failed', report};
  }
  const structural = inspect(rows, iso);
  if (!structural.ok) return {ok:false, reason:'STOP: structural gate failed', report};
  // Only the fields needed for a future research calendar. Never copy logos,
  // scores, external image URLs or the raw OpenLigaDB payload.
  const fixtures = structural.upcoming.map(match => ({
    match_id:match.id,
    kickoff_utc:match.kickoff,
    home:match.home,
    away:match.away,
    phase:match.phase
  }));
  const snapshot = {
    schema_version:SCHEMA_VERSION,
    kind:'RZOTKIEWKA_RESEARCH_UCL_CACHE',
    status:'RESEARCH_ONLY',
    source:SOURCE,
    source_license:'ODbL-1.0',
    reference_as_of:'2026-11-04',
    observed_at_utc:iso,
    league_shortcut:'ucl',
    league_season:2026,
    provider_league_id:rows[0].leagueId,
    total_source_records:rows.length,
    fixture_count:fixtures.length,
    expires_at_utc:new Date(instant+MAX_AGE_MS).toISOString(),
    fixture_sha256:digestFixtures(fixtures),
    production_release_allowed:false,
    predictions_allowed:false,
    premium_allowed:false,
    fixtures
  };
  return {ok:true,snapshot};
}
function inspectResearchSnapshot(doc, observedAt) {
  const now=Date.parse(observedAt);
  if(!Number.isFinite(now)) return {usable:false,status:'INVALID_CLOCK'};
  if (!doc || doc.kind!=='RZOTKIEWKA_RESEARCH_UCL_CACHE' ||
    doc.schema_version!==SCHEMA_VERSION || doc.status!=='RESEARCH_ONLY' ||
    doc.production_release_allowed!==false ||
    doc.predictions_allowed!==false || doc.premium_allowed!==false ||
    doc.league_shortcut!=='ucl' || doc.league_season!==2026 ||
    !Number.isSafeInteger(doc.provider_league_id) || doc.provider_league_id<=0 ||
    !Array.isArray(doc.fixtures) || doc.fixture_count!==doc.fixtures.length ||
    !/^[a-f0-9]{64}$/.test(String(doc.fixture_sha256)) ||
    doc.fixture_sha256!==digestFixtures(doc.fixtures))
    return {usable:false,status:'INVALID_SNAPSHOT'};
  const stamped=Date.parse(doc.observed_at_utc),expires=Date.parse(doc.expires_at_utc);
  if(!Number.isFinite(stamped) || !Number.isFinite(expires) ||
    expires-stamped!==MAX_AGE_MS || now<stamped || now>=expires)
    return {usable:false,status:'STALE_OR_FUTURE'};
  return {usable:true,status:'RESEARCH_ONLY',ageMinutes:Math.floor((now-stamped)/60000),
    fixtureCount:doc.fixture_count,productionReleaseAllowed:false};
}
async function main(args=process.argv.slice(2)) {
  if(args.length===1 && args[0]==='--help'){
    process.stdout.write('Usage: node research/ucl_central_snapshot.cjs --input existing.json --output local-report.json\n');
    return 0;
  }
  if(args.length!==4 || args[0]!=='--input' || args[2]!=='--output' ||
    !args[1] || !args[3] || args[1]===args[3]) {
    process.stderr.write('STOP: require explicit distinct --input and --output\n');
    return 2;
  }
  try {
    const inputInfo=await fs.stat(args[1]);
    if(!inputInfo.isFile() || inputInfo.size>LIMIT_BYTES || inputInfo.size===0)
      throw new Error('Invalid input file');
    const raw=JSON.parse(await fs.readFile(args[1],'utf8'));
    const result=buildResearchSnapshot(raw,new Date().toISOString());
    if(!result.ok) {
      process.stderr.write('STOP: source did not pass research gates; no snapshot written\n');
      return 1;
    }
    // Exclusive create: cannot overwrite an existing output, including
    // public production snapshot, even if invoked by mistake.
    await fs.writeFile(args[3],JSON.stringify(result.snapshot,null,2)+'\n',{
      flag:'wx',encoding:'utf8',mode:0o600
    });
    process.stdout.write('RESEARCH_ONLY: local snapshot created; never approved for publication\n');
    return 0;
  }catch(error){
    process.stderr.write('STOP: '+String(error && error.name || 'Error')+'; no release\n');
    return 2;
  }
}
if(require.main===module){
  main().then(code=>{process.exitCode=code;}).catch(()=>{process.exitCode=2;});
}
module.exports={buildResearchSnapshot,inspectResearchSnapshot,main,MAX_AGE_MS,SCHEMA_VERSION};