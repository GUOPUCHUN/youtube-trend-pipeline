"""Write records to S3 as Parquet.

Uses pyarrow directly rather than pandas: the deployment package stays small
enough to ship without a Lambda layer.
"""

import io
import logging
import os

import boto3
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

# An explicit schema keeps column types stable across daily partitions.
SCHEMA = pa.schema(
    [
        ("video_id", pa.string()),
        ("title", pa.string()),
        ("channel_id", pa.string()),
        ("channel_title", pa.string()),
        ("category_id", pa.string()),
        ("published_at", pa.timestamp("us", tz="UTC")),
        ("tag_count", pa.int32()),
        ("duration_seconds", pa.int32()),
        ("view_count", pa.int64()),
        ("like_count", pa.int64()),
        ("comment_count", pa.int64()),
        ("region_code", pa.string()),
        ("dt", pa.string()),
    ]
)


def put_parquet(key: str, rows: list[dict]) -> str:
    """Write rows to the curated zone as a single Snappy-compressed Parquet file."""
    bucket = os.environ["S3_BUCKET"]

    columns = {field.name: [row.get(field.name) for row in rows] for field in SCHEMA}
    table = pa.Table.from_pydict(columns, schema=SCHEMA)

    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression="snappy")
    body = buffer.getvalue()

    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/octet-stream",
    )

    uri = f"s3://{bucket}/{key}"
    logger.info("wrote %d rows (%d bytes) to %s", len(rows), len(body), uri)
    return uri


def build_curated_key(date_str: str, region_code: str) -> str:
    """Hive-style partitioned key for the curated zone."""
    return f"curated/dt={date_str}/region={region_code}/data.parquet"
