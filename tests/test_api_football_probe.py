"""Testy offline: zadnych polaczen z prawdziwym API."""
import io
import json
import unittest

from api_football_probe import api_get, fixture_query, verify_subscription


class FakeResponse:
    def __init__(self, data):
        self.payload = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _n):
        return self.payload


class APIFootballProbeTests(unittest.TestCase):
    def test_auth_header_and_endpoint_without_exposing_key(self):
        seen = {}
        def fake_open(request, timeout):
            seen["url"] = request.full_url
            seen["key"] = request.get_header("X-apisports-key")
            return FakeResponse({"errors": [], "response": {}})
        api_get("status", "temporary-test-value", opener=fake_open)
        self.assertEqual(seen["url"], "https://v3.football.api-sports.io/status")
        self.assertEqual(seen["key"], "temporary-test-value")
        self.assertNotIn("temporary-test-value", seen["url"])

    def test_valid_pro(self):
        data = {"response": {"account": {"email": "private@example.com"},
                "subscription": {"plan": "Pro", "active": True},
                "requests": {"limit_day": 7500, "current": 2}}}
        self.assertEqual(verify_subscription(data),
                         {"plan": "Pro", "limit_day": 7500, "used_today": 2})

    def test_free_rejected(self):
        data = {"response": {"subscription": {"plan": "Free", "active": True},
                "requests": {"limit_day": 100, "current": 0}}}
        with self.assertRaises(RuntimeError):
            verify_subscription(data)

    def test_provider_errors_rejected_even_with_http_200(self):
        def fake_open(_request, timeout):
            return FakeResponse({"errors": {"token": "invalid"}, "response": []})
        with self.assertRaises(RuntimeError):
            api_get("status", "temporary-test-value", opener=fake_open)

    def test_fixture_query_validation(self):
        self.assertEqual(fixture_query("39", "2026", "2026-11-11"),
                         {"league": "39", "season": "2026", "date": "2026-11-11"})
        for league, season, day in [("x", "2026", "2026-11-11"), ("39", "20xx", "2026-11-11"),
                                    ("39", "2026", "2026-99-99")]:
            with self.assertRaises(ValueError):
                fixture_query(league, season, day)


if __name__ == "__main__":
    unittest.main()
