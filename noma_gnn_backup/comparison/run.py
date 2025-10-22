#!/usr/bin/env python
"""
Quick Run Script for Comparison

Usage:
    python run.py                          # Run on 500-user test scenario (skip Blossom)
    python run.py --full                   # Run on 500-user test scenario (include Blossom)
    python run.py --file YOUR_DATA.csv     # Run on custom dataset
    python run.py --help                   # Show all options
"""

import subprocess
import sys
import os
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Default paths (relative to this script's directory)
DEFAULT_H_VALUES = SCRIPT_DIR.parent / "test_scenario_500users.csv"
DEFAULT_CHECKPOINT = SCRIPT_DIR.parent / "checkpoints" / "best_model.pt"
DEFAULT_SCALER = SCRIPT_DIR.parent / "data" / "processed" / "feature_scaler.json"
DEFAULT_OUTPUT = SCRIPT_DIR / "comparison_results.csv"

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Quick comparison runner - simplified interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Quick test (no Blossom)
  python run.py --full             # Full test (with Blossom)
  python run.py --file data.csv    # Custom dataset
  python run.py --show             # Show last results
        """
    )
    
    parser.add_argument("--file", "-f", help="Custom h_values CSV file")
    parser.add_argument("--full", action="store_true", help="Include Blossom (slower)")
    parser.add_argument("--show", "-s", action="store_true", help="Show last results only")
    parser.add_argument("--iterations", "-i", type=int, default=3, help="Number of iterations (default: 3)")
    parser.add_argument("--output", "-o", help="Output CSV file")
    
    args = parser.parse_args()
    
    # Show results only
    if args.show:
        print("\nShowing last results...\n")
        show_script = SCRIPT_DIR / "show_results.py"
        subprocess.run([sys.executable, str(show_script)])
        return
    
    # Build command
    h_values = args.file if args.file else str(DEFAULT_H_VALUES)
    output = args.output if args.output else str(DEFAULT_OUTPUT)
    
    compare_script = SCRIPT_DIR / "compare_methods.py"
    
    cmd = [
        sys.executable,
        str(compare_script),
        "--h-values", h_values,
        "--ckpt", str(DEFAULT_CHECKPOINT),
        "--scaler", str(DEFAULT_SCALER),
        "--output", output,
        "--iterations", str(args.iterations)
    ]
    
    if args.full:
        cmd.append("--run-blossom")
        print("\n🔥 Running FULL comparison (including Blossom - will take ~45 seconds)")
    else:
        print("\n⚡ Running FAST comparison (skipping Blossom)")
    
    print(f"📊 Dataset: {h_values}")
    print(f"💾 Output: {output}")
    print(f"🔄 Iterations: {args.iterations}\n")
    
    # Run comparison
    subprocess.run(cmd)
    
    # Auto-show results if output is default
    if output == str(DEFAULT_OUTPUT):
        print("\n" + "="*90)
        print(" AUTO-DISPLAYING RESULTS")
        print("="*90)
        show_script = SCRIPT_DIR / "show_results.py"
        subprocess.run([sys.executable, str(show_script)])

if __name__ == "__main__":
    main()
