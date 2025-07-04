#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GetSectorData.py - Download stock data from s-vgtick01 server using DJFile command

Usage:
    python GetSectorData.py --start 202501 --end 202506 --sector DJ_IC基板,DJ_IC封測,DJ_IC設計

Requirements:
    - DJFile command must be available in system PATH
    - Access to s-vgtick01 server
    - Sector files in sectorInfo/ folder with BIG5 encoding
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import logging
import zipfile
import shutil

# Configuration
SERVER_IP = "s-vgtick01"
BASE_LOCAL_PATH = r"D:\lab\TASave"
TICKSAVE_REMOTE_BASE = r"D:\SHARE\TICkSave\TW"
TASAVE_REMOTE_BASE = r"D:\SHARE\TASave\TW"
SECTOR_INFO_PATH = "sectorInfo"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('GetSectorData.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Download sector stock data from s-vgtick01')
    parser.add_argument('--start', required=True, help='Start period (YYYYMM), e.g., 202501')
    parser.add_argument('--end', required=True, help='End period (YYYYMM), e.g., 202506')
    parser.add_argument('--sector', required=True, help='Comma-separated sector names, e.g., DJ_IC基板,DJ_IC封測')
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.start, '%Y%m')
        datetime.strptime(args.end, '%Y%m')
    except ValueError:
        logger.error("Invalid date format. Use YYYYMM format.")
        sys.exit(1)
    
    if args.start > args.end:
        logger.error("Start date must be earlier than end date.")
        sys.exit(1)
    
    return args

def read_sector_file(sector_name):
    """Read stock symbols from sector file (BIG5 encoding)"""
    sector_file = Path(SECTOR_INFO_PATH) / f"{sector_name}.txt"
    
    if not sector_file.exists():
        logger.error(f"Sector file not found: {sector_file}")
        return []
    
    stocks = []
    try:
        with open(sector_file, 'r', encoding='big5') as f:
            for line in f:
                line = line.strip()
                if line and '.TW' in line:
                    # Extract stock symbol without .TW suffix
                    stock_id = line.split('.TW')[0]
                    if stock_id.isdigit():
                        stocks.append(stock_id)
        
        logger.info(f"Found {len(stocks)} stocks in sector {sector_name}")
        return stocks
    
    except Exception as e:
        logger.error(f"Error reading sector file {sector_file}: {e}")
        return []

def generate_date_range(start_period, end_period):
    """Generate list of YYYYMM periods between start and end"""
    periods = []
    
    start_year = int(start_period[:4])
    start_month = int(start_period[4:])
    end_year = int(end_period[:4])
    end_month = int(end_period[4:])
    
    current_year = start_year
    current_month = start_month
    
    while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
        periods.append(f"{current_year:04d}{current_month:02d}")
        
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    
    return periods

def create_stock_folder(stock_id):
    """Create local folder for stock data"""
    stock_folder = Path(BASE_LOCAL_PATH) / stock_id
    stock_folder.mkdir(parents=True, exist_ok=True)
    return stock_folder

def file_exists_locally(local_path):
    """Check if file already exists locally"""
    return Path(local_path).exists()

def execute_djfile_command(cmd_args):
    """Execute DJFile command and return success status"""
    try:
        cmd = ["DJFile"] + cmd_args
        logger.info(f"Executing: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("Download successful")
            return True
        elif result.returncode == -2:
            logger.warning("Partial download success")
            return True
        else:
            logger.error(f"Download failed with return code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        logger.error("DJFile command timed out")
        return False
    except Exception as e:
        logger.error(f"Error executing DJFile command: {e}")
        return False

def extract_zip_file(zip_path, extract_to=None):
    """Extract zip file to specified directory or same directory"""
    try:
        zip_path = Path(zip_path)
        if not zip_path.exists():
            logger.error(f"Zip file not found: {zip_path}")
            return False
        
        if extract_to is None:
            extract_to = zip_path.parent
        else:
            extract_to = Path(extract_to)
        
        extract_to.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        logger.info(f"Extracted {zip_path.name} to {extract_to}")
        return True
    
    except zipfile.BadZipFile:
        logger.error(f"Bad zip file: {zip_path}")
        return False
    except Exception as e:
        logger.error(f"Error extracting {zip_path}: {e}")
        return False

def extract_all_zips_in_folder(folder_path):
    """Extract all zip files in a folder"""
    folder_path = Path(folder_path)
    if not folder_path.exists():
        logger.warning(f"Folder not found: {folder_path}")
        return 0
    
    zip_files = list(folder_path.glob("*.zip"))
    if not zip_files:
        logger.info(f"No zip files found in {folder_path}")
        return 0
    
    success_count = 0
    for zip_file in zip_files:
        if extract_zip_file(zip_file):
            success_count += 1
    
    logger.info(f"Extracted {success_count}/{len(zip_files)} zip files in {folder_path}")
    return success_count

def download_tick_data(stock_id, period):
    """Download TICK data for a stock in specific period"""
    year = period[:4]
    month = period[4:]
    stock_prefix = stock_id[:2]
    
    remote_file = f"{TICKSAVE_REMOTE_BASE}\\{stock_prefix}\\{stock_id}\\{year}\\{month}\\Min_{period}.zip"
    local_folder = create_stock_folder(stock_id)
    local_file = local_folder / f"Min_{period}.zip"
    
    if file_exists_locally(local_file):
        logger.info(f"TICK file already exists: {local_file}")
        return True
    
    cmd_args = ["get", SERVER_IP, remote_file, str(local_folder)]
    return execute_djfile_command(cmd_args)

def download_ta_data(stock_id, period):
    """Download TA statistical data for a stock in specific period"""
    year = period[:4]
    month = period[4:]
    stock_prefix = stock_id[:2]
    
    remote_file = f"{TASAVE_REMOTE_BASE}\\{stock_prefix}\\{stock_id}\\{year}\\{month}\\TAMin_{period}.zip"
    local_folder = create_stock_folder(stock_id)
    local_file = local_folder / f"TAMin_{period}.zip"
    
    if file_exists_locally(local_file):
        logger.info(f"TA file already exists: {local_file}")
        return True
    
    cmd_args = ["get", SERVER_IP, remote_file, str(local_folder)]
    return execute_djfile_command(cmd_args)

def process_stock(stock_id, periods, processed_stocks):
    """Process a single stock for all periods"""
    if stock_id in processed_stocks:
        logger.info(f"Stock {stock_id} already processed, skipping...")
        return
    
    logger.info(f"Processing stock: {stock_id}")
    processed_stocks.add(stock_id)
    
    success_count = 0
    total_downloads = len(periods) * 2  # TICK + TA for each period
    
    for period in periods:
        logger.info(f"Downloading data for {stock_id} - {period}")
        
        # Download TICK data
        if download_tick_data(stock_id, period):
            success_count += 1
        
        # Download TA data
        if download_ta_data(stock_id, period):
            success_count += 1
    
    logger.info(f"Stock {stock_id} completed: {success_count}/{total_downloads} files downloaded")

def main():
    """Main function"""
    args = parse_arguments()
    
    logger.info(f"Starting GetSectorData.py")
    logger.info(f"Period: {args.start} to {args.end}")
    logger.info(f"Sectors: {args.sector}")
    
    # Generate date range
    periods = generate_date_range(args.start, args.end)
    logger.info(f"Processing {len(periods)} periods: {periods}")
    
    # Parse sectors
    sectors = [s.strip() for s in args.sector.split(',')]
    
    # Track processed stocks to avoid duplicates
    processed_stocks = set()
    total_stocks = 0
    
    # Process each sector
    for sector in sectors:
        logger.info(f"Processing sector: {sector}")
        stocks = read_sector_file(sector)
        
        if not stocks:
            logger.warning(f"No stocks found in sector {sector}")
            continue
        
        total_stocks += len(stocks)
        
        for stock_id in stocks:
            try:
                process_stock(stock_id, periods, processed_stocks)
            except Exception as e:
                logger.error(f"Error processing stock {stock_id}: {e}")
                continue
    
    logger.info(f"Download phase completed!")
    logger.info(f"Total stocks in sectors: {total_stocks}")
    logger.info(f"Unique stocks processed: {len(processed_stocks)}")
    
    # Extract all zip files after successful downloads
    logger.info("Starting zip extraction phase...")
    total_extracted = 0
    
    for stock_id in processed_stocks:
        stock_folder = Path(BASE_LOCAL_PATH) / stock_id
        if stock_folder.exists():
            logger.info(f"Extracting zip files for stock {stock_id}...")
            extracted_count = extract_all_zips_in_folder(stock_folder)
            total_extracted += extracted_count
    
    logger.info(f"Extraction completed! Total zip files extracted: {total_extracted}")
    logger.info(f"All processing completed successfully!")

if __name__ == "__main__":
    main()