import os
import shutil
import sys

def archive_files(config_name):
    # absolute paths
    base_dir = "/Users/air/Library/Mobile Documents/com~apple~CloudDocs/Dev/youtube-scraper"
    source_dir = os.path.join(base_dir, "data/5_output/json")
    dest_dir = os.path.join(base_dir, "data/zfinal", config_name)
    
    if not os.path.exists(source_dir):
        print(f"Source directory not found: {source_dir}")
        return

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f"Created directory: {dest_dir}")
        
    files = [f for f in os.listdir(source_dir) if f.endswith('.json')]
    
    if not files:
        print("No JSON files found to archive.")
        return
        
    print(f"Found {len(files)} files to archive...")
    
    count = 0
    for filename in files:
        src_path = os.path.join(source_dir, filename)
        dst_path = os.path.join(dest_dir, filename)
        
        try:
            shutil.move(src_path, dst_path)
            count += 1
            # print(f"Moved {filename}")
        except Exception as e:
            print(f"Error moving {filename}: {e}")
            
    print(f"Successfully archived {count} files to {dest_dir}")

if __name__ == "__main__":
    # Hardcoded for this task as requested, but could be arg
    config_name = "ross_coulthart"
    if len(sys.argv) > 1:
        config_name = sys.argv[1]
        
    archive_files(config_name)
