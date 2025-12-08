# Config Runs Directory

This directory contains subject-specific configuration files for the Q&A extraction pipeline.

## 📋 Available Configs

### `ross_coulthart.json`
Configuration for Ross Coulthart Q&A extraction from NewsNation's Reality Check.

**Usage:**
```bash
.venv/bin/python scripts/run_pipeline.py --ross
```

**Filters:** Matches videos with "Q&A", "Q and A", "Questions Answered", etc.

---

### `template.json`
Template for creating new subject configurations.

**To create a new config:**
1. Copy `template.json` to `your_subject.json`  
2. Fill in all fields (subject, source, filter patterns, etc.)
3. Add a shortcut to `scripts/run_pipeline.py` (optional)

**Note:** Subject-specific JSON files (like `ross_coulthart.json`) are gitignored. Only `template.json` is tracked in git.

---

## 🔧 Config Structure

Each config file contains:

### `subject`
```json
{
  "name": "Subject Name",
  "subject_id": "uuid-from-supabase",
  "description": "Brief description"
}
```

### `source`
```json
{
  "channel_id": "YouTube channel ID",
  "channel_name": "Channel Name",
  "show_name": "Show Name",
  "base_transcripts_dir": "path/to/transcripts"
}
```

### `filter`
```json
{
  "type": "filename_patterns",
  "patterns": [
    "regex_pattern_1",
    "regex_pattern_2"
  ],
  "case_sensitive": false,
  "description": "What makes a Q&A video"
}
```

### `extraction`
```json
{
  "model": "gpt-4o",
  "prompt_style": "qa_moderator",
  "speaker_labels": {
    "host": "HostName",
    "viewer": "Viewer",
    "moderator": "ModeratorName"
  },
  "concise_format": true,
  "split_multi_questions": true,
  "min_confidence": 0.7
}
```

### `output`
```json
{
  "filtered_dir": "get_transcripts/transcripts_filtered",
  "extractions_dir": "outputs/qa_extractions",
  "csv_filename": "qa_dataset_subject.csv",
  "naming_prefix": "subject_prefix"
}
```

### `supabase`
```json
{
  "project_id": "supabase_project_id",
  "schema": "staging",
  "tables": {
    "pitches": "staging.pitches",
    "answers": "staging.answers"
  },
  "pitch_type": "QUESTION",
  "default_language": "en",
  "default_status": "PENDING"
}
```

### `processing`
```json
{
  "batch_size": 50,
  "max_retries": 3,
  "timeout_seconds": 60,
  "cost_limit_usd": 10.0
}
```

---

## 🚀 Usage Examples

### Using Named Shortcuts
```bash
# Ross Coulthart (existing)
.venv/bin/python scripts/run_pipeline.py --ross

# Lue Elizondo (if configured)
.venv/bin/python scripts/run_pipeline.py --lue

# With options
.venv/bin/python scripts/run_pipeline.py --ross --limit 2 --dry-run
```

### Using Custom Config
```bash
.venv/bin/python scripts/run_pipeline.py --run-config config_runs/custom.json
```

---

## ➕ Adding New Shortcuts

To add a shortcut like `--yourname`:

1. Create `config_runs/yourname.json`
2. Edit `scripts/run_pipeline.py`:
   ```python
   # In load_run_config() function:
   elif args.yourname:
       run_config_path = config_runs_dir / "yourname.json"
   
   # In parser arguments:
   config_group.add_argument(
       "--yourname",
       action="store_true",
       help="Use YourName config"
   )
   ```

---

## 🎯 Benefits

✅ **Reusable** - Same pipeline for different subjects  
✅ **Isolated** - Each subject has its own config  
✅ **Maintainable** - Easy to update filters and settings  
✅ **Scalable** - Add new subjects without changing core code  
✅ **Traceable** - Clear separation between API keys (global) and subject settings (run)  

---

## 📝 Notes

-  **Global Config (`scraper_config.json`)** contains API keys and shared settings
- **Run Configs (this directory)** contain subject-specific settings only
- Filter patterns use regex - be sure to escape special characters
- Output directories can be unique per subject to avoid conflicts
