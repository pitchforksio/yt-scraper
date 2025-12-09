import csv
import os
import re
import time
import requests
import argparse

import json
from pathlib import Path

# Configuration
INPUT_CSV = "../data/1_video_lists/coulthart_reality_check.csv"
OUTPUT_DIR = "../data/2_transcripts_raw"
CONFIG_FILE = "../scraper_config.json"
TRANSCRIPT_API_ENDPOINT = "https://transcriptapi.com/api/v2/youtube/transcript"

def load_config():
    """Load configuration from JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, CONFIG_FILE)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

config = load_config()
API_KEY = config.get("transcript_api_key") or config.get("supadata_api_key", "")
if not config.get("transcript_api_key") and API_KEY:
    print("⚠️  Warning: Using 'supadata_api_key' from config. Please rename key to 'transcript_api_key'.")

def sanitize_filename(name):
    """Sanitize title for filename."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name[:50]

def get_transcript_api(video_id):
    """Fetch transcript from TranscriptAPI.com"""
    # API expects video_url, but usually handles IDs too. 
    # Safest to assume full URL or just try ID if docs say so. 
    # Docs example: ...?video_url=dQw4w9WgXcQ 
    # It takes the ID as 'video_url' param in the example!
    
    url = f"{TRANSCRIPT_API_ENDPOINT}?video_url={video_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # Parse sections
            # Format: {"transcript": [{"text": "...", ...}]}
            if "transcript" in data:
                # Concatenate all text segments
                full_text = " ".join([seg.get("text", "") for seg in data["transcript"]])
                return full_text
            return None
        else:
            print(f"   Error {response.status_code}: {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"   Request failed: {e}")
        return None

def main():
    # Setup directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, INPUT_CSV)
    output_path = os.path.join(base_dir, OUTPUT_DIR)
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Validation
    if not API_KEY:
        print("❌ Error: 'transcript_api_key' not found in scraper_config.json")
        return

    # Read CSV
    print(f"Reading from {INPUT_CSV}...")
    videos_to_process = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("title", "").lower()
            if "q&a" in title or "question" in title or "answer" in title:
                videos_to_process.append(row)
    
    print(f"Found {len(videos_to_process)} Q&A videos total.")
    
    processed_count = 0
    success_count = 0
    
    for i, video in enumerate(videos_to_process, 1):
        vid = video["video_id"]
        title = video.get("title", "unknown_title")
        safe_title = sanitize_filename(title)
        filename = f"{vid}_{safe_title}.txt"
        file_path = os.path.join(output_path, filename)
        
        # Check if already exists in ANY bucket
        project_root = Path(base_dir).parent
        
        possible_locs = [
            project_root / "data/2_transcripts_raw" / filename,
            project_root / "data/3_filtering/archive_discarded" / filename,
            project_root / "data/3_filtering/accepted" / filename,
            project_root / "data/4_extraction/queue" / filename,
            project_root / "data/4_extraction/processed" / filename,
            project_root / "data/4_extraction/failed" / filename,
        ]
        
        exists = False
        for loc in possible_locs:
            if loc.exists():
                exists = True
                break
        
        if exists:
            continue
            
        print(f"[{i}/{len(videos_to_process)}] Fetching fallback for {vid}: {title[:30]}...")
        
        transcript_text = get_transcript_api(vid)
        
        if transcript_text:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(transcript_text)
            
            print("   ✓ Success")
            success_count += 1
        else:
            print("   ✗ Failed")
            
        # Rate limit / niceness
        time.sleep(1)
        
    print(f"\nFallback processing complete.")
    print(f"New transcripts downloaded: {success_count}")

if __name__ == "__main__":
    main()
