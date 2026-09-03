"""Unit tests for the YouTube API client.

All HTTP traffic is mocked — these tests never touch the network and never
consume API quota.
"""

import pytest
import requests
import responses

from src.ingest import client
from src.ingest.client import (
    API_URL,
    FatalAPIError,
    RetryableAPIError,
    fetch_most_popular,
)

SAMPLE_RESPONSE = {
    "kind": "youtube#videoListResponse",
    "items": [
        {
            "id": "abc123",
            "snippet": {
                "publishedAt": "2026-08-31T12:00:00Z",
                "channelId": "UC_test",
                "title": "test video",
                "channelTitle": "test channel",
                "categoryId": "10",
            },
            "statistics": {"viewCount": "1000"},
            "contentDetails": {"duration": "PT4M13S"},
        }
    ],
}


@pytest.fixture(autouse=True)
def _no_retry_delay(monkeypatch):
    """Strip the exponential backoff so tests run instantly.

    The retry *policy* is what we're testing; the wall-clock delay is not.
    """
    monkeypatch.setattr(client._get.retry, "wait", lambda *_, **__: 0)


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch):
    """Never read the developer's real key during tests."""
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key-not-real")


class TestSuccessPath:
    @responses.activate
    def test_returns_parsed_json(self):
        responses.add(responses.GET, API_URL, json=SAMPLE_RESPONSE, status=200)

        result = fetch_most_popular(region_code="JP", max_results=1)

        assert result["items"][0]["id"] == "abc123"
        assert len(responses.calls) == 1

    @responses.activate
    def test_sends_expected_query_parameters(self):
        responses.add(responses.GET, API_URL, json=SAMPLE_RESPONSE, status=200)

        fetch_most_popular(region_code="US", max_results=25)

        sent = responses.calls[0].request.params
        assert sent["chart"] == "mostPopular"
        assert sent["regionCode"] == "US"
        assert sent["maxResults"] == "25"


class TestRetryableErrors:
    """429 and 5xx are transient — the client must retry."""

    @responses.activate
    def test_recovers_after_transient_failures(self):
        responses.add(responses.GET, API_URL, json={}, status=503)
        responses.add(responses.GET, API_URL, json={}, status=503)
        responses.add(responses.GET, API_URL, json=SAMPLE_RESPONSE, status=200)

        result = fetch_most_popular()

        assert result["items"][0]["id"] == "abc123"
        assert len(responses.calls) == 3, "should have retried twice"

    @responses.activate
    def test_gives_up_after_four_attempts(self):
        for _ in range(5):
            responses.add(responses.GET, API_URL, json={}, status=503)

        with pytest.raises(RetryableAPIError):
            fetch_most_popular()

        assert len(responses.calls) == 4, "stop_after_attempt(4) must be honoured"

    @responses.activate
    def test_rate_limiting_is_retried(self):
        responses.add(responses.GET, API_URL, json={}, status=429)
        responses.add(responses.GET, API_URL, json=SAMPLE_RESPONSE, status=200)

        fetch_most_popular()

        assert len(responses.calls) == 2


class TestFatalErrors:
    """4xx client errors will never succeed on retry — fail immediately."""

    @responses.activate
    def test_forbidden_is_not_retried(self):
        responses.add(responses.GET, API_URL, json={}, status=403)

        with pytest.raises(FatalAPIError):
            fetch_most_popular()

        assert len(responses.calls) == 1, "403 must not consume retry budget"

    @responses.activate
    def test_bad_request_is_not_retried(self):
        responses.add(responses.GET, API_URL, json={}, status=400)

        with pytest.raises(FatalAPIError):
            fetch_most_popular()

        assert len(responses.calls) == 1

    @responses.activate
    def test_error_message_carries_the_status_code(self):
        """Failures must be diagnosable from a single log line."""
        responses.add(responses.GET, API_URL, json={}, status=403)

        with pytest.raises(FatalAPIError, match="403"):
            fetch_most_popular()


class TestNetworkErrors:
    @responses.activate
    def test_timeout_is_retried(self):
        responses.add(responses.GET, API_URL, body=requests.exceptions.Timeout())
        responses.add(responses.GET, API_URL, json=SAMPLE_RESPONSE, status=200)

        fetch_most_popular()

        assert len(responses.calls) == 2