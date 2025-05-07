#!/usr/bin/env python3

def generate_ccel_url(source_id):
    """Generate a CCEL URL from a source ID."""
    print(f"Input: {source_id}")
    
    try:
        # Split on colon to separate path from section
        parts = source_id.split(":")
        path_part = parts[0]  # ccel/a/anonymous/westminster3.xml
        
        # Split the path to extract components
        path_components = path_part.split("/")
        
        # We need at least 3 components: ccel, a, anonymous/work
        if len(path_components) >= 3:
            # Ignore the 'a' part (or whatever comes after ccel/)
            author = path_components[2]  # anonymous
            
            # Get work name, removing .xml if present
            work = path_components[3] if len(path_components) > 3 else ""
            work = work.split(".")[0]  # remove .xml
            
            # Get section part (before any "-" if present)
            section = ""
            if len(parts) > 1:
                section = parts[1].split("-")[0]  # i.xxi
            
            # Construct URL following the pattern
            url = f"https://ccel.org/ccel/{author}/{work}/{work}.{section}.html"
            print(f"Generated URL: {url}")
            return url
    except Exception as e:
        print(f"Error generating URL: {str(e)}")
    
    return None

# Test cases
test_cases = [
    "ccel/a/anonymous/westminster3.xml:i.xxi-p1",
    "ccel/a/aquinas/summa.xml:FP_Q6_A2-p5",
    "ccel/a/arminius/works1.xml:iii.vi.i-p6",
    "ccel/a/augustine/city.xml:xi.4-p3"
]

print("CCEL URL Generation Test\n")

for test_case in test_cases:
    generate_ccel_url(test_case)
    print("-" * 50) 