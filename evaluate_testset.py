#!/usr/bin/env python3
"""
Early Church Fathers Test Set Evaluation Script

This script evaluates the RAG system's performance by testing queries from the
early_church_fathers_testset.csv file against the /test endpoint.
"""

import csv
import requests
import time
from typing import Dict, List

# === CONFIGURATION ===
API_URL = "http://localhost:8080/test"
CSV_PATH = "early_church_fathers_testset.csv"
TOP_K = 10  # Check within top K results
USE_AGENTIC = False  # Set to True to test agentic RAG, False for regular RAG
FILTER_WORKS = ["anf01"]  # Filter to specific works (Ante-Nicene Fathers Vol 1)
REQUEST_DELAY = 0.25  # Delay between requests to avoid overloading

def evaluate() -> Dict:
    """
    Run evaluation on the test set.
    
    Returns:
        Dict containing evaluation metrics
    """
    total = 0
    correct = 0
    no_response = 0
    errors = []

    print("=" * 60)
    print(" Early Church Fathers Test Set Evaluation ".center(60, "="))
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  API URL: {API_URL}")
    print(f"  CSV Path: {CSV_PATH}")
    print(f"  Top K: {TOP_K}")
    print(f"  Agentic Mode: {USE_AGENTIC}")
    print(f"  Filter Works: {FILTER_WORKS}")
    print(f"\nStarting evaluation...\n")

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            query = row["query"]
            expected = row["expected_record_id"]
            subject = row.get("subject", "Unknown")
            total += 1

            try:
                # Send query to the test endpoint
                # The /test endpoint expects:
                # - query: the search text
                # - agentic: whether to use agentic mode (default false)
                # - works: filter to specific works
                # - top_k: number of results (default 5)
                # - return_fields: what fields to include in results
                payload = {
                    "query": query,
                    "agentic": USE_AGENTIC,
                    "works": FILTER_WORKS,
                    "top_k": TOP_K,
                    "return_fields": ["record_id", "knn_distance"]
                }

                response = requests.post(API_URL, json=payload, timeout=30)
                
                if response.status_code != 200:
                    print(f"[{total}] ❌ Server error ({response.status_code}) for: {query}")
                    no_response += 1
                    errors.append({
                        "id": total,
                        "query": query,
                        "subject": subject,
                        "error": f"HTTP {response.status_code}: {response.text[:100]}"
                    })
                    continue

                data = response.json()

                # Check if results exist
                if "results" not in data or not data["results"]:
                    print(f"[{total}] ⚠️  No results for: {query}")
                    no_response += 1
                    errors.append({
                        "id": total,
                        "query": query,
                        "subject": subject,
                        "error": "No results returned"
                    })
                    continue

                # Extract record IDs from results
                results = [r.get("record_id", "") for r in data["results"][:TOP_K]]

                # Check if expected record is in top K
                if expected in results:
                    correct += 1
                    rank = results.index(expected) + 1
                    print(f"[{total}] ✅ Correct (rank {rank}): {subject} - {query[:60]}...")
                else:
                    print(f"[{total}] ❌ Incorrect: {subject} - {query[:60]}...")
                    print(f"           Expected: {expected}")
                    print(f"           Got: {results[0] if results else 'None'}")

            except requests.exceptions.ConnectionError:
                print(f"[{total}] ⚠️  Connection error for: {query}")
                no_response += 1
                errors.append({
                    "id": total,
                    "query": query,
                    "subject": subject,
                    "error": "Connection error - is the server running?"
                })
            except requests.exceptions.Timeout:
                print(f"[{total}] ⚠️  Timeout for: {query}")
                no_response += 1
                errors.append({
                    "id": total,
                    "query": query,
                    "subject": subject,
                    "error": "Request timeout"
                })
            except Exception as e:
                print(f"[{total}] ⚠️  Request failed for: {query} ({e})")
                no_response += 1
                errors.append({
                    "id": total,
                    "query": query,
                    "subject": subject,
                    "error": str(e)
                })

            # Delay to avoid overloading the server
            time.sleep(REQUEST_DELAY)

    # Calculate metrics
    accuracy = correct / total if total > 0 else 0
    success_rate = (total - no_response) / total if total > 0 else 0

    # Print summary
    print("\n" + "=" * 60)
    print(" EVALUATION SUMMARY ".center(60, "="))
    print("=" * 60)
    print(f"\n📊 Results:")
    print(f"  Total queries tested:     {total}")
    print(f"  Correct matches (top-{TOP_K}): {correct}")
    print(f"  Incorrect matches:        {total - correct - no_response}")
    print(f"  No responses/errors:      {no_response}")
    print(f"\n📈 Metrics:")
    print(f"  Accuracy (top-{TOP_K}):        {accuracy:.2%}")
    print(f"  Success rate:             {success_rate:.2%}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} errors occurred during evaluation")
        print("\nFirst 5 errors:")
        for error in errors[:5]:
            print(f"  [{error['id']}] {error['subject']}: {error['error']}")

    print("\n" + "=" * 60)

    return {
        "total": total,
        "correct": correct,
        "incorrect": total - correct - no_response,
        "no_response": no_response,
        "accuracy": accuracy,
        "success_rate": success_rate,
        "errors": errors
    }

if __name__ == "__main__":
    try:
        results = evaluate()
    except FileNotFoundError:
        print(f"❌ Error: Could not find CSV file at {CSV_PATH}")
        print("   Make sure the file exists in the current directory.")
    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

