/* Dated UEFA 2026/27 matchday 5 facts, offline tests only.
 * Production release is explicitly blocked irrespective of spotcheck success.
 */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {official,verify,norm,matchName} = require('../research/ucl_official_matchday5.js');
function payload(){
  return official.map((item,i)=>({
    matchID:10000+i,
    matchDateTimeUTC:item.kickoffUtc,
    team1:{teamId:100+i*2,teamName:item.home},
    team2:{teamId:101+i*2,teamName:item.away},
    matchIsFinished:false,matchResults:[],
  }));
}
test('official dated UEFA reference contains exactly 18 unique ordered pair/date matches',()=>{
  assert.equal(official.length,18);
  assert.equal(official.filter(x=>x.kickoffUtc.startsWith('2026-11-24')).length,9);
  assert.equal(official.filter(x=>x.kickoffUtc.startsWith('2026-11-25')).length,9);
  const keys=official.map(x=>[x.kickoffUtc,x.home,x.away].join('/'));
  assert.equal(new Set(keys).size,18);
});
test('complete source matches only the known 18 official facts, not the whole season',()=>{
  const report=verify(payload());
  assert.equal(report.ok,true);
  assert.equal(report.checked,18);
  assert.equal(report.expected,18);
  assert.equal(report.fullSeasonVerified,false);
  assert.equal(report.clubIdsIndependentlyVerified,false);
  assert.equal(report.predictionsAllowed,false);
});
test('missing official match blocks preview',()=>{
  const report=verify(payload().slice(1));
  assert.equal(report.ok,false);
  assert.equal(report.checked,17);
});
test('duplicate official fixture with changed provider ID blocks preview',()=>{
  const rows=payload();
  rows.push({...rows[0],matchID:55555});
  const report=verify(rows);
  assert.equal(report.ok,false);
  assert.match(report.issues.join(' '),/wiele dopasowań/);
});
test('changed kick-off blocks even with the correct two team names',()=>{
  const rows=payload();
  rows[2].matchDateTimeUTC='2026-11-24T19:00:00Z';
  const report=verify(rows);
  assert.equal(report.ok,false);
  assert.match(report.issues.join(' '),/termin różni/);
});
test('swapped home/away roles block preview',()=>{
  const rows=payload();
  const home=rows[2].team1;
  rows[2].team1=rows[2].team2;rows[2].team2=home;
  assert.equal(verify(rows).ok,false);
});
test('wrong game/club feed fails closed',()=>{
  const rows=payload();
  rows[8].team1.teamName='AZ Alkmaar';
  assert.equal(verify(rows).ok,false);
});
test('name comparison permits only predeclared variants and accents, never loose substrings',()=>{
  assert.equal(matchName('FC Barcelona','Barcelona'),true);
  assert.equal(matchName('Bodo Glimt','Bodø/Glimt'),true);
  assert.equal(matchName('Arsenal Reserves','Arsenal'),false);
  assert.equal(matchName('Manchester United U21','Manchester United'),false);
  assert.equal(norm('Atlético de Madrid'),'atletico de madrid');
});
test('wrong source type is blocked',()=>{
  for(const value of [null,{},'',false])assert.equal(verify(value).ok,false);
});
test('all upcoming reference includes 72 UEFA matches on seven match dates',()=>{
  const {allOfficial,officialRemaining}=require('../research/ucl_official_matchday5.js');
  assert.equal(officialRemaining.length,54);
  assert.equal(allOfficial.length,72);
  const days={};
  for(const fixture of allOfficial){
    const day=fixture.kickoffUtc.slice(0,10);
    days[day]=(days[day]||0)+1;
  }
  assert.deepEqual(days,{
    '2026-11-24':9,'2026-11-25':9,
    '2026-12-08':9,'2026-12-09':9,
    '2027-01-19':9,'2027-01-20':9,
    '2027-01-27':18
  });
  assert.equal(new Set(allOfficial.map(x=>x.kickoffUtc+'/'+x.home+'/'+x.away)).size,72);
});

test('all upcoming fixtures require 72 out of 72 identical official pair/kickoff facts',()=>{
  const {allOfficial,verifyAllUpcoming}=require('../research/ucl_official_matchday5.js');
  const rows=allOfficial.map((item,i)=>({
    matchID:300000+i,
    matchDateTimeUTC:item.kickoffUtc,
    team1:{teamId:1000+i*2,teamName:item.home},
    team2:{teamId:1001+i*2,teamName:item.away},
    matchIsFinished:false,matchResults:[],
  }));
  const ok=verifyAllUpcoming(rows);
  assert.equal(ok.ok,true);
  assert.equal(ok.checked,72);
  assert.equal(ok.expected,72);
  assert.equal(ok.fullSeasonVerified,false);
  assert.equal(ok.clubIdsIndependentlyVerified,false);
  assert.equal(ok.predictionsAllowed,false);
  const missing=verifyAllUpcoming(rows.slice(0,71));
  assert.equal(missing.ok,false);
  assert.equal(missing.checked,71);
  const wrong=rows.map(x=>({
    ...x,
    team1:{...x.team1},
    team2:{...x.team2}
  }));
  wrong[71].matchDateTimeUTC='2027-01-27T19:00:00Z';
  assert.equal(verifyAllUpcoming(wrong).ok,false);
  const swapped=rows.map(x=>({
    ...x,
    team1:{...x.team1},
    team2:{...x.team2}
  }));
  [swapped[36].team1,swapped[36].team2]=[swapped[36].team2,swapped[36].team1];
  assert.equal(verifyAllUpcoming(swapped).ok,false);
});

test('page must enforce official check before showing any source fixtures',()=>{
  const html=fs.readFileSync(path.join(__dirname,'../research/ucl_calendar_preview.html'),'utf8');
  assert.match(html,/src="\.\/ucl_official_matchday5\.js"/);
  const a=html.indexOf('UclOfficialMatchday5.verifyAllUpcoming(rows)');
  const b=html.indexOf('UclPreview.inspect(rows');
  assert.ok(a>0&&b>a);
  assert.match(html,/officialCheck\.ok/);
  assert.match(html,/Nie pokazujemy terminarza/);
});
