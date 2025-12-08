#!/usr/bin/env python3
"""
Upload Q&A pairs to Supabase staging schema from CSV input.

Accepts CSV export from export_qa_csv.py and performs batch inserts
to staging.pitches and staging.answers tables.
"""
import csv
import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def escape_sql(text: str) -> str:
    """Escape single quotes for SQL."""
    if text is None:
        return None
    return text.replace("'", "''")


def build_pitch_insert(row: Dict[str, str]) -> str:
    """Build SQL INSERT statement for staging.pitches."""
    return f"""INSERT INTO staging.pitches (id, subject_id, type, body_md, concise, language, canonical_source_url, status)
VALUES (
    '{row["id"]}',
    '{row["subject_id"]}',
    '{row["type"]}',
    '{escape_sql(row["body_md"])}',
    '{escape_sql(row["concise"])}',
    '{row["language"]}',
    {f"'{escape_sql(row['canonical_source_url'])}'" if row.get('canonical_source_url') else 'NULL'},
    '{row["status"]}'
);"""


def build_answer_insert(row: Dict[str, str]) -> str:
    """Build SQL INSERT statement for staging.answers."""
    return f"""INSERT INTO staging.answers (id, pitch_id, body_md, source_url, status)
VALUES (
    '{row["id"]}',
    '{row["pitch_id"]}',
    '{escape_sql(row["body_md"])}',
    {f"'{escape_sql(row['source_url'])}'" if row.get('source_url') else 'NULL'},
    '{row["status"]}'
);"""


def load_csv_data(csv_path: str) -> Dict[str, List[Dict]]:
    """
    Load CSV and separate into pitches and answers.
    
    Returns:
        Dict with 'pitches' and 'answers' lists
    """
    pitches = []
    answers = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['table'] == 'pitches':
                pitches.append(row)
            elif row['table'] == 'answers':
                answers.append(row)
    
    return {
        'pitches': pitches,
        'answers': answers
    }


def generate_batch_sql(
    pitches: List[Dict],
    answers: List[Dict],
    batch_size: int = 50
) -> List[str]:
    """
    Generate SQL batch insert statements.
    
    Args:
        pitches: List of pitch rows
        answers: List of answer rows
        batch_size: Number of inserts per batch
        
    Returns:
        List of SQL statement batches
    """
    batches = []
    
    # Process pitches in batches
    for i in range(0, len(pitches), batch_size):
        batch = pitches[i:i + batch_size]
        sql_statements = [build_pitch_insert(row) for row in batch]
        batches.append({
            'type': 'pitches',
            'batch_num': i // batch_size + 1,
            'count': len(batch),
            'sql': '\n\n'.join(sql_statements)
        })
    
    # Process answers in batches
    for i in range(0, len(answers), batch_size):
        batch = answers[i:i + batch_size]
        sql_statements = [build_answer_insert(row) for row in batch]
        batches.append({
            'type': 'answers',
            'batch_num': i // batch_size + 1,
            'count': len(batch),
            'sql': '\n\n'.join(sql_statements)
        })
    
    return batches


def upload_csv_to_supabase(
    csv_path: str,
    project_id: str,
    dry_run: bool = False,
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Upload CSV data to Supabase.
    
    Args:
        csv_path: Path to CSV file from export_qa_csv.py
        project_id: Supabase project ID
        dry_run: If True, only show what would be uploaded
        batch_size: Number of rows per batch insert
        
    Returns:
        Stats dict
    """
    # Load CSV
    data = load_csv_data(csv_path)
    pitches = data['pitches']
    answers = data['answers']
    
    print(f"\n📊 CSV Data Loaded:")
    print(f"   Pitches: {len(pitches)}")
    print(f"   Answers: {len(answers)}")
    print(f"   Total rows: {len(pitches) + len(answers)}\n")
    
    # Generate batches
    batches = generate_batch_sql(pitches, answers, batch_size)
    
    print(f"📦 Generated {len(batches)} SQL batches (max {batch_size} rows each)\n")
    
    if dry_run:
        print("[DRY RUN MODE] - Showing SQL preview (first batch of each type):\n")
        print("=" * 80)
        
        # Show first pitch batch
        pitch_batch = next((b for b in batches if b['type'] == 'pitches'), None)
        if pitch_batch:
            print(f"\n-- PITCHES BATCH 1 ({pitch_batch['count']} rows) --")
            # Show only first 2 statements
            statements = pitch_batch['sql'].split('\n\n')
            print('\n\n'.join(statements[:2]))
            if len(statements) > 2:
                print(f"\n... and {len(statements) - 2} more pitch inserts")
        
        # Show first answer batch
        answer_batch = next((b for b in batches if b['type'] == 'answers'), None)
        if answer_batch:
            print(f"\n\n-- ANSWERS BATCH 1 ({answer_batch['count']} rows) --")
            # Show only first 2 statements
            statements = answer_batch['sql'].split('\n\n')
            print('\n\n'.join(statements[:2]))
            if len(statements) > 2:
                print(f"\n... and {len(statements) - 2} more answer inserts")
        
        print("\n" + "=" * 80)
        print("\n✅ Dry run complete - no data uploaded")
        
    else:
        print("[LIVE MODE] - Ready to execute via MCP\n")
        print("=" * 80)
        print("To upload, use MCP tools with the following batches:")
        print(f"Project ID: {project_id}")
        print(f"Total batches: {len(batches)}")
        print("\nCall mcp_execute_sql for each batch:")
        
        for i, batch in enumerate(batches, 1):
            print(f"\nBatch {i}/{len(batches)}: {batch['type']} ({batch['count']} rows)")
            print(f"   Characters: {len(batch['sql'])}")
        
        print("\n" + "=" * 80)
        print("\n⚠️  This script generates SQL - execute via MCP in AI assistant")
    
    return {
        'pitches': len(pitches),
        'answers': len(answers),
        'batches': len(batches),
        'total_rows': len(pitches) + len(answers)
    }


def main():
    parser = argparse.ArgumentParser(
        description="Upload Q&A CSV to Supabase staging schema"
    )
    parser.add_argument(
        "--config",
        default="scraper_config.json",
        help="Config file path"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input CSV file from export_qa_csv.py"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview SQL without uploading"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of rows per batch (default: 50)"
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    supabase_config = config.get("supabase", {})
    
    project_id = "xajmsivavyqbjkfuwfdn"  # Hardcoded for pitchforks staging
    subject_id = supabase_config.get("subject_id")
    
    if not subject_id:
        print("❌ Error: subject_id not configured in scraper_config.json")
        sys.exit(1)
    
    # Verify CSV exists
    if not Path(args.input).exists():
        print(f"❌ Error: CSV file not found: {args.input}")
        sys.exit(1)
    
    print("=" * 80)
    print("🚀 Supabase Q&A CSV Upload")
    print("=" * 80)
    print(f"Input CSV: {args.input}")
    print(f"Project ID: {project_id}")
    print(f"Subject ID: {subject_id}")
    print(f"Batch size: {args.batch_size}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    
    try:
        stats = upload_csv_to_supabase(
            args.input,
            project_id,
            dry_run=args.dry_run,
            batch_size=args.batch_size
        )
        
        print(f"\n{'=' * 80}")
        print("📈 Upload Summary:")
        print(f"   Pitches: {stats['pitches']}")
        print(f"   Answers: {stats['answers']}")
        print(f"   Batches: {stats['batches']}")
        print(f"   Total rows: {stats['total_rows']}")
        print(f"{'=' * 80}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
