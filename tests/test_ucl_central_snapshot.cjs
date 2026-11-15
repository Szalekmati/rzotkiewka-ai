'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const {allOfficial}=require('../research/ucl_official_matchday5.js');
const {buildResearchSnapshot,inspectResearchSnapshot,main,MAX_AGE_MS}=
  require('../research/ucl_central_snapshot.cjs');
const NOW='2026-11-08T18:00:00Z';
function fixtureRows(){
  const clubs=new Map();
  function team(name){
    if(!clubs.has(name))clubs.set(name,1000+clubs.size);
    return {teamId:clubs.get(name),teamName:name};
  }
  return allOfficial.map((match,i)=>({
    matchID:900000+i,
    matchDateTimeUTC:match.kickoffUtc,
    leagueShortcut:'ucl',
    leagueSeason:2026,
    leagueId:2800,
    matchIsFinished:false,
    matchResults:[],
    team1:team(match.home),team2:team(match.away),
    group:{groupName:'Faza ligowa'}
  }));
}
test('synthetic 72-match snapshot is research only and strips extra fields',()=>{
  const rows=fixtureRows();
  rows[0].team1.teamIconUrl='https://example.org/logo.png';
  rows[0].extraPrivate='never export';
  const result=buildResearchSnapshot(rows,NOW);
  assert.equal(result.ok,true,JSON.stringify(result.report||{}));
  const snapshot=result.snapshot;
  assert.equal(snapshot.fixture_count,72);
  assert.equal(snapshot.provider_league_id,2800);
  assert.equal(snapshot.production_release_allowed,false);
  assert.equal(snapshot.predictions_allowed,false);
  assert.equal(snapshot.premium_allowed,false);
  assert.equal(snapshot.status,'RESEARCH_ONLY');
  assert.equal(snapshot.fixtures[0].home,'Bodø/Glimt');
  assert.equal(snapshot.fixtures[0].kickoff_utc,'2026-11-24T17:45:00.000Z');
  assert.doesNotMatch(JSON.stringify(snapshot),/teamIconUrl|extraPrivate|logo\.png|matchResults/);
  assert.equal(inspectResearchSnapshot(snapshot,NOW).usable,true);
});
test('stale UEFA reference cannot produce even a research-only cache',()=>{
  const report=buildResearchSnapshot(fixtureRows(),'2026-11-15T18:00:00Z');
  assert.equal(report.ok,false);
  assert.equal(report.report.status,'STOP');
  assert.equal(report.report.referenceAgeDays,11);
  assert.equal(report.report.referenceReviewRequired,true);
});

test('missing, extra and incorrect UEFA records cannot create snapshot',()=>{
  const rows=fixtureRows();
  assert.equal(buildResearchSnapshot(rows.slice(1),NOW).ok,false);
  rows[0].leagueShortcut='la1';
  assert.equal(buildResearchSnapshot(rows,NOW).ok,false);
  const changed=fixtureRows();
  changed[10].matchDateTimeUTC='2026-11-25T18:01:00Z';
  assert.equal(buildResearchSnapshot(changed,NOW).ok,false);
});
test('stale snapshots and changed fixtures fail closed',()=>{
  const doc=buildResearchSnapshot(fixtureRows(),NOW).snapshot;
  assert.equal(inspectResearchSnapshot(doc,'2026-11-08T23:59:59Z').usable,true);
  assert.equal(inspectResearchSnapshot(doc,'2026-11-09T00:00:00Z').status,'STALE_OR_FUTURE');
  assert.equal(inspectResearchSnapshot(doc,'2026-11-08T17:59:59Z').usable,false);
  doc.fixtures[0].home='Changed team';
  assert.equal(inspectResearchSnapshot(doc,'2026-11-08T20:00:00Z').status,'INVALID_SNAPSHOT');
  assert.equal(MAX_AGE_MS,21600000);
});
test('CLI writes validated research-only output and refuses overwrite or bad data',async()=>{
  const folder=await fs.mkdtemp(path.join(os.tmpdir(),'rzotkiewka-ucl-cache-'));
  try{
    const input=path.join(folder,'source.json'),output=path.join(folder,'research.json');
    await fs.writeFile(input,JSON.stringify(fixtureRows()));
    assert.equal(await main(['--input',input,'--output',output],NOW),0);
    const original=await fs.readFile(output,'utf8');
    assert.equal(JSON.parse(original).fixture_count,72);
    assert.equal(JSON.parse(original).production_release_allowed,false);
    assert.equal(await main(['--input',input,'--output',output],NOW),2);
    assert.equal(await fs.readFile(output,'utf8'),original);
    const invalid=path.join(folder,'invalid.json'),rejected=path.join(folder,'rejected.json');
    await fs.writeFile(invalid,'[]');
    assert.equal(await main(['--input',invalid,'--output',rejected],NOW),1);
    await assert.rejects(fs.stat(rejected),{code:'ENOENT'});
    assert.equal(await main([]),2);
    assert.equal(await main(['--help']),0);
  }finally{
    await fs.rm(folder,{recursive:true,force:true});
  }
});
