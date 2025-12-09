import json
import os

try:
    with open('scraper_config.json', 'r') as f:
        config = json.load(f)
        print("Keys in config:", config.keys())
        if 'supabase' in config:
            print("Keys in supabase config:", config['supabase'].keys())
except Exception as e:
    print(f"Error: {e}")
