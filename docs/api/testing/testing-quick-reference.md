# Testing Quick Reference Guide

## 🤖 NEW: Automatic LLM Scoring

**Tests now automatically scored using Claude Sonnet 3.5!**

```bash
python scripts/run_tests.py --pilot
# → Relevance and Answer Quality scored automatically!
# → No manual review needed!

# To disable automatic scoring:
python scripts/run_tests.py --pilot --no-llm
```

**Requirements:** Set `ANTHROPIC_API_KEY` in `.env` file

See **`LLM_SCORING_GUIDE.md`** for complete details.

---

## Three Testing Scenarios - At a Glance

### 1️⃣ Author-Filtered Testing
**Purpose:** Validate author filtering works correctly

**Request Format:**
```json
{
  "query": "What does Augustine say about grace?",
  "agentic": true,
  "authors": ["augustine"],
  "return_fields": ["record_id", "text", "authorid", "answer"]
}
```

**Success Criteria:**
- ✅ ALL results have `authorid == "augustine"`
- ✅ Content is relevant to query
- ✅ Answer reflects Augustine's views
- ⚠️ ANY wrong author = **CRITICAL FAILURE**

**Target Score:** 100% filter accuracy, ≥70% relevance

---

### 2️⃣ Work-Filtered Testing
**Purpose:** Validate work filtering works correctly

**Request Format:**
```json
{
  "query": "What does the Confessions say about time?",
  "agentic": true,
  "works": ["confessions"],
  "return_fields": ["record_id", "text", "workid", "answer"]
}
```

**Success Criteria:**
- ✅ ALL results have `workid == "confessions"`
- ✅ Content is relevant to query
- ✅ Answer only uses Confessions content
- ⚠️ ANY wrong work = **CRITICAL FAILURE**

**Target Score:** 100% filter accuracy, ≥70% relevance

---

### 3️⃣ Broad/Unfiltered Testing
**Purpose:** Test pure semantic search performance

**Request Format:**
```json
{
  "query": "What is the Trinity?",
  "agentic": true,
  "return_fields": ["record_id", "text", "authorid", "workid", "knn_distance", "answer"]
}
```

**Success Criteria:**
- ✅ Results are semantically relevant
- ✅ Multiple different sources
- ✅ Comprehensive AI answer
- ✅ Good ranking (best results first)

**Target Score:** ≥65% overall (relevance 60%, answer quality 75%, diversity 50%)

---

## Relevance Rating Scale

| Score | Meaning | Example |
|-------|---------|---------|
| **0** | Completely Irrelevant | Query: "grace" → Result: "geography of Palestine" |
| **1** | Tangentially Related | Query: "grace" → Result: "mentions grace once in passing" |
| **2** | Somewhat Relevant | Query: "grace" → Result: "discusses salvation, mentions grace" |
| **3** | Relevant | Query: "grace" → Result: "paragraph about grace and works" |
| **4** | Highly Relevant | Query: "grace" → Result: "detailed explanation of grace" |

---

## Quick Test Commands

### Check Author Filter
```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does Augustine say about sin?",
    "authors": ["augustine"],
    "return_fields": ["authorid", "text", "answer"]
  }'
```

**Verify:** All `authorid` values are `"augustine"`

### Check Work Filter
```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does this book say about prayer?",
    "works": ["confessions"],
    "return_fields": ["workid", "text", "answer"]
  }'
```

**Verify:** All `workid` values are `"confessions"`

### Check Broad Search
```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is salvation?",
    "agentic": true,
    "return_fields": ["record_id", "text", "authorid", "workid", "answer"]
  }'
```

**Verify:** Results are diverse and relevant

---

## Test Script Commands

### Running the Test Script

**Note:** All test runs now auto-generate unique timestamped filenames to prevent overwriting previous results.

**Filename format:** `test_results_{scenario}_{YYYYMMDD_HHMMSS}.json` and `.csv`

```bash
# Setup
cd /Users/david/CS_senior_project/JETON_SERVER/server
source venv/bin/activate
python main.py  # Start server in one terminal

# In another terminal:
# Pilot test (10 questions) - auto-generates: test_results_pilot_20251104_143022.json/csv
python scripts/run_tests.py --pilot

# Full suite - auto-generates: test_results_all_20251104_143022.json/csv  
python scripts/run_tests.py --questions tests/sample_questions.json

# Specific scenarios
python scripts/run_tests.py --questions tests/sample_questions.json --scenario author  # test_results_author_...
python scripts/run_tests.py --questions tests/sample_questions.json --scenario work    # test_results_work_...
python scripts/run_tests.py --questions tests/sample_questions.json --scenario broad   # test_results_broad_...

# Custom filenames (optional)
python scripts/run_tests.py --pilot --output my_custom_results.json
python scripts/run_tests.py --pilot --output my_test.json --csv my_test.csv
```

---

## Common Author & Work IDs

### Authors
- `augustine` - Augustine of Hippo
- `aquinas` - Thomas Aquinas
- `calvin` - John Calvin
- `luther` - Martin Luther
- `anselm` - Anselm of Canterbury

### Works
- `confessions` - Augustine's Confessions
- `city` - City of God
- `summa` - Summa Theologica
- `institutes` - Institutes of the Christian Religion

**Find more:** `GET /authors` or `GET /works`

---

## Sample Questions by Category

### Author-Filtered (33 questions)
```
1. What does Augustine say about original sin?
2. According to Aquinas, what is natural law?
3. How does Calvin explain predestination?
4. What is Luther's view on justification by faith?
5. How does Anselm prove God's existence?
...
```

### Work-Filtered (33 questions)
```
1. What does the Confessions say about Augustine's conversion?
2. How is the Trinity explained in the Summa Theologica?
3. What do the Institutes say about the sacraments?
4. How is the fall of Rome explained in City of God?
5. What does the Proslogion say about God's nature?
...
```

### Broad (34 questions)
```
1. What is the Trinity?
2. What is grace?
3. What is justification?
4. How is atonement understood?
5. What is the relationship between faith and works?
...
```

---

## Red Flags 🚩

### Critical Issues (Must Fix Immediately)
- ❌ Wrong `authorid` in author-filtered test
- ❌ Wrong `workid` in work-filtered test
- ❌ Completely irrelevant results for common queries
- ❌ Invalid or malformed `record_id` values
- ❌ System errors or crashes

### Warning Signs (Investigate)
- ⚠️ Low relevance scores (<50%) on multiple tests
- ⚠️ All results from same source in broad tests
- ⚠️ Missing well-known relevant sources
- ⚠️ Very high KNN distances (>0.8)
- ⚠️ Processing time >10s

### Acceptable Issues
- ✓ Occasional low relevance in edge case queries
- ✓ Missing some secondary sources
- ✓ Minor formatting issues in citations

---

## Testing Workflow (5 Steps)

1. **Prepare** - Create question bank (100 questions)
2. **Execute** - Run tests via `/test` endpoint
3. **Validate** - Check filters, rate relevance
4. **Analyze** - Calculate scores, identify patterns
5. **Report** - Document findings and recommendations

---

## Scoring Formulas

### Author/Work Tests
```
IF filter_accuracy = 100%:
    score = relevance_score
ELSE:
    score = FAIL (0%)

relevance_score = (sum of ratings / (results × 2)) × 100%
```

### Broad Tests
```
overall_score = (relevance × 0.5) + (answer_quality × 0.3) + (diversity × 0.2)

relevance = (sum of ratings / 20) × 100%
answer_quality = (rating / 4) × 100%
diversity = (points / 2) × 100%
```

---

## Expected Results

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| **Filter Accuracy** | 100% | 100% | <100% |
| **Relevance (Filtered)** | ≥70% | ≥60% | <60% |
| **Relevance (Broad)** | ≥65% | ≥55% | <55% |
| **Answer Quality** | ≥75% | ≥65% | <65% |
| **Source Diversity** | ≥50% | ≥30% | <30% |
| **Processing Time** | <3s | <5s | >5s |

---

## Verification Examples

### Example 1: Valid Author Filter ✅
```json
{
  "query": "What does Augustine say about grace?",
  "authors": ["augustine"],
  "results": [
    {"authorid": "augustine", "text": "Grace is...", ...},
    {"authorid": "augustine", "text": "In my work...", ...},
    {"authorid": "augustine", "text": "The nature of grace...", ...}
  ]
}
```
**Status:** PASS - All results match filter

### Example 2: Invalid Author Filter ❌
```json
{
  "query": "What does Augustine say about grace?",
  "authors": ["augustine"],
  "results": [
    {"authorid": "augustine", "text": "Grace is...", ...},
    {"authorid": "aquinas", "text": "Grace differs...", ...},  ← WRONG!
    {"authorid": "augustine", "text": "In my work...", ...}
  ]
}
```
**Status:** CRITICAL FAILURE - Result 2 has wrong author

### Example 3: Valid Broad Search ✅
```json
{
  "query": "What is the Trinity?",
  "results": [
    {"authorid": "augustine", "workid": "trinity", "text": "The Trinity is...", "knn_distance": 0.32},
    {"authorid": "aquinas", "workid": "summa", "text": "Three persons...", "knn_distance": 0.35},
    {"authorid": "athanasius", "workid": "nicene", "text": "One God in three...", "knn_distance": 0.38}
  ]
}
```
**Status:** PASS - Diverse sources, low KNN, relevant

---

## Record ID Format

**Pattern:** `ccel/{author}/{work}/{version}.xml:{section}-p{paragraph}`

**Examples:**
- `ccel/a/augustine/confessions.xml:xi-p70`
- `ccel/a/aquinas/summa.xml:FP_Q1_A1-p1`
- `ccel/c/calvin/institutes.xml:book1_ch1-p5`

**Validation:**
```bash
# Visit: https://www.ccel.org/ccel/{author}/{work}.{section}.html#{section}-p{paragraph}
# Example: 
https://www.ccel.org/ccel/augustine/confessions.xi.html#xi-p70
```

---

**Quick Tip:** Start with 10 pilot questions (3 author, 3 work, 4 broad) to validate your setup before running the full 100-question suite.

---

**Last Updated:** November 4, 2025

