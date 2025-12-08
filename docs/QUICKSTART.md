# Quick Start Guide

## 🚀 Run the Pipeline

### Check Current Status
```bash
.venv/bin/python scripts/check_pipeline_status.py
```

### Option 1: Test Run (2 files, ~$0.30, 2-3 minutes)
```bash
.venv/bin/python scripts/run_pipeline.py --ross --limit 2
```

### Option 2: Full Production Run (15 files, ~$2.50, 20-30 minutes)
```bash
.venv/bin/python scripts/run_pipeline.py --ross
```

### Option 3: Dry Run (no costs, preview only)
```bash
.venv/bin/python scripts/run_pipeline.py --ross --dry-run
```

## 📋 Current Status

✅ **Configuration** - OpenAI API key and Subject ID configured  
✅ **Step 1 Complete** - 15 Q&A transcripts filtered from 91 total  
⏳ **Step 2 Pending** - Ready to extract Q&A pairs with GPT-4o  
⏳ **Step 3 Pending** - Will export to CSV after extraction  
⏳ **Step 4 Pending** - Will generate SQL for Supabase upload  

## 📚 Documentation

- **Full Guide:** `docs/QA_PIPELINE.md`
- **Implementation Summary:** `docs/IMPLEMENTATION_SUMMARY.md`

## 💡 Next Step Recommendation

Start with a small test run to verify everything works:

```bash
.venv/bin/python scripts/run_pipeline.py --ross --limit 2
```

This will:
1. ✅ Use the 15 filtered Q&A transcripts (already done)
2. 🤖 Extract Q&A pairs from first 2 files using GPT-4o
3. 📊 Export results to CSV
4. 📤 Generate SQL for upload

**Cost:** ~$0.20-0.40  
**Time:** 2-3 minutes  
**Output:** ~15-25 Q&A pairs ready for Supabase  

After successful test, run full pipeline with all 15 files! 🎯
