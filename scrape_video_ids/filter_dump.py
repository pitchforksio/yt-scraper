import csv
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Filter a bulk CSV dump by keywords")
    parser.add_argument("input_file", help="Path to the bulk CSV dump (e.g. youtube_channel_dump.csv)")
    parser.add_argument("output_file", help="Path to save the filtered results")
    parser.add_argument("--keywords", nargs="+", required=True, help="List of keywords to match (OR logic)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: {args.input_file} does not exist.")
        sys.exit(1)
        
    keyword_list = [k.lower() for k in args.keywords]
    print(f"Filtering {args.input_file} for {keyword_list}...")
    
    matches = []
    
    with open(args.input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        # Ensure 'source' is in fieldnames if we want to add it
        if "source" not in fieldnames:
            fieldnames.append("source")
            
        for row in reader:
            title = row.get("title", "").lower()
            if any(k in title for k in keyword_list):
                # Tag it as from the dump
                row["source"] = "bulk_dump"
                matches.append(row)
    
    print(f"Found {len(matches)} matches.")
    
    if matches:
        with open(args.output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(matches)
        print(f"Saved to {args.output_file}")
    else:
        print("No matches found. No file created.")

if __name__ == "__main__":
    main()
