#!/usr/bin/env python3
"""
NOMA Simulation Results Manager
Helps view and compare results from different simulation runs
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import glob

def list_simulation_runs():
    """List all available simulation runs"""
    if not os.path.exists("simulation_results"):
        print("No simulation results found. Run clustering.py first.")
        return []
    
    runs = []
    for folder in os.listdir("simulation_results"):
        if os.path.isdir(f"simulation_results/{folder}"):
            try:
                # Parse timestamp
                timestamp = datetime.strptime(folder, "%Y%m%d_%H%M%S")
                runs.append((folder, timestamp))
            except ValueError:
                continue
    
    # Sort by timestamp (newest first)
    runs.sort(key=lambda x: x[1], reverse=True)
    
    print("Available Simulation Runs:")
    print("=" * 50)
    for i, (folder, timestamp) in enumerate(runs, 1):
        readable_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{i:2d}. {folder} ({readable_time})")
    
    return [folder for folder, _ in runs]

def view_run_summary(run_folder):
    """Display summary for a specific run"""
    summary_path = f"simulation_results/{run_folder}/clustering_summary.csv"
    
    if not os.path.exists(summary_path):
        print(f"Summary file not found for run {run_folder}")
        return
    
    print(f"\nSummary for Run: {run_folder}")
    print("=" * 60)
    
    df = pd.read_csv(summary_path)
    
    for _, row in df.iterrows():
        print(f"\n{row['Method'].upper()} CLUSTERING:")
        print(f"  - Total Throughput: {row['Total_Throughput_Mbps']:.2f} Mbps")
        print(f"  - NOMA Pairs: {row['NOMA_Pairs']}")
        print(f"  - OMA Users: {row['OMA_Users']}")
        print(f"  - NOMA Coverage: {row['NOMA_Percentage']:.1f}%")
        print(f"  - Avg NOMA Rate: {row['Avg_NOMA_Rate_bitsHz']:.2f} bits/Hz")
        print(f"  - Avg OMA Rate: {row['Avg_OMA_Rate_bitsHz']:.2f} bits/Hz")

def compare_runs(run_folders):
    """Compare multiple simulation runs"""
    if len(run_folders) < 2:
        print("Need at least 2 runs to compare")
        return
    
    comparison_data = []
    
    for run_folder in run_folders:
        summary_path = f"simulation_results/{run_folder}/clustering_summary.csv"
        if os.path.exists(summary_path):
            df = pd.read_csv(summary_path)
            for _, row in df.iterrows():
                comparison_data.append({
                    'Run': run_folder,
                    'Method': row['Method'],
                    'Throughput': row['Total_Throughput_Mbps'],
                    'NOMA_Coverage': row['NOMA_Percentage']
                })
    
    if not comparison_data:
        print("No valid data found for comparison")
        return
    
    # Create comparison plots
    comp_df = pd.DataFrame(comparison_data)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Throughput comparison
    for method in comp_df['Method'].unique():
        method_data = comp_df[comp_df['Method'] == method]
        ax1.plot(method_data['Run'], method_data['Throughput'], 
                marker='o', label=method, linewidth=2)
    
    ax1.set_xlabel('Simulation Run')
    ax1.set_ylabel('Total Throughput (Mbps)')
    ax1.set_title('Throughput Comparison Across Runs')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
    
    # NOMA Coverage comparison
    for method in comp_df['Method'].unique():
        method_data = comp_df[comp_df['Method'] == method]
        ax2.plot(method_data['Run'], method_data['NOMA_Coverage'], 
                marker='s', label=method, linewidth=2)
    
    ax2.set_xlabel('Simulation Run')
    ax2.set_ylabel('NOMA Coverage (%)')
    ax2.set_title('NOMA Coverage Comparison Across Runs')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig('simulation_results/runs_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"Comparison plot saved as 'simulation_results/runs_comparison.png'")

def cleanup_old_runs(keep_latest=5):
    """Clean up old simulation runs, keeping only the latest N runs"""
    runs = list_simulation_runs()
    
    if len(runs) <= keep_latest:
        print(f"Only {len(runs)} runs found, no cleanup needed")
        return
    
    runs_to_delete = runs[keep_latest:]
    
    print(f"Will delete {len(runs_to_delete)} old runs (keeping latest {keep_latest}):")
    for run in runs_to_delete:
        print(f"  - {run}")
    
    confirm = input("\nProceed with deletion? (y/N): ").lower()
    if confirm == 'y':
        import shutil
        for run in runs_to_delete:
            shutil.rmtree(f"simulation_results/{run}")
            print(f"Deleted {run}")
        print("Cleanup completed!")
    else:
        print("Cleanup cancelled")

def main():
    """Main interactive menu"""
    while True:
        print("\n" + "=" * 50)
        print("NOMA Simulation Results Manager")
        print("=" * 50)
        print("1. List all simulation runs")
        print("2. View run summary")
        print("3. Compare multiple runs")
        print("4. Cleanup old runs")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            list_simulation_runs()
        
        elif choice == '2':
            runs = list_simulation_runs()
            if not runs:
                continue
            
            try:
                idx = int(input(f"\nEnter run number (1-{len(runs)}): ")) - 1
                if 0 <= idx < len(runs):
                    view_run_summary(runs[idx])
                else:
                    print("Invalid run number")
            except ValueError:
                print("Invalid input")
        
        elif choice == '3':
            runs = list_simulation_runs()
            if len(runs) < 2:
                print("Need at least 2 runs for comparison")
                continue
            
            print("\nSelect runs to compare (enter numbers separated by spaces):")
            try:
                indices = [int(x) - 1 for x in input().split()]
                selected_runs = [runs[i] for i in indices if 0 <= i < len(runs)]
                if len(selected_runs) >= 2:
                    compare_runs(selected_runs)
                else:
                    print("Invalid selection")
            except (ValueError, IndexError):
                print("Invalid input")
        
        elif choice == '4':
            try:
                keep = int(input("How many latest runs to keep? (default: 5): ") or "5")
                cleanup_old_runs(keep)
            except ValueError:
                print("Invalid input")
        
        elif choice == '5':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
