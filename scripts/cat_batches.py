import sys
import glob

def main():
    if len(sys.argv) < 3:
        print("Usage: python cat_batches.py <start> <end>")
        return

    start = int(sys.argv[1])
    end = int(sys.argv[2])
    
    for i in range(start, end + 1):
        filename = f"data/sql_updates/batch_{i:03d}.sql"
        try:
            with open(filename, 'r') as f:
                content = f.read()
                print(content)
                print("\n") # Ensure separation
        except FileNotFoundError:
            print(f"File not found: {filename}")

if __name__ == "__main__":
    main()
