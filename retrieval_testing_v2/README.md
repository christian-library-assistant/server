# Retrieval Testing Framework

A testing framework for evaluating the Manticore retrieval system's quality and relevance.

## Overview

This framework tests whether Manticore successfully identifies and returns the most relevant paragraphs for each query. It supports testing multiple XML books and provides detailed scoring and analytics.

## Directory Structure

```
retrieval_testing_v2/
├── data/                       # XML books go here
│   └── anf01.xml              # Default: Ante-Nicene Fathers Vol 1
├── output/                     # Generated output files
│   ├── filtered_paragraphs_*.csv
│   ├── test_questions_*.json
│   ├── test_results_*.json
│   └── analytics_report_*.txt
├── config_v2.py               # Central configuration
├── utils_v2.py                # Utility functions
├── prepare_data_v2.py         # Step 1: Extract paragraphs from XML
├── generate_questions_v2.py   # Step 2: Generate test questions
├── evaluate_retrieval_v2.py   # Step 3: Run evaluation
├── evaluate_from_csv_v2.py    # Alternative: Evaluate from existing CSV
├── run_full_pipeline_v2.sh    # Run all steps
├── requirements_v2.txt        # Python dependencies
└── README.md                  # This file
```

## Quick Start

### 1. Install Dependencies

```bash
cd retrieval_testing_v2
pip install -r requirements_v2.txt
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### 3. Run the Pipeline

**For the default book (anf01):**

```bash
python prepare_data_v2.py
python generate_questions_v2.py
python evaluate_retrieval_v2.py
```

**Or use the pipeline script:**

```bash
./run_full_pipeline_v2.sh
```

## Working with Multiple Books

The framework supports testing multiple XML books. Place XML files in the `data/` directory.

### List Available Books

```bash
python prepare_data_v2.py --list
python config_v2.py  # Shows current config and available books
```

### Test a Specific Book

```bash
# Step 1: Prepare data
python prepare_data_v2.py --book anf01

# Step 2: Generate questions  
python generate_questions_v2.py --book anf01

# Step 3: Evaluate
python evaluate_retrieval_v2.py --book anf01
```

### Add a New Book

1. Place the XML file in `data/`:
   ```bash
   cp /path/to/mybook.xml data/
   ```

2. Run the pipeline:
   ```bash
   python prepare_data_v2.py --book mybook
   python generate_questions_v2.py --book mybook
   python evaluate_retrieval_v2.py --book mybook
   ```

## Pipeline Steps

### Step 1: Prepare Data (`prepare_data_v2.py`)

Extracts and filters paragraphs from the XML file.

```bash
python prepare_data_v2.py                    # Use default book
python prepare_data_v2.py --book anf02       # Specific book
python prepare_data_v2.py data/custom.xml    # Custom path
python prepare_data_v2.py --list             # List available books
```

**Output:** `output/filtered_paragraphs_<book>.csv`

### Step 2: Generate Questions (`generate_questions_v2.py`)

Uses Claude LLM to generate realistic test questions for each paragraph.

```bash
python generate_questions_v2.py              # Use default book
python generate_questions_v2.py --book anf01 # Specific book
python generate_questions_v2.py --list       # List books with prepared data
```

**Output:** `output/test_questions_<book>.json`

**Note:** Requires `ANTHROPIC_API_KEY` to be set.

### Step 3: Evaluate Retrieval (`evaluate_retrieval_v2.py`)

Queries the server and scores retrieval performance.

```bash
python evaluate_retrieval_v2.py              # Use default book
python evaluate_retrieval_v2.py --book anf01 # Specific book
python evaluate_retrieval_v2.py --list       # List books with questions
```

**Output:** 
- `output/test_results_<book>_<timestamp>.json`
- `output/analytics_report_<book>_<timestamp>.txt`

**Note:** Requires the server to be running.

## Scoring System

| Condition | Score |
|-----------|-------|
| Gold paragraph in ranks **1-3** | **+3 points** |
| Gold paragraph in ranks **4-10** | **+2 points** |
| Gold paragraph beyond rank 10 | **+1 point** |
| Missing a gold paragraph | **-2 points** |

### Score Labels

- **0.9 - 1.0**: Excellent
- **0.7 - 0.9**: Good  
- **0.5 - 0.7**: Mixed Relevance
- **0.3 - 0.5**: Poor
- **0.0 - 0.3**: Very Poor

## Configuration

Edit `config_v2.py` to customize:

```python
# API Settings
API_BASE_URL = "http://localhost:8080"

# Data Filtering
MIN_PARAGRAPH_LENGTH = 100
MAX_PARAGRAPH_LENGTH = 5000
MAX_PARAGRAPHS = None  # Set to limit for testing (e.g., 50)

# Retrieval Testing
TOP_K = 15
USE_AGENTIC = True
FILTER_WORKS = ["anf01"]  # Works to filter in API calls

# Scoring
SCORE_RANK_1_3 = 3
SCORE_RANK_4_10 = 2
SCORE_RANK_BEYOND_10 = 1
PENALTY_MISSING = -2
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

Set your API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or create a `.env` file in this directory:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### "Could not reach API endpoint"

Make sure the server is running:
```bash
cd /Users/david/CS_senior_project/JETON_SERVER/server
python main.py
```

### "XML file not found"

Place your XML file in the `data/` directory:
```bash
cp /path/to/book.xml data/
python prepare_data_v2.py --list  # Verify it's detected
```

### "No paragraphs passed filtering"

Adjust filtering in `config_v2.py`:
- Reduce `MIN_PARAGRAPH_LENGTH`
- Increase `MAX_PARAGRAPH_LENGTH`
- Modify `EXCLUDE_KEYWORDS`

## Alternative: Evaluate from CSV

If you have pre-generated questions in CSV format:

```bash
python evaluate_from_csv_v2.py questions.csv
```

Expected CSV format:
- `query`: Question text
- `gold_paragraph_ids`: Expected paragraph ID(s)
- `paragraph_text`: Source paragraph (optional)
- `question_type`: Question type (optional)

---

**Version:** 2.0  
**Last Updated:** December 2025

