#!/usr/bin/env python3
"""
Data Preparation Script for Retrieval Testing V2

This script processes the XML file and filters paragraphs to create
a clean dataset for question generation.

Usage:
    python prepare_data_v2.py                    # Use default XML (anf01.xml)
    python prepare_data_v2.py path/to/book.xml   # Use specific XML file
    python prepare_data_v2.py --list             # List available books
"""

import csv
import sys
import argparse
import xml.etree.ElementTree as ET
from typing import List, Dict
from pathlib import Path
import re
import config_v2
from config_v2 import (
    MIN_PARAGRAPH_LENGTH,
    MAX_PARAGRAPH_LENGTH,
    EXCLUDE_KEYWORDS,
    MAX_PARAGRAPHS,
    VERBOSE,
    CONFIG_DIR,
    get_available_books,
    set_input_xml,
    ensure_directories
)


def extract_text_from_element(element) -> str:
    """
    Extract all text content from an XML element, including nested elements.
    
    Args:
        element: XML element
    
    Returns:
        Concatenated text content
    """
    if element.text:
        text = element.text
    else:
        text = ""
    
    for child in element:
        text += extract_text_from_element(child)
        if child.tail:
            text += child.tail
    
    return text


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Raw text
    
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def should_exclude_paragraph(text: str, paragraph_id: str) -> bool:
    """
    Determine if a paragraph should be excluded based on filters.
    
    Args:
        text: Paragraph text
        paragraph_id: Paragraph ID
    
    Returns:
        True if paragraph should be excluded, False otherwise
    """
    text_lower = text.lower()
    
    # Check length
    if len(text) < MIN_PARAGRAPH_LENGTH or len(text) > MAX_PARAGRAPH_LENGTH:
        return True
    
    # Check for excluded keywords
    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in text_lower:
            return True
    
    # Exclude if mostly numbers (likely index or reference)
    digit_ratio = sum(c.isdigit() for c in text) / len(text) if text else 0
    if digit_ratio > 0.5:
        return True
    
    return False


def extract_paragraph_id(element, file_prefix: str = "ccel/s/schaff/anf01.xml") -> str:
    """
    Extract or generate a paragraph ID from an XML element.
    
    Args:
        element: XML element
        file_prefix: Prefix for the record ID
    
    Returns:
        Paragraph ID string
    """
    # Try to get ID from common attributes
    para_id = element.get('id') or element.get('n') or element.get('osisID')
    
    if para_id:
        return f"{file_prefix}:{para_id}"
    else:
        # Generate a simple ID based on position
        return f"{file_prefix}:para-{id(element)}"


def parse_xml_paragraphs(xml_file: str) -> List[Dict[str, str]]:
    """
    Parse XML file and extract paragraph elements.
    
    Args:
        xml_file: Path to XML file
    
    Returns:
        List of paragraph dictionaries with 'id' and 'text' keys
    """
    print(f"📖 Parsing XML file: {xml_file}")
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Error parsing XML: {e}")
        return []
    
    paragraphs = []
    
    # Find all paragraph-like elements
    # Common XML tags for paragraphs: p, div1.p, div2.p, etc.
    for elem in root.iter():
        # Check if element is a paragraph type
        if elem.tag.endswith('p') or 'p' in elem.tag.lower():
            text = extract_text_from_element(elem)
            text = clean_text(text)
            
            if text:  # Only process if there's actual text
                para_id = extract_paragraph_id(elem)
                paragraphs.append({
                    'id': para_id,
                    'text': text
                })
    
    print(f"✅ Extracted {len(paragraphs)} paragraph elements")
    return paragraphs


def filter_paragraphs(paragraphs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter paragraphs based on criteria.
    
    Args:
        paragraphs: List of paragraph dictionaries
    
    Returns:
        Filtered list of paragraphs
    """
    print(f"🔍 Filtering paragraphs...")
    
    filtered = []
    excluded_count = 0
    
    for para in paragraphs:
        if should_exclude_paragraph(para['text'], para['id']):
            excluded_count += 1
        else:
            filtered.append(para)
        
        # Apply max paragraphs limit if set
        if MAX_PARAGRAPHS and len(filtered) >= MAX_PARAGRAPHS:
            break
    
    print(f"✅ Filtered to {len(filtered)} paragraphs (excluded {excluded_count})")
    return filtered


def save_paragraphs_csv(paragraphs: List[Dict[str, str]], output_file: str):
    """
    Save filtered paragraphs to CSV file.
    
    Args:
        paragraphs: List of paragraph dictionaries
        output_file: Output CSV filename
    """
    print(f"💾 Saving paragraphs to {output_file}")
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['id', 'text', 'length']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for para in paragraphs:
            writer.writerow({
                'id': para['id'],
                'text': para['text'],
                'length': len(para['text'])
            })
    
    print(f"✅ Saved {len(paragraphs)} paragraphs to CSV")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Prepare data from XML books for retrieval testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python prepare_data_v2.py                         # Use default XML (anf01.xml)
    python prepare_data_v2.py data/anf02.xml          # Use specific XML file
    python prepare_data_v2.py --list                  # List available books
    python prepare_data_v2.py --book anf01            # Use book by name from data/
        """
    )
    parser.add_argument(
        "xml_file", 
        nargs="?", 
        help="Path to XML file to process"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available XML books in data/ directory"
    )
    parser.add_argument(
        "--book", "-b",
        help="Book name (without .xml extension) from data/ directory"
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    
    # Handle --list flag
    if args.list:
        print("\n📚 Available books in data/ directory:")
        books = get_available_books()
        if books:
            for book in books:
                print(f"   • {book}")
            print(f"\nUsage: python prepare_data_v2.py --book {books[0]}")
        else:
            print("   (No XML files found)")
            print(f"\nPlace XML files in: {CONFIG_DIR / 'data'}")
        return
    
    # Set input XML file
    if args.xml_file:
        set_input_xml(args.xml_file)
    elif args.book:
        set_input_xml(f"data/{args.book}.xml")
    
    # Get current config values
    xml_file = config_v2.INPUT_XML_FILE
    output_csv = config_v2.FILTERED_PARAGRAPHS_CSV
    book_name = config_v2.BOOK_NAME
    
    print("=" * 80)
    print(" DATA PREPARATION FOR RETRIEVAL TESTING V2 ".center(80, "="))
    print("=" * 80)
    print()
    print(f"📚 Book: {book_name}")
    print(f"📄 Input: {xml_file}")
    print()
    
    # Check if file exists
    if not Path(xml_file).exists():
        print(f"❌ XML file not found: {xml_file}")
        print()
        print("💡 Available books:")
        books = get_available_books()
        if books:
            for book in books:
                print(f"   • {book}")
        else:
            print(f"   Place XML files in: {CONFIG_DIR / 'data'}")
        return
    
    # Ensure output directory exists
    ensure_directories()
    
    # Parse XML
    paragraphs = parse_xml_paragraphs(xml_file)
    
    if not paragraphs:
        print("❌ No paragraphs found in XML file")
        return
    
    # Filter paragraphs
    filtered = filter_paragraphs(paragraphs)
    
    if not filtered:
        print("❌ No paragraphs passed filtering criteria")
        return
    
    # Save to CSV
    save_paragraphs_csv(filtered, output_csv)
    
    # Print summary
    print()
    print("=" * 80)
    print(" SUMMARY ".center(80, "="))
    print("=" * 80)
    print(f"Book:                        {book_name}")
    print(f"Total paragraphs extracted:  {len(paragraphs)}")
    print(f"Paragraphs after filtering:  {len(filtered)}")
    print(f"Output file:                 {output_csv}")
    print()
    print("✅ Data preparation complete!")
    print()
    print(f"Next step: python generate_questions_v2.py --book {book_name}")
    print("=" * 80)


if __name__ == "__main__":
    main()


