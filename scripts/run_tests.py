"""
Automated Testing Script for JETON Theological Search System

This script implements the three-scenario testing methodology:
1. Author-Filtered Testing
2. Work-Filtered Testing  
3. Broad/Unfiltered Testing

Usage:
    python scripts/run_tests.py --scenario all --output results.json
    python scripts/run_tests.py --scenario author --questions author_questions.json
    python scripts/run_tests.py --pilot  # Run 10 pilot questions
"""

import argparse
import json
import time
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import csv
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:8080"
DEFAULT_TOP_K = 5
DEFAULT_RETURN_FIELDS = ["record_id", "text", "authorid", "workid", "knn_distance", "answer"]
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


@dataclass
class TestQuestion:
    """Represents a single test question"""
    id: str
    scenario: str  # "author", "work", or "broad"
    query: str
    authors: Optional[List[str]] = None
    works: Optional[List[str]] = None
    expected_author: Optional[str] = None
    expected_work: Optional[str] = None
    expected_topics: Optional[List[str]] = None


@dataclass
class TestResult:
    """Represents the result of a single test"""
    question_id: str
    scenario: str
    query: str
    filter_accuracy: float  # 0-100%
    relevance_score: float  # 0-100%
    answer_quality: Optional[float] = None  # 0-100%
    source_diversity: Optional[float] = None  # 0-100%
    overall_score: float = 0.0
    passed: bool = False
    critical_failure: bool = False
    failure_reason: Optional[str] = None
    processing_time: float = 0.0
    results_count: int = 0
    raw_response: Optional[Dict[str, Any]] = None


class LLMEvaluator:
    """LLM-based rubric evaluator using Claude for automatic scoring"""
    
    RELEVANCE_RUBRIC = """
Rate the relevance of this text passage to the query on a scale of 0-4:

0 = Completely Irrelevant: Text has nothing to do with query topic
1 = Tangentially Related: Topic mentioned but not addressing query
2 = Somewhat Relevant: Addresses part of query but not comprehensive
3 = Relevant: Clearly addresses query with good detail
4 = Highly Relevant: Directly answers query with excellent detail

Query: {query}

Text Passage:
{text}

Respond with ONLY a single number (0, 1, 2, 3, or 4) representing the relevance score.
"""

    ANSWER_QUALITY_RUBRIC = """
Rate the quality of this AI-generated answer on a scale of 0-4:

0 = Incorrect/Unhelpful: Factually wrong or doesn't address query
1 = Minimal: Very basic, missing key information
2 = Adequate: Covers basics but lacks depth
3 = Good: Comprehensive, accurate, well-cited
4 = Excellent: Comprehensive, nuanced, multiple perspectives, well-cited

Query: {query}

AI Answer:
{answer}

Source Texts Used:
{sources}

Respond with ONLY a single number (0, 1, 2, 3, or 4) representing the answer quality score.
"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.use_llm = bool(self.api_key)
        
        if not self.use_llm:
            print("\n⚠️  Warning: No Anthropic API key found. Using fallback scoring (all zeros).")
            print("   Set ANTHROPIC_API_KEY environment variable to enable LLM-based scoring.\n")
    
    def rate_relevance(self, query: str, text: str) -> int:
        """Rate relevance of a text passage to a query (0-4 scale)"""
        if not self.use_llm:
            return 0  # Fallback to manual scoring
        
        prompt = self.RELEVANCE_RUBRIC.format(query=query, text=text[:2000])  # Limit text length
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 10,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            score_text = result["content"][0]["text"].strip()
            
            # Extract number from response
            score = int(score_text[0]) if score_text and score_text[0].isdigit() else 0
            return min(max(score, 0), 4)  # Clamp to 0-4
            
        except Exception as e:
            print(f"    ⚠️  LLM evaluation error: {str(e)[:50]}... Using fallback score 0")
            return 0
    
    def rate_answer_quality(self, query: str, answer: str, sources: List[str]) -> int:
        """Rate quality of AI-generated answer (0-4 scale)"""
        if not self.use_llm:
            return 0  # Fallback to manual scoring
        
        sources_text = "\n".join(f"- {s[:500]}" for s in sources[:3])  # Limit sources
        prompt = self.ANSWER_QUALITY_RUBRIC.format(
            query=query,
            answer=answer[:2000],
            sources=sources_text[:1500]
        )
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 10,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            score_text = result["content"][0]["text"].strip()
            
            # Extract number from response
            score = int(score_text[0]) if score_text and score_text[0].isdigit() else 0
            return min(max(score, 0), 4)  # Clamp to 0-4
            
        except Exception as e:
            print(f"    ⚠️  LLM evaluation error: {str(e)[:50]}... Using fallback score 0")
            return 0
    
    def calculate_relevance_score(self, ratings: List[int]) -> float:
        """Calculate relevance score from individual ratings (0-100%)"""
        if not ratings:
            return 0.0
        max_possible = len(ratings) * 4  # Max 4 per rating
        total = sum(ratings)
        return (total / max_possible * 100) if max_possible > 0 else 0.0
    
    def calculate_answer_quality_score(self, rating: int) -> float:
        """Calculate answer quality score from single rating (0-100%)"""
        return (rating / 4.0 * 100) if rating >= 0 else 0.0


class TestRunner:
    """Main test runner for JETON system"""
    
    def __init__(self, base_url: str = API_BASE_URL, verbose: bool = True, use_llm_scoring: bool = True):
        self.base_url = base_url
        self.verbose = verbose
        self.use_llm_scoring = use_llm_scoring
        self.evaluator = LLMEvaluator() if use_llm_scoring else None
        
    def run_test(self, question: TestQuestion) -> TestResult:
        """Run a single test and return results"""
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"Testing: {question.query}")
            print(f"Scenario: {question.scenario}")
            
        # Prepare request
        payload = {
            "query": question.query,
            "agentic": True,
            "top_k": DEFAULT_TOP_K,
            "return_fields": DEFAULT_RETURN_FIELDS,
            "authors": question.authors or [],
            "works": question.works or []
        }
        
        # Execute request
        start_time = time.time()
        try:
            response = requests.post(f"{self.base_url}/test", json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            return TestResult(
                question_id=question.id,
                scenario=question.scenario,
                query=question.query,
                filter_accuracy=0.0,
                relevance_score=0.0,
                passed=False,
                critical_failure=True,
                failure_reason=f"Request failed: {str(e)}",
                processing_time=time.time() - start_time
            )
        
        processing_time = time.time() - start_time
        
        # Evaluate results based on scenario
        if question.scenario == "author":
            result = self._evaluate_author_test(question, data, processing_time)
        elif question.scenario == "work":
            result = self._evaluate_work_test(question, data, processing_time)
        else:  # broad
            result = self._evaluate_broad_test(question, data, processing_time)
        
        if self.verbose:
            self._print_result(result)
            
        return result
    
    def _evaluate_author_test(self, question: TestQuestion, data: Dict[str, Any], proc_time: float) -> TestResult:
        """Evaluate author-filtered test"""
        results = data.get("results", [])
        
        if not results:
            return TestResult(
                question_id=question.id,
                scenario=question.scenario,
                query=question.query,
                filter_accuracy=0.0,
                relevance_score=0.0,
                passed=False,
                critical_failure=True,
                failure_reason="No results returned",
                processing_time=proc_time,
                results_count=0,
                raw_response=data
            )
        
        # Check filter accuracy
        correct_authors = sum(1 for r in results if r.get("authorid") in (question.authors or []))
        filter_accuracy = (correct_authors / len(results)) * 100 if results else 0.0
        
        # Critical failure if ANY wrong author
        critical_failure = filter_accuracy < 100.0
        
        # LLM-based relevance scoring
        if self.evaluator:
            if self.verbose:
                print("  Evaluating relevance with LLM...")
            relevance_ratings = []
            for i, result in enumerate(results[:5], 1):  # Rate top 5 results
                text = result.get("text", "")
                if text:
                    rating = self.evaluator.rate_relevance(question.query, text)
                    relevance_ratings.append(rating)
                    if self.verbose:
                        print(f"    Result {i}/5: Relevance = {rating}/4")
                    time.sleep(0.3)  # Small delay between API calls
            
            relevance_score = self.evaluator.calculate_relevance_score(relevance_ratings)
        else:
            relevance_score = 0.0  # Fallback to manual scoring
        
        # Determine overall pass/fail
        if critical_failure:
            overall_score = 0.0
            passed = False
            failure_reason = f"Filter accuracy {filter_accuracy}% (expected 100%)"
        else:
            overall_score = relevance_score
            passed = relevance_score >= 70.0
            failure_reason = None if passed else f"Relevance {relevance_score}% < 70%"
        
        return TestResult(
            question_id=question.id,
            scenario=question.scenario,
            query=question.query,
            filter_accuracy=filter_accuracy,
            relevance_score=relevance_score,
            overall_score=overall_score,
            passed=passed,
            critical_failure=critical_failure,
            failure_reason=failure_reason,
            processing_time=proc_time,
            results_count=len(results),
            raw_response=data
        )
    
    def _evaluate_work_test(self, question: TestQuestion, data: Dict[str, Any], proc_time: float) -> TestResult:
        """Evaluate work-filtered test"""
        results = data.get("results", [])
        
        if not results:
            return TestResult(
                question_id=question.id,
                scenario=question.scenario,
                query=question.query,
                filter_accuracy=0.0,
                relevance_score=0.0,
                passed=False,
                critical_failure=True,
                failure_reason="No results returned",
                processing_time=proc_time,
                results_count=0,
                raw_response=data
            )
        
        # Check filter accuracy
        correct_works = sum(1 for r in results if r.get("workid") in (question.works or []))
        filter_accuracy = (correct_works / len(results)) * 100 if results else 0.0
        
        # Critical failure if ANY wrong work
        critical_failure = filter_accuracy < 100.0
        
        # LLM-based relevance scoring
        if self.evaluator:
            if self.verbose:
                print("  Evaluating relevance with LLM...")
            relevance_ratings = []
            for i, result in enumerate(results[:5], 1):  # Rate top 5 results
                text = result.get("text", "")
                if text:
                    rating = self.evaluator.rate_relevance(question.query, text)
                    relevance_ratings.append(rating)
                    if self.verbose:
                        print(f"    Result {i}/5: Relevance = {rating}/4")
                    time.sleep(0.3)  # Small delay between API calls
            
            relevance_score = self.evaluator.calculate_relevance_score(relevance_ratings)
        else:
            relevance_score = 0.0  # Fallback to manual scoring
        
        # Determine overall pass/fail
        if critical_failure:
            overall_score = 0.0
            passed = False
            failure_reason = f"Filter accuracy {filter_accuracy}% (expected 100%)"
        else:
            overall_score = relevance_score
            passed = relevance_score >= 70.0
            failure_reason = None if passed else f"Relevance {relevance_score}% < 70%"
        
        return TestResult(
            question_id=question.id,
            scenario=question.scenario,
            query=question.query,
            filter_accuracy=filter_accuracy,
            relevance_score=relevance_score,
            overall_score=overall_score,
            passed=passed,
            critical_failure=critical_failure,
            failure_reason=failure_reason,
            processing_time=proc_time,
            results_count=len(results),
            raw_response=data
        )
    
    def _evaluate_broad_test(self, question: TestQuestion, data: Dict[str, Any], proc_time: float) -> TestResult:
        """Evaluate broad/unfiltered test"""
        results = data.get("results", [])
        
        if not results:
            return TestResult(
                question_id=question.id,
                scenario=question.scenario,
                query=question.query,
                filter_accuracy=100.0,  # N/A for broad tests
                relevance_score=0.0,
                passed=False,
                critical_failure=False,
                failure_reason="No results returned",
                processing_time=proc_time,
                results_count=0,
                raw_response=data
            )
        
        # LLM-based relevance scoring
        if self.evaluator:
            if self.verbose:
                print("  Evaluating relevance with LLM...")
            relevance_ratings = []
            for i, result in enumerate(results[:5], 1):  # Rate top 5 results
                text = result.get("text", "")
                if text:
                    rating = self.evaluator.rate_relevance(question.query, text)
                    relevance_ratings.append(rating)
                    if self.verbose:
                        print(f"    Result {i}/5: Relevance = {rating}/4")
                    time.sleep(0.3)  # Small delay between API calls
            
            relevance_score = self.evaluator.calculate_relevance_score(relevance_ratings)
            
            # LLM-based answer quality scoring
            if self.verbose:
                print("  Evaluating answer quality with LLM...")
            ai_answer = data.get("ai_answer", "")
            source_texts = [r.get("text", "")[:500] for r in results[:3]]
            
            answer_quality_rating = self.evaluator.rate_answer_quality(
                question.query, 
                ai_answer, 
                source_texts
            )
            answer_quality = self.evaluator.calculate_answer_quality_score(answer_quality_rating)
            
            if self.verbose:
                print(f"    Answer Quality: {answer_quality_rating}/4 ({answer_quality:.1f}%)")
        else:
            relevance_score = 0.0  # Fallback to manual scoring
            answer_quality = 0.0  # Fallback to manual scoring
        
        # Source diversity
        unique_authors = len(set(r.get("authorid") for r in results if r.get("authorid")))
        if unique_authors <= 1:
            diversity_points = 0
        elif unique_authors <= 3:
            diversity_points = 1
        else:
            diversity_points = 2
        source_diversity = (diversity_points / 2) * 100
        
        # Calculate overall score
        overall_score = (relevance_score * 0.5) + (answer_quality * 0.3) + (source_diversity * 0.2)
        passed = overall_score >= 65.0
        failure_reason = None if passed else f"Overall score {overall_score:.1f}% < 65%"
        
        return TestResult(
            question_id=question.id,
            scenario=question.scenario,
            query=question.query,
            filter_accuracy=100.0,  # N/A
            relevance_score=relevance_score,
            answer_quality=answer_quality,
            source_diversity=source_diversity,
            overall_score=overall_score,
            passed=passed,
            critical_failure=False,
            failure_reason=failure_reason,
            processing_time=proc_time,
            results_count=len(results),
            raw_response=data
        )
    
    def _print_result(self, result: TestResult):
        """Print test result to console"""
        status = "✅ PASS" if result.passed else ("🚨 CRITICAL FAIL" if result.critical_failure else "❌ FAIL")
        print(f"\n{status}")
        print(f"  Filter Accuracy: {result.filter_accuracy:.1f}%")
        print(f"  Relevance Score: {result.relevance_score:.1f}%")
        if result.answer_quality is not None:
            print(f"  Answer Quality: {result.answer_quality:.1f}%")
        if result.source_diversity is not None:
            print(f"  Source Diversity: {result.source_diversity:.1f}%")
        print(f"  Overall Score: {result.overall_score:.1f}%")
        print(f"  Processing Time: {result.processing_time:.2f}s")
        print(f"  Results Count: {result.results_count}")
        if result.failure_reason:
            print(f"  Failure Reason: {result.failure_reason}")
    
    def run_test_suite(self, questions: List[TestQuestion]) -> List[TestResult]:
        """Run a full test suite"""
        results = []
        
        print(f"\n{'='*80}")
        print(f"Running Test Suite: {len(questions)} questions")
        print(f"{'='*80}")
        
        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}]", end=" ")
            result = self.run_test(question)
            results.append(result)
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.5)
        
        return results
    
    def generate_report(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate summary report from test results"""
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        critical_failures = sum(1 for r in results if r.critical_failure)
        
        # Group by scenario
        by_scenario = {}
        for result in results:
            if result.scenario not in by_scenario:
                by_scenario[result.scenario] = []
            by_scenario[result.scenario].append(result)
        
        scenario_stats = {}
        for scenario, scenario_results in by_scenario.items():
            scenario_total = len(scenario_results)
            scenario_passed = sum(1 for r in scenario_results if r.passed)
            avg_filter = sum(r.filter_accuracy for r in scenario_results) / scenario_total
            avg_relevance = sum(r.relevance_score for r in scenario_results) / scenario_total
            avg_time = sum(r.processing_time for r in scenario_results) / scenario_total
            
            scenario_stats[scenario] = {
                "total": scenario_total,
                "passed": scenario_passed,
                "pass_rate": (scenario_passed / scenario_total * 100) if scenario_total else 0,
                "avg_filter_accuracy": avg_filter,
                "avg_relevance": avg_relevance,
                "avg_processing_time": avg_time
            }
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_questions": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": (passed / total * 100) if total else 0,
                "critical_failures": critical_failures
            },
            "by_scenario": scenario_stats,
            "all_results": [asdict(r) for r in results]
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """Print summary report to console"""
        print(f"\n{'='*80}")
        print("TEST SUMMARY REPORT")
        print(f"{'='*80}")
        print(f"\nTimestamp: {report['timestamp']}")
        
        summary = report['summary']
        print(f"\nOverall Results:")
        print(f"  Total Questions: {summary['total_questions']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Pass Rate: {summary['pass_rate']:.1f}%")
        print(f"  Critical Failures: {summary['critical_failures']}")
        
        print(f"\nBy Scenario:")
        for scenario, stats in report['by_scenario'].items():
            print(f"\n  {scenario.upper()} Tests:")
            print(f"    Total: {stats['total']}")
            print(f"    Passed: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1f}%)")
            print(f"    Avg Filter Accuracy: {stats['avg_filter_accuracy']:.1f}%")
            print(f"    Avg Relevance: {stats['avg_relevance']:.1f}%")
            print(f"    Avg Processing Time: {stats['avg_processing_time']:.2f}s")
        
        print(f"\n{'='*80}")


def load_questions_from_json(filepath: str) -> List[TestQuestion]:
    """Load test questions from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    questions = []
    for item in data.get("questions", []):
        questions.append(TestQuestion(**item))
    
    return questions


def get_pilot_questions() -> List[TestQuestion]:
    """Get a small set of pilot questions for initial testing"""
    return [
        # Author tests (3)
        TestQuestion(
            id="author_001",
            scenario="author",
            query="What does Augustine say about original sin?",
            authors=["augustine"],
            expected_author="augustine"
        ),
        TestQuestion(
            id="author_002",
            scenario="author",
            query="According to Aquinas, what is natural law?",
            authors=["aquinas"],
            expected_author="aquinas"
        ),
        TestQuestion(
            id="author_003",
            scenario="author",
            query="How does Calvin explain predestination?",
            authors=["calvin"],
            expected_author="calvin"
        ),
        
        # Work tests (3)
        TestQuestion(
            id="work_001",
            scenario="work",
            query="What does the Confessions say about Augustine's conversion?",
            works=["confessions"],
            expected_work="confessions"
        ),
        TestQuestion(
            id="work_002",
            scenario="work",
            query="How is the Trinity explained in the Summa Theologica?",
            works=["summa"],
            expected_work="summa"
        ),
        TestQuestion(
            id="work_003",
            scenario="work",
            query="What do the Institutes say about election?",
            works=["institutes"],
            expected_work="institutes"
        ),
        
        # Broad tests (4)
        TestQuestion(
            id="broad_001",
            scenario="broad",
            query="What is the Trinity?"
        ),
        TestQuestion(
            id="broad_002",
            scenario="broad",
            query="What is grace?"
        ),
        TestQuestion(
            id="broad_003",
            scenario="broad",
            query="What is justification?"
        ),
        TestQuestion(
            id="broad_004",
            scenario="broad",
            query="What is the relationship between faith and works?"
        ),
    ]


def export_to_csv(results: List[TestResult], filepath: str):
    """Export results to CSV for manual review"""
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'question_id', 'scenario', 'query', 'passed', 'critical_failure',
            'filter_accuracy', 'relevance_score', 'answer_quality', 'source_diversity',
            'overall_score', 'processing_time', 'results_count', 'failure_reason'
        ])
        writer.writeheader()
        for result in results:
            writer.writerow({
                'question_id': result.question_id,
                'scenario': result.scenario,
                'query': result.query,
                'passed': result.passed,
                'critical_failure': result.critical_failure,
                'filter_accuracy': f"{result.filter_accuracy:.1f}",
                'relevance_score': f"{result.relevance_score:.1f}",
                'answer_quality': f"{result.answer_quality:.1f}" if result.answer_quality else "N/A",
                'source_diversity': f"{result.source_diversity:.1f}" if result.source_diversity else "N/A",
                'overall_score': f"{result.overall_score:.1f}",
                'processing_time': f"{result.processing_time:.2f}",
                'results_count': result.results_count,
                'failure_reason': result.failure_reason or ""
            })


def main():
    parser = argparse.ArgumentParser(description="Run JETON testing suite")
    parser.add_argument("--scenario", choices=["author", "work", "broad", "all"], default="all",
                        help="Which scenario to test")
    parser.add_argument("--questions", type=str, help="Path to questions JSON file")
    parser.add_argument("--pilot", action="store_true", help="Run 10 pilot questions")
    parser.add_argument("--output", type=str, help="Output file for results (default: auto-generated timestamp)")
    parser.add_argument("--csv", type=str, help="Export results to CSV file (default: auto-generated if not specified)")
    parser.add_argument("--url", type=str, default=API_BASE_URL, help="API base URL")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM-based scoring (use manual scoring placeholders)")
    
    args = parser.parse_args()
    
    # Generate timestamp-based filenames if not specified
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output is None:
        test_type = "pilot" if args.pilot else args.scenario
        args.output = f"test_results_{test_type}_{timestamp}.json"
    
    # Auto-generate CSV filename if --csv flag is present but no value given
    # Note: This is handled by checking if user wants CSV export later
    
    # Create test runner with LLM scoring enabled by default
    use_llm = not args.no_llm
    runner = TestRunner(base_url=args.url, verbose=not args.quiet, use_llm_scoring=use_llm)
    
    if use_llm and not args.quiet:
        print("\n🤖 LLM-based automatic scoring enabled (using Claude Sonnet 3.5)")
        print("   Each test result will be evaluated using the rubric from documentation.")
        print("   Use --no-llm flag to disable automatic scoring.\n")
    
    # Load questions
    if args.pilot:
        questions = get_pilot_questions()
        print("Running pilot test with 10 questions...")
    elif args.questions:
        questions = load_questions_from_json(args.questions)
        print(f"Loaded {len(questions)} questions from {args.questions}")
    else:
        print("Error: Please provide --questions file or use --pilot flag")
        return
    
    # Filter by scenario if specified
    if args.scenario != "all":
        questions = [q for q in questions if q.scenario == args.scenario]
        print(f"Filtered to {len(questions)} {args.scenario} questions")
    
    # Run tests
    results = runner.run_test_suite(questions)
    
    # Generate and print report
    report = runner.generate_report(results)
    runner.print_report(report)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nFull results saved to: {args.output}")
    
    # Auto-generate CSV filename from JSON filename if not specified but seems desired
    # For now, always export to CSV with auto-generated name
    if args.csv:
        csv_filename = args.csv
    else:
        # Auto-generate CSV filename based on JSON filename
        csv_filename = args.output.replace('.json', '.csv')
    
    export_to_csv(results, csv_filename)
    print(f"Results exported to CSV: {csv_filename}")


if __name__ == "__main__":
    main()

