import json
import os

def find_empty_answer_contexts():
    dataset_path = "/Users/air/Library/Mobile Documents/com~apple~CloudDocs/Dev/youtube-scraper/qa_dataset.json"
    transcript_dir = "/Users/air/Library/Mobile Documents/com~apple~CloudDocs/Dev/youtube-scraper/get_transcripts/transcripts"
    
    with open(dataset_path, 'r') as f:
        data = json.load(f)
        
    empty_entries = [d for d in data if not d['answer']]
    
    print(f"Found {len(empty_entries)} empty answer entries.")
    
    for entry in empty_entries:
        src = entry['source_file']
        q_text = entry['question']
        
        # Open source file
        full_path = os.path.join(transcript_dir, src)
        with open(full_path, 'r') as f:
            lines = f.read().splitlines()
            
        # Reconstruct blocks
        blocks = []
        current_block = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith(">>"):
                if current_block:
                    blocks.append(" ".join(current_block))
                current_block = [line]
            else:
                current_block.append(line)
        if current_block:
            blocks.append(" ".join(current_block))
            
        # Find the block matching the question
        # We'll use simple substring matching
        matches_idx = -1
        for i, b in enumerate(blocks):
            # Clean both for comparison
            b_clean = b.replace('>>', '').strip()
            if b_clean == q_text:
                matches_idx = i
                break
        
        if matches_idx != -1 and matches_idx + 1 < len(blocks):
            next_block = blocks[matches_idx + 1]
            print(f"\n--- SOURCE: {src} ---")
            print(f"QUESTION: {q_text[:100]}...")
            print(f"FALSE POSITIVE TRIGGER (Next Block): {next_block[:200]}...")
        else:
            print(f"Could not locate block for {q_text[:30]}")

if __name__ == "__main__":
    find_empty_answer_contexts()
