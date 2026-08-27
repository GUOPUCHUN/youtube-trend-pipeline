"""Minimal YouTube Data API client — first working version."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://www.googleapis.com/youtube/v3/videos"


def fetch_most_popular(region_code: str = "JP", max_results: int = 10) -> dict:
    """Fetch the mostPopular chart for a region."""
    api_key = os.environ["YOUTUBE_API_KEY"]

    params = {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": max_results,
        "key": api_key,
    }

    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    data = fetch_most_popular()
    items = data.get("items", [])
    print(f"fetched {len(items)} items")

    for item in items:
        title = item["snippet"]["title"]
        category = item["snippet"]["categoryId"]
        views = item["statistics"].get("viewCount", "N/A")
        print(f"[cat {category:>2}] {views:>12} | {title[:50]}")

    # 幂等：文件名由日期决定，同一天重跑只会覆盖，不会重复
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"saved to {out_path}")


if __name__ == "__main__":
    main()