#!/usr/bin/env node
'use strict';
// One-off German fixtures audit: requires explicit --live.
// No API credentials, scheduled reads, local writes, Pages or model changes.
const {buildBundle,codes}=require('./german_fixture_bundle.cjs');
const YEAR=2026;
const MAX_BYTES=8_000_000;
const MAX_RECORDS=500;
const DELAY_MS=1250;
const TIMEOUT_MS=14000;
const BASE='https://api.openligadb.de/getmatchdata/';
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function urlFor(code){
  if(!codes.includes(code))throw Error('unsupported competition');
  return BASE+code+'/'+YEAR;
}
async function readBounded(response){
  const hdr=response.headers&&response.headers.get('content-length');
  const declared=hdr===null||hdr===undefined?null:Number(hdr);
  if(declared!==null&&(!Number.isSafeInteger(declared)||declared<0||declared>MAX_BYTES))
    throw Error('declared source size is not acceptable');
  let text;
  if(response.body&&typeof response.body.getReader==='function'){
    const reader=response.body.getReader(),parts=[];
    let bytes=0;
    while(true){
      const item=await reader.read();
      if(item.done)break;
      bytes+=item.value.byteLength;
      if(bytes>MAX_BYTES){
        await reader.cancel();
        throw Error('source exceeded size limit');
      }
      parts.push(Buffer.from(item.value));
    }
    text=Buffer.concat(parts).toString('utf8');
  }else{
    text=await response.text();
    if(Buffer.byteLength(text,'utf8')>MAX_BYTES)throw Error('source exceeded size limit');
  }
  const rows=JSON.parse(text);
  if(!Array.isArray(rows)||rows.length===0||rows.length>MAX_RECORDS)
    throw Error('unexpected number/format of fixtures');
  return rows;
}
async function fetchThree(fetchFn=globalThis.fetch,pause=wait,timeoutMs=TIMEOUT_MS){
  if(typeof fetchFn!=='function')throw Error('fetch unavailable');
  const all={};
  for(const [i,code] of codes.entries()){
    if(i>0)await pause(DELAY_MS);
    const control=new AbortController();
    const timer=setTimeout(()=>control.abort(),timeoutMs);
    try{
      const response=await fetchFn(urlFor(code),{
        method:'GET',
        headers:{accept:'application/json'},
        cache:'no-store',
        redirect:'error',
        signal:control.signal
      });
      if(!response||!response.ok)throw Error('OpenLigaDB returned HTTP '+(response&&response.status));
      all[code]=await readBounded(response);
    }finally{clearTimeout(timer)}
  }
  return all;
}
function makeAudit(rows,observedAt){
  const r=buildBundle(rows,observedAt);
  const counts=Object.fromEntries(codes.map(c=>[c,Array.isArray(rows&&rows[c])?rows[c].length:null]));
  if(!r.ok)return {
    status:'STOP',reason:r.reason,observed_at_utc:observedAt,
    source:'OpenLigaDB',records_per_league:counts,
    production_release_allowed:false,predictions_allowed:false,premium_allowed:false
  };
  return {
    status:'RESEARCH_ONLY_NO_RELEASE',
    observed_at_utc:r.snapshot.observed_at_utc,
    source:'OpenLigaDB',
    source_license:'ODbL-1.0',
    records_per_league:counts,
    upcoming_per_league:Object.fromEntries(codes.map(c=>[c,r.snapshot.leagues[c].upcoming_count])),
    source_identity_checked:true,
    independently_verified_against_official_source:false,
    production_release_allowed:false,
    predictions_allowed:false,
    premium_allowed:false
  };
}
async function main(args=process.argv.slice(2),deps={}){
  if(args.length===1&&args[0]==='--help'){
    process.stdout.write('One-off read-only audit: node research/german_live_probe.cjs --live\n');
    return 0;
  }
  if(args.length!==1||args[0]!=='--live'){
    process.stderr.write('STOP: real API read requires explicit --live; no automatic requests\n');
    return 2;
  }
  try{
    const rows=await fetchThree(deps.fetchFn, deps.pause, deps.timeoutMs||TIMEOUT_MS);
    const report=makeAudit(rows,deps.observedAt||new Date().toISOString());
    process.stdout.write(JSON.stringify(report,null,2)+'\n');
    return report.status==='RESEARCH_ONLY_NO_RELEASE'?0:1;
  }catch(error){
    process.stderr.write('STOP: OpenLigaDB not verified ('+
      String(error&&error.name||'Error')+'); no data saved\n');
    return 2;
  }
}
if(require.main===module)main().then(code=>{process.exitCode=code;})
  .catch(()=>{process.exitCode=2;});
module.exports={fetchThree,makeAudit,main,urlFor,DELAY_MS,MAX_BYTES};
