#!/usr/bin/env node
'use strict';
// One-off, research-only public OpenLigaDB identity investigation.
// No API keys, writes, model input, browser usage, production changes or network on import.
const fs = require('node:fs/promises');
const {fetchLive, LIMIT_BYTES} = require('./ucl_verify_snapshot.cjs');
const {sourceIdentityValid} = require('./ucl_calendar_preview.js');

const TARGETS = ['Excelsior Rotterdam','Barcelona','FC Barcelona'];
const SOURCE = 'https://api.openligadb.de/getmatchdata/ucl/2026';
const norm = value => typeof value === 'string'
  ? value.normalize('NFKC').trim().toLocaleLowerCase('en-US') : '';
const clean = value => typeof value === 'string'
  ? value.replace(/[\u0000-\u001f\u007f]/g,'').slice(0,100) : '';
const positiveId = value => Number.isSafeInteger(value) && value>0;

function inspectTeamIdentity(rows, observedAt) {
  const stamp=Date.parse(observedAt);
  const empty={
    kind:'RZOTKIEWKA_UCL_IDENTITY_PROBE', observedAt,
    source:SOURCE, records:Array.isArray(rows)?rows.length:null,
    status:'STOP', publicationAllowed:false, predictionsAllowed:false,
    premiumAllowed:false
  };
  if (!Number.isFinite(stamp) || !sourceIdentityValid(rows) ||
    rows.length>260 || !rows.every(row => positiveId(row.matchID) &&
      row.team1 && row.team2 && positiveId(row.team1.teamId) &&
      positiveId(row.team2.teamId) && typeof row.team1.teamName==='string' &&
      typeof row.team2.teamName==='string' &&
      typeof row.matchDateTimeUTC==='string' &&
      Number.isFinite(Date.parse(row.matchDateTimeUTC))))
    return {...empty, reason:'invalid clock, source identity or match/team metadata'};

  const memberships = new Map();
  const detected=[];
  const ids = new Set();
  for(const row of rows) {
    for(const side of ['team1','team2']){
      const team=row[side];
      if(!memberships.has(team.teamId)) memberships.set(team.teamId,new Set());
      memberships.get(team.teamId).add(clean(team.teamName));
      if(TARGETS.some(name=>norm(team.teamName)===norm(name))){
        detected.push({
          matchId:row.matchID,kickoffUtc:new Date(row.matchDateTimeUTC).toISOString(),
          side,teamId:team.teamId,teamName:clean(team.teamName),
          opponentId:row[side==='team1'?'team2':'team1'].teamId,
          opponentName:clean(row[side==='team1'?'team2':'team1'].teamName)
        });
        ids.add(team.teamId);
      }
    }
  }
  detected.sort((a,b)=>a.kickoffUtc.localeCompare(b.kickoffUtc) || a.matchId-b.matchId);
  const relevantIds=[...ids].sort((a,b)=>a-b).map(teamId=>({
    teamId,namesSeen:[...memberships.get(teamId)].sort()
  }));
  const excelsior=detected.filter(row=>norm(row.teamName)===norm('Excelsior Rotterdam'));
  const barcelona=detected.filter(row=>norm(row.teamName)!==norm('Excelsior Rotterdam'));
  return {...empty,
    status:excelsior.length?'STOP_FOREIGN_CLUB_LABEL':'NEEDS_INDEPENDENT_VERIFICATION',
    reason:excelsior.length
      ? 'Excelsior appears in UCL; do not alias it to Barcelona'
      : 'Team IDs and official registration are not independently verified',
    records:rows.length,excelsiorMatches:excelsior.length,barcelonaMatches:barcelona.length,
    suspectRecords:detected.slice(0,30),targetTeamIds:relevantIds,
    independentlyVerifiedTeamIds:false
  };
}

async function main(args=process.argv.slice(2)) {
  const live=args.length===1&&args[0]==='--live';
  const file=args.length===2&&args[0]==='--file'&&args[1];
  if(!live&&!file){
    process.stderr.write('STOP: explicitly supply --live or --file existing.json\n');
    return 2;
  }
  try{
    let rows;
    if(live) rows=await fetchLive();
    else {
      const stat=await fs.stat(args[1]);
      if(!stat.isFile()||stat.size<=0||stat.size>LIMIT_BYTES)
        throw new Error('input file exceeds bound or is not a file');
      rows=JSON.parse(await fs.readFile(args[1],'utf8'));
    }
    const report=inspectTeamIdentity(rows,new Date().toISOString());
    process.stdout.write(JSON.stringify(report,null,2)+'\n');
    return report.status==='NEEDS_INDEPENDENT_VERIFICATION'?0:1;
  }catch(error){
    process.stderr.write('STOP: data source unavailable ('+String(error && error.name || 'Error')+')\n');
    return 2;
  }
}

if(require.main===module) main().then(code=>{process.exitCode=code;}).catch(()=>{process.exitCode=2;});
module.exports={inspectTeamIdentity,main,SOURCE};
