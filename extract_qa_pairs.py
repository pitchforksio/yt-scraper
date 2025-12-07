import glob
import os
import json
import re

def clean_text(text):
    return text.replace('\n', ' ').replace('>>', '').strip()

def is_moderator_question_block(block_text):
    """
    Determines if a block (starting with >>) is a Moderator introducing a question.
    """
    text_lower = block_text.lower()
    
    # --- 1. NEGATIVE LOOKAHEAD (Ross detection) ---
    # Ross often starts answers with these phrases.
    
    # Check starts
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
        ">> um,",
        ">> oh,",
        ">> just", # Ross: "Just for those of you..."
        ">> that's what", # Ross: "That's what irritates me..."
        ">> that is a", # Ross: "That is a very good..."
        ">> i think",
        ">> um look",
        ">> um, look",
        ">> fantastic", # Ross: "Fantastic. Absolutely fantastic."
        ">> hi", # Ross: "Hi, Simone" (Broad check, handled strictly below)
        ">> wow",
        ">> right",
        ">> you're", 
        ">> you are",
        ">> that's a", # Covers "That's a really interesting..."
        ">> sure",
        ">> obviously",
        ">> actually",
        ">> ah",
    ]
    
    for start in ross_answer_starts:
        if text_lower.startswith(start):
            return False, "Ross Start"

    # Specific "Okay" checks
    # Ross: ">> Okay, it's really interesting"
    if text_lower.startswith(">> okay"):
        # If followed by 'we', 'let', 'here', 'next' -> Likely Moderator
        # If followed by 'it', 'so', 'look', 'i', 'that', 'the' -> Likely Ross ("The law of one...")
        
        # Check first 100 chars instead of splitting by dot, to catch "Okay. The law..."
        intro_snippet = text_lower[:100]
        
        mod_indicators = ["we will", "let's", "here is", "here's", "next", "another", "question", "email", "coming in"]
        ross_indicators = ["it's", "so", "look", "that", "i think", "just", "the ", "this is"] 
        
        # Check Mod first (Specific Overrides)
        if any(w in intro_snippet for w in mod_indicators):
             pass # Likely mod, continue checks
        elif any(w in intro_snippet for w in ross_indicators):
             return False, "Ross Okay-Start"

    # Ross referencing User: ">> Hi, Simone. And I completely agree..."
    # If the block starts with ">> Hi, <Name>" AND does NOT contain "question"/"email", it's Ross talking.
    if text_lower.startswith(">> hi,"):
        # Mod might say ">> Hi Ross," -> But usually "Hi Ross, we have..."
        if "question" not in text_lower and "email" not in text_lower and "from" not in text_lower:
            return False, "Ross Hi"

    # --- 2. POSITIVE MATCHERS (Moderator detection) ---
    
    # A. "From <User>" patterns
    # Strictness: "from" matches MUST be accompanied by a source type or action
    if "from" in text_lower:
        # Strong Contexts
        # Examples: "question from", "email from", "coming in from", "sent by", "read from"
        strong_keywords = ["question", "email", "post", "voice", "coming in", "reaching out", "sent by", "read", "go to", "start with", "next one", "another one"]
        if any(w in text_lower for w in strong_keywords):
            return True, "Keyword + From"
        
        # Specific "From X"
        if "from x" in text_lower or "on x" in text_lower:
            return True, "From/On X"
            
    # B. Explicit "Question" / "Email" / "Post" (Must have directional context)
    keywords = ["question", "email", "voice note", "voicemail", "post on x", "tweet"]
    for k in keywords:
        if k in text_lower:
            # Must be coupled with some indication of source or action
            directionals = ["we have", "got a", "here is", "here's", "next", "first", "another", "final", "last", "go to", "come to"]
            if any(d in text_lower for d in directionals):
                return True, f"Directional + {k}"
            # "Question from" is covered by A, but "Question is" is weak unless "Here is the question".

    # C. "Here is" / "Here's" (Strong starter)
    if text_lower.startswith(">> here is") or text_lower.startswith(">> here's") or text_lower.startswith(">> all right, here"):
         # Ensure it's not "Here is the thing..." (Ross)
         if "question" in text_lower or "email" in text_lower or "from" in text_lower:
            return True, "Here Is + Context"
         
    # D. "Says" / "Asks" (Risky - restrict to early usage)
    intro_part = text_lower[:150]
    if 'says,' in intro_part or 'says "' in intro_part:
        return True, "Says (Early)"
    if 'asks,' in intro_part or 'asks "' in intro_part:
        return True, "Asks (Early)"
        
    # E. "Let's go to"
    if "let's go to" in text_lower:
        return True, "Let's Go To"

    return False, "No Match"

def extract_qa_from_file_comprehensive(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    blocks = []
    current_block = []
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.startswith(">>"):
            if current_block:
                # Filter out pure timestamps or noise if needed, but transcripts seem clean
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
        
        is_q, reason = is_moderator_question_block(block_text)
        
        if is_q:
            # It's a Question
            if current_q_text:
                qa_pairs.append({
                    "question": clean_text(current_q_text),
                    "answer": clean_text(" ".join(current_a_blocks))
                })
            
            current_q_text = block_text
            current_a_blocks = []
            
            # Consume Answers
            j = i + 1
            while j < len(blocks):
                next_block_text = " ".join(blocks[j])
                is_next_q, next_reason = is_moderator_question_block(next_block_text)
                
                if is_next_q:
                    break 
                
                if "that is it for today" in next_block_text.lower():
                    break
                
                current_a_blocks.append(next_block_text)
                j += 1
            i = j
        else:
            i += 1

    # Save final
    if current_q_text:
        qa_pairs.append({
            "question": clean_text(current_q_text),
            "answer": clean_text(" ".join(current_a_blocks))
        })
        
    return qa_pairs

def main():
    files = glob.glob("/Users/air/Library/Mobile Documents/com~apple~CloudDocs/Dev/youtube-scraper/get_transcripts/transcripts/*Q&A*.txt")
    files.sort()
    
    all_data = []
    print(f"Processing {len(files)} Q&A transcripts with REFINED logic...")
    
    for fp in files:
        filename = os.path.basename(fp)
        pairs = extract_qa_from_file_comprehensive(fp)
        
        empty_answers = sum(1 for p in pairs if not p['answer'])
        print(f"  {filename}: Found {len(pairs)} pairs (Empty Answers: {empty_answers})")
        
        for p in pairs:
            p['source_file'] = filename
            all_data.append(p)
            
    output_path = "/Users/air/Library/Mobile Documents/com~apple~CloudDocs/Dev/youtube-scraper/qa_dataset.json"
    with open(output_path, 'w') as f:
        json.dump(all_data, f, indent=2)
        
    print(f"\nSaved {len(all_data)} Q&A pairs to {output_path}")

if __name__ == "__main__":
    main()
