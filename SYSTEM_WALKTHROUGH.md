# System Flow: YouTube Q&A Extraction Pipeline

This document outlines the complete workflow of the system, from raw video discovery to database insertion.

## 0. Configuration
**Files**: 
- `scraper_config.json`: API Keys (YouTube, OpenAI, TranscriptAPI, Supabase).
- `config_runs/*.json`: Subject-specific settings (e.g., Ross Coulthart, Lue Elizondo).

---

## 1. Data Acquisition Phase (Getting the Content)
**Goal**: Get a text transcript for every relevant video.

### A. Video Discovery
- **`scraper_recent_20k.py`**: Initial fetch. Gets the most recent ~20,000 videos (or API limit) from a channel.
- **`smart_scraper.py`**: **Backfill Tool**. Finds the *earliest* video in your CSV and searches recursively backwards in time (to 2021) to capture older content that the API limit might have cut off.
- **Input**: YouTube Channel ID
- **Output**: `data/1_video_lists/coulthart_reality_check.csv` (List of video IDs and titles)

### B. Transcript Download (Primary)
- **Script**: `download_transcripts_smart.py`
- **Output**: `data/2_transcripts_raw` (The Inbox).
- **Logic**:
    - Reads the CSV.
    - Uses a **smart proxy system** (Proxifly) to rotate IPs and avoid bans.
    - Saves transcript text to the Inbox.

### C. Transcript Fallback (Secondary)
- **Script**: `get_transcripts/fallback_transcript_api.py`
- **Output**: `data/2_transcripts_raw` (The Inbox).
- **Logic**:
    - Scans for missing transcripts of "Q&A" videos.
    - Calls **TranscriptAPI.com** (replaced Supadata) as a reliable backup (verified +13 transcripts vs Supadata).
    - Fills in the gaps in `data/2_transcripts_raw`.

---

## 2. Processing Phase (The Intelligence)
**Goal**: Turn raw text into structured Q&A data.
**Orchestrator**: `scripts/run_pipeline.py` (Runs the following steps in order)

### Step 1: The Sorting Hat (Filter)
- **Script**: `scripts/filter_qa_transcripts.py`
- **Action**: Sorts the raw inbox.
- **Logic**:
    - **Match**: Moves file to `data/4_extraction/queue`.
    - **No Match**: Moves file to `data/3_filtering/archive_discarded`.
    - **Result**: The Inbox (`data/2_transcripts_raw`) should be empty after this runs.

### Step 2: Extract (The Core)
- **Script**: `scripts/extract_qa_gpt4o.py`
- **Source**: `data/4_extraction/queue`
- **Action**: Sends full transcripts to **GPT-4o** with a specialized system prompt.
- **Rules**:
    - Identifies speaker changes (Host vs. Guest).
    - Splits multi-part questions.
    - Generates "Concise" versions of Q&A.
- **State Management**:
    - **On Success**: Moves source file to `data/4_extraction/processed`.
    - **On Failure**: Moves source file to `data/4_extraction/failed`.
- **"Smart Resume"**: If the JSON output already exists, it skips the expense.
- **Output**: Individual JSON files in `data/5_output/json`.

### Step 3: Export
- **Script**: `scripts/export_qa_csv.py`
- **Action**: Aggregates all individual JSON files into one master CSV.
- **Output**: `data/5_output/csv/qa_dataset_RossCoulthart.csv`

### **Cost & Performance**
- **Cost**: ~$0.05 - $0.20 per transcript (GPT-4o).
- **Time**: ~20-30 minutes for a full batch of 15.
- **Accuracy**: Optimized for speaker attribution and splitting multi-part questions.

---

## 3. Storage Phase (The Destination)
**Goal**: Make data queryable for the app.

### Step 4: Upload
- **Script**: `scripts/upload_to_supabase.py`
- **Action**:
    - Reads the master CSV.
    - Generates UUIDs for questions and answers.
    - **Upserts** (Update/Insert) data to the `staging` schema in Supabase.
- **Destination**: `pitches` (questions) and `answers` tables.

---

## Summary of Data Buckets (`data/`)
| Directory | Content |
|---|---|
| `1_video_lists/` | Input CSVs (Video Lists) |
| `2_transcripts_raw/` | **Inbox**: Initial landing zone for raw downloads |
| `3_filtering/archive_discarded/` | **Archive**: Non-Q&A files (rejected by Sorting Hat) |
| `4_extraction/queue/` | **Queue**: Ready for GPT-4 Processing |
| `4_extraction/processed/` | **Done**: Successfully extracted source files |
| `5_output/json/` | **Results**: The extracted JSON files |
| `5_output/csv/` | **Results**: The final CSV |
