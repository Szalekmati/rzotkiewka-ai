// Verify the real helper extracted from index.html, not a duplicated implementation.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const begin = html.indexOf('  function labSnapshotAge(status,now=Date.now()){');
const end = html.indexOf('  async function loadLabAutomation(signal){', begin);
assert.ok(begin >= 0 && end > begin, 'The published snapshot helper must exist');
const labSnapshotAge = vm.runInNewContext(
  html.slice(begin, end) + '\nlabSnapshotAge;',
  {Date}, {timeout: 5000}
);
const observed_at = '2026-11-15T09:51:00+00:00';
const saved = {schema: 1, observed_at};
const stamp = Date.parse(observed_at);

test('recent published observation is not labeled stale', () => {
  const x = labSnapshotAge(saved, stamp + 2*60*60*1000);
  assert.equal(x.at, stamp);
  assert.equal(x.isOld, false);
});
test('older published observation is labeled stale, without assuming failure', () => {
  const x = labSnapshotAge(saved, stamp + 4*60*60*1000);
  assert.equal(x.isOld, true);
  assert.equal(x.ageHours, 4);
});
test('timezone, schema, invalid dates, and clock skew fail closed', () => {
  assert.throws(() => labSnapshotAge({...saved, schema: 2}, stamp));
  assert.throws(() => labSnapshotAge({...saved, observed_at:'2026-11-15T09:51:00'}, stamp));
  assert.throws(() => labSnapshotAge({...saved, observed_at:'not a date UTC'}, stamp));
  assert.throws(() => labSnapshotAge(saved, stamp - 10*60*1000));
});
test('a small future clock skew does not imply that the experiment ran early', () => {
  const x = labSnapshotAge(saved, stamp - 2*60*1000);
  assert.equal(x.isOld, false);
  assert.equal(x.ageHours, 0);
});
