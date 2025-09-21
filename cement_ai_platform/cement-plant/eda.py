import pandas as pd
import os

def analyze_csv(file_path):
    """
    Analyzes a CSV file and prints information about its columns.
    """
    try:
        df = pd.read_csv(file_path)
        print(f"Analysis for: {file_path}")
        print("-" * 30)
        print("Data Head:")
        print(df.head())
        print("\nData Tail:")
        print(df.tail())
        print(f"\nNumber of columns: {len(df.columns)}")
        print(f"Column names: {list(df.columns)}")
        print("Unique value counts per column:")
        for col in df.columns:
            print(f"  - {col}: {df[col].nunique()} unique values")
        print("\n")
    except Exception as e:
        print(f"Could not analyze {file_path}: {e}\n")

if __name__ == "__main__":
    archive_dir = 'archive'
    for root, dirs, files in os.walk(archive_dir):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                analyze_csv(file_path)
