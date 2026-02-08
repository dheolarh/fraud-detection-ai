#!/usr/bin/env python3
"""
PaySim Dataset Loader
Downloads and loads PaySim synthetic fraud dataset into database.

Dataset: https://www.kaggle.com/datasets/ealaxi/paysim1
File: PS_20174392719_1491204439457_log.csv (6.3M records)
"""

import sys
import os
from pathlib import Path
import pandas as pd
from loguru import logger

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from storage.database import get_db_context
from storage.repositories import PaySimRepository
from core.exceptions import DatabaseError


PAYSIM_URL = "https://www.kaggle.com/datasets/ealaxi/paysim1"
DATASET_DIR = Path(__file__).parent.parent / "data_sample"
DATASET_PATH = DATASET_DIR / "PS_20174392719_1491204439457_log.csv"
FULL_DATASET_NAME = "PS_20174392719_1491204439457_log.csv"


def check_file_size():
    """Check CSV file size without loading it"""
    if DATASET_PATH.exists():
        size_bytes = DATASET_PATH.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        return size_mb
    return 0


def verify_dataset_exists():
    """Verify PaySim dataset exists"""
    if DATASET_PATH.exists():
        size_mb = check_file_size()
        logger.info(f"Dataset found: {DATASET_PATH}")
        logger.info(f"File size: {size_mb:.2f} MB")
        
        if size_mb > 100:
            logger.warning(f"Large file detected ({size_mb:.2f} MB). Will use chunked processing.")
        
        return True
    else:
        logger.error(f"Dataset not found: {DATASET_PATH}")
        logger.info("Please download from: https://www.kaggle.com/datasets/ealaxi/paysim1")
        logger.info(f"Place file in: {DATASET_DIR}")
        return False


def load_paysim_to_dataframe(sample_size: int = None, chunk_size: int = 10000) -> pd.DataFrame:
    """
    Load PaySim CSV into pandas DataFrame using chunked reading for memory efficiency.
    For 500MB+ files, this prevents system crashes.
    """
    try:
        logger.info(f"Loading PaySim data from: {DATASET_PATH}")
        
        if not DATASET_PATH.exists():
            raise FileNotFoundError(f"PaySim dataset not found: {DATASET_PATH}")
        
        file_size_mb = check_file_size()
        
        if file_size_mb > 100:
            logger.info(f"Using chunked loading for {file_size_mb:.2f} MB file...")
            
            chunks = []
            total_rows = 0
            
            for chunk in pd.read_csv(DATASET_PATH, chunksize=chunk_size):
                chunks.append(chunk)
                total_rows += len(chunk)
                
                if sample_size and total_rows >= sample_size:
                    logger.info(f"Reached sample size limit: {sample_size}")
                    break
                
                if len(chunks) % 10 == 0:
                    logger.info(f"Loaded {total_rows:,} rows...")
            
            df = pd.concat(chunks, ignore_index=True)
            
            if sample_size:
                df = df.head(sample_size)
        else:
            df = pd.read_csv(DATASET_PATH, nrows=sample_size)
        
        logger.info(f"Loaded {len(df):,} records from PaySim dataset")
        
        # Validate columns
        expected_cols = ['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 
                        'newbalanceOrig', 'nameDest', 'oldbalanceDest', 
                        'newbalanceDest', 'isFraud', 'isFlaggedFraud']
        
        if not all(col in df.columns for col in expected_cols):
            raise ValueError(f"Missing expected columns. Found: {df.columns.tolist()}")
        
        fraud_count = df['isFraud'].sum()
        fraud_rate = (fraud_count / len(df)) * 100
        logger.info(f"Fraud statistics: {fraud_count} fraudulent ({fraud_rate:.2f}%)")
        
        return df
    
    except Exception as e:
        logger.error(f"Failed to load PaySim data: {e}")
        raise


def prepare_paysim_records(df: pd.DataFrame) -> list:
    """Convert DataFrame to database record format"""
    try:
        records = []
        for _, row in df.iterrows():
            record = {
                'step': int(row['step']),
                'type': str(row['type']),
                'amount': float(row['amount']),
                'nameOrig': str(row['nameOrig']),
                'oldbalanceOrg': float(row['oldbalanceOrg']),
                'newbalanceOrig': float(row['newbalanceOrig']),
                'nameDest': str(row['nameDest']),
                'oldbalanceDest': float(row['oldbalanceDest']),
                'newbalanceDest': float(row['newbalanceDest']),
                'isFraud': int(row['isFraud']),
                'isFlaggedFraud': int(row['isFlaggedFraud'])
            }
            records.append(record)
        
        logger.info(f"Prepared {len(records)} records for database insertion")
        return records
    
    except Exception as e:
        logger.error(f"Failed to prepare PaySim records: {e}")
        raise


def load_paysim_to_database(sample_size: int = 50000, batch_size: int = 1000):
    """Main function to load PaySim data into database"""
    try:
        logger.info("=== PaySim Dataset Loader ===")
        logger.info(f"Target sample size: {sample_size:,} records")
        
        if not verify_dataset_exists():
            logger.error("Dataset not available. Exiting.")
            return False
        
        # Load data
        df = load_paysim_to_dataframe(sample_size)
        
        # Prepare records
        records = prepare_paysim_records(df)
        
        # Insert in batches
        logger.info("Inserting records into database...")
        with get_db_context() as db:
            from storage.models import PaySimData
            repo = PaySimRepository(db)
            
            # Check if data already loaded
            existing_count = db.query(PaySimData).count()
            if existing_count > 0:
                logger.warning(f"Database already contains {existing_count} PaySim records")
                user_input = input("Clear and reload? (yes/no): ")
                if user_input.lower() != 'yes':
                    logger.info("Skipping reload")
                    return True
                
                # Clear existing data
                db.query(PaySimData).delete()
                db.commit()
                logger.info("Cleared existing PaySim data")
            
            # Batch insert for performance
            total_inserted = 0
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                repo.bulk_create(batch)
                total_inserted += len(batch)
                logger.info(f"Progress: {total_inserted}/{len(records)} records inserted")
            
            # Get fraud statistics
            stats = repo.count_fraud()
            logger.success("PaySim data loaded successfully!")
            logger.info(f"Total records: {stats['total']}")
            logger.info(f"Fraudulent: {stats['fraud']} ({stats['fraud_rate']:.2f}%)")
            logger.info(f"Legitimate: {stats['legitimate']}")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to load PaySim data: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load PaySim dataset into database')
    parser.add_argument('--sample-size', type=int, default=50000, 
                       help='Number of records to load (default: 50000)')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Batch size for insertion (default: 1000)')
    
    args = parser.parse_args()
    
    success = load_paysim_to_database(args.sample_size, args.batch_size)
    sys.exit(0 if success else 1)
