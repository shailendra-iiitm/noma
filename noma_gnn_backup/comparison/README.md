# NOMA Pairing Methods - Comparison Tool

This folder contains a comprehensive comparison tool for evaluating 5 NOMA pairing methods on the **SAME** dataset.

## 📊 Methods Compared

| Method | Algorithm | Complexity | Source |
|--------|-----------|------------|--------|
| **Static** | Strongest-Weakest pairing | O(N log N) | noma.py line 678 |
| **Balanced** | Upper-half with lower-half | O(N log N) | noma.py line 683 |
| **Bipartite** | Graph-based PF matching | O(N³) | noma.py lines 562-591 |
| **Blossom** | General max-weight matching | O(N³) | noma.py lines 686-703 |
| **NOMA-GNN** | GNN-based learned pairing | O(N log N) typical | Proposed method |

All traditional methods (Static, Balanced, Bipartite, Blossom) are **EXACT** implementations copied from `codes/27sept/noma.py`.

## 📈 Metrics Evaluated

1. **Execution Time** (ms) - Average over multiple iterations
2. **Number of Pairs** - How many users were successfully paired
3. **Pairing Efficiency** (%) - Percentage of users paired
4. **Total Throughput** (Mbps) - System capacity
5. **Average Sum Rate** (bits/s/Hz) - Spectral efficiency per pair

## 🚀 Usage

### Basic Usage (Skip Blossom for Speed)

```bash
python compare_methods.py \
  --h-values ../test_scenario_500users.csv \
  --ckpt ../checkpoints/best_model.pt \
  --scaler ../data/processed/feature_scaler.json
```

### Include Blossom (Slow for N > 500)

```bash
python compare_methods.py \
  --h-values ../test_scenario_500users.csv \
  --ckpt ../checkpoints/best_model.pt \
  --scaler ../data/processed/feature_scaler.json \
  --run-blossom
```

### Custom Iterations and Output

```bash
python compare_methods.py \
  --h-values my_scenario.csv \
  --ckpt ../checkpoints/best_model.pt \
  --scaler ../data/processed/feature_scaler.json \
  --iterations 5 \
  --output my_comparison.csv
```

## 📋 Input File Format

Your CSV file must contain these columns (flexible naming):

| Required Column | Alternative Names | Description | Type |
|----------------|-------------------|-------------|------|
| `h_linear` | (none) | Channel gain (linear scale) | float |
| `angle` OR | `angle_rad`, `theta` | User angle (radians) | float |
| `distance` OR | `distance_m`, `d_2D` | Distance from BS (meters) | float |
| `is_los` (optional) | `is_LOS` | Line-of-sight indicator | bool/int |

**Note**: If `is_los` is not provided, all users are assumed to be NLOS (this doesn't affect Static, Balanced, Bipartite, or Blossom methods).

Example:
```csv
h_linear,angle_rad,distance_m
0.000123,1.234,1500.5
0.000456,2.345,2300.2
...
```

## 📊 Output Format

Results are saved to CSV with these columns:

| Column | Description |
|--------|-------------|
| `Method` | Method name |
| `Time_ms` | Average execution time (ms) |
| `Time_std_ms` | Standard deviation of time |
| `Pairs` | Number of pairs formed |
| `Pairing_Efficiency_%` | Percentage of users paired |
| `Throughput_Mbps` | Total system throughput |
| `Avg_Sum_Rate_bps_Hz` | Average sum rate per pair |

## ⚙️ Parameters (from noma.py)

The tool uses these global parameters:

```python
SIC_THRESHOLD_DB = 8.0      # SIC constraint (h2 - h1 >= 8 dB)
MIN_ANGLE_DEG = 25.0        # Angular guard for bipartite
NOISE_POWER = 1e-9          # Noise power (W)
TOTAL_POWER = 1.0           # Total power (W)
B_TOTAL = 20e6              # Bandwidth (Hz)
```

## 🎯 Use Cases

### 1. Single Scenario Comparison
Compare all methods on one specific scenario:
```bash
python compare_methods.py --h-values scenario1.csv --ckpt model.pt --scaler scaler.json
```

### 2. Multiple Scenario Testing
Run on multiple test files (bash):
```bash
for file in scenarios/*.csv; do
    python compare_methods.py \
        --h-values "$file" \
        --ckpt ../checkpoints/best_model.pt \
        --scaler ../data/processed/feature_scaler.json \
        --output "results_$(basename $file)"
done
```

### 3. Performance Profiling
Test with different N values:
```bash
# N = 100
python compare_methods.py --h-values scenario_100users.csv ... --run-blossom

# N = 500
python compare_methods.py --h-values scenario_500users.csv ... --run-blossom

# N = 2000 (skip Blossom - too slow!)
python compare_methods.py --h-values scenario_2000users.csv ...
```

## ⏱️ Performance Notes

**Expected Timing (approximate):**

| N Users | Static | Balanced | Bipartite | Blossom | GNN |
|---------|--------|----------|-----------|---------|-----|
| 100 | <1 ms | <1 ms | ~500 ms | ~2 s | ~100 ms |
| 500 | <1 ms | <1 ms | ~20 s | ~40 s | ~700 ms |
| 2000 | <1 ms | <1 ms | ~5 min | Hours! | ~12 s |

**Recommendations:**
- **N ≤ 500**: Run all methods including Blossom
- **500 < N ≤ 2000**: Skip Blossom (use `--run-blossom` flag only if needed)
- **N > 2000**: Only Static, Balanced, and GNN are practical

## 📝 Implementation Details

### Static Pairing
```python
# Sort users by channel gain
sorted_indices = np.argsort(h_linear)
# Pair strongest with weakest
pairs = [(sorted[i], sorted[N-1-i]) for i in range(N//2)]
```

### Balanced Pairing
```python
# Sort users by channel gain
sorted_indices = np.argsort(h_linear)
# Pair upper half with lower half
pairs = [(sorted[i], sorted[i+N//2]) for i in range(N//2)]
```

### Bipartite Matching
```python
# Split into weak (lower 50%) and strong (upper 50%)
weak = sorted_indices[:N//2]
strong = sorted_indices[N//2:]

# Build bipartite graph
G = nx.Graph()
for i in weak:
    for j in strong:
        if angle_diff(i, j) >= 25° and sic_satisfied(h[i], h[j]):
            weight = log(R1) + log(R2)  # PF weight
            G.add_edge(i, j, weight=weight)

# Maximum weight matching
pairs = nx.max_weight_matching(G, maxcardinality=True)
```

### Blossom Matching
```python
# Build complete graph
G = nx.Graph()
for i in range(N):
    for j in range(i+1, N):
        if sic_satisfied(h[i], h[j]):
            weight = R1 + R2  # Sum rate
            G.add_edge(i, j, weight=weight)

# Maximum weight matching (Edmonds' Blossom algorithm)
pairs = nx.max_weight_matching(G, maxcardinality=True)
```

### GNN Pairing
```python
# Build features: [h_db, angle, distance, is_los, h_rank]
x = build_features(...)

# Normalize
x = scaler.transform(x)

# Build edge index (all feasible pairs)
edge_index = build_edge_index(...)

# Run GNN
scores = model(x, edge_index)

# Greedy matching by score
pairs = greedy_match_by_score(scores)
```

## 🔬 Research Applications

1. **Paper Results**: Generate timing and throughput comparisons for research papers
2. **Ablation Studies**: Test GNN vs traditional methods on various scenarios
3. **Scalability Analysis**: Measure how each method scales with N
4. **Quality Metrics**: Compare pairing efficiency and spectral efficiency

## 📚 References

- Traditional methods: `codes/27sept/noma.py`
- GNN architecture: `models/pairpower_gnn.py`
- Training procedure: `training/train.py`

## ✅ Validation

All traditional methods have been validated against the original `noma.py` implementations:
- ✅ Static: Exact match (line 678)
- ✅ Balanced: Exact match (line 683)
- ✅ Bipartite: Exact match (lines 562-591)
- ✅ Blossom: Exact match (lines 686-703)

## 🎓 Author

Shailendra - October 2025
