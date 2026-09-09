"""Entry point: fetch, validate, persist to S3."""

import logging
from datetime import UTC, datetime
from typing import Any

from dotenv import load_dotenv

from src.common.s3 import build_raw_key, put_json
from src.ingest.client import fetch_most_popular
from src.transform.schema import VideoListResponse

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

REGION_CODE = "JP"


def run() -> dict[str, Any]:
    """Fetch one day of chart data and store it in the raw zone."""
    raw = fetch_most_popular(region_code=REGION_CODE, max_results=50)

    validated = VideoListResponse.model_validate(raw)
    logger.info("validated %d items", len(validated.items))

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    key = build_raw_key(today, REGION_CODE)
    uri = put_json(key, raw)

    return {
        "item_count": len(validated.items),
        "s3_uri": uri,
        "partition_date": today,
    }


def lambda_handler(event: dict, context: object) -> dict[str, Any]:
    """AWS Lambda entry point."""
    return run()


if __name__ == "__main__":
    result = run()
    logger.info("done: %s", result)
