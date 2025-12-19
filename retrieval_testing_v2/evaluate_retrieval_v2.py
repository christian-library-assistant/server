#!/usr/bin/env python3
"""
Retrieval Evaluation Script V2

This script evaluates the Manticore retrieval system by testing generated
questions against the /test endpoint and scoring the results.

Usage:
    python evaluate_retrieval_v2.py                    # Use default book
    python evaluate_retrieval_v2.py --book anf01       # Use specific book
    python evaluate_retrieval_v2.py --list             # List available books
"""

import requests
import time
import argparse
from typing import Dict, List, Any
from pathlib import Path
from utils_v2 import (
    load_questions_json,
    calculate_retrieval_score,
    calculate_aggregate_metrics,
    save_results_json,
    save_analytics_report,
    format_timestamp,
    print_progress_bar
)
import config_v2
from config_v2 import (
    TEST_ENDPOINT,
    TOP_K,
    USE_AGENTIC,
    FILTER_WORKS,
    REQUEST_DELAY,
    VERBOSE,
    set_input_xml,
    OUTPUT_DIR
)


def query_test_endpoint(
    query: str,
    top_k: int = TOP_K,
    agentic: bool = USE_AGENTIC,
    works: List[str] = None
) -> Dict[str, Any]:
    """
    Query the /test endpoint and get results.
    
    Args:
        query: Search query
        top_k: Number of results to return
        agentic: Whether to use agentic mode
        works: List of works to filter
    
    Returns:
        API response dictionary
    
    Raises:
        Exception: If API request fails
    """
    if works is None:
        works = FILTER_WORKS
    
    payload = {
        "query": query,
        "agentic": agentic,
        "works": works,
        "top_k": top_k,
        "return_fields": ["record_id", "knn_distance", "text"]
    }
    
    try:
        response = requests.post(TEST_ENDPOINT, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")


def extract_returned_paragraphs(api_response: Dict[str, Any]) -> List[str]:
    """
    Extract paragraph IDs from API response.
    
    Args:
        api_response: Response from /test endpoint
    
    Returns:
        List of paragraph IDs in ranked order
    """
    if "results" not in api_response:
        return []
    
    results = api_response["results"]
    return [r.get("record_id", "") for r in results if r.get("record_id")]


def get_matched_ranks(gold_paragraphs: List[str], returned_paragraphs: List[str]) -> List[int]:
    """
    Get the ranks of matched gold paragraphs.
    
    Args:
        gold_paragraphs: List of expected paragraph IDs
        returned_paragraphs: List of returned paragraph IDs
    
    Returns:
        List of ranks (1-indexed) for matched paragraphs
    """
    ranks = []
    for gold_id in gold_paragraphs:
        if gold_id in returned_paragraphs:
            rank = returned_paragraphs.index(gold_id) + 1
            ranks.append(rank)
    return ranks


def evaluate_single_query(question_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single query against the retrieval system.
    
    Args:
        question_item: Question dictionary with query and gold_paragraphs
    
    Returns:
        Result dictionary with scores and metadata
    """
    query = question_item["query"]
    gold_paragraphs = question_item["gold_paragraphs"]
    
    try:
        # Query the test endpoint
        api_response = query_test_endpoint(query)
        
        # Extract returned paragraph IDs
        returned_paragraphs = extract_returned_paragraphs(api_response)
        
        # Calculate score
        score_result = calculate_retrieval_score(gold_paragraphs, returned_paragraphs)
        
        # Get matched ranks
        matched_ranks = get_matched_ranks(gold_paragraphs, returned_paragraphs)
        
        # Build result
        result = {
            "query": query,
            "gold_paragraphs": gold_paragraphs,
            "returned_paragraphs": returned_paragraphs[:TOP_K],
            "score_breakdown": score_result["score_breakdown"],
            "raw_score": score_result["raw_score"],
            "max_possible": score_result["max_possible"],
            "normalized_score": score_result["normalized_score"],
            "label": score_result["label"],
            "matched_count": score_result["matched_count"],
            "total_gold": score_result["total_gold"],
            "matched_ranks": matched_ranks,
            "status": "success"
        }
        
        return result
        
    except Exception as e:
        # Handle errors gracefully
        if VERBOSE:
            print(f"\n⚠️  Error evaluating query: {query[:50]}... - {str(e)}")
        
        return {
            "query": query,
            "gold_paragraphs": gold_paragraphs,
            "returned_paragraphs": [],
            "score_breakdown": {
                "matched_top3": 0,
                "matched_top10": 0,
                "matched_beyond10": 0,
                "missing_gold": len(gold_paragraphs)
            },
            "raw_score": -2 * len(gold_paragraphs),
            "max_possible": 3 * len(gold_paragraphs),
            "normalized_score": 0.0,
            "label": "Error",
            "matched_count": 0,
            "total_gold": len(gold_paragraphs),
            "matched_ranks": [],
            "status": "error",
            "error": str(e)
        }


def evaluate_all_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Evaluate all questions against the retrieval system.
    
    Args:
        questions: List of question dictionaries
    
    Returns:
        List of result dictionaries
    """
    results = []
    total = len(questions)
    
    print(f"🔍 Evaluating {total} questions against retrieval system...")
    print(f"   Endpoint: {TEST_ENDPOINT}")
    print(f"   Top K: {TOP_K}")
    print(f"   Agentic: {USE_AGENTIC}")
    print(f"   Works Filter: {FILTER_WORKS}")
    print()
    
    for i, question_item in enumerate(questions):
        if VERBOSE:
            print_progress_bar(i + 1, total, prefix='Progress')
        
        result = evaluate_single_query(question_item)
        results.append(result)
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)
    
    print()
    return results


def print_evaluation_summary(results: List[Dict[str, Any]], aggregate: Dict[str, Any]):
    """
    Print a summary of evaluation results to console.
    
    Args:
        results: List of result dictionaries
        aggregate: Aggregate metrics dictionary
    """
    print()
    print("=" * 80)
    print(" EVALUATION SUMMARY ".center(80, "="))
    print("=" * 80)
    print()
    print("📊 Overall Metrics:")
    print(f"   Total Queries:            {aggregate['total_queries']}")
    print(f"   Average Normalized Score: {aggregate['avg_normalized_score']:.3f}")
    print(f"   Average Raw Score:        {aggregate['avg_raw_score']:.2f}")
    print(f"   Average Matched Count:    {aggregate['avg_matched_count']:.2f}")
    print(f"   Average Matched Rank:     {aggregate['avg_matched_rank']:.2f}")
    print()
    print(f"✅ Perfect Matches:          {aggregate['perfect_matches']} ({aggregate['perfect_match_rate']:.1%})")
    print(f"❌ No Matches:               {aggregate['no_matches']} ({aggregate['no_match_rate']:.1%})")
    print()
    print("📈 Score Distribution:")
    for label, count in sorted(
        aggregate['label_distribution'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        percentage = count / aggregate['total_queries'] * 100
        print(f"   {label:20s}: {count:3d} ({percentage:.1f}%)")
    print()
    
    # Show top 5 best and worst results
    sorted_results = sorted(results, key=lambda x: x["normalized_score"], reverse=True)
    
    print("🏆 Top 5 Best Results:")
    for i, result in enumerate(sorted_results[:5], 1):
        print(f"   [{i}] Score: {result['normalized_score']:.3f} - {result['query'][:60]}...")
    
    print()
    print("⚠️  Top 5 Worst Results:")
    worst_results = [r for r in sorted_results if r['status'] != 'error']
    for i, result in enumerate(worst_results[-5:], 1):
        print(f"   [{i}] Score: {result['normalized_score']:.3f} - {result['query'][:60]}...")
    
    print()
    print("=" * 80)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval system against generated questions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python evaluate_retrieval_v2.py                    # Use default book
    python evaluate_retrieval_v2.py --book anf01       # Use specific book
    python evaluate_retrieval_v2.py --list             # List available books
        """
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available books with generated questions"
    )
    parser.add_argument(
        "--book", "-b",
        help="Book name (must have run generate_questions_v2.py first)"
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    
    # Handle --list flag
    if args.list:
        print("\n📚 Books with generated questions (in output/):")
        output_dir = Path(OUTPUT_DIR)
        if output_dir.exists():
            json_files = list(output_dir.glob("test_questions_*.json"))
            if json_files:
                for f in json_files:
                    book = f.stem.replace("test_questions_", "")
                    print(f"   • {book}")
                print(f"\nUsage: python evaluate_retrieval_v2.py --book <name>")
            else:
                print("   (No generated questions found)")
                print("\nRun generate_questions_v2.py first to create questions.")
        return
    
    # Set book if specified
    if args.book:
        set_input_xml(f"data/{args.book}.xml")
    
    # Get current config values
    book_name = config_v2.BOOK_NAME
    questions_json = config_v2.QUESTIONS_JSON
    results_prefix = config_v2.RESULTS_JSON_PREFIX
    analytics_prefix = config_v2.ANALYTICS_REPORT_PREFIX
    
    print("=" * 80)
    print(" RETRIEVAL SYSTEM EVALUATION V2 ".center(80, "="))
    print("=" * 80)
    print()
    print(f"📚 Book: {book_name}")
    print()
    
    # Load questions
    print(f"📖 Loading questions from {questions_json}")
    try:
        questions = load_questions_json(questions_json)
    except FileNotFoundError:
        print(f"❌ File not found: {questions_json}")
        print(f"   Run: python generate_questions_v2.py --book {book_name}")
        return
    except Exception as e:
        print(f"❌ Error loading questions: {e}")
        return
    
    if not questions:
        print("❌ No questions found in file")
        return
    
    print(f"✅ Loaded {len(questions)} questions")
    print()
    
    # Test API endpoint connectivity
    print("🔌 Testing API endpoint connectivity...")
    try:
        test_response = requests.get(TEST_ENDPOINT.replace('/test', '/health'), timeout=5)
        print("✅ API endpoint is reachable")
    except Exception as e:
        print(f"⚠️  Warning: Could not reach API endpoint: {e}")
        print("   Make sure the server is running before continuing.")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    print()
    
    # Evaluate all questions
    results = evaluate_all_questions(questions)
    
    # Calculate aggregate metrics
    aggregate_metrics = calculate_aggregate_metrics(results)
    
    # Print summary
    print_evaluation_summary(results, aggregate_metrics)
    
    # Save results to output directory
    timestamp = format_timestamp()
    results_filename = str(Path(OUTPUT_DIR) / f"{results_prefix}_{timestamp}.json")
    analytics_filename = str(Path(OUTPUT_DIR) / f"{analytics_prefix}_{timestamp}.txt")
    
    save_results_json(results, results_filename)
    save_analytics_report(results, aggregate_metrics, analytics_filename)
    
    print()
    print("✅ Evaluation complete!")
    print()
    print(f"📁 Results saved to:")
    print(f"   - {results_filename}")
    print(f"   - {analytics_filename}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()


