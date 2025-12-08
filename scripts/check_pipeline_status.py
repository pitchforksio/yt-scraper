#!/usr/bin/env python3
"""
Quick status check for Q&A extraction pipeline.

Shows current state of all pipeline components.
"""
import json
from pathlib import Path


def check_status():
    """Check pipeline status."""
    project_root = Path(__file__).parent.parent
    
    print("\n" + "="*80)
    print("📊 Q&A EXTRACTION PIPELINE - STATUS CHECK")
    print("="*80 + "\n")
    
    # 1. Config
    config_file = project_root / "scraper_config.json"
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        
        has_openai = bool(
            config.get("openai", {}).get("api_key") or 
            config.get("openai_api_key")
        )
        has_subject = bool(config.get("supabase", {}).get("subject_id"))
        
        print("✅ Configuration:")
        print(f"   OpenAI API Key: {'✓' if has_openai else '✗ Missing'}")
        print(f"   Subject ID: {'✓' if has_subject else '✗ Missing'}")
    else:
        print("❌ Configuration: scraper_config.json not found")
    
    # 2. Transcripts
    transcripts_dir = project_root / "get_transcripts" / "transcripts"
    if transcripts_dir.exists():
        total = len(list(transcripts_dir.glob("*.txt")))
        print(f"\n✅ Source Transcripts: {total} files")
    else:
        print("\n❌ Source Transcripts: Directory not found")
    
    # 3. Filtered
    filtered_dir = project_root / "get_transcripts" / "transcripts_filtered"
    if filtered_dir.exists():
        filtered = len(list(filtered_dir.glob("*.txt")))
        print(f"✅ Filtered Q&A: {filtered} files")
    else:
        print("⚠️  Filtered Q&A: Not created yet (run Step 1)")
    
    # 4. Extractions
    qa_dir = project_root / "outputs" / "qa_extractions"
    if qa_dir.exists():
        extractions = len(list(qa_dir.glob("*.json")))
        print(f"{'✅' if extractions > 0 else '⚠️ '} Q&A Extractions: {extractions} files")
        
        if extractions > 0:
            # Count total pairs
            total_pairs = 0
            for json_file in qa_dir.glob("*.json"):
                with open(json_file) as f:
                    data = json.load(f)
                total_pairs += len(data.get("pairs", []))
            print(f"   Total Q&A pairs extracted: {total_pairs}")
    else:
        print("⚠️  Q&A Extractions: Not created yet (run Step 2)")
    
    # 5. CSV
    csv_file = project_root / "outputs" / "qa_dataset.csv"
    if csv_file.exists():
        # Count rows
        with open(csv_file) as f:
            rows = len(f.readlines()) - 1  # Subtract header
        print(f"✅ CSV Export: {rows} rows ({rows//2} Q&A pairs)")
    else:
        print("⚠️  CSV Export: Not created yet (run Step 3)")
    
    # 6. Scripts
    scripts = [
        "filter_qa_transcripts.py",
        "extract_qa_gpt4o.py",
        "export_qa_csv.py",
        "upload_to_supabase.py",
        "run_pipeline.py"
    ]
    scripts_dir = project_root / "scripts"
    missing = [s for s in scripts if not (scripts_dir / s).exists()]
    
    if missing:
        print(f"\n⚠️  Scripts: Missing {len(missing)}: {', '.join(missing)}")
    else:
        print(f"\n✅ Scripts: All 5 pipeline scripts present")
    
    # 7. Recommendations
    print("\n" + "="*80)
    print("📋 RECOMMENDATIONS")
    print("="*80)
    
    if not filtered_dir.exists() or len(list(filtered_dir.glob("*.txt"))) == 0:
        print("\n1️⃣  Run Step 1: Filter transcripts")
        print("   .venv/bin/python scripts/filter_qa_transcripts.py")
    elif not qa_dir.exists() or len(list(qa_dir.glob("*.json"))) == 0:
        print("\n2️⃣  Run Step 2: Extract Q&A pairs (start with 2 files)")
        print("   .venv/bin/python scripts/run_pipeline.py --limit 2")
    elif not csv_file.exists():
        print("\n3️⃣  Run Step 3: Export to CSV")
        print("   .venv/bin/python scripts/run_pipeline.py --step csv")
    else:
        print("\n🎯 Ready for full pipeline run!")
        print("   .venv/bin/python scripts/run_pipeline.py")
        print("\n   Or test with limited files:")
        print("   .venv/bin/python scripts/run_pipeline.py --limit 5")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    check_status()
