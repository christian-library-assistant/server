# Testing System Changelog

## [1.2.0] - 2025-11-04

### Added
- **🤖 LLM-Based Automatic Rubric Scoring** - Major enhancement!
  - Automated relevance rating (0-4 scale) using Claude Sonnet 3.5
  - Automated answer quality rating (0-4 scale) using Claude Sonnet 3.5
  - Based on the exact rubric from documentation
  - Evaluates each result automatically - no manual scoring needed!
  - Fallback to manual scoring if API key not available
  - Use `--no-llm` flag to disable and use manual scoring

### Changed
- Test results now include actual scores instead of placeholder zeros
- More detailed console output showing individual result ratings
- Longer test runtime due to LLM evaluation calls (~30s for 10 pilot questions)

### Benefits
- ✅ Fully automated testing - run and get complete scores
- ✅ Consistent evaluation using documented rubric
- ✅ Compare results objectively over time
- ✅ Still supports manual review if preferred

---

## [1.1.0] - 2025-11-04

### Added
- **Automatic Timestamped Filenames** - Test results now automatically generate unique timestamped filenames
  - Format: `test_results_{scenario}_{YYYYMMDD_HHMMSS}.json` and `.csv`
  - Example: `test_results_pilot_20251104_143022.json`
  - Prevents overwriting previous test results
  - Enables tracking testing history over time
  - Custom filenames still supported via `--output` and `--csv` flags

### Changed
- Default output filename is now auto-generated instead of fixed `test_results.json`
- CSV files are now always exported (previously optional)
- CSV filename auto-generated from JSON filename if not specified

### Benefits
- ✅ Never lose previous test results
- ✅ Easy comparison between test runs
- ✅ Track improvements over time
- ✅ Clear chronological organization
- ✅ Can still use custom names when needed

### Migration Notes
- No breaking changes - existing scripts will work
- Old behavior available by specifying `--output test_results.json`
- Look for timestamped files instead of fixed filename

### Example Usage

**Before (overwrites results):**
```bash
python scripts/run_tests.py --pilot
# Creates: test_results.json (overwrites if exists)
```

**After (preserves history):**
```bash
python scripts/run_tests.py --pilot
# Creates: test_results_pilot_20251104_143022.json
#          test_results_pilot_20251104_143022.csv

# Run again 5 minutes later:
python scripts/run_tests.py --pilot
# Creates: test_results_pilot_20251104_144500.json
#          test_results_pilot_20251104_144500.csv

# Both sets of results preserved!
```

**Custom naming (still works):**
```bash
python scripts/run_tests.py --pilot --output my_test.json
# Creates: my_test.json and my_test.csv
```

---

## [1.0.0] - 2025-11-04

### Initial Release
- Three testing scenarios: Author-Filtered, Work-Filtered, Broad/Unfiltered
- Automated test runner script
- Sample question bank (50 questions)
- Comprehensive documentation
- Visual workflow diagrams
- Scoring rubrics and evaluation framework
- JSON and CSV export
- Automated filter validation

