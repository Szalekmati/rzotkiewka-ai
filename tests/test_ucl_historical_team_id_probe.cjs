'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {URL,inspectHistoricalIds,fetchHistorical,main}=
  require('../research/ucl_historical_team_id_probe.cjs');
const NOW='2026-11-15T19:45:00Z';
const row=(id,teamId,name,leagueSeason=2025)=>({
  matchID:id,leagueId:2500,leagueShortcut:'ucl',leagueSeason,
  team1:{teamId,teamName:name},team2:{teamId:800+id,teamName:'Other FC'}
});
test('two historical clubs are kept separate even when both have many appearances',()=>{
  const report=inspectHistoricalIds([
    row(1,100,'FC Barcelona'),row(2,100,'Barcelona'),
    row(3,356,'Excelsior Rotterdam')
  ],NOW);
  assert.equal(report.status,'STOP_IDENTITY_REVIEW');
  assert.equal(report.foreignExcelsiorPresent,true);
  assert.equal(report.identityReviewRequired,true);
  assert.equal(report.barcelonaMatches,2);
  assert.equal(report.excelsiorMatches,1);
  assert.deepEqual(report.historicalNameIds.map(x=>x.teamId),[100,356]);
  assert.deepEqual(report.id356NamesSeen,['Excelsior Rotterdam']);
  assert.equal(report.currentSeasonIdentityApproved,false);
  assert.equal(report.publicationAllowed,false);
});
test('same ID with contradictory historical labels is exposed, never resolved',()=>{
  const report=inspectHistoricalIds([row(1,356,'Barcelona'),row(2,356,'Excelsior Rotterdam')],NOW);
  assert.equal(report.status,'STOP_IDENTITY_REVIEW');
  assert.equal(report.barcelonaMatches,1);
  assert.equal(report.excelsiorMatches,1);
  assert.deepEqual(report.id356NamesSeen,['Barcelona','Excelsior Rotterdam']);
  assert.equal(report.independentCurrentSeasonIdVerification,false);
});
test('historical feed without Barcelona but with Excelsior is an explicit STOP',()=>{
  const rows=Array.from({length:12},(_,i)=>row(i+1,356,'Excelsior Rotterdam'));
  const report=inspectHistoricalIds(rows,NOW);
  assert.equal(report.status,'STOP_IDENTITY_REVIEW');
  assert.equal(report.barcelonaLabelMissing,true);
  assert.equal(report.foreignExcelsiorPresent,true);
  assert.equal(report.barcelonaMatches,0);
  assert.equal(report.excelsiorMatches,12);
  assert.deepEqual(report.historicalNameIds,[{
    type:'excelsior',teamId:356,appearances:12,namesSeen:['Excelsior Rotterdam']
  }]);
  assert.equal(report.publicationAllowed,false);
  assert.equal(report.currentSeasonIdentityApproved,false);
});

test('a feed with an identified Barcelona and no foreign club stays research-only',()=>{
  const report=inspectHistoricalIds([row(1,123,'Barcelona'),row(2,123,'FC Barcelona')],NOW);
  assert.equal(report.status,'HISTORICAL_READ_ONLY');
  assert.equal(report.identityReviewRequired,false);
  assert.equal(report.barcelonaMatches,2);
  assert.equal(report.currentSeasonIdentityApproved,false);
  assert.equal(report.publicationAllowed,false);
});

test('empty, mixed-source and mismatched metadata STOP',()=>{
  for(const rows of [
    [],null,[row(1,2,'FC Barcelona',2026)],
    [{...row(1,2,'Barcelona'),leagueShortcut:'la1'}],
    [row(1,2,'Barcelona'),{...row(2,3,'Excelsior Rotterdam'),leagueId:3000}]
  ])assert.equal(inspectHistoricalIds(rows,NOW).status,'STOP');
});
test('historical fixed endpoint does one read only and rejects oversized body',async()=>{
  let seen;
  const fn=async(url,opts)=>{
    seen={url,opts};
    return {ok:true,headers:{get:()=>null},text:async()=>JSON.stringify([row(1,100,'FC Barcelona')])};
  };
  const rows=await fetchHistorical(fn);
  assert.equal(rows.length,1);
  assert.equal(seen.url,URL);
  assert.equal(seen.opts.method,'GET');
  assert.equal(seen.opts.redirect,'error');
  await assert.rejects(fetchHistorical(async()=>({
    ok:true,headers:{get:()=>String(3_000_001)}
  })),/size/);
  assert.equal(await main([]),2);
});
