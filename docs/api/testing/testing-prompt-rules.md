# Testing Prompt Rules & Methodology

## Overview

This document outlines the standardized testing methodology for evaluating the JETON theological search system across three distinct scenarios. Each scenario tests different aspects of the system's accuracy, relevance, and filtering capabilities.

---

## Three Testing Scenarios

### 1. Author-Filtered Testing
**Goal:** Validate that the system correctly retrieves content ONLY from specified authors and that the content is relevant.

### 2. Work-Filtered Testing
**Goal:** Validate that the system correctly retrieves content ONLY from specified works/books and that the content is relevant.

### 3. Broad/Unfiltered Testing
**Goal:** Validate pure semantic search performance and relevance ranking without any filters (mirrors actual user experience).

---

## 1. Author-Filtered Testing

### Purpose
Test whether the system correctly:
- Filters results to ONLY the specified author(s)
- Returns relevant content from that author
- Properly maps author names to author IDs

### Methodology

#### Setup
```json
{
  "query": "<theological_question>",
  "agentic": true,
  "top_k": 5,
  "return_fields": ["record_id", "text", "authorid", "knn_distance", "answer"],
  "authors": ["<author_id>"]
}
```

#### Test Questions Format
Questions should explicitly reference the author to make validation clear:

**Template:**
```
"What does [AUTHOR_NAME] say about [THEOLOGICAL_TOPIC]?"
"According to [AUTHOR_NAME], what is [CONCEPT]?"
"How does [AUTHOR_NAME] explain [DOCTRINE]?"
```

#### Sample Test Questions

1. **Augustine Questions:**
   - "What does Augustine say about original sin?"
   - "According to Augustine, what is grace?"
   - "How does Augustine explain the nature of time?"
   - "What is Augustine's view on free will?"
   - "How does Augustine describe the Trinity?"

2. **Aquinas Questions:**
   - "What does Aquinas say about natural law?"
   - "According to Aquinas, what are the five ways to prove God's existence?"
   - "How does Aquinas explain the relationship between faith and reason?"
   - "What is Aquinas's view on virtue ethics?"

3. **Calvin Questions:**
   - "What does Calvin say about predestination?"
   - "According to Calvin, what is total depravity?"
   - "How does Calvin explain the sovereignty of God?"
   - "What is Calvin's view on the sacraments?"

### Evaluation Criteria

#### ✅ Success Indicators
1. **Author Match (Critical):** ALL returned results have `authorid` matching the filter
2. **Relevance:** Returned text passages directly address the query topic
3. **Answer Quality:** AI answer accurately reflects the author's view
4. **Source Count:** System returns meaningful sources (3-5 sources minimum)
5. **Record ID Validity:** All `record_id` values are properly formatted (e.g., `ccel/a/augustine/confessions.xml:...`)

#### ❌ Failure Indicators
1. **Wrong Author:** ANY result has `authorid` ≠ specified author → **CRITICAL FAILURE**
2. **No Results:** Query returns 0 results when author has relevant content
3. **Irrelevant Content:** Text passages don't address the query topic
4. **Incorrect Attribution:** AI answer attributes views to wrong author
5. **Invalid Record IDs:** Malformed or missing `record_id` values

### Scoring Rubric

**Author Filter Accuracy:** `(Correct Author Results / Total Results) × 100%`
- **Target:** 100% (any deviation is a critical failure)

**Content Relevance:** Manually rate each result 0-2
- 0 = Irrelevant
- 1 = Somewhat relevant
- 2 = Highly relevant
- **Score:** `(Sum of Ratings / (Total Results × 2)) × 100%`
- **Target:** ≥70%

**Overall Author Test Score:**
```
IF Author Filter Accuracy = 100%:
    Score = Content Relevance Score
ELSE:
    Score = FAIL (0%)
```

---

## 2. Work-Filtered Testing

### Purpose
Test whether the system correctly:
- Filters results to ONLY the specified work(s)
- Returns relevant content from that work
- Properly maps work titles to work IDs

### Methodology

#### Setup
```json
{
  "query": "<theological_question>",
  "agentic": true,
  "top_k": 5,
  "return_fields": ["record_id", "text", "workid", "authorid", "knn_distance", "answer"],
  "works": ["<work_id>"]
}
```

#### Test Questions Format
Questions should explicitly reference the work to make validation clear:

**Template:**
```
"What does [WORK_TITLE] say about [TOPIC]?"
"According to [WORK_TITLE], what is [CONCEPT]?"
"How is [TOPIC] described in [WORK_TITLE]?"
"In [WORK_TITLE], how is [DOCTRINE] explained?"
```

#### Sample Test Questions

1. **Confessions (Augustine):**
   - "What does the Confessions say about Augustine's conversion?"
   - "How is time described in the Confessions?"
   - "What does the Confessions say about memory?"
   - "According to the Confessions, what is the nature of evil?"

2. **City of God (Augustine):**
   - "What does City of God say about the two cities?"
   - "How is the fall of Rome explained in City of God?"
   - "What does City of God say about divine providence?"

3. **Summa Theologica (Aquinas):**
   - "What does the Summa Theologica say about the essence of God?"
   - "How are the sacraments explained in the Summa Theologica?"
   - "What does the Summa say about angels?"

4. **Institutes of the Christian Religion (Calvin):**
   - "What do the Institutes say about election?"
   - "How is sanctification described in the Institutes?"
   - "What do the Institutes say about church governance?"

### Evaluation Criteria

#### ✅ Success Indicators
1. **Work Match (Critical):** ALL returned results have `workid` matching the filter
2. **Relevance:** Returned text passages directly address the query topic
3. **Answer Quality:** AI answer accurately reflects content from the specified work
4. **Source Count:** System returns meaningful sources (3-5 sources minimum)
5. **Record ID Contains Work:** `record_id` contains the correct work identifier

#### ❌ Failure Indicators
1. **Wrong Work:** ANY result has `workid` ≠ specified work → **CRITICAL FAILURE**
2. **No Results:** Query returns 0 results when work has relevant content
3. **Irrelevant Content:** Text passages don't address the query topic
4. **Cross-Work Attribution:** AI answer includes content from other works
5. **Invalid Record IDs:** Record IDs don't match the specified work

### Scoring Rubric

**Work Filter Accuracy:** `(Correct Work Results / Total Results) × 100%`
- **Target:** 100% (any deviation is a critical failure)

**Content Relevance:** Manually rate each result 0-2
- 0 = Irrelevant
- 1 = Somewhat relevant
- 2 = Highly relevant
- **Score:** `(Sum of Ratings / (Total Results × 2)) × 100%`
- **Target:** ≥70%

**Overall Work Test Score:**
```
IF Work Filter Accuracy = 100%:
    Score = Content Relevance Score
ELSE:
    Score = FAIL (0%)
```

---

## 3. Broad/Unfiltered Testing

### Purpose
Test the system's pure performance:
- Semantic search accuracy without filters
- Relevance ranking quality
- Ability to find best sources across entire database
- Real-world user experience simulation

### Methodology

#### Setup
```json
{
  "query": "<theological_question>",
  "agentic": true,
  "top_k": 5,
  "return_fields": ["record_id", "text", "authorid", "workid", "knn_distance", "answer"],
  "authors": [],
  "works": []
}
```

#### Test Questions Format
Questions should be natural, as users would actually ask them:

**Template:**
```
"What is [THEOLOGICAL_CONCEPT]?"
"How is [TOPIC] understood in Christian theology?"
"What do Christian theologians say about [ISSUE]?"
"Explain [DOCTRINE] from a Christian perspective"
```

#### Sample Test Questions

1. **Foundational Concepts:**
   - "What is the Trinity?"
   - "What is salvation?"
   - "What is grace?"
   - "What is original sin?"
   - "What is justification?"

2. **Theological Topics:**
   - "What is the relationship between faith and works?"
   - "How is the nature of God described in Christian theology?"
   - "What is the purpose of the sacraments?"
   - "What is the role of the Holy Spirit?"

3. **Doctrinal Questions:**
   - "What is predestination?"
   - "How is the incarnation explained?"
   - "What is atonement?"
   - "What is sanctification?"

4. **Practical Theology:**
   - "What is the purpose of prayer?"
   - "How should Christians understand suffering?"
   - "What is the nature of the church?"
   - "What is Christian ethics based on?"

5. **Comparative/Complex:**
   - "What are different views on free will?"
   - "How do different theologians explain the problem of evil?"
   - "What are various perspectives on divine providence?"

### Evaluation Criteria

#### ✅ Success Indicators
1. **Semantic Relevance:** Top results directly address the query topic
2. **Diversity:** Results come from multiple authoritative sources
3. **Answer Quality:** AI answer synthesizes information from multiple sources
4. **Source Quality:** Results include well-known, authoritative texts
5. **KNN Distance:** Lower distances for top results (better semantic match)
6. **Comprehensive Coverage:** Answer addresses different aspects/perspectives

#### ❌ Failure Indicators
1. **Irrelevant Results:** Top results don't address the query
2. **Poor Ranking:** Highly relevant content ranked low (position 4-5)
3. **Single Source Bias:** All results from same author/work
4. **Missing Key Sources:** Well-known relevant texts not retrieved
5. **High KNN Distance:** Top results have poor semantic match scores
6. **Incomplete Answer:** AI answer misses key theological perspectives

### Scoring Rubric

#### Relevance Rating (Per Result)
Manually rate each of the top 5 results:
- **0 = Completely Irrelevant:** Text has nothing to do with query
- **1 = Tangentially Related:** Mentions topic but doesn't address query
- **2 = Somewhat Relevant:** Addresses part of query but not comprehensive
- **3 = Relevant:** Clearly addresses query
- **4 = Highly Relevant:** Directly answers query with good detail

**Relevance Score:** `(Sum of Ratings / 20) × 100%`
- **Target:** ≥60% (12/20 points)

#### Answer Quality Rating
Rate the AI-generated answer:
- **0 = Incorrect/Unhelpful:** Factually wrong or doesn't address query
- **1 = Minimal:** Very basic, missing key information
- **2 = Adequate:** Covers basics but lacks depth
- **3 = Good:** Comprehensive, accurate, well-cited
- **4 = Excellent:** Comprehensive, nuanced, multiple perspectives, well-cited

**Answer Quality Score:** `(Rating / 4) × 100%`
- **Target:** ≥75%

#### Source Diversity Rating
- **All same author:** 0 points
- **2-3 different authors:** 1 point
- **4+ different authors:** 2 points

**Source Diversity Score:** `(Points / 2) × 100%`
- **Target:** ≥50%

#### Overall Broad Test Score
```
Overall Score = (Relevance Score × 0.5) + (Answer Quality × 0.3) + (Source Diversity × 0.2)
```
- **Target:** ≥65%

---

## Testing Pipeline Workflow

### Phase 1: Preparation
1. **Create Question Bank:** 100 questions (33 per category, 1 control)
2. **Map Subject IDs:** For each question, identify expected subject tags
3. **Document Expected Sources:** Note which authors/works should appear
4. **Set Up Tracking Sheet:** Spreadsheet with columns for all metrics

### Phase 2: Execution
1. **Run Tests:** Send each question via `/test` endpoint
2. **Record Raw Results:** Save complete JSON responses
3. **Extract Record IDs:** Pull all `record_id` values for validation
4. **Note Processing Time:** Track performance metrics

### Phase 3: Validation

#### Automated Checks
```python
# Check 1: Author filter compliance
if authors_filter:
    for result in results:
        assert result['authorid'] in authors_filter

# Check 2: Work filter compliance  
if works_filter:
    for result in results:
        assert result['workid'] in works_filter

# Check 3: Record ID format
for result in results:
    assert re.match(r'ccel/\w+/\w+/\w+\.xml:\w+-\w+\d+', result['record_id'])
```

#### Manual Review
1. **Read Retrieved Paragraphs:** Review `text` field for each result
2. **Rate Relevance:** Apply rubric scores
3. **Validate Answer:** Compare AI answer against source texts
4. **Check Citations:** Verify `record_id` values are valid CCEL references

#### Subject ID Comparison (Advanced)
1. **Extract Subject IDs from Results:** Parse `record_id` for subject tags
2. **Compare to Expected:** Match against known subject taxonomy
3. **Calculate Precision:** `Relevant Subject Matches / Total Results`

### Phase 4: Analysis

#### Per-Question Metrics
- Author/Work filter accuracy
- Relevance score
- Answer quality score
- KNN distance average
- Processing time

#### Aggregate Metrics
- **Overall Accuracy:** % of tests passing target scores
- **Category Performance:** Author vs Work vs Broad comparison
- **Failure Patterns:** Common failure modes
- **Performance Stats:** Average processing time, result count

#### Reporting Format
```
Test Summary Report
==================

Total Questions: 100
- Author-Filtered: 33 questions
- Work-Filtered: 33 questions  
- Broad/Unfiltered: 34 questions

Overall Results:
- Pass Rate: 85% (85/100)
- Average Relevance: 72%
- Average Answer Quality: 78%
- Critical Failures: 2 (wrong author/work)

Category Breakdown:
1. Author Tests: 31/33 pass (94%)
   - Average Relevance: 75%
   - Filter Accuracy: 99.4%
   
2. Work Tests: 29/33 pass (88%)
   - Average Relevance: 71%
   - Filter Accuracy: 98.8%
   
3. Broad Tests: 25/34 pass (74%)
   - Average Relevance: 69%
   - Average Answer Quality: 77%
   - Source Diversity: 68%
```

---

## Best Practices for Question Design

### DO:
✅ Ask realistic questions users would actually ask
✅ Use clear, specific theological terms
✅ Vary complexity (simple to complex)
✅ Include both common and uncommon topics
✅ Test edge cases (ambiguous terms, multiple meanings)

### DON'T:
❌ Create artificially easy questions
❌ Use overly broad queries ("Tell me about God")
❌ Ask questions with no relevant sources in database
❌ Duplicate questions across categories
❌ Use modern slang or non-theological language

---

## Sample Question Bank Structure

```
Author-Filtered Questions (33 total)
├── Augustine (11 questions)
│   ├── Confessions-specific (4)
│   ├── City of God-specific (4)
│   └── General Augustine (3)
├── Aquinas (11 questions)
│   ├── Summa-specific (6)
│   └── General Aquinas (5)
└── Calvin (11 questions)
    ├── Institutes-specific (6)
    └── General Calvin (5)

Work-Filtered Questions (33 total)
├── Confessions (8)
├── City of God (8)
├── Summa Theologica (8)
├── Institutes (8)
└── Other classic works (1)

Broad Questions (34 total)
├── Foundational Concepts (8)
├── Theological Topics (8)
├── Doctrinal Questions (8)
├── Practical Theology (5)
└── Comparative/Complex (5)
```

---

## Implementation Checklist

- [ ] Create 100-question test bank with expected results
- [ ] Set up automated test runner script
- [ ] Create results tracking spreadsheet
- [ ] Implement automated filter validation
- [ ] Set up manual review process
- [ ] Create reporting template
- [ ] Run pilot test with 10 questions
- [ ] Refine methodology based on pilot
- [ ] Execute full 100-question test
- [ ] Analyze results and document findings
- [ ] Share results with team
- [ ] Iterate on system based on findings

---

## Tools & Resources

### Required Endpoints
- `POST /test` - Main testing endpoint
- `GET /test/fields` - Available fields reference
- `GET /authors` - Author ID lookup
- `GET /works` - Work ID lookup

### Suggested Tools
- Python script for automated testing
- Spreadsheet for manual review
- CCEL website for record ID verification
- Claude API for answer quality assessment (optional)

### Record ID Verification
Format: `ccel/{author}/{work}/{version}.xml:{section}-p{paragraph}`

Verify at: `https://www.ccel.org/ccel/{author}/{work}.{section}`

Example: `ccel/a/augustine/confessions.xml:xi-p70`
→ https://www.ccel.org/ccel/augustine/confessions.xi.html#xi-p70

---

## Expected Outcomes

### Success Criteria
1. **Filter Accuracy:** 100% for author/work filtered tests
2. **Broad Relevance:** ≥65% overall score
3. **Answer Quality:** ≥75% across all categories
4. **No Critical Failures:** Zero instances of wrong author/work in filtered tests
5. **Performance:** <5s average processing time

### Acceptable Issues
- Occasional low relevance in broad searches (acceptable if <30% of tests)
- Missing some secondary sources
- Minor citation formatting issues

### Critical Issues (Must Fix)
- ANY filter compliance failure
- Consistently irrelevant results for common queries
- System errors or crashes
- Invalid record IDs
- Fabricated or incorrect theological information

---

**Document Version:** 1.0  
**Last Updated:** November 4, 2025  
**Author:** JETON Testing Team


