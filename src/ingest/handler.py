"""Entry point: fetch, validate, persist raw JSON and curated Parquet."""

import logging
from datetime import UTC, datetime
from typing import Any

from dotenv import load_dotenv

from src.common.parquet import build_curated_key, put_parquet
from src.common.s3 import build_raw_key, put_json
from src.ingest.client import fetch_most_popular
from src.transform.flatten import flatten

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

REGION_CODE = "JP"


def run() -> dict[str, Any]:
    """Fetch one day of chart data; write raw JSON then curated Parquet."""
    raw = fetch_most_popular(region_code=REGION_CODE, max_results=50)

    today = datetime.now(UTC).strftime("%Y-%m-%d")

    raw_uri = put_json(build_raw_key(today, REGION_CODE), raw)

    rows = flatten(raw, partition_date=today, region_code=REGION_CODE)
    curated_uri = put_parquet(build_curated_key(today, REGION_CODE), rows)

    return {
        "row_count": len(rows),
        "raw_uri": raw_uri,
        "curated_uri": curated_uri,
        "partition_date": today,
    }


def lambda_handler(event: dict, context: object) -> dict[str, Any]:
    """AWS Lambda entry point."""
    return run()


if __name__ == "__main__":
    logger.info("done: %s", run())
