#!/usr/bin/env node
'use strict';
// Research-only identity history for OpenLigaDB UCL 2025/26.
// One public, bounded GET only when explicitly passed "--live".
// NO current-season team-ID approval, production changes, predictions or Premium.
const URL='https://api.openligadb.de/getmatchdata/ucl/2025';
const LIMIT_BYTES=3000000;
const norm=value=>typeof value==='string'
  ? value.normalize('NFKC').trim().toLocaleLowerCase('en-US'):'';
const clean=value=>typeof value==='string'
  ? value.replace(/[\u0000-\u001f\u007f]/g,'').slice(0,100):'';
const safeId=n=>Number.isSafeInteger(n)&&n>0;
const BARCELONA=new Set(['barcelona','fc barcelona']);
const EXCELSIOR='excelsior rotterdam';

function inspectHistoricalIds(rows,observedAt){
  const base={
    kind:'RZOTKIEWKA_UCL_HISTORICAL_TEAM_ID_RESEARCH_ONLY',
    observedAt,source:URL,leagueSeason:2025,
    records:Array.isArray(rows)?rows.length:null,
    status:'STOP',publicationAllowed:false,predictionsAllowed:false,premiumAllowed:false,
    currentSeasonIdentityApproved:false
  };
  if(!Number.isFinite(Date.parse(observedAt))||!Array.isArray(rows)||
    rows.length<1||rows.length>260){
    return {...base,reason:'wrong date, empty data or unsafe array size'};
  }
  const firstId=rows[0]?.leagueId;
  if(!safeId(firstId)||!rows.every(row=>row&&typeof row==='object'&&
    row.leagueId===firstId&&row.leagueShortcut==='ucl'&&row.leagueSeason===2025&&
    safeId(row.matchID)&&row.team1&&row.team2&&
    safeId(row.team1.teamId)&&safeId(row.team2.teamId)&&
    typeof row.team1.teamName==='string'&&typeof row.team2.teamName==='string')){
    return {...base,reason:'invalid league or match/team metadata'};
  }
  const candidates=new Map();
  const namesAt356=new Set();
  for(const row of rows){
    for(const team of [row.team1,row.team2]){
      if(team.teamId===356) namesAt356.add(clean(team.teamName));
      const type=BARCELONA.has(norm(team.teamName))?'barcelona'
        :norm(team.teamName)===EXCELSIOR?'excelsior':null;
      if(!type)continue;
      const key=type+':'+team.teamId;
      if(!candidates.has(key))candidates.set(key,{
        type,teamId:team.teamId,appearances:0,namesSeen:new Set()
      });
      const entry=candidates.get(key);
      entry.appearances++;
      entry.namesSeen.add(clean(team.teamName));
    }
  }
  const list=[...candidates.values()].map(item=>({
    type:item.type,teamId:item.teamId,appearances:item.appearances,
    namesSeen:[...item.namesSeen].sort()
  })).sort((a,b)=>a.type.localeCompare(b.type)||a.teamId-b.teamId);
  const barcelonaMatches=list.filter(x=>x.type==='barcelona')
    .reduce((sum,x)=>sum+x.appearances,0);
  const excelsiorMatches=list.filter(x=>x.type==='excelsior')
    .reduce((sum,x)=>sum+x.appearances,0);
  return {...base,status:'HISTORICAL_READ_ONLY',providerLeagueId:firstId,
    barcelonaMatches,excelsiorMatches,
    historicalNameIds:list,id356NamesSeen:[...namesAt356].sort(),
    independentCurrentSeasonIdVerification:false,
    reason:'These are 2025 provider identities, not UEFA-confirmed 2026 identities'};
}

async function fetchHistorical(fetchFn=globalThis.fetch,timeoutMs=14000){
  if(typeof fetchFn!=='function')throw Error('missing fetch implementation');
  const abort=new AbortController();
  const timer=setTimeout(()=>abort.abort(),timeoutMs);
  try{
    const response=await fetchFn(URL,{
      method:'GET',headers:{accept:'application/json'},
      cache:'no-store',redirect:'error',signal:abort.signal
    });
    if(!response||!response.ok)throw Error('HTTP status '+(response?.status??'unknown'));
    const declared=Number(response.headers?.get('content-length')||0);
    if(!Number.isFinite(declared)||declared>LIMIT_BYTES)throw Error('declared size exceeded');
    let body='';
    if(response.body&&typeof response.body.getReader==='function'){
      const reader=response.body.getReader(),chunks=[];
      let length=0;
      while(true){
        const {done,value}=await reader.read();
        if(done)break;
        length+=value.byteLength;
        if(length>LIMIT_BYTES){
          await reader.cancel();
          throw Error('body size exceeded');
        }
        chunks.push(Buffer.from(value));
      }
      body=Buffer.concat(chunks).toString('utf8');
    }else{
      body=await response.text();
      if(Buffer.byteLength(body,'utf8')>LIMIT_BYTES)throw Error('body size exceeded');
    }
    return JSON.parse(body);
  }finally{clearTimeout(timer);}
}

async function main(args=process.argv.slice(2)){
  if(args.length!==1||args[0]!=='--live'){
    process.stderr.write('STOP: explicit --live required for one historical public read\n');
    return 2;
  }
  try{
    const rows=await fetchHistorical();
    const report=inspectHistoricalIds(rows,new Date().toISOString());
    process.stdout.write(JSON.stringify(report,null,2)+'\n');
    return report.status==='HISTORICAL_READ_ONLY'?0:1;
  }catch(e){
    process.stderr.write('STOP: historical source unavailable ('+String(e?.name||'Error')+')\n');
    return 2;
  }
}
if(require.main===module)main().then(code=>{process.exitCode=code;}).catch(()=>{process.exitCode=2;});
module.exports={URL,inspectHistoricalIds,fetchHistorical,main};
