#!/usr/bin/env python3
"""Test citation number validation and fixing."""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.agents.theological_agent import TheologicalAgent


def test_citation_validation():
    """Test that invalid citation numbers are detected and fixed."""

    # Create agent instance (we only need the validation method)
    agent = TheologicalAgent()

    # Test case 1: Citations with numbers beyond available sources
    answer_with_invalid = """
According to Augustine [[7]](#source-7), grace is essential [[6]](#source-6).
Thomas Aquinas notes [[4]](#source-4) that faith precedes understanding.
The early church fathers [[1]](#source-1) emphasized this truth.
"""

    num_sources = 4

    print("=" * 80)
    print("TEST: Citation Validation")
    print("=" * 80)
    print(f"\nInput answer (with {num_sources} sources available):")
    print(answer_with_invalid)
    print("\n" + "-" * 80)

    # Fix the citations
    fixed_answer = agent._validate_and_fix_citation_numbers(answer_with_invalid, num_sources)

    print("\nFixed answer:")
    print(fixed_answer)
    print("\n" + "=" * 80)

    # Verify the fix
    assert "[[7]]" not in fixed_answer, "[[7]] should be fixed"
    assert "[[6]]" not in fixed_answer, "[[6]] should be fixed"
    assert "[[4]]" in fixed_answer, "[[4]] should remain"
    assert "[[1]]" in fixed_answer, "[[1]] should remain"
    assert "#source-7" not in fixed_answer, "#source-7 should be fixed"
    assert "#source-6" not in fixed_answer, "#source-6 should be fixed"

    print("\n✓ All assertions passed!")
    print("  - Invalid citations [[7]] and [[6]] were fixed")
    print("  - Valid citations [[1]] and [[4]] were preserved")

    # Test case 2: Mixed citation formats
    answer_mixed = """
Augustine writes [[5]](#source-5) about grace.
As noted in [City of God](#source-3), the Trinity is central.
See also #source-8 for more details.
"""

    print("\n" + "=" * 80)
    print("TEST: Mixed Citation Formats")
    print("=" * 80)
    print(f"\nInput answer (with {num_sources} sources available):")
    print(answer_mixed)
    print("\n" + "-" * 80)

    fixed_mixed = agent._validate_and_fix_citation_numbers(answer_mixed, num_sources)

    print("\nFixed answer:")
    print(fixed_mixed)
    print("\n" + "=" * 80)

    # Verify
    assert "[[5]]" not in fixed_mixed, "[[5]] should be fixed"
    assert "#source-8" not in fixed_mixed, "#source-8 should be fixed"
    assert "#source-3" in fixed_mixed, "#source-3 should remain"

    print("\n✓ All assertions passed!")
    print("  - Superscript [[5]] was capped to [[4]]")
    print("  - Bare anchor #source-8 was capped to #source-4")
    print("  - Valid markdown citation #source-3 was preserved")


if __name__ == "__main__":
    test_citation_validation()
    print("\n" + "=" * 80)
    print("All tests passed successfully! 🎉")
    print("=" * 80)
