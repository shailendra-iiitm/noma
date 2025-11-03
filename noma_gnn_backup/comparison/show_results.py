import pandas as pd
import sys
from pathlib import Path

# Get script directory
SCRIPT_DIR = Path(__file__).parent.absolute()

# Try to find results file
if len(sys.argv) > 1:
    results_file = sys.argv[1]
else:
    # Try common filenames in script directory
    for fname in ['comparison_results.csv', 'comparison_results_500users.csv']:
        fpath = SCRIPT_DIR / fname
        if fpath.exists():
            results_file = str(fpath)
            break
    else:
        print("❌ No results file found!")
        print(f"Searched in: {SCRIPT_DIR}")
        print("Usage: python show_results.py [results_file.csv]")
        sys.exit(1)

df = pd.read_csv(results_file)
print(f"\n📊 Analyzing: {Path(results_file).name}")

print("\n" + "="*90)
print(" COMPREHENSIVE COMPARISON RESULTS (500 Users)")
print("="*90 + "\n")
print(df.to_string(index=False))

print("\n" + "="*90)
print(" KEY INSIGHTS FOR RESEARCH PAPER")
print("="*90)

print(f"\n1. TIMING COMPARISON:")
print(f"   Note: Static, Balanced, Bipartite, GNN = average of {df['Time_std_ms'].notna().sum()-1} runs")
print(f"         Blossom = single run (too slow for multiple iterations)")
for idx, row in df.iterrows():
    method = row['Method']
    time_ms = row['Time_ms']
    time_std = row['Time_std_ms']
    
    if time_ms < 1:
        time_str = f"{time_ms:.4f} ms"
    elif time_ms < 1000:
        time_str = f"{time_ms:.2f} ms"
    else:
        time_str = f"{time_ms:.2f} ms ({time_ms/1000:.2f} s)"
    
    # Add std dev if available
    if pd.notna(time_std) and time_std > 0:
        time_str += f" ± {time_std:.2f} ms"
    elif method == "Blossom":
        time_str += " [single run]"
    
    print(f"   - {method:12s} {time_str}")

print(f"\n2. SPEEDUP ANALYSIS:")
# Find GNN row
gnn_idx = df[df['Method'] == 'NOMA-GNN'].index[0]
gnn_time = df.loc[gnn_idx, 'Time_ms']

# Find Bipartite
if 'Bipartite' in df['Method'].values:
    bip_idx = df[df['Method'] == 'Bipartite'].index[0]
    speedup_bipartite = df.loc[bip_idx, 'Time_ms'] / gnn_time
    print(f"   - GNN is {speedup_bipartite:.1f}× FASTER than Bipartite")

# Find Blossom if exists
if 'Blossom' in df['Method'].values:
    blos_idx = df[df['Method'] == 'Blossom'].index[0]
    speedup_blossom = df.loc[blos_idx, 'Time_ms'] / gnn_time
    print(f"   - GNN is {speedup_blossom:.1f}× FASTER than Blossom (optimal)")
    print(f"   - Time reduction vs Blossom: {(1 - 1/speedup_blossom)*100:.1f}%")
else:
    print(f"   - Blossom not run (use --full to include)")

print(f"\n3. THROUGHPUT COMPARISON:")
baseline = df[df['Method'] == 'Static']['Throughput_Mbps'].values[0]
for idx, row in df.iterrows():
    method = row['Method']
    throughput = row['Throughput_Mbps']
    improvement = (throughput / baseline - 1) * 100
    marker = " [OPTIMAL]" if method == "Blossom" else ""
    print(f"   - {method:12s} {throughput:.2f} Mbps (+{improvement:.1f}%){marker}")

print(f"\n4. GNN PERFORMANCE vs OPTIMAL:")
gnn_throughput = df[df['Method'] == 'NOMA-GNN']['Throughput_Mbps'].values[0]

if 'Blossom' in df['Method'].values:
    blossom_throughput = df[df['Method'] == 'Blossom']['Throughput_Mbps'].values[0]
    throughput_ratio = gnn_throughput / blossom_throughput
    blos_idx = df[df['Method'] == 'Blossom'].index[0]
    speedup = df.loc[blos_idx, 'Time_ms'] / gnn_time
    print(f"   - Throughput: {throughput_ratio*100:.2f}% of Blossom optimal")
    print(f"   - Throughput gap: {blossom_throughput - gnn_throughput:.2f} Mbps")
    print(f"   - Speed: {speedup:.1f}× faster than Blossom")
else:
    bipartite_throughput = df[df['Method'] == 'Bipartite']['Throughput_Mbps'].values[0]
    throughput_ratio = gnn_throughput / bipartite_throughput
    print(f"   - Throughput: {throughput_ratio*100:.2f}% of Bipartite")
    print(f"   - Throughput gap: {bipartite_throughput - gnn_throughput:.2f} Mbps")
    print(f"   - Note: Run with --full to compare against Blossom optimal")

print(f"\n5. PAIRING EFFICIENCY:")
for idx, row in df.iterrows():
    method = row['Method']
    noma_pairs = int(row['NOMA_Pairs'])
    oma_users = int(row['OMA_Users'])
    efficiency = row['Pairing_Efficiency_%']
    print(f"   - {method:12s} {noma_pairs} NOMA pairs, {oma_users} OMA users ({efficiency:.1f}% paired)")

print(f"\n6. SPECTRAL EFFICIENCY (Avg Sum Rate):")
best_rate = df['Avg_Sum_Rate_bps_Hz'].max()
for idx, row in df.iterrows():
    method = row['Method']
    rate = row['Avg_Sum_Rate_bps_Hz']
    marker = " (BEST)" if rate == best_rate else ""
    print(f"   - {method:12s} {rate:.2f} bits/s/Hz{marker}")

print(f"\n7. BANDWIDTH ALLOCATION:")
print(f"   Fixed: 180 kHz per NOMA pair (OMA users excluded)")
for idx, row in df.iterrows():
    method = row['Method']
    noma_pairs = int(row['NOMA_Pairs'])
    total_bw = noma_pairs * 180  # kHz
    print(f"   - {method:12s} {noma_pairs} pairs × 180 kHz = {total_bw/1000:.1f} MHz total")

print("\n" + "="*90)
print(" RECOMMENDED TEXT FOR PAPER")
print("="*90)

gnn_rate = df[df['Method'] == 'NOMA-GNN']['Avg_Sum_Rate_bps_Hz'].values[0]
n_users = int(df['Users_Served'].iloc[0])  # Get from Users_Served column

if 'Blossom' in df['Method'].values:
    blos_idx = df[df['Method'] == 'Blossom'].index[0]
    bip_idx = df[df['Method'] == 'Bipartite'].index[0]
    speedup_blossom = df.loc[blos_idx, 'Time_ms'] / gnn_time
    speedup_bipartite = df.loc[bip_idx, 'Time_ms'] / gnn_time
    blossom_throughput = df[df['Method'] == 'Blossom']['Throughput_Mbps'].values[0]
    throughput_ratio = gnn_throughput / blossom_throughput
    
    print(f"""
The proposed NOMA-GNN achieves:
- {speedup_bipartite:.1f}× speedup over bipartite matching
- {speedup_blossom:.1f}× speedup over optimal Blossom matching
- {throughput_ratio*100:.1f}% of optimal throughput
- {gnn_rate:.2f} bits/s/Hz average spectral efficiency

For N≈{n_users} users, GNN completes in {gnn_time:.2f} ms compared to 
{df.loc[blos_idx, 'Time_ms']/1000:.2f}s for Blossom, enabling real-time deployment.
""")
else:
    bip_idx = df[df['Method'] == 'Bipartite'].index[0]
    speedup_bipartite = df.loc[bip_idx, 'Time_ms'] / gnn_time
    bipartite_throughput = df[df['Method'] == 'Bipartite']['Throughput_Mbps'].values[0]
    throughput_ratio = gnn_throughput / bipartite_throughput
    
    print(f"""
The proposed NOMA-GNN achieves:
- {speedup_bipartite:.1f}× speedup over bipartite matching
- {throughput_ratio*100:.1f}% of Bipartite throughput
- {gnn_rate:.2f} bits/s/Hz average spectral efficiency

For N≈{n_users} users, GNN completes in {gnn_time:.2f} ms compared to 
{df.loc[bip_idx, 'Time_ms']/1000:.2f}s for Bipartite.

Note: Run with --full to include Blossom optimal baseline.
""")

print("="*90)
