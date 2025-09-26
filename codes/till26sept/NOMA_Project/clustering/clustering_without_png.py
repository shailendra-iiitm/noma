# -------------------- Parameters & Initialization --------------------
import numpy as np
import pandas as pd
import networkx as nx
from tqdm import tqdm
import os
import time
from datetime import datetime

# Parameters (Referenced: 3GPP TR 38.901, Section 7.4.1 & 7.4.2, UMa scenario)
np.random.seed(int(time.time()))
N, radius = 1100, 5000  # Users, cell radius (m)
fc, c = 3.5e9, 3e8  # Carrier frequency (Hz), speed of light (m/s)
lambda_c = c / fc  # Wavelength (m)
h_BS = 25  # Base station height (m)
path_loss_exp, shadow_std_db = 3.5, 8
noise_power, total_power = 1e-9, 1.0
sic_threshold_db, B_total = 8, 20e6

# Create main results directory and timestamped subdirectory
main_results_dir = "results"
os.makedirs(main_results_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results_dir = os.path.join(main_results_dir, f"results_{timestamp}")
os.makedirs(results_dir, exist_ok=True)
print(f"Results will be saved to: {results_dir}")

# Path loss reference (1m reference distance)
pl_1m_db = 20 * np.log10(4 * np.pi / lambda_c)

# -------------------- User Placement --------------------
# Generate random positions uniformly in circular cell
r = np.sqrt(np.random.uniform(0, radius**2, N))  # 2D distance from BS
theta = np.random.uniform(0, 2*np.pi, N)
x_coords, y_coords = r * np.cos(theta), r * np.sin(theta)

# Random UE heights within 3GPP UMa limits (1.5m – 22.5m)
h_UTs = np.random.uniform(1.5, 22.5, N)

# -------------------- LOS Probability (3GPP Eq. 7.4.2-1) --------------------
def C_hUT(h_UT):
    if h_UT <= 13:
        return 0
    elif h_UT < 23:
        return ((h_UT - 13) / 10) ** 1.5
    else:
        return ((23 - 13) / 10) ** 1.5

def prob_LOS_UMa(d_2D_out, h_UT):
    P_LOS = np.zeros_like(d_2D_out, dtype=float)
    mask1 = d_2D_out <= 18
    P_LOS[mask1] = 1.0
    mask2 = ~mask1
    C_val = np.array([C_hUT(h) for h in h_UT])
    P_LOS[mask2] = (
        (18 / d_2D_out[mask2]) +
        np.exp(-d_2D_out[mask2] / 63) * (1 - 18 / d_2D_out[mask2])
    ) * (
        1 + C_val[mask2] * (5/4) * ((d_2D_out[mask2] / 100) ** 3) *
        np.exp(-d_2D_out[mask2] / 150)
    )
    return np.clip(P_LOS, 0, 1)

# -------------------- Path Loss Models --------------------
def PL_UMa_LOS(d_3D, fc):
    return 28.0 + 22 * np.log10(d_3D) + 20 * np.log10(fc / 1e9)

def PL_UMa_NLOS(d_3D, fc, h_UT):
    return 13.54 + 39.08 * np.log10(d_3D) + 20 * np.log10(fc / 1e9) - \
           0.6 * (h_UT - 1.5)

# -------------------- Generate Path Loss for Each User --------------------
d_3D = np.sqrt(r**2 + (h_BS - h_UTs)**2)
P_LOS_users = prob_LOS_UMa(r, h_UTs)

# Initialize path loss arrays
PL_dB_no_shadow = np.zeros(N)  # Path loss without shadowing
PL_dB = np.zeros(N)  # Path loss with shadowing
is_LOS = np.zeros(N, dtype=bool)

for i in range(N):
    if np.random.rand() <= P_LOS_users[i]:
        PL_dB_no_shadow[i] = PL_UMa_LOS(d_3D[i], fc)
        is_LOS[i] = True
    else:
        # FIXED: Apply 3GPP rule exactly - NLOS path loss is max of LOS and NLOS formulas
        PL_LOS_val = PL_UMa_LOS(d_3D[i], fc)
        PL_NLOS_val = PL_UMa_NLOS(d_3D[i], fc, h_UTs[i])
        PL_dB_no_shadow[i] = max(PL_LOS_val, PL_NLOS_val)
        is_LOS[i] = False

# Convert PL to linear scale (without shadowing)
pl_linear = 10 ** (-PL_dB_no_shadow / 10)

# -------------------- Shadowing --------------------
shadowing = np.random.normal(0, shadow_std_db, N)  # Log-normal shadowing in dB

# FIXED: Apply shadowing to path loss properly (only once)
PL_dB = PL_dB_no_shadow + shadowing  # Path loss with shadowing

# -------------------- Small-Scale Fading --------------------
fading = np.zeros(N)
K_factor_LOS = 9  # Typical UMa LOS Rician K-factor in dB
K_linear = 10 ** (K_factor_LOS / 10)

for i in range(N):
    if is_LOS[i]:
        # Rician fading for LOS users
        s = np.sqrt(K_linear / (K_linear + 1))
        sigma = np.sqrt(1 / (2 * (K_linear + 1)))
        complex_fading = np.random.normal(s, sigma) + 1j * np.random.normal(0, sigma)
        fading[i] = np.abs(complex_fading)
    else:
        # Rayleigh fading for NLOS users
        fading[i] = np.random.rayleigh(scale=1.0)

# -------------------- Channel Gain --------------------
# FIXED: Combine path loss (with shadowing) and fading correctly
pl_with_shadowing_linear = 10 ** (-PL_dB / 10)
h_values = fading * np.sqrt(pl_with_shadowing_linear)

# FIXED: Correct dB conversion for channel gains
h_db = 20 * np.log10(h_values + 1e-12)  # Use 20*log10 for magnitude, not power

# Create alias for consistent naming
pl_db = PL_dB

# Sorted indices for clustering
sorted_indices = np.argsort(h_values)

# Save comprehensive user data including coordinates and channel components
user_data = pd.DataFrame({
    "User_ID": np.arange(N),
    "x_coord_m": x_coords,
    "y_coord_m": y_coords,
    "distance_m": r,
    "angle_rad": theta,
    "height_m": h_UTs,
    "distance_3D_m": d_3D,
    "LOS_status": is_LOS,
    "LOS_probability": P_LOS_users,
    "path_loss_dB_no_shadow": PL_dB_no_shadow,  # Path loss without shadowing
    "path_loss_dB": pl_db,  # Path loss with shadowing
    "path_loss_linear": pl_linear,
    "shadowing_dB": shadowing,
    "rayleigh_fading": fading,
    "h_linear": h_values,
    "h_dB": h_db
})
user_data.to_csv(f"{results_dir}/h_values.csv", index=False)

print(f"Channel generation completed successfully!")
print(f"Number of LOS users: {np.sum(is_LOS)}")
print(f"Number of NLOS users: {np.sum(~is_LOS)}")
print(f"Channel gain range: {h_db.min():.2f} to {h_db.max():.2f} dB")

# Validate channel modeling (debugging info)
print(f"\nChannel Modeling Validation:")
print(f"Path loss range (no shadow): {PL_dB_no_shadow.min():.1f} to {PL_dB_no_shadow.max():.1f} dB")
print(f"Path loss range (with shadow): {PL_dB.min():.1f} to {PL_dB.max():.1f} dB")
print(f"Shadowing range: {shadowing.min():.1f} to {shadowing.max():.1f} dB")
print(f"Fading range: {fading.min():.3f} to {fading.max():.3f}")

# -------------------- SIC Condition Check --------------------
def sic_satisfied(h1, h2):
    """
    Check if SIC decoding is possible for a pair of users
    Args:
        h1, h2: Channel gains of two users
    Returns:
        Boolean indicating if SIC is satisfied
    """
    # Determine strong and weak users
    if h1 > h2:
        h_strong, h_weak = h1, h2
    else:
        h_strong, h_weak = h2, h1
    
    # Power allocation: more power to weak user
    P_weak = total_power * h_strong / (h_strong + h_weak)
    P_strong = total_power * h_weak / (h_strong + h_weak)
    
    # SINR at strong user when decoding weak user's signal
    SINR = (h_strong * P_weak) / (h_strong * P_strong + noise_power)
    SINR_dB = 10 * np.log10(SINR)
    
    return SINR_dB >= sic_threshold_db

# -------------------- SIC Rate Calculation --------------------
def calc_pair_rate(h1, h2):
    """
    Calculate rates for a NOMA pair
    Args:
        h1, h2: Channel gains (h1 should be weak user, h2 should be strong user)
    Returns:
        P1, P2, R1, R2, R_sum
    """
    # Ensure h1 <= h2 (h1 is weak user, h2 is strong user)
    if h1 > h2:
        h1, h2 = h2, h1
    
    # Power allocation: more power to weak user
    P1 = total_power * h2 / (h1 + h2)  # Power for weak user
    P2 = total_power * h1 / (h1 + h2)  # Power for strong user
    
    # Rate calculations
    R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))  # Weak user rate
    R2 = np.log2(1 + (P2 * h2) / noise_power)  # Strong user rate after SIC
    
    return P1, P2, R1, R2, R1 + R2

# -------------------- Clustering Common Function --------------------
def perform_clustering(pairs_indices, name):
    """
    Perform clustering with given pair indices and save results with comprehensive calculations
    
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
        if used[u1] or used[u2]:  # Skip if either user is already paired
            continue
            
        h1, h2 = h_values[u1], h_values[u2]
        if h1 > h2:
            h_strong, h_weak = h1, h2
        else:
            h_strong, h_weak = h2, h1

        if sic_satisfied(h1, h2):
            P1, P2, R1, R2, R_sum = calc_pair_rate(h_weak, h_strong)
            used[[u1, u2]] = True
            
            # Comprehensive calculations for User 1
            d_2D_u1 = r[u1]
            h_UT_u1 = h_UTs[u1]
            d_3D_u1 = d_3D[u1]
            LOS_status_u1 = is_LOS[u1]
            channel_type_u1 = "LOS" if LOS_status_u1 else "NLOS"
            PL_dB_u1 = PL_dB[u1]
            PL_dB_no_shadow_u1 = PL_dB_no_shadow[u1]
            PL_linear_u1 = pl_linear[u1]
            shadowing_dB_u1 = shadowing[u1]
            fading_u1 = fading[u1]
            prob_LOS_u1 = P_LOS_users[u1]
            
            # Comprehensive calculations for User 2
            d_2D_u2 = r[u2]
            h_UT_u2 = h_UTs[u2]
            d_3D_u2 = d_3D[u2]
            LOS_status_u2 = is_LOS[u2]
            channel_type_u2 = "LOS" if LOS_status_u2 else "NLOS"
            PL_dB_u2 = PL_dB[u2]
            PL_dB_no_shadow_u2 = PL_dB_no_shadow[u2]
            PL_linear_u2 = pl_linear[u2]
            shadowing_dB_u2 = shadowing[u2]
            fading_u2 = fading[u2]
            prob_LOS_u2 = P_LOS_users[u2]
            
            # For more accurate reporting, use actual SINR for margin
            P_weak = total_power * h_strong / (h_strong + h_weak)
            P_strong = total_power * h_weak / (h_strong + h_weak)
            SINR = (h_strong * P_weak) / (h_strong * P_strong + noise_power)
            sic_margin_dB = 10 * np.log10(SINR)
            sic_satisfied_flag = sic_margin_dB >= sic_threshold_db
            
            data.append([
                u1, u2, h1, h2, P1, P2, R1, R2, R_sum, "NOMA",
                # User 1 detailed calculations
                d_2D_u1, h_UT_u1, d_3D_u1, LOS_status_u1, channel_type_u1, 
                PL_dB_no_shadow_u1, PL_dB_u1, PL_linear_u1, shadowing_dB_u1, fading_u1, prob_LOS_u1,
                # User 2 detailed calculations  
                d_2D_u2, h_UT_u2, d_3D_u2, LOS_status_u2, channel_type_u2,
                PL_dB_no_shadow_u2, PL_dB_u2, PL_linear_u2, shadowing_dB_u2, fading_u2, prob_LOS_u2,
                # SIC analysis
                sic_margin_dB, sic_satisfied_flag
            ])
            total_rate += R_sum
            noma_pairs_count += 1

    num_pairs, num_oma = len(data), N - 2 * len(data)
    B_pair = B_total / (num_pairs + num_oma) if (num_pairs + num_oma) > 0 else B_total
    throughput_total = 0

    # Calculate throughput for NOMA pairs
    for row in data:
        throughput = row[8] * B_pair / 1e6  # R_sum * bandwidth in Mbps
        row.append(throughput)  # Add throughput as last column
        throughput_total += throughput

    # Handle remaining OMA users
    oma_users_count = 0
    for u in range(N):
        if not used[u]:
            h = h_values[u]
            R1_oma = np.log2(1 + total_power * h / noise_power)
            throughput = R1_oma * B_pair / 1e6
            throughput_total += throughput
            
            # Comprehensive calculations for OMA user
            d_2D_u = r[u]
            h_UT_u = h_UTs[u]
            d_3D_u = d_3D[u]
            LOS_status_u = is_LOS[u]
            channel_type_u = "LOS" if LOS_status_u else "NLOS"
            PL_dB_u = PL_dB[u]
            PL_dB_no_shadow_u = PL_dB_no_shadow[u]
            PL_linear_u = pl_linear[u]
            shadowing_dB_u = shadowing[u]
            fading_u = fading[u]
            prob_LOS_u = P_LOS_users[u]
            
            data.append([
                u, -1, h, 0, total_power, 0, R1_oma, 0, R1_oma, "OMA",
                # User detailed calculations
                d_2D_u, h_UT_u, d_3D_u, LOS_status_u, channel_type_u,
                PL_dB_no_shadow_u, PL_dB_u, PL_linear_u, shadowing_dB_u, fading_u, prob_LOS_u,
                # User 2 (empty for OMA)
                -1, -1, -1, False, "N/A", -1, -1, -1, -1, -1, -1,
                # SIC analysis (N/A for OMA)
                -1, False, throughput
            ])
            oma_users_count += 1

    # Save results with comprehensive column headers
    save_name = f"{results_dir}/{name}_clustering.csv"
    cols = [
        "User1_ID", "User2_ID", "h1", "h2", "P1", "P2", "R1_bitsHz", "R2_bitsHz", "R_sum_bitsHz", "Mode",
        # User 1 detailed calculations
        "U1_Distance_2D_m", "U1_Height_m", "U1_Distance_3D_m", "U1_LOS_Status", "U1_Channel_Type",
        "U1_PathLoss_NoShadow_dB", "U1_PathLoss_dB", "U1_PathLoss_Linear", "U1_Shadowing_dB", "U1_Fading", "U1_LOS_Probability",
        # User 2 detailed calculations
        "U2_Distance_2D_m", "U2_Height_m", "U2_Distance_3D_m", "U2_LOS_Status", "U2_Channel_Type", 
        "U2_PathLoss_NoShadow_dB", "U2_PathLoss_dB", "U2_PathLoss_Linear", "U2_Shadowing_dB", "U2_Fading", "U2_LOS_Probability",
        # SIC analysis
        "SIC_Margin_dB", "SIC_Satisfied", "Throughput_Mbps"
    ]
    pd.DataFrame(data, columns=cols).to_csv(save_name, index=False)
    
    # Print performance summary
    print(f"NOMA Pairs: {noma_pairs_count}")
    print(f"OMA Users: {oma_users_count}")
    print(f"Total Throughput: {throughput_total:.2f} Mbps")
    print(f"NOMA Coverage: {(noma_pairs_count * 2)/N*100:.1f}%")
    
    return {
        'noma_pairs': noma_pairs_count,
        'oma_users': oma_users_count,
        'total_throughput': throughput_total,
        'noma_coverage': (noma_pairs_count * 2)/N*100
    }

def generate_clustering_summary(clustering_results):
    """Generate summary statistics CSV"""
    summary_data = []
    for method, results in clustering_results.items():
        summary_data.append({
            'Method': method.title(),
            'Total_Throughput_Mbps': results['total_throughput'],
            'NOMA_Pairs': results['noma_pairs'],
            'OMA_Users': results['oma_users'],
            'NOMA_Percentage': results['noma_coverage'],
            'Avg_Throughput_Per_User_Mbps': results['total_throughput'] / N
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(f'{results_dir}/clustering_summary.csv', index=False)
    print("Clustering summary CSV saved successfully!")
    return summary_df

# -------------------- Main Execution --------------------
print("="*60)
print("NOMA CLUSTERING SIMULATION AND ANALYSIS (CSV ONLY)")
print("="*60)
print(f"System Parameters:")
print(f"- Number of Users: {N}")
print(f"- Cell Radius: {radius} m")
print(f"- Carrier Frequency: {fc/1e9:.1f} GHz")
print(f"- SIC Threshold: {sic_threshold_db} dB")
print(f"- Total Bandwidth: {B_total/1e6:.0f} MHz")

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
        h1, h2 = h_values[i], h_values[j]
        
        if sic_satisfied(h1, h2):
            _, _, _, _, R_sum = calc_pair_rate(min(h1, h2), max(h1, h2))
            G.add_edge(i, j, weight=R_sum)
            edge_count += 1

print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

if G.number_of_edges() > 0:
    blossom_indices = list(nx.max_weight_matching(G, maxcardinality=True))
    clustering_results['blossom'] = perform_clustering(blossom_indices, "blossom")
else:
    print("No valid pairs found for Blossom clustering!")
    clustering_results['blossom'] = {'noma_pairs': 0, 'oma_users': N, 'total_throughput': 0, 'noma_coverage': 0}

# -------------------- Generate Summary --------------------
print("\n" + "="*50)
print("Generating summary analysis...")
summary_df = generate_clustering_summary(clustering_results)

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
    print(f"  - Avg Throughput/User: {results['total_throughput']/N:.3f} Mbps")

# Find best performing method
if clustering_results:
    best_method = max(clustering_results.keys(), 
                     key=lambda x: clustering_results[x]['total_throughput'])
    print(f"\nBEST PERFORMING METHOD: {best_method.upper()}")
    print(f"Throughput: {clustering_results[best_method]['total_throughput']:.2f} Mbps")

print(f"\nFiles generated:")
print(f"- h_values.csv: User channel data")
print(f"- static_clustering.csv: Static clustering results")
print(f"- balanced_clustering.csv: Balanced clustering results")
print(f"- blossom_clustering.csv: Blossom clustering results")
print(f"- clustering_summary.csv: Performance comparison")
print(f"\nAll results saved to '{results_dir}/' directory")
print("Simulation completed successfully!")
print("="*60)
