# load.py
import pandas as pd
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


# ----------------- Environment Variables -----------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


# ----------------- Column Mappings -----------------
COLUMN_MAPPINGS = {
    "Dim_Date": {
        "Date_Key": "DateKey",
        "Year": "Year",
        "Decade": "Decade"
    },
    "Dim_Model": {
        "Model_Key": "ModelKey",
        "Model_Name": "ModelName"
    },
    "Dim_Region": {
        "Region_Key": "RegionKey",
        "Region": "RegionName"
    },
    "Dim_Vehicle": {
        "Vehicle_Key": "VehicleKey",
        "Fuel_Type": "FuelType",
        "Transmission": "Transmission",
        "Color": "Color"
    },
    "Dim_Sales_Class": {
        "Sales_Class_Key": "SalesClassKey",
        "Sales_Classification": "SalesClassification"
    },
    "Fact_BMW": {
        "Date_Key": "DateKey",
        "Model_Key": "ModelKey",
        "Region_Key": "RegionKey",
        "Vehicle_Key": "VehicleKey",
        "Sales_Class_Key": "SalesClassKey",
        "Sales_Volume": "SalesVolume",
        "Price_USD": "PriceUSD",
        "Revenue_USD": "RevenueUSD",
        "Engine_Size_L": "EngineSizeL",
        "Mileage_KM": "MileageKM",
        "Vehicle_Age": "VehicleAge"
    }
}


# ----------------- MySQL Connection -----------------
def create_connection():
    """
    Create and return MySQL database connection.
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        if connection.is_connected():
            print("Connected to MySQL database")

        return connection

    except Error as e:
        raise ConnectionError(f"MySQL connection failed: {e}")


# ----------------- Create Tables -----------------
def create_tables(connection):
    """
    Create dimension and fact tables if they do not exist.
    """
    print("\n--- Creating BMW Tables ---")

    sql_statements = """
    CREATE TABLE IF NOT EXISTS Dim_Date (
        DateKey INT PRIMARY KEY,
        Year INT,
        Decade INT
    );

    CREATE TABLE IF NOT EXISTS Dim_Model (
        ModelKey INT PRIMARY KEY,
        ModelName VARCHAR(100)
    );

    CREATE TABLE IF NOT EXISTS Dim_Region (
        RegionKey INT PRIMARY KEY,
        RegionName VARCHAR(100)
    );

    CREATE TABLE IF NOT EXISTS Dim_Vehicle (
        VehicleKey INT PRIMARY KEY,
        FuelType VARCHAR(50),
        Transmission VARCHAR(50),
        Color VARCHAR(50)
    );

    CREATE TABLE IF NOT EXISTS Dim_Sales_Class (
        SalesClassKey INT PRIMARY KEY,
        SalesClassification VARCHAR(50)
    );

    CREATE TABLE IF NOT EXISTS Fact_BMW (
        DateKey INT,
        ModelKey INT,
        RegionKey INT,
        VehicleKey INT,
        SalesClassKey INT,
        SalesVolume INT,
        PriceUSD DECIMAL(10,2),
        RevenueUSD DECIMAL(10,2),
        EngineSizeL FLOAT,
        MileageKM FLOAT,
        VehicleAge INT,
        PRIMARY KEY (DateKey, ModelKey, RegionKey, VehicleKey, SalesClassKey),
        FOREIGN KEY (DateKey) REFERENCES Dim_Date(DateKey),
        FOREIGN KEY (ModelKey) REFERENCES Dim_Model(ModelKey),
        FOREIGN KEY (RegionKey) REFERENCES Dim_Region(RegionKey),
        FOREIGN KEY (VehicleKey) REFERENCES Dim_Vehicle(VehicleKey),
        FOREIGN KEY (SalesClassKey) REFERENCES Dim_Sales_Class(SalesClassKey)
    );
    """

    cursor = connection.cursor()
    for stmt in sql_statements.split(";"):
        if stmt.strip():
            cursor.execute(stmt)

    connection.commit()
    cursor.close()

    print("All BMW tables created successfully")


# ----------------- Load CSV to MySQL -----------------
def load_csv_to_mysql(connection, table_name, csv_path):
    """
    Load a CSV file into a MySQL table.
    """
    print(f"Loading {table_name}...")

    df = pd.read_csv(csv_path)

    if table_name in COLUMN_MAPPINGS:
        df.rename(columns=COLUMN_MAPPINGS[table_name], inplace=True)

    cursor = connection.cursor()

    columns = ", ".join(df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    insert_query = f"""
        INSERT IGNORE INTO {table_name} ({columns})
        VALUES ({placeholders})
    """

    for row in df.itertuples(index=False):
        cursor.execute(insert_query, tuple(row))

    connection.commit()
    cursor.close()

    print(f"{table_name} loaded successfully")


# ----------------- Run Load Process -----------------
def run_load(project_root):
    """
    Execute full loading process.
    """
    processed_dir = os.path.join(project_root, "data", "processed")

    connection = create_connection()
    create_tables(connection)

    load_csv_to_mysql(connection, "Dim_Date", os.path.join(processed_dir, "dim_date.csv"))
    load_csv_to_mysql(connection, "Dim_Model", os.path.join(processed_dir, "dim_model.csv"))
    load_csv_to_mysql(connection, "Dim_Region", os.path.join(processed_dir, "dim_region.csv"))
    load_csv_to_mysql(connection, "Dim_Vehicle", os.path.join(processed_dir, "dim_vehicle_attributes.csv"))
    load_csv_to_mysql(connection, "Dim_Sales_Class", os.path.join(processed_dir, "dim_sales_classification.csv"))
    load_csv_to_mysql(connection, "Fact_BMW", os.path.join(processed_dir, "fact_bmw_sales.csv"))

    connection.close()
    print("All BMW CSVs loaded and MySQL connection closed")

