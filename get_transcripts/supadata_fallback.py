import csv
import os
import re
import time
import requests
import argparse

import json

# Configuration
INPUT_CSV = "../scrape_video_ids/coulthart_reality_check.csv"
OUTPUT_DIR = "transcripts"
CONFIG_FILE = "../scraper_config.json"
SUPADATA_ENDPOINT = "https://api.supadata.ai/v1/youtube/transcript"

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
SUPADATA_API_KEY = config.get("supadata_api_key", "")

def sanitize_filename(name):
    """Sanitize title for filename."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name[:50]

def get_transcript_supadata(video_id):
    """Fetch transcript from Supadata."""
    url = f"{SUPADATA_ENDPOINT}?videoId={video_id}&text=true"
    headers = {"x-api-key": SUPADATA_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.text
        else:
            print(f"   Error {response.status_code}: {response.text}")
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
        
        # Check if already exists
        if os.path.exists(file_path):
            continue
            
        print(f"[{i}/{len(videos_to_process)}] Fetching fallback for {vid}: {title[:30]}...")
        
        transcript_text = get_transcript_supadata(vid)
        
        if transcript_text:
            # Add header to match youtube_transcript_api format style roughly or just raw text
            # The current download_transcripts.py saves raw text from formatter.
            # We will save the raw text received from Supadata.
            
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
