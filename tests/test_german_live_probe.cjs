'use strict';
// Offline tests with injected fake fetch: never make an external HTTP request.
const test=require('node:test');
const assert=require('node:assert/strict');
const {fetchThree,makeAudit,main,urlFor,DELAY_MS}=require('../research/german_live_probe.cjs');
const NOW='2026-11-15T18:00:00Z';
function single(code,leagueId,matchId,home,away,iso,finished){
  return {
    leagueId,leagueShortcut:code,leagueSeason:2026,matchID:matchId,
    matchDateTimeUTC:iso,matchIsFinished:finished,
    team1:{teamId:home,teamName:code+'-Team-'+home},
    team2:{teamId:away,teamName:code+'-Team-'+away},
    matchResults:finished?[{resultTypeID:2,pointsTeam1:1,pointsTeam2:0}]:[]
  };
}
function fixtureDataset(code){
  const n=['bl1','bl2','bl3'].indexOf(code)+1,ids=n*10000,leagueId=n*100;
  return [
    single(code,leagueId,ids+1,ids+2,ids+3,'2026-11-11T20:00:00Z',true),
    single(code,leagueId,ids+2,ids+3,ids+2,'2026-12-02T20:00:00Z',false)
  ];
}
function mockedFetch(record){
  return async (url,options)=>{
    record.push({url,options});
    const code=url.split('/')[4];
    return {ok:true,status:200,headers:{get:()=>null},
      text:async()=>JSON.stringify(fixtureDataset(code))};
  };
}
test('three fixed league GETs occur sequentially with one-second-plus gaps',async()=>{
  const seen=[],pauses=[];
  const rows=await fetchThree(mockedFetch(seen),async ms=>pauses.push(ms));
  assert.deepEqual(seen.map(x=>x.url),[
    urlFor('bl1'),urlFor('bl2'),urlFor('bl3')]);
  assert.deepEqual(pauses,[DELAY_MS,DELAY_MS]);
  for(const x of seen){
    assert.equal(x.options.method,'GET');
    assert.equal(x.options.redirect,'error');
    assert.equal(x.options.cache,'no-store');
    assert.ok(x.options.signal);
  }
  assert.deepEqual(Object.keys(rows),['bl1','bl2','bl3']);
  assert.equal(makeAudit(rows,NOW).status,'RESEARCH_ONLY_NO_RELEASE');
  assert.deepEqual(makeAudit(rows,NOW).upcoming_per_league,{bl1:1,bl2:1,bl3:1});
  assert.equal(makeAudit(rows,NOW).production_release_allowed,false);
  assert.equal(makeAudit(rows,NOW).predictions_allowed,false);
});
test('no live request is made without explicit --live',async()=>{
  let calls=0;
  const fake=async()=>{calls++;throw Error('Should never fetch');};
  assert.equal(await main([],{fetchFn:fake}),2);
  assert.equal(await main(['--help'],{fetchFn:fake}),0);
  assert.equal(await main(['--file','x'],{fetchFn:fake}),2);
  assert.equal(calls,0);
});
test('stale/invalid source feed rejects research approval',async()=>{
  const dataset=Object.fromEntries(['bl1','bl2','bl3'].map(c=>[c,fixtureDataset(c)]));
  dataset.bl2[1].leagueShortcut='ucl';
  const result=makeAudit(dataset,NOW);
  assert.equal(result.status,'STOP');
  assert.equal(result.production_release_allowed,false);
});
test('invalid HTTP or oversized/malformed responses fail and never fetch later leagues',async()=>{
  let count=0;
  await assert.rejects(fetchThree(async()=>{count++;return {ok:false,status:429};},async()=>{}),/429/);
  assert.equal(count,1);
  await assert.rejects(fetchThree(async()=>({ok:true,headers:{get:()=>String(8_000_001)}}),async()=>{}),/size/);
  await assert.rejects(fetchThree(async()=>({
    ok:true,headers:{get:()=>null},text:async()=>'[]'
  }),async()=>{}),/number/);
});
test('streaming response is bounded even when Content-Length is absent',async()=>{
  let cancelled=false;
  const fake=async()=>({
    ok:true,headers:{get:()=>null},
    body:{getReader:()=>{
      let i=0;
      return {read:async()=>({done:false,value:new Uint8Array(++i===1?7_999_999:2)}),
        cancel:async()=>{cancelled=true;}};
    }}
  });
  await assert.rejects(fetchThree(fake,async()=>{}),/size/);
  assert.equal(cancelled,true);
});