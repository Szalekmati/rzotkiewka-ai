/* Official-source dated fixture spot-check for 2026/27 UEFA Champions League MD5–MD8.
 * Facts manually transcribed from UEFA's dated public fixture schedule:
 * https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-uefa-champions-league-all-the-league-phase-fixtures-a/
 * UEFA source dated 2026-11-04; all times CET (UTC+01:00).
 * Local provider-name variants are UNVERIFIED candidate strings. Never
 * claim full season verification or source/license approval.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.UclOfficialMatchday5=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const sourceUrl='https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-uefa-champions-league-all-the-league-phase-fixtures-a/';
  const day24='2026-11-24',day25='2026-11-25';
  const E=(day,clock,home,away)=>Object.freeze({
    kickoffUtc:day+'T'+(clock==='early'?'17:45:00':'20:00:00')+'Z',
    home,away
  });
  const official=Object.freeze([
    E(day24,'early','Bodø/Glimt','LASK'),
    E(day24,'early','Galatasaray','Aston Villa'),
    E(day24,'standard','Arsenal','Borussia Dortmund'),
    E(day24,'standard','Como','AEK Athens'),
    E(day24,'standard','Feyenoord','Porto'),
    E(day24,'standard','Manchester City','Napoli'),
    E(day24,'standard','Leipzig','Lens'),
    E(day24,'standard','Real Madrid','PSV Eindhoven'),
    E(day24,'standard','Slovan Bratislava','Real Betis'),
    E(day25,'early','Sabah','Barcelona'),
    E(day25,'early','Slavia Praha','Villarreal'),
    E(day25,'standard','Atlético de Madrid','Viking'),
    E(day25,'standard','Club Brugge','Liverpool'),
    E(day25,'standard','Inter','Stuttgart'),
    E(day25,'standard','Shakhtar Donetsk','Fenerbahçe'),
    E(day25,'standard','Lille','Bayern München'),
    E(day25,'standard','Paris Saint-Germain','Roma'),
    E(day25,'standard','Sporting CP','Manchester United'),
  ]);
  // Official remaining league-phase fixtures, MD6–MD8, dated 2026-11-04.
  // As with MD5, all dates are CET at source; E() converts 18:45 and 21:00 to UTC.
  const officialRemaining=Object.freeze([
    // MD6 — Tuesday 8 December (9)
    E('2026-12-08','early','Viking','Feyenoord'),
    E('2026-12-08','early','Villarreal','Sabah'),
    E('2026-12-08','standard','AEK Athens','Galatasaray'),
    E('2026-12-08','standard','Roma','Sporting CP'),
    E('2026-12-08','standard','Aston Villa','Paris Saint-Germain'),
    E('2026-12-08','standard','Barcelona','Manchester City'),
    E('2026-12-08','standard','Bayern München','Slavia Praha'),
    E('2026-12-08','standard','Manchester United','Leipzig'),
    E('2026-12-08','standard','Napoli','Club Brugge'),
    // MD6 — Wednesday 9 December (9)
    E('2026-12-09','early','Real Betis','Como'),
    E('2026-12-09','early','Slovan Bratislava','Shakhtar Donetsk'),
    E('2026-12-09','standard','Arsenal','Real Madrid'),
    E('2026-12-09','standard','Borussia Dortmund','Inter'),
    E('2026-12-09','standard','LASK','Fenerbahçe'),
    E('2026-12-09','standard','Liverpool','Porto'),
    E('2026-12-09','standard','Lens','Bodø/Glimt'),
    E('2026-12-09','standard','PSV Eindhoven','Atlético de Madrid'),
    E('2026-12-09','standard','Stuttgart','Lille'),
    // MD7 — Tuesday 19 January (9)
    E('2027-01-19','early','Bodø/Glimt','Atlético de Madrid'),
    E('2027-01-19','early','Galatasaray','Feyenoord'),
    E('2027-01-19','standard','AEK Athens','Roma'),
    E('2027-01-19','standard','Aston Villa','Borussia Dortmund'),
    E('2027-01-19','standard','Inter','Liverpool'),
    E('2027-01-19','standard','Porto','Slavia Praha'),
    E('2027-01-19','standard','Lille','Slovan Bratislava'),
    E('2027-01-19','standard','Real Madrid','LASK'),
    E('2027-01-19','standard','Stuttgart','Club Brugge'),
    // MD7 — Wednesday 20 January (9)
    E('2027-01-20','early','Fenerbahçe','Villarreal'),
    E('2027-01-20','early','Sabah','Napoli'),
    E('2027-01-20','standard','Como','Paris Saint-Germain'),
    E('2027-01-20','standard','Manchester United','Bayern München'),
    E('2027-01-20','standard','Leipzig','Shakhtar Donetsk'),
    E('2027-01-20','standard','Lens','Manchester City'),
    E('2027-01-20','standard','Real Betis','Arsenal'),
    E('2027-01-20','standard','Sporting CP','Barcelona'),
    E('2027-01-20','standard','Viking','PSV Eindhoven'),
    // MD8 — Wednesday 27 January: all matches at 21:00 CET (18)
    E('2027-01-27','standard','Arsenal','Sabah'),
    E('2027-01-27','standard','Roma','Lille'),
    E('2027-01-27','standard','Atlético de Madrid','Fenerbahçe'),
    E('2027-01-27','standard','Borussia Dortmund','AEK Athens'),
    E('2027-01-27','standard','Club Brugge','Bodø/Glimt'),
    E('2027-01-27','standard','Bayern München','Real Betis'),
    E('2027-01-27','standard','Barcelona','Como'),
    E('2027-01-27','standard','Shakhtar Donetsk','Real Madrid'),
    E('2027-01-27','standard','Feyenoord','Leipzig'),
    E('2027-01-27','standard','LASK','Porto'),
    E('2027-01-27','standard','Liverpool','Lens'),
    E('2027-01-27','standard','Manchester City','Sporting CP'),
    E('2027-01-27','standard','Paris Saint-Germain','Galatasaray'),
    E('2027-01-27','standard','PSV Eindhoven','Stuttgart'),
    E('2027-01-27','standard','Slavia Praha','Aston Villa'),
    E('2027-01-27','standard','Napoli','Viking'),
    E('2027-01-27','standard','Villarreal','Manchester United'),
    E('2027-01-27','standard','Slovan Bratislava','Inter'),
  ]);
  const allOfficial=Object.freeze([...official,...officialRemaining]);
  const aliases=Object.freeze({
    'Bodø/Glimt':['FK Bodø/Glimt','FK Bodo Glimt','Bodoe/Glimt'],
    LASK:['LASK Linz'],
    Galatasaray:['Galatasaray Istanbul'],
    'Aston Villa':['Aston Villa FC'],
    Arsenal:['Arsenal FC'],
    'Borussia Dortmund':['BVB Borussia Dortmund'],
    Como:['Como 1907','Como 1907 FC'],
    'AEK Athens':['AEK Athen','AEK Athina'],
    Feyenoord:['Feyenoord Rotterdam'],
    Porto:['FC Porto'],
    'Manchester City':['Manchester City FC','Man City'],
    Napoli:['SSC Napoli','SSC Neapel'],
    Leipzig:['RB Leipzig','RasenBallsport Leipzig'],
    Lens:['RC Lens'],
    'Real Madrid':['Real Madrid CF'],
    'PSV Eindhoven':['PSV'],
    'Slovan Bratislava':['SK Slovan Bratislava'],
    'Real Betis':['Real Betis Balompié','Betis Sevilla'],
    Sabah:['Sabah FK'],
    Barcelona:['FC Barcelona'],
    'Slavia Praha':['SK Slavia Praha','Slavia Prag','SK Slavia Prag'],
    Villarreal:['Villarreal CF'],
    'Atlético de Madrid':['Atletico Madrid','Atletico de Madrid'],
    Viking:['Viking FK'],
    'Club Brugge':['Club Brugge KV','FC Brügge'],
    Liverpool:['Liverpool FC'],
    Inter:['Inter Milano','Inter Mailand','FC Internazionale Milano','Internazionale'],
    Stuttgart:['VfB Stuttgart'],
    'Shakhtar Donetsk':['FC Shakhtar Donetsk','Schachtar Donezk','Schachtjor Donezk'],
    'Fenerbahçe':['Fenerbahce Istanbul','Fenerbahce'],
    Lille:['LOSC Lille','Lille OSC'],
    'Bayern München':['FC Bayern München','Bayern Munich'],
    'Paris Saint-Germain':['Paris SG','PSG','Paris Saint Germain'],
    Roma:['AS Roma'],
    'Sporting CP':['Sporting Lisbon','Sporting Lissabon','Sporting Clube de Portugal'],
    'Manchester United':['Manchester United FC','Man United'],
  });
  function norm(value){
    return typeof value==='string'
      ? value.normalize('NFKD').replace(/[\u0300-\u036f]/g,'')
        .replace(/[øØ]/g,'o').replace(/[łŁ]/g,'l').replace(/[ß]/g,'ss')
        .toLocaleLowerCase('en-US').replace(/[^a-z0-9]+/g,' ').trim().replace(/\s+/g,' ')
      : '';
  }
  function matchName(actual,canonical){
    const input=norm(actual);
    return input!==''&&[canonical,...(aliases[canonical]||[])].some(name=>norm(name)===input);
  }
  function verifySet(payload,reference,scope){
    const problems=[];
    if(!Array.isArray(payload)) return {ok:false,checked:0,expected:reference.length,issues:['Brak tabeli meczów w danych.']};
    for(const item of reference){
      const candidates=payload.filter(row=>row&&typeof row==='object'&&row.team1&&row.team2
        &&matchName(row.team1.teamName,item.home)&&matchName(row.team2.teamName,item.away));
      const label=item.home+' – '+item.away;
      if(candidates.length!==1) {
        problems.push(label+': '+(candidates.length===0?'brak jednoznacznego dopasowania':'wiele dopasowań'));
        continue;
      }
      const date=candidates[0].matchDateTimeUTC;
      const parsed=typeof date==='string'?Date.parse(date):NaN;
      if(!Number.isFinite(parsed)||new Date(parsed).toISOString()!==new Date(item.kickoffUtc).toISOString())
        problems.push(label+': termin różni się od oficjalnego zapisu UEFA (04.11.2026)');
    }
    return {
      ok:problems.length===0,
      expected:reference.length,
      checked:reference.length-problems.length,
      issues:problems.slice(0,10),
      issueCount:problems.length,
      sourceUrl,
      referenceAsOf:'2026-11-04',
      scope,
      fullSeasonVerified:false,
      clubIdsIndependentlyVerified:false,
      predictionsAllowed:false,
    };
  }
  function verify(payload) { return verifySet(payload,official,'matchday5-only'); }
  function verifyAllUpcoming(payload) {
    return verifySet(payload,allOfficial,'league-phase-matchdays-5-to-8-only');
  }
  return Object.freeze({official,officialRemaining,allOfficial,verify,verifyAllUpcoming,norm,matchName});
});
