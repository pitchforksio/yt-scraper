import glob
import os
import json
import re
import argparse

def clean_text(text):
    return text.replace('\n', ' ').replace('>>', '').strip()

def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)

def is_moderator_question_block(block_text, config_keywords):
    """
    Determines if a block (starting with >>) is a Moderator introducing a question.
    """
    text_lower = block_text.lower()
    
    # --- 1. NEGATIVE LOOKAHEAD (Ross detection - Hardcoded for now) ---
    ross_answer_starts = [
        ">> that's a good question",
        ">> that's a really good question",
        ">> good question",
        ">> great question",
        ">> interesting question",
        ">> look,",
        ">> well,", 
        ">> i agree",
        ">> absolutely",
        ">> no,",
        ">> uh,",
    ]
    
    for start in ross_answer_starts:
        if text_lower.startswith(start):
            return False, "Ross Start"

    if text_lower.startswith(">> oh,") and "question" in text_lower[:50]:
        return False, "Ross Oh-Question"
        
    if text_lower.startswith(">> okay"):
        first_sentence = text_lower.split('.')[0]
        if any(w in first_sentence for w in ["we will", "let's", "here is", "here's", "next", "another"]):
             pass 
        elif any(w in first_sentence for w in ["it's", "so", "look", "that", "i think", "just"]):
             return False, "Ross Okay-Start"

    # --- 2. POSITIVE MATCHERS (Configurable) ---
    
    # A. "From <User>" - logic kept, but keywords checked
    if "from" in text_lower:
        if any(w in text_lower for w in config_keywords):
            return True, "Keyword + From"
        if "from x" in text_lower or "on x" in text_lower:
            return True, "From/On X"
            
    # B. Explicit Keywords with Directionals
    # Use keywords from config
    for k in config_keywords:
        if k in text_lower:
            directionals = ["we have", "got a", "here is", "here's", "next", "first", "another", "final", "last", "go to"]
            if any(d in text_lower for d in directionals):
                return True, f"Directional + {k}"

    # C. Strong Starters
    if text_lower.startswith(">> here is") or text_lower.startswith(">> here's") or text_lower.startswith(">> all right, here"):
         return True, "Here Is Start"

    # D. Says/Asks
    intro_part = text_lower[:150]
    if 'says,' in intro_part or 'says "' in intro_part:
        return True, "Says (Early)"
    if 'asks,' in intro_part or 'asks "' in intro_part:
        return True, "Asks (Early)"
        
    if "let's go to" in text_lower:
        return True, "Let's Go To"

    return False, "No Match"

def extract_qa_from_file(filepath, config_keywords):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    blocks = []
    current_block = []
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.startswith(">>"):
            if current_block:
                blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)

    qa_pairs = []
    current_q_text = ""
    current_a_blocks = []
    
    i = 0
    while i < len(blocks):
        block = blocks[i]
        block_text = " ".join(block)
        
        is_q, reason = is_moderator_question_block(block_text, config_keywords)
        
        if is_q:
            if current_q_text:
                qa_pairs.append({
                    "question": clean_text(current_q_text),
                    "answer": clean_text(" ".join(current_a_blocks))
                })
            
            current_q_text = block_text
            current_a_blocks = []
            
            j = i + 1
            while j < len(blocks):
                next_block_text = " ".join(blocks[j])
                is_next_q, next_reason = is_moderator_question_block(next_block_text, config_keywords)
                
                if is_next_q:
                    break
                
                if "that is it for today" in next_block_text.lower():
                    break
                
                current_a_blocks.append(next_block_text)
                j += 1
            i = j
        else:
            i += 1

    if current_q_text:
        qa_pairs.append({
            "question": clean_text(current_q_text),
            "answer": clean_text(" ".join(current_a_blocks))
        })
        
    return qa_pairs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="scraper_config.json")
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output", default="qa_dataset.json")
    args = parser.parse_args()
    
    config = load_config(args.config)
    keywords = config["filtering"]["qa_keywords"]
    
    files = glob.glob(os.path.join(args.input_dir, "*Q&A*.txt"))
    # Also support if input_dir is a file glob pattern? No, assuming dir.
    # If explicit glob needed:
    if not files:
         files = glob.glob(args.input_dir)
         
    files.sort()
    
    all_data = []
    print(f"Processing {len(files)} files...")
    
    for fp in files:
        filename = os.path.basename(fp)
        pairs = extract_qa_from_file(fp, keywords)
        
        for p in pairs:
            p['source_file'] = filename
            all_data.append(p)
            
    with open(args.output, 'w') as f:
        json.dump(all_data, f, indent=2)
        
    print(f"Saved {len(all_data)} pairs to {args.output}")

if __name__ == "__main__":
    main()
