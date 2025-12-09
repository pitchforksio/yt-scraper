#!/usr/bin/env python3
"""
Generate SQL UPDATE statements to fix body_md fields in staging schema.

Reads the repaired JSON files and matches them to database rows to generate
UPDATE statements that will populate body_md with the correct full text.
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse, parse_qs


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    if not url:
        return None
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    return query_params.get('v', [None])[0]


def escape_sql(text: str) -> str:
    """Escape single quotes for SQL."""
    if text is None:
        return None
    return text.replace("'", "''")


def clean_text(text: str) -> str:
    """Remove speaker prefixes like 'Viewer: ' or 'Ross: '."""
    import re
    if not text:
        return text
    # Remove "Name: " pattern at start of string
    return re.sub(r'^[\w\s]{1,30}:\s+', '', text)


def generate_pitch_update(pitch_id: str, full_question: str) -> str:
    """Generate SQL UPDATE for a pitch's body_md field."""
    clean_question = clean_text(full_question)
    return f"""UPDATE staging.pitches 
SET body_md = '{escape_sql(clean_question)}'
WHERE id = '{pitch_id}';"""


def generate_answer_update(answer_id: str, full_answer: str) -> str:
    """Generate SQL UPDATE for an answer's body_md field."""
    clean_answer = clean_text(full_answer)
    return f"""UPDATE staging.answers 
SET body_md = '{escape_sql(clean_answer)}'
WHERE id = '{answer_id}';"""


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate SQL UPDATE statements for body_md fields"
    )
    parser.add_argument(
        '--json-dir',
        default='data/zfinal/ross_coulthart',
        help='Directory containing repaired JSON files'
    )
    parser.add_argument(
        '--output',
        default='body_md_updates.sql',
        help='Output SQL file'
    )
    parser.add_argument(
        '--db-export',
        required=True,
        help='JSON file with database export (pitches and answers with IDs)'
    )
    
    args = parser.parse_args()
    
    # Load database export to get row IDs
    with open(args.db_export, 'r') as f:
        db_data = json.load(f)
    
    pitches = db_data.get('pitches', [])
    answers = db_data.get('answers', [])
    
    # Create lookup by (video_id, concise) -> row
    pitch_lookup = {}
    for pitch in pitches:
        video_id = extract_video_id(pitch.get('canonical_source_url', ''))
        concise = clean_text(pitch.get('concise', ''))
        if video_id and concise:
            key = (video_id, concise)
            pitch_lookup[key] = pitch
    
    answer_lookup = {}
    for answer in answers:
        # Answers need pitch lookup to get video_id
        pitch_id = answer.get('pitch_id')
        concise = clean_text(answer.get('concise', ''))
        if pitch_id and concise:
            # Find the pitch
            pitch = next((p for p in pitches if p['id'] == pitch_id), None)
            if pitch:
                video_id = extract_video_id(pitch.get('canonical_source_url', ''))
                if video_id:
                    key = (video_id, concise)
                    answer_lookup[key] = answer
    
    # Process JSON files
    json_dir = Path(args.json_dir)
    json_files = sorted(json_dir.glob('*.json'))
    
    pitch_updates = []
    answer_updates = []
    matched_pitches = 0
    matched_answers = 0
    unmatched_pitches = 0
    unmatched_answers = 0
    
    print("=" * 80)
    print("🔄 GENERATING SQL UPDATES")
    print("=" * 80)
    print(f"📂 JSON directory: {json_dir}")
    print(f"📊 Database rows: {len(pitches)} pitches, {len(answers)} answers")
    print(f"💾 Output file: {args.output}")
    print("=" * 80)
    
    for json_file in json_files:
        # Extract video ID from filename
        video_id = json_file.stem.split('_')[0]
        
        # Load JSON
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        pairs = data.get('pairs', [])
        
        for pair in pairs:
            question = pair.get('question', '')
            answer = pair.get('answer', '')
            concise_q = clean_text(pair.get('concise_question', ''))
            concise_a = clean_text(pair.get('concise_answer', ''))
            
            # Match pitch by video_id + concise_question
            if question and question.strip():
                pitch_key = (video_id, concise_q)
                if pitch_key in pitch_lookup:
                    pitch_row = pitch_lookup[pitch_key]
                    pitch_id = pitch_row['id']
                    pitch_updates.append(generate_pitch_update(pitch_id, question))
                    matched_pitches += 1
                else:
                    unmatched_pitches += 1
            
            # Match answer by video_id + concise_answer
            if answer and answer.strip():
                answer_key = (video_id, concise_a)
                if answer_key in answer_lookup:
                    answer_row = answer_lookup[answer_key]
                    answer_id = answer_row['id']
                    answer_updates.append(generate_answer_update(answer_id, answer))
                    matched_answers += 1
                else:
                    unmatched_answers += 1
    
    # Write SQL file
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write("-- SQL UPDATE statements to fix body_md fields\n")
        f.write("-- Generated from repaired JSON files\n")
        f.write(f"-- Date: {__import__('datetime').datetime.now().isoformat()}\n")
        f.write("--\n")
        f.write(f"-- Pitch updates: {len(pitch_updates)}\n")
        f.write(f"-- Answer updates: {len(answer_updates)}\n")
        f.write("--\n\n")
        
        f.write("-- Begin transaction\n")
        f.write("BEGIN;\n\n")
        
        if pitch_updates:
            f.write("-- Update pitches.body_md\n")
            for update in pitch_updates:
                f.write(update + "\n")
            f.write("\n")
        
        if answer_updates:
            f.write("-- Update answers.body_md\n")
            for update in answer_updates:
                f.write(update + "\n")
            f.write("\n")
        
        f.write("-- Commit transaction\n")
        f.write("COMMIT;\n")
    
    print(f"\n✅ SQL file generated: {args.output}")
    print(f"   Pitch updates: {matched_pitches}")
    print(f"   Answer updates: {matched_answers}")
    
    if unmatched_pitches > 0 or unmatched_answers > 0:
        print(f"\n⚠️  Unmatched items:")
        print(f"   Pitches: {unmatched_pitches}")
        print(f"   Answers: {unmatched_answers}")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
