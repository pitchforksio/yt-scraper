import csv
import time
import argparse
from typing import List, Dict, Any

import requests

# Defaults
DEFAULT_API_KEY = "AIzaSyAyf34yxPP0e803laPf64ju4YqKHs6JAec"
DEFAULT_CHANNEL_ID = "UCCjG8NtOig0USdrT5D1FpxQ"
BASE_URL = "https://www.googleapis.com/youtube/v3"


def get_uploads_playlist_id(api_key: str, channel_id: str) -> str:
    params = {
        "part": "contentDetails",
        "id": channel_id,
        "key": api_key,
    }
    resp = requests.get(f"{BASE_URL}/channels", params=params)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    if not items:
        raise RuntimeError("No channel found – check CHANNEL_ID.")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_all_videos_from_uploads_playlist(
    api_key: str, uploads_playlist_id: str
) -> List[Dict[str, Any]]:
    videos: List[Dict[str, Any]] = []
    page_token = None

    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(f"{BASE_URL}/playlistItems", params=params)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("items", []):
            snippet = item["snippet"]
            resource = snippet["resourceId"]
            videos.append(
                {
                    "video_id": resource["videoId"],
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "published_at": snippet.get("publishedAt", ""),
                }
            )

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(0.05)

    return videos


def search_videos_by_keywords(
    api_key: str, channel_id: str, keywords: List[str]
) -> List[Dict[str, Any]]:
    videos: List[Dict[str, Any]] = []
    page_token = None
    query = " ".join(keywords)

    print(f"Searching for videos with query: '{query}' in channel: {channel_id}")

    while True:
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "q": query,
            "type": "video",
            "maxResults": 50,
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(f"{BASE_URL}/search", params=params)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("items", []):
            snippet = item["snippet"]
            video_id = item["id"]["videoId"]
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

        time.sleep(0.05)

    return videos


def enrich_with_video_stats(api_key: str, videos: List[Dict[str, Any]]) -> None:
    """Mutates `videos` in-place to add stats/duration."""
    id_to_video = {v["video_id"]: v for v in videos}
    video_ids = list(id_to_video.keys())

    if not video_ids:
        return

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
            v["duration"] = details.get("duration")  # ISO 8601, e.g. PT5M10S

        time.sleep(0.05)


def filter_by_title_keywords_local(
    videos: List[Dict[str, Any]], keywords: List[str]
) -> List[Dict[str, Any]]:
    """Legacy local filter if needed, though search API is preferred for keywords."""
    lowered = [k.lower() for k in keywords]
    result: List[Dict[str, Any]] = []
    for v in videos:
        title = v["title"].lower()
        if any(k in title for k in lowered):
            result.append(v)
    return result


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print("No rows to write.")
        # Create an empty file or just return?
        # Let's clean up old file if it exists or just do nothing.
        # But user might expect a file.
        with open(path, "w", newline="", encoding="utf-8") as f:
            pass # Create empty file
        return

    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube Channel Video Scraper")
    parser.add_argument(
        "--api_key", default=DEFAULT_API_KEY, help="YouTube Data API Key"
    )
    parser.add_argument(
        "--channel_id", default=DEFAULT_CHANNEL_ID, help="Target YouTube Channel ID"
    )
    parser.add_argument(
        "--keywords",
        nargs="*",
        help="Optional: Filter the downloaded list by these keywords (local filter).",
    )
    parser.add_argument(
        "--output",
        default="youtube_channel_dump.csv",
        help="Output CSV filename",
    )
    parser.add_argument(
        "--no-stats",
        action="store_true",
        help="Skip fetching video statistics (views/likes) to save time/quota.",
    )

    args = parser.parse_args()

    print(f"Using Channel ID: {args.channel_id}")
    print("Fetching uploads playlist ID...")
    try:
        uploads_playlist_id = get_uploads_playlist_id(args.api_key, args.channel_id)
    except Exception as e:
        print(f"Error fetching channel: {e}")
        return

    print(f"Uploads playlist ID: {uploads_playlist_id}")
    print("Fetching all videos... (This may take a while for large channels)")
    
    # We could add a simple progress indicator here if we wanted to change the get_all... function,
    # but for now we'll stick to the simple implementation unless requested.
    videos = get_all_videos_from_uploads_playlist(args.api_key, uploads_playlist_id)
    print(f"Total videos fetched: {len(videos)}")

    if not args.no_stats:
        print(f"Enriching {len(videos)} videos with statistics. This will consume ~{len(videos)//50} additional quota units.")
        enrich_with_video_stats(args.api_key, videos)
    else:
        print("Skipping statistics enrichment.")

    if args.keywords:
        print(f"Filtering locally by keywords: {args.keywords}")
        before_count = len(videos)
        videos = filter_by_title_keywords_local(videos, args.keywords)
        print(f"Filtered {before_count} -> {len(videos)} videos.")
    
    write_csv(args.output, videos)
    print(f"Done. Saved to {args.output}")


if __name__ == "__main__":
    main()