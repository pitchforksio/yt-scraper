import csv
import time
import argparse
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set

# Configuration
DEFAULT_API_KEY = "AIzaSyAyf34yxPP0e803laPf64ju4YqKHs6JAec"
DEFAULT_CHANNEL_ID = "UCCjG8NtOig0USdrT5D1FpxQ"
BASE_URL = "https://www.googleapis.com/youtube/v3"
SAFE_LIMIT = 450 # If we get more than this, we assume we might be truncated

def parse_date(date_str):
    try:
        # Handles 2024-09-17 or 2024-09-17T12:00:00Z
        if "T" in date_str:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def get_earliest_date_from_csv(filepath: str) -> str:
    earliest = None
    if not os.path.exists(filepath):
        return None
        
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = parse_date(row["published_at"])
            if d:
                if earliest is None or d < earliest:
                    earliest = d
    
    if earliest:
        return earliest.strftime("%Y-%m-%d")
    return None

def load_existing_ids(filepath: str) -> Set[str]:
    ids = set()
    if not os.path.exists(filepath):
        return ids
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "video_id" in row:
                ids.add(row["video_id"])
    return ids

def search_strict_range(api_key, channel_id, keywords, start_dt, end_dt):
    """
    Returns (videos, hit_limit_bool)
    """
    videos = []
    page_token = None
    query = " ".join(keywords)
    
    # RFC 3339
    published_after = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    published_before = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    print(f"  >> Querying {published_after} -> {published_before} ... ", end="", flush=True)

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

        try:
            resp = requests.get(f"{BASE_URL}/search", params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Error: {e}")
            return [], False

        for item in data.get("items", []):
            snippet = item["snippet"]
            video_id = item["id"].get("videoId")
            
            # Skip if it is upcoming/live
            if snippet.get("liveBroadcastContent") in ["upcoming", "live"]:
                 continue

            if video_id:
                videos.append({
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "published_at": snippet.get("publishedAt", ""),
                })

        page_token = data.get("nextPageToken")
        if not page_token:
            break
            
        time.sleep(0.05)
    
    print(f"Found {len(videos)}")
    # The API limit is around 500-600. If we hit 450, we assume unsafe.
    return videos, (len(videos) >= SAFE_LIMIT)

def recursive_search(api_key, channel_id, keywords, start_dt, end_dt, all_found):
    """
    Recursively splits time range if results are too dense.
    """
    videos, hit_limit = search_strict_range(api_key, channel_id, keywords, start_dt, end_dt)
    
    if hit_limit:
        mid_ts = start_dt.timestamp() + (end_dt.timestamp() - start_dt.timestamp()) / 2
        mid_dt = datetime.fromtimestamp(mid_ts)
        
        print(f"    [!] Hit safe limit ({len(videos)}). Splitting range...")
        print(f"    1) {start_dt} -> {mid_dt}")
        print(f"    2) {mid_dt} -> {end_dt}")
        
        recursive_search(api_key, channel_id, keywords, start_dt, mid_dt, all_found)
        recursive_search(api_key, channel_id, keywords, mid_dt, end_dt, all_found)
    else:
        # Safe to add
        for v in videos:
            all_found.append(v)

def enrich_and_append(api_key, videos, filepath):
    if not videos:
        return

    # Dedupe list just in case
    unique_v = {v["video_id"]: v for v in videos}.values()
    videos = list(unique_v)
    
    # Fetch stats
    print(f"Enriching {len(videos)} new videos...")
    id_to_video = {v["video_id"]: v for v in videos}
    video_ids = list(id_to_video.keys())
    
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        params = {"part": "statistics,contentDetails", "id": ",".join(batch), "key": api_key}
        data = requests.get(f"{BASE_URL}/videos", params=params).json()
        for item in data.get("items", []):
            vid = item["id"]
            stats = item.get("statistics", {})
            dur = item.get("contentDetails", {}).get("duration")
            if vid in id_to_video:
                id_to_video[vid]["view_count"] = stats.get("viewCount", 0)
                id_to_video[vid]["like_count"] = stats.get("likeCount", 0)
                id_to_video[vid]["comment_count"] = stats.get("commentCount", 0)
                id_to_video[vid]["duration"] = dur

    # Append
    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        # Use keys from first item
        fieldnames = ["video_id","title","description","published_at","view_count","like_count","comment_count","duration","source"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        if not file_exists:
            writer.writeheader()
        for v in videos:
            v["source"] = "smart_search"
            writer.writerow(v)
    
    print(f"Saved {len(videos)} videos to {filepath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api_key", default=DEFAULT_API_KEY)
    parser.add_argument("--channel_id", default=DEFAULT_CHANNEL_ID)
    parser.add_argument("--keywords", nargs="*", default=["Coulthart", "Reality Check"])
    parser.add_argument("--output", default="coulthart_reality_check.csv")
    parser.add_argument("--start_date", help="YYYY-MM-DD (e.g. 2021-01-01)", default="2021-01-01")
    
    args = parser.parse_args()
    
    # 1. Determine End Date (Earliest from CSV)
    end_date_str = get_earliest_date_from_csv(args.output)
    if not end_date_str:
        print("Could not find dates in CSV. Using Today.")
        end_date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"Search Window: {args.start_date} -> {end_date_str}")
    
    start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    if start_dt >= end_dt:
        print("Start date must be before end date.")
        return

    # 2. Recursive Search
    all_found_videos = []
    recursive_search(args.api_key, args.channel_id, args.keywords, start_dt, end_dt, all_found_videos)
    
    print(f"Total found in range: {len(all_found_videos)}")
    
    # 3. Filter Duplicates
    existing_ids = load_existing_ids(args.output)
    new_videos = [v for v in all_found_videos if v["video_id"] not in existing_ids]
    
    print(f"New unique videos: {len(new_videos)}")
    
    # 4. Save
    if new_videos:
        enrich_and_append(args.api_key, new_videos, args.output)
    else:
        print("No new videos to add.")

if __name__ == "__main__":
    main()
