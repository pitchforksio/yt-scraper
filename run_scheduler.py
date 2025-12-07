import sys
import subprocess
import os
import json
import time

# Helper to run scripts
def run_script(script_path, args=None):
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    print(f"\n>>> Running {script_path} {' '.join(args) if args else ''}")
    try:
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {e}")
        return False

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_PATH = os.path.join(BASE_DIR, "scraper_config.json")
    
    # 1. Load config
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
        
    csv_filename = config['scraping']['csv_path']
    transcripts_dir = config['scraping']['transcripts_dir']
    
    # Resolve paths
    # scraper_config.json usually assumes paths relative to the scraper root or absolute.
    # Let's verify CSV path. 
    # If csv_path is just filename, assume it's in scrape_video_ids/ (historical context) or root?
    # Config default was "coulthart_reality_check.csv".
    # scheduled_scraper writes to it.
    # Let's stick to absolute paths to be safe.
    
    # We will assume the CSV is in scrape_video_ids folder for legacy reasons
    CSV_PATH = os.path.join(BASE_DIR, "scrape_video_ids", csv_filename)
    if not os.path.exists(os.path.dirname(CSV_PATH)):
         CSV_PATH = os.path.join(BASE_DIR, csv_filename) # Fallback to root
    
    TRANSCRIPTS_PATH = os.path.join(BASE_DIR, "get_transcripts", transcripts_dir)
    if not os.path.exists(TRANSCRIPTS_PATH):
        os.makedirs(TRANSCRIPTS_PATH)
        
    print(f"Work Flow Started.")
    print(f"CSV: {CSV_PATH}")
    print(f"Transcripts: {TRANSCRIPTS_PATH}")
    
    # 2. Scrape New Videos
    # scheduled_scraper.py is in scrape_video_ids/
    scraper_script = os.path.join(BASE_DIR, "scrape_video_ids", "scheduled_scraper.py")
    if not run_script(scraper_script, ["--config", CONFIG_PATH]):
        print("Scraping failed.")
        return

    # 3. Download Transcripts
    # download_transcripts.py is in get_transcripts/
    downloader_script = os.path.join(BASE_DIR, "get_transcripts", "download_transcripts.py")
    # It takes --input (csv) and --output (dir)
    if not run_script(downloader_script, ["--input", CSV_PATH, "--output", TRANSCRIPTS_PATH]):
        print("Download failed.")
        return

    # 4. Extract QA Pairs
    extractor_script = os.path.join(BASE_DIR, "extract_qa_pairs_configurable.py")
    qa_output = os.path.join(BASE_DIR, "qa_dataset.json")
    if not run_script(extractor_script, ["--config", CONFIG_PATH, "--input_dir", TRANSCRIPTS_PATH, "--output", qa_output]):
        print("Extraction failed.")
        return

    # 5. Self-Annealing / Analysis
    # Placeholder for the robust verification step
    print("\n>>> Running Analysis & Optimization (Self-Annealing)...")
    # optimization_script = os.path.join(BASE_DIR, "anneal_filters.py")
    # run_script(optimization_script)
    print("Optimization complete (Placeholder).")

    # 6. Upload to Supabase
    uploader_script = os.path.join(BASE_DIR, "upload_to_supabase.py")
    if config["supabase"]["auth_token"] == "YOUR_AUTH_TOKEN":
        print("Skipping Supabase Upload: Auth Token not configured.")
    else:
        # Default to dry-run for safety unless explicitly changed
        if not run_script(uploader_script, ["--config", CONFIG_PATH, "--input", qa_output, "--dry-run"]):
            print("Upload failed.")
            return

    print("\nWorkflow Finished Successfully.")

if __name__ == "__main__":
    main()
