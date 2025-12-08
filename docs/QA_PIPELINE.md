# Q&A Extraction Pipeline

Complete automated pipeline for extracting Q&A pairs from YouTube transcripts and uploading to Supabase.

## 📋 Overview

This pipeline processes Ross Coulthart Q&A video transcripts through 4 stages:

1. **Filter** - Identify Q&A transcripts from all transcripts
2. **Extract** - Use GPT-4o to extract structured Q&A pairs  
3. **Export** - Convert JSON output to CSV matching Supabase schema
4. **Upload** - Batch insert to Supabase staging.pitches and staging.answers

## 🚀 Quick Start

### Run Full Pipeline

```bash
.venv/bin/python scripts/run_pipeline.py
```

This will:
- Filter 15 Q&A transcripts from 91 total
- Extract Q&A pairs using GPT-4o (~$2.50 estimated cost)
- Export to CSV
- Generate SQL for Supabase upload

### Test with Limited Files

```bash
# Dry run (no API calls, no uploads)
.venv/bin/python scripts/run_pipeline.py --dry-run --limit 2

# Process only 2 files
.venv/bin/python scripts/run_pipeline.py --limit 2
```

### Run Individual Steps

```bash
# Step 1: Filter transcripts only
.venv/bin/python scripts/run_pipeline.py --step filter

# Step 2: Extract Q&A pairs only  
.venv/bin/python scripts/run_pipeline.py --step extract --limit 5

# Step 3: Export to CSV only
.venv/bin/python scripts/run_pipeline.py --step csv

# Step 4: Upload to Supabase only
.venv/bin/python scripts/run_pipeline.py --step upload
```

## 📁 Directory Structure

```
youtube-scraper/
├── get_transcripts/
│   ├── transcripts/              # All transcripts (91 files)
│   └── transcripts_filtered/     # Q&A only (15 files)
├── outputs/
│   ├── qa_extractions/           # GPT-4o JSON outputs
│   └── qa_dataset.csv            # Final CSV for upload
└── scripts/
    ├── filter_qa_transcripts.py  # Step 1: Filter
    ├── extract_qa_gpt4o.py       # Step 2: Extract
    ├── export_qa_csv.py          # Step 3: Export
    ├── upload_to_supabase.py     # Step 4: Upload
    └── run_pipeline.py           # Master orchestrator
```

## 🎯 Pipeline Details

### Step 1: Filter Q&A Transcripts

**Script:** `filter_qa_transcripts.py`

Scans filenames for Q&A patterns:
- "Q&A" (case-insensitive)
- "Q and A"
- "Questions Answered"
- "Viewer Questions"

**Output:** 15 Q&A transcripts copied to `get_transcripts/transcripts_filtered/`

**Usage:**
```bash
.venv/bin/python scripts/filter_qa_transcripts.py --dry-run  # Preview
.venv/bin/python scripts/filter_qa_transcripts.py            # Execute
```

### Step 2: Extract Q&A Pairs (GPT-4o)

**Script:** `extract_qa_gpt4o.py`

Uses GPT-4o to extract structured Q&A pairs from each transcript.

**Features:**
- Full transcript processing (no chunking)
- Line-numbered input for precise extraction
- Concise question/answer rephrasing
- Speaker attribution (Viewer: / Ross:)
- Multi-question splitting
- Confidence scores

**Output Format:**
```json
{
  "pairs": [
    {
      "question": "Full question text...",
      "answer": "Full answer text...",
      "concise_question": "Viewer: [concise version]",
      "concise_answer": "Ross: [concise version]",
      "q_lines": [59, 65],
      "a_lines": [72, 100],
      "confidence": 0.9,
      "source": "gpt4o_full"
    }
  ],
  "metadata": {
    "model": "gpt-4o",
    "total_pairs": 12,
    "total_tokens": 15000,
    "processing_time": 8.5,
    "cost_estimate": 0.075
  }
}
```

**Usage:**
```bash
.venv/bin/python scripts/extract_qa_gpt4o.py \
  --transcript get_transcripts/transcripts_filtered/VIDEOID_title.txt \
  --output outputs/qa_extractions/VIDEOID_title_qa.json \
  --api-key YOUR_OPENAI_KEY
```

**Cost:** ~$0.05-0.20 per transcript (varies by length)

### Step 3: Export to CSV

**Script:** `export_qa_csv.py`

Converts GPT-4o JSON outputs to CSV matching Supabase schema.

**CSV Format:**
Each Q&A pair generates 2 rows:

1. **Pitch Row** (Question):
   - `table`: "pitches"
   - `id`: UUID (generated client-side)
   - `subject_id`: Ross Coulthart UUID
   - `type`: "QUESTION"
   - `body_md`: Full question text
   - `concise`: First 100 chars
   - `language`: "en"
   - `canonical_source_url`: YouTube URL
   - `status`: "PENDING"

2. **Answer Row** (linked to pitch):
   - `table`: "answers"
   - `id`: UUID (generated client-side)
   - `pitch_id`: Links to question UUID
   - `body_md`: Full answer text
   - `source_url`: YouTube URL
   - `status`: "PENDING"

**Usage:**
```bash
# Single file
.venv/bin/python scripts/export_qa_csv.py \
  --input outputs/qa_extractions/VIDEOID_qa.json \
  --output outputs/qa_dataset.csv \
  --subject-id 9d6f9ab7-5f62-4977-a7ab-728fd19fe4df

# Batch mode (all JSONs in directory)
.venv/bin/python scripts/export_qa_csv.py \
  --input outputs/qa_extractions/ \
  --output outputs/qa_dataset.csv \
  --subject-id 9d6f9ab7-5f62-4977-a7ab-728fd19fe4df \
  --batch
```

### Step 4: Upload to Supabase

**Script:** `upload_to_supabase.py`

Generates SQL batch inserts for Supabase staging schema.

**Features:**
- Reads CSV from Step 3
- Generates batched SQL INSERTs (50 rows/batch)
- Proper SQL escaping
- Foreign key linking (pitch_id → answers)

**Target:**
- **Project:** `xajmsivavyqbjkfuwfdn` (pitchforks)
- **Schema:** `staging`
- **Tables:** `staging.pitches`, `staging.answers`

**Usage:**
```bash
# Dry run (preview SQL)
.venv/bin/python scripts/upload_to_supabase.py \
  --input outputs/qa_dataset.csv \
  --dry-run

# Generate SQL for MCP execution
.venv/bin/python scripts/upload_to_supabase.py \
  --input outputs/qa_dataset.csv
```

**Note:** This script generates SQL statements. Execute via MCP in AI assistant.

## ⚙️ Configuration

**File:** `scraper_config.json`

Required fields:
```json
{
  "openai_api_key": "sk-...",
  "supabase": {
    "subject_id": "9d6f9ab7-5f62-4977-a7ab-728fd19fe4df"
  }
}
```

## 📊 Expected Results

For 15 Q&A transcripts (~45-60 minutes each):

- **Total Q&A pairs:** ~150-250 (varies by video)
- **CSV rows:** ~300-500 (2 rows per pair)
- **GPT-4o cost:** ~$2-3 total
- **Processing time:** ~15-25 minutes
- **SQL batches:** ~6-10 batches

## 🔧 Troubleshooting

### "OpenAI API key not found"
Add to `scraper_config.json`:
```json
{
  "openai_api_key": "sk-proj-..."
}
```

### "No transcripts found in filtered directory"
Run Step 1 first:
```bash
.venv/bin/python scripts/filter_qa_transcripts.py
```

### "subject_id not configured"
Add to `scraper_config.json`:
```json
{
  "supabase": {
    "subject_id": "9d6f9ab7-5f62-4977-a7ab-728fd19fe4df"
  }
}
```

### Rate limits / API errors
Use `--limit` to process fewer files at a time:
```bash
.venv/bin/python scripts/run_pipeline.py --limit 5
```

## 📈 Cost Estimation

**GPT-4o Pricing:** ~$5/1M tokens

- **Average transcript:** 10-15K tokens
- **Cost per file:** $0.05-0.20
- **15 files total:** ~$2-3

Use `--dry-run` or `--limit 1` to test before full batch.

## 🎯 Next Steps

After running the pipeline:

1. Review `outputs/qa_dataset.csv` for quality
2. Execute SQL batches via MCP in AI assistant
3. Verify uploads in Supabase staging schema
4. Run advisors to check for missing RLS policies:
   ```bash
   # Via MCP in AI assistant
   mcp_get_advisors --project-id xajmsivavyqbjkfuwfdn --type security
   ```

## 📝 Notes

- **Idempotency:** Step 1 can be re-run safely (overwrites filtered dir)
- **Incremental:** Steps 2-4 can process new files incrementally
- **Dry run:** Always test with `--dry-run` first
- **Limits:** Use `--limit N` for testing with small batches
- **MCP Required:** Final upload requires MCP-enabled environment
