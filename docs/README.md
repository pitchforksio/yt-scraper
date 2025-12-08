# YouTube Q&A Extraction Pipeline

Automated pipeline to extract, process, and upload Q&A content from YouTube transcripts to Supabase.

> **🚀 Quick Start:** See [QUICKSTART.md](QUICKSTART.md) to run the pipeline immediately!

---

## 📋 Overview

This pipeline processes YouTube Q&A videos through 4 automated stages:

1. **Filter** - Identify Q&A videos from transcripts
2. **Extract** - Use GPT-4o to extract structured Q&A pairs
3. **Export** - Convert to CSV matching Supabase schema
4. **Upload** - Batch insert to Supabase staging tables

**Current Subject:** Ross Coulthart (NewsNation Reality Check)  
**Future Ready:** Easily add new subjects via config files

---

## 🎯 Features

✅ **Multi-subject support** - Configure for different hosts/channels  
✅ **Smart filtering** - Regex patterns identify Q&A videos  
✅ **GPT-4o extraction** - Accurate Q&A pair identification  
✅ **Concise rephrasing** - Clean summaries with speaker attribution  
✅ **Multi-question splitting** - Handles multiple questions per viewer message  
✅ **CSV export** - Supabase-ready format with UUID generation  
✅ **Batch processing** - Process all Q&A videos at once  
✅ **Cost tracking** - Real-time API cost estimation  
✅ **Dry-run mode** - Test without spending money  

---

## 📁 Project Structure

```
youtube-scraper/
├── scripts/
│   ├── run_pipeline.py            # Master orchestrator
│   ├── filter_qa_transcripts.py   # Step 1: Filter
│   ├── extract_qa_gpt4o.py        # Step 2: Extract
│   ├── export_qa_csv.py           # Step 3: Export
│   ├── upload_to_supabase.py      # Step 4: Upload
│   └── check_pipeline_status.py   # Status checker
│
├── config_runs/
│   ├── ross_coulthart.json        # Ross's config (gitignored)
│   ├── template.json              # Template for new subjects
│   └── README.md                  # Config documentation
│
├── get_transcripts/
│   ├── transcripts/               # Source transcripts
│   └── transcripts_filtered/      # Q&A only (generated)
│
├── outputs/
│   ├── qa_extractions/            # GPT-4o outputs (generated)
│   └── qa_dataset_ross.csv        # Final export (generated)
│
├── docs/
│   ├── QA_PIPELINE.md             # Detailed pipeline docs
│   ├── EXTRACTION_EXAMPLE.md      # Sample output
│   └── GITIGNORE_STRATEGY.md      # Git workflow docs
│
├── scraper_config.json            # API keys (gitignored)
├── QUICKSTART.md                  # Get started guide
└── README.md                      # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the template and add your keys:

```bash
cp scraper_config.json.template scraper_config.json
```

Edit `scraper_config.json`:
```json
{
  "openai_api_key": "sk-proj-...",
  "supabase": {
    "subject_id": "uuid-for-ross-coulthart"
  }
}
```

### 3. Run the Pipeline

```bash
# Test with 2 files first (~$0.30, 2-3 minutes)
.venv/bin/python scripts/run_pipeline.py --ross --limit 2

# Full production run (~$2.50, 20-30 minutes)
.venv/bin/python scripts/run_pipeline.py --ross

# Dry run (no costs, preview only)
.venv/bin/python scripts/run_pipeline.py --ross --dry-run
```

### 4. Check Status

```bash
.venv/bin/python scripts/check_pipeline_status.py
```

---

## 📊 Pipeline Stages

### Stage 1: Filter Q&A Transcripts

Scans filenames for Q&A patterns:
- "Q&A" (case-insensitive)
- "Q and A"
- "Questions Answered"
- "Viewer Questions"

**Output:** ~15 Q&A transcripts from 91 total (for Ross Coulthart)

### Stage 2: Extract Q&A Pairs (GPT-4o)

Uses GPT-4o to:
- Identify viewer questions from moderator introductions
- Extract complete answers (can span 70+ lines)
- Create concise rephrased versions
- Add speaker attribution ("Viewer:", "Ross:")
- Split multi-part questions
- Assign confidence scores

**Output:** JSON files with structured Q&A pairs

**Example:**
```json
{
  "pairs": [
    {
      "question": "Full question text...",
      "answer": "Full answer text...",
      "concise_question": "Viewer: Brief version?",
      "concise_answer": "Ross: Brief answer.",
      "confidence": 0.9
    }
  ],
  "metadata": {
    "total_pairs": 12,
    "cost_estimate": 0.075
  }
}
```

### Stage 3: Export to CSV

Converts JSON → CSV with exact Supabase schema:
- Generates UUIDs client-side
- Maps to `staging.pitches` and `staging.answers`
- Links questions to answers via foreign keys
- Adds YouTube source URLs

### Stage 4: Upload to Supabase

Generates SQL batch inserts for:
- `staging.pitches` table (questions)
- `staging.answers` table (answers)

Executed via MCP in AI assistant.

---

## 💰 Cost & Performance

| Metric | Estimate |
|--------|----------|
| **Per transcript** | $0.05-0.20 |
| **All 15 Q&As** | $2-3 total |
| **Processing time** | 20-30 minutes |
| **Q&A pairs extracted** | 150-250 total |

---

## 🎯 Multi-Subject Configuration

The pipeline supports multiple subjects via `config_runs/` directory.

### Current Subjects

```bash
# Ross Coulthart (configured)
.venv/bin/python scripts/run_pipeline.py --ross
```

### Adding New Subjects

1. **Copy template:**
   ```bash
   cp config_runs/template.json config_runs/your_subject.json
   ```

2. **Configure:**
   - Subject name & UUID
   - Filter patterns for Q&A videos
   - Speaker labels
   - Output paths

3. **Run:**
   ```bash
   .venv/bin/python scripts/run_pipeline.py --run-config config_runs/your_subject.json
   ```

See [config_runs/README.md](config_runs/README.md) for details.

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Get started immediately |
| [docs/QA_PIPELINE.md](docs/QA_PIPELINE.md) | Complete pipeline reference |
| [docs/EXTRACTION_EXAMPLE.md](docs/EXTRACTION_EXAMPLE.md) | Sample output |
| [config_runs/README.md](config_runs/README.md) | Subject configuration guide |
| [docs/GITIGNORE_STRATEGY.md](docs/GITIGNORE_STRATEGY.md) | Git workflow |

---

## 🔧 Development

### Run Individual Steps

```bash
# Step 1: Filter only
.venv/bin/python scripts/run_pipeline.py --ross --step filter

# Step 2: Extract only
.venv/bin/python scripts/run_pipeline.py --ross --step extract --limit 5

# Step 3: CSV export only
.venv/bin/python scripts/run_pipeline.py --ross --step csv

# Step 4: Upload only
.venv/bin/python scripts/run_pipeline.py --ross --step upload
```

### Check Pipeline Status

```bash
.venv/bin/python scripts/check_pipeline_status.py
```

Shows:
- Config validation
- File counts
- Next recommended step

---

## 🐛 Troubleshooting

### "OpenAI API key not found"
Add to `scraper_config.json`:
```json
{
  "openai_api_key": "sk-proj-..."
}
```

### "Subject ID not found"
Check `config_runs/ross_coulthart.json` has valid `subject.subject_id`.

### "No transcripts found"
Run filter step first:
```bash
.venv/bin/python scripts/filter_qa_transcripts.py
```

### Rate limits / API errors
Use `--limit` to process fewer files:
```bash
.venv/bin/python scripts/run_pipeline.py --ross --limit 2
```

---

## 🔐 Security

**Gitignored (not tracked):**
- `scraper_config.json` - API keys
- `config_runs/*.json` - Subject configs (except template)
- `get_transcripts/transcripts_filtered/*.txt` - Generated files
- `outputs/qa_extractions/*.json` - GPT-4o outputs

**Tracked in git:**
- All scripts and code
- Documentation
- Templates (`config_runs/template.json`)
- Directory structure (READMEs, .gitignore files)

See [docs/GITIGNORE_STRATEGY.md](docs/GITIGNORE_STRATEGY.md) for details.

---

## 📈 Output Stats (Ross Coulthart)

From 91 total transcripts:
- **15 Q&A videos** identified (16.5%)
- **~150-250 Q&A pairs** extracted
- **~300-500 CSV rows** generated
- **~6-10 SQL batches** for upload

---

## 🎯 Command Reference

```bash
# Help
.venv/bin/python scripts/run_pipeline.py --help

# Full pipeline
.venv/bin/python scripts/run_pipeline.py --ross

# With options
.venv/bin/python scripts/run_pipeline.py --ross --limit 2 --dry-run

# Individual steps
.venv/bin/python scripts/run_pipeline.py --ross --step extract

# Custom config
.venv/bin/python scripts/run_pipeline.py --run-config custom.json

# Status check
.venv/bin/python scripts/check_pipeline_status.py
```

---

## ✅ Quality Metrics

- ✅ **High accuracy** - Correctly identifies viewer Q&A
- ✅ **Multi-question splitting** - Handles complex viewer messages
- ✅ **No duplicates** - Clean output
- ✅ **Speaker attribution** - "Viewer:" and "Ross:" labels
- ✅ **Confidence scores** - Average 0.9 per pair
- ✅ **Line tracking** - Traceable to source transcript

---

## 🚀 Next Steps

1. **Run test:** `.venv/bin/python scripts/run_pipeline.py --ross --limit 2`
2. **Review output:** Check `outputs/qa_dataset_ross.csv`
3. **Full run:** `.venv/bin/python scripts/run_pipeline.py --ross`
4. **Upload:** Ask AI assistant to execute SQL via MCP

---

## 📝 License

See project license for details.

---

**Need help?** See [docs/QA_PIPELINE.md](docs/QA_PIPELINE.md) for comprehensive documentation!
