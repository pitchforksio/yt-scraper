import csv
import time
import argparse
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Set

import requests

# Defaults
DEFAULT_API_KEY = "AIzaSyAyf34yxPP0e803laPf64ju4YqKHs6JAec"
DEFAULT_CHANNEL_ID = "UCCjG8NtOig0USdrT5D1FpxQ"
BASE_URL = "https://www.googleapis.com/youtube/v3"


def load_existing_ids(filepath: str) -> Set[str]:
    """Reads the CSV and returns a set of video_ids to allow deduplication."""
    if not os.path.exists(filepath):
        return set()
    
    ids = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "video_id" in row:
                    ids.add(row["video_id"])
    except Exception as e:
        print(f"Warning: Could not read existing file {filepath}: {e}")
    return ids


def search_videos_in_range(
    api_key: str, 
    channel_id: str, 
    keywords: List[str], 
    start_date: str, 
    end_date: str
) -> List[Dict[str, Any]]:
    videos: List[Dict[str, Any]] = []
    page_token = None
    
    # Construct query
    query = " ".join(keywords) if keywords else ""
    
    # Format dates to RFC 3339 (YYYY-MM-DD -> YYYY-MM-DDT00:00:00Z)
    # We assume inclusive start, exclusive end logic often works best, 
    # but for simple YYYY-MM-DD input, we'll just append simple time.
    
    # Ensure RFC 3339 format
    published_after = f"{start_date}T00:00:00Z"
    published_before = f"{end_date}T23:59:59Z"

    print(f"Searching: '{query}' | Range: {published_after} to {published_before}")

    while True:
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "q": query,
            "type": "video",
            "maxResults": 50,
            "key": api_key,
            "publishedAfter": published_after,
            "publishedBefore": published_before,
        }
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(f"{BASE_URL}/search", params=params)
        
        if resp.status_code == 403:
             print("Quota exceeded or permission denied.")
             resp.raise_for_status()

        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        if not items:
            break
            
        for item in items:
            snippet = item["snippet"]
            video_id = item["id"].get("videoId")
            if not video_id:
                continue # Sometimes playlist items appear
                
            videos.append(
                {
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "published_at": snippet.get("publishedAt", ""),
                }
            )

        page_token = data.get("nextPageToken")
        if not page_token:
            break
        
        # Safety break for very deep results to prevent infinite loops if API acts up
        if len(videos) > 2000:
             print("Warning: Hit 2000 results in single batch. Consider splitting date range.")
             break

        time.sleep(0.05)
    
    return videos


def enrich_with_video_stats(api_key: str, videos: List[Dict[str, Any]]) -> None:
    """Mutates `videos` in-place to add stats/duration."""
    id_to_video = {v["video_id"]: v for v in videos}
    video_ids = list(id_to_video.keys())

    if not video_ids:
        return

    print(f"Enriching {len(videos)} videos with statistics...")

    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i : i + 50]
        params = {
            "part": "statistics,contentDetails",
            "id": ",".join(batch_ids),
            "maxResults": 50,
            "key": api_key,
        }
        resp = requests.get(f"{BASE_URL}/videos", params=params)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("items", []):
            vid = item["id"]
            stats = item.get("statistics", {})
            details = item.get("contentDetails", {})
            v = id_to_video.get(vid)
            if not v:
                continue
            v["view_count"] = int(stats.get("viewCount", 0))
            v["like_count"] = int(stats.get("likeCount", 0)) if "likeCount" in stats else None
            v["comment_count"] = (
                int(stats.get("commentCount", 0)) if "commentCount" in stats else None
            )
            v["duration"] = details.get("duration")

        time.sleep(0.05)


def append_to_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    """Appends to CSV, writing header only if file is new/empty."""
    if not rows:
        return

    file_exists = os.path.exists(path) and os.path.getsize(path) > 0
    
    # Ensure fields match existing schema implies we generally know the schema.
    # We will use keys from the first new row.
    fieldnames = list(rows[0].keys())
    
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube Date-Range Search Scraper")
    parser.add_argument("--api_key", default=DEFAULT_API_KEY)
    parser.add_argument("--channel_id", default=DEFAULT_CHANNEL_ID)
    parser.add_argument("--keywords", nargs="*", help="Keywords to filter/search by.")
    parser.add_argument("--output", default="coulthart_reality_check.csv", help="Output CSV file (appends to it)")
    
    # Date args
    parser.add_argument("--start_date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end_date", required=True, help="YYYY-MM-DD")

    args = parser.parse_args()
    
    # 1. Load existing IDs
    existing_ids = load_existing_ids(args.output)
    print(f"Loaded {len(existing_ids)} existing video IDs from {args.output}")

    # 2. Search
    found_videos = search_videos_in_range(
        args.api_key, 
        args.channel_id, 
        args.keywords if args.keywords else [],
        args.start_date,
        args.end_date
    )
    print(f"Search returned {len(found_videos)} videos.")

    # 3. Deduplicate
    new_videos = []
    for v in found_videos:
        if v["video_id"] not in existing_ids:
            new_videos.append(v)
            existing_ids.add(v["video_id"]) # Prevent internal duplicates if API is weird
    
    if not new_videos:
        print("No NEW videos found (all duplicates). Exiting.")
        return
    
    print(f"Identified {len(new_videos)} NEW videos to add.")

    # 4. Enrich
    enrich_with_video_stats(args.api_key, new_videos)

    # 5. Append
    append_to_csv(args.output, new_videos)
    print(f"Appended {len(new_videos)} videos to {args.output}")


if __name__ == "__main__":
    main()
