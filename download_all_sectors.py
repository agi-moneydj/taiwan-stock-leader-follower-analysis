#!/usr/bin/env python3
"""
Batch Download Script for All Sectors
Downloads tick data using GetSectorData.py for all sectors except DJ_IC基板
"""

import os
import subprocess
import sys
from pathlib import Path
import time

def get_sector_files(sector_dir):
    """Get all sector files except DJ_IC基板."""
    sector_files = []
    for file in Path(sector_dir).glob("DJ_*.txt"):
        if file.stem != "DJ_IC基板":  # Skip DJ_IC基板 as it's already downloaded
            sector_files.append(file.stem)
    return sorted(sector_files)

def run_sector_download(sector, start_period, end_period):
    """Run GetSectorData.py for a single sector."""
    print(f"\n{'='*60}")
    print(f"DOWNLOADING SECTOR: {sector}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable, 
        "GetSectorData.py", 
        "--start", start_period,
        "--end", end_period,
        "--sector", sector
    ]
    
    try:
        start_time = time.time()
        # Run with real-time output
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 universal_newlines=True, bufsize=1)
        
        # Print output in real-time
        for line in process.stdout:
            print(line.rstrip())
        
        process.wait()
        end_time = time.time()
        
        if process.returncode == 0:
            print(f"✅ SUCCESS: {sector} (took {end_time-start_time:.1f}s)")
            return True, f"Success: {sector}"
        else:
            print(f"❌ FAILED: {sector}")
            return False, f"Failed: {sector}"
            
    except Exception as e:
        print(f"💥 ERROR: {sector} - {str(e)}")
        return False, f"Error: {sector} - {str(e)}"

def main():
    start_period = "202506"
    end_period = "202506"
    sector_dir = "sectorInfo"
    
    print(f"Batch Sector Data Download")
    print(f"Period: {start_period} - {end_period}")
    print(f"Excluding: DJ_IC基板 (already downloaded)")
    
    # Get all sectors
    sectors = get_sector_files(sector_dir)
    print(f"Total sectors to download: {len(sectors)}")
    
    # Confirm before starting
    print(f"\nThis will download data for {len(sectors)} sectors.")
    print("This may take a very long time and use significant bandwidth.")
    response = input("Do you want to continue? (y/N): ")
    
    if response.lower() != 'y':
        print("Download cancelled.")
        return 0
    
    # Results tracking
    results = []
    successful = 0
    failed = 0
    
    # Download each sector
    for i, sector in enumerate(sectors, 1):
        print(f"\n[{i}/{len(sectors)}] Processing: {sector}")
        
        success, message = run_sector_download(sector, start_period, end_period)
        results.append(message)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Show progress
        print(f"Progress: {i}/{len(sectors)} ({successful} success, {failed} failed)")
        
        # Small delay between downloads to be nice to the server
        if i < len(sectors):
            time.sleep(2)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"BATCH DOWNLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"Total sectors processed: {len(sectors)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(sectors)*100:.1f}%")
    
    # Save results summary
    summary_file = Path("download_summary.txt")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Batch Sector Download Summary\n")
        f.write(f"Period: {start_period} - {end_period}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total sectors: {len(sectors)}\n")
        f.write(f"Successful: {successful}\n")
        f.write(f"Failed: {failed}\n")
        f.write(f"Success rate: {successful/len(sectors)*100:.1f}%\n\n")
        f.write("Detailed Results:\n")
        for result in results:
            f.write(f"{result}\n")
    
    print(f"\nSummary saved to: {summary_file}")
    
    if failed > 0:
        print(f"\n⚠️  {failed} sectors failed. Check the summary for details.")
        return 1
    else:
        print(f"\n🎉 All sectors downloaded successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())