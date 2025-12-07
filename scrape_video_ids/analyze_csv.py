import csv
from datetime import datetime

dates = []
with open("youtube_channel_dump.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["published_at"]:
            dates.append(row["published_at"])

if not dates:
    print("No dates found.")
else:
    print(f"Total rows with dates: {len(dates)}")
    print(f"First (Top of file): {dates[0]}")
    print(f"Last (Bottom of file): {dates[-1]}")
    
    # Sort to be sure
    dates.sort()
    print(f"Earliest Date: {dates[0]}")
    print(f"Latest Date: {dates[-1]}")
