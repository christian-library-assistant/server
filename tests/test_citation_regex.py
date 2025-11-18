#!/usr/bin/env python3
"""Standalone test for citation number validation regex logic."""

import re


def validate_and_fix_citation_numbers(answer: str, num_sources: int) -> str:
    """
    Validate that all citation numbers in the answer match available sources.
    Caps any out-of-range numbers to the valid range.
    """
    if num_sources == 0:
        return answer

    fixed_answer = answer
    found_invalid = False

    # Collect all unique citation numbers used in the text
    all_citation_nums = set()

    # Find all citation patterns: [[N]](#source-N), [text](#source-N), #source-N
    superscript_pattern = r'\[\[(\d+)\]\]\(#source-(\d+)\)'
    markdown_pattern = r'\[([^\]]+)\]\(#source-(\d+)\)'
    bare_pattern = r'#source-(\d+)(?!\d)'

    for match in re.finditer(superscript_pattern, answer):
        all_citation_nums.add(int(match.group(2)))

    for match in re.finditer(markdown_pattern, answer):
        if not re.match(r'\[\d+\]', match.group(1)):
            all_citation_nums.add(int(match.group(2)))

    for match in re.finditer(bare_pattern, answer):
        start = match.start()
        if start == 0 or answer[start-1] not in ['(', '[']:
            all_citation_nums.add(int(match.group(1)))

    # Check if any citation numbers are out of range
    invalid_nums = [n for n in all_citation_nums if n > num_sources or n < 1]

    if invalid_nums:
        found_invalid = True
        print(f"⚠️  Found {len(invalid_nums)} invalid citation number(s): {sorted(invalid_nums)}")
        print(f"   Valid range is 1-{num_sources}")

    # Fix superscript citations: [[N]](#source-N)
    def fix_superscript(match):
        display_num = int(match.group(1))
        source_num = int(match.group(2))

        if source_num > num_sources:
            corrected_num = num_sources
            return f'[[{corrected_num}]](#source-{corrected_num})'
        elif source_num < 1:
            corrected_num = 1
            return f'[[{corrected_num}]](#source-{corrected_num})'

        return match.group(0)

    fixed_answer = re.sub(superscript_pattern, fix_superscript, fixed_answer)

    # Fix markdown-style citations: [text](#source-N)
    def fix_markdown(match):
        text = match.group(1)
        source_num = int(match.group(2))

        if source_num > num_sources:
            return f'[{text}](#source-{num_sources})'
        elif source_num < 1:
            return f'[{text}](#source-1)'

        return match.group(0)

    fixed_answer = re.sub(markdown_pattern, fix_markdown, fixed_answer)

    # Fix bare anchor references: #source-N
    def fix_bare(match):
        source_num = int(match.group(1))

        if source_num > num_sources:
            return f'#source-{num_sources}'
        elif source_num < 1:
            return f'#source-1'

        return match.group(0)

    fixed_answer = re.sub(bare_pattern, fix_bare, fixed_answer)

    if found_invalid:
        print(f"✓  Fixed invalid citation numbers. All citations now reference sources 1-{num_sources}")

    return fixed_answer


def test_citation_validation():
    """Test that invalid citation numbers are detected and fixed."""

    # Test case 1: User's actual example - citations [7], [6], [4], [1] with only 4 sources
    print("=" * 80)
    print("TEST 1: Real-world example (citations 7, 6, 4, 1 with only 4 sources)")
    print("=" * 80)

    answer_real = """
According to Augustine [[7]](#source-7), grace is essential [[6]](#source-6).
Thomas Aquinas notes [[4]](#source-4) that faith precedes understanding.
The early church fathers [[1]](#source-1) emphasized this truth.
"""

    num_sources = 4

    print(f"\nInput (with {num_sources} sources available):")
    print(answer_real)
    print("\n" + "-" * 80)

    fixed_answer = validate_and_fix_citation_numbers(answer_real, num_sources)

    print("\nFixed answer:")
    print(fixed_answer)
    print("\n" + "=" * 80)

    # Verify the fix
    assert "[[7]]" not in fixed_answer, "[[7]] should be fixed to [[4]]"
    assert "[[6]]" not in fixed_answer, "[[6]] should be fixed to [[4]]"
    assert "[[4]]" in fixed_answer, "[[4]] should remain"
    assert "[[1]]" in fixed_answer, "[[1]] should remain"
    assert "#source-7" not in fixed_answer, "#source-7 should be fixed"
    assert "#source-6" not in fixed_answer, "#source-6 should be fixed"
    assert "#source-4" in fixed_answer, "#source-4 should remain"
    assert "#source-1" in fixed_answer, "#source-1 should remain"

    print("\n✓ All assertions passed!")
    print("  - [[7]] → [[4]] (capped to max)")
    print("  - [[6]] → [[4]] (capped to max)")
    print("  - [[4]] → [[4]] (unchanged)")
    print("  - [[1]] → [[1]] (unchanged)")

    # Test case 2: Mixed citation formats
    print("\n" + "=" * 80)
    print("TEST 2: Mixed citation formats")
    print("=" * 80)

    answer_mixed = """
Augustine writes [[5]](#source-5) about grace.
As noted in [City of God](#source-3), the Trinity is central.
See also #source-8 for more details.
"""

    print(f"\nInput (with {num_sources} sources available):")
    print(answer_mixed)
    print("\n" + "-" * 80)

    fixed_mixed = validate_and_fix_citation_numbers(answer_mixed, num_sources)

    print("\nFixed answer:")
    print(fixed_mixed)
    print("\n" + "=" * 80)

    # Verify
    assert "[[5]]" not in fixed_mixed, "[[5]] should be fixed"
    assert "#source-8" not in fixed_mixed, "#source-8 should be fixed"
    assert "#source-3" in fixed_mixed, "#source-3 should remain"
    assert "[[4]]" in fixed_mixed, "[[5]] should become [[4]]"
    assert "#source-4" in fixed_mixed, "#source-8 should become #source-4"

    print("\n✓ All assertions passed!")
    print("  - [[5]] → [[4]] (capped to max)")
    print("  - #source-8 → #source-4 (capped to max)")
    print("  - [City of God](#source-3) → unchanged")


if __name__ == "__main__":
    test_citation_validation()
    print("\n" + "=" * 80)
    print("All tests passed successfully! 🎉")
    print("Citation validation is working correctly.")
    print("=" * 80)
