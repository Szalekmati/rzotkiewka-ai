/* Official-source spot-check for 2026/27 UEFA Champions League matchday 5.
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
  function verify(payload){
    const problems=[];
    if(!Array.isArray(payload)) return {ok:false,checked:0,expected:18,issues:['Brak tabeli meczów w danych.']};
    for(const item of official){
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
      expected:official.length,
      checked:official.length-problems.length,
      issues:problems.slice(0,10),
      issueCount:problems.length,
      sourceUrl,
      referenceAsOf:'2026-11-04',
      scope:'matchday5-only',
      fullSeasonVerified:false,
      clubIdsIndependentlyVerified:false,
      predictionsAllowed:false,
    };
  }
  return Object.freeze({official,verify,norm,matchName});
});
