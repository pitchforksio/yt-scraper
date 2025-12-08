"""
Upload Q&A pairs to Supabase staging schema using MCP server.
This script uses the Supabase MCP integration instead of direct REST API calls.
"""
import json
import argparse
import uuid
import sys

def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)

def upload_pair_mcp(project_id, subject_id, question, answer, source_url=None, dry_run=False):
    """
    Upload a Q&A pair using SQL INSERT statements.
    In production, this would call the MCP server, but for now we'll generate the SQL.
    """
    # Generate UUIDs client-side (required by staging schema)
    pitch_id = str(uuid.uuid4())
    answer_id = str(uuid.uuid4())
    
    # Create concise version of question (first 100 chars)
    concise = question[:100] + "..." if len(question) > 100 else question
    
    # Escape single quotes for SQL
    def escape_sql(text):
        if text is None:
            return None
        return text.replace("'", "''")
    
    question_escaped = escape_sql(question)
    answer_escaped = escape_sql(answer)
    concise_escaped = escape_sql(concise)
    source_escaped = escape_sql(source_url) if source_url else None
    
    # Build INSERT statements
    pitch_sql = f"""
INSERT INTO staging.pitches (id, subject_id, type, body_md, concise, language, canonical_source_url, status)
VALUES (
    '{pitch_id}',
    '{subject_id}',
    'QUESTION',
    '{question_escaped}',
    '{concise_escaped}',
    'en',
    {f"'{source_escaped}'" if source_escaped else 'NULL'},
    'PENDING'
);
"""
    
    answer_sql = f"""
INSERT INTO staging.answers (id, pitch_id, body_md, source_url, status)
VALUES (
    '{answer_id}',
    '{pitch_id}',
    '{answer_escaped}',
    {f"'{source_escaped}'" if source_escaped else 'NULL'},
    'PENDING'
);
"""
    
    if dry_run:
        print(f"\n[DRY RUN] Would execute:")
        print(f"Pitch ID: {pitch_id}")
        print(f"Answer ID: {answer_id}")
        print(f"Question (first 50 chars): {question[:50]}...")
        print(f"Answer (first 50 chars): {answer[:50]}...")
        return True
    else:
        # In actual execution, we would call MCP here
        # For now, print the SQL that would be executed
        print(f"\n[LIVE MODE] SQL to execute via MCP:")
        print("=" * 80)
        print(pitch_sql)
        print(answer_sql)
        print("=" * 80)
        print("\nNOTE: This script needs to be called from an MCP-enabled environment.")
        print("Please use the AI assistant to execute these SQL statements via MCP.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Upload Q&A pairs to Supabase staging via MCP")
    parser.add_argument("--config", default="scraper_config.json", help="Config file path")
    parser.add_argument("--input", default="qa_dataset.json", help="Input Q&A JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Simulate upload without executing")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    supabase_config = config["supabase"]
    
    project_id = "xajmsivavyqbjkfuwfdn"  # Hardcoded project ID
    subject_id = supabase_config.get("subject_id")
    
    if not subject_id:
        print("Error: subject_id not configured in scraper_config.json")
        sys.exit(1)
    
    # Load Q&A data
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} Q&A pairs from {args.input}")
    print(f"Target: Supabase project {project_id}, staging schema")
    print(f"Subject ID: {subject_id}")
    
    if args.dry_run:
        print("\n[DRY RUN MODE] No data will be uploaded.\n")
    else:
        print("\n[LIVE MODE] Data will be uploaded via MCP.\n")
    
    success_count = 0
    for i, item in enumerate(data):
        question = item.get("question", "")
        answer = item.get("answer", "")
        source_file = item.get("source_file", "")
        
        if not question or not answer:
            print(f"[{i+1}/{len(data)}] Skipping - missing question or answer")
            continue
        
        # Extract video ID from source file for URL
        vid_id = source_file.split('_')[0] if '_' in source_file else None
        source_url = f"https://www.youtube.com/watch?v={vid_id}" if vid_id else None
        
        print(f"\n[{i+1}/{len(data)}] Processing:")
        print(f"  Question: {question[:60]}...")
        print(f"  Answer: {answer[:60]}...")
        
        if upload_pair_mcp(project_id, subject_id, question, answer, source_url, args.dry_run):
            success_count += 1
    
    print(f"\n{'=' * 80}")
    print(f"Upload {'simulation' if args.dry_run else 'preparation'} complete.")
    print(f"Processed: {success_count}/{len(data)} pairs")
    
    if not args.dry_run:
        print("\nTo execute via MCP, ask the AI assistant to run the generated SQL statements.")

if __name__ == "__main__":
    main()
