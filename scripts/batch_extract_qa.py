#!/usr/bin/env python3
"""
Batch process all transcripts using GPT-4o extraction.
"""
import json
import os
import time
from pathlib import Path
import subprocess

def load_config():
    """Load API key from config."""
    config_path = Path(__file__).parent.parent / 'scraper_config.json'
    with open(config_path, 'r') as f:
        return json.load(f)

def get_transcripts(transcript_dir):
    """Get all transcript files."""
    base_path = Path(__file__).parent.parent
    transcript_path = base_path / transcript_dir
    return sorted(transcript_path.glob('*.txt'))

def process_all_transcripts(api_key: str, output_dir: str = 'qa_outputs'):
    """Process all transcripts."""
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Get all transcripts
    transcripts = get_transcripts('get_transcripts/transcripts')
    total = len(transcripts)
    
    print(f"🚀 Processing {total} transcripts with GPT-4o")
    print("=" * 80)
    
    results = []
    total_cost = 0
    total_pairs = 0
    
    for i, transcript_path in enumerate(transcripts, 1):
        video_id = transcript_path.stem.split('_')[0]
        output_file = f"{output_dir}/{video_id}_qa.json"
        
        # Skip if already processed
        if os.path.exists(output_file):
            print(f"[{i}/{total}] ⏭️  Skipping {video_id} (already processed)")
            continue
        
        print(f"[{i}/{total}] 📄 Processing {video_id}...", end=" ", flush=True)
        
        try:
            # Run extraction
            extract_script = Path(__file__).parent / 'extract_qa_gpt4o.py'
            cmd = [
                '../.venv/bin/python', str(extract_script),
                '--transcript', str(transcript_path),
                '--output', output_file,
                '--api-key', api_key
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Load result to get stats
                with open(output_file, 'r') as f:
                    data = json.load(f)
                
                pairs = len(data['pairs'])
                cost = data['metadata']['cost_estimate']
                
                total_pairs += pairs
                total_cost += cost
                
                print(f"✅ {pairs} pairs, ${cost:.4f}")
                
                results.append({
                    'video_id': video_id,
                    'pairs': pairs,
                    'cost': cost,
                    'status': 'success'
                })
            else:
                print(f"❌ Error: {result.stderr[:100]}")
                results.append({
                    'video_id': video_id,
                    'status': 'error',
                    'error': result.stderr[:200]
                })
        
        except Exception as e:
            print(f"❌ Exception: {str(e)[:100]}")
            results.append({
                'video_id': video_id,
                'status': 'error',
                'error': str(e)[:200]
            })
        
        # Rate limiting - be nice to OpenAI
        if i < total:
            time.sleep(1)
    
    # Save summary
    summary = {
        'total_transcripts': total,
        'successful': sum(1 for r in results if r['status'] == 'success'),
        'failed': sum(1 for r in results if r['status'] == 'error'),
        'total_pairs': total_pairs,
        'total_cost': total_cost,
        'results': results
    }
    
    with open(f'{output_dir}/batch_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"✅ Complete!")
    print(f"   Successful: {summary['successful']}/{total}")
    print(f"   Total Q&A pairs: {total_pairs}")
    print(f"   Total cost: ${total_cost:.2f}")
    print(f"   Summary saved to: {output_dir}/batch_summary.json")

def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-key', help='OpenAI API key (or set in scraper_config.json)')
    parser.add_argument('--output-dir', default='qa_outputs', help='Output directory')
    args = parser.parse_args()
    
    # Get API key
    if args.api_key:
        api_key = args.api_key
    else:
        config = load_config()
        api_key = config.get('openai_api_key')
        if not api_key:
            print("❌ Error: No API key found in scraper_config.json")
            print("   Add 'openai_api_key' to scraper_config.json or use --api-key")
            return
    
    process_all_transcripts(api_key, args.output_dir)

if __name__ == "__main__":
    main()
