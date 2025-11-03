"""
Quick script to compute Jain's Fairness Index from predicted pairs
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def compute_jains_fairness(user_rates):
    """Compute Jain's Fairness Index from user rates dictionary"""
    rates_array = np.array(list(user_rates.values()))
    n = len(rates_array)
    sum_rates = np.sum(rates_array)
    sum_rates_squared = np.sum(rates_array ** 2)
    fairness = (sum_rates ** 2) / (n * sum_rates_squared)
    return fairness

def compute_per_user_rates_from_csv(pairs_csv, h_values_csv):
    """
    Compute per-user rates from predicted pairs CSV
    """
    pairs_df = pd.read_csv(pairs_csv)
    h_df = pd.read_csv(h_values_csv)
    
    # Create h_linear lookup
    h_lookup = dict(zip(h_df['User_ID'], h_df['h_linear']))
    
    user_rates = {}
    
    # Process each pair
    for idx, row in pairs_df.iterrows():
        user1 = row['User1_ID']
        user2 = row['User2_ID']
        
        h1 = h_lookup[user1]
        h2 = h_lookup[user2]
        
        # Determine weak/strong
        if h1 >= h2:
            h_strong, h_weak = h1, h2
            strong_id, weak_id = user1, user2
        else:
            h_strong, h_weak = h2, h1
            strong_id, weak_id = user2, user1
        
        # Get power allocation
        if 'alpha' in row:
            alpha = row['alpha']
        elif 'Alpha' in row:
            alpha = row['Alpha']
        else:
            alpha = 0.8  # default
        
        # Compute rates (P=1, noise=1e-9 from config)
        P = 1.0
        N0 = 1e-9
        
        # Weak user rate (decodes its own signal treating strong as noise)
        snr_weak = (alpha * P * h_weak) / (N0 + (1-alpha) * P * h_weak)
        rate_weak = np.log2(1 + snr_weak)
        
        # Strong user rate (after SIC removes weak signal)
        snr_strong = ((1-alpha) * P * h_strong) / N0
        rate_strong = np.log2(1 + snr_strong)
        
        # Accumulate rates
        user_rates[weak_id] = user_rates.get(weak_id, 0) + rate_weak
        user_rates[strong_id] = user_rates.get(strong_id, 0) + rate_strong
    
    return user_rates

def plot_rate_distribution(user_rates, h_df, output_file='fairness_analysis.png'):
    """Plot rate distribution analysis"""
    rates_array = np.array(list(user_rates.values()))
    user_ids = list(user_rates.keys())
    
    # Get channel gains for scatter plot
    h_lookup = dict(zip(h_df['User_ID'], h_df['h_dB']))
    h_db_vals = [h_lookup[uid] for uid in user_ids]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Histogram
    ax = axes[0, 0]
    ax.hist(rates_array, bins=30, alpha=0.7, color='steelblue', edgecolor='black')
    ax.set_xlabel('User Rate (bits/s/Hz)', fontsize=11)
    ax.set_ylabel('Number of Users', fontsize=11)
    ax.set_title('Rate Distribution', fontsize=12, fontweight='bold')
    ax.axvline(rates_array.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean = {rates_array.mean():.2f}')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # 2. CDF
    ax = axes[0, 1]
    sorted_rates = np.sort(rates_array)
    cdf = np.arange(1, len(sorted_rates)+1) / len(sorted_rates)
    ax.plot(sorted_rates, cdf, 'b-', linewidth=2)
    ax.set_xlabel('User Rate (bits/s/Hz)', fontsize=11)
    ax.set_ylabel('CDF', fontsize=11)
    ax.set_title('Cumulative Distribution Function', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add percentile markers
    percentiles = [10, 50, 90]
    for p in percentiles:
        val = np.percentile(sorted_rates, p)
        ax.axhline(p/100, color='gray', linestyle=':', alpha=0.5)
        ax.axvline(val, color='gray', linestyle=':', alpha=0.5)
        ax.text(val, p/100, f'{p}th: {val:.1f}', fontsize=8, ha='right')
    
    # 3. Rate vs Channel Gain
    ax = axes[1, 0]
    ax.scatter(h_db_vals, rates_array, alpha=0.5, s=25, c='green')
    ax.set_xlabel('Channel Gain (dB)', fontsize=11)
    ax.set_ylabel('User Rate (bits/s/Hz)', fontsize=11)
    ax.set_title('Rate vs Channel Quality', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add trend line
    z = np.polyfit(h_db_vals, rates_array, 1)
    p = np.poly1d(z)
    ax.plot(sorted(h_db_vals), p(sorted(h_db_vals)), "r--", alpha=0.8, linewidth=2, label='Trend')
    ax.legend(fontsize=10)
    
    # 4. Box plot with statistics
    ax = axes[1, 1]
    bp = ax.boxplot([rates_array], labels=['All Users'], patch_artist=True)
    bp['boxes'][0].set_facecolor('lightblue')
    ax.set_ylabel('User Rate (bits/s/Hz)', fontsize=11)
    ax.set_title('Rate Statistics', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add text with statistics
    stats_text = f"Mean: {rates_array.mean():.2f}\n"
    stats_text += f"Median: {np.median(rates_array):.2f}\n"
    stats_text += f"Std: {rates_array.std():.2f}\n"
    stats_text += f"Min: {rates_array.min():.2f}\n"
    stats_text += f"Max: {rates_array.max():.2f}"
    ax.text(1.15, 0.5, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nSaved plot to {output_file}")
    plt.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Compute Jain\'s Fairness Index')
    parser.add_argument('--pairs_csv', type=str, 
                       default='predicted_pairs_relaxed.csv',
                       help='Path to predicted pairs CSV')
    parser.add_argument('--h_values_csv', type=str,
                       default='h_values.csv',
                       help='Path to h_values CSV with channel gains')
    
    args = parser.parse_args()
    
    print("="*60)
    print("COMPUTING JAIN'S FAIRNESS INDEX")
    print("="*60)
    
    print(f"\nLoading data...")
    print(f"  Pairs: {args.pairs_csv}")
    print(f"  H values: {args.h_values_csv}")
    
    # Compute per-user rates
    user_rates = compute_per_user_rates_from_csv(args.pairs_csv, args.h_values_csv)
    
    print(f"\nPer-User Rates Computed:")
    print(f"  Total users: {len(user_rates)}")
    print(f"  Total pairs: {pd.read_csv(args.pairs_csv).shape[0]}")
    
    rates_array = np.array(list(user_rates.values()))
    
    print(f"\nRate Statistics:")
    print(f"  Mean:   {rates_array.mean():.2f} bits/s/Hz")
    print(f"  Median: {np.median(rates_array):.2f} bits/s/Hz")
    print(f"  Std:    {rates_array.std():.2f}")
    print(f"  Min:    {rates_array.min():.2f}")
    print(f"  Max:    {rates_array.max():.2f}")
    print(f"  10th percentile: {np.percentile(rates_array, 10):.2f}")
    print(f"  90th percentile: {np.percentile(rates_array, 90):.2f}")
    
    # Compute Jain's fairness
    fairness = compute_jains_fairness(user_rates)
    
    print(f"\n" + "="*60)
    print(f"JAIN'S FAIRNESS INDEX: {fairness:.4f}")
    print("="*60)
    
    print(f"\nInterpretation:")
    if fairness >= 0.9:
        print("  Excellent fairness (≥ 0.9) - Nearly equal rates")
    elif fairness >= 0.8:
        print("  Good fairness (0.8-0.9) - Well-balanced distribution")
    elif fairness >= 0.7:
        print("  Moderate fairness (0.7-0.8) - Acceptable variation")
    else:
        print("  Low fairness (< 0.7) - Significant rate disparity")
    
    # Load h_values for plotting
    h_df = pd.read_csv(args.h_values_csv)
    
    # Plot distribution
    plot_rate_distribution(user_rates, h_df)
    
    # Save detailed results
    output_csv = 'per_user_rates.csv'
    rates_df = pd.DataFrame([
        {'User_ID': uid, 'Rate_bitsHz': rate, 'Channel_Gain_dB': h_df[h_df['User_ID']==uid]['h_dB'].values[0]}
        for uid, rate in user_rates.items()
    ])
    rates_df = rates_df.sort_values('Rate_bitsHz', ascending=False)
    rates_df.to_csv(output_csv, index=False)
    print(f"\nSaved per-user rates to {output_csv}")
    
    # Save summary
    with open('fairness_summary.txt', 'w') as f:
        f.write("="*60 + "\n")
        f.write("JAIN'S FAIRNESS INDEX ANALYSIS\n")
        f.write("="*60 + "\n\n")
        f.write(f"Jain's Fairness Index: {fairness:.4f}\n\n")
        f.write("Rate Statistics:\n")
        f.write(f"  Mean:   {rates_array.mean():.2f} bits/s/Hz\n")
        f.write(f"  Median: {np.median(rates_array):.2f} bits/s/Hz\n")
        f.write(f"  Std:    {rates_array.std():.2f}\n")
        f.write(f"  Min:    {rates_array.min():.2f}\n")
        f.write(f"  Max:    {rates_array.max():.2f}\n")
        f.write(f"  10th percentile: {np.percentile(rates_array, 10):.2f}\n")
        f.write(f"  90th percentile: {np.percentile(rates_array, 90):.2f}\n")
    
    print(f"Saved summary to fairness_summary.txt")
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE!")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
