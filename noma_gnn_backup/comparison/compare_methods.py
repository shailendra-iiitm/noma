"""
NOMA Pairing Methods - Comprehensive Comparison Tool

This tool compares 5 pairing methods on the SAME dataset:
1. Static (Strongest-Weakest)
2. Balanced (Upper-Lower Half)
3. Bipartite (Graph-based PF matching)
4. Blossom (General max-weight matching)
5. NOMA-GNN (Proposed)

Metrics Compared:
- Execution Time (ms)
- Number of Pairs
- Total Throughput (Mbps)
- Average Sum Rate (bits/s/Hz)
- Pairing Efficiency (% users paired)

EXACT implementations copied from noma.py (codes/27sept/noma.py)

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
    Calculate NOMA rates and optimal power allocation.
    EXACT implementation from noma.py.
    
    Args:
        h1: weaker channel gain (linear)
        h2: stronger channel gain (linear)
    
    Returns:
        P1, P2, R1, R2, R_sum (all in linear/bits/s/Hz)
    """
    # Baseline split (50-50)
    P1 = TOTAL_POWER / 2
    P2 = TOTAL_POWER / 2
    
    # SINR calculations
    SINR1 = (P1 * h1) / (P2 * h1 + NOISE_POWER)
    SINR2_after_sic = (P2 * h2) / NOISE_POWER
    
    # Rates (bits/s/Hz)
    R1 = np.log2(1 + SINR1)
    R2 = np.log2(1 + SINR2_after_sic)
    R_sum = R1 + R2
    
    return P1, P2, R1, R2, R_sum


def calculate_throughput_mbps(pairs: List[Tuple[int, int]], h_linear: np.ndarray) -> float:
    """
    Calculate total throughput in Mbps for given pairs.
    
    Args:
        pairs: List of (user1_idx, user2_idx) tuples
        h_linear: Channel gains (linear scale)
    
    Returns:
        Total throughput in Mbps
    """
    total_rate = 0.0
    
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
    
    # Convert to Mbps: rate (bits/s/Hz) × bandwidth (Hz) / 1e6
    throughput_mbps = (total_rate * B_TOTAL) / 1e6
    
    return throughput_mbps


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
    Bipartite PF matching with angular guard.
    EXACT implementation from noma.py (build_bipartite_pf_matching).
    
    Steps:
    1. Split users: weak (lower half) and strong (upper half) by channel gain
    2. Build bipartite graph (weak ↔ strong) with edges satisfying:
       - Angular guard (>= 25°)
       - SIC constraint (>= 8 dB difference)
    3. Edge weight = log(R1) + log(R2) (proportional fairness)
    4. Run NetworkX max_weight_matching
    
    Complexity: O(N³)
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
            
            # PF weight
            _, _, R1, R2, _ = calc_pair_rate(h1, h2)
            w = np.log(R1 + PF_EPS) + np.log(R2 + PF_EPS)
            
            if np.isfinite(w):
                G.add_edge(i, j, weight=w)
    
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
                   iterations: int = 3,
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
    
    throughput_static = calculate_throughput_mbps(pairs_static, h_linear)
    
    results.append({
        'Method': 'Static',
        'Time_ms': np.mean(times),
        'Time_std_ms': np.std(times),
        'Pairs': len(pairs_static),
        'Pairing_Efficiency_%': (len(pairs_static) * 2 / n_users) * 100,
        'Throughput_Mbps': throughput_static,
        'Avg_Sum_Rate_bps_Hz': throughput_static * 1e6 / B_TOTAL / len(pairs_static) if len(pairs_static) > 0 else 0
    })
    print(f"  ✓ Time: {np.mean(times):.4f} ± {np.std(times):.4f} ms")
    print(f"  ✓ Pairs: {len(pairs_static)} ({len(pairs_static)*2}/{n_users} users)")
    print(f"  ✓ Throughput: {throughput_static:.2f} Mbps")
    
    # --- METHOD 2: BALANCED ---
    print(f"\n[4/6] Running BALANCED pairing...")
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        pairs_balanced = balanced_pairing(h_linear)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    
    throughput_balanced = calculate_throughput_mbps(pairs_balanced, h_linear)
    
    results.append({
        'Method': 'Balanced',
        'Time_ms': np.mean(times),
        'Time_std_ms': np.std(times),
        'Pairs': len(pairs_balanced),
        'Pairing_Efficiency_%': (len(pairs_balanced) * 2 / n_users) * 100,
        'Throughput_Mbps': throughput_balanced,
        'Avg_Sum_Rate_bps_Hz': throughput_balanced * 1e6 / B_TOTAL / len(pairs_balanced) if len(pairs_balanced) > 0 else 0
    })
    print(f"  ✓ Time: {np.mean(times):.4f} ± {np.std(times):.4f} ms")
    print(f"  ✓ Pairs: {len(pairs_balanced)} ({len(pairs_balanced)*2}/{n_users} users)")
    print(f"  ✓ Throughput: {throughput_balanced:.2f} Mbps")
    
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
    
    throughput_bipartite = calculate_throughput_mbps(pairs_bipartite, h_linear)
    
    results.append({
        'Method': 'Bipartite',
        'Time_ms': np.mean(times),
        'Time_std_ms': np.std(times),
        'Pairs': len(pairs_bipartite),
        'Pairing_Efficiency_%': (len(pairs_bipartite) * 2 / n_users) * 100,
        'Throughput_Mbps': throughput_bipartite,
        'Avg_Sum_Rate_bps_Hz': throughput_bipartite * 1e6 / B_TOTAL / len(pairs_bipartite) if len(pairs_bipartite) > 0 else 0
    })
    print(f"  ✓ Mean Time: {np.mean(times):.2f} ± {np.std(times):.2f} ms")
    print(f"  ✓ Pairs: {len(pairs_bipartite)} ({len(pairs_bipartite)*2}/{n_users} users)")
    print(f"  ✓ Throughput: {throughput_bipartite:.2f} Mbps")
    
    # --- METHOD 4: BLOSSOM ---
    if not skip_blossom:
        print(f"\n[6/6] Running BLOSSOM pairing...")
        print(f"  Note: O(N³) with high constants - VERY slow for large N")
        
        start = time.perf_counter()
        pairs_blossom = blossom_pairing(h_linear, angles, show_progress=True)
        elapsed = (time.perf_counter() - start) * 1000
        
        throughput_blossom = calculate_throughput_mbps(pairs_blossom, h_linear)
        
        results.append({
            'Method': 'Blossom',
            'Time_ms': elapsed,
            'Time_std_ms': 0.0,
            'Pairs': len(pairs_blossom),
            'Pairing_Efficiency_%': (len(pairs_blossom) * 2 / n_users) * 100,
            'Throughput_Mbps': throughput_blossom,
            'Avg_Sum_Rate_bps_Hz': throughput_blossom * 1e6 / B_TOTAL / len(pairs_blossom) if len(pairs_blossom) > 0 else 0
        })
        print(f"  ✓ Time: {elapsed:.2f} ms ({elapsed/1000:.2f} s)")
        print(f"  ✓ Pairs: {len(pairs_blossom)} ({len(pairs_blossom)*2}/{n_users} users)")
        print(f"  ✓ Throughput: {throughput_blossom:.2f} Mbps")
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
    
    throughput_gnn = calculate_throughput_mbps(pairs_gnn, h_linear)
    
    results.append({
        'Method': 'NOMA-GNN',
        'Time_ms': np.mean(times),
        'Time_std_ms': np.std(times),
        'Pairs': len(pairs_gnn),
        'Pairing_Efficiency_%': (len(pairs_gnn) * 2 / n_users) * 100,
        'Throughput_Mbps': throughput_gnn,
        'Avg_Sum_Rate_bps_Hz': throughput_gnn * 1e6 / B_TOTAL / len(pairs_gnn) if len(pairs_gnn) > 0 else 0
    })
    print(f"  ✓ Mean Time: {np.mean(times):.2f} ± {np.std(times):.2f} ms")
    print(f"  ✓ Pairs: {len(pairs_gnn)} ({len(pairs_gnn)*2}/{n_users} users)")
    print(f"  ✓ Throughput: {throughput_gnn:.2f} Mbps")
    
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
