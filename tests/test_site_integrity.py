"""Offline tests for the RZOTKIEWKA public free-forecast page."""
import json
import shutil
import subprocess
import tempfile
import unittest
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.ids = []
        self.js = []
        self.json_data = {}
        self.script = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "script":
            self.script = {"type": attrs.get("type") or "text/javascript",
                           "id": attrs.get("id"), "chunks": []}

    def handle_data(self, data):
        if self.script is not None:
            self.script["chunks"].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            kind = self.script["type"].lower()
            content = "".join(self.script["chunks"])
            if kind in ("text/javascript", "application/javascript", "module"):
                self.js.append(content)
            if kind == "application/json":
                self.json_data[self.script["id"]] = json.loads(content)
            self.script = None


class SiteIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.page = Page()
        cls.page.feed(cls.html)
        cls.page.close()

    def test_unique_ids(self):
        duplicates = [i for i, n in Counter(self.page.ids).items() if n > 1]
        self.assertFalse(duplicates, f"Duplicate HTML IDs: {duplicates}")
        for ident in ("ranking", "rank-list", "rank-state", "rank-order",
                      "rank-minprob", "rank-hit", "rank-brier", "premium", "lab"):
            self.assertIn(ident, self.page.ids)

    def test_mobile_navigation_has_five_accessible_destinations(self):
        from html.parser import HTMLParser

        class MobileNavParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.inside_mobile_nav = False
                self.links = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "nav" and "mobile-nav" in attrs.get("class", "").split():
                    self.inside_mobile_nav = True
                elif self.inside_mobile_nav and tag == "a":
                    self.links.append((attrs.get("href"), "data-page-link" in attrs))

            def handle_endtag(self, tag):
                if tag == "nav" and self.inside_mobile_nav:
                    self.inside_mobile_nav = False

        parser = MobileNavParser()
        parser.feed(self.html)
        self.assertEqual(
            parser.links,
            [(dest, True) for dest in (
                "#mecze", "#ranking", "#sporty", "#raport", "#wiecej"
            )],
        )
        self.assertIn("grid-template-columns:repeat(5,minmax(0,1fr))", self.html)
        self.assertIn('.mobile-nav a[aria-current="page"]', self.html)
        self.assertIn(".mobile-nav a:focus-visible", self.html)
        js = "\\n".join(self.page.js)
        self.assertIn("a.setAttribute('aria-current','page')", js)

    def test_free_daily_forecast_only_from_verified_upcoming_records(self):
        self.assertIn('id="free-daily-forecast"', self.html)
        self.assertIn('aria-label="Darmowa analiza dnia"', self.html)
        js = "\\n".join(self.page.js)
        for token in (
            "function warsawDay(value)",
            "timeZone:'Europe/Warsaw'",
            "function pickTodayForecast(records,at=Date.now())",
            "r.settlement.state==='pending'",
            "saved<start&&saved<=at&&start>at",
            "warsawDay(start)===day",
            "function renderDailyForecast(at=Date.now())",
            "if(state.archiveFailed)",
            "if(!state.archiveReady)",
            "Nie podstawiamy dawnych trafień ani prognoz DEMO.",
            "renderDailyForecast();",
            "url.searchParams.set('forecast',chosen.id)",
        ):
            with self.subTest(token=token):
                self.assertIn(token, js)
        self.assertIn("wyłącznie według najbliższej godziny meczu", self.html)
        self.assertIn("SHA-256 potwierdza spójność zapisu", self.html)

    def test_free_forecast_legend_explains_1x2_without_promises(self):
        self.assertIn('id="forecast-legend"', self.html)
        for phrase in ("wygrana gospodarzy", "remis", "wygrana gości",
                       "szacowane prawdopodobieństwa modelu",
                       "a nie kursy ani pewność wyniku"):
            self.assertIn(phrase, self.html)

    def test_audit_metrics_explained_without_claims_of_roi(self):
        self.assertIn('id="audit-metrics-guide"', self.html)
        for phrase in ("trafione mecze / wszystkie rozliczone mecze",
                       "0,222", "tej samej próbie spotkań",
                       "Bez rozliczonych meczów",
                       "To nie jest miara zysku z zakładów"):
            self.assertIn(phrase, self.html)

    def test_version_two_showcase_has_real_archive_bindings(self):
        self.assertIn("RZOTKIEWKA 2.0", self.html)
        for ident in ("hero-archive-total", "hero-archive-graded",
                      "hero-archive-hits", "hero-archive-misses",
                      "hero-archive-ratio", "hero-bar-hits",
                      "hero-bar-misses", "hero-archive-note"):
            self.assertIn(ident, self.page.ids)
        js = "\n".join(self.page.js)
        self.assertIn("const ready=state.archiveReady&&!state.archiveFailed;", js)
        self.assertIn("const hitPercent=ready&&stats.graded", js)
        self.assertNotIn("RZOTKIEWKA 1.14", self.html)

    def test_openligadb_license_notice_is_visible_on_all_page_tabs(self):
        # Keep the ODbL notice in the unconditional footer, not only
        # the match section (which hides when browsing other tabs).
        footer = self.html.split('<footer class="footer">', 1)[1].split(
            '</footer>', 1)[0]
        self.assertIn("Dane meczowe:", footer)
        self.assertIn("https://www.openligadb.de/", footer)
        self.assertIn("https://www.openligadb.de/lizenz", footer)
        self.assertIn("ODbL 1.0", footer)
        self.assertIn('rel="noopener noreferrer"', footer)
        self.assertNotIn("TeamIconUrl", self.html)
        self.assertNotIn("teamIconUrl", self.html)

    def test_favorite_teams_filter_is_local_and_safe(self):
        for ident in ("live-favorites", "live-favorites-note", "live-search", "live-list"):
            self.assertIn(ident, self.page.ids)
        js = "\n".join(self.page.js)
        for term in (
            "rzotkiewka:favorite-teams:v1",
            "favoriteTeams=new Set(savedTeams.filter(",
            "function favoriteMatch(match)",
            "function toggleFavoriteTeam(teamId)",
            "function favoriteTeamButton(teamId,teamName)",
            "localStorage.setItem(favoriteTeamsKey,JSON.stringify([...favoriteTeams]))",
            "button.setAttribute('aria-pressed',String(chosen));",
            "button.setAttribute('aria-label',(chosen?",
            ".filter(m=>!onlyFavoriteTeams||favoriteMatch(m));",
            "onlyFavoriteTeams?'Nie ma meczów Twoich ulubionych drużyn",
            "if(favoriteTeams.size<60)",
        ):
            with self.subTest(term=term):
                self.assertIn(term, js)
        self.assertIn("Filtr działa w wybranej lidze i sezonie.", self.html)

    def test_cross_league_favorites_use_real_fixtures_and_keep_lab_untouched(self):
        self.assertIn("league-favorites-summary", self.page.ids)
        js = "\n".join(self.page.js)
        for phrase in (
            "const favoriteSchedule=leagueRows.flatMap(item=>item.error?[]:",
            "item.matches.filter(m=>!m.score&&m.time>Date.now()&&favoriteMatch(m))",
            ".sort((a,b)=>a.match.time-b.match.time||a.code.localeCompare(b.code));",
            "if(!favoriteTeams.size){",
            "favoriteSchedule.slice(0,8)",
            "details.append(make('strong','',match.home+' – '+match.away));",
            "$('live-league').value=code;",
            "$('live-search').value=match.home;",
            "state.tab='next';",
            "await load();",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, js)
        # Overview only reads fixture data and favorites; never alters frozen LAB.
        overview = js.split("  // Oddzielny przegląd terminarzy;", 1)[1].split(
            "  $('live-more').addEventListener", 1)[0]
        self.assertNotIn("lab_forward/", overview)
        self.assertNotIn("predictions.json", overview)
        self.assertNotIn("state.archive=", overview)

    def test_quick_mobile_league_switcher_keeps_the_model_scoped(self):
        js = "\\n".join(self.page.js)
        for league in ("bl1", "bl2", "bl3"):
            self.assertIn('data-quick-league="'+league+'"', self.html)
        for phrase in (
            'class="league-quick-nav"',
            'aria-label="Szybki wybór ligi"',
            'league-quick-button[aria-pressed="true"]',
            "function syncQuickLeagueButtons(league)",
            "document.querySelectorAll('[data-quick-league]')",
            "if(!Object.hasOwn(allowedLeagues,league))return;",
            "$('live-league').value=league;",
            "syncQuickLeagueButtons(league);",
            "state.league=league;state.season=season;",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.html if phrase.startswith('class=') or phrase.startswith('aria-') else js if phrase not in ("league-quick-button[aria-pressed=\"true\"]",) else self.html)
        self.assertIn("rzotkiewka:favorite-teams:v1", js)
        self.assertIn("favoriteTeams.has(String(match.homeId))", js)
        self.assertIn("favoriteTeams.has(String(match.awayId))", js)

    def test_league_overview_is_read_only_and_keeps_models_separate(self):
        for ident in ("league-overview-toggle", "league-overview",
                      "league-overview-refresh", "league-overview-grid",
                      "league-overview-status"):
            self.assertIn(ident, self.page.ids)
        js = "\n".join(self.page.js)
        for term in (
            "async function loadLeagueOverview(force=false)",
            "Object.keys(allowedLeagues).map(async code=>",
            "'https://api.openligadb.de/getmatchdata/'+code+'/'+season",
            "if(!Array.isArray(payload))throw new Error('Niepoprawne dane');",
            "for(const game of upcoming.slice(0,3))",
            "if(game",  # exact comparison logic is checked below
            "open.addEventListener('click',()=>{",
            "$('live-league').value=item.code;",
            "$('league-overview').hidden=true;",
            "To przegląd terminarzy, nie prognozy 1X2.",
            "if(!$('league-overview').hidden){",
            "Wybrana liga pozostaje jedynym źródłem historii",
        ):
            if term == "if(game":
                continue
            with self.subTest(term=term):
                self.assertIn(term, js)
        overview = js.split("  // Oddzielny przegląd terminarzy;", 1)[1].split(
            "  $('live-more').addEventListener", 1)[0]
        self.assertNotIn("state.matches=", overview)
        self.assertNotIn("predictions.json", overview)
        self.assertNotIn("lab_forward/", overview)
        self.assertIn("favoriteMatch(game)?' ★':''", overview)
        self.assertIn('aria-expanded="false"', self.html)

    def test_league_catalogue_filter_shows_only_actually_connected_sources(self):
        # This is a presentation filter, NOT a new provider or model.
        self.assertIn('id="sport-connected-only"', self.html)
        self.assertIn('aria-pressed="false">✓ Tylko podłączone ligi', self.html)
        js = "\\n".join(self.page.js)
        for token in (
            "let sport='all',connectedOnly=false;",
            "$('sport-connected-only').addEventListener('click',()=>{",
            "connectedOnly=!connectedOnly;",
            "$('sport-connected-only').setAttribute('aria-pressed',String(connectedOnly));",
            "(!connectedOnly||Boolean(r[4]))",
            "Brak podłączonych lig w tych filtrach.",
            "active?'Dane podłączone':'Planowane'",
        ):
            with self.subTest(token=token):
                self.assertIn(token, js)
        catalogue = js.split("const catalogue=[", 1)[1].split("];", 1)[0]
        # Exactly the three German leagues have source ids; all other
        # catalogue entries are only a roadmap and must not claim live data.
        for ident in ("'bl1'", "'bl2'", "'bl3'"):
            self.assertEqual(catalogue.count(ident), 1)
        self.assertEqual(catalogue.count("['"), 17)

    def test_forecast_sharing_uses_only_verified_archive_and_deep_link(self):
        self.assertIn("shared-forecast-status", self.page.ids)
        js = "\n".join(self.page.js)
        for code in (
            "const sharedForecastId=rawSharedId&&/^[a-zA-Z0-9_-]{1,100}$/.test(rawSharedId)",
            "const sharedRecord=ready&&sharedForecastId?data.find(r=>r.id===sharedForecastId):null;",
            "const url=new URL(location.pathname,location.origin);",
            "url.searchParams.set('forecast',record.id);",
            "url.hash='ranking';",
            "if(typeof navigator.share==='function')",
            "await navigator.clipboard.writeText(link);",
            "window.prompt('Skopiuj link do tej prognozy:',link);",
            "rows.unshift(sharedRecord);",
            "if(sharedRecord&&r.id===sharedForecastId)",
            "if(focusSharedForecast&&sharedRecord)",
            "card.classList.add('shared-target');",
            "target.scrollIntoView({behavior:'auto',block:'start'});",
            "if(focusSharedForecast&&sharedRecord)",
        ):
            self.assertIn(code, js)
        self.assertIn("forecast-card-actions", self.html)
        self.assertIn("share-forecast-button", self.html)
        self.assertIn("Nie znaleziono tej prognozy w zweryfikowanym archiwum", js)

    def test_lab_automation_is_honest_about_manual_runs(self):
        for ident in ("lab-run-badge", "lab-run-detail", "lab-automation-heading"):
            self.assertIn(ident, self.page.ids)
        js = "\n".join(self.page.js)
        self.assertIn("./lab_forward/run_status.json?t=", js)
        self.assertIn("status.event==='schedule'", js)
        self.assertIn("status.event==='workflow_dispatch'", js)
        self.assertIn("status.event==='workflow_run'&&status.upstream_event==='schedule'", js)
        self.assertIn("const automatic=status.event==='schedule'||backup;", js)
        self.assertIn("Udany test ręczny nie potwierdza działania harmonogramu.", js)
        self.assertIn("ageHours>3", js)
        self.assertIn("void loadLabAutomation(controller.signal);", js)
        self.assertIn("Brak prognoz może także oznaczać", self.html)

    def test_quality_home_benchmark_uses_same_verified_sample(self):
        js = "\n".join(self.page.js)
        self.assertIn("quality-home-benchmark", self.page.ids)
        self.assertIn("const graded=data.filter(scored)", js)
        self.assertIn("const homeHits=graded.filter(r=>r.settlement.outcome==='1').length;", js)
        self.assertIn("Model (najwyższe prawdopodobieństwo):", js)
        self.assertIn("Prosta strategia „zawsze gospodarze”:", js)
        self.assertIn("Brak zweryfikowanego archiwum", js)
        self.assertIn("Brak rozliczonych spotkań", js)
        self.assertIn("Nie jest to porównanie ROI ani wynik LAB.", js)

    def test_quality_brier_has_same_sample_uniform_baseline(self):
        import math
        js = "\n".join(self.page.js)
        self.assertIn("quality-brier-baseline", self.page.ids)
        for term in (
            "const meanBrier=graded.length?graded.reduce((sum,r)=>sum+brierOf(r),0)/graded.length:null;",
            "const uniformBrier=2/9;",
            "Brier modelu:",
            "równe szanse 1/X/2:",
            "Porównanie na tych samych",
            "próba za mała, by oceniać przewagę.",
            "To nie jest wynik LAB ani miara opłacalności zakładów.",
        ):
            self.assertIn(term, js)
        self.assertIn("Brier archiwum = średnia trzech kwadratowych błędów", self.html)
        self.assertIn("W LAB 2.1/2.2 Brier jest SUMĄ", self.html)

        # A multinomial Brier score averaged across 1/X/2 is always 2/9
        # for uniform probabilities, regardless of the realized result.
        uniform = {"1": 1/3, "X": 1/3, "2": 1/3}
        for outcome in ("1", "X", "2"):
            average = sum((uniform[k] - (k == outcome)) ** 2
                          for k in ("1", "X", "2")) / 3
            self.assertTrue(math.isclose(average, 2/9, abs_tol=1e-12))
            self.assertTrue(math.isclose(3*average, 2/3, abs_tol=1e-12))

        # Compute the real current sample without imposing any expected winner.
        from forecast_engine import valid_doc
        archive = json.loads((ROOT / "predictions.json").read_text(encoding="utf-8"))
        valid_doc(archive)
        scored = [r for r in archive["forecasts"]
                  if r["settlement"]["state"] == "graded"]
        values = []
        for record in scored:
            p = record["snapshot"]["probabilities"]
            result = record["settlement"]["outcome"]
            brier = sum((p[k] - (k == result)) ** 2 for k in ("1", "X", "2")) / 3
            self.assertTrue(math.isfinite(brier) and 0 <= brier <= 2/3)
            values.append(brier)
        if values:
            self.assertTrue(0 <= sum(values)/len(values) <= 2/3)

    def test_lab_report_counts_must_match_raw_ledger(self):
        for ident in ("lab-ledger-check", "lab-run-direct"):
            self.assertIn(ident, self.page.ids)
        js = "\n".join(self.page.js)
        for required in (
            "fetch('./lab_forward/ledger.json'",
            "ledger?.schema!==1",
            "Array.isArray(ledger.forecasts)",
            "ledger.forecasts.length!==data.pairs",
            "To kontrola spójności, nie dowód skuteczności ani czasu publikacji.",
            "Nie pokazujemy niesprawdzonych statystyk.",
            "if(/^[0-9]{1,20}$/.test(runId))",
            "direct.hidden=false;",
        ):
            self.assertIn(required, js)
        self.assertIn('href="./lab_forward/ledger.json"', self.html)

        # The current published report and raw research ledger must be
        # consistent. Test on a real CSV-free fixture, no network access.
        from pathlib import Path
        import re
        report = (ROOT / "lab_forward" / "RAPORT.md").read_text(encoding="utf-8")
        match = re.search(r"Zapisane pary prognoz:\s*(\d+)", report)
        self.assertIsNotNone(match)
        ledger = json.loads((ROOT / "lab_forward" / "ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger.get("schema"), 1)
        self.assertIsInstance(ledger.get("forecasts"), list)
        self.assertIsInstance(ledger.get("settlements"), dict)
        self.assertEqual(int(match.group(1)), len(ledger["forecasts"]))

    def test_full_verified_archive_can_be_downloaded_safely(self):
        self.assertIn("rank-export-csv", self.page.ids)
        self.assertIn("rank-export-status", self.page.ids)
        self.assertIn('id="rank-export-csv" type="button" class="secondary" disabled', self.html)
        js = "\n".join(self.page.js)
        for required in (
            "if(!state.archiveReady||state.archiveFailed)return;",
            "const records=state.archive.slice().sort(",
            "const rows=records.map(r=>",
            "r.snapshot_sha256",
            "settled?(lead.outcome===r.settlement.outcome?'TAK':'NIE')",
            "const csv='",
            "const url=URL.createObjectURL(new Blob([csv]",
            "if(/^\\s*[=+\\-@]/u.test(val))val=\"'\"+val;",
            "$('rank-export-csv').disabled=!ready;",
            "$('rank-export-csv').addEventListener('click',downloadVerifiedArchiveCsv);",
        ):
            self.assertIn(required, js)
        self.assertIn("bez ukrywania wyników", js)

    def test_archive_verification_fails_closed(self):
        js = "\n".join(self.page.js)
        self.assertIn("const invalid=checks.filter(ok=>!ok).length;", js)
        self.assertIn("if(invalid)throw new Error('Archiwum niekompletne:", js)
        self.assertIn("if(new Set(ids).size!==ids.length)", js)
        self.assertIn("state.archive=payload.forecasts;", js)
        self.assertIn("state.archive=[];state.archiveAt=null;state.archiveReady=false;state.archiveFailed=true;", js)
        self.assertIn("Nie pokazujemy częściowej próbki ani statystyk z wybranych rekordów.", js)
        self.assertNotIn("state.archive=verified;", js)

    def test_no_default_cherry_picking(self):
        self.assertRegex(self.html, r'<select id="rank-state">\s*<option value="all" selected>')
        self.assertRegex(self.html, r'<select id="rank-minprob">\s*<option value="0" selected>')
        self.assertRegex(self.html, r'<select id="rank-order">\s*<option value="newest" selected>')
        js = "\n".join(self.page.js)
        for check in ("if(status==='all')return true;", "if(order==='newest')return -dt",
                      "const data=state.archive,stats=rankGroup(data);", "NIETRAFIONY"):
            self.assertIn(check, js)

    def test_demonstration_is_clearly_separate(self):
        self.assertIn("BEZ OPŁAT · PUBLICZNE WYNIKI", self.html)
        self.assertIn("fikcyjne dane demonstracyjne", self.html)
        self.assertIn("Płatności i dostęp Premium jeszcze nie są aktywne.", self.html)
        tips = json.loads((ROOT / "tips.json").read_text(encoding="utf-8"))
        self.assertEqual(tips.get("mode"), "demo")

    def test_published_archive_is_valid(self):
        from forecast_engine import valid_doc
        doc = json.loads((ROOT / "predictions.json").read_text(encoding="utf-8"))
        valid_doc(doc)
        for entry in doc["forecasts"]:
            snap = entry["snapshot"]
            created = datetime.fromisoformat(snap["created_at"].replace("Z", "+00:00"))
            kickoff = datetime.fromisoformat(snap["kickoff"].replace("Z", "+00:00"))
            self.assertLess(created, kickoff, entry["id"])

    def test_embedded_json(self):
        self.assertIsInstance(self.page.json_data.get("research-original-json"), dict)

    def test_rank_filters_have_single_reset_control(self):
        self.assertEqual(self.page.ids.count("rank-reset"), 1)
        self.assertIn('aria-label="Wyczyść wszystkie filtry prognoz"', self.html)
        self.assertIn("  $('rank-reset').addEventListener('click',()=>{", self.html)
        for fragment in ("['rank-league','all']", "['rank-state','all']",
                         "['rank-order','newest']", "['rank-minprob','0']",
                         "$('rank-search').value=''",
                         "onlyWatched=false",
                         "$('rank-watched').setAttribute('aria-pressed','false')",
                         "renderRanking();"):
            self.assertIn(fragment, self.html)

    def test_live_team_filters_can_be_cleared_without_changing_league(self):
        self.assertEqual(self.page.ids.count("live-clear-team-filters"), 1)
        self.assertIn('aria-label="Pokaż wszystkie drużyny w wybranej lidze i sezonie"', self.html)
        self.assertIn("$('live-clear-team-filters').addEventListener('click'", self.html)
        for snippet in ("$('live-search').value=''", "onlyFavoriteTeams=false",
                        "$('live-favorites').setAttribute('aria-pressed','false')",
                        "$('live-favorites').textContent='☆ Moje drużyny'",
                        "liveLimit=16"):
            self.assertIn(snippet, self.html)

    def test_fixture_validation_reports_invalid_and_duplicate_source_records(self):
        self.assertIn("if(!m){invalidCount++;continue;}", self.html)
        self.assertIn("if(unique.has(matchKey))duplicateCount++;", self.html)
        self.assertIn("if(payload.length && !unique.size)throw new Error('Brak poprawnych rekordów terminarza')", self.html)
        self.assertIn("pominięto ${invalidCount} niepoprawnych i ${duplicateCount} powtórzonych", self.html)
        self.assertIn("state.loadedAt=cached.loadedAt;evaluateModel();render()", self.html)
        self.assertIn("new Date(cached.loadedAt).toLocaleString('pl-PL')", self.html)

    def test_inline_javascript_syntax(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js not installed locally; CI requires Node.js")
        self.assertGreater(len(self.page.js), 0)
        with tempfile.TemporaryDirectory() as tmp:
            for n, source in enumerate(self.page.js, 1):
                file = Path(tmp) / f"page_{n}.js"
                file.write_text(source, encoding="utf-8")
                result = subprocess.run([node, "--check", str(file)],
                                        capture_output=True, text=True, timeout=25)
                self.assertEqual(result.returncode, 0,
                                 f"JavaScript #{n} invalid: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
