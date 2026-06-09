"""Tests for mqtt2mail pure functions (no MQTT broker needed)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Module calls load_dotenv() at import — set env before importing.
os.environ.setdefault("POOL_LIST", '[]')
os.environ.setdefault("REPORT_TIMES", "")
os.environ.setdefault("SMTP_HOST", "")
os.environ.setdefault("SMTP_USERNAME", "")
os.environ.setdefault("SMTP_PASSWORD", "")
os.environ.setdefault("MAIL_FROM", "test@test.com")
os.environ.setdefault("MAIL_TO", "test@test.com")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import mqtt2mail


class TestNormalizeTopic:
    def test_strips_whitespace(self):
        assert mqtt2mail.normalize_topic(" /foo/bar ") == "/foo/bar"

    def test_strips_trailing_slash(self):
        assert mqtt2mail.normalize_topic("/foo/bar/") == "/foo/bar"

    def test_keeps_root_slash(self):
        assert mqtt2mail.normalize_topic("/") == "/"

    def test_empty_string(self):
        assert mqtt2mail.normalize_topic("") == ""


class TestParsePoolTopics:
    def test_returns_empty_on_empty_env(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST", "")
        assert mqtt2mail.parse_pool_topics() == []

    def test_returns_empty_on_invalid_json(self, monkeypatch, caplog):
        monkeypatch.setenv("POOL_LIST", "not-json")
        result = mqtt2mail.parse_pool_topics()
        assert result == []
        assert "Invalid JSON" in caplog.text

    def test_returns_empty_on_non_array(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST", '{"key":"val"}')
        assert mqtt2mail.parse_pool_topics() == []

    def test_parses_single_pool(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST", '[{"name":"Pool","topic":"home/H32/pool"}]')
        assert mqtt2mail.parse_pool_topics() == ["home/H32/pool"]

    def test_parses_multiple_pools(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST", '[{"name":"A","topic":"a/b"},{"name":"B","topic":"c/d"}]')
        assert mqtt2mail.parse_pool_topics() == ["a/b", "c/d"]

    def test_skips_entry_missing_topic(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST", '[{"name":"A"},{"name":"B","topic":"b/topic"}]')
        assert mqtt2mail.parse_pool_topics() == ["b/topic"]

    def test_skips_entry_with_empty_topic(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST", '[{"name":"A","topic":""},{"name":"B","topic":"b/topic"}]')
        assert mqtt2mail.parse_pool_topics() == ["b/topic"]


class TestUniqueTopics:
    def test_dedup(self):
        assert mqtt2mail.unique_topics(["a", "b", "a", "c"]) == ["a", "b", "c"]

    def test_empty(self):
        assert mqtt2mail.unique_topics([]) == []

    def test_skips_empty_strings(self):
        assert mqtt2mail.unique_topics(["a", "", "b"]) == ["a", "b"]


class TestResolveTopics:
    def test_data_topic_adds_wildcard(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST", '[{"name":"P","topic":"home/pool"}]')
        data, alerts, avail = mqtt2mail.resolve_topics()
        assert data == ["home/pool/+"]

    def test_alert_topic_has_double_wildcard(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST", '[{"name":"P","topic":"base"}]')
        data, alerts, avail = mqtt2mail.resolve_topics()
        assert alerts == ["base/+/alert"]

    def test_availability_is_empty(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST", '[{"name":"P","topic":"x"}]')
        _, _, avail = mqtt2mail.resolve_topics()
        assert avail == []

    def test_multiple_pools_dedup_topics(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST",
            '[{"name":"A","topic":"x"},{"name":"B","topic":"x"}]')
        data, alerts, _ = mqtt2mail.resolve_topics()
        assert data == ["x/+"]
        assert alerts == ["x/+/alert"]

    def test_returns_empty_when_no_pools(self, monkeypatch):
        monkeypatch.setenv("POOL_LIST", "[]")
        data, alerts, avail = mqtt2mail.resolve_topics()
        assert data == []
        assert alerts == []
        assert avail == []


class TestTopicMatches:
    def test_exact_match(self):
        assert mqtt2mail.topic_matches("foo/bar", "foo/bar") is True

    def test_exact_mismatch(self):
        assert mqtt2mail.topic_matches("foo/bar", "foo/baz") is False

    def test_plus_single_level(self):
        assert mqtt2mail.topic_matches("foo/+/bar", "foo/x/bar") is True

    def test_plus_rejects_deeper(self):
        assert mqtt2mail.topic_matches("foo/+/bar", "foo/x/y/bar") is False

    def test_hash_matches_rest(self):
        assert mqtt2mail.topic_matches("foo/#", "foo/bar/baz") is True

    def test_hash_matches_nothing(self):
        assert mqtt2mail.topic_matches("foo/#", "foo") is True

    def test_hash_not_at_end_pragmatically_matches(self):
        # The implementation is more permissive than strict MQTT: `#`
        # matches the rest regardless of position, which is safe for
        # mqtt2mail's filtering use case (no false negatives).
        assert mqtt2mail.topic_matches("foo/#/bar", "foo/x/bar") is True

    def test_different_root(self):
        assert mqtt2mail.topic_matches("a/b", "x/y") is False


class TestParseReportTimes:
    def test_single_time(self):
        assert mqtt2mail.parse_report_times("09:00") == [540]

    def test_multiple_times(self):
        assert mqtt2mail.parse_report_times("09:00,12:30,16:00") == [540, 750, 960]

    def test_returns_sorted(self):
        assert mqtt2mail.parse_report_times("16:00,09:00") == [540, 960]

    def test_empty_string(self):
        assert mqtt2mail.parse_report_times("") == []

    def test_invalid_value_skipped_silently(self):
        # Values without ":" separator are silently skipped (no warning).
        result = mqtt2mail.parse_report_times("09:00,abc,16:00")
        assert result == [540, 960]

    def test_malformed_time_component_warns(self, caplog):
        result = mqtt2mail.parse_report_times("09:00,ab:cd,16:00")
        assert result == [540, 960]
        assert "Invalid" in caplog.text


class TestFormatSubjectDate:
    def test_returns_german_short_format(self):
        dt = mqtt2mail.datetime(2026, 6, 7, 10, 0)
        result = mqtt2mail.format_subject_date(dt)
        # Sunday 7 June 2026 is a Sunday
        assert "So." in result
        assert "7.6." in result
        assert "10:00" in result

    def test_monday(self):
        dt = mqtt2mail.datetime(2026, 6, 8, 14, 30)
        result = mqtt2mail.format_subject_date(dt)
        assert "Mo." in result

    def test_thursday(self):
        dt = mqtt2mail.datetime(2026, 6, 11, 8, 15)
        result = mqtt2mail.format_subject_date(dt)
        assert "Do." in result


class TestBuildEmailBody:
    @staticmethod
    def _make_snapshot(**kw):
        base = {
            "window_start": mqtt2mail.datetime(2026, 6, 7, 9, 0),
            "window_end": mqtt2mail.datetime(2026, 6, 7, 10, 0),
            "metrics": {},
            "message_count": 0,
            "alerts": [],
            "availability": [],
            "sensor_name": "Pool",
        }
        base.update(kw)
        return base

    def test_plain_heading_contains_pool_name(self):
        snapshot = self._make_snapshot(message_count=5, sensor_name="TestPool")
        body = mqtt2mail.build_email_body(snapshot)
        assert "TestPool" in body
        assert "7.6." in body
        assert "Empfangene Messungen: 5" in body

    def test_plain_includes_alert_section_when_present(self):
        snapshot = self._make_snapshot(
            message_count=3,
            alerts=[mqtt2mail.AlertEvent(
                is_alert=True, kind="temp", value=29.0,
                min_value=20.0, max_value=30.0, text="temp zu hoch",
                timestamp=mqtt2mail.datetime(2026, 6, 7, 9, 30),
            )],
            sensor_name="P",
        )
        body = mqtt2mail.build_email_body(snapshot)
        assert "Warnung:" in body

    def test_html_contains_h1(self):
        snapshot = self._make_snapshot(sensor_name="Pool")
        html = mqtt2mail.build_email_body_html(snapshot)
        assert "<h1>" in html
        assert "Pool" in html
        assert "Empfangene Messungen: 0" in html
