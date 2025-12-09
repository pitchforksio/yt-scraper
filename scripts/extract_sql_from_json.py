
import json
import sys
import os

def main():
    json_file = 'batches_final.json'
    target_type = sys.argv[1] # 'pitches' or 'answers'
    output_dir = sys.argv[2]
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(json_file, 'r') as f:
        batches = json.load(f)
        
    count = 0
    for i, batch in enumerate(batches):
        if batch['type'] == target_type:
            filename = f"{target_type}_batch_{batch['batch_num']}.sql"
            path = os.path.join(output_dir, filename)
            with open(path, 'w') as f:
                f.write(batch['sql'])
            print(f"Extracted {filename}")
            count += 1
            
    if count == 0:
        print(f"No batches found for {target_type}")

if __name__ == "__main__":
    main()
