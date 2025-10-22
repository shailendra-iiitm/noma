"""
Verification Script: Check if papers have been corrected properly
Scans for false claims and verifies correct numbers are present
"""

import re
from pathlib import Path

# Define what should NOT be in papers (false claims)
FALSE_CLAIMS = {
    "50,000 scenarios": "Should be: 200 scenarios",
    "50000 scenarios": "Should be: 200 scenarios", 
    "N \\in \\{4, 6, 8, 10, 12\\}": "Should be: N = 500",
    "N ∈ {4,6,8,10,12}": "Should be: N = 500",
    "7,500 test": "Should be: 1 test scenario",
    "7500 test": "Should be: 1 test scenario",
    "70\\% / 15\\% / 15\\%": "Should remove: no train/val/test split",
    "35,000 scenarios": "Should remove: no split used",
    "20× speedup": "Should be: 52.9× speedup",
    "20× faster": "Should be: 52.9× faster",
    "95.8\\% of": "Should be: 96.5% of optimal",
    "N=12 users": "Check context: should be N=500 for actual results",
}

# Define what SHOULD be in papers (correct values)
CORRECT_VALUES = {
    "200 scenarios": "Training dataset size",
    "500 users": "User count per scenario",
    "100,000": "Total training samples (200 × 500)",
    "70.74": "GNN throughput in Gbps",
    "73.30": "Blossom throughput in Gbps",
    "96.5": "GNN percentage of optimal",
    "846": "GNN runtime in ms",
    "44,749": "Blossom runtime in ms (or 44749)",
    "52.9": "Speedup factor",
    "15.72": "GNN sum-rate in bits/s/Hz",
    "15.80": "Blossom sum-rate in bits/s/Hz",
}

# Files to check
FILES_TO_CHECK = [
    "NOMA_IEEE/simulation_setup.tex",
    "NOMA_IEEE/result_discussion.tex",
    "PROJECT_REPORT/chapters/14_experimental_setup.tex",
    "PROJECT_REPORT/chapters/15_results.tex",
]

def check_file(filepath):
    """Check a single file for false claims and correct values"""
    filepath = Path(filepath)
    
    if not filepath.exists():
        return {
            'file': str(filepath),
            'exists': False,
            'false_claims': [],
            'missing_correct': [],
            'status': 'FILE NOT FOUND'
        }
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Check for false claims
    found_false = []
    for claim, fix in FALSE_CLAIMS.items():
        # Escape regex special characters except those in LaTeX
        pattern = claim.replace('\\', '\\\\')
        if re.search(pattern, content, re.IGNORECASE):
            found_false.append(f"❌ Found: '{claim}' → {fix}")
    
    # Check for correct values
    missing_correct = []
    for value, description in CORRECT_VALUES.items():
        if value not in content:
            # Check if it might be formatted differently
            alt_value = value.replace(',', '')  # Try without comma
            if alt_value not in content:
                missing_correct.append(f"⚠️  Missing: '{value}' ({description})")
    
    # Determine status
    if found_false:
        status = '🔴 NEEDS FIXING'
    elif missing_correct:
        status = '🟡 CHECK NEEDED'
    else:
        status = '✅ LOOKS GOOD'
    
    return {
        'file': str(filepath),
        'exists': True,
        'false_claims': found_false,
        'missing_correct': missing_correct,
        'status': status
    }

def main():
    print("="*80)
    print(" PAPER VERIFICATION - Checking for False Claims and Correct Values")
    print("="*80)
    
    results = []
    for filepath in FILES_TO_CHECK:
        result = check_file(filepath)
        results.append(result)
    
    # Print results
    for result in results:
        print(f"\n{'='*80}")
        print(f"📄 File: {result['file']}")
        print(f"Status: {result['status']}")
        print("="*80)
        
        if not result['exists']:
            print("❌ FILE NOT FOUND - Check path or create file")
            continue
        
        if result['false_claims']:
            print("\n🚨 FALSE CLAIMS FOUND (must fix):")
            for claim in result['false_claims']:
                print(f"  {claim}")
        
        if result['missing_correct']:
            print("\n⚠️  POTENTIALLY MISSING VALUES:")
            for missing in result['missing_correct']:
                print(f"  {missing}")
        
        if not result['false_claims'] and not result['missing_correct']:
            print("\n✅ No false claims detected")
            print("✅ All expected values appear to be present")
    
    # Summary
    print("\n" + "="*80)
    print(" SUMMARY")
    print("="*80)
    
    needs_fix = [r for r in results if r['status'] == '🔴 NEEDS FIXING']
    needs_check = [r for r in results if r['status'] == '🟡 CHECK NEEDED']
    looks_good = [r for r in results if r['status'] == '✅ LOOKS GOOD']
    not_found = [r for r in results if not r['exists']]
    
    print(f"\n🔴 Needs Fixing: {len(needs_fix)}")
    print(f"🟡 Needs Check: {len(needs_check)}")
    print(f"✅ Looks Good: {len(looks_good)}")
    print(f"❌ Not Found: {len(not_found)}")
    
    if needs_fix:
        print("\n⚠️  Files requiring immediate attention:")
        for r in needs_fix:
            print(f"  • {r['file']}")
    
    if not_found:
        print("\n❌ Files not found (check paths):")
        for r in not_found:
            print(f"  • {r['file']}")
    
    if not needs_fix and not not_found:
        print("\n🎉 All checked files appear to be corrected!")
        print("   (Some missing values are OK if context doesn't require them)")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
