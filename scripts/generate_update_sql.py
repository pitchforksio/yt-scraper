import os
import json
import re
import glob

def clean_text(text):
    """
    Remove speaker prefixes like 'Viewer: ' or 'Ross: '.
    Same logic as upload_to_supabase.py
    """
    if not text:
        return text
    # Regex for "Name: " pattern at start of string
    return re.sub(r'^[\w\s]{1,30}:\s+', '', text)

def escape_sql(text):
    """Escape single quotes for SQL."""
    if text is None:
        return None
    return text.replace("'", "''")

def generate_updates():
    base_dir = "/Users/air/Library/Mobile Documents/com~apple~CloudDocs/Dev/youtube-scraper"
    json_dir = os.path.join(base_dir, "data/zfinal/ross_coulthart")
    output_file = os.path.join(base_dir, "data/sql_updates/update_body_correction.sql")
    
    # Ensure output dir exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"Scanning {json_dir}...")
    files = glob.glob(os.path.join(json_dir, "*.json"))
    
    if not files:
        print("No JSON files found.")
        return

    statements = []
    
    for file_path in files:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        pairs = data.get("pairs", [])
        for pair in pairs:
            # Process Pitch (Question)
            concise_q_raw = pair.get("concise_question", "")
            concise_q_clean = clean_text(concise_q_raw)
            full_q = pair.get("question", "")
            
            if concise_q_clean:
                # We match on the CLEANED concise text (which is in the DB)
                # And update body_md to the FULL text
                escaped_concise_q = escape_sql(concise_q_clean)
                escaped_full_q = escape_sql(full_q)
                
                sql = f"UPDATE staging.pitches SET body_md = '{escaped_full_q}' WHERE concise = '{escaped_concise_q}';"
                statements.append(sql)
                
            # Process Answer
            concise_a_raw = pair.get("concise_answer", "")
            concise_a_clean = clean_text(concise_a_raw)
            full_a = pair.get("answer", "")
            
            if concise_a_clean:
                escaped_concise_a = escape_sql(concise_a_clean)
                escaped_full_a = escape_sql(full_a)
                
                sql = f"UPDATE staging.answers SET body_md = '{escaped_full_a}' WHERE concise = '{escaped_concise_a}';"
                statements.append(sql)

    print(f"Generated {len(statements)} UPDATE statements.")
    
    with open(output_file, 'w') as f:
        # Write in batches/transactions if needed, but for now simple list
        f.write("\n".join(statements))
        
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    generate_updates()
