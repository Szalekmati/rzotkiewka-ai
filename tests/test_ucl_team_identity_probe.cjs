'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {inspectTeamIdentity,main}=require('../research/ucl_team_identity_probe.cjs');
const NOW='2026-11-15T19:45:00Z';
function fixture(id,teamId,teamName,opponentId=900+id,opponent='Other Club'){
  return {
    matchID:id,leagueShortcut:'ucl',leagueSeason:2026,leagueId:2800,
    matchDateTimeUTC:'2027-01-27T20:00:00Z',matchIsFinished:false,matchResults:[],
    team1:{teamId,teamName},team2:{teamId:opponentId,teamName:opponent}
  };
}
test('foreign team label stops research and reports exact public IDs',()=>{
  const report=inspectTeamIdentity([
    fixture(1,33,'Excelsior Rotterdam'),fixture(2,33,'Excelsior Rotterdam'),
    fixture(3,12,'FC Barcelona')
  ],NOW);
  assert.equal(report.status,'STOP_FOREIGN_CLUB_LABEL');
  assert.equal(report.excelsiorMatches,2);
  assert.equal(report.barcelonaMatches,1);
  assert.deepEqual(report.targetTeamIds.map(x=>x.teamId),[12,33]);
  assert.equal(report.publicationAllowed,false);
  assert.equal(report.predictionsAllowed,false);
  assert.equal(report.premiumAllowed,false);
});
test('identical provider ID under conflicting labels is surfaced, never silently reconciled',()=>{
  const report=inspectTeamIdentity([
    fixture(1,33,'Excelsior Rotterdam'),fixture(2,33,'FC Barcelona')
  ],NOW);
  assert.equal(report.status,'STOP_FOREIGN_CLUB_LABEL');
  assert.deepEqual(report.targetTeamIds[0].namesSeen,['Excelsior Rotterdam','FC Barcelona']);
  assert.equal(report.independentlyVerifiedTeamIds,false);
});
test('four foreign UCL fixtures remain blocked even with consistent team ID',()=>{
  const rows=Array.from({length:4},(_,i)=>fixture(i+1,33,'Excelsior Rotterdam'));
  const report=inspectTeamIdentity(rows,NOW);
  assert.equal(report.status,'STOP_FOREIGN_CLUB_LABEL');
  assert.equal(report.excelsiorMatches,4);
  assert.equal(report.targetTeamIds.length,1);
});
test('correct-looking Barcelona records still need independent official identity checks',()=>{
  const report=inspectTeamIdentity([fixture(1,12,'FC Barcelona')],NOW);
  assert.equal(report.status,'NEEDS_INDEPENDENT_VERIFICATION');
  assert.equal(report.barcelonaMatches,1);
  assert.equal(report.independentlyVerifiedTeamIds,false);
  assert.equal(report.publicationAllowed,false);
});
test('malformed source metadata and arguments fail closed without network',async()=>{
  for(const bad of [[],null,[{matchID:1}],[(r=>({...r,leagueShortcut:'pl'}))(fixture(1,33,'Excelsior Rotterdam'))]]){
    assert.equal(inspectTeamIdentity(bad,NOW).status,'STOP');
  }
  assert.equal(await main([]),2);
});
