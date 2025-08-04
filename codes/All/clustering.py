# -------------------- Parameters & Initialization --------------------
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import networkx as nx
from tqdm import tqdm
import os
import time
from datetime import datetime
import seaborn as sns
from matplotlib.patches import Circle

# Create timestamped results directory
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results_dir = f"simulation_results/{timestamp}"
os.makedirs(results_dir, exist_ok=True)
os.makedirs("simulation_results", exist_ok=True)

print(f"Results will be saved to: {results_dir}")

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Parameters (Referenced: 3GPP TR 38.901, Chen et al. (2021) IEEE TWC)
np.random.seed(int(time.time()))
N, radius = 500, 5000  # Users and cell radius (m)
fc, c = 3.5e9, 3e8  # Carrier frequency (Hz), Speed of light (m/s)
lambda_c = c / fc  # Wavelength (m)
path_loss_exp, shadow_std_db = 3.5, 8  # Urban macrocell [3GPP TR 38.901]
noise_power, total_power = 1e-9, 1.0  # Noise power and total power budget
sic_threshold_db, B_total = 8, 20e6  # SIC threshold (dB), Total bandwidth (Hz)

# -------------------- User Placement (Uniform Circular) --------------------
r = np.sqrt(np.random.uniform(0, radius**2, N))  # Random radius [Chen et al. 2021]
theta = np.random.uniform(0, 2*np.pi, N)
x_coords, y_coords = r * np.cos(theta), r * np.sin(theta)

# -------------------- Path Loss & Shadowing (3GPP TR 38.901) --------------------
pl_1m_db = 20 * np.log10(4 * np.pi / lambda_c)
shadowing = np.random.normal(0, shadow_std_db, N)
pl_db = pl_1m_db + 10 * path_loss_exp * np.log10(r) + shadowing
pl_linear = 10**(-pl_db/10)

# -------------------- Small-Scale Rayleigh Fading (Chen et al. 2021) --------------------
fading = np.random.rayleigh(scale=1.0, size=N)

# -------------------- Channel Gain Calculation --------------------
h_values = fading * np.sqrt(pl_linear)  # [Chen et al. 2021]
h_db = 10 * np.log10(h_values**2 + 1e-12)

# Sorted indices for clustering
sorted_indices = np.argsort(h_values)

# Save comprehensive user data including coordinates and channel components
user_data = pd.DataFrame({
    "User_ID": np.arange(N),
    "x_coord_m": x_coords,
    "y_coord_m": y_coords,
    "distance_m": r,
    "angle_rad": theta,
    "path_loss_dB": pl_db,
    "path_loss_linear": pl_linear,
    "shadowing_dB": shadowing,
    "rayleigh_fading": fading,
    "h_linear": h_values,
    "h_dB": h_db
})
user_data.to_csv(f"{results_dir}/h_values.csv", index=False)

# -------------------- Visualization Functions --------------------
def plot_user_distribution():
    """Plot user distribution in the cell"""
    plt.figure(figsize=(10, 8))
    
    # Create cell boundary
    circle = plt.Circle((0, 0), radius, fill=False, color='black', linewidth=2, linestyle='--')
    plt.gca().add_patch(circle)
    
    # Scatter plot of users with color-coded channel gains
    scatter = plt.scatter(x_coords, y_coords, c=h_db, cmap='viridis', 
                         s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
    
    plt.colorbar(scatter, label='Channel Gain (dB)')
    plt.xlabel('X Position (m)', fontsize=12)
    plt.ylabel('Y Position (m)', fontsize=12)
    plt.title('User Distribution in Cell with Channel Gains', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(f'{results_dir}/user_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_channel_characteristics():
    """Plot channel gain distributions and characteristics"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Channel gain histogram
    ax1.hist(h_db, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.set_xlabel('Channel Gain (dB)')
    ax1.set_ylabel('Number of Users')
    ax1.set_title('Channel Gain Distribution')
    ax1.grid(True, alpha=0.3)
    
    # Path loss vs distance
    ax2.scatter(r, pl_db, alpha=0.6, color='orange', s=30)
    ax2.set_xlabel('Distance from BS (m)')
    ax2.set_ylabel('Path Loss (dB)')
    ax2.set_title('Path Loss vs Distance')
    ax2.grid(True, alpha=0.3)
    
    # Fading distribution
    ax3.hist(fading, bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
    ax3.set_xlabel('Rayleigh Fading Coefficient')
    ax3.set_ylabel('Number of Users')
    ax3.set_title('Rayleigh Fading Distribution')
    ax3.grid(True, alpha=0.3)
    
    # Sorted channel gains
    ax4.plot(range(N), np.sort(h_db), linewidth=2, color='red')
    ax4.set_xlabel('User Index (Sorted)')
    ax4.set_ylabel('Channel Gain (dB)')
    ax4.set_title('Sorted Channel Gains')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{results_dir}/channel_characteristics.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_pairing_visualization(pairs_indices, name, clustering_data):
    """Visualize user pairing for each clustering method"""
    plt.figure(figsize=(12, 10))
    
    # Create cell boundary
    circle = plt.Circle((0, 0), radius, fill=False, color='black', linewidth=2, linestyle='--')
    plt.gca().add_patch(circle)
    
    # Plot all users
    plt.scatter(x_coords, y_coords, c='lightgray', s=30, alpha=0.5, label='Unpaired Users')
    
    # Plot NOMA pairs with lines
    colors = plt.cm.Set3(np.linspace(0, 1, len(pairs_indices)))
    
    for idx, (u1, u2) in enumerate(pairs_indices):
        h1, h2 = h_values[u1], h_values[u2]
        if sic_satisfied(min(h1, h2), max(h1, h2)):
            plt.plot([x_coords[u1], x_coords[u2]], [y_coords[u1], y_coords[u2]], 
                    color=colors[idx], linewidth=1.5, alpha=0.7)
            plt.scatter([x_coords[u1], x_coords[u2]], [y_coords[u1], y_coords[u2]], 
                       c=[colors[idx]], s=50, edgecolors='black', linewidth=0.5)
    
    plt.xlabel('X Position (m)', fontsize=12)
    plt.ylabel('Y Position (m)', fontsize=12)
    plt.title(f'{name.title()} Clustering - User Pairing Visualization', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(f'{results_dir}/{name}_pairing.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_channel_components_analysis():
    """Plot detailed analysis of individual channel components"""
    # Load the comprehensive user data
    user_data = pd.DataFrame({
        "User_ID": np.arange(N),
        "x_coord_m": x_coords,
        "y_coord_m": y_coords,
        "distance_m": r,
        "angle_rad": theta,
        "path_loss_dB": pl_db,
        "path_loss_linear": pl_linear,
        "shadowing_dB": shadowing,
        "rayleigh_fading": fading,
        "h_linear": h_values,
        "h_dB": h_db
    })
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Distance vs Path Loss (showing path loss model)
    ax1.scatter(user_data['distance_m'], user_data['path_loss_dB'], alpha=0.6, s=20, color='red')
    # Add theoretical path loss line
    dist_theory = np.linspace(100, radius, 100)
    pl_theory = pl_1m_db + 10 * path_loss_exp * np.log10(dist_theory)
    ax1.plot(dist_theory, pl_theory, 'k--', linewidth=2, label='Theoretical Path Loss')
    ax1.set_xlabel('Distance from BS (m)')
    ax1.set_ylabel('Path Loss (dB)')
    ax1.set_title('Path Loss vs Distance (3GPP Model)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Spatial distribution of shadowing
    scatter2 = ax2.scatter(user_data['x_coord_m'], user_data['y_coord_m'], 
                          c=user_data['shadowing_dB'], cmap='RdBu_r', s=30, alpha=0.7)
    circle2 = plt.Circle((0, 0), radius, fill=False, color='black', linewidth=2, linestyle='--')
    ax2.add_patch(circle2)
    plt.colorbar(scatter2, ax=ax2, label='Shadowing (dB)')
    ax2.set_xlabel('X Position (m)')
    ax2.set_ylabel('Y Position (m)')
    ax2.set_title('Spatial Distribution of Shadowing Effects')
    ax2.axis('equal')
    ax2.grid(True, alpha=0.3)
    
    # Channel gain components comparison
    components = ['Path Loss', 'Shadowing', 'Rayleigh Fading', 'Overall Channel']
    # Convert to dB for comparison
    pl_contribution = user_data['path_loss_dB']
    shadowing_contribution = user_data['shadowing_dB'] 
    fading_contribution = 20 * np.log10(user_data['rayleigh_fading'])  # Convert to dB
    overall_gain = user_data['h_dB']
    
    ax3.boxplot([pl_contribution, shadowing_contribution, fading_contribution, overall_gain],
                labels=components)
    ax3.set_ylabel('Magnitude (dB)')
    ax3.set_title('Channel Component Contributions')
    ax3.grid(True, alpha=0.3)
    plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
    
    # Distance vs Overall Channel Gain (showing combined effect)
    ax4.scatter(user_data['distance_m'], user_data['h_dB'], alpha=0.6, s=20, color='green')
    ax4.set_xlabel('Distance from BS (m)')
    ax4.set_ylabel('Overall Channel Gain (dB)')
    ax4.set_title('Distance vs Overall Channel Gain')
    ax4.grid(True, alpha=0.3)
    
    # Add statistics text
    stats_text = f"""
    Statistics:
    Mean distance: {user_data['distance_m'].mean():.0f} m
    Mean path loss: {user_data['path_loss_dB'].mean():.1f} dB
    Shadowing std: {user_data['shadowing_dB'].std():.1f} dB
    Channel gain range: {user_data['h_dB'].min():.1f} to {user_data['h_dB'].max():.1f} dB
    """
    ax4.text(0.02, 0.98, stats_text, transform=ax4.transAxes, fontsize=9,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(f'{results_dir}/channel_components_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_user_positioning_analysis():
    """Plot analysis of user positioning and spatial characteristics"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Radial distribution
    ax1.hist(r, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.set_xlabel('Distance from BS (m)')
    ax1.set_ylabel('Number of Users')
    ax1.set_title('Radial Distribution of Users')
    ax1.grid(True, alpha=0.3)
    
    # Angular distribution
    ax2.hist(theta, bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
    ax2.set_xlabel('Angle (radians)')
    ax2.set_ylabel('Number of Users')
    ax2.set_title('Angular Distribution of Users')
    ax2.grid(True, alpha=0.3)
    
    # Polar plot of user positions
    ax3 = plt.subplot(2, 2, 3, projection='polar')
    scatter3 = ax3.scatter(theta, r, c=h_db, cmap='viridis', s=20, alpha=0.7)
    ax3.set_title('Polar View of User Distribution\n(Color = Channel Gain)')
    plt.colorbar(scatter3, ax=ax3, label='Channel Gain (dB)', shrink=0.8)
    
    # Distance vs angle with channel quality
    scatter4 = ax4.scatter(theta * 180/np.pi, r, c=h_db, cmap='viridis', s=30, alpha=0.7)
    ax4.set_xlabel('Angle (degrees)')
    ax4.set_ylabel('Distance from BS (m)')
    ax4.set_title('User Positions (Angle vs Distance)')
    plt.colorbar(scatter4, ax=ax4, label='Channel Gain (dB)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{results_dir}/user_positioning_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_clustering_comparison():
    """Compare performance of different clustering methods"""
    # Read results from CSV files
    methods = ['static', 'balanced', 'blossom']
    results = {}
    
    for method in methods:
        try:
            df = pd.read_csv(f'{results_dir}/{method}_clustering.csv')
            noma_pairs = df[df['Mode'] == 'NOMA']
            oma_users = df[df['Mode'] == 'OMA']
            
            results[method] = {
                'total_throughput': df['Throughput_Mbps'].sum(),
                'noma_pairs': len(noma_pairs),
                'oma_users': len(oma_users),
                'avg_noma_rate': noma_pairs['R_sum_bitsHz'].mean() if len(noma_pairs) > 0 else 0,
                'avg_oma_rate': oma_users['R_sum_bitsHz'].mean() if len(oma_users) > 0 else 0
            }
        except FileNotFoundError:
            continue
    
    if not results:
        return
    
    # Create comparison plots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Total throughput comparison
    methods_list = list(results.keys())
    throughputs = [results[m]['total_throughput'] for m in methods_list]
    bars1 = ax1.bar(methods_list, throughputs, color=['skyblue', 'lightgreen', 'orange'])
    ax1.set_ylabel('Total Throughput (Mbps)')
    ax1.set_title('Total System Throughput Comparison')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars1, throughputs):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(throughputs)*0.01,
                f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # NOMA vs OMA distribution
    noma_counts = [results[m]['noma_pairs'] for m in methods_list]
    oma_counts = [results[m]['oma_users'] for m in methods_list]
    
    x = np.arange(len(methods_list))
    width = 0.35
    
    bars2 = ax2.bar(x - width/2, noma_counts, width, label='NOMA Pairs', color='coral')
    bars3 = ax2.bar(x + width/2, oma_counts, width, label='OMA Users', color='lightblue')
    
    ax2.set_xlabel('Clustering Method')
    ax2.set_ylabel('Number of Users/Pairs')
    ax2.set_title('NOMA vs OMA User Distribution')
    ax2.set_xticks(x)
    ax2.set_xticklabels(methods_list)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Average rates comparison
    avg_noma_rates = [results[m]['avg_noma_rate'] for m in methods_list]
    avg_oma_rates = [results[m]['avg_oma_rate'] for m in methods_list]
    
    bars4 = ax3.bar(x - width/2, avg_noma_rates, width, label='Avg NOMA Rate', color='mediumseagreen')
    bars5 = ax3.bar(x + width/2, avg_oma_rates, width, label='Avg OMA Rate', color='plum')
    
    ax3.set_xlabel('Clustering Method')
    ax3.set_ylabel('Average Rate (bits/Hz)')
    ax3.set_title('Average Data Rates Comparison')
    ax3.set_xticks(x)
    ax3.set_xticklabels(methods_list)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Performance summary pie chart
    method_colors = ['skyblue', 'lightgreen', 'orange']
    ax4.pie(throughputs, labels=methods_list, colors=method_colors, autopct='%1.1f%%', startangle=90)
    ax4.set_title('Throughput Share by Method')
    
    plt.tight_layout()
    plt.savefig(f'{results_dir}/clustering_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save summary statistics
    summary_data = []
    for method in methods_list:
        summary_data.append({
            'Method': method.title(),
            'Total_Throughput_Mbps': results[method]['total_throughput'],
            'NOMA_Pairs': results[method]['noma_pairs'],
            'OMA_Users': results[method]['oma_users'],
            'Avg_NOMA_Rate_bitsHz': results[method]['avg_noma_rate'],
            'Avg_OMA_Rate_bitsHz': results[method]['avg_oma_rate'],
            'NOMA_Percentage': (results[method]['noma_pairs'] * 2) / N * 100
        })
    
    pd.DataFrame(summary_data).to_csv(f'{results_dir}/clustering_summary.csv', index=False)

# -------------------- SIC Rate Calculation --------------------
def calc_pair_rate(h1, h2):
    P1, P2 = total_power * h2 / (h1 + h2), total_power * h1 / (h1 + h2)
    R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))
    R2 = np.log2(1 + (P2 * h2) / noise_power)
    return P1, P2, R1, R2, R1 + R2

# -------------------- SIC Condition Check --------------------
def sic_satisfied(h1, h2):
    return 10 * np.log10(h2 / h1) >= sic_threshold_db

# -------------------- Clustering Common Function --------------------
def perform_clustering(pairs_indices, name):
    """
    Perform clustering with given pair indices and save results with visualizations
    
    Args:
        pairs_indices: List of tuples representing user pairs
        name: String identifier for the clustering method
    
    Returns:
        Dictionary containing performance metrics
    """
    data, used = [], np.zeros(N, bool)
    total_rate = 0
    noma_pairs_count = 0

    print(f"\n--- {name.title()} Clustering ---")
    print(f"Evaluating {len(pairs_indices)} potential pairs...")
    
    for u1, u2 in tqdm(pairs_indices, desc=f"Processing {name} pairs"):
        h1, h2 = h_values[u1], h_values[u2]
        if sic_satisfied(min(h1, h2), max(h1, h2)):
            P1, P2, R1, R2, R_sum = calc_pair_rate(min(h1, h2), max(h1, h2))
            used[[u1, u2]] = True
            data.append([u1, u2, h1, h2, P1, P2, R1, R2, R_sum, "NOMA"])
            total_rate += R_sum
            noma_pairs_count += 1

    num_pairs, num_oma = len(data), N - 2 * len(data)
    B_pair = B_total / (num_pairs + num_oma)
    throughput_total = 0

    # Calculate throughput for NOMA pairs
    for row in data:
        row.append(row[8] * B_pair / 1e6)
        throughput_total += row[-1]

    # Handle remaining OMA users
    oma_users_count = 0
    for u in range(N):
        if not used[u]:
            h = h_values[u]
            R1_oma = np.log2(1 + total_power * h / noise_power)
            throughput = R1_oma * B_pair / 1e6
            throughput_total += throughput
            data.append([u, -1, h, 0, total_power, 0, R1_oma, 0, R1_oma, "OMA", throughput])
            oma_users_count += 1

    # Save results
    save_name = f"{results_dir}/{name}_clustering.csv"
    cols = ["User1_ID", "User2_ID", "h1", "h2", "P1", "P2", "R1_bitsHz", "R2_bitsHz", "R_sum_bitsHz", "Mode", "Throughput_Mbps"]
    pd.DataFrame(data, columns=cols).to_csv(save_name, index=False)
    
    # Print performance summary
    print(f"NOMA Pairs: {noma_pairs_count}")
    print(f"OMA Users: {oma_users_count}")
    print(f"Total Throughput: {throughput_total:.2f} Mbps")
    print(f"NOMA Coverage: {(noma_pairs_count * 2)/N*100:.1f}%")
    
    # Generate pairing visualization
    plot_pairing_visualization(pairs_indices, name, data)
    
    return {
        'noma_pairs': noma_pairs_count,
        'oma_users': oma_users_count,
        'total_throughput': throughput_total,
        'noma_coverage': (noma_pairs_count * 2)/N*100
    }

# -------------------- Main Execution with Visualizations --------------------
print("="*60)
print("NOMA CLUSTERING SIMULATION AND ANALYSIS")
print("="*60)
print(f"System Parameters:")
print(f"- Number of Users: {N}")
print(f"- Cell Radius: {radius} m")
print(f"- Carrier Frequency: {fc/1e9:.1f} GHz")
print(f"- SIC Threshold: {sic_threshold_db} dB")
print(f"- Total Bandwidth: {B_total/1e6:.0f} MHz")

# Generate initial visualizations
print("\nGenerating channel analysis plots...")
plot_user_distribution()
plot_channel_characteristics()
plot_channel_components_analysis()
plot_user_positioning_analysis()

# Store results for comparison
clustering_results = {}

# -------------------- Static Clustering --------------------
print("\n" + "="*50)
static_indices = [(sorted_indices[i], sorted_indices[N-1-i]) for i in range(N//2)]
clustering_results['static'] = perform_clustering(static_indices, "static")

# -------------------- Balanced Clustering --------------------
print("\n" + "="*50)
balanced_indices = [(sorted_indices[i], sorted_indices[i + N//2]) for i in range(N//2)]
clustering_results['balanced'] = perform_clustering(balanced_indices, "balanced")

# -------------------- Blossom Clustering --------------------
print("\n" + "="*50)
print("Blossom Clustering")
print("Building maximum weight matching graph...")
G = nx.Graph()
edge_count = 0

for i in tqdm(range(N), desc="Building graph"):
    for j in range(i+1, N):
        if sic_satisfied(min(h_values[i], h_values[j]), max(h_values[i], h_values[j])):
            _, _, _, _, R_sum = calc_pair_rate(min(h_values[i], h_values[j]), max(h_values[i], h_values[j]))
            G.add_edge(i, j, weight=R_sum)
            edge_count += 1

print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

blossom_indices = list(nx.max_weight_matching(G, maxcardinality=True))
clustering_results['blossom'] = perform_clustering(blossom_indices, "blossom")

# -------------------- Generate Comparison Plots --------------------
print("\n" + "="*50)
print("Generating comparison analysis...")
plot_clustering_comparison()

# -------------------- Final Summary --------------------
print("\n" + "="*60)
print("SIMULATION SUMMARY")
print("="*60)

for method, results in clustering_results.items():
    print(f"\n{method.upper()} CLUSTERING:")
    print(f"  - NOMA Pairs: {results['noma_pairs']}")
    print(f"  - OMA Users: {results['oma_users']}")
    print(f"  - Total Throughput: {results['total_throughput']:.2f} Mbps")
    print(f"  - NOMA Coverage: {results['noma_coverage']:.1f}%")

# Find best performing method
best_method = max(clustering_results.keys(), 
                 key=lambda x: clustering_results[x]['total_throughput'])
print(f"\nBEST PERFORMING METHOD: {best_method.upper()}")
print(f"Throughput: {clustering_results[best_method]['total_throughput']:.2f} Mbps")

print(f"\nAll results and visualizations saved to '{results_dir}/' directory")
print("Simulation completed successfully!")
print("="*60)
