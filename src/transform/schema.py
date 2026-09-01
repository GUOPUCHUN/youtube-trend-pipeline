"""Pydantic models for the YouTube API response.

Purpose: fail fast on upstream schema drift. If YouTube changes a field's
name, type, or presence, validation raises immediately rather than letting
corrupted records flow into the curated zone.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VideoSnippet(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    published_at: datetime = Field(alias="publishedAt")
    channel_id: str = Field(alias="channelId")
    title: str
    channel_title: str = Field(alias="channelTitle")
    category_id: str = Field(alias="categoryId")
    # Many videos carry no tags at all — absence is normal, not an error.
    tags: list[str] = Field(default_factory=list)


class VideoStatistics(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # The API returns these as strings ("1879773"); pydantic coerces to int.
    # Creators can hide like counts, so these are genuinely optional.
    view_count: int | None = Field(default=None, alias="viewCount")
    like_count: int | None = Field(default=None, alias="likeCount")
    comment_count: int | None = Field(default=None, alias="commentCount")


class VideoContentDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # ISO 8601 duration, e.g. "PT4M13S". Parsed downstream in transform.
    duration: str


class Video(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    snippet: VideoSnippet
    statistics: VideoStatistics
    content_details: VideoContentDetails = Field(alias="contentDetails")


class VideoListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[Video]
