import csv
from datetime import datetime

KEYWORDS = ["coulthart", "reality check"]
CSV_FILE = "youtube_channel_dump.csv"

def parse_date(date_str):
    try:
        # Format: 2024-09-17T12:15:15Z
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None

def main():
    matches = []
    all_dates = []

    print(f"Analyzing {CSV_FILE} for keywords: {KEYWORDS}")

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row["title"].lower()
            date_str = row["published_at"]
            dt = parse_date(date_str)
            
            if not dt:
                continue

            all_dates.append(dt)

            # Check for keywords
            if any(k in title for k in KEYWORDS):
                matches.append({
                    "title": row["title"],
                    "date": dt,
                    "date_str": date_str
                })

    if not all_dates:
        print("No valid dates found in CSV.")
        return

    all_dates.sort()
    matches.sort(key=lambda x: x["date"])

    dump_oldest = all_dates[0]
    dump_newest = all_dates[-1]

    print("-" * 40)
    print(f"DUMP RANGE:")
    print(f"  Newest Video: {dump_newest}")
    print(f"  Oldest Video: {dump_oldest}")
    print("-" * 40)

    if not matches:
        print("No videos found matching the keywords.")
        print("This implies the content might be older than this dump, or doesn't exist.")
    else:
        print(f"Found {len(matches)} matching videos.")
        match_newest = matches[-1]
        match_oldest = matches[0]

        print(f"MATCHES RANGE:")
        print(f"  Newest Match: {match_newest['date_str']} - {match_newest['title'][:50]}...")
        print(f"  Oldest Match: {match_oldest['date_str']} - {match_oldest['title'][:50]}...")
        
        gap = match_oldest['date'] - dump_oldest
        print("-" * 40)
        print("CONCLUSION DATA:")
        print(f"  Gap between Oldest Match and End of Dump: {gap.days} days")
        
        if gap.days < 7:
            print("  (!) The oldest match is very close to the dump cutoff.")
            print("      It is HIGHLY LIKELY there are more videos older than this.")
        else:
            print("  (i) There is a significant gap of non-matching videos before your first match.")
            print("      It is LIKELY you have captured the start of this content.")

if __name__ == "__main__":
    main()
