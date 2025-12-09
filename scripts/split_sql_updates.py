import os

def split_sql_file(input_file, batch_size=50):
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    # Filter out empty lines
    statements = [line.strip() for line in lines if line.strip()]
    
    total_statements = len(statements)
    print(f"Total statements: {total_statements}")
    
    output_dir = os.path.dirname(input_file)
    batch_files = []
    
    for i in range(0, total_statements, batch_size):
        batch = statements[i:i + batch_size]
        batch_filename = os.path.join(output_dir, f"batch_{i // batch_size + 1:03d}.sql")
        with open(batch_filename, 'w') as f:
            f.write('\n'.join(batch))
        batch_files.append(batch_filename)
        print(f"Created {batch_filename} with {len(batch)} statements")
        
    return batch_files

if __name__ == "__main__":
    split_sql_file("data/sql_updates/update_body_correction.sql")
