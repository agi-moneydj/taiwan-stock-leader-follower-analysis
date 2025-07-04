#!/usr/bin/env python3
"""
Generate Windows Download Commands Script
Creates download commands for all sectors from 202501 to 202506 except DJ_IC基板
Formatted for Windows copy-paste execution
"""

from pathlib import Path

def main():
    sector_dir = Path("sectorInfo")
    start_period = "202501"
    end_period = "202506"
    
    # Get all sector files except DJ_IC基板
    sectors = []
    for file in sector_dir.glob("DJ_*.txt"):
        if file.stem != "DJ_IC基板":
            sectors.append(file.stem)
    
    sectors.sort()
    
    print(f"REM Download commands for all sectors (Period: {start_period}-{end_period})")
    print(f"REM Total sectors: {len(sectors)}")
    print(f"REM Excluding: DJ_IC基板")
    print(f"REM Copy and paste these commands in Windows Command Prompt")
    print()
    
    # Generate individual commands for Windows
    for i, sector in enumerate(sectors, 1):
        print(f"REM [{i}/{len(sectors)}] {sector}")
        print(f"python GetSectorData.py --start {start_period} --end {end_period} --sector {sector}")
        print()
    
    # Also save to batch file for Windows
    batch_file = Path("download_all_sectors.bat")
    with open(batch_file, 'w', encoding='utf-8') as f:
        f.write(f"@echo off\n")
        f.write(f"REM Download commands for all sectors (Period: {start_period}-{end_period})\n")
        f.write(f"REM Total sectors: {len(sectors)}\n")
        f.write(f"REM Excluding: DJ_IC基板\n\n")
        
        for i, sector in enumerate(sectors, 1):
            f.write(f"REM [{i}/{len(sectors)}] {sector}\n")
            f.write(f"echo Downloading {sector}...\n")
            f.write(f"python GetSectorData.py --start {start_period} --end {end_period} --sector {sector}\n")
            f.write(f"if errorlevel 1 (\n")
            f.write(f"    echo ERROR: Failed to download {sector}\n")
            f.write(f"    pause\n")
            f.write(f") else (\n")
            f.write(f"    echo SUCCESS: {sector} downloaded\n")
            f.write(f")\n\n")
        
        f.write(f"echo All downloads completed!\n")
        f.write(f"pause\n")
    
    # Save individual commands to text file
    txt_file = Path("windows_download_commands.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"# Download commands for all sectors (Period: {start_period}-{end_period})\n")
        f.write(f"# Total sectors: {len(sectors)}\n")
        f.write(f"# Excluding: DJ_IC基板\n")
        f.write(f"# Copy and paste these commands in Windows Command Prompt\n\n")
        
        for i, sector in enumerate(sectors, 1):
            f.write(f"# [{i}/{len(sectors)}] {sector}\n")
            f.write(f"python GetSectorData.py --start {start_period} --end {end_period} --sector {sector}\n\n")
    
    print(f"Files generated:")
    print(f"1. {batch_file} - Windows batch file (double-click to run)")
    print(f"2. {txt_file} - Individual commands for copy-paste")
    print(f"\nFor Windows users:")
    print(f"- Option 1: Double-click '{batch_file}' to run all downloads automatically")
    print(f"- Option 2: Copy commands from '{txt_file}' and paste in Command Prompt")

if __name__ == "__main__":
    main()