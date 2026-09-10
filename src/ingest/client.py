"""YouTube Data API client with retry and error classification."""

import logging
from typing import Any

import requests
from dotenv import load_dotenv
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.common.config import get_api_key

load_dotenv()

logger = logging.getLogger(__name__)

API_URL = "https://www.googleapis.com/youtube/v3/videos"

# Transient failures: rate limiting and server-side errors.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class RetryableAPIError(Exception):
    """Transient failure — retrying may succeed."""


class FatalAPIError(Exception):
    """Client-side failure — retrying will never help."""


@retry(
    retry=retry_if_exception_type(
        (
            RetryableAPIError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        )
    ),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(4),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _get(params: dict[str, Any]) -> dict[str, Any]:
    """Single HTTP call. Classifies failures so the retry policy can act."""
    response = requests.get(API_URL, params=params, timeout=30)

    if response.status_code in RETRYABLE_STATUS:
        raise RetryableAPIError(f"HTTP {response.status_code}: {response.text[:200]}")

    if 400 <= response.status_code < 500:
        # 400 (bad request), 403 (invalid key / quota exhausted for the day)
        raise FatalAPIError(f"HTTP {response.status_code}: {response.text[:200]}")

    response.raise_for_status()
    return response.json()


def fetch_most_popular(
    region_code: str = "JP",
    max_results: int = 50,
) -> dict[str, Any]:
    """Fetch the mostPopular chart for a region.

    Quota cost: 1 unit per call.
    """
    params = {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": max_results,
        "key": get_api_key(),
    }
    logger.info("fetching mostPopular region=%s max=%s", region_code, max_results)
    return _get(params)
