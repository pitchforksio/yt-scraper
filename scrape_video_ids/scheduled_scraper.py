import csv
import time
import argparse
import os
import requests
import json
from datetime import datetime, timedelta

# Configuration defaults
DEFAULT_CONFIG_PATH = "../scraper_config.json"
BASE_URL = "https://www.googleapis.com/youtube/v3"
SAFE_LIMIT = 450 

def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)

def parse_date(date_str):
    try:
        if "T" in date_str:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def get_latest_date_from_csv(filepath):
    latest = None
    if not os.path.exists(filepath):
        return None
        
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = parse_date(row["published_at"])
            if d:
                if latest is None or d > latest:
                    latest = d
    return latest

def search_strict_range(api_key, channel_id, keywords, start_dt, end_dt):
    videos = []
    page_token = None
    query = " ".join(keywords)
    
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
    return videos, (len(videos) >= SAFE_LIMIT)

def create_initial_csv(filepath):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["video_id","title","description","published_at","view_count","like_count","comment_count","duration","source"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

def enrich_and_append(api_key, videos, filepath):
    if not videos:
        return

    # Dedupe based on video_id
    existing_ids = set()
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_ids.add(row["video_id"])
    
    new_videos = [v for v in videos if v["video_id"] not in existing_ids]
    
    if not new_videos:
        print("No new unique videos found.")
        return

    print(f"Enriching {len(new_videos)} new videos...")
    id_to_video = {v["video_id"]: v for v in new_videos}
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

    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["video_id","title","description","published_at","view_count","like_count","comment_count","duration","source"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        if not file_exists:
            writer.writeheader()
        for v in new_videos:
            v["source"] = "scheduled_search"
            writer.writerow(v)
    
    print(f"Saved {len(new_videos)} videos to {filepath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    
    config = load_config(args.config)
    csv_path = config["scraping"]["csv_path"]
    
    # Adjust path if relative
    if not os.path.isabs(csv_path):
        # Assume relative to working dir or common location
        # Since we run in scrape_video_ids, let's just use it
        pass

    latest_date = get_latest_date_from_csv(csv_path)
    
    if not latest_date:
        print("No existing data found. Defaulting to config start date.")
        start_dt = datetime.strptime(config["scraping"]["start_date"], "%Y-%m-%d")
    else:
        print(f"Latest video date in CSV: {latest_date}")
        start_dt = latest_date + timedelta(seconds=1) # Start right after
        
    end_dt = datetime.now()
    
    if start_dt >= end_dt:
        print("Up to date. No new search needed.")
        return

    print(f"Searching for new videos from {start_dt} to {end_dt}...")
    
    videos, hit_limit = search_strict_range(
        config["youtube"]["api_key"],
        config["youtube"]["channel_id"],
        config["youtube"]["keywords"],
        start_dt,
        end_dt
    )
    
    enrich_and_append(config["youtube"]["api_key"], videos, csv_path)

if __name__ == "__main__":
    main()
