#!/bin/bash
# Full Pipeline Runner for Retrieval Testing
# Runs all three steps: prepare data, generate questions, evaluate retrieval
#
# Usage:
#   ./run_full_pipeline_v2.sh              # Use default book (anf01)
#   ./run_full_pipeline_v2.sh anf02        # Use specific book
#   ./run_full_pipeline_v2.sh --help       # Show help

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
BOOK=""
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [book_name]"
    echo ""
    echo "Run the full retrieval testing pipeline."
    echo ""
    echo "Arguments:"
    echo "  book_name    Name of book in data/ directory (default: anf01)"
    echo ""
    echo "Examples:"
    echo "  $0              # Use default book"
    echo "  $0 anf01        # Use anf01"
    echo "  $0 anf02        # Use anf02"
    echo ""
    echo "Available books:"
    python3 prepare_data_v2.py --list 2>/dev/null || echo "  (run to see available books)"
    exit 0
fi

if [ -n "$1" ]; then
    BOOK="--book $1"
    echo "📚 Using book: $1"
fi

echo "========================================"
echo "  Retrieval Testing - Full Pipeline"
echo "========================================"
echo ""

# Check environment
if [ -z "$ANTHROPIC_API_KEY" ] && [ ! -f .env ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set and no .env file found"
    echo "   Question generation requires an API key."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Prepare Data
echo "📋 Step 1/3: Preparing data..."
echo "------------------------------------"
python3 prepare_data_v2.py $BOOK
echo ""

# Step 2: Generate Questions
echo "📋 Step 2/3: Generating questions..."
echo "------------------------------------"
python3 generate_questions_v2.py $BOOK
echo ""

# Step 3: Evaluate Retrieval
echo "📋 Step 3/3: Evaluating retrieval..."
echo "------------------------------------"
python3 evaluate_retrieval_v2.py $BOOK
echo ""

echo "========================================"
echo "✅ Full pipeline completed successfully!"
echo "========================================"
echo ""
echo "Results saved in output/ directory:"
ls -la output/*.txt output/*.json 2>/dev/null | tail -5 || echo "  (check output/ folder)"
echo ""


