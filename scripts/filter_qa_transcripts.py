#!/usr/bin/env python3
"""
Filter Q&A transcripts from the main transcripts directory.

Scans filenames for Q&A patterns and copies them to a filtered directory
for batch processing with GPT-4o extraction.
"""
import os
import re
import shutil
from pathlib import Path
import argparse


def is_qa_transcript(filename: str) -> bool:
    """
    Determine if a filename indicates a Q&A session.
    
    Patterns to match:
    - "Q&A" (case-insensitive)
    - "Q and A" 
    - Video titles with question indicators
    """
    filename_lower = filename.lower().replace('_', ' ').replace('-', ' ')
    
    qa_patterns = [
        r'q\s*&\s*a',           # Q&A, Q & A, etc.
        r'q\s+and\s+a',          # Q and A
        r'questions?\s*answered',  # Questions Answered
        r'viewer\s*questions?',    # Viewer Questions
        r'your\s*questions?',      # Your Questions
        r'searching\s*for\s*answers', # searching for answers (exclude?) - wait, user might want this? 
                                      # No, user wants Q&A. "searching for answers" is usually investigation.
                                      # But "answers viewer questions" should match "viewer questions".
        r'answers?\s+questions?',  # answers questions
        r'answers?\s+viewer',      # answers viewer (catch truncated "viewer que...")
    ]
    
    for pattern in qa_patterns:
        if re.search(pattern, filename_lower):
            return True
    
    return False


def filter_qa_transcripts(source_dir: str, target_dir: str, discard_dir: str = None, dry_run: bool = False) -> dict:
    """
    Scan source directory for Q&A transcripts and MOVE them to target or discard directory.
    
    Args:
        source_dir: Directory to scan (e.g. data/2_transcripts_raw)
        target_dir: Directory for matches (e.g. data/4_extraction/queue)
        discard_dir: Directory for non-matches (e.g. data/3_filtering/archive_discarded)
        dry_run: If True, only simulate
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    discard_path = Path(discard_dir) if discard_dir else None
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    
    # Create directories
    if not dry_run:
        target_path.mkdir(parents=True, exist_ok=True)
        if discard_path:
            discard_path.mkdir(parents=True, exist_ok=True)
            
    # Scan
    all_files = list(source_path.glob("*.txt"))
    
    stats = {
        "total_files": len(all_files),
        "matches": 0,
        "moved_to_target": 0,
        "moved_to_discard": 0
    }
    
    print(f"Scanning {len(all_files)} files in {source_dir}...")
    
    for f in all_files:
        is_match = is_qa_transcript(f.name)
        
        if is_match:
            stats["matches"] += 1
            dest = target_path / f.name
            action = "MATCH -> Queue"
            stats["moved_to_target"] += 1
        else:
            if discard_path:
                dest = discard_path / f.name
                action = "NO MATCH -> Archive"
                stats["moved_to_discard"] += 1
            else:
                action = "NO MATCH -> Skip"
                dest = None
                
        if dry_run:
            print(f"   [DRY] {f.name[:30]}... : {action}")
        else:
            if dest:
                if str(f) == str(dest):
                    # Same file, no move needed
                    # print(f"   [SKIP] Same location: {f.name}")
                    pass
                else:
                    shutil.move(str(f), str(dest))
                    print(f"   ✓ {action}: {f.name}")
                
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Filter Q&A transcripts for batch processing"
    )
    parser.add_argument(
        "--source",
        default="data/2_transcripts_raw",
        help="Inbox directory"
    )
    parser.add_argument(
        "--target",
        default="data/4_extraction/queue",
        help="Target directory for matches"
    )
    parser.add_argument(
        "--discard",
        default="data/3_filtering/archive_discarded",
        help="Target directory for non-matches"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate move"
    )
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute
    script_dir = Path(__file__).parent.parent
    source_dir = (script_dir / args.source).resolve()
    target_dir = (script_dir / args.target).resolve()
    discard_dir = (script_dir / args.discard).resolve() if args.discard else None
    
    print("=" * 80)
    print("🔍 Q&A SORTING HAT")
    print("=" * 80)
    print(f"Inbox:   {source_dir}")
    print(f"Queue:   {target_dir}")
    print(f"Archive: {discard_dir}")
    
    try:
        stats = filter_qa_transcripts(
            str(source_dir),
            str(target_dir),
            str(discard_dir),
            dry_run=args.dry_run
        )
        
        print(f"\n{'=' * 80}")
        print(f"✅ Sorting Complete")
        print(f"   Moved to Queue:   {stats['moved_to_target']}")
        print(f"   Moved to Archive: {stats['moved_to_discard']}")
        print(f"{'=' * 80}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
