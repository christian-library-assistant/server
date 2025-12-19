# JETON Testing Workflow - Visual Guide

## Testing Pipeline Overview

```mermaid
graph TD
    A[Start Testing] --> B{Choose Test Type}
    B -->|Quick Validation| C[Pilot Tests - 10 Questions]
    B -->|Full Suite| D[100 Questions Test]
    
    C --> E[Run Test Script]
    D --> E
    
    E --> F[Automated Validation]
    F --> G[Filter Accuracy Check]
    F --> H[Source Diversity Check]
    F --> I[Processing Time Check]
    
    G --> J{All Filters Pass?}
    J -->|No| K[CRITICAL FAILURE]
    J -->|Yes| L[Manual Review Required]
    
    H --> L
    I --> L
    
    L --> M[Rate Relevance 0-4]
    L --> N[Rate Answer Quality 0-4]
    
    M --> O[Calculate Scores]
    N --> O
    
    O --> P[Generate Report]
    P --> Q[Analyze Results]
    Q --> R{Pass Rate ≥ Target?}
    
    R -->|Yes| S[Success! Monitor & Maintain]
    R -->|No| T[Investigate Failures]
    
    T --> U[Fix Issues]
    U --> E
    
    K --> V[Debug Filter Logic]
    V --> E
```

## Three Testing Scenarios

```mermaid
graph LR
    A[JETON Testing] --> B[Author-Filtered]
    A --> C[Work-Filtered]
    A --> D[Broad/Unfiltered]
    
    B --> B1[Filter by Author ID]
    B1 --> B2[Validate ALL results<br/>match author]
    B2 --> B3[100% Accuracy<br/>Required]
    
    C --> C1[Filter by Work ID]
    C1 --> C2[Validate ALL results<br/>match work]
    C2 --> C3[100% Accuracy<br/>Required]
    
    D --> D1[No Filters]
    D1 --> D2[Evaluate Semantic<br/>Relevance]
    D2 --> D3[65% Overall<br/>Score Target]
    
    style B3 fill:#f99,stroke:#333,stroke-width:2px
    style C3 fill:#f99,stroke:#333,stroke-width:2px
    style D3 fill:#9f9,stroke:#333,stroke-width:2px
```

## Scoring Decision Tree

```mermaid
graph TD
    A[Test Result] --> B{Scenario Type?}
    
    B -->|Author/Work| C{Filter Accuracy = 100%?}
    C -->|No| D[FAIL - Score: 0%<br/>Critical Issue]
    C -->|Yes| E{Relevance ≥ 70%?}
    E -->|Yes| F[PASS]
    E -->|No| G[FAIL - Low Relevance]
    
    B -->|Broad| H[Calculate Components]
    H --> I[Relevance Score × 50%]
    H --> J[Answer Quality × 30%]
    H --> K[Source Diversity × 20%]
    
    I --> L[Sum Components]
    J --> L
    K --> L
    
    L --> M{Overall ≥ 65%?}
    M -->|Yes| N[PASS]
    M -->|No| O[FAIL]
    
    style D fill:#f99,stroke:#333,stroke-width:3px
    style F fill:#9f9,stroke:#333,stroke-width:2px
    style G fill:#fc9,stroke:#333,stroke-width:2px
    style N fill:#9f9,stroke:#333,stroke-width:2px
    style O fill:#fc9,stroke:#333,stroke-width:2px
```

## Question Design Process

```mermaid
graph LR
    A[Identify Topic] --> B{User Scenario?}
    
    B -->|Specific Author| C[Author-Filtered Question]
    C --> C1["What does [AUTHOR]<br/>say about [TOPIC]?"]
    C1 --> D[Add Expected Author ID]
    
    B -->|Specific Book| E[Work-Filtered Question]
    E --> E1["What does [WORK]<br/>say about [TOPIC]?"]
    E1 --> F[Add Expected Work ID]
    
    B -->|General Query| G[Broad Question]
    G --> G1["What is [CONCEPT]?"]
    G1 --> H[Add Expected Topics]
    
    D --> I[Add to Question Bank]
    F --> I
    H --> I
    
    I --> J{Have 100 Questions?}
    J -->|No| A
    J -->|Yes| K[Ready to Test]
```

## Test Execution Flow

```mermaid
sequenceDiagram
    participant U as User
    participant S as Test Script
    participant API as /test Endpoint
    participant DB as CCEL Database
    participant LLM as AI Agent
    
    U->>S: Run test script
    S->>S: Load questions
    
    loop For each question
        S->>API: POST request<br/>(query + filters)
        API->>DB: Search embeddings
        DB-->>API: Return top results
        API->>LLM: Generate answer
        LLM-->>API: AI response
        API-->>S: Results + Answer
        S->>S: Validate filters
        S->>S: Calculate metrics
    end
    
    S->>S: Generate report
    S-->>U: Display summary
    S->>S: Save JSON + CSV
```

## Manual Review Process

```mermaid
graph TD
    A[Open results.csv] --> B[Select Test Question]
    B --> C[Read Query]
    C --> D[Review Result 1-5]
    
    D --> E[Read Text Paragraph]
    E --> F{Addresses Query?}
    
    F -->|Not at all| G1[Rate: 0]
    F -->|Tangentially| G2[Rate: 1]
    F -->|Somewhat| G3[Rate: 2]
    F -->|Yes| G4[Rate: 3]
    F -->|Perfectly| G5[Rate: 4]
    
    G1 --> H{More Results?}
    G2 --> H
    G3 --> H
    G4 --> H
    G5 --> H
    
    H -->|Yes| D
    H -->|No| I[Read AI Answer]
    
    I --> J{Answer Quality?}
    J -->|Poor| K1[Rate: 0-1]
    J -->|Adequate| K2[Rate: 2]
    J -->|Good| K3[Rate: 3]
    J -->|Excellent| K4[Rate: 4]
    
    K1 --> L[Calculate Final Score]
    K2 --> L
    K3 --> L
    K4 --> L
    
    L --> M{More Questions?}
    M -->|Yes| B
    M -->|No| N[Export Scored Results]
```

## Result Analysis Flow

```mermaid
graph TD
    A[Test Results] --> B[Group by Scenario]
    
    B --> C[Author Tests]
    B --> D[Work Tests]
    B --> E[Broad Tests]
    
    C --> C1{Any Filter Failures?}
    C1 -->|Yes| C2[CRITICAL: Debug Filter Logic]
    C1 -->|No| C3[Check Relevance Scores]
    
    D --> D1{Any Filter Failures?}
    D1 -->|Yes| D2[CRITICAL: Debug Filter Logic]
    D1 -->|No| D3[Check Relevance Scores]
    
    E --> E1[Check Overall Scores]
    
    C3 --> F{Pass Rate ≥ 94%?}
    D3 --> G{Pass Rate ≥ 94%?}
    E1 --> H{Pass Rate ≥ 71%?}
    
    F -->|Yes| I1[Author Tests: GOOD]
    F -->|No| I2[Author Tests: NEEDS WORK]
    
    G -->|Yes| J1[Work Tests: GOOD]
    G -->|No| J2[Work Tests: NEEDS WORK]
    
    H -->|Yes| K1[Broad Tests: GOOD]
    H -->|No| K2[Broad Tests: NEEDS WORK]
    
    I1 --> L[Generate Report]
    I2 --> L
    J1 --> L
    J2 --> L
    K1 --> L
    K2 --> L
    
    L --> M[Document Findings]
    M --> N[Share with Team]
    
    style C2 fill:#f99,stroke:#333,stroke-width:3px
    style D2 fill:#f99,stroke:#333,stroke-width:3px
    style I1 fill:#9f9,stroke:#333
    style J1 fill:#9f9,stroke:#333
    style K1 fill:#9f9,stroke:#333
```

## Testing Maturity Levels

```mermaid
graph LR
    A[Level 1:<br/>Initial Setup] --> B[Level 2:<br/>Pilot Testing]
    B --> C[Level 3:<br/>Full Suite]
    C --> D[Level 4:<br/>Regular Monitoring]
    D --> E[Level 5:<br/>Continuous Improvement]
    
    A1[• Install script<br/>• Review docs<br/>• Understand scenarios] -.-> A
    B1[• Run 10 questions<br/>• Manual review<br/>• Validate setup] -.-> B
    C1[• Expand to 100 questions<br/>• Full test run<br/>• Comprehensive report] -.-> C
    D1[• Weekly test runs<br/>• Track trends<br/>• Quick issue detection] -.-> D
    E1[• Question refinement<br/>• Methodology updates<br/>• Performance optimization] -.-> E
    
    style A fill:#fcc
    style B fill:#fc9
    style C fill:#ff9
    style D fill:#9f9
    style E fill:#9cf
```

## Filter Validation Logic

```mermaid
graph TD
    A[Receive Test Results] --> B{Scenario Has Filter?}
    
    B -->|No Filter<br/>Broad Test| C[Skip Filter Check]
    C --> D[Evaluate Relevance Only]
    
    B -->|Author Filter| E[Check Each Result]
    E --> F{result.authorid in<br/>filter.authors?}
    F -->|All Yes| G[Filter: PASS - 100%]
    F -->|Any No| H[Filter: FAIL - Critical]
    
    B -->|Work Filter| I[Check Each Result]
    I --> J{result.workid in<br/>filter.works?}
    J -->|All Yes| K[Filter: PASS - 100%]
    J -->|Any No| L[Filter: FAIL - Critical]
    
    G --> M[Continue to Relevance]
    K --> M
    
    H --> N[Mark Test as<br/>CRITICAL FAILURE]
    L --> N
    
    N --> O[Debug Required]
    
    style H fill:#f99,stroke:#333,stroke-width:3px
    style L fill:#f99,stroke:#333,stroke-width:3px
    style N fill:#f99,stroke:#333,stroke-width:3px
```

## Relevance Rating Guide

```
┌─────────────────────────────────────────────────────────────┐
│                    Relevance Rating Scale                    │
├────────┬──────────────────────┬────────────────────────────┤
│ Score  │ Label                │ Description                 │
├────────┼──────────────────────┼────────────────────────────┤
│   0    │ Completely           │ Text has nothing to do     │
│        │ Irrelevant           │ with query topic           │
├────────┼──────────────────────┼────────────────────────────┤
│   1    │ Tangentially         │ Topic mentioned but not    │
│        │ Related              │ addressing query           │
├────────┼──────────────────────┼────────────────────────────┤
│   2    │ Somewhat             │ Addresses part of query    │
│        │ Relevant             │ but not comprehensive      │
├────────┼──────────────────────┼────────────────────────────┤
│   3    │ Relevant             │ Clearly addresses query    │
│        │                      │ with good detail           │
├────────┼──────────────────────┼────────────────────────────┤
│   4    │ Highly               │ Directly answers query     │
│        │ Relevant             │ with excellent detail      │
└────────┴──────────────────────┴────────────────────────────┘
```

## Example Test Question Lifecycle

```mermaid
graph LR
    A[Create Question] -->|author_001| B["What does Augustine<br/>say about grace?"]
    B --> C[Add to JSON]
    C --> D[Test Script Loads]
    D --> E[Send to API]
    E --> F[API Returns 5 Results]
    
    F --> G[Auto Check:<br/>All authorid = 'augustine'?]
    G -->|Yes| H[✓ Filter Pass]
    G -->|No| I[✗ Critical Fail]
    
    H --> J[Manual Review:<br/>Read 5 paragraphs]
    J --> K[Rate: 4,3,4,3,2]
    K --> L[Sum: 16/20 = 80%]
    
    L --> M{≥70%?}
    M -->|Yes| N[✓ Test PASS]
    M -->|No| O[✗ Test FAIL]
    
    I --> P[Debug Filter Logic]
    
    N --> Q[Include in Report]
    O --> Q
    P --> Q
    
    style H fill:#9f9
    style I fill:#f99
    style N fill:#9f9
    style O fill:#fc9
```

## Report Generation Flow

```mermaid
graph TD
    A[All Tests Complete] --> B[Aggregate Results]
    B --> C[Calculate Summary Stats]
    
    C --> D[Total: X/100 Pass]
    C --> E[Author: X/33 Pass]
    C --> F[Work: X/33 Pass]
    C --> G[Broad: X/34 Pass]
    
    D --> H[Generate Report]
    E --> H
    F --> H
    G --> H
    
    H --> I[Console Summary]
    H --> J[JSON Output<br/>test_results.json]
    H --> K[CSV Export<br/>results.csv]
    
    I --> L[Review Findings]
    J --> L
    K --> L
    
    L --> M{Overall Pass Rate?}
    M -->|≥90%| N[Excellent!<br/>Monitor & Maintain]
    M -->|75-89%| O[Good<br/>Fix specific issues]
    M -->|60-74%| P[Concerning<br/>Investigation needed]
    M -->|<60%| Q[Poor<br/>Major issues]
    
    style N fill:#9f9
    style O fill:#cf9
    style P fill:#fc9
    style Q fill:#f99
```

---

## Quick Reference Commands

**Note:** All test runs now auto-generate unique timestamped filenames to preserve testing history!

**Filename Format:** `test_results_{scenario}_{YYYYMMDD_HHMMSS}.json` and `.csv`

```bash
# Setup
cd /Users/david/CS_senior_project/JETON_SERVER/server
source venv/bin/activate
python main.py  # Start server

# Run Tests (in new terminal - auto-generates timestamped files)
python scripts/run_tests.py --pilot                    # → test_results_pilot_20251104_143022.json/csv
python scripts/run_tests.py --questions tests/sample_questions.json  # → test_results_all_...
python scripts/run_tests.py --questions tests/sample_questions.json --scenario author  # → test_results_author_...
python scripts/run_tests.py --questions tests/sample_questions.json --scenario work    # → test_results_work_...
python scripts/run_tests.py --questions tests/sample_questions.json --scenario broad   # → test_results_broad_...

# Custom Filenames (optional)
python scripts/run_tests.py --pilot --output custom.json              # Custom JSON name
python scripts/run_tests.py --pilot --output custom.json --csv custom.csv  # Custom both
```

---

## Visual Summary

```
┌─────────────────────────────────────────────────────────────┐
│              JETON Testing System Overview                   │
└─────────────────────────────────────────────────────────────┘

INPUT: 100 Questions
├── 33 Author-Filtered (What does [AUTHOR] say about X?)
├── 33 Work-Filtered   (What does [WORK] say about X?)
└── 34 Broad           (What is X?)

         ↓

EXECUTION: run_tests.py
├── Load questions from JSON
├── Send requests to /test API
├── Collect responses
└── Automatic validation

         ↓

VALIDATION
├── Automated Checks
│   ├── Filter accuracy (100% required)
│   ├── Source diversity
│   └── Processing time
│
└── Manual Review
    ├── Relevance rating (0-4)
    └── Answer quality (0-4)

         ↓

OUTPUT
├── Console: Summary stats
├── JSON: Complete raw data
└── CSV: Manual review spreadsheet

         ↓

ANALYSIS
├── Pass/Fail by scenario
├── Performance metrics
├── Issue identification
└── Recommendations

         ↓

ACTION
├── Fix critical issues
├── Refine questions
├── Improve system
└── Retest
```

---

**Note:** These diagrams are written in Mermaid syntax. They will render automatically in:
- GitHub
- GitLab  
- Many markdown editors
- VS Code (with Mermaid extension)
- Online: https://mermaid.live/

To view, paste the code blocks into any Mermaid-compatible viewer.

---

**Created:** November 4, 2025  
**Purpose:** Visual guide to JETON testing workflow

