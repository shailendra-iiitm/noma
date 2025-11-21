"""
Visualization of NOMA-GNN Performance Results
Generates publication-quality plots for IEEE paper
Focus: Throughput, Scalability, and Timing Analysis
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Set IEEE style parameters
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 13
plt.rcParams['figure.dpi'] = 300
plt.rcParams['lines.linewidth'] = 2.5
plt.rcParams['lines.markersize'] = 9

# Data from paper results
methods = ['Static', 'Balanced', 'Bipartite', 'Blossom', 'NOMA-GNN']
user_densities = [500, 1000, 2000]

# Throughput data (Mbps)
throughput_data = {
    'Static': [363.14, 716.94, 1389.04],
    'Balanced': [474.61, 950.0, 1900.0],
    'Bipartite': [659.07, 1335.41, 2644.88],
    'Blossom': [659.07, 1335.41, 2644.88],
    'NOMA-GNN': [636.15, 1277.60, 2553.10]
}

# Runtime data (seconds)
runtime_data = {
    'Static': [0.00038, 0.00252, 0.00059],
    'Balanced': [0.00009, 0.00015, 0.00020],
    'Bipartite': [21.143, 171.648, 1839.536],
    'Blossom': [30.363, 240.0, 2100.0],
    'NOMA-GNN': [0.752, 2.682, 16.083]
}

# Efficiency data (% of optimal)
efficiency_data = {
    'NOMA-GNN': [96.5, 95.7, 96.5],
    'Static': [55.1, 53.7, 52.5],
    'Balanced': [72.0, 71.1, 71.8]
}



def plot_three_panel_performance():
    """Combined 3-panel plot: Throughput, Scalability Efficiency, and Runtime"""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))
    
    # Color scheme
    colors = {
        'NOMA-GNN': '#9B59B6',
        'Bipartite': '#2ECC71',
        'Blossom': '#F39C12',
        'Static': '#E74C3C',
        'Balanced': '#3498DB'
    }
    
    markers = {
        'NOMA-GNN': 'd',
        'Bipartite': 'o',
        'Blossom': 's',
        'Static': '^',
        'Balanced': 'v'
    }
    
    # Panel 1: Throughput vs User Density
    for method in ['Bipartite', 'NOMA-GNN', 'Balanced', 'Static']:
        ax1.plot(user_densities, throughput_data[method], 
                marker=markers[method], linestyle='-', linewidth=2.5, markersize=9,
                label=method, color=colors[method],
                markerfacecolor='white', markeredgewidth=2.5, alpha=0.85)
    
    ax1.set_xlabel('Number of Users (N)', fontweight='bold', fontsize=12)
    ax1.set_ylabel('System Throughput (Mbps)', fontweight='bold', fontsize=12)
    ax1.set_title('(a) Throughput Scalability', fontweight='bold', fontsize=13)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    ax1.legend(loc='upper left', framealpha=0.95, edgecolor='black', fontsize=10)
    ax1.set_xticks(user_densities)
    
    # Panel 2: Efficiency (% of Optimal)
    for method in ['NOMA-GNN', 'Balanced', 'Static']:
        ax2.plot(user_densities, efficiency_data[method],
                marker=markers[method], linestyle='-', linewidth=2.5, markersize=9,
                label=method, color=colors[method],
                markerfacecolor='white', markeredgewidth=2.5, alpha=0.85)
    
    ax2.axhline(y=100, color='red', linestyle='--', linewidth=2, 
               label='Optimal (100%)', alpha=0.7)
    ax2.set_xlabel('Number of Users (N)', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Throughput Efficiency (%)', fontweight='bold', fontsize=12)
    ax2.set_title('(b) Efficiency Analysis', fontweight='bold', fontsize=13)
    ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    ax2.legend(loc='lower left', framealpha=0.95, edgecolor='black', fontsize=10)
    ax2.set_xticks(user_densities)
    ax2.set_ylim([45, 105])
    
    # Panel 3: Runtime (log scale)
    for method in ['Bipartite', 'NOMA-GNN', 'Balanced', 'Static']:
        ax3.plot(user_densities, runtime_data[method],
                marker=markers[method], linestyle='-', linewidth=2.5, markersize=9,
                label=method, color=colors[method],
                markerfacecolor='white', markeredgewidth=2.5, alpha=0.85)
    
    ax3.set_yscale('log')
    ax3.set_xlabel('Number of Users (N)', fontweight='bold', fontsize=12)
    ax3.set_ylabel('Runtime (seconds, log scale)', fontweight='bold', fontsize=12)
    ax3.set_title('(c) Computational Complexity', fontweight='bold', fontsize=13)
    ax3.grid(True, alpha=0.3, linestyle='--', linewidth=0.8, which='both')
    ax3.legend(loc='upper left', framealpha=0.95, edgecolor='black', fontsize=10)
    ax3.set_xticks(user_densities)
    
    plt.tight_layout()
    plt.savefig('performance_analysis_three_panel.png', dpi=300, bbox_inches='tight')
    plt.savefig('performance_analysis_three_panel.pdf', bbox_inches='tight')
    print("✓ Saved: performance_analysis_three_panel.png/pdf")
    plt.close()


def plot_throughput_runtime_combined():
    """2-panel plot: Throughput and Runtime side-by-side"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    colors = {
        'NOMA-GNN': '#9B59B6',
        'Bipartite': '#2ECC71',
        'Static': '#E74C3C',
        'Balanced': '#3498DB'
    }
    
    markers = {
        'NOMA-GNN': 'd',
        'Bipartite': 'o',
        'Static': '^',
        'Balanced': 'v'
    }
    
    # Panel 1: Throughput
    for method in ['Bipartite', 'NOMA-GNN', 'Balanced', 'Static']:
        ax1.plot(user_densities, throughput_data[method],
                marker=markers[method], linestyle='-', linewidth=2.5, markersize=10,
                label=method, color=colors[method],
                markerfacecolor='white', markeredgewidth=2.5, alpha=0.85)
    
    ax1.set_xlabel('Number of Users (N)', fontweight='bold', fontsize=13)
    ax1.set_ylabel('System Throughput (Mbps)', fontweight='bold', fontsize=13)
    ax1.set_title('(a) Scalability: Throughput Performance', fontweight='bold', fontsize=14)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    ax1.legend(loc='upper left', framealpha=0.95, edgecolor='black', fontsize=11)
    ax1.set_xticks(user_densities)
    
    # Panel 2: Runtime
    for method in ['Bipartite', 'NOMA-GNN', 'Static']:
        ax2.plot(user_densities, runtime_data[method],
                marker=markers[method], linestyle='-', linewidth=2.5, markersize=10,
                label=method, color=colors[method],
                markerfacecolor='white', markeredgewidth=2.5, alpha=0.85)
    
    ax2.set_yscale('log')
    ax2.set_xlabel('Number of Users (N)', fontweight='bold', fontsize=13)
    ax2.set_ylabel('Runtime (seconds, log scale)', fontweight='bold', fontsize=13)
    ax2.set_title('(b) Computational Efficiency', fontweight='bold', fontsize=14)
    ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.8, which='both')
    ax2.legend(loc='upper left', framealpha=0.95, edgecolor='black', fontsize=11)
    ax2.set_xticks(user_densities)
    
    plt.tight_layout()
    plt.savefig('throughput_runtime_comparison.png', dpi=300, bbox_inches='tight')
    plt.savefig('throughput_runtime_comparison.pdf', bbox_inches='tight')
    print("✓ Saved: throughput_runtime_comparison.png/pdf")
    plt.close()


def plot_efficiency_speedup_combined():
    """Combined plot showing efficiency maintained while speedup increases"""
    fig, ax1 = plt.subplots(figsize=(8, 5.5))
    
    # Plot efficiency on left y-axis
    color1 = '#9B59B6'
    ax1.set_xlabel('Number of Users (N)', fontweight='bold', fontsize=13)
    ax1.set_ylabel('Throughput Efficiency (%)', color=color1, fontweight='bold', fontsize=13)
    line1 = ax1.plot(user_densities, efficiency_data['NOMA-GNN'], 
                     'd-', linewidth=3, markersize=12,
                     color=color1, label='NOMA-GNN Efficiency',
                     markerfacecolor='white', markeredgewidth=2.5)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_ylim([94, 98])
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    
    # Add efficiency value labels
    for x, y in zip(user_densities, efficiency_data['NOMA-GNN']):
        ax1.text(x, y + 0.4, f'{y:.1f}%', ha='center', fontsize=11,
                fontweight='bold', color=color1)
    
    # Plot speedup on right y-axis
    speedup_vs_bipartite = [
        runtime_data['Bipartite'][i] / runtime_data['NOMA-GNN'][i] 
        for i in range(len(user_densities))
    ]
    
    ax2 = ax1.twinx()
    color2 = '#E74C3C'
    ax2.set_ylabel('Speedup vs Bipartite (×)', color=color2, fontweight='bold', fontsize=13)
    line2 = ax2.plot(user_densities, speedup_vs_bipartite, 
                     'o-', linewidth=3, markersize=12,
                     color=color2, label='Speedup Factor',
                     markerfacecolor='white', markeredgewidth=2.5)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Add speedup value labels
    for x, y in zip(user_densities, speedup_vs_bipartite):
        ax2.text(x, y + 6, f'{y:.1f}×', ha='center', fontsize=11,
                fontweight='bold', color=color2)
    
    ax1.set_xticks(user_densities)
    ax1.set_title('NOMA-GNN: Near-Optimal Efficiency with Growing Speedup', 
                  fontweight='bold', fontsize=14, pad=20)
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left', framealpha=0.95, 
              edgecolor='black', fontsize=11)
    
    fig.tight_layout()
    plt.savefig('efficiency_speedup_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig('efficiency_speedup_analysis.pdf', bbox_inches='tight')
    print("✓ Saved: efficiency_speedup_analysis.png/pdf")
    plt.close()


def plot_throughput_bar_comparison():
    """Bar chart: Throughput comparison for N=500 users"""
    methods_bar = ['Static', 'Balanced', 'Bipartite', 'Blossom', 'NOMA-GNN']
    throughput_500 = [363.14, 474.61, 659.07, 659.07, 636.15]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6']
    bars = ax.bar(methods_bar, throughput_500, color=colors, alpha=0.85, 
                  edgecolor='black', linewidth=2, width=0.6)
    
    # Add value labels on bars
    for bar, val in zip(bars, throughput_500):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 15,
                f'{val:.1f} Mbps', ha='center', va='bottom', 
                fontsize=11, fontweight='bold')
    
    # Add horizontal line for optimal
    ax.axhline(y=659.07, color='red', linestyle='--', linewidth=2.5, 
               label='Optimal (Blossom/Bipartite)', alpha=0.7)
    
    # Add percentage annotations relative to optimal
    percentages = [(val/659.07)*100 for val in throughput_500]
    for i, (bar, pct) in enumerate(zip(bars, percentages)):
        ax.text(bar.get_x() + bar.get_width()/2., 50,
                f'{pct:.1f}%', ha='center', va='bottom',
                fontsize=10, fontweight='bold', color='white',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=colors[i], alpha=0.8))
    
    ax.set_ylabel('System Throughput (Mbps)', fontweight='bold', fontsize=14)
    ax.set_xlabel('Pairing Method', fontweight='bold', fontsize=14)
    ax.set_title('Throughput Comparison on 500-User Scenario', 
                 fontweight='bold', fontsize=15, pad=20)
    ax.set_ylim([0, 750])
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1)
    ax.legend(loc='upper left', framealpha=0.95, edgecolor='black', fontsize=12)
    
    plt.xticks(fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('throughput_bar_comparison.png', dpi=300, bbox_inches='tight')
    plt.savefig('throughput_bar_comparison.pdf', bbox_inches='tight')
    print("✓ Saved: throughput_bar_comparison.png/pdf")
    plt.close()


def generate_all_plots():
    """Generate all visualization plots"""
    print("\n" + "="*70)
    print("Generating NOMA-GNN Performance Analysis Plots")
    print("Focus: Throughput, Scalability, and Timing")
    print("="*70 + "\n")
    
    plot_throughput_bar_comparison()
    plot_three_panel_performance()
    plot_throughput_runtime_combined()
    plot_efficiency_speedup_combined()
    
    print("\n" + "="*70)
    print("✓ All plots generated successfully!")
    print("="*70)
    print("\nGenerated files:")
    print("  1. throughput_bar_comparison.png/pdf")
    print("     └─ Bar chart: Throughput comparison (N=500)")
    print("  2. performance_analysis_three_panel.png/pdf")
    print("     └─ 3-panel: Throughput + Efficiency + Runtime")
    print("  3. throughput_runtime_comparison.png/pdf")
    print("     └─ 2-panel: Throughput vs Runtime scalability")
    print("  4. efficiency_speedup_analysis.png/pdf")
    print("     └─ Dual-axis: Efficiency maintained + Speedup growth")
    print("\n" + "="*70)
    print("Ready for IEEE paper inclusion!")
    print("="*70)


if __name__ == "__main__":
    generate_all_plots()
