#!/usr/bin/env python3
"""
Generate Download Commands Script
Creates individual download commands for all sectors except DJ_IC基板
"""

from pathlib import Path

def main():
    sector_dir = Path("sectorInfo")
    start_period = "202506"
    end_period = "202506"
    
    # Get all sector files except DJ_IC基板
    sectors = []
    for file in sector_dir.glob("DJ_*.txt"):
        if file.stem != "DJ_IC基板":
            sectors.append(file.stem)
    
    sectors.sort()
    
    print(f"# Download commands for all sectors (Period: {start_period}-{end_period})")
    print(f"# Total sectors: {len(sectors)}")
    print(f"# Excluding: DJ_IC基板 (already downloaded)")
    print()
    
    # Generate individual commands
    for i, sector in enumerate(sectors, 1):
        print(f"# [{i}/{len(sectors)}] {sector}")
        print(f"python GetSectorData.py --start {start_period} --end {end_period} --sector {sector}")
        print()
    
    # Also save to file
    output_file = Path("download_commands.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Download commands for all sectors (Period: {start_period}-{end_period})\n")
        f.write(f"# Total sectors: {len(sectors)}\n")
        f.write(f"# Excluding: DJ_IC基板 (already downloaded)\n\n")
        
        for i, sector in enumerate(sectors, 1):
            f.write(f"# [{i}/{len(sectors)}] {sector}\n")
            f.write(f"python GetSectorData.py --start {start_period} --end {end_period} --sector {sector}\n\n")
    
    print(f"Commands also saved to: {output_file}")
    print(f"\nTo run all downloads, you can either:")
    print(f"1. Use the batch script: python download_all_sectors.py")
    print(f"2. Run individual commands from: {output_file}")

if __name__ == "__main__":
    main()