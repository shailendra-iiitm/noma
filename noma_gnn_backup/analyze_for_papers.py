"""
Comprehensive Analysis for NOMA-GNN Papers
Generates all metrics, statistics, and visualizations needed for IEEE paper and Project Report
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json

# Configuration
COMPARISON_FILE = "comparison/comparison_results_500users.csv"
OUTPUT_DIR = Path("paper_analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_comparison_results():
    """Load comparison results"""
    df = pd.read_csv(COMPARISON_FILE)
    print(f"✓ Loaded comparison results: {len(df)} methods")
    return df

def generate_throughput_stats(df):
    """Generate throughput comparison statistics"""
    print("\n=== THROUGHPUT ANALYSIS ===")
    
    stats = []
    gnn_throughput = df[df['Method'] == 'NOMA-GNN']['Throughput_Mbps'].values[0]
    blossom_throughput = df[df['Method'] == 'Blossom']['Throughput_Mbps'].values[0]
    
    for _, row in df.iterrows():
        method = row['Method']
        throughput = row['Throughput_Mbps']
        sum_rate = row['Avg_Sum_Rate_bps_Hz']
        
        # Calculate percentage vs Blossom (optimal)
        vs_blossom_pct = (throughput / blossom_throughput) * 100
        
        # Calculate percentage vs GNN
        vs_gnn_pct = (throughput / gnn_throughput) * 100 if method != 'NOMA-GNN' else 100.0
        
        stats.append({
            'Method': method,
            'Throughput_Gbps': throughput / 1000,  # Convert to Gbps
            'Sum_Rate_bps_Hz': sum_rate,
            'vs_Blossom_%': vs_blossom_pct,
            'vs_GNN_%': vs_gnn_pct
        })
        
        print(f"{method:15} | {throughput/1000:6.2f} Gbps | {sum_rate:6.2f} bps/Hz | {vs_blossom_pct:5.1f}% of optimal")
    
    stats_df = pd.DataFrame(stats)
    stats_df.to_csv(OUTPUT_DIR / "throughput_statistics.csv", index=False)
    print(f"\n✓ Saved: {OUTPUT_DIR / 'throughput_statistics.csv'}")
    
    return stats_df

def generate_timing_stats(df):
    """Generate timing and speedup statistics"""
    print("\n=== TIMING & SPEEDUP ANALYSIS ===")
    
    timing = []
    gnn_time = df[df['Method'] == 'NOMA-GNN']['Time_ms'].values[0]
    
    for _, row in df.iterrows():
        method = row['Method']
        time_ms = row['Time_ms']
        time_s = time_ms / 1000
        
        # Calculate speedup vs GNN
        if method != 'NOMA-GNN':
            speedup_vs_gnn = time_ms / gnn_time
            speedup_text = f"{speedup_vs_gnn:.2f}× slower" if speedup_vs_gnn > 1 else f"{1/speedup_vs_gnn:.2f}× faster"
        else:
            speedup_text = "baseline"
        
        timing.append({
            'Method': method,
            'Time_ms': time_ms,
            'Time_s': time_s,
            'Speedup_vs_GNN': speedup_text
        })
        
        print(f"{method:15} | {time_ms:10.2f} ms ({time_s:7.2f} s) | {speedup_text}")
    
    timing_df = pd.DataFrame(timing)
    timing_df.to_csv(OUTPUT_DIR / "timing_statistics.csv", index=False)
    print(f"\n✓ Saved: {OUTPUT_DIR / 'timing_statistics.csv'}")
    
    # Calculate key speedups
    blossom_time = df[df['Method'] == 'Blossom']['Time_ms'].values[0]
    bipartite_time = df[df['Method'] == 'Bipartite']['Time_ms'].values[0]
    
    print(f"\n KEY SPEEDUPS:")
    print(f"   GNN vs Blossom:   {blossom_time / gnn_time:.1f}× faster")
    print(f"   GNN vs Bipartite: {bipartite_time / gnn_time:.1f}× faster")
    
    return timing_df

def plot_throughput_comparison(stats_df):
    """Create throughput comparison bar chart"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    methods = stats_df['Method'].values
    throughput = stats_df['Throughput_Gbps'].values
    
    # Color coding
    colors = ['#ff7f0e', '#2ca02c', '#1f77b4', '#d62728', '#9467bd']
    bars = ax.bar(methods, throughput, color=colors, alpha=0.8, edgecolor='black')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_ylabel('System Throughput (Gbps)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Pairing Method', fontsize=12, fontweight='bold')
    ax.set_title('System Throughput Comparison (N=500 Users)', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, max(throughput) * 1.15)
    
    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    
    filepath = OUTPUT_DIR / "throughput_comparison.png"
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {filepath}")
    plt.close()

def plot_timing_comparison(timing_df, df):
    """Create timing comparison chart (log scale)"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    methods = timing_df['Method'].values
    times_ms = timing_df['Time_ms'].values
    
    # Chart 1: Log scale
    colors = ['#ff7f0e', '#2ca02c', '#1f77b4', '#d62728', '#9467bd']
    bars1 = ax1.bar(methods, times_ms, color=colors, alpha=0.8, edgecolor='black')
    ax1.set_yscale('log')
    ax1.set_ylabel('Execution Time (ms, log scale)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Pairing Method', fontsize=12, fontweight='bold')
    ax1.set_title('Execution Time Comparison', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3, linestyle='--', which='both')
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=15, ha='right')
    
    # Add value labels
    for bar, time in zip(bars1, times_ms):
        height = bar.get_height()
        if time < 1:
            label = f'{time:.2f} ms'
        elif time < 1000:
            label = f'{time:.1f} ms'
        else:
            label = f'{time/1000:.1f} s'
        ax1.text(bar.get_x() + bar.get_width()/2., height * 1.3,
                label, ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Chart 2: Complexity O() notation
    complexity_data = {
        'Static': 'O(N log N)',
        'Balanced': 'O(N log N)',
        'Bipartite': 'O(N³)',
        'Blossom': 'O(N³)',
        'NOMA-GNN': 'O(N log N)'
    }
    
    # Group by complexity
    fast_methods = [m for m in methods if complexity_data[m] == 'O(N log N)']
    slow_methods = [m for m in methods if complexity_data[m] == 'O(N³)']
    
    fast_times = [timing_df[timing_df['Method'] == m]['Time_ms'].values[0] for m in fast_methods]
    slow_times = [timing_df[timing_df['Method'] == m]['Time_ms'].values[0] for m in slow_methods]
    
    ax2.bar(fast_methods, fast_times, color='green', alpha=0.7, label='O(N log N)', edgecolor='black')
    ax2.bar(slow_methods, slow_times, color='red', alpha=0.7, label='O(N³)', edgecolor='black')
    ax2.set_ylabel('Execution Time (ms)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Pairing Method', fontsize=12, fontweight='bold')
    ax2.set_title('Complexity Classes', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=15, ha='right')
    
    plt.tight_layout()
    
    filepath = OUTPUT_DIR / "timing_comparison.png"
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {filepath}")
    plt.close()

def generate_paper_ready_text(stats_df, timing_df, df):
    """Generate copy-paste ready text snippets for papers"""
    
    gnn_throughput = stats_df[stats_df['Method'] == 'NOMA-GNN']['Throughput_Gbps'].values[0]
    blossom_throughput = stats_df[stats_df['Method'] == 'Blossom']['Throughput_Gbps'].values[0]
    gnn_vs_blossom_pct = stats_df[stats_df['Method'] == 'NOMA-GNN']['vs_Blossom_%'].values[0]
    
    gnn_time = timing_df[timing_df['Method'] == 'NOMA-GNN']['Time_ms'].values[0]
    blossom_time = timing_df[timing_df['Method'] == 'Blossom']['Time_ms'].values[0]
    speedup = blossom_time / gnn_time
    
    gnn_sumrate = df[df['Method'] == 'NOMA-GNN']['Avg_Sum_Rate_bps_Hz'].values[0]
    blossom_sumrate = df[df['Method'] == 'Blossom']['Avg_Sum_Rate_bps_Hz'].values[0]
    
    text = f"""
{'='*80}
PAPER-READY TEXT SNIPPETS
{'='*80}

1. DATASET SPECIFICATIONS:
   "We generated 200 user deployment scenarios, each containing 500 users, for a
   total of 100,000 training samples. Channel characteristics were modeled using
   the 3GPP UMa standard at 3.5 GHz with 20 MHz bandwidth."

2. THROUGHPUT PERFORMANCE:
   "NOMA-GNN achieves {gnn_vs_blossom_pct:.1f}% of optimal Blossom throughput
   ({gnn_throughput:.2f} Gbps vs {blossom_throughput:.2f} Gbps) on a test 
   scenario with 500 users."

3. COMPUTATIONAL SPEEDUP:
   "Our GNN approach provides a {speedup:.1f}× speedup compared to Blossom
   matching ({gnn_time:.1f} ms vs {blossom_time/1000:.2f} s for N=500 users),
   making it suitable for real-time deployment."

4. SUM-RATE ACHIEVEMENT:
   "NOMA-GNN achieves an average sum-rate of {gnn_sumrate:.2f} bits/s/Hz,
   reaching {(gnn_sumrate/blossom_sumrate)*100:.1f}% of the optimal rate
   obtained by Blossom matching ({blossom_sumrate:.2f} bits/s/Hz)."

5. COMPLEXITY ADVANTAGE:
   "Unlike Blossom and Bipartite methods with O(N³) complexity, NOMA-GNN
   maintains O(N log N) complexity through efficient edge construction and
   Hungarian matching on predicted scores."

6. METHOD COMPARISON TABLE (LaTeX):
   \\begin{{tabular}}{{lrrr}}
   \\toprule
   \\textbf{{Method}} & \\textbf{{Time (ms)}} & \\textbf{{Throughput (Gbps)}} & \\textbf{{vs Optimal (\\%)}} \\\\
   \\midrule
"""
    
    for _, row in stats_df.iterrows():
        method = row['Method']
        time = timing_df[timing_df['Method'] == method]['Time_ms'].values[0]
        throughput = row['Throughput_Gbps']
        vs_blossom = row['vs_Blossom_%']
        
        text += f"   {method:15} & {time:10.2f} & {throughput:6.2f} & {vs_blossom:5.1f} \\\\\n"
    
    text += """   \\bottomrule
   \\end{tabular}

"""
    
    text += f"""
7. KEY FINDINGS FOR ABSTRACT:
   - Trained on 200 scenarios (100,000 samples) with 500 users each
   - Achieves {gnn_vs_blossom_pct:.1f}% of optimal throughput
   - Provides {speedup:.1f}× speedup over optimal baseline
   - Maintains O(N log N) complexity vs O(N³) for traditional methods
   - Test scenario: Single deployment with 500 users

8. LIMITATIONS TO ACKNOWLEDGE:
   - Single test scenario (not statistical evaluation across multiple scenarios)
   - No train/validation/test split (trained on full dataset)
   - Classification metrics (AUC, F1) not evaluated (would require labeled pairs)
   - Throughput measured on single deployment, not averaged across diverse conditions

{'='*80}
"""
    
    filepath = OUTPUT_DIR / "paper_text_snippets.txt"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"\n✓ Saved: {filepath}")
    print(text)

def generate_what_we_have_report():
    """Document what metrics we actually have vs what papers claim"""
    
    report = """
{'='*80}
ACTUAL DATA vs PAPER CLAIMS - DISCREPANCY REPORT
{'='*80}

WHAT WE ACTUALLY HAVE:
✓ Training data: 200 scenarios × 500 users = 100,000 samples
✓ Test data: 1 scenario × 500 users = single deployment test
✓ Comparison results: 5 methods tested on same 500-user scenario
✓ Timing measurements: Average of 3 iterations per method
✓ Throughput: Calculated from sum-rate predictions
✓ Pairing efficiency: Percentage of users successfully paired

WHAT WE DON'T HAVE:
✗ Train/Validation/Test split (we used all data for training)
✗ Classification metrics on test set (no labeled pairs for evaluation)
✗ Regression metrics (MAE, RMSE, R² for sum-rate/power prediction)
✗ Multiple test scenarios for statistical validation
✗ Confidence intervals from repeated testing
✗ Out-of-distribution testing (different N, channel conditions)
✗ Jain's fairness index calculations
✗ Per-user throughput distributions

PAPER CLAIMS TO REMOVE/FIX:

IEEE PAPER (result_discussion.tex):
❌ Line 5: "50,000 scenarios" → Should be "200 scenarios"
❌ Line 5: "N ∈ {4,6,8,10,12}" → Should be "N = 500"
❌ Line 5: "70%/15%/15% split" → No split, used all data for training
❌ Line 5: "7,500 test scenarios" → Should be "1 test scenario"
❌ Lines 17-24: Classification metrics table → NO DATA (remove or mark as N/A)
❌ Lines 47-55: Regression metrics table → NO DATA (remove or mark as N/A)
❌ Lines 78-85: Statistical significance, confidence intervals → NO DATA
❌ Line 95: "averaged over 1,000 test instances" → Should be "3 iterations on 1 scenario"

PROJECT REPORT (14_experimental_setup.tex):
❌ Lines 7-9: "50,000 scenarios, N ∈ {4,6,8,10,12}" → "200 scenarios, N = 500"
❌ Lines 13-19: Train/Val/Test split table → Remove (no split used)
❌ Lines 21-28: Out-of-distribution testing → Remove (not performed)

PROJECT REPORT (15_results.tex):
❌ Lines 5-24: Classification performance table → NO DATA
❌ Lines 29-45: Sum-rate regression table → NO DATA
❌ Lines 50-66: Power allocation regression table → NO DATA
❌ Lines 71-85: Statistical testing, confidence intervals → NO DATA
❌ Line 95: "7,500 test scenarios" → "1 test scenario"

WHAT TO KEEP (ACCURATE):
✓ Throughput comparison between methods
✓ Timing measurements and speedup calculations
✓ Complexity analysis (O(N log N) vs O(N³))
✓ Hardware specifications
✓ Channel model parameters (3GPP UMa)
✓ GNN architecture details
✓ Training hyperparameters

RECOMMENDED FIXES:
1. Replace "extensive evaluation on 7,500 scenarios" with "proof-of-concept test on 500-user deployment"
2. Remove all classification/regression metric tables (or mark as "Future Work")
3. Focus paper on: (a) GNN architecture, (b) Throughput comparison, (c) Speedup analysis
4. Acknowledge limitations: single-scenario testing, no statistical validation
5. Present as "preliminary results" or "computational feasibility study"

{'='*80}
"""
    
    filepath = OUTPUT_DIR / "discrepancy_report.txt"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✓ Saved: {filepath}")
    print(report)

def main():
    print("="*80)
    print(" COMPREHENSIVE ANALYSIS FOR NOMA-GNN PAPERS")
    print("="*80)
    
    # Load data
    df = load_comparison_results()
    
    # Generate statistics
    stats_df = generate_throughput_stats(df)
    timing_df = generate_timing_stats(df)
    
    # Create visualizations
    print("\n=== GENERATING VISUALIZATIONS ===")
    plot_throughput_comparison(stats_df)
    plot_timing_comparison(timing_df, df)
    
    # Generate paper-ready content
    print("\n=== GENERATING PAPER CONTENT ===")
    generate_paper_ready_text(stats_df, timing_df, df)
    generate_what_we_have_report()
    
    print("\n" + "="*80)
    print(f" ANALYSIS COMPLETE - All outputs saved to: {OUTPUT_DIR.absolute()}")
    print("="*80)
    
    print("\nGENERATED FILES:")
    for file in OUTPUT_DIR.glob("*"):
        print(f"  📄 {file.name}")

if __name__ == "__main__":
    main()
