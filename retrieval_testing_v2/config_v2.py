"""
Configuration file for Retrieval Testing V2

This file contains all configuration settings for the retrieval evaluation system.
Supports multiple XML books - default is anf01.xml but can be changed via environment
variable or command line argument.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === DIRECTORY SETUP ===
# Get the directory where this config file is located
CONFIG_DIR = Path(__file__).parent.resolve()

# === API CONFIGURATION ===
# Server endpoint for testing
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
TEST_ENDPOINT = f"{API_BASE_URL}/test"

# LLM API Key for question generation (Claude/Anthropic)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# === FILE PATHS ===
# Input XML file - can be overridden via INPUT_XML_FILE env var or command line
# Default: data/anf01.xml in the testing folder
DEFAULT_XML_FILE = CONFIG_DIR / "data" / "anf01.xml"
INPUT_XML_FILE = os.getenv("INPUT_XML_FILE", str(DEFAULT_XML_FILE))

# Helper function to get book name from XML path
def get_book_name(xml_path: str = None) -> str:
    """Extract book name from XML file path (e.g., 'anf01' from 'anf01.xml')"""
    path = xml_path or INPUT_XML_FILE
    return Path(path).stem

# Output files - will include book name for clarity
BOOK_NAME = get_book_name()
OUTPUT_DIR = CONFIG_DIR / "output"
FILTERED_PARAGRAPHS_CSV = str(OUTPUT_DIR / f"filtered_paragraphs_{BOOK_NAME}.csv")
QUESTIONS_JSON = str(OUTPUT_DIR / f"test_questions_{BOOK_NAME}.json")
RESULTS_JSON_PREFIX = f"test_results_{BOOK_NAME}"
ANALYTICS_REPORT_PREFIX = f"analytics_report_{BOOK_NAME}"

# === DATA FILTERING CONFIGURATION ===
# Minimum paragraph length to include (in characters)
MIN_PARAGRAPH_LENGTH = 100

# Maximum paragraph length (very long paragraphs may not be useful)
MAX_PARAGRAPH_LENGTH = 5000

# Keywords to exclude (title pages, indexes, etc.)
EXCLUDE_KEYWORDS = [
    "table of contents",
    "index",
    "title page",
    "copyright",
    "contents of volume",
    "introductory note",
    "preface"
]

# === QUESTION GENERATION CONFIGURATION ===
# Number of questions to generate per paragraph
QUESTIONS_PER_PARAGRAPH = 1

# Question types to generate
QUESTION_TYPES = ["specific"]  # Start with specific questions only
# Future: ["specific", "broad"]

# LLM settings for question generation
QUESTION_GEN_TEMPERATURE = 0.7
QUESTION_GEN_MAX_TOKENS = 200

# === RETRIEVAL TESTING CONFIGURATION ===
# Number of results to retrieve from Manticore
TOP_K = 15

# Use agentic RAG or regular RAG
USE_AGENTIC = True

# Works to filter (e.g., ["anf01"])
FILTER_WORKS = ["anf01"]

# Delay between API requests (seconds) to avoid overloading
REQUEST_DELAY = 0.5

# === SCORING CONFIGURATION ===
# Points awarded based on ranking position
SCORE_RANK_1_3 = 3      # Gold paragraph in top 3
SCORE_RANK_4_10 = 2     # Gold paragraph in ranks 4-10
SCORE_RANK_BEYOND_10 = 1  # Gold paragraph beyond rank 10
PENALTY_MISSING = -2     # Missing a gold paragraph

# === ANALYTICS CONFIGURATION ===
# Labels for scoring ranges (normalized score 0-1)
SCORE_LABELS = {
    (0.9, 1.0): "Excellent",
    (0.7, 0.9): "Good",
    (0.5, 0.7): "Mixed Relevance",
    (0.3, 0.5): "Poor",
    (0.0, 0.3): "Very Poor"
}

# === BATCH PROCESSING ===
# Process paragraphs in batches for question generation
BATCH_SIZE = 10

# Maximum number of paragraphs to process (set to None for all)
MAX_PARAGRAPHS = None  # Set to a number like 50 for testing

# === OUTPUT CONFIGURATION ===
# Whether to save detailed results
SAVE_DETAILED_RESULTS = True

# Whether to print progress during processing
VERBOSE = True

# === HELPER FUNCTIONS ===
def ensure_directories():
    """Create output and data directories if they don't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    (CONFIG_DIR / "data").mkdir(exist_ok=True)

def set_input_xml(xml_path: str):
    """
    Set a new input XML file and update related paths.
    
    Args:
        xml_path: Path to XML file (absolute or relative to config dir)
    """
    global INPUT_XML_FILE, BOOK_NAME, FILTERED_PARAGRAPHS_CSV, QUESTIONS_JSON
    global RESULTS_JSON_PREFIX, ANALYTICS_REPORT_PREFIX
    
    # Resolve path
    path = Path(xml_path)
    if not path.is_absolute():
        path = CONFIG_DIR / xml_path
    
    INPUT_XML_FILE = str(path)
    BOOK_NAME = path.stem
    
    # Update output file names
    FILTERED_PARAGRAPHS_CSV = str(OUTPUT_DIR / f"filtered_paragraphs_{BOOK_NAME}.csv")
    QUESTIONS_JSON = str(OUTPUT_DIR / f"test_questions_{BOOK_NAME}.json")
    RESULTS_JSON_PREFIX = f"test_results_{BOOK_NAME}"
    ANALYTICS_REPORT_PREFIX = f"analytics_report_{BOOK_NAME}"

def get_available_books():
    """List available XML books in the data directory."""
    data_dir = CONFIG_DIR / "data"
    if data_dir.exists():
        return [f.stem for f in data_dir.glob("*.xml")]
    return []

# === VALIDATION ===
def validate_config(require_api_key: bool = True):
    """
    Validate that required configuration is present.
    
    Args:
        require_api_key: Whether to require API key (not needed for data prep)
    """
    errors = []
    
    if require_api_key and not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY not set in environment")
    
    if not Path(INPUT_XML_FILE).exists():
        errors.append(f"Input XML file not found: {INPUT_XML_FILE}")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(errors))
    
    return True

# Ensure directories exist on import
ensure_directories()

if __name__ == "__main__":
    # Test configuration
    print("=" * 60)
    print(" Retrieval Testing Configuration ".center(60, "="))
    print("=" * 60)
    print()
    
    print("📂 Directories:")
    print(f"   Config Dir: {CONFIG_DIR}")
    print(f"   Data Dir:   {CONFIG_DIR / 'data'}")
    print(f"   Output Dir: {OUTPUT_DIR}")
    print()
    
    print("📚 Available Books:")
    books = get_available_books()
    if books:
        for book in books:
            marker = "→" if book == BOOK_NAME else " "
            print(f"   {marker} {book}")
    else:
        print("   (No XML files in data/ directory)")
    print()
    
    print(f"⚙️  Current Settings:")
    print(f"   Input XML:     {INPUT_XML_FILE}")
    print(f"   Book Name:     {BOOK_NAME}")
    print(f"   API Endpoint:  {TEST_ENDPOINT}")
    print(f"   Top K:         {TOP_K}")
    print(f"   Use Agentic:   {USE_AGENTIC}")
    print()
    
    # Validate
    try:
        validate_config(require_api_key=False)
        print("✅ Configuration validated (XML file found)")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    
    if ANTHROPIC_API_KEY:
        print("✅ Anthropic API key is set")
    else:
        print("⚠️  Anthropic API key not set (needed for question generation)")
    
    print()
    print("=" * 60)

