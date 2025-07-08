import sys
import os

# Add the parent directory of src to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from district_code_loader import load_lawd_table, build_lawd_dict

try:
    print("Attempting to load lawd table...")
    df = load_lawd_table()
    print("Successfully loaded lawd table.")
    print(df.head())

    print("\nAttempting to build lawd dictionary...")
    lawd_dict = build_lawd_dict()
    print("Successfully built lawd dictionary.")
    # Print a few examples to verify filtering and sorting
    for sido, sgg_dict in lawd_dict.items():
        print(f"\n{sido}:")
        # Print first 5 sggs to check sorting and filtering
        for i, (sgg, code) in enumerate(sgg_dict.items()):
            if i >= 5: break
            print(f"  {sgg}: {code}")
        if len(sgg_dict) > 5:
            print("  ...")

except Exception as e:
    print(f"Error: {e}")