"""
Utility functions for Retrieval Testing V2

Contains helper functions for scoring, analytics, and data processing.
"""

import json
import csv
from typing import Dict, List, Tuple, Any
from datetime import datetime
from config_v2 import (
    SCORE_RANK_1_3,
    SCORE_RANK_4_10,
    SCORE_RANK_BEYOND_10,
    PENALTY_MISSING,
    SCORE_LABELS
)


def calculate_retrieval_score(
    gold_paragraphs: List[str],
    returned_paragraphs: List[str]
) -> Dict[str, Any]:
    """
    Calculate the retrieval score based on the scoring rubric.
    
    Args:
        gold_paragraphs: List of expected paragraph IDs
        returned_paragraphs: List of returned paragraph IDs in ranked order
    
    Returns:
        Dictionary containing score breakdown and metrics
    """
    score_breakdown = {
        "matched_top3": 0,
        "matched_top10": 0,
        "matched_beyond10": 0,
        "missing_gold": 0
    }
    
    raw_score = 0
    matched_ids = set()
    
    # Check each gold paragraph
    for gold_id in gold_paragraphs:
        if gold_id in returned_paragraphs:
            rank = returned_paragraphs.index(gold_id) + 1  # 1-indexed rank
            matched_ids.add(gold_id)
            
            if rank <= 3:
                score_breakdown["matched_top3"] += 1
                raw_score += SCORE_RANK_1_3
            elif rank <= 10:
                score_breakdown["matched_top10"] += 1
                raw_score += SCORE_RANK_4_10
            else:
                score_breakdown["matched_beyond10"] += 1
                raw_score += SCORE_RANK_BEYOND_10
        else:
            score_breakdown["missing_gold"] += 1
            raw_score += PENALTY_MISSING
    
    # Calculate max possible score (all gold paragraphs in top 3)
    max_possible = len(gold_paragraphs) * SCORE_RANK_1_3
    
    # Normalize score to 0-1 range
    # Handle case where raw_score is negative
    if max_possible == 0:
        normalized_score = 0.0
    else:
        normalized_score = max(0, raw_score / max_possible)
    
    # Get label based on normalized score
    label = get_score_label(normalized_score)
    
    return {
        "score_breakdown": score_breakdown,
        "raw_score": raw_score,
        "max_possible": max_possible,
        "normalized_score": round(normalized_score, 3),
        "label": label,
        "matched_count": len(matched_ids),
        "total_gold": len(gold_paragraphs)
    }


def get_score_label(normalized_score: float) -> str:
    """
    Get the label for a normalized score.
    
    Args:
        normalized_score: Score between 0 and 1
    
    Returns:
        Label string (e.g., "Excellent", "Good", etc.)
    """
    for (min_score, max_score), label in SCORE_LABELS.items():
        if min_score <= normalized_score <= max_score:
            return label
    return "Unknown"


def calculate_aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregate metrics across all test results.
    
    Args:
        results: List of test result dictionaries
    
    Returns:
        Dictionary containing aggregate metrics
    """
    if not results:
        return {
            "total_queries": 0,
            "avg_normalized_score": 0.0,
            "avg_raw_score": 0.0,
            "avg_matched_count": 0.0,
            "perfect_matches": 0,
            "no_matches": 0,
            "label_distribution": {}
        }
    
    total_queries = len(results)
    total_normalized = sum(r["normalized_score"] for r in results)
    total_raw = sum(r["raw_score"] for r in results)
    total_matched = sum(r["matched_count"] for r in results)
    
    perfect_matches = sum(1 for r in results if r["matched_count"] == r["total_gold"])
    no_matches = sum(1 for r in results if r["matched_count"] == 0)
    
    # Label distribution
    label_counts = {}
    for result in results:
        label = result["label"]
        label_counts[label] = label_counts.get(label, 0) + 1
    
    # Average rank for matched gold paragraphs
    total_ranks = []
    for result in results:
        if "matched_ranks" in result:
            total_ranks.extend(result["matched_ranks"])
    
    avg_matched_rank = sum(total_ranks) / len(total_ranks) if total_ranks else 0
    
    return {
        "total_queries": total_queries,
        "avg_normalized_score": round(total_normalized / total_queries, 3),
        "avg_raw_score": round(total_raw / total_queries, 2),
        "avg_matched_count": round(total_matched / total_queries, 2),
        "avg_matched_rank": round(avg_matched_rank, 2),
        "perfect_matches": perfect_matches,
        "perfect_match_rate": round(perfect_matches / total_queries, 3),
        "no_matches": no_matches,
        "no_match_rate": round(no_matches / total_queries, 3),
        "label_distribution": label_counts
    }


def save_results_json(results: List[Dict[str, Any]], filename: str):
    """
    Save results to a JSON file.
    
    Args:
        results: List of result dictionaries
        filename: Output filename
    """
    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(results)
        },
        "results": results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Results saved to {filename}")


def save_analytics_report(
    results: List[Dict[str, Any]],
    aggregate_metrics: Dict[str, Any],
    filename: str
):
    """
    Save a human-readable analytics report.
    
    Args:
        results: List of result dictionaries
        aggregate_metrics: Aggregate metrics dictionary
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(" RETRIEVAL EVALUATION ANALYTICS REPORT V2 ".center(80, "=") + "\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("=" * 80 + "\n")git 
        f.write("AGGREGATE METRICS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total Queries Tested:     {aggregate_metrics['total_queries']}\n")
        f.write(f"Average Normalized Score: {aggregate_metrics['avg_normalized_score']:.3f}\n")
        f.write(f"Average Raw Score:        {aggregate_metrics['avg_raw_score']:.2f}\n")
        f.write(f"Average Matched Count:    {aggregate_metrics['avg_matched_count']:.2f}\n")
        f.write(f"Average Matched Rank:     {aggregate_metrics['avg_matched_rank']:.2f}\n\n")
        
        f.write(f"Perfect Matches:          {aggregate_metrics['perfect_matches']} ")
        f.write(f"({aggregate_metrics['perfect_match_rate']:.1%})\n")
        f.write(f"No Matches:               {aggregate_metrics['no_matches']} ")
        f.write(f"({aggregate_metrics['no_match_rate']:.1%})\n\n")
        
        f.write("Label Distribution:\n")
        for label, count in sorted(
            aggregate_metrics['label_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            percentage = count / aggregate_metrics['total_queries'] * 100
            f.write(f"  {label:20s}: {count:3d} ({percentage:.1f}%)\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("DETAILED RESULTS\n")
        f.write("=" * 80 + "\n\n")
        
        # Sort results by score (best first)
        sorted_results = sorted(results, key=lambda x: x["normalized_score"], reverse=True)
        
        for i, result in enumerate(sorted_results, 1):
            f.write(f"[{i}] Query: {result['query'][:70]}...\n")
            f.write(f"    Score: {result['normalized_score']:.3f} ({result['label']})\n")
            f.write(f"    Matched: {result['matched_count']}/{result['total_gold']} gold paragraphs\n")
            
            if result['matched_count'] > 0:
                f.write(f"    Top 3: {result['score_breakdown']['matched_top3']}, ")
                f.write(f"Top 10: {result['score_breakdown']['matched_top10']}, ")
                f.write(f"Beyond 10: {result['score_breakdown']['matched_beyond10']}\n")
            
            if result['score_breakdown']['missing_gold'] > 0:
                f.write(f"    Missing: {result['score_breakdown']['missing_gold']} gold paragraphs\n")
            
            f.write("\n")
    
    print(f"✅ Analytics report saved to {filename}")


def load_questions_json(filename: str) -> List[Dict[str, Any]]:
    """
    Load questions from JSON file.
    
    Args:
        filename: Input filename
    
    Returns:
        List of question dictionaries
    """
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and "questions" in data:
        return data["questions"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Invalid questions file format")


def load_paragraphs_csv(filename: str) -> List[Dict[str, str]]:
    """
    Load filtered paragraphs from CSV file.
    
    Args:
        filename: Input filename
    
    Returns:
        List of paragraph dictionaries
    """
    paragraphs = []
    with open(filename, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            paragraphs.append(row)
    
    return paragraphs


def format_timestamp() -> str:
    """
    Get a formatted timestamp for filenames.
    
    Returns:
        Timestamp string in format YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def print_progress_bar(iteration: int, total: int, prefix: str = '', length: int = 50):
    """
    Print a progress bar to console.
    
    Args:
        iteration: Current iteration
        total: Total iterations
        prefix: Prefix string
        length: Character length of bar
    """
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% ({iteration}/{total})', end='\r')
    if iteration == total:
        print()


