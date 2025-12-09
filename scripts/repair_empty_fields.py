#!/usr/bin/env python3
"""
Repair empty question/answer fields in JSON files by extracting from transcripts.

Uses the line numbers saved in q_lines/a_lines to extract the exact text from
the original transcript files.
"""
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


def find_transcript(video_id: str, transcript_dir: str) -> Path:
    """Find transcript file for a given video ID."""
    transcript_path = Path(transcript_dir)
    
    # Try exact match first
    matches = list(transcript_path.glob(f"{video_id}_*.txt"))
    if matches:
        return matches[0]
    
    return None


def reconstruct_text(lines: List[str], start: int, end: int) -> str:
    """Reconstruct text from line range."""
    return ' '.join(lines[start:end+1])


def repair_json_file(json_path: Path, transcript_dir: str, backup: bool = True) -> Dict:
    """Repair a single JSON file by extracting full text from transcript.
    
    Returns:
        Dict with repair statistics
    """
    # Load JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract video ID from filename
    filename = json_path.stem
    video_id = filename.split('_')[0]
    
    # Find transcript
    transcript_path = find_transcript(video_id, transcript_dir)
    if not transcript_path:
        return {
            'video_id': video_id,
            'status': 'no_transcript',
            'repaired': 0
        }
    
    # Load transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    lines = transcript_text.split('\n')
    
    # Repair pairs
    pairs = data.get('pairs', [])
    repaired_questions = 0
    repaired_answers = 0
    
    for pair in pairs:
        # Check and repair question
        if not pair.get('question', '').strip():
            if pair.get('q_lines'):
                q_start, q_end = pair['q_lines']
                full_question = reconstruct_text(lines, q_start, q_end)
                pair['question'] = full_question
                repaired_questions += 1
        
        # Check and repair answer
        if not pair.get('answer', '').strip():
            if pair.get('a_lines'):
                a_start, a_end = pair['a_lines']
                full_answer = reconstruct_text(lines, a_start, a_end)
                pair['answer'] = full_answer
                repaired_answers += 1
    
    # Backup original if requested
    if backup and (repaired_questions > 0 or repaired_answers > 0):
        backup_path = json_path.with_suffix('.json.bak')
        shutil.copy2(json_path, backup_path)
    
    # Save repaired JSON
    if repaired_questions > 0 or repaired_answers > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    return {
        'video_id': video_id,
        'status': 'repaired' if (repaired_questions > 0 or repaired_answers > 0) else 'no_changes',
        'repaired_questions': repaired_questions,
        'repaired_answers': repaired_answers,
        'transcript': str(transcript_path.name)
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Repair empty Q&A fields by extracting from transcripts"
    )
    parser.add_argument(
        '--json-dir',
        default='data/zfinal/ross_coulthart',
        help='Directory containing JSON files to repair'
    )
    parser.add_argument(
        '--transcript-dir',
        default='get_transcripts/transcripts',
        help='Directory containing transcript files'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create .bak files before modifying'
    )
    parser.add_argument(
        '--log',
        default='repair_log.txt',
        help='Log file for repair results'
    )
    
    args = parser.parse_args()
    
    json_dir = Path(args.json_dir)
    json_files = sorted(json_dir.glob('*.json'))
    
    print("=" * 80)
    print("🔧 JSON REPAIR TOOL")
    print("=" * 80)
    print(f"📂 JSON directory: {json_dir}")
    print(f"📄 Transcript directory: {args.transcript_dir}")
    print(f"📦 Backup files: {'No' if args.no_backup else 'Yes'}")
    print(f"📝 Log file: {args.log}")
    print(f"\n🔍 Found {len(json_files)} JSON files to process")
    print("=" * 80)
    
    results = []
    total_repaired_questions = 0
    total_repaired_answers = 0
    
    for i, json_path in enumerate(json_files, 1):
        print(f"\n[{i}/{len(json_files)}] Processing {json_path.name}...", end=" ")
        
        result = repair_json_file(
            json_path,
            args.transcript_dir,
            backup=not args.no_backup
        )
        results.append(result)
        
        if result['status'] == 'repaired':
            total_repaired_questions += result['repaired_questions']
            total_repaired_answers += result['repaired_answers']
            print(f"✅ Repaired {result['repaired_questions']}Q + {result['repaired_answers']}A")
        elif result['status'] == 'no_changes':
            print("✓ No changes needed")
        elif result['status'] == 'no_transcript':
            print("⚠️  No transcript found")
    
    # Save log
    with open(args.log, 'w', encoding='utf-8') as f:
        f.write("JSON REPAIR LOG\n")
        f.write("=" * 80 + "\n\n")
        
        for result in results:
            f.write(f"Video ID: {result['video_id']}\n")
            f.write(f"Status: {result['status']}\n")
            if result['status'] == 'repaired':
                f.write(f"Repaired questions: {result['repaired_questions']}\n")
                f.write(f"Repaired answers: {result['repaired_answers']}\n")
                f.write(f"Transcript: {result.get('transcript', 'N/A')}\n")
            f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total files processed: {len(results)}\n")
        f.write(f"Files repaired: {sum(1 for r in results if r['status'] == 'repaired')}\n")
        f.write(f"Total questions repaired: {total_repaired_questions}\n")
        f.write(f"Total answers repaired: {total_repaired_answers}\n")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 REPAIR SUMMARY")
    print("=" * 80)
    print(f"✅ Files repaired: {sum(1 for r in results if r['status'] == 'repaired')}/{len(results)}")
    print(f"🎯 Questions repaired: {total_repaired_questions}")
    print(f"💬 Answers repaired: {total_repaired_answers}")
    print(f"📝 Log saved to: {args.log}")
    print("=" * 80)


if __name__ == "__main__":
    main()
