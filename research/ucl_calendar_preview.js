/* RZOTKIEWKA: isolated, research-only UCL calendar data checks.
   No betting odds, predictions, automatic source approval, storage or model calls.
   Browser global: UclPreview; Node: module.exports (for offline tests).
*/
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.UclPreview = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const SEASON_START = Date.parse('2026-07-01T00:00:00Z');
  const SEASON_END = Date.parse('2027-07-01T00:00:00Z');
  const MAX_RECORDS = 260;
  const ZONED = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;
  const safeText = (value, max) => typeof value === 'string' && value.trim() && value.length <= max && !/[\u0000-\u001f\u007f]/.test(value)
    ? value.trim() : null;
  const positiveId = value => Number.isSafeInteger(value) && value > 0;
  const monthKey = record => record.kickoff.slice(0, 7);

  function parseKickoff(raw) {
    if (typeof raw !== 'string' || !ZONED.test(raw)) return null;
    const year = Number(raw.slice(0, 4));
    const month = Number(raw.slice(5, 7));
    const day = Number(raw.slice(8, 10));
    const check = new Date(Date.UTC(year, month - 1, day));
    if (!Number.isFinite(check.getTime()) || check.toISOString().slice(0, 10) !== raw.slice(0, 10)) return null;
    const timestamp = Date.parse(raw);
    if (!Number.isFinite(timestamp) || timestamp < SEASON_START || timestamp >= SEASON_END) return null;
    const iso = new Date(timestamp).toISOString();
    return { timestamp, iso };
  }

  function finalScorePresent(results) {
    if (!Array.isArray(results)) return false;
    return results.some(row => row && typeof row === 'object' &&
      (row.resultTypeID === 2 || /endergebnis/i.test(String(row.resultName || ''))));
  }

  function inspect(payload, nowInput) {
    const now = Date.parse(nowInput);
    if (!Number.isFinite(now)) return { ok: false, reason: 'Nieprawidłowy czas kontroli', issues: [], upcoming: [], total: 0 };
    if (!Array.isArray(payload) || payload.length === 0 || payload.length > MAX_RECORDS)
      return { ok: false, reason: 'Niepoprawny rozmiar danych źródłowych', issues: [], upcoming: [], total: 0 };

    const problems = [];
    const ids = new Set();
    const pairs = new Set();
    const teamNames = new Map();
    const teamIds = new Map();
    const forthcoming = [];
    let finishedWithScore = 0;

    for (let i = 0; i < payload.length; i++) {
      const raw = payload[i];
      const mark = 'Rekord ' + (i + 1) + ': ';
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
        problems.push(mark + 'błędny format spotkania'); continue;
      }
      const id = raw.matchID;
      const when = parseKickoff(raw.matchDateTimeUTC);
      const home = raw.team1, away = raw.team2;
      if (!positiveId(id) || ids.has(id)) problems.push(mark + 'brak lub powtórzone ID meczu');
      else ids.add(id);
      if (!when) problems.push(mark + 'niepoprawna data lub strefa UTC');
      if (!home || !away || typeof home !== 'object' || typeof away !== 'object') {
        problems.push(mark + 'brak danych drużyn'); continue;
      }
      const homeId = home.teamId, awayId = away.teamId;
      const homeName = safeText(home.teamName, 100), awayName = safeText(away.teamName, 100);
      if (!positiveId(homeId) || !positiveId(awayId) || homeId === awayId || !homeName || !awayName) {
        problems.push(mark + 'niepoprawne drużyny lub identyfikatory'); continue;
      }
      for (const [tid, name] of [[homeId, homeName], [awayId, awayName]]) {
        const canonical = name.normalize('NFKC').toLocaleLowerCase('en-US');
        if (teamNames.has(tid) && teamNames.get(tid) !== canonical)
          problems.push(mark + 'sprzeczne nazwy jednego ID drużyny');
        if (teamIds.has(canonical) && teamIds.get(canonical) !== tid)
          problems.push(mark + 'sprzeczne ID tej samej nazwy drużyny');
        teamNames.set(tid, canonical);
        teamIds.set(canonical, tid);
      }
      if (!when) continue;
      const pair = when.iso + '/' + homeId + '/' + awayId;
      if (pairs.has(pair)) problems.push(mark + 'powtórzony mecz w tym samym terminie');
      pairs.add(pair);
      if (typeof raw.matchIsFinished !== 'boolean') {
        problems.push(mark + 'brak jednoznacznego stanu meczu'); continue;
      }
      const finalPresent = finalScorePresent(raw.matchResults);
      if (when.timestamp > now) {
        if (raw.matchIsFinished || finalPresent) {
          problems.push(mark + 'przyszły mecz ma wynik lub flagę zakończenia');
          continue;
        }
        const phase = raw.group && safeText(raw.group.groupName, 80);
        forthcoming.push({ id, kickoff: when.iso, home: homeName, away: awayName, phase: phase || 'Faza niepotwierdzona' });
      } else {
        if (raw.matchIsFinished && finalPresent) finishedWithScore++;
        if (when.timestamp < now - 48 * 3600000 && (!raw.matchIsFinished || !finalPresent))
          problems.push(mark + 'zaległy wynik powyżej 48 godzin');
      }
    }
    forthcoming.sort((a, b) => a.kickoff.localeCompare(b.kickoff) || a.id - b.id);
    if (problems.length) {
      return { ok: false, reason: 'Niespójność źródła: terminarz zablokowany', issues: problems.slice(0, 8),
        issueCount: problems.length, upcoming: [], total: payload.length };
    }
    if (!forthcoming.length)
      return { ok: false, reason: 'Brak przyszłych spotkań do podglądu', issues: [], upcoming: [], total: payload.length };
    return { ok: true, reason: 'Struktura danych poprawna. Niezależna weryfikacja UEFA nadal wymagana.',
      independentVerification: false, modelApproved: false, productionApproved: false,
      source: 'OpenLigaDB/ucl/2026', total: payload.length, finishedWithScore,
      upcoming: forthcoming, issues: [] };
  }

  function monthOptions(records) {
    return Array.from(new Set(records.map(monthKey))).sort();
  }
  function byMonth(records, month) {
    return month === 'all' ? records.slice() : records.filter(row => monthKey(row) === month);
  }
  return Object.freeze({ inspect, monthOptions, byMonth });
});
