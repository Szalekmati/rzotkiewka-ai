"""Offline safeguards for RZOTKIEWKA LAB's read-only fixture diagnostic.

Passing these tests does not prove that GitHub delivered a scheduled run.
"""
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "diagnostyka_terminarza_lab.yml"
STEP_START = (
    "      - name: Sprawdz terminarz i gotowosc modeli\n"
    "        shell: python\n"
    "        run: |\n"
)
STEP_END = "      - name: Pobierz czytelny raport"


def inline_python():
    text = WORKFLOW.read_text(encoding="utf-8")
    if text.count(STEP_START) != 1 or text.count(STEP_END) != 1:
        raise ValueError("Missing or duplicated diagnostic Python step")
    section = text.split(STEP_START, 1)[1].split(STEP_END, 1)[0]
    lines = section.splitlines()
    if any(line.strip() and not line.startswith("          ") for line in lines):
        raise ValueError("Bad YAML block indentation")
    script = "\n".join(line[10:] if line.startswith("          ") else ""
                       for line in lines)
    return text, script


class LabDiagnosticSafetyTests(unittest.TestCase):
    def test_inline_python_compiles_without_running_api_requests(self):
        _, script = inline_python()
        compile(script, str(WORKFLOW), "exec")

    def test_scheduled_read_only_operation(self):
        workflow, script = inline_python()
        self.assertIn("on:\n  workflow_dispatch:\n  schedule:", workflow)
        self.assertIn("- cron: '17 17 * * *'", workflow)
        self.assertIn("permissions:\n  contents: read\n", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertIn("actions/upload-artifact@v6", workflow)
        self.assertIn("if: always()", workflow)
        for dangerous in ("git push", "git commit", "git add ", "workflow_dispatch: # write"):
            self.assertNotIn(dangerous, workflow)
        self.assertIn("observer.validate_state", script)
        self.assertIn("source_hashes", script)
        self.assertIn("max_lead_hours", script)

    def test_window_limits_include_162_and_168_hours(self):
        _, script = inline_python()
        parsed = ast.parse(script)
        functions = [node for node in parsed.body
                     if isinstance(node, ast.FunctionDef)
                     and node.name == "window_status"]
        self.assertEqual(len(functions), 1)
        namespace = {}
        exec(compile(ast.Module(body=functions, type_ignores=[]),
                     str(WORKFLOW), "exec"), namespace)
        status = namespace["window_status"]
        kickoff = datetime(2026, 11, 20, 18, tzinfo=timezone.utc)
        for lead, expected in (
            (169, "ZA WCZEŚNIE"),
            (168, "W OKNIE"),
            (165, "W OKNIE"),
            (162, "W OKNIE"),
            (161, "OKNO MINĘŁO"),
        ):
            with self.subTest(lead=lead):
                self.assertEqual(status(kickoff,
                                        kickoff - timedelta(hours=lead),
                                        162, 168), expected)

    def test_missing_stale_failed_and_future_status_warning(self):
        _, script = inline_python()
        for phrase in (
            "lab_forward/run_status.json",
            "if not status_path.exists():",
            "if hours_since > 3:",
            "elif hours_since < -0.05:",
            "if outcome != 'success':",
            "Ostatni status ma ponad 3 godziny",
            "Ostatni krok obserwacji nie byl oznaczony success",
            "Zapis statusu nie oznacza zapisania prognozy",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, script)


if __name__ == "__main__":
    unittest.main()
