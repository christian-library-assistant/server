#!/usr/bin/env python3
"""
Direct Evaluation from CSV - Retrieval Testing V2

This script loads questions from a CSV file and goes straight to testing,
skipping the question generation step.

Usage:
    python evaluate_from_csv_v2.py                    # Use default CSV
    python evaluate_from_csv_v2.py questions.csv     # Use specific CSV
"""

import csv
import requests
import time
from pathlib import Path
from typing import Dict, List, Any
from utils_v2 import (
    calculate_retrieval_score,
    calculate_aggregate_metrics,
    save_results_json,
    save_analytics_report,
    format_timestamp,
    print_progress_bar
)
from config_v2 import (
    TEST_ENDPOINT,
    TOP_K,
    USE_AGENTIC,
    FILTER_WORKS,
    REQUEST_DELAY,
    VERBOSE,
    OUTPUT_DIR,
    ensure_directories
)


def load_questions_from_csv(csv_file: str) -> List[Dict[str, Any]]:
    """
    Load questions from CSV file.
    
    Expected CSV format:
    - query: The question text
    - gold_paragraph_ids: Expected paragraph ID(s)
    - paragraph_id: Paragraph ID (same as gold)
    - paragraph_text: The source paragraph text
    - question_type: Type of question (e.g., "specific")
    
    Args:
        csv_file: Path to CSV file
    
    Returns:
        List of question dictionaries
    """
    questions = []
    
    print(f"📖 Loading questions from {csv_file}")
    
    with open(csv_file, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Handle single or multiple gold paragraph IDs
            gold_ids = row['gold_paragraph_ids']
            if ',' in gold_ids:
                gold_paragraphs = [id.strip() for id in gold_ids.split(',')]
            else:
                gold_paragraphs = [gold_ids]
            
            question = {
                "query": row['query'],
                "gold_paragraphs": gold_paragraphs,
                "paragraph_text": row.get('paragraph_text', ''),
                "question_type": row.get('question_type', 'specific')
            }
            questions.append(question)
    
    print(f"✅ Loaded {len(questions)} questions")
    return questions


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
    
    # Debug: print first request payload
    if not hasattr(query_test_endpoint, '_first_call_logged'):
        print(f"\n🔍 Sample API Request Payload:")
        import json
        print(json.dumps(payload, indent=2))
        print()
        query_test_endpoint._first_call_logged = True
    
    try:
        response = requests.post(TEST_ENDPOINT, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")


def extract_returned_paragraphs(api_response: Dict[str, Any]) -> List[str]:
    """Extract paragraph IDs from API response."""
    if "results" not in api_response:
        return []
    
    results = api_response["results"]
    return [r.get("record_id", "") for r in results if r.get("record_id")]


def get_matched_ranks(gold_paragraphs: List[str], returned_paragraphs: List[str]) -> List[int]:
    """Get the ranks of matched gold paragraphs."""
    ranks = []
    for gold_id in gold_paragraphs:
        if gold_id in returned_paragraphs:
            rank = returned_paragraphs.index(gold_id) + 1
            ranks.append(rank)
    return ranks


def evaluate_single_query(question_item: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single query against the retrieval system."""
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


def evaluate_all_questions(questions: List[Dict[str, Any]], live_output_file: str = "davidtest.txt") -> List[Dict[str, Any]]:
    """Evaluate all questions against the retrieval system."""
    results = []
    total = len(questions)
    
    print(f"🔍 Evaluating {total} questions against retrieval system...")
    print(f"   Endpoint: {TEST_ENDPOINT}")
    print(f"   Top K: {TOP_K}")
    print(f"   Agentic: {USE_AGENTIC}")
    print(f"   Works Filter: {FILTER_WORKS}")
    print(f"   Live output: {live_output_file}")
    print()
    
    # Open live output file
    with open(live_output_file, 'w', encoding='utf-8') as live_file:
        # Write header
        live_file.write("=" * 80 + "\n")
        live_file.write(" LIVE RETRIEVAL TEST RESULTS ".center(80, "=") + "\n")
        live_file.write("=" * 80 + "\n\n")
        live_file.write(f"Total Questions: {total}\n")
        live_file.write(f"Endpoint: {TEST_ENDPOINT}\n")
        live_file.write(f"Top K: {TOP_K}\n")
        live_file.write(f"Agentic: {USE_AGENTIC}\n")
        live_file.write(f"Started: {format_timestamp()}\n\n")
        live_file.write("=" * 80 + "\n\n")
        live_file.flush()
        
        for i, question_item in enumerate(questions):
            if VERBOSE:
                print_progress_bar(i + 1, total, prefix='Progress')
            
            result = evaluate_single_query(question_item)
            results.append(result)
            
            # Write result to live file immediately
            live_file.write(f"[{i+1}/{total}] Query: {result['query'][:70]}...\n")
            live_file.write(f"  Score: {result['normalized_score']:.3f} ({result['label']})\n")
            live_file.write(f"  Matched: {result['matched_count']}/{result['total_gold']} gold paragraphs\n")
            
            if result['matched_count'] > 0:
                live_file.write(f"  Ranks: Top3={result['score_breakdown']['matched_top3']}, ")
                live_file.write(f"Top10={result['score_breakdown']['matched_top10']}, ")
                live_file.write(f"Beyond={result['score_breakdown']['matched_beyond10']}\n")
            
            if result['status'] == 'error':
                live_file.write(f"  ⚠️  ERROR: {result.get('error', 'Unknown error')}\n")
            
            live_file.write("\n")
            live_file.flush()  # Force write to disk
            
            # Rate limiting
            time.sleep(REQUEST_DELAY)
        
        # Write completion message
        live_file.write("\n" + "=" * 80 + "\n")
        live_file.write(" TESTING COMPLETE ".center(80, "=") + "\n")
        live_file.write("=" * 80 + "\n")
        live_file.write(f"Completed: {format_timestamp()}\n")
        live_file.write(f"Total tests: {total}\n")
        live_file.flush()
    
    print()
    print(f"✅ Live results written to: {live_output_file}")
    return results


def print_evaluation_summary(results: List[Dict[str, Any]], aggregate: Dict[str, Any]):
    """Print a summary of evaluation results to console."""
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


def main(csv_file: str = None):
    """Main execution function."""
    print("=" * 80)
    print(" DIRECT EVALUATION FROM CSV ".center(80, "="))
    print("=" * 80)
    print()
    
    # Ensure output directory exists
    ensure_directories()
    
    # Default CSV file
    if csv_file is None:
        csv_file = "questions.csv"
    
    print(f"📄 CSV File: {csv_file}")
    print()
    
    # Load questions from CSV
    try:
        questions = load_questions_from_csv(csv_file)
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file}")
        print()
        print("Expected CSV format:")
        print("  query,gold_paragraph_ids,paragraph_text,question_type")
        return
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return
    
    if not questions:
        print("❌ No questions found in CSV file")
        return
    
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
    
    # Live output file in output directory
    live_output = str(Path(OUTPUT_DIR) / "live_results.txt")
    
    # Evaluate all questions
    results = evaluate_all_questions(questions, live_output_file=live_output)
    
    # Calculate aggregate metrics
    aggregate_metrics = calculate_aggregate_metrics(results)
    
    # Print summary
    print_evaluation_summary(results, aggregate_metrics)
    
    # Save results to output directory
    timestamp = format_timestamp()
    csv_name = Path(csv_file).stem
    results_filename = str(Path(OUTPUT_DIR) / f"test_results_{csv_name}_{timestamp}.json")
    analytics_filename = str(Path(OUTPUT_DIR) / f"analytics_report_{csv_name}_{timestamp}.txt")
    
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
    import sys
    
    # Allow passing CSV filename as argument
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(csv_file)

