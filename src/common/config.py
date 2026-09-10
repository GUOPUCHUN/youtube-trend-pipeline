"""Configuration resolution.

Locally the API key comes from .env. On Lambda it comes from SSM Parameter
Store, so the secret never lives in an environment variable or in code.
"""

import functools
import os

import boto3

SSM_PARAM_NAME = "/youtube-pipeline/api-key"


@functools.lru_cache(maxsize=1)
def get_api_key() -> str:
    """Return the YouTube API key.

    Prefers the local environment; falls back to SSM when running on Lambda.
    """
    local = os.environ.get("YOUTUBE_API_KEY")
    if local:
        return local

    client = boto3.client("ssm")
    response = client.get_parameter(Name=SSM_PARAM_NAME, WithDecryption=True)
    return response["Parameter"]["Value"]
