#!/usr/bin/env python3
"""
NOMA Simulation Results Manager - Simple Version
Helps view and compare results from different simulation runs
"""

import os
from datetime import datetime

def list_simulation_runs():
    """List all available simulation runs"""
    if not os.path.exists("simulation_results"):
        print("No simulation results found. Run clustering.py first.")
        return []
    
    runs = []
    for folder in os.listdir("simulation_results"):
        folder_path = f"simulation_results/{folder}"
        if os.path.isdir(folder_path):
            try:
                # Parse timestamp
                timestamp = datetime.strptime(folder, "%Y%m%d_%H%M%S")
                runs.append((folder, timestamp))
            except ValueError:
                # Skip folders that don't match timestamp format
                continue
    
    if not runs:
        print("No valid simulation runs found.")
        return []
    
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
    
    try:
        # Read CSV manually without pandas
        with open(summary_path, 'r') as f:
            lines = f.readlines()
            header = lines[0].strip().split(',')
            
            for line in lines[1:]:
                values = line.strip().split(',')
                if len(values) >= 7:
                    method = values[0]
                    throughput = float(values[1])
                    noma_pairs = int(values[2])
                    oma_users = int(values[3])
                    noma_coverage = float(values[6])
                    
                    print(f"\n{method.upper()} CLUSTERING:")
                    print(f"  - Total Throughput: {throughput:.2f} Mbps")
                    print(f"  - NOMA Pairs: {noma_pairs}")
                    print(f"  - OMA Users: {oma_users}")
                    print(f"  - NOMA Coverage: {noma_coverage:.1f}%")
                    
    except Exception as e:
        print(f"Error reading summary file: {e}")

def view_run_details(run_folder):
    """Display detailed information about a run"""
    run_path = f"simulation_results/{run_folder}"
    
    if not os.path.exists(run_path):
        print(f"Run folder not found: {run_path}")
        return
    
    print(f"\nDetailed information for Run: {run_folder}")
    print("=" * 60)
    
    # List all files in the run directory
    files = os.listdir(run_path)
    
    print("\nAvailable files:")
    csv_files = []
    png_files = []
    
    for file in sorted(files):
        file_path = os.path.join(run_path, file)
        try:
            file_size = os.path.getsize(file_path)
            size_str = f"{file_size/1024:.1f} KB" if file_size < 1024*1024 else f"{file_size/(1024*1024):.1f} MB"
            
            if file.endswith('.csv'):
                csv_files.append(file)
                print(f"  📄 {file} ({size_str})")
            elif file.endswith('.png'):
                png_files.append(file)
                print(f"  📊 {file} ({size_str})")
            else:
                print(f"  📄 {file} ({size_str})")
        except:
            print(f"  📄 {file}")
    
    print(f"\nSummary: {len(csv_files)} CSV files, {len(png_files)} PNG files")

def cleanup_old_runs(keep_latest=5):
    """Clean up old simulation runs, keeping only the latest N runs"""
    runs = list_simulation_runs()
    
    if not runs:
        return
        
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
        deleted_count = 0
        for run in runs_to_delete:
            try:
                shutil.rmtree(f"simulation_results/{run}")
                print(f"Deleted {run}")
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {run}: {e}")
        print(f"Cleanup completed! Deleted {deleted_count} runs.")
    else:
        print("Cleanup cancelled")

def main():
    """Main interactive menu"""
    print("NOMA Simulation Results Manager")
    print("=" * 50)
    
    # Check if simulation_results directory exists
    if not os.path.exists("simulation_results"):
        print("No simulation_results directory found.")
        print("Please run clustering.py first to generate some results.")
        return
    
    while True:
        print("\n" + "=" * 50)
        print("NOMA Simulation Results Manager")
        print("=" * 50)
        print("1. List all simulation runs")
        print("2. View run summary")
        print("3. View run details")
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
            if not runs:
                continue
            
            try:
                idx = int(input(f"\nEnter run number (1-{len(runs)}): ")) - 1
                if 0 <= idx < len(runs):
                    view_run_details(runs[idx])
                else:
                    print("Invalid run number")
            except ValueError:
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
