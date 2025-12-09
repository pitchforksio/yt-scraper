# Archive Directory

This directory contains files that were used during development, debugging, and one-time fixes. They are **no longer needed for production** but are kept for reference.

## 📁 Directory Structure

### `sql_batches_archive/`
**Purpose**: Batch SQL INSERT files that were already executed to upload Q&A data to Supabase.
- Contains 12 batch files (pitches_batch_1-6.sql, answers_batch_1-6.sql)
- **Status**: ✅ All batches successfully uploaded
- **Safe to delete**: Yes, data is in Supabase

### `temp_sql_files/`
**Purpose**: Temporary SQL files generated during data correction processes.
- `answers_final.sql` - Consolidated answers upload
- `pitches_final.sql` - Consolidated pitches upload  
- `batches_final.json` - Batch metadata
- `validation_results.json` - Historical validation results
- **Status**: ✅ All uploads complete
- **Safe to delete**: Yes

### `debug_scripts/`
**Purpose**: One-time debug scripts used during development.
- `audit_qa_files.py` - File audit utility
- **Safe to delete**: Yes

### `one_time_scripts/`
**Purpose**: Scripts created to fix specific issues or data problems.
- `fix_body_md.py` - Fixed truncated body_md fields in Supabase
- `filter_empty_updates.py` - Filtered out empty SQL updates
- `split_sql_updates.py` - Split large SQL files into batches
- `extract_sql_from_json.py` - JSON to SQL converter
- `cat_batches.py` - Batch file concatenation
- `filter_sql_batches.py` - Batch filtering utility
- `archive_files.py` - File archival utility
- `analyze_body_md_issues.py` - Data quality analysis
- `quick_body_md_analysis.py` - Quick data check
- **Status**: ✅ All fixes applied successfully
- **Safe to delete**: Yes, issues resolved

### Legacy Directories (From Previous Cleanup)
- `qa_extractions_legacy/` - Old extraction output format
- `transcripts_legacy/` - Old transcript storage
- `transcripts_filtered_legacy/` - Old filtering approach
- `transcript_unavailable_legacy/` - Old unavailable transcript tracking

## 🗑️ Deletion Schedule

**Recommendation**: Keep for 30 days, then delete entire `to_delete/` directory.

**Last Archive Date**: 2025-12-08

## 🔍 If You Need to Restore

If you ever need any of these files:
1. Check git history (some may be committed)
2. Recreate from documentation in `docs/`
3. Most scripts can be regenerated from the production pipeline

---

**Note**: This archive was created to clean up the project root and keep only production-ready files.
