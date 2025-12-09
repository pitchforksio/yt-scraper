import glob
import os

def filter_sql_files():
    # Target specific temp files we plan to use
    files = glob.glob('data/sql_updates/temp_*.sql')
    
    for file_path in files:
        print(f"Processing {file_path}...")
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        filtered_lines = []
        removed_count = 0
        
        for line in lines:
            if "SET body_md = '' WHERE" in line:
                removed_count += 1
                continue
            filtered_lines.append(line)
            
        output_path = file_path.replace('temp_', 'filtered_')
        with open(output_path, 'w') as f:
            f.writelines(filtered_lines)
            
        print(f"  - Original lines: {len(lines)}")
        print(f"  - Removed lines: {removed_count}")
        print(f"  - Saved to: {output_path}")

if __name__ == "__main__":
    filter_sql_files()
