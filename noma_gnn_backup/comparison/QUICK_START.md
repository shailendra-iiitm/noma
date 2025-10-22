# Comparison Folder - Quick Start Guide

## 📁 What's in This Folder?

This is a **standalone** comparison tool for evaluating NOMA pairing methods. All implementations are **exact copies** from `codes/27sept/noma.py`.

```
comparison/
├── compare_methods.py                      # Main comparison script
├── README.md                               # Detailed documentation
├── run_comparison_500users.bat             # Quick test (no Blossom)
├── run_comparison_500users_with_blossom.bat # Full test (includes Blossom)
└── comparison_results_*.csv                # Output files (generated)
```

## 🚀 Quick Start

### Option 1: Run Batch Script (Windows)
```cmd
# Fast comparison (skip Blossom)
run_comparison_500users.bat

# Full comparison (includes Blossom - ~40s wait)
run_comparison_500users_with_blossom.bat
```

### Option 2: Command Line
```bash
# Basic usage (recommended for N > 500)
python compare_methods.py \
  --h-values ../test_scenario_500users.csv \
  --ckpt ../checkpoints/best_model.pt \
  --scaler ../data/processed/feature_scaler.json

# Include Blossom (only for N ≤ 500)
python compare_methods.py \
  --h-values ../test_scenario_500users.csv \
  --ckpt ../checkpoints/best_model.pt \
  --scaler ../data/processed/feature_scaler.json \
  --run-blossom
```

## 📊 What Gets Compared?

| Method | Source | Time Complexity |
|--------|--------|----------------|
| Static | noma.py line 678 | O(N log N) |
| Balanced | noma.py line 683 | O(N log N) |
| Bipartite | noma.py lines 562-591 | O(N³) |
| Blossom | noma.py lines 686-703 | O(N³) |
| NOMA-GNN | Proposed | O(N log N) |

## 📈 Output Metrics

Each method is evaluated on:

1. **Execution Time** - Average over 3 iterations
2. **Pairs Formed** - Number of successful pairings
3. **Pairing Efficiency** - % of users paired
4. **Total Throughput** - System capacity (Mbps)
5. **Average Sum Rate** - Spectral efficiency per pair

## 🎯 Use Cases

### 1. Paper Results
Generate timing comparison for research paper:
```bash
python compare_methods.py --h-values my_test_scenario.csv ... --output paper_results.csv
```

### 2. Multiple Scenarios
Test on different datasets (bash/PowerShell loop):
```bash
# PowerShell
Get-ChildItem test_scenarios\*.csv | ForEach-Object {
    python compare_methods.py `
        --h-values $_.FullName `
        --ckpt ..\checkpoints\best_model.pt `
        --scaler ..\data\processed\feature_scaler.json `
        --output "results_$($_.BaseName).csv"
}
```

### 3. Different User Counts
```bash
# N = 100 (fast, can run Blossom)
python compare_methods.py --h-values scenario_100.csv ... --run-blossom

# N = 500 (medium, Blossom takes ~40s)
python compare_methods.py --h-values scenario_500.csv ... --run-blossom

# N = 2000 (large, skip Blossom!)
python compare_methods.py --h-values scenario_2000.csv ...
```

## 📋 Input File Requirements

Your CSV must have:
- `h_linear` (required)
- `angle` or `angle_rad` or `theta` (required)
- `distance` or `distance_m` or `d_2D` (optional, can use zeros)
- `is_los` or `is_LOS` (optional, defaults to False)

**Example from test_scenario_500users.csv:**
```csv
User_ID,x_coord_m,y_coord_m,distance_m,angle_rad,h_linear,h_dB,Graph_ID
0,1234.5,2345.6,2678.9,1.234,0.000123,-39.1,0
1,3456.7,4567.8,5789.0,2.345,0.000456,-33.4,0
...
```

## ⏱️ Expected Runtimes

| N Users | Static | Balanced | Bipartite | Blossom | GNN |
|---------|--------|----------|-----------|---------|-----|
| 100 | <1 ms | <1 ms | ~500 ms | ~2 s | ~100 ms |
| 500 | <1 ms | <1 ms | ~20 s | ~40 s | ~700 ms |
| 2000 | <1 ms | <1 ms | ~5 min | Hours! | ~12 s |

**TIP**: For N > 500, skip Blossom (don't use `--run-blossom` flag)

## 📊 Sample Output

```
Method      Time_ms  Time_std_ms  Pairs  Pairing_Efficiency_%  Throughput_Mbps  Avg_Sum_Rate_bps_Hz
Static         0.28         0.26    250                  100.0           543.21                 8.67
Balanced       0.08         0.03    250                  100.0           521.34                 8.34
Bipartite  20709.58      2078.68    232                   92.8           612.45                10.56
Blossom    39271.37         0.00    232                   92.8           634.78                10.94
NOMA-GNN     707.19        79.76    203                   81.2           598.23                11.79
```

## ✅ Validation

All implementations validated against noma.py:
- ✅ Static: Exact match (strongest-weakest)
- ✅ Balanced: Exact match (upper-lower half)
- ✅ Bipartite: Exact match (graph PF matching)
- ✅ Blossom: Exact match (general max matching)

## 🔧 Troubleshooting

**Error: "Missing column: angle"**
→ Use `angle_rad` or `theta` in your CSV

**Error: "Missing column: distance"**
→ Use `distance_m` or `d_2D`, or script will use zeros

**Bipartite/Blossom taking too long**
→ These are O(N³)! For N>500, expect long wait times

**GNN produces fewer pairs than others**
→ This is expected - GNN learns quality over quantity

## 📚 For More Details

See `README.md` for:
- Complete API documentation
- Implementation details for each method
- Advanced usage examples
- Parameter tuning guide

## 🎓 Citation

If you use this comparison tool in your research, please cite the exact implementations from:
- Traditional methods: `codes/27sept/noma.py`
- GNN method: `models/pairpower_gnn.py`

---

**Author**: Shailendra  
**Date**: October 2025  
**Purpose**: Research comparison for NOMA pairing methods
