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

test('the dated reference covers 36 distinct clubs with exactly four remaining matches each',()=>{
  const {allOfficial}=require('../research/ucl_official_matchday5.js');
  const appearances=new Map();
  for(const match of allOfficial){
    assert.notEqual(match.home,match.away);
    for(const club of [match.home,match.away]){
      assert.equal(typeof club,'string');
      assert.ok(club.trim().length>0);
      appearances.set(club,(appearances.get(club)||0)+1);
    }
  }
  assert.equal(appearances.size,36);
  for(const [club,count] of appearances){
    assert.equal(count,4,club+' should appear in each of MD5-MD8 exactly once');
  }
});

test('every club plays once in each official remaining matchday',()=>{
  const {allOfficial}=require('../research/ucl_official_matchday5.js');
  const roundByDate={
    '2026-11-24':5,'2026-11-25':5,
    '2026-12-08':6,'2026-12-09':6,
    '2027-01-19':7,'2027-01-20':7,
    '2027-01-27':8
  };
  const clubsByRound=new Map([[5,new Set()],[6,new Set()],[7,new Set()],[8,new Set()]]);
  for(const match of allOfficial){
    const date=match.kickoffUtc.slice(0,10);
    const round=roundByDate[date];
    assert.ok(round,match.kickoffUtc+' belongs to an unsupported matchday');
    assert.ok(Number.isFinite(Date.parse(match.kickoffUtc)));
    assert.equal(new Date(match.kickoffUtc).toISOString(),match.kickoffUtc);
    const clubs=clubsByRound.get(round);
    for(const club of [match.home,match.away]){
      assert.equal(clubs.has(club),false,club+' appears twice in MD'+round);
      clubs.add(club);
    }
  }
  for(const [round,clubs] of clubsByRound)
    assert.equal(clubs.size,36,'MD'+round+' must have 36 unique participants');
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

test('the full UEFA gate rejects extra unlisted fixtures even when the required 72 are present',()=>{
  const {allOfficial,verifyAllUpcoming}=require('../research/ucl_official_matchday5.js');
  const rows=allOfficial.map((item,i)=>({
    matchID:400000+i,matchDateTimeUTC:item.kickoffUtc,
    team1:{teamId:2000+i*2,teamName:item.home},
    team2:{teamId:2001+i*2,teamName:item.away},
    matchIsFinished:false,matchResults:[]
  }));
  const unlisted={matchID:777777,matchDateTimeUTC:'2026-11-20T20:00:00Z',
    team1:{teamId:9000,teamName:'Unlisted FC'},
    team2:{teamId:9001,teamName:'Another Unlisted FC'},
    matchIsFinished:false,matchResults:[]};
  const result=verifyAllUpcoming([...rows,unlisted]);
  assert.equal(result.ok,false);
  assert.equal(result.checked,72);
  assert.equal(result.unlistedMatches,1);
  assert.match(result.issues.join(' '),/Niezatwierdzony mecz/);
  assert.equal(result.predictionsAllowed,false);
});

test('unknown later knockout matches remain blocked until separately reviewed',()=>{
  const {allOfficial,verifyAllUpcoming}=require('../research/ucl_official_matchday5.js');
  const rows=allOfficial.map((item,i)=>({
    matchID:500000+i,matchDateTimeUTC:item.kickoffUtc,
    team1:{teamId:3000+i*2,teamName:item.home},
    team2:{teamId:3001+i*2,teamName:item.away},
    matchIsFinished:false,matchResults:[]
  }));
  const unknown={matchID:888888,matchDateTimeUTC:'2027-02-17T20:00:00Z',
    team1:{teamId:9900,teamName:'Unlisted FC'},
    team2:{teamId:9901,teamName:'Another Unlisted FC'},
    matchIsFinished:false,matchResults:[]};
  assert.equal(verifyAllUpcoming([...rows,unknown]).ok,false);
  // Completed matches before 5 November are outside this reference scope.
  rows.push({matchID:888889,matchDateTimeUTC:'2026-11-04T20:00:00Z',
    team1:{teamId:9930,teamName:'Prior Round Club'},
    team2:{teamId:9931,teamName:'Different Club'},
    matchIsFinished:true,matchResults:[]});
  assert.equal(verifyAllUpcoming(rows).ok,true);
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
