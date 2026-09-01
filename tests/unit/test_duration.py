"""Unit tests for ISO 8601 duration parsing.

These tests make no network calls and touch no external services.
"""

import pytest

from src.transform.duration import DurationParseError, parse_duration


class TestValidDurations:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("PT4M13S", 253),  # typical music video
            ("PT45S", 45),  # Shorts-length clip
            ("PT1H", 3600),  # hours only
            ("PT2H30M", 9000),  # no seconds component
            ("PT1H2M10S", 3730),  # all three components
            ("PT10M", 600),  # minutes only
            ("PT0S", 0),  # explicit zero is meaningful
            ("PT12H34M56S", 45296),  # long-form content
        ],
    )
    def test_parses_to_expected_seconds(self, value: str, expected: int) -> None:
        assert parse_duration(value) == expected

    def test_zero_seconds_is_not_treated_as_missing(self) -> None:
        """PT0S is a real value, distinct from a parse failure."""
        assert parse_duration("PT0S") == 0


class TestInvalidDurations:
    @pytest.mark.parametrize(
        "value",
        [
            "",  # empty
            "PT",  # matches the pattern but carries no data
            "4M13S",  # missing the PT prefix
            "P1DT4M",  # date component — not expected from YouTube
            "PT4M13",  # trailing number with no unit
            "hello",  # not a duration at all
            "PT-5M",  # negative
        ],
    )
    def test_rejects_malformed_input(self, value: str) -> None:
        with pytest.raises(DurationParseError):
            parse_duration(value)

    def test_error_message_includes_the_offending_value(self) -> None:
        """Failures must be debuggable from the log line alone."""
        with pytest.raises(DurationParseError, match="PT4M13"):
            parse_duration("PT4M13")
