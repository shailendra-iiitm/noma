#!/usr/bin/env python
"""
NOMA-GNN Main Runner - Quick Access to All Tools

Usage:
    python run.py train              # Train the model
    python run.py compare            # Run comparison (fast)
    python run.py compare --full     # Run comparison (with Blossom)
    python run.py infer FILE.csv     # Run inference on dataset
    python run.py prepare            # Prepare training data
    python run.py --help             # Show help
"""

import os
import subprocess
import sys
from pathlib import Path

def print_menu():
    print("\n" + "="*80)
    print(" NOMA-GNN TOOLKIT - Quick Runner")
    print("="*80)
    print("\nAvailable commands:")
    print("  train              - Train the GNN model")
    print("  compare            - Run method comparison (fast - no Blossom)")
    print("  compare --full     - Run method comparison (with Blossom)")
    print("  infer FILE.csv     - Run inference on a dataset")
    print("  prepare            - Prepare/verify training data")
    print("  show               - Show last comparison results")
    print("\nExamples:")
    print("  python run.py compare")
    print("  python run.py compare --full")
    print("  python run.py infer test_scenario_500users.csv")
    print("  python run.py show")
    print("="*80 + "\n")

def main():
    if len(sys.argv) < 2:
        print_menu()
        return
    
    command = sys.argv[1].lower()
    
    if command == "train":
        print("\n🚀 Starting training...")
        subprocess.run([
            sys.executable,
            "training/train.py"
        ])
    
    elif command == "compare":
        print("\n📊 Running comparison...")
        # Pass remaining args to comparison runner
        args = sys.argv[2:] if len(sys.argv) > 2 else []
        # Use absolute path to comparison/run.py
        comparison_script = Path(__file__).parent / "comparison" / "run.py"
        subprocess.run([sys.executable, str(comparison_script)] + args)
    
    elif command == "infer":
        if len(sys.argv) < 3:
            print("❌ Error: Please specify input file")
            print("Usage: python run.py infer FILE.csv")
            return
        
        input_file = sys.argv[2]
        print(f"\n🔮 Running inference on {input_file}...")
        
        # Set PYTHONPATH to include the project root
        env = os.environ.copy()
        project_root = str(Path(__file__).parent)
        env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')
        
        subprocess.run([
            sys.executable,
            "inference/infer_pairing.py",
            "--h_values_csv", input_file,
            "--ckpt", "checkpoints/best_model.pt",
            "--scaler", "data/processed/feature_scaler.json"
        ], env=env, cwd=project_root)
    
    elif command == "prepare":
        print("\n📦 Preparing training data...")
        subprocess.run([
            sys.executable,
            "scripts/prepare_data.py"
        ])
    
    elif command == "show":
        print("\n📈 Showing last comparison results...")
        # Change to comparison directory first
        original_dir = Path.cwd()
        comparison_dir = Path(__file__).parent / "comparison"
        subprocess.run([sys.executable, "show_results.py"], cwd=str(comparison_dir))
    
    elif command in ["help", "-h", "--help"]:
        print_menu()
    
    else:
        print(f"❌ Unknown command: {command}")
        print_menu()

if __name__ == "__main__":
    main()
