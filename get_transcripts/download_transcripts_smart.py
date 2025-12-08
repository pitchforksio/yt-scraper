import csv
import os
import re
import argparse
import random
import time
import threading
import queue
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import requests
from requests import Session

# Configuration
DEFAULT_INPUT_CSV = "../scrape_video_ids/coulthart_reality_check.csv"
DEFAULT_OUTPUT_DIR = "transcripts"
PROXIFLY_HTTP_URL = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt"
PROXIFLY_SOCKS5_URL = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt"
TEST_URL = "https://www.google.com"
PROXY_TEST_TIMEOUT = 5
PROXY_QUEUE_SIZE = 10  # Keep this many validated proxies ready

def sanitize_filename(name):
    """Sanitize title for filename."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name[:50]

class ProxyValidator(threading.Thread):
    """Background thread that continuously fetches and validates proxies."""
    
    def __init__(self, proxy_queue, stop_event):
        super().__init__(daemon=True)
        self.proxy_queue = proxy_queue
        self.stop_event = stop_event
        self.tested_proxies = set()
        
    def fetch_fresh_proxies(self):
        """Fetch new proxies from Proxifly."""
        proxies = []
        for url, protocol in [(PROXIFLY_HTTP_URL, "http"), (PROXIFLY_SOCKS5_URL, "socks5")]:
            try:
                response = requests.get(url, timeout=10)
                for line in response.text.strip().split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxy = f"{protocol}://{line}"
                        if proxy not in self.tested_proxies:
                            proxies.append(proxy)
            except:
                pass
        return proxies
    
    def test_proxy(self, proxy_url):
        """Quick test if proxy works with Google."""
        proxy_dict = {"http": proxy_url, "https": proxy_url}
        try:
            response = requests.get(TEST_URL, proxies=proxy_dict, timeout=PROXY_TEST_TIMEOUT)
            return response.status_code == 200
        except:
            return False
    
    def run(self):
        """Continuously validate proxies and add to queue."""
        print("[ProxyValidator] Starting background proxy validation...")
        
        while not self.stop_event.is_set():
            # Only fetch more if queue is getting low
            if self.proxy_queue.qsize() < PROXY_QUEUE_SIZE // 2:
                print(f"[ProxyValidator] Queue low ({self.proxy_queue.qsize()}), fetching fresh proxies...")
                fresh_proxies = self.fetch_fresh_proxies()
                
                if fresh_proxies:
                    print(f"[ProxyValidator] Testing {len(fresh_proxies)} new proxies...")
                    for proxy in fresh_proxies:
                        if self.stop_event.is_set():
                            break
                            
                        self.tested_proxies.add(proxy)
                        if self.test_proxy(proxy):
                            try:
                                self.proxy_queue.put(proxy, timeout=1)
                                print(f"[ProxyValidator] ✓ Added working proxy: {proxy}")
                            except queue.Full:
                                break
                else:
                    print("[ProxyValidator] No new proxies available, waiting...")
                    time.sleep(30)
            else:
                # Queue is healthy, wait a bit
                time.sleep(10)

def main():
    parser = argparse.ArgumentParser(description="Download YouTube Transcripts with Smart Proxy Management")
    parser.add_argument("--input", default=DEFAULT_INPUT_CSV, help="Path to CSV containing video_id")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Directory to save .txt files")
    parser.add_argument("--use-proxies", action="store_true", help="Enable smart proxy system")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    formatter = TextFormatter()
    
    print(f"Reading from {args.input}...")
    videos_to_process = []
    
    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "video_id" in row:
                videos_to_process.append(row)
    
    print(f"Found {len(videos_to_process)} videos. Starting download...")
    
    # Setup proxy system if requested
    proxy_queue = None
    proxy_validator = None
    stop_event = None
    
    if args.use_proxies:
        print("\n[PROXY MODE] Initializing smart proxy system...")
        proxy_queue = queue.Queue(maxsize=PROXY_QUEUE_SIZE)
        stop_event = threading.Event()
        proxy_validator = ProxyValidator(proxy_queue, stop_event)
        proxy_validator.start()
        
        # Give it a moment to find first proxies
        print("[PROXY MODE] Waiting for initial proxies...")
        time.sleep(5)
    
    success_count = 0
    fail_count = 0
    
    try:
        for i, video in enumerate(videos_to_process, 1):
            vid = video["video_id"]
            title = video.get("title", "unknown_title")
            safe_title = sanitize_filename(title)
            filename = f"{vid}_{safe_title}.txt"
            file_path = os.path.join(args.output, filename)
            
            # Skip if already exists
            if os.path.exists(file_path):
                print(f"[{i}/{len(videos_to_process)}] Skipping {vid} (Already downloaded)")
                continue
            
            print(f"[{i}/{len(videos_to_process)}] Downloading {vid}: {title[:30]}...")
            
            # Determine delay and proxy
            if proxy_queue and not proxy_queue.empty():
                # We have a working proxy, use short delay
                delay = random.uniform(2, 5)
                try:
                    proxy_url = proxy_queue.get(timeout=1)
                    print(f"   Using proxy: {proxy_url}")
                    proxy_dict = {"http": proxy_url, "https": proxy_url}
                    session = Session()
                    session.proxies.update(proxy_dict)
                    yt_api = YouTubeTranscriptApi(http_client=session)
                except queue.Empty:
                    # No proxy available, fall back to direct
                    delay = random.uniform(60, 70)
                    yt_api = YouTubeTranscriptApi()
                    print(f"   No proxy available, using direct connection")
            else:
                # No proxy system or queue empty, use slow mode
                delay = random.uniform(60, 70)
                yt_api = YouTubeTranscriptApi()
            
            print(f"   ...sleeping {delay:.1f}s...")
            time.sleep(delay)
            
            try:
                transcript = yt_api.fetch(vid, languages=['en', 'en-US'])
                formatted_text = formatter.format_transcript(transcript)
                
                with open(file_path, "w", encoding="utf-8") as out:
                    out.write(formatted_text)
                
                success_count += 1
                print(f"   ✓ Success")
                
            except Exception as e:
                error_msg = str(e)
                
                # Categorize the error
                is_unavailable = False
                is_blocked = False
                
                # Check for transcript unavailable errors
                if any(phrase in error_msg.lower() for phrase in [
                    'transcripts are disabled',
                    'no transcript found',
                    'could not retrieve a transcript',
                    'subtitles are disabled'
                ]):
                    is_unavailable = True
                
                # Check for blocking/connection errors
                elif any(phrase in error_msg.lower() for phrase in [
                    'ip has been blocked',
                    'too many requests',
                    'connection refused',
                    'proxy error',
                    'timeout'
                ]):
                    is_blocked = True
                
                if is_unavailable:
                    # Create marker file in unavailable folder
                    unavailable_dir = os.path.join(args.output, "../transcript_unavailable")
                    os.makedirs(unavailable_dir, exist_ok=True)
                    marker_file = os.path.join(unavailable_dir, f"{vid}.txt")
                    
                    with open(marker_file, "w", encoding="utf-8") as f:
                        f.write(f"Video ID: {vid}\n")
                        f.write(f"Title: {title}\n")
                        f.write(f"Error: {error_msg[:200]}\n")
                        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    
                    print(f"   ⚠ Transcript unavailable (marked for later)")
                    
                elif is_blocked:
                    fail_count += 1
                    print(f"   ✗ Blocked/Connection Error: {error_msg[:80]}")
                    # Could add longer delay here if needed
                    
                else:
                    fail_count += 1
                    print(f"   ✗ Unknown Error: {error_msg[:80]}")
    
    finally:
        # Cleanup
        if stop_event:
            print("\n[PROXY MODE] Shutting down proxy validator...")
            stop_event.set()
            if proxy_validator:
                proxy_validator.join(timeout=2)
    
    print("-" * 40)
    print(f"Download Complete.")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    
    # Count unavailable
    unavailable_dir = os.path.join(args.output, "../transcript_unavailable")
    if os.path.exists(unavailable_dir):
        unavailable_count = len([f for f in os.listdir(unavailable_dir) if f.endswith('.txt')])
        print(f"Transcript Unavailable: {unavailable_count}")
        print(f"  (See {unavailable_dir}/ for details)")

if __name__ == "__main__":
    main()
