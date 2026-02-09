# transform.py
import pandas as pd
import os


def clean_bmw_data(project_root):
    """
    Cleans raw BMW data from staging and saves cleaned dataset.
    """
    print("\n--- Cleaning BMW Data ---")

    staging_path = os.path.join(project_root, "data", "staging", "bmw_raw.csv")
    processed_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    df = pd.read_csv(staging_path)
    print("Initial dataset shape:", df.shape)

    # ---- Missing values ----
    categorical_cols = [
        "Model", "Region", "Color",
        "Fuel_Type", "Transmission", "Sales_Classification"
    ]

    numerical_cols = [
        "Year", "Engine_Size_L",
        "Mileage_KM", "Price_USD", "Sales_Volume"
    ]

    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].mode()[0])

    for col in numerical_cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    # ---- Year validation ----
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"])

    # ---- Standardization ----
    for col in categorical_cols:
        df[col] = df[col].str.title().str.strip()

    # ---- Remove duplicates ----
    df = df.drop_duplicates()

    cleaned_path = os.path.join(processed_dir, "bmw_cleaned.csv")
    df.to_csv(cleaned_path, index=False)
    print("Cleaned BMW dataset saved")

    return df


def transform_bmw_data(df, project_root):
    """
    Adds KPIs, creates dimensions and fact table.
    """
    print("\n--- Transforming BMW Data ---")

    processed_dir = os.path.join(project_root, "data", "processed")

    # ---- KPIs ----
    df["Revenue_USD"] = df["Price_USD"] * df["Sales_Volume"]
    df["Vehicle_Age"] = df["Year"].max() - df["Year"]

    df["Price_Range"] = pd.cut(
        df["Price_USD"],
        bins=[0, 30000, 60000, 100000, df["Price_USD"].max()],
        labels=["Budget", "Mid-Range", "Premium", "Luxury"]
    )

    df["Mileage_Range"] = pd.cut(
        df["Mileage_KM"],
        bins=[0, 50000, 100000, 150000, df["Mileage_KM"].max()],
        labels=["Low", "Medium", "High", "Very High"]
    )

    analytics_path = os.path.join(processed_dir, "bmw_analytics_ready.csv")
    df.to_csv(analytics_path, index=False)

    # ----------------- Dimensions -----------------

    dim_date = df[["Year"]].drop_duplicates().reset_index(drop=True)
    dim_date["Date_Key"] = dim_date.index + 1
    dim_date["Decade"] = (dim_date["Year"] // 10) * 10
    dim_date.to_csv(os.path.join(processed_dir, "dim_date.csv"), index=False)

    dim_model = df[["Model"]].drop_duplicates().reset_index(drop=True)
    dim_model["Model_Key"] = dim_model.index + 1
    dim_model.rename(columns={"Model": "Model_Name"}, inplace=True)
    dim_model.to_csv(os.path.join(processed_dir, "dim_model.csv"), index=False)

    dim_region = df[["Region"]].drop_duplicates().reset_index(drop=True)
    dim_region["Region_Key"] = dim_region.index + 1
    dim_region.to_csv(os.path.join(processed_dir, "dim_region.csv"), index=False)

    dim_vehicle = df[["Fuel_Type", "Transmission", "Color"]].drop_duplicates().reset_index(drop=True)
    dim_vehicle["Vehicle_Key"] = dim_vehicle.index + 1
    dim_vehicle.to_csv(
        os.path.join(processed_dir, "dim_vehicle_attributes.csv"),
        index=False
    )

    dim_sales_class = df[["Sales_Classification"]].drop_duplicates().reset_index(drop=True)
    dim_sales_class["Sales_Class_Key"] = dim_sales_class.index + 1
    dim_sales_class.to_csv(
        os.path.join(processed_dir, "dim_sales_classification.csv"),
        index=False
    )

    # ----------------- Fact Table -----------------

    fact_bmw = (
        df.merge(dim_date, on="Year", how="left")
          .merge(dim_model, left_on="Model", right_on="Model_Name", how="left")
          .merge(dim_region, on="Region", how="left")
          .merge(dim_vehicle, on=["Fuel_Type", "Transmission", "Color"], how="left")
          .merge(dim_sales_class, on="Sales_Classification", how="left")
    )

    fact_bmw = fact_bmw[
        [
            "Date_Key", "Model_Key", "Region_Key",
            "Vehicle_Key", "Sales_Class_Key",
            "Sales_Volume", "Price_USD", "Revenue_USD",
            "Engine_Size_L", "Mileage_KM", "Vehicle_Age"
        ]
    ]

    fact_path = os.path.join(processed_dir, "fact_bmw_sales.csv")
    fact_bmw.to_csv(fact_path, index=False)
    print("Fact table saved")

    return df, fact_bmw


def validate_bmw_data(fact_df):
    """
    Validates fact table integrity.
    """
    print("\n--- Validating BMW Fact Table ---")
    null_cols = fact_df.columns[fact_df.isnull().any()].tolist()
    if null_cols:
        raise ValueError(f"Unexpected NULLs found in columns: {null_cols}")
    print("BMW data validation passed successfully")
