import csv
import os
import re
import argparse
import random
import time
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
# ProxyConfig might reside in .proxies or similar depending on version, 
# checking imports from earlier debug. 
# Based on earlier debug output, ProxyConfig is in .proxies but imported in __init__?
# Wait, let's verify import. Earlier `cat __init__.py` didn't explicitly show `ProxyConfig` in `__all__`?
# Actually it did NOT show ProxyConfig in __all__. 
# It imported it `from .proxies import ProxyConfig`.
# But `__all__` list didn't include it. 
# So we might need `from youtube_transcript_api.proxies import ProxyConfig`
# or rely on internal if not exposed.
# Checking typical usage: `YouTubeTranscriptApi(proxy_config=...)`
# Let's try importing from sub-module to be safe.

try:
    from youtube_transcript_api.proxies import ProxyConfig
except ImportError:
    # Fallback or older version logic location
    print("Warning: Could not import ProxyConfig directly.")
    ProxyConfig = None

from youtube_transcript_api.formatters import TextFormatter

# Configuration
DEFAULT_INPUT_CSV = "../scrape_video_ids/coulthart_reality_check.csv"
DEFAULT_OUTPUT_DIR = "transcripts"
DEFAULT_PROXY_FILE = "proxies.txt"

def sanitize_filename(name):
    """Sanitize title for filename."""
    name = re.sub(r'[\\/*?:"<>|]', "", name) # Remove invalid chars
    name = name.replace(" ", "_")
    return name[:50] # Limit length

def load_proxies(filepath):
    """
    Parses proxy list. Supports:
    1. CSV format: ip,anonymityLevel,...,port,protocols,... (Free_Proxy_List.txt)
    2. Simple format: protocol://ip:port
    """
    proxies = []
    if not os.path.exists(filepath):
        print(f"Proxy file {filepath} not found.")
        return []
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            # Check if likely CSV with header
            first_line = f.readline()
            f.seek(0)
            
            # Simple heuristic: header line contains 'ip' and 'port'
            if "ip" in first_line and "port" in first_line:
                reader = csv.DictReader(f)
                for row in reader:
                    # Extract fields
                    ip = row.get("ip", "").replace('"', '').strip()
                    port = row.get("port", "").replace('"', '').strip()
                    protocols = row.get("protocols", "").replace('"', '').strip()
                    
                    if ip and port:
                        # Construct proxy URL. 
                        # 'protocols' might be "socks4", "socks5", "http". 
                        # Requests usually needs 'http' or 'socks5'.
                        proto = "http" 
                        if "socks5" in protocols:
                            proto = "socks5"
                        elif "socks4" in protocols:
                            proto = "socks4"
                        
                        # Format: protocol://ip:port
                        proxy_url = f"{proto}://{ip}:{port}"
                        proxies.append(proxy_url)
            else:
                # Fallback to simple line-based
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        proxies.append(line)
                        
    except Exception as e:
        print(f"Error parsing proxies: {e}")
        
    return proxies

def main():
    parser = argparse.ArgumentParser(description="Download YouTube Transcripts from CSV")
    parser.add_argument("--input", default=DEFAULT_INPUT_CSV, help="Path to CSV containing video_id")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Directory to save .txt files")
    parser.add_argument("--proxies", default=DEFAULT_PROXY_FILE, help="Path to text file with one proxy per line")

    args = parser.parse_args()
    
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        
    proxies = load_proxies(args.proxies)
    if proxies:
        print(f"Loaded {len(proxies)} proxies from {args.proxies}")
    else:
        print(f"No proxies loaded (checked {args.proxies}). Using direct connection.")

    formatter = TextFormatter()
    
    print(f"Reading from {args.input}...")
    videos_to_process = []
    
    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "video_id" in row:
                videos_to_process.append(row)
    
    print(f"Found {len(videos_to_process)} videos. Starting download...")
    
    success_count = 0
    fail_count = 0
    
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

        # Sleep logic (Lower if proxies, higher if not)
        if proxies:
             delay = random.uniform(2, 5) # Proxies let us go faster
        else:
             delay = random.uniform(60, 70) # Slow mode for single IP
             
        print(f"   ...sleeping {delay:.1f}s...")
        time.sleep(delay)
        
        try:
            # Create API instance PER REQUEST if we want to rotate proxies nicely
            # or just pick one.
            current_proxy = None
            yt_api = None
            
            if proxies:
                proxy_url = random.choice(proxies)
                # proxies dict for ProxyConfig? NO, ProxyConfig takes specific args.
                # Actually, looking at source `_api.py`:
                # ProxyConfig takes (http_proxy, https_proxy, etc.)
                # But verifying the class init signature?
                # We don't have it easily. 
                # Alternative: Use the http_client arg with configured session proxies.
                # But standard way is dictionary: {"http": ..., "https": ...}
                pass 
                
                # Let's try the simplest mapping:
                # If the library supports 'proxies' dict directly? 
                # The _api.py showed `__init__(self, proxy_config=..., http_client=...)`
                # And `http_client.proxies = proxy_config.to_requests_dict()`
                
                # We can just manually inject proxies into the session if ProxyConfig is annoying.
                
                proxy_dict = {"http": proxy_url, "https": proxy_url}
                
                # Create a fresh API instance with a custom session/proxy
                # Or use the ProxyConfig class if we can guess it.
                # Let's try importing requests Session and configuring it manually.
                from requests import Session
                session = Session()
                session.proxies.update(proxy_dict)
                yt_api = YouTubeTranscriptApi(http_client=session)
            else:
                yt_api = YouTubeTranscriptApi()

            # Try fetching transcript
            transcript = yt_api.fetch(vid, languages=['en', 'en-US'])
            
            # Format to text
            formatted_text = formatter.format_transcript(transcript)
            
            with open(file_path, "w", encoding="utf-8") as out:
                out.write(formatted_text)
            
            success_count += 1
            
        except Exception as e:
            # Common errors: TranscriptsDisabled, NoTranscriptFound
            print(f"    Failed: {e}")
            fail_count += 1

    print("-" * 40)
    print(f"Download Complete.")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    main()
