# YouTube Scraper Playbook

This project contains a suite of tools to scrape a massive YouTube channel (78k+ videos) efficiently by combining **Bulk Downloading** (for recent videos) and **Surgical Searching** (for history).

## The Scripts

1.  **`scraper_recent_20k.py`** ("The Dragnet")
    -   **What it does**: Downloads the *entire* list of the channel's most recent 20,000 videos.
    -   **Cost**: Low/Medium (~400 quota).
    -   **Use case**: Step 1 for any project. Get the recent 2 years of data locally.

2.  **`filter_dump.py`** ("The Sieve")
    -   **What it does**: Filters a CSV dump for specific keywords.
    -   **Cost**: Free (Local).
    -   **Use case**: Step 2. Extract your topic from the big dragnet.

3.  **`smart_scraper.py`** ("The Time Traveler")
    -   **What it does**: Reads your filtered CSV, finds the oldest date, and searches *backwards* in time using the API.
    -   **Cost**: Variable (100 quota per search request).
    -   **Use case**: Step 3. Fill in the gaps beyond the 20k limit.

---

## The "Golden Workflow" for New Keywords

If you want to start a new search (e.g., for "UFO"):

### Step 1: Update the Master Dump (Optional)
If your `youtube_channel_dump.csv` is old or deleted, grab a fresh execution of the last 20,000 videos.
```bash
.venv/bin/python scraper_recent_20k.py --output master_recent_20k.csv --no-stats
```
*(Note: `--no-stats` makes this blazing fast. You can enrich later if needed, or omit it to look up view counts.)*

### Step 2: Create your Topic File
Extract the relevant videos from the master dump.
```bash
.venv/bin/python filter_dump.py master_recent_20k.csv ufo_videos.csv --keywords "UFO" "UAP" "Aliens"
```
*Result: `ufo_videos.csv` now contains all recent matches.*

### Step 3: Go Back in Time
Point the smart scraper at your new topic file. It will see the oldest date in `ufo_videos.csv` and start searching backwards from there.
```bash
.venv/bin/python smart_scraper.py \
  --output ufo_videos.csv \
  --keywords "UFO" "UAP" "Aliens" \
  --start_date 2010-01-01
```
*Result: It appends older history to your file until it hits 2010.*

### Step 4: Done
You now have a complete dataset in `ufo_videos.csv` covering 2010 to Now.
