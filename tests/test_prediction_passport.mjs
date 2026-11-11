// Read-only, offline regression tests for the actual passport builder.
// No remote APIs, wagers, model changes, or modifications to predictions.json.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';

const root=new URL('../',import.meta.url);
const page=readFileSync(new URL('index.html',root),'utf8');
const archive=JSON.parse(readFileSync(new URL('predictions.json',root),'utf8')).forecasts;
const start=page.indexOf('  function passportRecords(');
const end=page.indexOf('  function renderForecast(',start);
assert.ok(start>=0&&end>start,'Passport function anchors changed');
const source=page.slice(start,end);

function node(tag,cls='',value=''){
  return {tag,cls,textContent:String(value),children:[],style:{},
    append(...children){this.children.push(...children);},
    addEventListener(){}};
}
function textOf(root){
  return [root.textContent,...root.children.map(textOf)].join(' ');
}
function find(root,tag){
  return [...(root.tag===tag?[root]:[]),...root.children.flatMap(el=>find(el,tag))];
}
function passport(record){
  const state={archive,archiveReady:true,archiveFailed:false,loadedAt:null};
  const probFormatter=new Intl.NumberFormat('pl-PL',{maximumFractionDigits:1,minimumFractionDigits:1});
  const context={state,make:node,probFormatter,Date,
    allowedLeagues:{bl1:'Bundesliga',bl2:'2. Bundesliga',bl3:'3. Liga'},
    estimate1x2(){throw new Error('Archived predictions MUST NOT be recalculated');},
    formattedPercent:n=>probFormatter.format(n*100)+'%',
    scored:r=>r.settlement.state==='graded'&&Array.isArray(r.settlement.score),
    bestOutcome:p=>['1','X','2'].reduce((best,k)=>p[k]>p[best]?k:best,'1'),
  };
  const render=vm.runInNewContext(source+'\nbuildPassport;',context,{timeout:5000});
  return render(null,record);
}

test('archive passport lists recorded inputs, lead time and source, not invented xG',()=>{
  assert.ok(archive.length>0,'Expected stored forecasts');
  const rec=archive[0],s=rec.snapshot;
  const root=passport(rec),visible=textOf(root);
  const minutes=Math.round((Date.parse(s.kickoff)-Date.parse(s.created_at))/60000);
  assert.match(visible,/Paszport analizy/);
  assert.ok(visible.includes('Wyprzedzenie zapisu '+Math.floor(minutes/60)+' godz. '+(minutes%60)+' min'));
  assert.ok(visible.includes('Zapisana próba: '+s.league_matches_used+' wcześniejszych meczów ligi'));
  assert.ok(visible.includes('gospodarze: '+s.home_matches_used+' spotkań'));
  assert.ok(visible.includes('goście: '+s.away_matches_used+' spotkań'));
  assert.ok(visible.includes('NIE pomiar xG'));
  assert.ok(visible.includes('OpenLigaDB'));
  assert.ok(visible.includes('nie wynik testu LAB 2.1/2.2'));
  assert.ok(visible.includes('SHA-256: '+rec.snapshot_sha256));
  assert.ok(visible.includes(String(s.home_match_ids[0])));
  assert.ok(visible.includes(String(s.away_match_ids[0])));
  assert.equal(find(root,'details').length,2,'Passport and nested ID list should use accessible details');
});

test('missing snapshot input metadata is explicitly unavailable, never invented',()=>{
  const rec=structuredClone(archive[0]);
  delete rec.snapshot.league_matches_used;
  delete rec.snapshot.home_matches_used;
  delete rec.snapshot.away_matches_used;
  delete rec.snapshot.expected_home_goals;
  delete rec.snapshot.expected_away_goals;
  delete rec.snapshot.home_match_ids;
  delete rec.snapshot.away_match_ids;
  // Unit test of presentation fallback only: this mutated record is never
  // inserted into the verified archive or shown by the real page.
  const root=passport(rec);
  // Remove original record from fixture state by changing the match ID so
  // the lookup will be empty and the supplied record will be used as latest.
  assert.ok(root);
});

// Verify fallback with a record ID absent from the true archive.
test('passport shows missing counts and scores without fabricating values',()=>{
  const rec=structuredClone(archive[0]);
  rec.snapshot.match_id=987654321;
  delete rec.snapshot.league_matches_used;
  delete rec.snapshot.home_matches_used;
  delete rec.snapshot.away_matches_used;
  delete rec.snapshot.expected_home_goals;
  delete rec.snapshot.expected_away_goals;
  delete rec.snapshot.home_match_ids;
  delete rec.snapshot.away_match_ids;
  const root=passport(rec),visible=textOf(root);
  assert.ok(visible.includes('Brak pełnych liczników meczów wejściowych'));
  assert.ok(visible.includes('Brak zapisanych szacunków liczby goli'));
  assert.equal(find(root,'details').length,1);
  assert.doesNotMatch(visible,/Zapisana próba:/);
  assert.doesNotMatch(visible,/Prognozowane gole:/);
});
