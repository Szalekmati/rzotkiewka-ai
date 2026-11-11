// Honest daily free-analysis tests; production selection reads ONLY the SHA-verified archive.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';

const root=new URL('../',import.meta.url);
const source=readFileSync(new URL('index.html',root),'utf8');
const stored=JSON.parse(readFileSync(new URL('predictions.json',root),'utf8')).forecasts;
const begin=source.indexOf('  function warsawDay(');
const end=source.indexOf('  function renderRanking()',begin);
assert.ok(begin>0&&end>begin,'Daily forecast function boundaries changed');
const code=source.slice(begin,end);
const at=Date.parse('2026-11-11T00:10:00Z'); // 01:10 Warsaw, local day 11 Nov

function match(id,kickoff,{created='2026-11-10T18:00:00Z',status='pending',confidence=.4}={}){
  return {id,snapshot:{league:'bl1',season:2026,home:'Dom',away:id,
    created_at:created,kickoff,model_version:'1.3.0',
    probabilities:{'1':confidence,X:.25,'2':.75-confidence}},
    settlement:{state:status},snapshot_sha256:'a'.repeat(64)};
}
function el(tag,cls='',text=''){
  return {tag,cls,textContent:String(text),children:[],href:'',
    append(...items){this.children.push(...items)},
    replaceChildren(...items){this.children=items}};
}
function contentOf(elm){return [elm.textContent,...elm.children.map(contentOf)].join(' ')}
function harness({records=[],ready=true,failed=false}={}){
  const root=el('section');
  const state={archive:records,archiveReady:ready,archiveFailed:failed};
  const context={Date,Intl,Object,URL,location:{pathname:'/rzotkiewka-ai/',origin:'https://example.test'},
    state, make:el,$:id=>{assert.equal(id,'free-daily-forecast');return root},
    allowedLeagues:{bl1:'Bundesliga'},
    passportDate:x=>new Date(x).toISOString(),
    formattedPercent:n=>Math.round(n*100)+'%'};
  const result=vm.runInNewContext(code+'\n({warsawDay,pickTodayForecast,renderDailyForecast});',context,{timeout:5000});
  return {...result,root,records};
}

test('daily selection uses Warsaw day and excludes next-day UTC rollover',()=>{
  const candidate=match('today','2026-11-10T23:30:00Z'); // 00:30 Warsaw Nov 11
  const tomorrow=match('tomorrow','2026-11-11T23:30:00Z'); // 00:30 Nov 12 Warsaw
  const t=harness({records:[tomorrow,candidate]});
  assert.equal(t.warsawDay(at),'2026-11-11');
  assert.equal(t.warsawDay(candidate.snapshot.kickoff),'2026-11-11');
  assert.equal(t.warsawDay(tomorrow.snapshot.kickoff),'2026-11-12');
  assert.equal(t.pickTodayForecast(t.records,at)?.id,'today');
});

test('earliest upcoming verified snapshot wins, never the most confident',()=>{
  const high=match('later','2026-11-11T17:00:00Z',{confidence:.7});
  const low=match('earlier','2026-11-11T10:00:00Z',{confidence:.35});
  const graded=match('old-winner','2026-11-11T07:00:00Z',{status:'graded',confidence:.74});
  const futureSaved=match('future-saved','2026-11-11T06:00:00Z',{created:'2026-11-11T02:00:00Z'});
  const expired=match('expired','2026-11-10T22:30:00Z',{status:'graded'});
  const t=harness({records:[high,graded,low,futureSaved,expired]});
  assert.equal(t.pickTodayForecast(t.records,at)?.id,'earlier');
  t.renderDailyForecast(at);
  const content=contentOf(t.root);
  assert.ok(content.includes('Dom – earlier'));
  assert.ok(content.includes('1 35%'));
  assert.ok(content.includes('wyłącznie według najbliższej godziny meczu'));
  assert.doesNotMatch(content,/old-winner|Dom – later/);
  const links=t.root.children.filter(e=>e.tag==='a');
  assert.equal(links.length,1);
  assert.equal(new URL(links[0].href).searchParams.get('forecast'),'earlier');
  assert.equal(new URL(links[0].href).hash,'#ranking');
});

test('tie at kickoff sorts by immutable record ID',()=>{
  const t=harness({records:[match('zzz','2026-11-11T10:00:00Z'),match('aaa','2026-11-11T10:00:00Z')]});
  assert.equal(t.pickTodayForecast(t.records,at).id,'aaa');
});

test('existing archive has no new free prediction for 11 Nov, no fake demo',()=>{
  const t=harness({records:stored});
  assert.equal(t.pickTodayForecast(t.records,Date.parse('2026-11-11T12:30:00Z')),null);
  t.renderDailyForecast(Date.parse('2026-11-11T12:30:00Z'));
  const content=contentOf(t.root);
  assert.match(content,/Brak nowej, zapisanej prognozy na dziś/);
  assert.match(content,/Nie podstawiamy dawnych trafień ani prognoz DEMO/);
  assert.doesNotMatch(content,/\d+%/);
  assert.ok(t.root.children.some(e=>e.tag==='a'&&e.href==='./predictions.json'));
});

test('unverified, failed, or empty archive never yields a daily free tip',()=>{
  const future=match('untrusted','2026-11-11T13:00:00Z');
  for(const [ready,failed,phrase] of [[false,false,'Trwa weryfikacja'],[false,true,'Nie udało się zweryfikować'],[true,false,'Brak nowej']]){
    const t=harness({records:[future],ready,failed});
    if(ready&&!failed)t.records.length=0;
    t.renderDailyForecast(at);
    assert.match(contentOf(t.root),new RegExp(phrase));
    assert.ok(!t.root.children.some(e=>e.tag==='a'&&e.href.includes('forecast=')));
  }
});

test('no presentation of graded, already-started or future-recorded predictions',()=>{
  const rows=[
    match('graded','2026-11-11T10:00:00Z',{status:'graded'}),
    match('already-started','2026-11-10T23:05:00Z'),
    match('invalid-snapshot','2026-11-11T11:00:00Z',{created:'2026-11-11T12:00:00Z'}),
  ];
  const t=harness({records:rows});
  assert.equal(t.pickTodayForecast(rows,at),null);
});
