import csv
import sys

# Script to Filter the Bulk Dump into a Specialized "Coulthart/Reality Check" Dataset

INPUT_FILE = "youtube_channel_dump_backup.csv" # Reading from source
OUTPUT_FILE = "coulthart_reality_check.csv"   # Writing to new specific file
KEYWORDS = ["coulthart", "reality check"]

def main():
    print(f"Reading from {INPUT_FILE}...")
    
    matches = []
    
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            for row in reader:
                title = row.get("title", "").lower()
                # Check keywords
                if any(k in title for k in KEYWORDS):
                    matches.append(row)
                    
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        sys.exit(1)

    print(f"Found {len(matches)} matching videos in the initial 20k dump.")

    if matches:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matches)
        print(f"Created new file: {OUTPUT_FILE}")
    else:
        print("No matches found to create file.")

if __name__ == "__main__":
    main()
