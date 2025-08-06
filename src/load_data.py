import os
import logging
import argparse
import pandas as pd
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from db_config import engine

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Data normalization ---
def load_and_normalize_csv(csv_path: str) -> Optional[pd.DataFrame]:
    try:
        logger.info(f"Loading CSV: {csv_path}")
        df = pd.read_csv(csv_path)

        # Normalize text fields
        manufacturer_map = {
            "dawa life sciences": "dawa ltd",
            "dawa limited": "dawa ltd",
            "dawa ltd": "dawa ltd",
            "dawa pharmaceuticals": "dawa ltd",
            "dawa pharmaceuticals ltd": "dawa ltd",
        }

        df['manufacturer'] = df['manufacturer'].astype(str).str.strip().str.lower().replace(manufacturer_map)
        df['product_name'] = df['product_name'].astype(str).str.strip()
        df['inn_name'] = df['inn_name'].astype(str).str.strip()
        df['reason'] = df['reason'].astype(str).str.strip()

        logger.info("Data normalization complete.")
        return df

    except FileNotFoundError:
        logger.error(f"File not found: {csv_path}")
        return None
    except Exception as e:
        logger.error(f"Failed to load/normalize data: {e}", exc_info=True)
        return None

# --- Insert Our DB ---
def insert_to_db(df: Optional[pd.DataFrame], table_name: str = 'recalls') -> None:
    if df is None or df.empty:
        logger.warning("No data to insert.")
        return

    try:
        df.to_sql(table_name, con=engine, if_exists='append', index=False, method='multi')
        logger.info(f"Inserted {len(df)} rows into '{table_name}' table.")
    except SQLAlchemyError as e:
        logger.error(f"Database insert failed: {e}", exc_info=True)

# --- CLI entry point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load and insert recall data into PostgreSQL.")
    parser.add_argument('--file', type=str, required=True, help='Path to the CSV file')
    parser.add_argument('--table', type=str, default='recalls', help='Target table name (default: recalls)')
    args = parser.parse_args()

    df = load_and_normalize_csv(args.file)
    insert_to_db(df, args.table)

#End. 