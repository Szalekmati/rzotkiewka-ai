#!/usr/bin/env node
'use strict';
// Research-only shared fixture snapshot for Germany's three already-connected leagues.
// Offline only: no fetch, credentials, schedules, Pages changes or model calls.
const fs=require('node:fs/promises');
const crypto=require('node:crypto');
const codes=Object.freeze(['bl1','bl2','bl3']);
const season=2026;
const ttl=6*60*60*1000;
const maxRows=500;
const maxBytes=8000000;
const utcPattern=/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$/;
const validId=value=>Number.isSafeInteger(value)&&value>0;
const safeName=value=>typeof value==='string'&&
  value.trim().length>0&&value.length<=100&&!/[\u0000-\u001f\u007f]/.test(value);
const normalizedName=name=>name.trim().normalize('NFKC').toLocaleLowerCase('en-US');
const digest=value=>crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');
function utcTime(value){
  if(typeof value!=='string'||!utcPattern.test(value))return null;
  const millis=Date.parse(value);
  if(!Number.isFinite(millis))return null;
  const iso=new Date(millis).toISOString();
  if(iso.slice(0,10)!==value.slice(0,10))return null;
  const start=Date.parse('2026-07-01T00:00:00Z');
  const end=Date.parse('2027-07-01T00:00:00Z');
  return millis>=start&&millis<end?{millis,iso}:null;
}
function acceptedFinal(results){
  if(!Array.isArray(results))throw Error('invalid matchResults');
  const found=results.filter(x=>x&&typeof x==='object'&&
    (x.resultTypeID===2||/endergebnis/i.test(String(x.resultName||''))));
  if(found.length>1)throw Error('ambiguous final score');
  if(!found.length)return null;
  const final=found[0];
  if(!Number.isInteger(final.pointsTeam1)||!Number.isInteger(final.pointsTeam2)||
    final.pointsTeam1<0||final.pointsTeam1>40||
    final.pointsTeam2<0||final.pointsTeam2>40)
    throw Error('invalid final score');
  return [final.pointsTeam1,final.pointsTeam2];
}
function validateLeague(code,rows,now){
  if(!codes.includes(code))throw Error('unsupported league shortcut');
  if(!Array.isArray(rows)||rows.length<1||rows.length>maxRows)
    throw Error(code+': invalid or empty source list');
  let leagueId=null;
  const ids=new Set(),slots=new Set(),teamTimeSlots=new Set(),pairSeason=new Set(),teamNames=new Map(),nameIds=new Map();
  const fixtures=[];
  for(const [index,row] of rows.entries()){
    const label=code+' row '+(index+1)+': ';
    if(!row||typeof row!=='object'||Array.isArray(row))throw Error(label+'record');
    if(row.leagueShortcut!==code||row.leagueSeason!==season||!validId(row.leagueId))
      throw Error(label+'wrong league or season');
    if(leagueId===null)leagueId=row.leagueId;
    if(row.leagueId!==leagueId)throw Error(label+'mixed leagueId');
    if(!validId(row.matchID)||ids.has(row.matchID))throw Error(label+'match ID duplicate/invalid');
    ids.add(row.matchID);
    const dt=utcTime(row.matchDateTimeUTC);
    if(!dt)throw Error(label+'invalid UTC kickoff/season');
    const home=row.team1,away=row.team2;
    if(!home||!away||typeof home!=='object'||typeof away!=='object'||
      !validId(home.teamId)||!validId(away.teamId)||home.teamId===away.teamId||
      !safeName(home.teamName)||!safeName(away.teamName))
      throw Error(label+'invalid club identity');
    for(const t of [home,away]){
      const name=normalizedName(t.teamName);
      if((teamNames.has(t.teamId)&&teamNames.get(t.teamId)!==name)||
        (nameIds.has(name)&&nameIds.get(name)!==t.teamId))
        throw Error(label+'conflicting team ID/name');
      teamNames.set(t.teamId,name); nameIds.set(name,t.teamId);
    }
    const slot=dt.iso+'|'+home.teamId+'|'+away.teamId;
    if(slots.has(slot))throw Error(label+'duplicate fixture slot');
    slots.add(slot);
    // A club cannot play two fixtures at the exact same UTC kickoff, even
    // when the opponent and provider's match ID are different.
    for(const teamId of [home.teamId,away.teamId]){
      const teamSlot=dt.iso+'|'+teamId;
      if(teamTimeSlots.has(teamSlot))throw Error(label+'club double-booked at kickoff');
      teamTimeSlots.add(teamSlot);
    }
    const orderedPair=home.teamId+'|'+away.teamId;
    if(pairSeason.has(orderedPair))throw Error(label+'repeated home-away fixture this season');
    pairSeason.add(orderedPair);
    if(typeof row.matchIsFinished!=='boolean')throw Error(label+'missing finished flag');
    const final=acceptedFinal(row.matchResults);
    if(row.matchIsFinished!==Boolean(final))throw Error(label+'finished flag / final score conflict');
    // Any score data attached to a future game is suspicious, including
    // non-final or in-progress result records with the finished flag false.
    if(dt.millis>now&&row.matchResults.length!==0)
      throw Error(label+'future match already has result data');
    if(dt.millis>now&&row.matchIsFinished)throw Error(label+'future match marked finished');
    if(dt.millis<=now-48*3600000&&!row.matchIsFinished)
      throw Error(label+'overdue match without final score');
    if(dt.millis>now){
      fixtures.push(Object.freeze({
        match_id:row.matchID,kickoff_utc:dt.iso,
        home_id:home.teamId,home:home.teamName.trim(),
        away_id:away.teamId,away:away.teamName.trim()
      }));
    }
  }
  if(!fixtures.length)throw Error(code+': no future fixtures to research');
  fixtures.sort((a,b)=>a.kickoff_utc.localeCompare(b.kickoff_utc)||a.match_id-b.match_id);
  return {source:'OpenLigaDB',league_id:leagueId,league_shortcut:code,
    league_season:season,source_records:rows.length,upcoming_count:fixtures.length,fixtures};
}
function buildBundle(inputs, observedAt){
  try{
    const observed=Date.parse(observedAt);
    if(!Number.isFinite(observed)||typeof observedAt!=='string'||!/[Z]|[+-]\d\d:\d\d$/.test(observedAt))
      throw Error('invalid observedAt');
    if(!inputs||typeof inputs!=='object'||Array.isArray(inputs)||
      Object.keys(inputs).length!==3||!codes.every(c=>Object.hasOwn(inputs,c)))
      throw Error('all three league datasets required');
    const leagues={};const providerIds=new Set(),matchIds=new Set();
    for(const code of codes){
      const result=validateLeague(code,inputs[code],observed);
      if(providerIds.has(result.league_id))throw Error('provider leagueId reused across leagues');
      providerIds.add(result.league_id);
      for(const raw of inputs[code]){
        if(matchIds.has(raw.matchID))throw Error('match ID reused across leagues');
        matchIds.add(raw.matchID);
      }
      leagues[code]=result;
    }
    const snapshot={
      kind:'RZOTKIEWKA_GERMAN_LEAGUES_RESEARCH_CACHE',
      schema_version:1,status:'RESEARCH_ONLY',
      source:'OpenLigaDB',source_license:'ODbL-1.0',
      observed_at_utc:new Date(observed).toISOString(),
      expires_at_utc:new Date(observed+ttl).toISOString(),
      production_release_allowed:false,
      predictions_allowed:false,premium_allowed:false,
      completeness_independently_verified:false,leagues
    };
    snapshot.sha256=digest(snapshot.leagues);
    return {ok:true,snapshot};
  }catch(error){
    return {ok:false,status:'STOP',reason:String(error.message||'Invalid data').slice(0,150)};
  }
}
function inspectBundle(snapshot,at){
  const now=Date.parse(at);
  if(!Number.isFinite(now))return {usable:false,status:'INVALID_TIME'};
  if(!snapshot||snapshot.kind!=='RZOTKIEWKA_GERMAN_LEAGUES_RESEARCH_CACHE'||
    snapshot.schema_version!==1||snapshot.status!=='RESEARCH_ONLY'||
    snapshot.production_release_allowed!==false||
    snapshot.predictions_allowed!==false||snapshot.premium_allowed!==false||
    snapshot.completeness_independently_verified!==false||
    !snapshot.leagues||typeof snapshot.leagues!=='object'||
    Object.keys(snapshot.leagues).length!==3||!codes.every(c=>Object.hasOwn(snapshot.leagues,c))||
    !/^[a-f0-9]{64}$/.test(String(snapshot.sha256))||
    snapshot.sha256!==digest(snapshot.leagues))
    return {usable:false,status:'INVALID_SNAPSHOT'};
  const seenProviders=new Set();
  for(const code of codes){
    const l=snapshot.leagues[code];
    if(!l||l.league_shortcut!==code||l.league_season!==season||
      !validId(l.league_id)||seenProviders.has(l.league_id)||
      !Array.isArray(l.fixtures)||l.upcoming_count!==l.fixtures.length||
      l.upcoming_count===0||l.source!=='OpenLigaDB')
      return {usable:false,status:'INVALID_SNAPSHOT'};
    seenProviders.add(l.league_id);
  }
  const stamped=Date.parse(snapshot.observed_at_utc),end=Date.parse(snapshot.expires_at_utc);
  if(!Number.isFinite(stamped)||!Number.isFinite(end)||end-stamped!==ttl||
    now<stamped||now>=end)return {usable:false,status:'STALE_OR_FUTURE'};
  return {usable:true,status:'RESEARCH_ONLY',
    age_minutes:Math.floor((now-stamped)/60000),
    fixture_counts:Object.fromEntries(codes.map(c=>[c,snapshot.leagues[c].upcoming_count])),
    production_release_allowed:false};
}
async function main(args=process.argv.slice(2),observedAt=new Date().toISOString()){
  const flags=['--bl1','--bl2','--bl3','--output'];
  if(args.length===1&&args[0]==='--help'){
    process.stdout.write('Usage: node research/german_fixture_bundle.cjs --bl1 data.json --bl2 data.json --bl3 data.json --output result.research.json\n');
    return 0;
  }
  if(args.length!==8||args.some((v,i)=>i%2===0&&!flags.includes(v))||
    new Set(args.filter((v,i)=>i%2===0)).size!==4||
    args.some((v,i)=>i%2===1&&(!v||v.startsWith('--')))){
    process.stderr.write('STOP: provide exactly three sources and an output path\n');
    return 2;
  }
  const options={};for(let i=0;i<8;i+=2)options[args[i]]=args[i+1];
  if(!options['--output'].endsWith('.research.json')||
    Object.values(options).some((v,i,a)=>a.indexOf(v)!==i)){
    process.stderr.write('STOP: unsafe/reused file path\n');return 2;
  }
  try{
    const inputs={};
    for(const code of codes){
      const file=options['--'+code],stat=await fs.stat(file);
      if(!stat.isFile()||stat.size<1||stat.size>maxBytes)throw Error('source too large/invalid');
      inputs[code]=JSON.parse(await fs.readFile(file,'utf8'));
    }
    const result=buildBundle(inputs,observedAt);
    if(!result.ok){process.stderr.write('STOP: '+result.reason+'\n');return 1;}
    await fs.writeFile(options['--output'],JSON.stringify(result.snapshot,null,2)+'\n',
      {encoding:'utf8',flag:'wx',mode:0o600});
    process.stdout.write('RESEARCH_ONLY snapshot written locally; not for Pages\n');
    return 0;
  }catch(error){
    process.stderr.write('STOP: cannot write validated bundle ('+String(error.code||error.name||'Error')+')\n');
    return 2;
  }
}
if(require.main===module)main().then(code=>{process.exitCode=code;})
  .catch(()=>{process.exitCode=2;});
module.exports={buildBundle,inspectBundle,main,codes,ttl};