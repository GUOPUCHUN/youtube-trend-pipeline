"""S3 helpers for the ingestion pipeline."""

import json
import logging
import os
from typing import Any

import boto3

logger = logging.getLogger(__name__)


def put_json(key: str, payload: dict[str, Any]) -> str:
    """Write a JSON document to the data bucket.

    The key is caller-supplied and derived from the partition date, so
    re-running the same day overwrites rather than duplicates.
    """
    bucket = os.environ["S3_BUCKET"]
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    client = boto3.client("s3")
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )

    uri = f"s3://{bucket}/{key}"
    logger.info("wrote %d bytes to %s", len(body), uri)
    return uri


def build_raw_key(date_str: str, region_code: str) -> str:
    """Build a Hive-style partitioned key for the raw zone."""
    return f"raw/dt={date_str}/region={region_code}/data.json"
