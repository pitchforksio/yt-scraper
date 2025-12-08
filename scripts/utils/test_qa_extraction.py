import re
import os

def extract_qa_refined(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Pre-process to create blocks based on `>>` OR pattern-based speaker change
    blocks = []
    current_block = []
    
    # Common answer starters (Ross often starts with these)
    # Note: These might also appear in normal speech, so we only trigger this split 
    # if we suspect we are currently reading a question and this line looks like a break.
    answer_starters = ["Well, ", "Okay, ", "Look, ", "That's a good question", "It's a really good question", "I think "]
    
    state = "normal" # normal, reading_question
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check for explicit speaker change
        if line.startswith(">>"):
            if current_block:
                blocks.append(current_block)
            current_block = [line]
            
            # Reset state? 
            # If the new block looks like a question intro, identify it? 
            # We'll classify blocks later, but splitting effectively is key.
            continue
            
        # Check for implicit speaker change (Answer start)
        # We only look for this if we haven't just started an explicit block (to avoid splitting ">> Well...")
        if current_block and not current_block[-1].startswith(">>"):
            # If line starts with an answer starter
            is_answer_start = False
            for starter in answer_starters:
                 if line.startswith(starter):
                     is_answer_start = True
                     break
            
            # Heuristic: If we were identifying a question, and now we see "Well, ...", split
            # But we don't know if we are identifying a question yet in this pass.
            # Let's just aggressively split on clearly starting lines if they seem like a change.
            # Actually, "Well," could be inside a quote. 
            pass  

        current_block.append(line)
        
    if current_block:
        blocks.append(current_block)

    # Now iterate blocks and classify
    final_qa = []
    
    i = 0
    while i < len(blocks):
        block_lines = blocks[i]
        block_text = " ".join(block_lines)
        block_intro = " ".join(block_lines[:4]).lower() # First few lines
        
        is_question_intro = False
        # Tight criteria for Question Intro
        # Must contain "question" or "email" AND "from"
        if ("question" in block_intro or "email" in block_intro):
            if ("from" in block_intro) or ("coming in" in block_intro):
                is_question_intro = True
        
        if is_question_intro:
            q_text_lines = []
            a_text_lines = []
            
            # Now we need to find where the question ends and answer starts WITHIN this block (if merged)
            # or in subsequent blocks.
            
            # Intra-block split? 
            # If the block contains the answer start, we need to split it.
            # Let's iterate lines in this block
            
            found_split = False
            for line_idx, line in enumerate(block_lines):
                # skip the first line (intro)
                if line_idx == 0: 
                    q_text_lines.append(line)
                    continue
                
                # Check for answer start
                is_ans = False
                for starter in answer_starters:
                    if line.startswith(starter):
                        is_ans = True
                        break
                
                # Also check if previous line ended with quote closing or signature
                prev_line = block_lines[line_idx-1]
                if prev_line.lower().endswith("evan.") or prev_line.strip().endswith('"'):
                     # Weak signal but maybe
                     pass

                if is_ans and not found_split:
                    found_split = True
                    # This line begins the answer
                    a_text_lines.append(line)
                elif found_split:
                    a_text_lines.append(line)
                else:
                    q_text_lines.append(line)
            
            # If we didn't find a split in this block, then the whole block is Question (or intro),
            # and subsequent blocks are the Answer.
            if not found_split:
                # The whole block is Q
                pass
            else:
                # We split the block. 
                # Q is q_text_lines
                # A is a_text_lines.
                # Are there subsequent blocks that are also A?
                # Yes, until next Q.
                pass

            # Gather subsequent blocks as part of Answer until next Q
            # NOTE: If we split the current block, we already have some A lines.
            
            j = i + 1
            while j < len(blocks):
                next_blk = blocks[j]
                next_intro = " ".join(next_blk[:4]).lower()
                
                # Check if next block is Q
                is_next_q = False
                if (">>" in next_blk[0]) and ("question" in next_intro or "email" in next_intro) and ("from" in next_intro):
                    is_next_q = True
                
                if is_next_q:
                    break
                
                a_text_lines.extend(next_blk)
                j += 1
            
            final_qa.append({
                "Q": " ".join(q_text_lines),
                "A": " ".join(a_text_lines)
            })
            i = j
        else:
            i += 1

    return final_qa

files = [
    "/Users/air/Library/Mobile Documents/com~apple~CloudDocs/Dev/youtube-scraper/get_transcripts/transcripts/1LxP0OhbKkM_Ross_Coulthart_Q&A_Inside_the_most_secure_military.txt",
    "/Users/air/Library/Mobile Documents/com~apple~CloudDocs/Dev/youtube-scraper/get_transcripts/transcripts/LtjlTqC1atI_Ross_Coulthart_Q&A_New_Jersey_drone_mystery_solved.txt"
]

for fp in files:
    print(f"--- Analyzing {os.path.basename(fp)} ---")
    qa = extract_qa_refined(fp)
    for idx, item in enumerate(qa):
         print(f"[{idx+1}] QUESTION: {item['Q'][:80]}...")
         print(f"    ANSWER: {item['A'][:80]}...")
         print("-" * 20)
