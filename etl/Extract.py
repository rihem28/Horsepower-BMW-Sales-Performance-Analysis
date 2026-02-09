# extract.py
import pandas as pd
import os


def extract_bmw_data(project_root):
    """
    Extract BMW sales data from staging directory
    and save a raw copy for downstream processing.
    """

    print("\n--- Starting BMW Data Extraction ---")

    # Define staging directory
    staging_dir = os.path.join(project_root, "data", "staging")
    os.makedirs(staging_dir, exist_ok=True)

    print(f"Staging directory ready at: {staging_dir}")

    # Source file path
    source_csv_path = os.path.join(staging_dir, "BMW_Sales_Data.csv")

    if not os.path.exists(source_csv_path):
        raise FileNotFoundError(
            "BMW_Sales_Data.csv not found in staging folder."
        )

    # Read data
    df = pd.read_csv(source_csv_path)
    print("BMW sales data successfully extracted.")

    # Save raw copy
    raw_output_path = os.path.join(staging_dir, "bmw_raw.csv")
    df.to_csv(raw_output_path, index=False)

    print("Raw BMW data saved to staging area.")

    return df