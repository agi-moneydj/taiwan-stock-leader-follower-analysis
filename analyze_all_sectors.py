#!/usr/bin/env python3
"""
Batch Sector Analysis Script
Analyzes all sectors in sectorInfo directory for a given period.
"""

import os
import subprocess
import sys
from pathlib import Path
import time

def get_sector_files(sector_dir):
    """Get all sector files except DJ_IC基板 (already analyzed)."""
    sector_files = []
    for file in Path(sector_dir).glob("DJ_*.txt"):
        if file.stem != "DJ_IC基板":  # Skip already analyzed sector
            sector_files.append(file.stem)
    return sorted(sector_files)

def run_sector_analysis(sector, start_period, end_period):
    """Run analysis for a single sector."""
    print(f"\n{'='*60}")
    print(f"ANALYZING SECTOR: {sector}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable, 
        "SectorAnalyzer.py", 
        "--start", start_period,
        "--end", end_period,
        "--sector", sector
    ]
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
        end_time = time.time()
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {sector} (took {end_time-start_time:.1f}s)")
            return True, f"Success: {sector}"
        else:
            print(f"❌ FAILED: {sector}")
            print(f"Error: {result.stderr}")
            return False, f"Failed: {sector} - {result.stderr[:100]}"
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {sector} (>5 minutes)")
        return False, f"Timeout: {sector}"
    except Exception as e:
        print(f"💥 ERROR: {sector} - {str(e)}")
        return False, f"Error: {sector} - {str(e)}"

def main():
    start_period = "202506"
    end_period = "202506"
    sector_dir = "sectorInfo"
    
    print(f"Batch Sector Analysis")
    print(f"Period: {start_period} - {end_period}")
    print(f"Excluding: DJ_IC基板 (already analyzed)")
    
    # Get all sectors
    sectors = get_sector_files(sector_dir)
    print(f"Total sectors to analyze: {len(sectors)}")
    
    # Results tracking
    results = []
    successful = 0
    failed = 0
    
    # Analyze each sector
    for i, sector in enumerate(sectors, 1):
        print(f"\n[{i}/{len(sectors)}] Processing: {sector}")
        
        success, message = run_sector_analysis(sector, start_period, end_period)
        results.append(message)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Show progress
        print(f"Progress: {i}/{len(sectors)} ({successful} success, {failed} failed)")
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"BATCH ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Total sectors processed: {len(sectors)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(sectors)*100:.1f}%")
    
    # Save results summary
    summary_file = Path("output") / "batch_analysis_summary.txt"
    summary_file.parent.mkdir(exist_ok=True)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Batch Sector Analysis Summary\n")
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
        print(f"\n🎉 All sectors analyzed successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())