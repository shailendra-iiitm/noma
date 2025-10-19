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

# ==================== SIMULATION CONFIGURATION FOR GOOGLE COLAB ====================
NUM_SIMULATIONS = 100       # Number of automatic simulation runs
SAVE_PLOTS_INTERVAL = 10    # Save detailed plots every N simulations (to save storage)
QUIET_MODE = True           # Reduce output for batch processing
SAVE_AGGREGATE_RESULTS = True  # Save aggregated results across all runs
# ================================================================================

# Parameters (Referenced: 3GPP TR 38.901, Section 7.4.1 & 7.4.2, UMa scenario)
# European Telecommunications Standards Institute
# https://www.etsi.org/deliver/etsi_tr/138900_138999/138901/16.01.00_60/tr_138901v160100p.pdf?

N, radius = 500, 5000  # Users, cell radius (m)
fc, c = 3.5e9, 3e8  # Carrier frequency (Hz), speed of light (m/s)
lambda_c = c / fc  # Wavelength (m)
h_BS = 25  # Base station height (m)
path_loss_exp, shadow_std_db = 3.5, 8
noise_power, total_power = 1e-9, 1.0
sic_threshold_db, B_total = 8, 20e6

# ==================== BATCH SIMULATION CONFIGURATION ====================
NUM_SIMULATIONS = 100       # Number of automatic simulation runs
SAVE_DETAILED_PLOTS = False # Save detailed plots for each run (set False to save space)
QUIET_MODE = True           # Reduce output for batch processing
SAVE_AGGREGATE_RESULTS = True  # Save aggregated results across all runs
# ====================================================================

# ==================== NEW: Matching/Power Optimization Knobs ====================
THETA_MIN_DEG = 25          # Angular guard for pairing (bipartite PF) in degrees
PF_EPS = 1e-12              # Small epsilon for PF logs to avoid -inf
POWER_OPT_TOL = 1e-4        # Tolerance for 1-D power optimizer
POWER_OPT_MAXIT = 80        # Maximum iterations for 1-D power optimizer
CHANNEL_GAIN_EPS = 1e-12    # Small epsilon for channel gain log calculation
# ================================================================================

# Path loss reference (1m reference distance)
pl_1m_db = 20 * np.log10(4 * np.pi / lambda_c)

# -------------------- SIMULATION SETUP FUNCTION --------------------
def setup_simulation_run(run_id, base_results_dir="results"):
    """Setup a single simulation run with unique random seed and directory"""
    # Set unique random seed for each run
    np.random.seed(run_id + int(time.time()))
    
    # Create timestamped results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = os.path.join(base_results_dir, f"run_{run_id:03d}_{timestamp}")
    os.makedirs(results_dir, exist_ok=True)
    
    # User Placement
    r = np.sqrt(np.random.uniform(0, radius**2, N))  # 2D distance from BS
    theta = np.random.uniform(0, 2*np.pi, N)
    x_coords, y_coords = r * np.cos(theta), r * np.sin(theta)
    
    # Random UE heights within 3GPP UMa limits (1.5m – 22.5m)
    h_UTs = np.random.uniform(1.5, 22.5, N)
    
    return results_dir, r, theta, x_coords, y_coords, h_UTs

# -------------------- CHANNEL GENERATION FUNCTION --------------------
def generate_channel_data(r, theta, x_coords, y_coords, h_UTs):
    """Generate complete channel data for given user positions"""
    # -------------------- LOS Probability (3GPP Eq. 7.4.2-1) --------------------
    d_3D = np.sqrt(r**2 + (h_BS - h_UTs)**2)
    P_LOS_users = prob_LOS_UMa(r, h_UTs)
    
    PL_dB = np.zeros(N)
    is_LOS = np.zeros(N, dtype=bool)
    
    for i in range(N):
        if np.random.rand() <= P_LOS_users[i]:
            PL_dB[i] = PL_UMa_LOS(d_3D[i], fc)
            is_LOS[i] = True
        else:
            PL_dB[i] = PL_UMa_NLOS(d_3D[i], fc, h_UTs[i])
            is_LOS[i] = False
    
    # Convert PL to linear scale
    pl_linear = 10 ** (-PL_dB / 10)
    
    # Shadowing
    shadowing = np.random.normal(0, shadow_std_db, N)
    
    # Small-Scale Fading
    fading = np.zeros(N)
    K_factor_LOS = 9
    K_linear = 10 ** (K_factor_LOS / 10)
    
    for i in range(N):
        if is_LOS[i]:
            s = np.sqrt(K_linear / (K_linear + 1))
            sigma = np.sqrt(1 / (2 * (K_linear + 1)))
            complex_fading = np.random.normal(s, sigma) + 1j * np.random.normal(0, sigma)
            fading[i] = np.abs(complex_fading)
        else:
            fading[i] = np.random.rayleigh(scale=1/np.sqrt(2))
    
    # Channel Gain
    channel_gain_linear = fading * np.sqrt(pl_linear * 10**(-shadowing/10))
    h_values = channel_gain_linear
    h_db = 20 * np.log10(h_values + CHANNEL_GAIN_EPS)
    
    # Create consistent path loss variable name
    path_loss_db = PL_dB
    
    # Sorted indices for clustering
    sorted_indices = np.argsort(h_values)
    
    return {
        'h_values': h_values,
        'h_db': h_db,
        'path_loss_db': path_loss_db,
        'pl_linear': pl_linear,
        'shadowing': shadowing,
        'fading': fading,
        'sorted_indices': sorted_indices,
        'r': r,
        'theta': theta,
        'x_coords': x_coords,
        'y_coords': y_coords,
        'h_UTs': h_UTs
    }

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
    return (13.54 + 39.08 * np.log10(d_3D) + 20 * np.log10(fc / 1e9) - 
            0.6 * (h_UT - 1.5))

# -------------------- Generate Path Loss for Each User --------------------
d_3D = np.sqrt(r*2 + (h_BS - h_UTs)*2)
P_LOS_users = prob_LOS_UMa(r, h_UTs)

PL_dB = np.zeros(N)
is_LOS = np.zeros(N, dtype=bool)

for i in range(N):
    if np.random.rand() <= P_LOS_users[i]:
        PL_dB[i] = PL_UMa_LOS(d_3D[i], fc)
        is_LOS[i] = True
    else:
        # FIXED: Use only NLOS model for NLOS condition
        PL_dB[i] = PL_UMa_NLOS(d_3D[i], fc, h_UTs[i])
        is_LOS[i] = False

# Convert PL to linear scale
pl_linear = 10 ** (-PL_dB / 10)

# -------------------- Shadowing --------------------
shadowing = np.random.normal(0, shadow_std_db, N)  # Log-normal shadowing in dB

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
        # Rayleigh fading for NLOS users - using standard scale
        fading[i] = np.random.rayleigh(scale=1/np.sqrt(2))

# -------------------- Channel Gain --------------------
# Combine path loss, shadowing, and fading components correctly
channel_gain_linear = fading * np.sqrt(pl_linear * 10**(-shadowing/10))
h_values = channel_gain_linear
h_db = 20 * np.log10(h_values + CHANNEL_GAIN_EPS)  # Convert to dB with small epsilon

# Debug prints
print(f"\nChannel Statistics:")
print(f"3D Distance range: {np.min(d_3D):.1f} - {np.max(d_3D):.1f} m")
print(f"Path Loss range: {np.min(PL_dB):.1f} - {np.max(PL_dB):.1f} dB")
print(f"Fading range: {np.min(fading):.3f} - {np.max(fading):.3f}")
print(f"Channel Gain range: {np.min(h_db):.1f} - {np.max(h_db):.1f} dB")

# Verify with theoretical values
d_test = 1000  # Test at 1km
pl_theoretical = 28 + 22*np.log10(d_test) + 20*np.log10(fc/1e9)
print(f"Theoretical PL at 1km: {pl_theoretical:.1f} dB")

# Create consistent path loss variable name for visualization functions
path_loss_db = PL_dB

# Channel values are now ready for clustering

# Sorted indices for clustering
sorted_indices = np.argsort(h_values)

# Save comprehensive user data including coordinates and channel components
user_data = pd.DataFrame({
    "User_ID": np.arange(N),
    "x_coord_m": x_coords,
    "y_coord_m": y_coords,
    "distance_m": r,
    "angle_rad": theta,
    "path_loss_dB": path_loss_db,
    "path_loss_linear": pl_linear,
    "shadowing_dB": shadowing,
    "rayleigh_fading": fading,
    "h_linear": h_values,
    "h_dB": h_db
})
user_data.to_csv(f"{results_dir}/h_values.csv", index=False)

# -------------------- Visualization Functions --------------------



# -------------------- SIC Rate Calculation --------------------
def calc_pair_rate(h1, h2):
    P1, P2 = total_power * h2 / (h1 + h2), total_power * h1 / (h1 + h2)
    R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))
    R2 = np.log2(1 + (P2 * h2) / noise_power)
    return P1, P2, R1, R2, R1 + R2

# -------------------- SIC Condition Check --------------------
def sic_satisfied(h1, h2):
    return 10 * np.log10(h2 / h1) >= sic_threshold_db

# ==================== NEW: Angle helper + 1-D power optimizer ====================
def angle_diff_rad(a, b):
    """Smallest absolute angle difference on circle [0, 2π)."""
    d = np.abs(a - b) % (2*np.pi)
    return np.minimum(d, 2*np.pi - d)

def _pair_rates_given_P1(h1, h2, P1):
    """Rates for a given split P1 (P2 = total_power - P1). h1<=h2 assumed."""
    P1 = np.clip(P1, 0.0, total_power)
    P2 = total_power - P1
    R1 = np.log2(1.0 + (P1 * h1) / (P2 * h1 + noise_power))
    R2 = np.log2(1.0 + (P2 * h2) / noise_power)
    return R1, R2, R1 + R2, P1, P2

def optimize_pair_power(h1, h2, objective='sum', w1=1.0, w2=1.0,
                        tol=POWER_OPT_TOL, max_iter=POWER_OPT_MAXIT):
    """
    1-D golden-section search to maximize:
      - 'sum' : R1 + R2
      - 'pf'  : log(R1) + log(R2)  (PF; uses PF_EPS)
    Assumes h1 <= h2 and P1 in (0, total_power).
    """
    lo = 1e-9
    hi = total_power - 1e-9
    gr = (np.sqrt(5) - 1) / 2  # ~0.618

    def U(P1):
        R1, R2, Rsum, _, _ = _pair_rates_given_P1(h1, h2, P1)
        if objective == 'pf':
            return np.log(R1 + PF_EPS) + np.log(R2 + PF_EPS)
        else:
            return Rsum

    c = hi - gr * (hi - lo)
    d = lo + gr * (hi - lo)
    uc, ud = U(c), U(d)

    it = 0
    while (hi - lo) > tol and it < max_iter:
        if uc < ud:
            lo = c
            c = d
            uc = ud
            d = lo + gr * (hi - lo)
            ud = U(d)
        else:
            hi = d
            d = c
            ud = uc
            c = hi - gr * (hi - lo)
            uc = U(c)
        it += 1

    P1_opt = 0.5 * (lo + hi)
    R1, R2, Rsum, P1_opt, P2_opt = _pair_rates_given_P1(h1, h2, P1_opt)
    return P1_opt, P2_opt, R1, R2, Rsum
# ================================================================================

# -------------------- Clustering Common Function (UPDATED) --------------------
def perform_clustering(pairs_indices, name, results_dir, power_opt=False, objective='sum', w1=1.0, w2=1.0):
    """
    Perform clustering with given pair indices and save results with visualizations

    Args:
        pairs_indices: List of tuples representing user pairs
        name: String identifier for the clustering method
        power_opt: If True, run 1-D power optimization per NOMA pair
        objective: 'sum' or 'pf' (used when power_opt=True)
        w1, w2: utility weights (usually 1,1)

    Returns:
        Dictionary containing performance metrics
    """
    data, used = [], np.zeros(N, bool)
    total_rate = 0
    noma_pairs_count = 0

    if not QUIET_MODE:
        print(f"\n--- {name.title()} Clustering ---")
        print(f"Evaluating {len(pairs_indices)} potential pairs...")

    iterator = tqdm(pairs_indices, desc=f"Processing {name} pairs") if not QUIET_MODE else pairs_indices
    for u1, u2 in iterator:
        h1u, h2u = h_values[u1], h_values[u2]
        if h1u <= h2u:
            a, b = u1, u2
            h1, h2 = h1u, h2u
        else:
            a, b = u2, u1
            h1, h2 = h2u, h1u

        if not sic_satisfied(h1, h2):
            continue

        if power_opt:
            P1, P2, R1, R2, R_sum = optimize_pair_power(h1, h2, objective=objective, w1=w1, w2=w2)
        else:
            P1, P2, R1, R2, R_sum = calc_pair_rate(h1, h2)

        used[[a, b]] = True
        data.append([a, b, h1, h2, P1, P2, R1, R2, R_sum, "NOMA"])
        total_rate += R_sum
        noma_pairs_count += 1

    num_pairs = noma_pairs_count
    num_oma = int(np.sum(~used))
    B_unit = B_total / (num_pairs + num_oma) if (num_pairs + num_oma) > 0 else 0.0
    throughput_total = 0.0

    # NOMA throughput
    for row in data:
        row.append(row[8] * B_unit / 1e6)
        throughput_total += row[-1]

    # OMA users
    oma_users_count = 0
    for u in range(N):
        if not used[u]:
            h = h_values[u]
            R1_oma = np.log2(1 + total_power * h / noise_power)
            throughput = R1_oma * B_unit / 1e6
            throughput_total += throughput
            data.append([u, -1, h, 0, total_power, 0, R1_oma, 0, R1_oma, "OMA", throughput])
            oma_users_count += 1

    # Save results
    save_name = f"{results_dir}/{name}_clustering.csv"
    cols = ["User1_ID", "User2_ID", "h1", "h2", "P1", "P2", "R1_bitsHz", "R2_bitsHz", "R_sum_bitsHz", "Mode", "Throughput_Mbps"]
    pd.DataFrame(data, columns=cols).to_csv(save_name, index=False)

    # Print performance summary
    if not QUIET_MODE:
        print(f"NOMA Pairs: {noma_pairs_count}")
        print(f"OMA Users: {oma_users_count}")
        print(f"Total Throughput: {throughput_total:.2f} Mbps")
        print(f"NOMA Coverage: {(noma_pairs_count * 2)/N*100:.1f}%")

    # Generate pairing visualization only if detailed plots are requested
    if SAVE_DETAILED_PLOTS:
        plot_pairing_visualization_local(pairs_indices, name, data, results_dir)

    return {
        'noma_pairs': noma_pairs_count,
        'oma_users': oma_users_count,
        'total_throughput': throughput_total,
        'noma_coverage': (noma_pairs_count * 2)/N*100
    }

# ==================== PF-weighted bipartite matching (moved to local function) ====================
    return list(matching)

def plot_pairing_visualization_local(pairs_indices, name, clustering_data, results_dir):
    """Local version of pairing visualization"""
    # Simplified version - just save basic info
    pass

# ==================== BATCH SIMULATION RUNNER ====================
def run_batch_simulations():
    """Run multiple simulations and aggregate results"""
    print(f"🚀 Starting {NUM_SIMULATIONS} NOMA simulations...")
    print(f"📊 Configuration: {N} users, {radius}m radius, {fc/1e9:.1f} GHz")
    print("=" * 70)
    
    # Create main results directory
    main_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_results_dir = f"batch_results_{main_timestamp}"
    os.makedirs(main_results_dir, exist_ok=True)
    
    # Storage for aggregated results
    all_results = {'static': [], 'balanced': [], 'blossom': [], 'bipartite_pf': []}
    
    # Progress bar for all simulations
    for run_id in tqdm(range(NUM_SIMULATIONS), desc="Running simulations"):
        try:
            results, run_num = run_single_simulation(run_id, main_results_dir)
            
            # Collect results
            for method in all_results.keys():
                if method in results:
                    result_entry = results[method].copy()
                    result_entry['run_id'] = run_id
                    all_results[method].append(result_entry)
                    
        except Exception as e:
            if not QUIET_MODE:
                print(f"⚠️  Error in simulation {run_id}: {e}")
            continue
    
    # Save aggregated results
    if SAVE_AGGREGATE_RESULTS:
        print("\n📈 Saving aggregated results...")
        save_aggregated_results(all_results, main_results_dir)
    
    print(f"\n✅ Batch simulation completed!")
    print(f"📁 Results saved to: {main_results_dir}")
    
    return all_results, main_results_dir

def save_aggregated_results(all_results, results_dir):
    """Save aggregated statistics across all simulation runs"""
    summary_stats = []
    
    for method, results in all_results.items():
        if not results:
            continue
            
        throughputs = [r['total_throughput'] for r in results]
        noma_pairs = [r['noma_pairs'] for r in results]
        noma_coverage = [r['noma_coverage'] for r in results]
        
        stats = {
            'Method': method,
            'Runs': len(results),
            'Mean_Throughput_Mbps': np.mean(throughputs),
            'Std_Throughput_Mbps': np.std(throughputs),
            'Min_Throughput_Mbps': np.min(throughputs),
            'Max_Throughput_Mbps': np.max(throughputs),
            'Mean_NOMA_Pairs': np.mean(noma_pairs),
            'Mean_NOMA_Coverage_%': np.mean(noma_coverage)
        }
        summary_stats.append(stats)
    
    # Save summary statistics
    summary_df = pd.DataFrame(summary_stats)
    summary_df.to_csv(f"{results_dir}/aggregated_summary.csv", index=False)
    
    # Save detailed results for each method
    for method, results in all_results.items():
        if results:
            detailed_df = pd.DataFrame(results)
            detailed_df.to_csv(f"{results_dir}/{method}_all_runs.csv", index=False)
    
    print(f"📊 Summary statistics saved to {results_dir}/aggregated_summary.csv")
    
    # Print final summary
    print("\n" + "="*70)
    print("📊 FINAL PERFORMANCE SUMMARY")
    print("="*70)
    
    for method in ['static', 'balanced', 'blossom', 'bipartite_pf']:
        if all_results[method]:
            throughputs = [r['total_throughput'] for r in all_results[method]]
            mean_tp = np.mean(throughputs)
            std_tp = np.std(throughputs)
            print(f"{method.upper():>12}: {mean_tp:6.2f} ± {std_tp:5.2f} Mbps ({len(throughputs)} runs)")

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    print("🎯 NOMA Clustering Simulation - Batch Runner")
    print(f"🔧 Configuration: {NUM_SIMULATIONS} runs, {N} users per run")
    print("🚀 Starting batch simulation...\n")
    
    start_time = time.time()
    
    try:
        all_results, results_dir = run_batch_simulations()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"\n⏱️  Total execution time: {elapsed_time:.1f} seconds")
        print(f"⚡ Average time per simulation: {elapsed_time/NUM_SIMULATIONS:.2f} seconds")
        print("\n✅ All simulations completed successfully!")
        print(f"📁 Check results in: {results_dir}/")
        
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during batch simulation: {e}")

# -------------------- Single Simulation Function --------------------
def run_single_simulation(run_id, base_results_dir="results"):
    """Run a single simulation instance"""
    # Set unique random seed for each run
    np.random.seed(run_id * 12345 + int(time.time()))
    
    # Create timestamped results directory for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = os.path.join(base_results_dir, f"run_{run_id:03d}_{timestamp}")
    os.makedirs(results_dir, exist_ok=True)
    
    if not QUIET_MODE:
        print(f"\n--- Running simulation {run_id+1}/{NUM_SIMULATIONS} ---")
        print(f"Results directory: {results_dir}")

    # -------------------- User Placement --------------------
    r = np.sqrt(np.random.uniform(0, radius**2, N))  # 2D distance from BS
    theta = np.random.uniform(0, 2*np.pi, N)
    x_coords, y_coords = r * np.cos(theta), r * np.sin(theta)
    
    # Random UE heights within 3GPP UMa limits (1.5m – 22.5m)
    h_UTs = np.random.uniform(1.5, 22.5, N)

    # -------------------- Generate Path Loss for Each User --------------------
    d_3D = np.sqrt(r**2 + (h_BS - h_UTs)**2)
    P_LOS_users = prob_LOS_UMa(r, h_UTs)
    
    PL_dB = np.zeros(N)
    is_LOS = np.zeros(N, dtype=bool)
    
    for i in range(N):
        if np.random.rand() <= P_LOS_users[i]:
            PL_dB[i] = PL_UMa_LOS(d_3D[i], fc)
            is_LOS[i] = True
        else:
            PL_dB[i] = PL_UMa_NLOS(d_3D[i], fc, h_UTs[i])
            is_LOS[i] = False
    
    # Convert PL to linear scale
    pl_linear = 10 ** (-PL_dB / 10)
    
    # -------------------- Shadowing --------------------
    shadowing = np.random.normal(0, shadow_std_db, N)  # Log-normal shadowing in dB
    
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
            # Rayleigh fading for NLOS users - using standard scale
            fading[i] = np.random.rayleigh(scale=1/np.sqrt(2))
    
    # -------------------- Channel Gain --------------------
    # Combine path loss, shadowing, and fading components correctly
    channel_gain_linear = fading * np.sqrt(pl_linear * 10**(-shadowing/10))
    h_values = channel_gain_linear
    h_db = 20 * np.log10(h_values + CHANNEL_GAIN_EPS)  # Convert to dB with small epsilon
    
    # Create consistent path loss variable name for visualization functions
    path_loss_db = PL_dB
    
    # Channel values are now ready for clustering
    # Sorted indices for clustering
    sorted_indices = np.argsort(h_values)
    
    # Save comprehensive user data
    user_data = pd.DataFrame({
        "User_ID": np.arange(N),
        "x_coord_m": x_coords,
        "y_coord_m": y_coords,
        "distance_m": r,
        "angle_rad": theta,
        "path_loss_dB": path_loss_db,
        "path_loss_linear": pl_linear,
        "shadowing_dB": shadowing,
        "rayleigh_fading": fading,
        "h_linear": h_values,
        "h_dB": h_db
    })
    user_data.to_csv(f"{results_dir}/h_values.csv", index=False)
    
    # Store results for comparison
    clustering_results = {}

    # -------------------- Static Clustering --------------------
    if not QUIET_MODE:
        print("\n" + "="*50)
    static_indices = [(sorted_indices[i], sorted_indices[N-1-i]) for i in range(N//2)]
    clustering_results['static'] = perform_clustering(static_indices, "static", results_dir)
    
    # -------------------- Balanced Clustering --------------------
    if not QUIET_MODE:
        print("\n" + "="*50)
    balanced_indices = [(sorted_indices[i], sorted_indices[i + N//2]) for i in range(N//2)]
    clustering_results['balanced'] = perform_clustering(balanced_indices, "balanced", results_dir)
    
    # -------------------- Blossom Clustering --------------------
    if not QUIET_MODE:
        print("\n" + "="*50)
        print("Blossom Clustering")
        print("Building maximum weight matching graph...")
    G = nx.Graph()
    
    iterator = tqdm(range(N), desc="Building graph") if not QUIET_MODE else range(N)
    for i in iterator:
        for j in range(i+1, N):
            if sic_satisfied(min(h_values[i], h_values[j]), max(h_values[i], h_values[j])):
                _, _, _, _, R_sum = calc_pair_rate(min(h_values[i], h_values[j]), max(h_values[i], h_values[j]))
                G.add_edge(i, j, weight=R_sum)
    
    if not QUIET_MODE:
        print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    blossom_indices = list(nx.max_weight_matching(G, maxcardinality=True))
    clustering_results['blossom'] = perform_clustering(blossom_indices, "blossom", results_dir)
    
    # -------------------- PF Bipartite (strong-weak) --------------------
    if not QUIET_MODE:
        print("\n" + "="*50)
        print("PF Bipartite (strong-weak) Matching with Angular Guard")
    bp_pairs = build_bipartite_pf_matching_local(sorted_indices, h_values, theta)
    if not QUIET_MODE:
        print(f"PF Bipartite candidate matches: {len(bp_pairs)}")
    clustering_results['bipartite_pf'] = perform_clustering(
        bp_pairs, "bipartite_pf", results_dir, power_opt=True, objective='pf'
    )

    # Generate plots only if requested
    if SAVE_DETAILED_PLOTS:
        if not QUIET_MODE:
            print("\n" + "="*50)
            print("Generating comparison analysis...")
        plot_clustering_comparison_local(clustering_results, results_dir)
    
    if not QUIET_MODE:
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
        
        print(f"\nResults saved to '{results_dir}/' directory")
    
    return clustering_results, run_id

def build_bipartite_pf_matching_local(sorted_indices, h_values, theta, theta_min_deg=THETA_MIN_DEG):
    """Local version of bipartite matching function"""
    theta_min_rad = np.deg2rad(theta_min_deg)
    weak = list(sorted_indices[:N//2])
    strong = list(sorted_indices[N//2:])
    
    G = nx.Graph()
    for i in weak:
        for j in strong:
            if angle_diff_rad(theta[i], theta[j]) < theta_min_rad:
                continue
            h1, h2 = (h_values[i], h_values[j]) if h_values[i] <= h_values[j] else (h_values[j], h_values[i])
            if not sic_satisfied(h1, h2):
                continue
            _, _, R1, R2, _ = calc_pair_rate(h1, h2)
            w = np.log(R1 + PF_EPS) + np.log(R2 + PF_EPS)
            if np.isfinite(w):
                G.add_edge(i, j, weight=w)
    
    matching = nx.max_weight_matching(G, maxcardinality=True)
    return list(matching)

def plot_clustering_comparison_local(clustering_results, results_dir):
    """Local version of comparison plotting function"""
    methods = list(clustering_results.keys())
    if not methods:
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    throughputs = [clustering_results[m]['total_throughput'] for m in methods]
    bars1 = ax1.bar(methods, throughputs)
    ax1.set_ylabel('Total Throughput (Mbps)')
    ax1.set_title('Total System Throughput Comparison')
    ax1.grid(True, alpha=0.3)
    
    for bar, value in zip(bars1, throughputs):
        ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.01, f'{value:.1f}',
                 ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{results_dir}/clustering_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()