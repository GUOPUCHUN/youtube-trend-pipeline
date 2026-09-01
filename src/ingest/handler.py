"""Local entry point: fetch, validate, persist."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from src.ingest.client import fetch_most_popular
from src.transform.schema import VideoListResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    raw = fetch_most_popular(region_code="JP", max_results=50)

    # Fail fast: any schema drift raises here, before anything is persisted.
    validated = VideoListResponse.model_validate(raw)
    logger.info("validated %d items", len(validated.items))

    for video in validated.items[:10]:
        logger.info(
            "cat=%-2s views=%-10s %s",
            video.snippet.category_id,
            video.statistics.view_count,
            video.snippet.title[:45],
        )

    # Idempotent: the key is derived from the date, so re-running a day
    # overwrites rather than duplicates.
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    logger.info("saved %s", out_path)


if __name__ == "__main__":
    main()
