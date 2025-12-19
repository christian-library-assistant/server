# JETON Testing System Documentation

This directory contains comprehensive testing documentation and tools for the JETON theological search system.

## 📚 Documentation Files

### 1. [testing-prompt-rules.md](./testing-prompt-rules.md)
**Complete Testing Methodology Guide**

Comprehensive documentation covering:
- Three testing scenarios (Author, Work, Broad)
- Detailed evaluation criteria and scoring rubrics
- Test question design guidelines
- Validation workflows
- Reporting formats

**Use this when:** You need to understand the testing methodology, create new questions, or evaluate results.

### 2. [testing-quick-reference.md](./testing-quick-reference.md)
**Quick Reference Cheat Sheet**

At-a-glance reference for:
- Request formats for each scenario
- Scoring formulas
- Success criteria
- Sample commands
- Common author/work IDs

**Use this when:** You need quick answers or command examples during testing.

### 3. [testing-endpoint.md](./testing-endpoint.md)
**API Endpoint Documentation**

Technical documentation for:
- `/test` endpoint specifications
- Available return fields
- Filter parameters
- Request/response schemas

**Use this when:** You need API technical details or integration information.

## 🚀 Quick Start

### Running Your First Test

1. **Start the server:**
```bash
cd /Users/david/CS_senior_project/JETON_SERVER/server
source venv/bin/activate
python main.py
```

2. **Run pilot tests (10 questions):**
```bash
python scripts/run_tests.py --pilot
```

3. **Review results:**
Results are automatically saved with unique timestamped filenames:
- JSON: `test_results_pilot_YYYYMMDD_HHMMSS.json`
- CSV: `test_results_pilot_YYYYMMDD_HHMMSS.csv`

Summary statistics are printed to console.

### Running Full Test Suite

1. **Prepare your question bank:**
   - Use `tests/sample_questions.json` as a template
   - Expand to 100 questions (33 author + 33 work + 34 broad)

2. **Run all tests:**
```bash
# Auto-generates timestamped filenames
python scripts/run_tests.py --questions tests/sample_questions.json

# Or specify custom filenames
python scripts/run_tests.py --questions tests/sample_questions.json --output my_results.json
```

3. **Run specific scenario:**
```bash
# Author tests only (auto-generates: test_results_author_TIMESTAMP.json/csv)
python scripts/run_tests.py --questions tests/sample_questions.json --scenario author

# Work tests only (auto-generates: test_results_work_TIMESTAMP.json/csv)
python scripts/run_tests.py --questions tests/sample_questions.json --scenario work

# Broad tests only (auto-generates: test_results_broad_TIMESTAMP.json/csv)
python scripts/run_tests.py --questions tests/sample_questions.json --scenario broad
```

## 📊 Understanding Results

### Automated Metrics

The test runner automatically calculates:

- **Filter Accuracy** - % of results matching author/work filter (must be 100%)
- **Source Diversity** - Number of unique authors in results
- **Processing Time** - How long each query takes
- **Results Count** - Number of results returned

### 🤖 NEW: LLM-Based Automatic Scoring

**Now automatically evaluated using Claude Sonnet 3.5!**

- **Relevance Score** - LLM rates each result (0-4 scale) using documentation rubric
- **Answer Quality** - LLM rates AI answer (0-4 scale) using documentation rubric
- **Fully automated** - No manual review needed!
- **Based on your rubric** - Uses exact criteria from documentation
- **Enable/Disable** - Use `--no-llm` flag to disable and use manual scoring

**Old way (manual):**
```bash
python scripts/run_tests.py --pilot
# → Scores = 0.0% (manual review required, 30-60 min work)
```

**New way (automated):**
```bash
python scripts/run_tests.py --pilot
# → Real scores automatically! (45 seconds total)
```

See **`LLM_SCORING_GUIDE.md`** for complete documentation.

### Result Files

**JSON Output (auto-generated with timestamp):**
- Filename format: `test_results_{scenario}_{YYYYMMDD_HHMMSS}.json`
- Complete raw responses
- All calculated metrics
- Timestamp and metadata
- Structured for further analysis

**CSV Output (auto-generated with timestamp):**
- Filename format: `test_results_{scenario}_{YYYYMMDD_HHMMSS}.csv`
- Spreadsheet-friendly format
- Easy manual review
- Can be imported to Google Sheets/Excel
- Add columns for manual scoring

**Note:** Each test run creates unique timestamped files, so previous results are never overwritten.

## 🎯 Three Testing Scenarios

### Scenario 1: Author-Filtered Testing

**Goal:** Validate author filtering accuracy

**Example Request:**
```json
{
  "query": "What does Augustine say about grace?",
  "authors": ["augustine"],
  "return_fields": ["record_id", "text", "authorid", "answer"]
}
```

**Critical Success Criterion:** 100% of results must have `authorid == "augustine"`

**Pass Criteria:**
- ✅ Filter accuracy = 100%
- ✅ Relevance score ≥ 70%

### Scenario 2: Work-Filtered Testing

**Goal:** Validate work filtering accuracy

**Example Request:**
```json
{
  "query": "What does the Confessions say about time?",
  "works": ["confessions"],
  "return_fields": ["record_id", "text", "workid", "answer"]
}
```

**Critical Success Criterion:** 100% of results must have `workid == "confessions"`

**Pass Criteria:**
- ✅ Filter accuracy = 100%
- ✅ Relevance score ≥ 70%

### Scenario 3: Broad/Unfiltered Testing

**Goal:** Validate semantic search quality

**Example Request:**
```json
{
  "query": "What is the Trinity?",
  "return_fields": ["record_id", "text", "authorid", "workid", "knn_distance", "answer"]
}
```

**Pass Criteria:**
- ✅ Overall score ≥ 65%
  - Relevance ≥ 60% (weight: 50%)
  - Answer quality ≥ 75% (weight: 30%)
  - Source diversity ≥ 50% (weight: 20%)

## 📝 Creating Test Questions

### Question Design Principles

**DO:**
- ✅ Ask realistic questions users would actually ask
- ✅ Use clear, specific theological terms
- ✅ Vary complexity (simple → complex)
- ✅ Include both common and uncommon topics
- ✅ Test edge cases

**DON'T:**
- ❌ Create artificially easy questions
- ❌ Use overly broad queries
- ❌ Ask questions with no relevant sources
- ❌ Duplicate questions across categories

### Question Templates

**Author-Filtered:**
```
"What does [AUTHOR] say about [TOPIC]?"
"According to [AUTHOR], what is [CONCEPT]?"
"How does [AUTHOR] explain [DOCTRINE]?"
```

**Work-Filtered:**
```
"What does [WORK] say about [TOPIC]?"
"According to [WORK], what is [CONCEPT]?"
"How is [TOPIC] described in [WORK]?"
```

**Broad/Unfiltered:**
```
"What is [CONCEPT]?"
"How is [TOPIC] understood in Christian theology?"
"What do Christian theologians say about [ISSUE]?"
```

### Sample Question Bank Structure

Aim for 100 total questions:
- **33 Author-filtered** (11 per major author: Augustine, Aquinas, Calvin)
- **33 Work-filtered** (8-9 per major work: Confessions, City of God, Summa, Institutes)
- **34 Broad** (varied topics covering fundamental concepts)

## 🔍 Manual Review Process

After running automated tests, manual review is required:

### Step 1: Review Results CSV

Find the auto-generated CSV file (e.g., `test_results_pilot_20251104_143022.csv`) and open it. Add these columns:
- `manual_relevance_0_4` - Your relevance rating (0-4)
- `manual_answer_quality_0_4` - Your answer quality rating (0-4)
- `notes` - Any observations

### Step 2: Rate Each Result

For each test question:
1. Read the query
2. Read the returned text passages
3. Rate relevance (0-4 scale):
   - 0 = Completely irrelevant
   - 1 = Tangentially related
   - 2 = Somewhat relevant
   - 3 = Relevant
   - 4 = Highly relevant

4. Read the AI answer
5. Rate answer quality (0-4 scale):
   - 0 = Incorrect/unhelpful
   - 1 = Minimal coverage
   - 2 = Adequate
   - 3 = Good (comprehensive, accurate)
   - 4 = Excellent (comprehensive, nuanced, well-cited)

### Step 3: Verify Record IDs (Sample Check)

For critical tests or suspicious results:
1. Copy the `record_id` (e.g., `ccel/a/augustine/confessions.xml:xi-p70`)
2. Visit: `https://www.ccel.org/ccel/augustine/confessions.xi.html#xi-p70`
3. Verify the paragraph actually contains relevant content

### Step 4: Update Scores

Re-calculate final scores with manual ratings:

```python
# For author/work tests
relevance_score = (sum_of_manual_ratings / (results_count × 4)) × 100
final_score = relevance_score if filter_accuracy == 100 else 0

# For broad tests
relevance_score = (sum_of_manual_ratings / 20) × 100  # max 5 results × 4
answer_quality = (manual_answer_rating / 4) × 100
overall = (relevance × 0.5) + (answer_quality × 0.3) + (diversity × 0.2)
```

## 📈 Analyzing Results

### Key Metrics to Track

**Overall Performance:**
- Total pass rate (target: ≥85%)
- Critical failures (target: 0)
- Average processing time (target: <5s)

**By Scenario:**
- Author filter accuracy (target: 100%)
- Work filter accuracy (target: 100%)
- Broad search relevance (target: ≥65%)

**Common Issues:**
- Wrong author/work in filtered results → Critical bug
- Low relevance across multiple queries → Embedding quality issue
- Missing obvious sources → Indexing problem
- High KNN distances → Query embedding issue

### Interpreting Pass Rates

| Pass Rate | Status | Action |
|-----------|--------|--------|
| **≥90%** | Excellent | Monitor and maintain |
| **75-89%** | Good | Identify and fix specific issues |
| **60-74%** | Concerning | Review methodology, investigate patterns |
| **<60%** | Poor | Major issues - deep investigation needed |

### Common Failure Patterns

**Pattern 1: All author tests fail**
- Issue: Author filter not being applied
- Check: Filter parameter passing in API

**Pattern 2: Broad tests return irrelevant results**
- Issue: Embedding quality or semantic search
- Check: Embedding model, query preprocessing

**Pattern 3: High processing times**
- Issue: Performance bottleneck
- Check: Database performance, agent iterations

**Pattern 4: Missing well-known sources**
- Issue: Indexing incomplete
- Check: Database content, embeddings coverage

## 🛠️ Troubleshooting

### Server Issues

**Problem:** Connection refused
```bash
# Solution: Start the server
cd /Users/david/CS_senior_project/JETON_SERVER/server
source venv/bin/activate
python main.py
```

**Problem:** 503 Service Unavailable
- Check `.env` file has required API keys
- Verify Anthropic API key is valid

### Testing Script Issues

**Problem:** ModuleNotFoundError
```bash
# Solution: Install dependencies
pip install requests
```

**Problem:** JSON decode error
- Verify `sample_questions.json` is valid JSON
- Use JSON validator: https://jsonlint.com/

### Result Validation Issues

**Problem:** All tests show 0% relevance
- This is expected - manual scoring required
- Follow "Manual Review Process" above

**Problem:** Filter accuracy is not 100% but should be
- This is a critical bug
- Check the raw response JSON
- Verify filter parameters in request

## 📋 Testing Checklist

### Pre-Testing
- [ ] Server is running (`python main.py`)
- [ ] API is accessible (`curl http://localhost:8000/health`)
- [ ] Question bank is prepared (JSON file)
- [ ] Dependencies installed (`requests`)

### During Testing
- [ ] Run pilot tests first (10 questions)
- [ ] Verify pilot results look reasonable
- [ ] Run full test suite
- [ ] Monitor for errors or crashes
- [ ] Save results to JSON and CSV

### Post-Testing
- [ ] Review automated metrics (filter accuracy, diversity)
- [ ] Perform manual relevance rating
- [ ] Perform manual answer quality rating
- [ ] Calculate final scores
- [ ] Generate summary report
- [ ] Document findings and recommendations
- [ ] Share with team

## 🎓 Best Practices

### 1. Start Small
Run pilot tests (10 questions) before full suite to:
- Validate your setup
- Check question quality
- Estimate time requirements

### 2. Iterate on Questions
After pilot tests:
- Refine unclear questions
- Remove duplicates
- Add missing coverage areas

### 3. Track Over Time
Run tests regularly to:
- Monitor performance trends
- Detect regressions
- Validate improvements

### 4. Document Everything
For each test run, record:
- Date and version
- Any system changes
- Pass/fail rates
- Notable findings

### 5. Use Version Control
Track changes to:
- Question bank
- Test results
- Findings documents

## 📚 Additional Resources

### Finding Author/Work IDs

```bash
# List all authors
curl http://localhost:8000/authors

# Search for specific author
curl "http://localhost:8000/authors?query=augustine"

# List all works
curl http://localhost:8000/works

# Search for specific work
curl "http://localhost:8000/works?query=confessions"
```

### Common IDs

**Authors:**
- `augustine` - Augustine of Hippo
- `aquinas` - Thomas Aquinas
- `calvin` - John Calvin
- `luther` - Martin Luther
- `anselm` - Anselm of Canterbury

**Works:**
- `confessions` - Augustine's Confessions
- `city` - City of God
- `summa` - Summa Theologica
- `institutes` - Institutes of the Christian Religion

### CCEL Record ID Format

Format: `ccel/{author}/{work}/{version}.xml:{section}-p{paragraph}`

Examples:
- `ccel/a/augustine/confessions.xml:xi-p70`
- `ccel/a/aquinas/summa.xml:FP_Q1_A1-p1`

Verify online:
`https://www.ccel.org/ccel/{author}/{work}.{section}.html#{section}-p{paragraph}`

## 🤝 Getting Help

### Documentation
1. Read [testing-prompt-rules.md](./testing-prompt-rules.md) for methodology
2. Check [testing-quick-reference.md](./testing-quick-reference.md) for quick answers
3. Review [testing-endpoint.md](./testing-endpoint.md) for API details

### Common Questions

**Q: How long does testing take?**
A: ~5-10 minutes for pilot (10 questions), 45-60 minutes for full suite (100 questions)

**Q: Can I run tests in parallel?**
A: Not recommended - could overwhelm the API. Run sequentially with small delays.

**Q: What if I get different results on re-run?**
A: Some variation is normal due to LLM temperature. Track trends over multiple runs.

**Q: How often should I run tests?**
A: After major changes, weekly for monitoring, or before releases.

## 📊 Sample Report Template

```
JETON Testing Report - [Date]
=============================

Test Configuration:
- Questions: 100 (33 author + 33 work + 34 broad)
- Server Version: [version]
- Model: claude-3-5-sonnet-20241022

Overall Results:
- Pass Rate: 87/100 (87%)
- Critical Failures: 1
- Avg Processing Time: 3.2s

By Scenario:
1. Author Tests (33):
   - Pass: 32/33 (97%)
   - Filter Accuracy: 99.7%
   - Avg Relevance: 76%
   - Critical Failures: 1 (wrong author in question author_023)

2. Work Tests (33):
   - Pass: 31/33 (94%)
   - Filter Accuracy: 100%
   - Avg Relevance: 72%
   - Critical Failures: 0

3. Broad Tests (34):
   - Pass: 24/34 (71%)
   - Avg Overall Score: 68%
   - Avg Relevance: 65%
   - Avg Answer Quality: 74%
   - Avg Source Diversity: 55%

Key Findings:
1. One critical failure in author filtering (needs investigation)
2. Broad search relevance meets target (≥65%)
3. Processing time within acceptable range (<5s)
4. Source diversity good (multiple authors represented)

Recommendations:
1. Fix author filter bug in question author_023
2. Improve relevance for edge case theological queries
3. Continue monitoring processing time as database grows
4. Consider expanding question bank for better coverage

Next Steps:
1. Debug and fix critical failure
2. Retest affected questions
3. Update question bank based on findings
```

---

**Last Updated:** November 4, 2025  
**Version:** 1.0  
**Maintained by:** JETON Testing Team

