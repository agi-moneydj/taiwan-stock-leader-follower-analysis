#!/bin/bash

# Taiwan Stock Sector Analysis Script
# Analyzes sectors using the sector_leader_follower_analyzer.py
# 
# Usage:
#   ./analyze_sectors.sh --start YYYYMM --end YYYYMM [--sectors "sector1,sector2,sector3"]
#   ./analyze_sectors.sh --start 202506 --end 202506
#   ./analyze_sectors.sh --start 202501 --end 202506 --sectors "散熱模組,IC基板,IC設計"

# set -e  # Commented out to allow multiple sectors processing
# We handle errors explicitly in each function

# Default values
START_DATE=""
END_DATE=""
SECTOR_LIST=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECTOR_INFO_DIR="${SCRIPT_DIR}/sectorInfo"
PYTHON_SCRIPT="${SCRIPT_DIR}/sector_leader_follower_analyzer.py"
SECTOR_ANALYZER="${SCRIPT_DIR}/SectorAnalyzer.py"

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
    echo "Taiwan Stock Sector Analysis Script"
    echo ""
    echo "Usage:"
    echo "  $0 --start YYYYMM --end YYYYMM [--sectors \"sector1,sector2,sector3\"]"
    echo ""
    echo "Parameters:"
    echo "  --start YYYYMM    Start date in YYYYMM format (required)"
    echo "  --end YYYYMM      End date in YYYYMM format (required)"
    echo "  --sectors LIST    Comma-separated list of sectors (optional)"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --start 202506 --end 202506"
    echo "  $0 --start 202501 --end 202506 --sectors \"散熱模組,IC基板,IC設計\""
    echo ""
    echo "Available sectors:"
    if [ -d "$SECTOR_INFO_DIR" ]; then
        for file in "$SECTOR_INFO_DIR"/DJ_*.txt; do
            if [ -f "$file" ]; then
                sector_name=$(basename "$file" .txt | sed 's/^DJ_//')
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
                sector_name=$(basename "$file" .txt | sed 's/^DJ_//')
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
    local sector_file="${SECTOR_INFO_DIR}/DJ_${sector}.txt"
    
    if [ ! -f "$sector_file" ]; then
        print_error "Sector file not found: $sector_file"
        return 1
    fi
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
    
    # Step 1: Generate CSV data using SectorAnalyzer
    print_info "Step 1/2: Generating CSV data for $sector..."
    if ! python "$SECTOR_ANALYZER" --sector "DJ_$sector" --start "$start_date" --end "$end_date"; then
        print_error "Failed to generate CSV data for sector: $sector"
        return 1
    fi
    
    # Step 2: Run leader-follower analysis
    print_info "Step 2/2: Running leader-follower analysis for $sector..."
    local csv_file="${SCRIPT_DIR}/output/${sector}/combined_data_debug.csv"
    
    if [ ! -f "$csv_file" ]; then
        print_error "CSV file not found: $csv_file"
        return 1
    fi
    
    if ! python "$PYTHON_SCRIPT" "$csv_file"; then
        print_error "Failed to run leader-follower analysis for sector: $sector"
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
    
    print_info "Starting analysis for $total_sectors sectors..."
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
    print_info "ANALYSIS SUMMARY"
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
if [ ! -f "$PYTHON_SCRIPT" ]; then
    print_error "Python script not found: $PYTHON_SCRIPT"
    exit 1
fi

if [ ! -f "$SECTOR_ANALYZER" ]; then
    print_error "SectorAnalyzer script not found: $SECTOR_ANALYZER"
    exit 1
fi

if [ ! -d "$SECTOR_INFO_DIR" ]; then
    print_error "Sector info directory not found: $SECTOR_INFO_DIR"
    exit 1
fi

# Show configuration
echo "=================================================="
print_info "Taiwan Stock Sector Analysis"
echo "=================================================="
print_info "Analysis period: $START_DATE to $END_DATE"
print_info "Script directory: $SCRIPT_DIR"
print_info "Sector info directory: $SECTOR_INFO_DIR"
if [ -n "$SECTOR_LIST" ]; then
    print_info "Specified sectors: $SECTOR_LIST"
else
    print_info "Mode: Analyze all available sectors"
fi
echo "=================================================="

# Run the analysis
run_analysis "$START_DATE" "$END_DATE"