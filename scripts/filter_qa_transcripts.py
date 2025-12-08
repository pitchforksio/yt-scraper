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
    filename_lower = filename.lower()
    
    qa_patterns = [
        r'q\s*&\s*a',           # Q&A, Q & A, etc.
        r'q\s+and\s+a',          # Q and A
        r'questions?\s*answered',  # Questions Answered
        r'viewer\s*questions?',    # Viewer Questions
        r'your\s*questions?',      # Your Questions
    ]
    
    for pattern in qa_patterns:
        if re.search(pattern, filename_lower):
            return True
    
    return False


def filter_qa_transcripts(source_dir: str, target_dir: str, dry_run: bool = False) -> dict:
    """
    Scan source directory for Q&A transcripts and copy to target directory.
    
    Args:
        source_dir: Path to directory containing all transcripts
        target_dir: Path to output directory for filtered Q&A transcripts
        dry_run: If True, only print what would be copied
        
    Returns:
        Dictionary with stats: total_files, qa_files, copied_files
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    
    # Create target directory if it doesn't exist
    if not dry_run and not target_path.exists():
        target_path.mkdir(parents=True)
        print(f"📁 Created directory: {target_path}")
    
    # Scan for transcripts
    all_files = list(source_path.glob("*.txt"))
    qa_files = [f for f in all_files if is_qa_transcript(f.name)]
    
    stats = {
        "total_files": len(all_files),
        "qa_files": len(qa_files),
        "copied_files": 0
    }
    
    print(f"\n📊 Scan Results:")
    print(f"   Total transcripts: {stats['total_files']}")
    print(f"   Q&A transcripts found: {stats['qa_files']}")
    print(f"   Percentage: {stats['qa_files']/stats['total_files']*100:.1f}%\n")
    
    if dry_run:
        print("[DRY RUN MODE] - No files will be copied\n")
    
    # Copy files
    for qa_file in qa_files:
        target_file = target_path / qa_file.name
        
        if dry_run:
            print(f"   Would copy: {qa_file.name}")
        else:
            shutil.copy2(qa_file, target_file)
            stats["copied_files"] += 1
            print(f"   ✓ Copied: {qa_file.name}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Filter Q&A transcripts for batch processing"
    )
    parser.add_argument(
        "--source",
        default="../get_transcripts/transcripts",
        help="Source directory with all transcripts"
    )
    parser.add_argument(
        "--target",
        default="../get_transcripts/transcripts_filtered",
        help="Target directory for filtered Q&A transcripts"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be copied without actually copying"
    )
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute
    script_dir = Path(__file__).parent
    source_dir = (script_dir / args.source).resolve()
    target_dir = (script_dir / args.target).resolve()
    
    print("=" * 80)
    print("🔍 Q&A Transcript Filter")
    print("=" * 80)
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    
    try:
        stats = filter_qa_transcripts(
            str(source_dir),
            str(target_dir),
            dry_run=args.dry_run
        )
        
        print(f"\n{'=' * 80}")
        if args.dry_run:
            print(f"✅ Dry run complete - {stats['qa_files']} files would be copied")
        else:
            print(f"✅ Filter complete - {stats['copied_files']} files copied")
        print(f"{'=' * 80}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
