#!/usr/bin/env python3
"""
Export GPT-4o extracted Q&A pairs to CSV format for Supabase upload.

Maps the JSON output from extract_qa_gpt4o.py to the exact schema
required by staging.pitches and staging.answers tables.
"""
import json
import csv
import uuid
import argparse
from pathlib import Path
from typing import List, Dict, Any


def extract_video_id(source_file: str) -> str:
    """Extract YouTube video ID from filename."""
    # Format: {video_id}_Title_Of_Video.txt
    if '_' in source_file:
        return source_file.split('_')[0]
    return ""


def create_source_url(video_id: str) -> str:
    """Generate YouTube URL from video ID."""
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return ""


def json_to_csv_rows(
    json_data: Dict[str, Any],
    source_file: str,
    subject_id: str
) -> List[Dict[str, str]]:
    """
    Convert GPT-4o JSON output to CSV rows matching Supabase schema.
    
    Each Q&A pair generates TWO rows:
    1. One for staging.pitches (the question)
    2. One for staging.answers (the answer, linked to pitch)
    
    Args:
        json_data: Output from extract_qa_gpt4o.py
        source_file: Original transcript filename
        subject_id: Supabase subject_id (Ross Coulthart)
        
    Returns:
        List of dicts ready for CSV export
    """
    video_id = extract_video_id(source_file)
    source_url = create_source_url(video_id)
    
    rows = []
    
    for pair in json_data.get("pairs", []):
        # Generate UUIDs client-side (required by staging schema)
        pitch_id = str(uuid.uuid4())
        answer_id = str(uuid.uuid4())
        
        # Extract text - Ensure we get both full and concise versions
        full_question = pair.get("question", "")
        concise_question = pair.get("concise_question", "")
        
        full_answer = pair.get("answer", "")
        concise_answer = pair.get("concise_answer", "")
        
        # Fallback if concise missing (shouldn't happen with valid data)
        if not concise_question:
            concise_question = full_question
        if not concise_answer:
            concise_answer = full_answer
        
        # Confidence score
        confidence = pair.get("confidence", 0.9)
        
        # ROW 1: Pitch (Question)
        pitch_row = {
            "table": "pitches",
            "id": pitch_id,
            "subject_id": subject_id,
            "pitch_id": "",  # Empty for pitches
            "type": "QUESTION",
            "body_md": full_question,
            "concise": concise_question,
            "language": "en",
            "canonical_source_url": source_url,
            "source_url": source_url,
            "status": "PENDING",
            "confidence": str(confidence),
            "source_file": source_file
        }
        
        # ROW 2: Answer (linked to pitch)
        answer_row = {
            "table": "answers",
            "id": answer_id,
            "subject_id": "",  # Empty for answers
            "pitch_id": pitch_id,
            "type": "",  # Empty for answers
            "body_md": full_answer,
            "concise": concise_answer,  # Now populating concise field (concise_answer from JSON)
            "language": "",  # Empty for answers
            "canonical_source_url": "",  # Empty for answers
            "source_url": source_url,
            "status": "PENDING",
            "confidence": str(confidence),
            "source_file": source_file
        }
        
        rows.append(pitch_row)
        rows.append(answer_row)
    
    return rows


def export_to_csv(
    input_json: str,
    output_csv: str,
    subject_id: str,
    source_file: str = None
) -> Dict[str, int]:
    """
    Convert Q&A JSON to CSV format.
    
    Args:
        input_json: Path to GPT-4o output JSON
        output_csv: Path to output CSV file
        subject_id: Supabase subject_id
        source_file: Original transcript filename (optional, can extract from JSON)
        
    Returns:
        Stats dict with counts
    """
    # Load JSON
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Determine source file
    if not source_file:
        # Try to extract from metadata
        source_file = data.get("metadata", {}).get("source_file", Path(input_json).stem)
    
    # Convert to CSV rows
    rows = json_to_csv_rows(data, source_file, subject_id)
    
    # Write CSV
    if rows:
        fieldnames = rows[0].keys()
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    # Calculate stats
    pitch_count = sum(1 for row in rows if row["table"] == "pitches")
    answer_count = sum(1 for row in rows if row["table"] == "answers")
    
    return {
        "total_rows": len(rows),
        "pitches": pitch_count,
        "answers": answer_count,
        "qa_pairs": pitch_count  # Should equal answer_count
    }


def batch_export(
    input_dir: str,
    output_csv: str,
    subject_id: str,
    pattern: str = "*.json"
) -> Dict[str, int]:
    """
    Batch export all JSON files in a directory to a single CSV.
    
    Args:
        input_dir: Directory containing GPT-4o JSON outputs
        output_csv: Path to output CSV file
        subject_id: Supabase subject_id
        pattern: File pattern to match (default: *.json)
        
    Returns:
        Aggregate stats
    """
    input_path = Path(input_dir)
    json_files = list(input_path.glob(pattern))
    
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {input_dir} matching {pattern}")
    
    all_rows = []
    total_pairs = 0
    
    print(f"\n📂 Found {len(json_files)} JSON files to process\n")
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract source filename from JSON or filename
        source_file = data.get("metadata", {}).get("source_file", json_file.stem)
        
        # Convert to rows
        rows = json_to_csv_rows(data, source_file, subject_id)
        all_rows.extend(rows)
        
        pairs = len(rows) // 2  # Each pair = 2 rows (pitch + answer)
        total_pairs += pairs
        
        print(f"   ✓ {json_file.name}: {pairs} pairs")
    
    # Write combined CSV
    if all_rows:
        fieldnames = all_rows[0].keys()
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
    
    return {
        "files_processed": len(json_files),
        "total_rows": len(all_rows),
        "qa_pairs": total_pairs
    }


def main():
    parser = argparse.ArgumentParser(
        description="Export Q&A JSON to CSV for Supabase upload"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input JSON file or directory"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output CSV file"
    )
    parser.add_argument(
        "--subject-id",
        required=True,
        help="Supabase subject_id (e.g., Ross Coulthart's UUID)"
    )
    parser.add_argument(
        "--source-file",
        help="Original transcript filename (optional)"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all JSON files in input directory"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("📊 Q&A JSON → CSV Converter")
    print("=" * 80)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Subject ID: {args.subject_id}")
    
    try:
        if args.batch:
            # Batch mode: process directory
            stats = batch_export(
                args.input,
                args.output,
                args.subject_id
            )
            print(f"\n{'=' * 80}")
            print(f"✅ Batch export complete!")
            print(f"   Files processed: {stats['files_processed']}")
            print(f"   Q&A pairs: {stats['qa_pairs']}")
            print(f"   Total CSV rows: {stats['total_rows']}")
        else:
            # Single file mode
            stats = export_to_csv(
                args.input,
                args.output,
                args.subject_id,
                args.source_file
            )
            print(f"\n{'=' * 80}")
            print(f"✅ Export complete!")
            print(f"   Q&A pairs: {stats['qa_pairs']}")
            print(f"   Total CSV rows: {stats['total_rows']}")
        
        print(f"   💾 Saved to: {args.output}")
        print(f"{'=' * 80}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
