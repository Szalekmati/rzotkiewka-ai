'use strict';
// Offline synthetic fixtures only. No API, network or production data.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
const os=require('node:os');
const {buildBundle,inspectBundle,main,ttl}=
  require('../research/german_fixture_bundle.cjs');
const NOW='2026-11-15T18:00:00Z';
function row(code,lid,id,homeId,awayId,when,finished=false){
  return {leagueShortcut:code,leagueSeason:2026,leagueId:lid,
    matchID:id,matchDateTimeUTC:when,matchIsFinished:finished,
    team1:{teamId:homeId,teamName:code+' Club '+homeId},
    team2:{teamId:awayId,teamName:code+' Club '+awayId},
    matchResults:finished?[{resultTypeID:2,pointsTeam1:2,pointsTeam2:1}]:[]};
}
function sample(){
  const out={};
  for(const [n,code] of ['bl1','bl2','bl3'].entries()){
    const lid=101+n,base=(n+1)*10000;
    out[code]=[
      row(code,lid,base+1,base+2,base+3,'2026-11-14T15:00:00Z',true),
      row(code,lid,base+2,base+3,base+2,'2026-11-25T20:00:00Z')
    ];
  }
  return out;
}
test('three leagues in one research-only cache, stripped source data',()=>{
  const input=sample();input.bl1[1].team1.teamIconUrl='https://example.com/icon.png';
  const result=buildBundle(input,NOW);
  assert.equal(result.ok,true,result.reason);
  const doc=result.snapshot;
  assert.deepEqual(Object.keys(doc.leagues),['bl1','bl2','bl3']);
  assert.equal(doc.leagues.bl1.upcoming_count,1);
  assert.equal(doc.leagues.bl2.source_records,2);
  assert.equal(doc.production_release_allowed,false);
  assert.equal(doc.predictions_allowed,false);
  assert.equal(doc.premium_allowed,false);
  assert.equal(doc.completeness_independently_verified,false);
  assert.doesNotMatch(JSON.stringify(doc),/teamIconUrl|icon\.png|matchResults|pointsTeam1/);
  assert.equal(inspectBundle(doc,NOW).usable,true);
});
test('wrong league, season, missing league and inconsistent provider ID fail closed',()=>{
  const missing=sample();delete missing.bl2;
  assert.equal(buildBundle(missing,NOW).ok,false);
  const bad=sample();bad.bl2[1].leagueShortcut='bl1';
  assert.equal(buildBundle(bad,NOW).ok,false);
  const badSeason=sample();badSeason.bl3[0].leagueSeason=2025;
  assert.equal(buildBundle(badSeason,NOW).ok,false);
  const badProvider=sample();badProvider.bl1[0].leagueId=999;
  assert.equal(buildBundle(badProvider,NOW).ok,false);
  const sameProvider=sample();sameProvider.bl3.forEach(x=>x.leagueId=102);
  assert.equal(buildBundle(sameProvider,NOW).ok,false);
});
test('duplicated match IDs and home-away pairs block without guessing',()=>{
  const sameId=sample();sameId.bl1[1].matchID=sameId.bl1[0].matchID;
  assert.equal(buildBundle(sameId,NOW).ok,false);
  const secondPair=sample();secondPair.bl1.push(
    row('bl1',101,10004,10003,10002,'2026-12-18T20:00:00Z'));
  assert.equal(buildBundle(secondPair,NOW).ok,false);
});
test('bad UTC times, delayed results and future final scores block',()=>{
  const invalid=sample();invalid.bl1[1].matchDateTimeUTC='2026-02-30T20:00:00Z';
  assert.equal(buildBundle(invalid,NOW).ok,false);
  const missing=sample();missing.bl1[0].matchIsFinished=false;missing.bl1[0].matchResults=[];
  missing.bl1[0].matchDateTimeUTC='2026-11-12T15:00:00Z'; // more than 48h overdue
  assert.equal(buildBundle(missing,NOW).ok,false);
  const future=sample();future.bl1[1].matchIsFinished=true;
  future.bl1[1].matchResults=[{resultTypeID:2,pointsTeam1:1,pointsTeam2:0}];
  assert.equal(buildBundle(future,NOW).ok,false);
});
test('stale, future and modified bundles are not usable',()=>{
  const doc=JSON.parse(JSON.stringify(buildBundle(sample(),NOW).snapshot));
  assert.equal(ttl,21600000);
  assert.equal(inspectBundle(doc,'2026-11-15T23:59:59Z').usable,true);
  assert.equal(inspectBundle(doc,'2026-11-16T00:00:00Z').status,'STALE_OR_FUTURE');
  assert.equal(inspectBundle(doc,'2026-11-15T17:59:59Z').usable,false);
  doc.leagues.bl1.fixtures[0].home='tampered';
  assert.equal(inspectBundle(doc,'2026-11-15T19:00:00Z').status,'INVALID_SNAPSHOT');
});
test('CLI writes one local snapshot, refuses overwrite and invalid sources',async()=>{
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'rzotkiewka-german-'));
  try{
    const data=sample(),flags=[];
    for(const code of ['bl1','bl2','bl3']){
      const file=path.join(dir,code+'.json');
      await fs.writeFile(file,JSON.stringify(data[code]));
      flags.push('--'+code,file);
    }
    const output=path.join(dir,'german.research.json');
    assert.equal(await main([...flags,'--output',output],NOW),0);
    const doc=JSON.parse(await fs.readFile(output,'utf8'));
    assert.equal(doc.status,'RESEARCH_ONLY');
    assert.equal(doc.production_release_allowed,false);
    const old=await fs.readFile(output,'utf8');
    assert.equal(await main([...flags,'--output',output],NOW),2);
    assert.equal(await fs.readFile(output,'utf8'),old);
    assert.equal(await main([...flags,'--output',path.join(dir,'index.html')],NOW),2);
    const bad=path.join(dir,'bad.research.json');
    await fs.writeFile(flags[1],'[]');
    assert.equal(await main([...flags,'--output',bad],NOW),1);
    await assert.rejects(fs.stat(bad),{code:'ENOENT'});
    assert.equal(await main([]),2);
  }finally{
    await fs.rm(dir,{recursive:true,force:true});
  }
});