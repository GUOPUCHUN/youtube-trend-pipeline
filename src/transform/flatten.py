"""Flatten the nested API response into analytics-ready rows."""

import logging
from typing import Any

from src.transform.duration import DurationParseError, parse_duration
from src.transform.schema import VideoListResponse

logger = logging.getLogger(__name__)


def flatten(raw: dict[str, Any], partition_date: str, region_code: str) -> list[dict]:
    """Convert a validated API response into flat records.

    Rows whose duration cannot be parsed are dropped and counted, rather than
    silently written with a bogus value.
    """
    validated = VideoListResponse.model_validate(raw)

    rows: list[dict] = []
    dropped = 0

    for video in validated.items:
        try:
            duration_seconds = parse_duration(video.content_details.duration)
        except DurationParseError:
            logger.warning("dropping %s: bad duration", video.id)
            dropped += 1
            continue

        rows.append(
            {
                "video_id": video.id,
                "title": video.snippet.title,
                "channel_id": video.snippet.channel_id,
                "channel_title": video.snippet.channel_title,
                "category_id": video.snippet.category_id,
                "published_at": video.snippet.published_at,
                "tag_count": len(video.snippet.tags),
                "duration_seconds": duration_seconds,
                "view_count": video.statistics.view_count,
                "like_count": video.statistics.like_count,
                "comment_count": video.statistics.comment_count,
                "region_code": region_code,
                "dt": partition_date,
            }
        )

    logger.info("flattened %d rows, dropped %d", len(rows), dropped)
    return rows
