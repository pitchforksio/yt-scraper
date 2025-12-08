# Git Ignore Strategy

## 📋 Overview

The pipeline generates several types of derived/intermediate files that should not be tracked in git. This document explains the gitignore strategy.

---

## 🚫 What's Ignored

### 1. **Subject Configs** (`config_runs/`)

**Ignored:**
- `*.json` (except `template.json`)
- e.g., `ross_coulthart.json`, `lue_elizondo.json`

**Tracked:**
- `template.json` - Template for creating new configs
- `README.md` - Documentation
- `.gitignore` - Ignore rules

**Why:** Subject configs may contain sensitive UUIDs and custom settings.

---

### 2. **Filtered Transcripts** (`get_transcripts/transcripts_filtered/`)

**Ignored:**
- `*.txt` - All transcript files

**Tracked:**
- `README.md` - Documentation
- `.gitignore` - Ignore rules

**Why:** These are derived files (copies from `../transcripts/`) that can be regenerated in seconds.

**Regenerate:**
```bash
.venv/bin/python scripts/filter_qa_transcripts.py
```

---

### 3. **Q&A Extractions** (`outputs/qa_extractions/`)

**Ignored:**
- `*.json` - All GPT-4o extraction outputs

**Tracked:**
- `README.md` - Documentation
- `.gitignore` - Ignore rules

**Why:** These are expensive API outputs (~$2-3 to regenerate all), but still shouldn't be in version control.

**Regenerate:**
```bash
.venv/bin/python scripts/run_pipeline.py --ross --step extract
# Cost: ~$2-3 for all 15 files
```

---

### 4. **CSV Exports** (`outputs/`)

Currently tracked but could be gitignored if they get large.

The main outputs like `qa_dataset_ross.csv` could be excluded if desired:
```gitignore
# In outputs/.gitignore
qa_dataset_*.csv
```

---

## ✅ What's Tracked

### Code & Scripts
- All Python scripts
- Pipeline orchestration code

### Documentation
- All README files
- Pipeline guides
- Configuration templates

### Configuration Templates
- `config_runs/template.json`
- `scraper_config.json.template`

### Directory Structure
- `.gitignore` files in each directory
- README files explaining each directory

---

## 📁 Directory Summary

```
youtube-scraper/
├── config_runs/
│   ├── .gitignore           ✅ Tracked
│   ├── README.md            ✅ Tracked
│   ├── template.json        ✅ Tracked
│   └── ross_coulthart.json  ❌ Ignored
│
├── get_transcripts/
│   ├── transcripts/         ✅ Tracked (original downloads)
│   └── transcripts_filtered/
│       ├── .gitignore       ✅ Tracked
│       ├── README.md        ✅ Tracked
│       └── *.txt            ❌ Ignored
│
├── outputs/
│   └── qa_extractions/
│       ├── .gitignore       ✅ Tracked
│       ├── README.md        ✅ Tracked
│       └── *.json           ❌ Ignored
│
└── scripts/                 ✅ All tracked
```

---

## 🔄 Regeneration Costs

| Directory | Cost | Time | Command |
|-----------|------|------|---------|
| `transcripts_filtered/` | Free | <1 sec | `filter_qa_transcripts.py` |
| `qa_extractions/` | $2-3 | 20-30 min | `run_pipeline.py --ross --step extract` |
| CSV exports | Free | <1 sec | `run_pipeline.py --ross --step csv` |

---

## 🎯 Benefits

### ✅ **Clean Repository**
- Only essential files tracked
- No large derived files bloating repo

### ✅ **Privacy**
- Subject UUIDs not exposed in public repos
- Custom configs stay local

### ✅ **Reproducibility**
- All outputs can be regenerated from tracked source
- Clear documentation on regeneration process

### ✅ **Efficiency**
- Faster git operations
- Smaller clone size
- No merge conflicts on generated files

---

## 📝 Adding New Ignored Directories

When adding new output directories to the pipeline:

1. **Create `.gitignore`** in the directory:
   ```gitignore
   # Ignore generated files
   *.extension
   
   # Keep structure
   !.gitignore
   !README.md
   ```

2. **Add `README.md`** explaining:
   - What the directory contains
   - How it's generated
   - How to regenerate
   - Cost/time to regenerate

3. **Update this document** with the new directory

---

## 🔍 Checking Ignore Status

```bash
# See what's ignored in a directory
git check-ignore -v directory/*

# See git status of specific paths
git status --short config_runs/ outputs/

# List all .gitignore files
find . -name ".gitignore" -type f
```

---

## ⚠️ Important Notes

1. **`scraper_config.json` is already gitignored** at the root level (contains API keys)
2. **Original transcripts** in `get_transcripts/transcripts/` ARE tracked (source data)
3. **Template files** are always tracked even if they end in `.json`
4. **README files** are always tracked to maintain documentation

This strategy ensures a clean, secure, and reproducible repository! 🔒
