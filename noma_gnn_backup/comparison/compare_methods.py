"""
NOMA Pairing Methods - Comprehensive Comparison Tool

This tool compares 5 pairing methods on the SAME dataset:
1. Static (Strongest-Weakest)
2. Balanced (Upper-Lower Half)
3. Bipartite (Graph-based matching with angular guard)
4. Blossom (General max-weight matching)
5. NOMA-GNN (Proposed)

Comparison Methodology:
- Fixed bandwidth: 180 kHz per NOMA pair
- Only NOMA pairs contribute to throughput (OMA users excluded)
- Focus on pairing quality rather than coverage
- All graph-based methods use sum rate (R1 + R2) optimization

Metrics Compared:
- Execution Time (ms)
- NOMA Pairs / OMA Users
- Total Throughput (Mbps) = num_pairs × avg_sum_rate × 180kHz
- Average Sum Rate per Pair (bits/s/Hz)
- Pairing Efficiency (% users paired)

Implementations based on noma.py (codes/27sept/noma.py)
FIXED: November 3, 2025 - Corrected power allocation
FIXED: November 3, 2025 - Unified weight function (sum rate)
FIXED: November 3, 2025 - Fixed bandwidth (180 kHz) for clean comparison

Author: Shailendra
Date: October 2025
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import torch
import networkx as nx
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.pairpower_gnn import PairPowerGNN
from data.normalization import Scaler

# ==========================================================================================
# GLOBAL PARAMETERS (from noma.py)
# ==========================================================================================
SIC_THRESHOLD_DB = 8.0          # SIC constraint (h2 - h1 >= 8 dB)
MIN_ANGLE_DEG = 25.0            # Angular guard for bipartite matching
MIN_ANGLE_RAD = np.deg2rad(MIN_ANGLE_DEG)
PF_EPS = 1e-12                  # Epsilon for PF log weights
NOISE_POWER = 1e-9              # Noise power (W)
TOTAL_POWER = 1.0               # Total power (W)
B_TOTAL = 20e6                  # Total bandwidth (Hz)

# ==========================================================================================
# HELPER FUNCTIONS (from noma.py)
# ==========================================================================================

def sic_satisfied(h1: float, h2: float) -> bool:
    """
    Check if SIC constraint is satisfied: h2 - h1 >= SIC_THRESHOLD_DB
    h1: weaker channel gain (linear)
    h2: stronger channel gain (linear)
    """
    h1_db = 10 * np.log10(h1 + 1e-15)
    h2_db = 10 * np.log10(h2 + 1e-15)
    return (h2_db - h1_db) >= SIC_THRESHOLD_DB


def angle_diff_rad(theta1: float, theta2: float) -> float:
    """Calculate minimum angular difference in radians."""
    diff = abs(theta1 - theta2)
    return min(diff, 2 * np.pi - diff)


def calc_pair_rate(h1: float, h2: float) -> Tuple[float, float, float, float, float]:
    """
    Calculate NOMA rates with channel-gain-based power allocation.
    CORRECTED to match noma.py implementation exactly.
    
    Args:
        h1: weaker channel gain (linear)
        h2: stronger channel gain (linear)
    
    Returns:
        P1, P2, R1, R2, R_sum (all in linear/bits/s/Hz)
    """
    # NOMA power allocation (inversely proportional to channel gain)
    # Weak user (h1) gets MORE power, strong user (h2) gets LESS power
    P1 = TOTAL_POWER * h2 / (h1 + h2)
    P2 = TOTAL_POWER * h1 / (h1 + h2)
    
    # SINR calculations
    SINR1 = (P1 * h1) / (P2 * h1 + NOISE_POWER)
    SINR2_after_sic = (P2 * h2) / NOISE_POWER
    
    # Rates (bits/s/Hz)
    R1 = np.log2(1 + SINR1)
    R2 = np.log2(1 + SINR2_after_sic)
    R_sum = R1 + R2
    
    return P1, P2, R1, R2, R_sum


def calculate_throughput_mbps(pairs: List[Tuple[int, int]], 
                              h_linear: np.ndarray,
                              n_users: int) -> Tuple[float, int, int, float]:
    """
    Calculate total throughput in Mbps with FIXED bandwidth per NOMA pair.
    
    Comparison methodology:
    - Only NOMA pairs are considered (OMA users ignored)
    - Each NOMA pair gets fixed 180 kHz bandwidth
    - Focus is on pairing quality, not coverage
    
    Args:
        pairs: List of (user1_idx, user2_idx) tuples
        h_linear: Channel gains (linear scale)
        n_users: Total number of users in scenario
    
    Returns:
        Tuple of (throughput_mbps, num_noma_pairs, num_oma_users, total_spectral_efficiency)
    """
    FIXED_BW_PER_PAIR = 180e3  # 180 kHz per NOMA pair
    
    total_rate = 0.0  # Spectral efficiency (bits/s/Hz)
    num_valid_pairs = 0
    paired = set()
    
    # Process NOMA pairs only
    for u1, u2 in pairs:
        h1, h2 = h_linear[u1], h_linear[u2]
        
        # Ensure h1 <= h2 (weak, strong)
        if h1 > h2:
            h1, h2 = h2, h1
        
        # Check SIC
        if not sic_satisfied(h1, h2):
            continue
        
        # Calculate rates
        _, _, R1, R2, _ = calc_pair_rate(h1, h2)
        total_rate += R1 + R2
        paired.add(u1)
        paired.add(u2)
        num_valid_pairs += 1
    
    # OMA users (unpaired) - count but don't include in throughput
    num_oma = n_users - len(paired)
    
    # Fixed bandwidth per pair
    if num_valid_pairs == 0:
        return 0.0, 0, num_oma, 0.0
    
    # Throughput = spectral_efficiency × bandwidth_per_pair × num_pairs
    throughput_mbps = (total_rate * FIXED_BW_PER_PAIR) / 1e6
    
    return throughput_mbps, num_valid_pairs, num_oma, total_rate


# ==========================================================================================
# METHOD 1: STATIC PAIRING (from noma.py line 678)
# ==========================================================================================
def static_pairing(h_linear: np.ndarray) -> List[Tuple[int, int]]:
    """
    Static pairing: strongest with weakest.
    EXACT implementation from noma.py.
    
    Complexity: O(N log N)
    """
    sorted_indices = np.argsort(h_linear)  # Ascending order
    n = len(h_linear)
    
    # Pair: sorted[0] with sorted[N-1], sorted[1] with sorted[N-2], etc.
    pairs = [(sorted_indices[i], sorted_indices[n-1-i]) for i in range(n//2)]
    
    return pairs


# ==========================================================================================
# METHOD 2: BALANCED PAIRING (from noma.py line 683)
# ==========================================================================================
def balanced_pairing(h_linear: np.ndarray) -> List[Tuple[int, int]]:
    """
    Balanced pairing: upper half with lower half.
    EXACT implementation from noma.py.
    
    Complexity: O(N log N)
    """
    sorted_indices = np.argsort(h_linear)  # Ascending order
    n = len(h_linear)
    
    # Pair: sorted[0] with sorted[N/2], sorted[1] with sorted[N/2+1], etc.
    pairs = [(sorted_indices[i], sorted_indices[i + n//2]) for i in range(n//2)]
    
    return pairs


# ==========================================================================================
# METHOD 3: BIPARTITE MATCHING (from noma.py lines 562-591)
# ==========================================================================================
def bipartite_pairing(h_linear: np.ndarray, angles: np.ndarray) -> List[Tuple[int, int]]:
    """
    Bipartite matching with angular guard.
    Modified from noma.py to use SUM RATE (same as Blossom) for fair comparison.
    
    Steps:
    1. Split users: weak (lower half) and strong (upper half) by channel gain
    2. Build bipartite graph (weak ↔ strong) with edges satisfying:
       - Angular guard (>= 25°)
       - SIC constraint (>= 8 dB difference)
    3. Edge weight = R1 + R2 (sum rate - SAME as Blossom for fair comparison)
    4. Run NetworkX max_weight_matching
    
    Complexity: O(N³)
    
    Note: Uses sum rate instead of PF (log-based) weights to ensure:
          - Fair timing comparison with Blossom
          - Same optimization objective (maximize total throughput)
    """
    n = len(h_linear)
    sorted_indices = np.argsort(h_linear)  # Ascending
    
    # Split: weak (lower half), strong (upper half)
    weak = list(sorted_indices[:n//2])
    strong = list(sorted_indices[n//2:])
    
    # Build bipartite graph
    G = nx.Graph()
    
    for i in weak:
        for j in strong:
            # Angular guard
            if angle_diff_rad(angles[i], angles[j]) < MIN_ANGLE_RAD:
                continue
            
            # SIC guard (i is weak, j is strong)
            h1, h2 = h_linear[i], h_linear[j]
            if not sic_satisfied(h1, h2):
                continue
            
            # Sum rate weight (SAME as Blossom)
            _, _, R1, R2, R_sum = calc_pair_rate(h1, h2)
            G.add_edge(i, j, weight=R_sum)
    
    # Maximum weight matching
    matching = nx.max_weight_matching(G, maxcardinality=True)
    pairs = list(matching)
    
    return pairs


# ==========================================================================================
# METHOD 4: BLOSSOM MATCHING (from noma.py lines 686-703)
# ==========================================================================================
def blossom_pairing(h_linear: np.ndarray, angles: np.ndarray, show_progress: bool = True) -> List[Tuple[int, int]]:
    """
    Blossom maximum weight matching on complete graph.
    EXACT implementation from noma.py.
    
    Steps:
    1. Build complete graph with ALL N users
    2. Add edges for all feasible pairs (SIC satisfied)
    3. Edge weight = R_sum (sum rate)
    4. Run NetworkX max_weight_matching (Edmonds' Blossom algorithm)
    
    Complexity: O(N³) with high constants
    """
    n = len(h_linear)
    
    # Build complete graph
    G = nx.Graph()
    edge_count = 0
    
    iterator = tqdm(range(n), desc="Building Blossom graph") if show_progress else range(n)
    
    for i in iterator:
        for j in range(i+1, n):
            # Get weak and strong
            h1, h2 = (h_linear[i], h_linear[j]) if h_linear[i] <= h_linear[j] else (h_linear[j], h_linear[i])
            
            # SIC constraint
            if not sic_satisfied(h1, h2):
                continue
            
            # Add edge with sum rate as weight
            _, _, _, _, R_sum = calc_pair_rate(h1, h2)
            G.add_edge(i, j, weight=R_sum)
            edge_count += 1
    
    if show_progress:
        print(f"  Graph: {n} nodes, {edge_count} edges")
    
    # Maximum weight matching
    matching = nx.max_weight_matching(G, maxcardinality=True)
    pairs = list(matching)
    
    return pairs


# ==========================================================================================
# METHOD 5: NOMA-GNN
# ==========================================================================================
def gnn_pairing(h_linear: np.ndarray, 
                angles: np.ndarray,
                distances: np.ndarray,
                is_los: np.ndarray,
                model: PairPowerGNN,
                scaler: Scaler,
                device: str = 'cpu') -> List[Tuple[int, int]]:
    """
    GNN-based pairing using learned pair scoring.
    
    Steps:
    1. Build node features (h, angle, distance, is_los, h_rank)
    2. Normalize features
    3. Build edge index (all feasible pairs)
    4. Run GNN to get pair scores
    5. Greedy matching: sort by score, greedily select non-overlapping pairs
    
    Complexity: O(N²) for edge construction + O(E) for GNN + O(N log N) for greedy
               Typical: O(N log N) if edges are sparse
    """
    n = len(h_linear)
    
    # Build node features
    h_db = 10 * np.log10(h_linear + 1e-15)
    h_ranks = np.argsort(np.argsort(h_linear)).astype(float) / n  # Normalized rank [0, 1]
    
    node_features = np.column_stack([
        h_db,
        angles,
        distances,
        is_los.astype(float),
        h_ranks
    ])  # Shape: (N, 5)
    
    # Normalize
    node_features_norm = scaler.transform(node_features)
    x = torch.FloatTensor(node_features_norm).to(device)
    
    # Build edge index (all feasible pairs with SIC)
    edge_list = []
    for i in range(n):
        for j in range(i+1, n):
            h1, h2 = (h_linear[i], h_linear[j]) if h_linear[i] <= h_linear[j] else (h_linear[j], h_linear[i])
            if sic_satisfied(h1, h2):
                edge_list.append([i, j])
    
    if len(edge_list) == 0:
        return []
    
    edge_index = torch.LongTensor(edge_list).t().contiguous().to(device)  # Shape: (2, E)
    
    # Run GNN
    model.eval()
    with torch.no_grad():
        # GNN expects (x, mp_edge_index, edge_index_eval)
        # Returns: (logit, rsum, alpha) - we use logit for pair scoring
        logit, rsum, alpha = model(x, edge_index, edge_index)
        edge_scores = torch.sigmoid(logit).cpu().numpy()  # Shape: (E,)
    
    # Greedy matching
    scored_edges = [(edge_list[i][0], edge_list[i][1], edge_scores[i]) for i in range(len(edge_list))]
    scored_edges.sort(key=lambda x: x[2], reverse=True)  # Sort by score descending
    
    paired = set()
    pairs = []
    
    for u, v, score in scored_edges:
        if u not in paired and v not in paired:
            pairs.append((u, v))
            paired.add(u)
            paired.add(v)
    
    return pairs


# ==========================================================================================
# COMPARISON ENGINE
# ==========================================================================================
def run_comparison(h_values_file: str,
                   checkpoint_file: str,
                   scaler_file: str,
                   device: str = 'cpu',
                   skip_blossom: bool = False,
                   iterations: int = 1,
                   output_file: str = 'comparison_results.csv') -> pd.DataFrame:
    """
    Run comprehensive comparison of all 5 methods.
    
    Returns:
        DataFrame with results for all methods
    """
    print("=" * 90)
    print(" NOMA PAIRING METHODS - COMPREHENSIVE COMPARISON")
    print("=" * 90)
    
    # ==================== LOAD DATA ====================
    print(f"\n[1/6] Loading scenario data...")
    df = pd.read_csv(h_values_file)
    
    # Handle different column naming conventions
    if 'h_linear' not in df.columns:
        raise ValueError("Missing required column: h_linear")
    
    h_linear = df['h_linear'].values
    
    # Angle: try 'angle', 'angle_rad', 'theta'
    if 'angle' in df.columns:
        angles = df['angle'].values
    elif 'angle_rad' in df.columns:
        angles = df['angle_rad'].values
    elif 'theta' in df.columns:
        angles = df['theta'].values
    else:
        raise ValueError("Missing angle column (expected: 'angle', 'angle_rad', or 'theta')")
    
    # Distance: try 'distance', 'distance_m', 'd_2D'
    if 'distance' in df.columns:
        distances = df['distance'].values
    elif 'distance_m' in df.columns:
        distances = df['distance_m'].values
    elif 'd_2D' in df.columns:
        distances = df['d_2D'].values
    else:
        print("  ⚠ Warning: No distance column found, using zeros")
        distances = np.zeros(len(h_linear))
    
    # is_los: optional, default to False
    if 'is_los' in df.columns:
        is_los = df['is_los'].values
    elif 'is_LOS' in df.columns:
        is_los = df['is_LOS'].values
    else:
        print("  ⚠ Warning: No is_los column found, assuming all NLOS")
        is_los = np.zeros(len(h_linear), dtype=bool)
    
    n_users = len(h_linear)
    print(f"  ✓ Loaded {n_users} users")
    
    # ==================== LOAD GNN MODEL ====================
    print(f"\n[2/6] Loading GNN model...")
    
    # Load scaler
    scaler = Scaler.load(scaler_file)
    
    # Load model
    checkpoint = torch.load(checkpoint_file, map_location=device, weights_only=False)
    
    if isinstance(checkpoint, dict) and 'model_state' in checkpoint:
        state_dict = checkpoint['model_state']
        cfg = checkpoint.get('cfg', {})
    else:
        state_dict = checkpoint
        cfg = {}
    
    model = PairPowerGNN(
        in_channels=5,
        hidden=cfg.get('hidden_dim', 128),
        out_channels=cfg.get('out_dim', 128),
        num_layers=cfg.get('num_layers', 3)
    ).to(device)
    
    model.load_state_dict(state_dict)
    model.eval()
    
    print(f"  ✓ GNN model loaded")
    
    # ==================== RUN COMPARISONS ====================
    results = []
    
    # --- METHOD 1: STATIC ---
    print(f"\n[3/6] Running STATIC pairing...")
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        pairs_static = static_pairing(h_linear)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        times.append(elapsed)
    
    throughput_static, noma_pairs_static, oma_users_static, total_rate_static = calculate_throughput_mbps(pairs_static, h_linear, n_users)
    
    results.append({
        'Method': 'Static',
        'Time_ms': np.mean(times),
        'Time_std_ms': np.std(times),
        'NOMA_Pairs': noma_pairs_static,
        'OMA_Users': oma_users_static,
        'Users_Served': noma_pairs_static * 2 + oma_users_static,
        'Pairing_Efficiency_%': (noma_pairs_static * 2 / n_users) * 100,
        'Throughput_Mbps': throughput_static,
        'Avg_Sum_Rate_bps_Hz': total_rate_static / noma_pairs_static if noma_pairs_static > 0 else 0,
        'Per_Pair_BW_kHz': 180.0  # Fixed bandwidth
    })
    print(f"  ✓ Time: {np.mean(times):.4f} ± {np.std(times):.4f} ms")
    print(f"  ✓ NOMA Pairs: {noma_pairs_static}, OMA Users: {oma_users_static}")
    print(f"  ✓ Throughput: {throughput_static:.2f} Mbps (180 kHz × {noma_pairs_static} pairs)")
    
    # --- METHOD 2: BALANCED ---
    print(f"\n[4/6] Running BALANCED pairing...")
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        pairs_balanced = balanced_pairing(h_linear)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    
    throughput_balanced, noma_pairs_balanced, oma_users_balanced, total_rate_balanced = calculate_throughput_mbps(pairs_balanced, h_linear, n_users)
    
    results.append({
        'Method': 'Balanced',
        'Time_ms': np.mean(times),
        'Time_std_ms': np.std(times),
        'NOMA_Pairs': noma_pairs_balanced,
        'OMA_Users': oma_users_balanced,
        'Users_Served': noma_pairs_balanced * 2 + oma_users_balanced,
        'Pairing_Efficiency_%': (noma_pairs_balanced * 2 / n_users) * 100,
        'Throughput_Mbps': throughput_balanced,
        'Avg_Sum_Rate_bps_Hz': total_rate_balanced / noma_pairs_balanced if noma_pairs_balanced > 0 else 0,
        'Per_Pair_BW_kHz': 180.0  # Fixed bandwidth
    })
    print(f"  ✓ Time: {np.mean(times):.4f} ± {np.std(times):.4f} ms")
    print(f"  ✓ NOMA Pairs: {noma_pairs_balanced}, OMA Users: {oma_users_balanced}")
    print(f"  ✓ Throughput: {throughput_balanced:.2f} Mbps (180 kHz × {noma_pairs_balanced} pairs)")
    
    # --- METHOD 3: BIPARTITE ---
    print(f"\n[5/6] Running BIPARTITE pairing...")
    print(f"  Note: O(N³) complexity - may take time for N={n_users}")
    times = []
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}...", end=' ')
        start = time.perf_counter()
        pairs_bipartite = bipartite_pairing(h_linear, angles)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        print(f"{elapsed:.2f} ms")
    
    throughput_bipartite, noma_pairs_bipartite, oma_users_bipartite, total_rate_bipartite = calculate_throughput_mbps(pairs_bipartite, h_linear, n_users)
    
    results.append({
        'Method': 'Bipartite',
        'Time_ms': np.mean(times),
        'Time_std_ms': np.std(times),
        'NOMA_Pairs': noma_pairs_bipartite,
        'OMA_Users': oma_users_bipartite,
        'Users_Served': noma_pairs_bipartite * 2 + oma_users_bipartite,
        'Pairing_Efficiency_%': (noma_pairs_bipartite * 2 / n_users) * 100,
        'Throughput_Mbps': throughput_bipartite,
        'Avg_Sum_Rate_bps_Hz': total_rate_bipartite / noma_pairs_bipartite if noma_pairs_bipartite > 0 else 0,
        'Per_Pair_BW_kHz': 180.0  # Fixed bandwidth
    })
    print(f"  ✓ Mean Time: {np.mean(times):.2f} ± {np.std(times):.2f} ms")
    print(f"  ✓ NOMA Pairs: {noma_pairs_bipartite}, OMA Users: {oma_users_bipartite}")
    print(f"  ✓ Throughput: {throughput_bipartite:.2f} Mbps (180 kHz × {noma_pairs_bipartite} pairs)")
    
    # --- METHOD 4: BLOSSOM ---
    if not skip_blossom:
        print(f"\n[6/6] Running BLOSSOM pairing...")
        print(f"  Note: O(N³) with high constants - VERY slow for large N")
        print(f"  Running single iteration due to computational cost...")
        
        start = time.perf_counter()
        pairs_blossom = blossom_pairing(h_linear, angles, show_progress=True)
        elapsed = (time.perf_counter() - start) * 1000
        
        throughput_blossom, noma_pairs_blossom, oma_users_blossom, total_rate_blossom = calculate_throughput_mbps(pairs_blossom, h_linear, n_users)
        
        results.append({
            'Method': 'Blossom',
            'Time_ms': elapsed,
            'Time_std_ms': np.nan,  # Single run - no std dev
            'NOMA_Pairs': noma_pairs_blossom,
            'OMA_Users': oma_users_blossom,
            'Users_Served': noma_pairs_blossom * 2 + oma_users_blossom,
            'Pairing_Efficiency_%': (noma_pairs_blossom * 2 / n_users) * 100,
            'Throughput_Mbps': throughput_blossom,
            'Avg_Sum_Rate_bps_Hz': total_rate_blossom / noma_pairs_blossom if noma_pairs_blossom > 0 else 0,
            'Per_Pair_BW_kHz': 180.0  # Fixed bandwidth
        })
        print(f"  ✓ Time: {elapsed:.2f} ms ({elapsed/1000:.2f} s) [single run]")
        print(f"  ✓ NOMA Pairs: {noma_pairs_blossom}, OMA Users: {oma_users_blossom}")
        print(f"  ✓ Throughput: {throughput_blossom:.2f} Mbps (180 kHz × {noma_pairs_blossom} pairs)")
    else:
        print(f"\n[6/6] BLOSSOM pairing SKIPPED (use --run-blossom to enable)")
    
    # --- METHOD 5: GNN ---
    print(f"\n[7/7] Running NOMA-GNN pairing...")
    times = []
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}...", end=' ')
        start = time.perf_counter()
        pairs_gnn = gnn_pairing(h_linear, angles, distances, is_los, model, scaler, device)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        print(f"{elapsed:.2f} ms")
    
    throughput_gnn, noma_pairs_gnn, oma_users_gnn, total_rate_gnn = calculate_throughput_mbps(pairs_gnn, h_linear, n_users)
    
    results.append({
        'Method': 'NOMA-GNN',
        'Time_ms': np.mean(times),
        'Time_std_ms': np.std(times),
        'NOMA_Pairs': noma_pairs_gnn,
        'OMA_Users': oma_users_gnn,
        'Users_Served': noma_pairs_gnn * 2 + oma_users_gnn,
        'Pairing_Efficiency_%': (noma_pairs_gnn * 2 / n_users) * 100,
        'Throughput_Mbps': throughput_gnn,
        'Avg_Sum_Rate_bps_Hz': total_rate_gnn / noma_pairs_gnn if noma_pairs_gnn > 0 else 0,
        'Per_Pair_BW_kHz': 180.0  # Fixed bandwidth
    })
    print(f"  ✓ Mean Time: {np.mean(times):.2f} ± {np.std(times):.2f} ms")
    print(f"  ✓ NOMA Pairs: {noma_pairs_gnn}, OMA Users: {oma_users_gnn}")
    print(f"  ✓ Throughput: {throughput_gnn:.2f} Mbps (180 kHz × {noma_pairs_gnn} pairs)")
    
    # ==================== SAVE RESULTS ====================
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_file, index=False)
    
    print(f"\n{'=' * 90}")
    print(" COMPARISON SUMMARY")
    print(f"{'=' * 90}\n")
    print(results_df.to_string(index=False))
    print(f"\n✓ Results saved to: {output_file}")
    
    return results_df


# ==========================================================================================
# MAIN
# ==========================================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive comparison of NOMA pairing methods",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare all methods (skip Blossom for speed)
  python compare_methods.py --h-values data.csv --ckpt model.pt --scaler scaler.json
  
  # Include Blossom (slow for large N)
  python compare_methods.py --h-values data.csv --ckpt model.pt --scaler scaler.json --run-blossom
  
  # Custom iterations and output
  python compare_methods.py --h-values data.csv --ckpt model.pt --scaler scaler.json --iterations 5 --output my_results.csv
        """
    )
    parser.add_argument("--h-values", required=True, help="Path to h_values CSV (must have: h_linear, angle, distance, is_los)")
    parser.add_argument("--ckpt", required=True, help="Path to GNN checkpoint (.pt)")
    parser.add_argument("--scaler", required=True, help="Path to feature scaler JSON")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Device for GNN")
    parser.add_argument("--run-blossom", action="store_true", help="Include Blossom (very slow for large N)")
    parser.add_argument("--iterations", type=int, default=3, help="Number of timing iterations")
    parser.add_argument("--output", default="comparison_results.csv", help="Output CSV file")
    
    args = parser.parse_args()
    
    run_comparison(
        h_values_file=args.h_values,
        checkpoint_file=args.ckpt,
        scaler_file=args.scaler,
        device=args.device,
        skip_blossom=not args.run_blossom,
        iterations=args.iterations,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
