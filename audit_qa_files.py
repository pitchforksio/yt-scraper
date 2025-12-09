import csv
import os
import re
from pathlib import Path

# Config matching the fallback script
INPUT_CSV = "data/1_video_lists/coulthart_reality_check.csv"

def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name[:50]

def main():
    project_root = Path.cwd()
    input_path = project_root / INPUT_CSV
    
    print(f"Auditing Q&A Candidates from {INPUT_CSV}...")
    
    videos_to_process = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("title", "").lower()
            if "q&a" in title or "question" in title or "answer" in title:
                videos_to_process.append(row)
    
    print(f"Total Q&A Candidates: {len(videos_to_process)}")
    print("-" * 60)
    print(f"{'ID':<12} | {'Location':<35} | {'Title':<30}")
    print("-" * 60)
    
    counts = {"Queue": 0, "Archive": 0, "Missing": 0, "Other": 0}
    
    for i, video in enumerate(videos_to_process, 1):
        vid = video["video_id"]
        title = video.get("title", "unknown_title")
        safe_title = sanitize_filename(title)
        filename = f"{vid}_{safe_title}.txt"
        
        # Check locations
        locs = {
            "Queue": project_root / "data/4_extraction/queue" / filename,
            "Queue (Filtered)": project_root / "data/2_transcripts_raw_filtered" / filename, # Check artifact of dry run error?
            "Archive": project_root / "data/3_filtering/archive_discarded" / filename,
            "Inbox": project_root / "data/2_transcripts_raw" / filename,
            "Processed": project_root / "data/4_extraction/processed" / filename,
            "Failed": project_root / "data/4_extraction/failed" / filename,
        }
        
        found_loc = "Missing"
        for name, path in locs.items():
            if path.exists():
                found_loc = name
                break
        
        # Update counts
        if found_loc in counts:
            counts[found_loc] += 1
        else:
            if "Queue" in found_loc: counts["Queue"] += 1
            elif "Archive" in found_loc: counts["Archive"] += 1
            else: counts["Other"] += 1
            
        print(f"{vid:<12} | {found_loc:<35} | {title[:30]}...")

    print("-" * 60)
    print("Summary:")
    print(f"Total: {len(videos_to_process)}")
    print(f"Queue:   {counts['Queue']}")
    print(f"Archive: {counts['Archive']}")
    print(f"Missing: {counts['Missing']}")
    print(f"Other:   {counts['Other']}")
    print("-" * 60)

if __name__ == "__main__":
    main()
