import glob
import os

files = glob.glob("/Users/air/Library/Mobile Documents/com~apple~CloudDocs/Dev/youtube-scraper/get_transcripts/transcripts/*Q&A*.txt")

def is_ross_answer_start(line):
    line = line.lower()
    triggers = ["good question", "great question", "interesting question", "ambit claim question"]
    for t in triggers:
        if t in line:
            return True
    return False

def is_moderator_question(line):
    line = line.lower()
    
    # Primary Keywords
    structure_1_kw = ["question", "email", "voice", "viewer", "query"]
    structure_1_ctx = ["from", "coming in", "sent", "asking", "reaching out"]
    
    match_1 = any(k in line for k in structure_1_kw) and any(c in line for c in structure_1_ctx)
    
    # "Here is/Here's ... from ..."
    structure_2_kw = ["here is", "here's"]
    structure_2_ctx = ["from", "coming in"]
    match_2 = any(k in line for k in structure_2_kw) and any(c in line for c in structure_2_ctx)

    # "Next/Another question..." (Explicit flow control)
    structure_3_kw = ["next", "another"]
    structure_3_ctx = ["question", "email", "one"]
    match_3 = any(k in line for k in structure_3_kw) and any(c in line for c in structure_3_ctx)
    
    # "Go to ... from"
    structure_4_kw = ["go to"]
    structure_4_ctx = ["from", "question", "email"]
    match_4 = any(k in line for k in structure_4_kw) and any(c in line for c in structure_4_ctx)

    return match_1 or match_2 or match_3 or match_4

print("--- Testing Logic on ALL lines starting with >> ---")

for fp in files:
    with open(fp, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line.startswith(">>"): continue
        
        # Determine logical classification
        is_ross = is_ross_answer_start(line)
        is_mod = is_moderator_question(line)
        
        if is_ross:
            # We want to make sure we don't accidentally classify Ross's answer start as a Question
            # In the extraction script, if we see a ROSS line, it confirms the PREVIOUS block was a Question/Context
            # and THIS block is the Answer.
            pass
        elif is_mod:
             print(f"[MODERATOR-Q] {line[:100]}")
        else:
             # Look for what we missed
             if len(line) > 30 and ("ross" in line.lower() or "megan" in line.lower()):
                 print(f"[UNCATEGORIZED] {line[:100]}")
