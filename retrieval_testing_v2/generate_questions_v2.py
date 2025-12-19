#!/usr/bin/env python3
"""
Question Generation Script for Retrieval Testing V2

This script uses LLM to generate realistic questions from filtered paragraphs.

Usage:
    python generate_questions_v2.py                    # Use default book
    python generate_questions_v2.py --book anf01       # Use specific book
    python generate_questions_v2.py --list             # List available books
"""

import json
import time
import argparse
from typing import List, Dict, Any
from pathlib import Path
import anthropic
from utils_v2 import load_paragraphs_csv, format_timestamp, print_progress_bar
import config_v2
from config_v2 import (
    ANTHROPIC_API_KEY,
    QUESTIONS_PER_PARAGRAPH,
    QUESTION_TYPES,
    QUESTION_GEN_TEMPERATURE,
    QUESTION_GEN_MAX_TOKENS,
    BATCH_SIZE,
    VERBOSE,
    validate_config,
    set_input_xml,
    get_available_books,
    CONFIG_DIR,
    OUTPUT_DIR
)


# === PROMPT TEMPLATES ===

SYSTEM_PROMPT = """You are an expert at creating realistic search queries that users would ask when researching Early Church Fathers and theological topics.

Your task is to generate natural, authentic questions that a real person would ask when trying to find information contained in a specific paragraph."""

SPECIFIC_QUESTION_PROMPT = """Based on the following paragraph from an Early Church Father text, generate {num_questions} specific question(s) that a user might ask to find this exact information.

Guidelines:
- The question should be natural and conversational, as if asked by a real person
- The question should be specific enough that this paragraph would be the ideal answer
- Avoid using exact phrases from the paragraph - rephrase naturally
- Questions should sound like genuine theological or historical inquiries
- Focus on the key concept, teaching, or event in the paragraph
- Keep questions concise (10-25 words)

Paragraph ID: {paragraph_id}

Paragraph text:
{paragraph_text}

Generate {num_questions} question(s) as a JSON array. Format:
{{"questions": ["question 1", "question 2", ...]}}

Only return the JSON, no other text."""


def generate_questions_anthropic(
    paragraph_text: str,
    paragraph_id: str,
    num_questions: int = 1
) -> List[str]:
    """
    Generate questions using Anthropic Claude API.
    
    Args:
        paragraph_text: The paragraph text
        paragraph_id: The paragraph ID
        num_questions: Number of questions to generate
    
    Returns:
        List of generated questions
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    user_prompt = SPECIFIC_QUESTION_PROMPT.format(
        num_questions=num_questions,
        paragraph_id=paragraph_id,
        paragraph_text=paragraph_text[:2000]  # Limit length
    )
    
    try:
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=QUESTION_GEN_MAX_TOKENS,
            temperature=QUESTION_GEN_TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        # Extract text from response
        response_text = response.content[0].text if response.content else ""
        
        # Parse JSON
        result = json.loads(response_text)
        questions = result.get("questions", [])
        
        return questions[:num_questions]
        
    except Exception as e:
        if VERBOSE:
            print(f"⚠️  Error generating questions with Claude: {e}")
        return []


def generate_questions_for_paragraph(paragraph: Dict[str, str]) -> List[str]:
    """
    Generate questions for a single paragraph using Claude.
    
    Args:
        paragraph: Paragraph dictionary with 'id' and 'text'
    
    Returns:
        List of generated questions
    """
    return generate_questions_anthropic(
        paragraph['text'],
        paragraph['id'],
        QUESTIONS_PER_PARAGRAPH
    )


def process_paragraphs_batch(paragraphs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Process multiple paragraphs to generate questions using Claude.
    
    Args:
        paragraphs: List of paragraph dictionaries
    
    Returns:
        List of question items with metadata
    """
    question_items = []
    
    print(f"🤖 Generating questions using Anthropic Claude API...")
    print(f"   Processing {len(paragraphs)} paragraphs...")
    print()
    
    for i, paragraph in enumerate(paragraphs):
        if VERBOSE:
            print_progress_bar(i + 1, len(paragraphs), prefix='Progress')
        
        questions = generate_questions_for_paragraph(paragraph)
        
        for question in questions:
            question_items.append({
                "query": question,
                "gold_paragraphs": [paragraph['id']],
                "paragraph_text": paragraph['text'],
                "question_type": "specific"
            })
        
        # Rate limiting - small delay between API calls
        time.sleep(0.5)
    
    print()
    print(f"✅ Generated {len(question_items)} questions")
    return question_items


def save_questions_json(question_items: List[Dict[str, Any]], output_file: str):
    """
    Save generated questions to JSON file.
    
    Args:
        question_items: List of question dictionaries
        output_file: Output filename
    """
    output = {
        "metadata": {
            "generated_at": format_timestamp(),
            "total_questions": len(question_items),
            "llm_provider": "anthropic",
            "questions_per_paragraph": QUESTIONS_PER_PARAGRAPH,
            "question_types": QUESTION_TYPES
        },
        "questions": question_items
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Questions saved to {output_file}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate test questions from filtered paragraphs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python generate_questions_v2.py                    # Use default book
    python generate_questions_v2.py --book anf01       # Use specific book
    python generate_questions_v2.py --list             # List available books
        """
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available books with prepared data"
    )
    parser.add_argument(
        "--book", "-b",
        help="Book name (must have run prepare_data_v2.py first)"
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    
    # Handle --list flag
    if args.list:
        print("\n📚 Books with prepared data (in output/):")
        output_dir = Path(OUTPUT_DIR)
        if output_dir.exists():
            csv_files = list(output_dir.glob("filtered_paragraphs_*.csv"))
            if csv_files:
                for f in csv_files:
                    book = f.stem.replace("filtered_paragraphs_", "")
                    print(f"   • {book}")
                print(f"\nUsage: python generate_questions_v2.py --book <name>")
            else:
                print("   (No prepared data found)")
                print("\nRun prepare_data_v2.py first to create paragraph data.")
        return
    
    # Set book if specified
    if args.book:
        set_input_xml(f"data/{args.book}.xml")
    
    # Get current config values
    book_name = config_v2.BOOK_NAME
    paragraphs_csv = config_v2.FILTERED_PARAGRAPHS_CSV
    questions_json = config_v2.QUESTIONS_JSON
    
    print("=" * 80)
    print(" QUESTION GENERATION FOR RETRIEVAL TESTING V2 ".center(80, "="))
    print("=" * 80)
    print()
    print(f"📚 Book: {book_name}")
    print()
    
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Load filtered paragraphs
    print(f"📖 Loading paragraphs from {paragraphs_csv}")
    try:
        paragraphs = load_paragraphs_csv(paragraphs_csv)
    except FileNotFoundError:
        print(f"❌ File not found: {paragraphs_csv}")
        print(f"   Run: python prepare_data_v2.py --book {book_name}")
        return
    
    if not paragraphs:
        print("❌ No paragraphs found in CSV file")
        return
    
    print(f"✅ Loaded {len(paragraphs)} paragraphs")
    print()
    
    # Generate questions
    question_items = process_paragraphs_batch(paragraphs)
    
    if not question_items:
        print("❌ No questions were generated")
        return
    
    # Save questions
    save_questions_json(question_items, questions_json)
    
    # Print summary
    print()
    print("=" * 80)
    print(" SUMMARY ".center(80, "="))
    print("=" * 80)
    print(f"Book:                        {book_name}")
    print(f"Paragraphs processed:        {len(paragraphs)}")
    print(f"Questions generated:         {len(question_items)}")
    print(f"LLM provider:                Anthropic Claude")
    print(f"Output file:                 {questions_json}")
    print()
    print("✅ Question generation complete!")
    print()
    print(f"Next step: python evaluate_retrieval_v2.py --book {book_name}")
    print("=" * 80)


if __name__ == "__main__":
    main()

