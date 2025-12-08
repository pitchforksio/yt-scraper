# YouTube Q&A Scraper

Extract and analyze Q&A content from Ross Coulthart's YouTube videos.

---

## 📁 Project Structure

```
youtube-scraper/
├── scripts/                    # Python scripts
│   ├── extract_qa_gpt4o.py    # GPT-4o Q&A extraction
│   ├── batch_extract_qa.py    # Batch processing
│   ├── upload_to_supabase.py  # Database upload
│   ├── run_scheduler.py       # Main orchestrator
│   └── utils/                 # Utility scripts
│
├── outputs/                   # Generated outputs
│   └── qa_outputs/           # Extracted Q&A JSON files
│
├── docs/                      # Documentation
│   └── CONFIG_README.md      # Configuration guide
│
├── get_transcripts/          # Transcript downloads
│   └── transcripts/          # Downloaded transcript files
│
├── scrape_video_ids/         # Video ID scraping
│
└── Configuration:
    ├── scraper_config.json   # API keys (gitignored)
    ├── requirements.txt      # Python dependencies
    └── Free_Proxy_List.txt  # Proxy list
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `scraper_config.json`:

```json
{
  "openai_api_key": "sk-proj-...",
  "supabase_url": "https://your-project.supabase.co",
  "supabase_service_role_key": "eyJ..."
}
```

### 3. Extract Q&A from Transcripts

```bash
cd scripts
python batch_extract_qa.py
```

### 4. Upload to Supabase

```bash
python upload_to_supabase.py --qa-dir ../outputs/qa_outputs
```

---

## 📝 Main Scripts

### `scripts/extract_qa_gpt4o.py`
Single transcript Q&A extraction using GPT-4o.

**Usage:**
```bash
python extract_qa_gpt4o.py \
  --transcript ../get_transcripts/transcripts/VIDEO_ID.txt \
  --output output.json \
  --api-key sk-...
```

### `scripts/batch_extract_qa.py`
Batch process all transcripts.

**Usage:**
```bash
python batch_extract_qa.py
```

**Output:**
- Individual JSON files in `outputs/qa_outputs/`
- Summary report: `outputs/qa_outputs/batch_summary.json`

### `scripts/upload_to_supabase.py`
Upload Q&A pairs to Supabase database.

**Usage:**
```bash
python upload_to_supabase.py --qa-dir ../outputs/qa_outputs
```

---

## 💰 Cost Estimates

| Operation | Cost |
|-----------|------|
| Extract 1 transcript | ~$0.053 |
| Extract all 91 transcripts | ~$4.82 |
| Upload to Supabase | Free |

---

## 📊 Output Format

Each Q&A JSON file contains:

```json
{
  "pairs": [
    {
      "question": "Full verbatim question...",
      "answer": "Full verbatim answer...",
      "concise_question": "Viewer: Brief question?",
      "concise_answer": "Ross: Brief answer.",
      "q_lines": [59, 65],
      "a_lines": [72, 78],
      "confidence": 0.9
    }
  ],
  "metadata": {
    "model": "gpt-4o",
    "total_pairs": 8,
    "total_tokens": 9521,
    "processing_time": 7.1,
    "cost_estimate": 0.053
  }
}
```

---

## 🔧 Development

### Run from Root Directory

All scripts are designed to run from the `scripts/` directory:

```bash
cd scripts
python batch_extract_qa.py
```

### Project Configuration

Config files are in the root directory and scripts load them from `../scraper_config.json`.

---

## 📚 Documentation

See `docs/CONFIG_README.md` for detailed configuration instructions.

---

## 🐛 Troubleshooting

**"No API key found"**
- Add `openai_api_key` to `scraper_config.json`

**"Module not found"**
- Activate venv: `source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`

**Script path errors**
- Always run scripts from `scripts/` directory
- Paths are configured relative to script location

---

## ✅ Quality Metrics

- **Accuracy:** High - correctly identifies viewer Q&A
- **Multi-question splitting:** Yes
- **No duplicates:** Clean output
- **Average pairs per transcript:** ~8
