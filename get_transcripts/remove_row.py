import csv
import os

CSV_FILE = "../scrape_video_ids/coulthart_reality_check.csv"
REMOVE_ID = "IbvorziWMm8"

def main():
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row["video_id"] != REMOVE_ID:
                rows.append(row)
            else:
                print(f"Removing {REMOVE_ID} ({row['title']})")
    
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("Done.")

if __name__ == "__main__":
    main()
