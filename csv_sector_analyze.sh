#!/bin/bash

# CSV Sector Analysis Script
# Analyzes sectors using the csv_based_leader_follower_analyzer.py
# 
# Usage:
#   ./csv_sector_analyze.sh --start YYYYMM --end YYYYMM [--sectors "sector1,sector2,sector3"]
#   ./csv_sector_analyze.sh --start 202505 --end 202506
#   ./csv_sector_analyze.sh --start 202505 --end 202506 --sectors "DJ_IC基板,DJ_IC設計,DJ_散熱模組"

set -e  # Exit on any error

# Default values
START_DATE=""
END_DATE=""
SECTOR_LIST=""
AUTO_CONVERT=true
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECTOR_INFO_DIR="${SCRIPT_DIR}/sectorInfo"
CSV_ANALYZER="${SCRIPT_DIR}/csv_based_leader_follower_analyzer.py"
TXT_CONVERTER="${SCRIPT_DIR}/convert_txt_to_csv.py"
CSV_INPUT_DIR="${SCRIPT_DIR}/csv"
CSV_OUTPUT_DIR="${SCRIPT_DIR}/csv_converted"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "CSV Sector Analysis Script"
    echo ""
    echo "Usage:"
    echo "  $0 --start YYYYMM --end YYYYMM [--sectors \"sector1,sector2,sector3\"]"
    echo ""
    echo "Parameters:"
    echo "  --start YYYYMM    Start date in YYYYMM format (required)"
    echo "  --end YYYYMM      End date in YYYYMM format (required)"
    echo "  --sectors LIST    Comma-separated list of sectors (optional)"
    echo "  --no-convert     Skip automatic TXT to CSV conversion"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --start 202505 --end 202506"
    echo "  $0 --start 202505 --end 202506 --sectors \"DJ_IC基板,DJ_IC設計,DJ_散熱模組\""
    echo ""
    echo "Available sectors:"
    if [ -d "$SECTOR_INFO_DIR" ]; then
        for file in "$SECTOR_INFO_DIR"/DJ_*.txt; do
            if [ -f "$file" ]; then
                sector_name=$(basename "$file" .txt)
                echo "  - $sector_name"
            fi
        done
    fi
}

# Function to validate date format
validate_date() {
    local date=$1
    if [[ ! $date =~ ^[0-9]{6}$ ]]; then
        print_error "Invalid date format: $date. Expected YYYYMM format."
        return 1
    fi
    
    local year=${date:0:4}
    local month=${date:4:2}
    
    if [ $year -lt 2020 ] || [ $year -gt 2030 ]; then
        print_error "Invalid year: $year. Expected range 2020-2030."
        return 1
    fi
    
    if [ $month -lt 1 ] || [ $month -gt 12 ]; then
        print_error "Invalid month: $month. Expected range 01-12."
        return 1
    fi
    
    return 0
}

# Function to get all available sectors
get_all_sectors() {
    local sectors=()
    if [ -d "$SECTOR_INFO_DIR" ]; then
        for file in "$SECTOR_INFO_DIR"/DJ_*.txt; do
            if [ -f "$file" ]; then
                sector_name=$(basename "$file" .txt)
                sectors+=("$sector_name")
            fi
        done
    fi
    
    if [ ${#sectors[@]} -eq 0 ]; then
        print_error "No sector files found in $SECTOR_INFO_DIR"
        return 1
    fi
    
    printf "%s\n" "${sectors[@]}"
}

# Function to check if sector file exists
check_sector_exists() {
    local sector=$1
    local sector_file="${SECTOR_INFO_DIR}/${sector}.txt"
    
    if [ ! -f "$sector_file" ]; then
        print_error "Sector file not found: $sector_file"
        return 1
    fi
    return 0
}

# Function to convert TXT data to CSV format
convert_txt_to_csv() {
    local sector=$1
    
    print_info "Converting TXT data to CSV format for sector: $sector..."
    
    # Check if converter exists
    if [ ! -f "$TXT_CONVERTER" ]; then
        print_error "TXT converter script not found: $TXT_CONVERTER"
        return 1
    fi
    
    # Get stock list for the sector
    local sector_file="${SECTOR_INFO_DIR}/${sector}.txt"
    if [ ! -f "$sector_file" ]; then
        print_error "Sector file not found: $sector_file"
        return 1
    fi
    
    # Extract stock codes (remove .TW suffix)
    local stocks_list=""
    while IFS= read -r line; do
        # Remove whitespace, carriage returns, and check if line contains stock code
        line=$(echo "$line" | tr -d '\r' | xargs)
        if [[ $line =~ ^([0-9]+)\.TW$ ]]; then
            stock_code="${BASH_REMATCH[1]}"
            if [ -n "$stocks_list" ]; then
                stocks_list="${stocks_list},${stock_code}"
            else
                stocks_list="$stock_code"
            fi
        fi
    done < "$sector_file"
    
    if [ -z "$stocks_list" ]; then
        print_error "No stock codes found in sector file: $sector_file"
        return 1
    fi
    
    print_info "Converting stocks: $stocks_list"
    
    # Run the converter
    if ! python "$TXT_CONVERTER" --input-dir "$CSV_INPUT_DIR" --output-dir "$CSV_OUTPUT_DIR" --stocks "$stocks_list"; then
        print_error "Failed to convert TXT data for sector: $sector"
        return 1
    fi
    
    print_success "TXT to CSV conversion completed for sector: $sector"
    return 0
}

# Function to analyze a single sector
analyze_sector() {
    local sector=$1
    local start_date=$2
    local end_date=$3
    
    print_info "Analyzing sector: $sector ($start_date to $end_date)"
    
    # Check if sector file exists
    if ! check_sector_exists "$sector"; then
        return 1
    fi
    
    # Convert TXT to CSV if enabled
    if [ "$AUTO_CONVERT" = true ]; then
        if ! convert_txt_to_csv "$sector"; then
            print_warning "TXT conversion failed for $sector, trying analysis anyway..."
        fi
    fi
    
    print_info "Running CSV-based leader-follower analysis for $sector..."
    
    # Determine which directory to use for CSV data
    local csv_backup_dir=""
    if [ "$AUTO_CONVERT" = true ] && [ -d "$CSV_OUTPUT_DIR" ]; then
        # Temporarily rename original csv directory and create symlink to converted data
        if [ -d "${SCRIPT_DIR}/csv" ]; then
            csv_backup_dir="${SCRIPT_DIR}/csv_original_backup"
            mv "${SCRIPT_DIR}/csv" "$csv_backup_dir"
        fi
        ln -sf "${CSV_OUTPUT_DIR}" "${SCRIPT_DIR}/csv"
    fi
    
    # Run the CSV-based analyzer
    analyzer_result=0
    if ! python "$CSV_ANALYZER" --start "$start_date" --end "$end_date" --sector "$sector" --base-dir "$SCRIPT_DIR"; then
        analyzer_result=1
    fi
    
    # Restore original csv directory if we made changes
    if [ -n "$csv_backup_dir" ]; then
        rm -f "${SCRIPT_DIR}/csv"
        if [ -d "$csv_backup_dir" ]; then
            mv "$csv_backup_dir" "${SCRIPT_DIR}/csv"
        fi
    fi
    
    if [ $analyzer_result -ne 0 ]; then
        print_error "Failed to run CSV-based analysis for sector: $sector"
        return 1
    fi
    
    print_success "Analysis completed for sector: $sector"
    return 0
}

# Function to run analysis for multiple sectors
run_analysis() {
    local start_date=$1
    local end_date=$2
    local sectors_to_analyze=()
    
    if [ -n "$SECTOR_LIST" ]; then
        # Parse comma-separated sector list
        IFS=',' read -ra sectors_to_analyze <<< "$SECTOR_LIST"
        # Trim whitespace
        for i in "${!sectors_to_analyze[@]}"; do
            sectors_to_analyze[i]=$(echo "${sectors_to_analyze[i]}" | xargs)
        done
        print_info "Analyzing specified sectors: ${sectors_to_analyze[*]}"
    else
        # Get all available sectors
        print_info "No sector list provided, analyzing all available sectors..."
        mapfile -t sectors_to_analyze < <(get_all_sectors)
        if [ ${#sectors_to_analyze[@]} -eq 0 ]; then
            print_error "No sectors found to analyze"
            return 1
        fi
        print_info "Found ${#sectors_to_analyze[@]} sectors to analyze"
    fi
    
    # Summary variables
    local total_sectors=${#sectors_to_analyze[@]}
    local successful_sectors=0
    local failed_sectors=()
    
    print_info "Starting CSV-based analysis for $total_sectors sectors..."
    echo "=================================================="
    
    # Analyze each sector
    for sector in "${sectors_to_analyze[@]}"; do
        echo ""
        print_info "Processing sector $((successful_sectors + ${#failed_sectors[@]} + 1))/$total_sectors: $sector"
        echo "--------------------------------------------------"
        
        if analyze_sector "$sector" "$start_date" "$end_date"; then
            ((successful_sectors++))
            print_success "✓ $sector analysis completed successfully"
        else
            failed_sectors+=("$sector")
            print_error "✗ $sector analysis failed"
        fi
        
        # Add a brief pause between sectors to avoid overwhelming the system
        sleep 1
    done
    
    # Print summary
    echo ""
    echo "=================================================="
    print_info "CSV ANALYSIS SUMMARY"
    echo "=================================================="
    print_success "Successfully analyzed: $successful_sectors/$total_sectors sectors"
    
    if [ ${#failed_sectors[@]} -gt 0 ]; then
        print_warning "Failed sectors (${#failed_sectors[@]}):"
        for failed_sector in "${failed_sectors[@]}"; do
            echo "  - $failed_sector"
        done
    fi
    
    echo ""
    print_info "Analysis period: $start_date to $end_date"
    print_info "Output files are saved in: ${SCRIPT_DIR}/output/"
    print_info "Interactive HTML files: output/{sector}/interactive_multi_stock_trend_YYYYMMDD.html"
    
    if [ $successful_sectors -eq $total_sectors ]; then
        print_success "🎉 All sectors analyzed successfully!"
        return 0
    else
        print_warning "⚠️ Some sectors failed to analyze. Check the errors above."
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --start)
            START_DATE="$2"
            shift 2
            ;;
        --end)
            END_DATE="$2"
            shift 2
            ;;
        --sectors)
            SECTOR_LIST="$2"
            shift 2
            ;;
        --no-convert)
            AUTO_CONVERT=false
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown parameter: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$START_DATE" ] || [ -z "$END_DATE" ]; then
    print_error "Missing required parameters --start and --end"
    show_usage
    exit 1
fi

# Validate date formats
if ! validate_date "$START_DATE"; then
    exit 1
fi

if ! validate_date "$END_DATE"; then
    exit 1
fi

# Check if start date is before or equal to end date
if [ "$START_DATE" -gt "$END_DATE" ]; then
    print_error "Start date ($START_DATE) must be before or equal to end date ($END_DATE)"
    exit 1
fi

# Check if required files exist
if [ ! -f "$CSV_ANALYZER" ]; then
    print_error "CSV analyzer script not found: $CSV_ANALYZER"
    exit 1
fi

if [ ! -d "$SECTOR_INFO_DIR" ]; then
    print_error "Sector info directory not found: $SECTOR_INFO_DIR"
    exit 1
fi

# Check converter script if auto-convert is enabled
if [ "$AUTO_CONVERT" = true ]; then
    if [ ! -f "$TXT_CONVERTER" ]; then
        print_error "TXT converter script not found: $TXT_CONVERTER"
        print_info "Use --no-convert to skip automatic conversion"
        exit 1
    fi
    
    if [ ! -d "$CSV_INPUT_DIR" ]; then
        print_error "CSV input directory not found: $CSV_INPUT_DIR"
        print_info "Expected directory: $CSV_INPUT_DIR"
        exit 1
    fi
fi

# Show configuration
echo "=================================================="
print_info "CSV-Based Sector Analysis"
echo "=================================================="
print_info "Analysis period: $START_DATE to $END_DATE"
print_info "Script directory: $SCRIPT_DIR"
print_info "Sector info directory: $SECTOR_INFO_DIR"
print_info "CSV analyzer: $CSV_ANALYZER"
if [ "$AUTO_CONVERT" = true ]; then
    print_info "Auto-convert: ENABLED"
    print_info "TXT converter: $TXT_CONVERTER"
    print_info "CSV input dir: $CSV_INPUT_DIR"
    print_info "CSV output dir: $CSV_OUTPUT_DIR"
else
    print_info "Auto-convert: DISABLED"
fi
if [ -n "$SECTOR_LIST" ]; then
    print_info "Specified sectors: $SECTOR_LIST"
else
    print_info "Mode: Analyze all available sectors"
fi
echo "=================================================="

# Run the analysis
run_analysis "$START_DATE" "$END_DATE"