import csv
import os

CSV_FILE = "coulthart_reality_check.csv"
TEMP_FILE = "coulthart_reality_check_temp.csv"

def main():
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found.")
        return

    print(f"Updating {CSV_FILE} with 'source' column...")
    
    with open(CSV_FILE, "r", encoding="utf-8") as f_in, \
         open(TEMP_FILE, "w", newline="", encoding="utf-8") as f_out:
        
        reader = csv.DictReader(f_in)
        # Add new field to header
        fieldnames = reader.fieldnames + ["source"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for row in reader:
            row["source"] = "initial_dump"
            writer.writerow(row)
            
    os.replace(TEMP_FILE, CSV_FILE)
    print("Done. All existing rows marked as 'initial_dump'.")

if __name__ == "__main__":
    main()
