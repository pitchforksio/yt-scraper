import requests
import json
import argparse
import time
import uuid

def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)

def upload_pair(base_url, token, subject_id, question, answer, source_url=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "apikey": token, # Supabase REST often needs apikey header + Authorization
        "Prefer": "return=representation", # To get the ID back
        "Content-Profile": "staging" # Use staging schema
    }
    
    # Generate UUIDs locally to ensure they match if we need references before insert?
    # Supabase/Postgres can gen_random_uuid(), but the staging schema might require explicit IDs?
    # Checked schema: "Explicit UUID required (no auto-generation) to preserve IDs when promoted"
    # So we MUST generate UUIDs here.
    
    pitch_id = str(uuid.uuid4())
    
    # 1. Create Pitch
    pitch_payload = {
        "id": pitch_id,
        "subject_id": subject_id,
        "type": "QUESTION",
        "body_md": question,
        "concise": question[:100] + "..." if len(question) > 100 else question,
        "status": "PENDING", # Enum: PENDING, APPROVED...
        "language": "en"
    }
    
    try:
        r1 = requests.post(f"{base_url}/rest/v1/pitches", json=pitch_payload, headers=headers)
        r1.raise_for_status()
        
        # 2. Create Answer
        # Answers also need explicit IDs? 
        # Schema for answers says: "Staging table for answers linked to staging pitches"
        # Checking columns... "id" options: ["updatable"] defaults to gen_random_uuid()? 
        # Re-reading schema dump for answers in staging: 
        # "name":"id", "default_value": "gen_random_uuid()" is NOT present in the staging dump snippet? 
        # Wait, the staging dump for `pitches` had "Explicit UUID required". 
        # Let's verify `answers` in staging...
        # The dump output showed: `answers` -> no comment about explicit ID, but let's be safe and generate it.
        
        answer_id = str(uuid.uuid4())
        
        answer_payload = {
            "id": answer_id,
            "pitch_id": pitch_id,
            "body_md": answer,
            "status": "PENDING",
            "source_url": source_url
        }
        
        r2 = requests.post(f"{base_url}/rest/v1/answers", json=answer_payload, headers=headers)
        r2.raise_for_status()
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"  API Error: {e}")
        if hasattr(e, 'response') and e.response:
             print(f"  Response: {e.response.text}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="scraper_config.json")
    parser.add_argument("--input", default="qa_dataset.json")
    parser.add_argument("--dry-run", action="store_true", help="Do not actually upload")
    args = parser.parse_args()
    
    config = load_config(args.config)
    api_config = config["supabase"]
    
    base_url = api_config.get("api_base_url")
    token = api_config.get("auth_token")
    subject_id = api_config.get("subject_id")
    
    if token == "YOUR_AUTH_TOKEN":
        print("Error: Auth token not configured in scraper_config.json")
        return

    with open(args.input, 'r') as f:
        data = json.load(f)
        
    print(f"Uploading {len(data)} items to {base_url} (Schema: staging)...")
    
    if args.dry_run:
        print("[Dry Run Mode] No changes will be made.")
    
    success_count = 0
    for i, item in enumerate(data):
        q = item.get("question")
        a = item.get("answer")
        src_file = item.get("source_file", "")
        
        vid_id = src_file.split('_')[0] if '_' in src_file else None
        source_url = f"https://www.youtube.com/watch?v={vid_id}" if vid_id else None
        
        print(f"[{i+1}/{len(data)}] Uploading: {q[:30]}...")
        
        if not args.dry_run:
            if upload_pair(base_url, token, subject_id, q, a, source_url):
                success_count += 1
            time.sleep(0.2)
        else:
            success_count += 1
            
    print(f"Upload Complete. Success: {success_count}/{len(data)}")

if __name__ == "__main__":
    main()
