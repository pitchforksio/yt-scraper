import glob
import os

# Files identified
files = glob.glob("/Users/air/Library/Mobile Documents/com~apple~CloudDocs/Dev/youtube-scraper/get_transcripts/transcripts/*Q&A*.txt")

print(f"Found {len(files)} Q&A files.")

match_keywords = ["question", "email", "voice note", "voicemail", "ask"]
match_context = ["from", "asking", "coming in", "sent"]

for fp in files:
    print(f"\n=== {os.path.basename(fp)} ===")
    with open(fp, 'r') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        line = line.strip()
        if not line.startswith(">>"): continue
        
        lower_line = line.lower()
        
        # Check current extraction logic matches
        is_match = False
        if any(k in lower_line for k in match_keywords):
             if any(c in lower_line for c in match_context):
                 is_match = True
        
        # Also check simple "question" presence
        has_question_word = "question" in lower_line
        
        if is_match:
            print(f"[MATCH] {line[:100]}")
        elif has_question_word:
            print(f"[MISSED QUESTION] {line[:100]}")
        else:
            # Print other potential moderator lines to spot gaps
            # We filter out short ones or obvious answers to reduce noise
            if len(line) > 30 and "ross" in lower_line:
                 print(f"[POTENTIAL] {line[:100]}")
