// Run actual archive loader, integrity checks and digest code from index.html.
// Fully offline: no external network or data mutations.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import {TextEncoder} from 'node:util';

const root = new URL('../', import.meta.url);
const source = readFileSync(new URL('index.html',root),'utf8');
const original = JSON.parse(readFileSync(new URL('predictions.json',root),'utf8'));
const start = source.indexOf('  function canonicalJson(value){');
const end = source.indexOf('  function renderCard(m) {',start);
assert.ok(start>=0 && end>start, 'Archive loader boundaries unexpectedly changed');
const code = source.slice(start,end);

async function loadFrom(payload, failedNetwork=false) {
  const dom = new Map();
  const state = {archive:[],archiveReady:false,archiveFailed:false,archiveAt:null};
  const $ = id => {
    if (!dom.has(id)) dom.set(id,{disabled:false,textContent:''});
    return dom.get(id);
  };
  let rendered=0;
  const context={
    crypto:webcrypto,TextEncoder,
    fetch:async()=>failedNetwork?{ok:false,status:503}:{ok:true,json:async()=>payload},
    $, state,
    pickOutcome:score=>score[0]>score[1]?'1':score[0]<score[1]?'2':'X',
    console:{warn:()=>{}},
    render:()=>{rendered++;$('rank-export-csv').disabled=!state.archiveReady||state.archiveFailed;},
  };
  const load=vm.runInNewContext(code+'\nloadArchive;',context,{timeout:5000});
  await load();
  return {state,dom,rendered};
}

test('all 9 valid original predictions load, including errors and defeats',async()=>{
  const {state,dom,rendered}=await loadFrom(original);
  assert.equal(state.archiveReady,true);
  assert.equal(state.archiveFailed,false);
  assert.equal(state.archive.length,original.forecasts.length);
  assert.equal(dom.get('rank-export-csv').disabled,false);
  assert.equal(rendered,1);
});

test('a tampered snapshot blocks the entire archive and exports',async()=>{
  const bad=structuredClone(original);
  bad.forecasts[0].snapshot.probabilities['1']=0.999;
  const {state,dom}=await loadFrom(bad);
  assert.equal(state.archiveReady,false);
  assert.equal(state.archiveFailed,true);
  assert.equal(state.archive.length,0);
  assert.equal(dom.get('rank-export-csv').disabled,true);
  assert.match(dom.get('archive-status').textContent,/Nie pokazujemy częściowej próbki/);
});

test('duplicate ID cannot artificially inflate result counts',async()=>{
  const bad=structuredClone(original);
  bad.forecasts.push(structuredClone(bad.forecasts[0]));
  const {state,dom}=await loadFrom(bad);
  assert.equal(state.archiveReady,false);
  assert.equal(state.archive.length,0);
  assert.equal(dom.get('rank-export-csv').disabled,true);
});

test('a missing record ID blocks all performance statistics',async()=>{
  const bad=structuredClone(original);
  delete bad.forecasts[0].id;
  const {state}=await loadFrom(bad);
  assert.equal(state.archiveReady,false);
  assert.equal(state.archiveFailed,true);
  assert.equal(state.archive.length,0);
});

test('unavailable archive cannot reuse an old valid sample',async()=>{
  const {state}=await loadFrom(original,true);
  assert.equal(state.archiveReady,false);
  assert.equal(state.archiveFailed,true);
  assert.equal(state.archiveAt,null);
  assert.equal(state.archive.length,0);
});
