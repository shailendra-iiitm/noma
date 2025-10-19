# Data Preparation Script Documentation

## 📋 File: `scripts/prepare_data.py`

### 🎯 Purpose
Preprocesses raw CSV data files and converts them into PyTorch Geometric graph objects for efficient training. This script is the **first step** in the NOMA-GNN workflow.

---

## 🔄 Data Flow

```
Raw CSVs              →    PyG Graphs           →    Saved Files
--------------------------------------------------------------------
merged_h_values.csv   →    Graph objects        →    dataset.pt
merged_pairs.csv      →    with normalized      →    feature_scaler.json
                           features
```

---

## 📊 Input Data Format

### 1. Users CSV (`merged_h_values.csv`)

**Required Columns**:
```csv
Graph_ID,User_ID,x,y,angle_deg,angle_rad,distance,h_linear,h_dB,snr_dB,snr_linear
0,0,123.45,67.89,45.0,0.7854,150.23,0.000123,-39.10,10.90,12.303
0,1,234.56,78.90,90.0,1.5708,200.45,0.000089,-40.51,9.49,8.902
0,2,345.67,89.01,135.0,2.3562,250.67,0.000067,-41.74,8.26,6.702
...
1,0,456.78,90.12,180.0,3.1416,300.89,0.000056,-42.52,7.48,5.596
1,1,567.89,01.23,225.0,3.9270,350.12,0.000045,-43.47,6.53,4.495
...
```

**Column Descriptions**:
- **Graph_ID**: Scenario/topology identifier (groups users into graphs)
- **User_ID**: Unique user identifier within a graph
- **x, y**: 2D Cartesian coordinates (meters)
- **angle_deg**: Angle from base station (degrees)
- **angle_rad**: Angle from base station (radians)
- **distance**: Distance from base station (meters)
- **h_linear**: Channel gain (linear scale)
- **h_dB**: Channel gain (dB scale): $10 \log_{10}(h_{\text{linear}})$
- **snr_dB**: Signal-to-Noise Ratio (dB)
- **snr_linear**: SNR (linear scale)

### 2. Pairs CSV (`merged_pairs.csv`)

**Required Columns**:
```csv
Graph_ID,User1_ID,User2_ID,alpha,R_sum_bitsHz
0,0,250,0.72,2.345
0,1,251,0.68,2.123
0,2,252,0.75,2.456
...
1,0,300,0.70,2.234
1,1,301,0.73,2.412
...
```

**Column Descriptions**:
- **Graph_ID**: Matches Graph_ID in users CSV
- **User1_ID**: Weak user (lower channel gain)
- **User2_ID**: Strong user (higher channel gain)
- **alpha**: Optimal power split (fraction to weak user)
- **R_sum_bitsHz**: Sum-rate of the pair (bits/Hz)

---

## 🏗️ Script Functionality

### Complete Script

```python
"""
Prepare PyG graphs from merged CSVs and save as a .pt file for quick loading.
"""
import os, argparse, torch
from data.dataset import build_graphs_from_merged

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--users_csv", required=True, help="merged_h_values.csv")
    ap.add_argument("--pairs_csv", required=True, help="merged_pairs.csv")
    ap.add_argument("--out_pt", default="graph_dataset.pt")
    ap.add_argument("--scaler_out", default="feature_scaler.json")
    args = ap.parse_args()

    # Build PyG graphs with normalized features
    graphs = build_graphs_from_merged(
        args.users_csv, 
        args.pairs_csv,
        sic_db=8.0,              # SIC threshold (dB)
        use_angle_guard=True,    # Apply angular constraint
        min_angle_deg=25.0,      # Minimum angular separation
        scaler_outpath=args.scaler_out  # Save normalization params
    )
    
    # Save graph dataset
    torch.save(graphs, args.out_pt)
    
    print(f"✅ Saved {len(graphs)} graphs to {args.out_pt}")
    print(f"✅ Saved scaler to {args.scaler_out}")

if __name__ == "__main__":
    main()
```

---

## 📦 Output Files

### 1. Graph Dataset (`graph_dataset.pt`)

**Structure**: List of PyTorch Geometric `Data` objects

**Each Graph Object Contains**:
```python
Data(
    x=[N, F],                    # Node features (normalized)
    edge_index_pos=[2, E_pos],   # Positive edges (ground truth pairs)
    y_pos_rsum=[E_pos],          # Sum-rate labels for positive edges
    y_pos_alpha=[E_pos],         # Alpha labels for positive edges
    h_linear=[N],                # Channel gains (linear scale)
    h_db=[N],                    # Channel gains (dB scale)
    angles=[N],                  # User angles (radians)
    num_nodes=N                  # Number of users in graph
)
```

**Example**:
```python
import torch
graphs = torch.load("graph_dataset.pt")
print(f"Number of graphs: {len(graphs)}")
print(f"First graph: {graphs[0]}")

# Output:
# Number of graphs: 100
# First graph: Data(x=[500, 10], edge_index_pos=[2, 240], 
#                    y_pos_rsum=[240], y_pos_alpha=[240], 
#                    h_linear=[500], h_db=[500], angles=[500])
```

### 2. Feature Scaler (`feature_scaler.json`)

**Structure**: JSON file with normalization parameters

**Format**:
```json
{
    "mean": [0.123, 0.456, ...],   // Mean of each feature
    "std": [1.234, 2.345, ...],    // Std of each feature
    "feature_names": ["x", "y", "angle_rad", ...]
}
```

**Purpose**:
- **Training**: Normalize training data to zero mean, unit variance
- **Inference**: Apply same normalization to new scenarios

**Critical**: Must use training scaler for inference consistency!

---

## 🎯 Usage Examples

### Example 1: Basic Usage

```bash
python -m scripts.prepare_data \
    --users_csv data/raw/merged_h_values.csv \
    --pairs_csv data/raw/merged_pairs.csv \
    --out_pt data/processed/graph_dataset.pt \
    --scaler_out checkpoints/feature_scaler.json
```

**Output**:
```
✅ Saved 100 graphs to data/processed/graph_dataset.pt
✅ Saved scaler to checkpoints/feature_scaler.json
```

### Example 2: Custom Constraints

```python
# Modify before running script
from config import CFG

# More strict constraints (fewer pairs, higher quality)
CFG.SIC_THRESHOLD_DB = 10.0
CFG.MIN_ANGLE_DEG = 30.0

# Then run script
python -m scripts.prepare_data ...
```

### Example 3: Multiple Datasets

```bash
# Prepare train set
python -m scripts.prepare_data \
    --users_csv data/raw/train_users.csv \
    --pairs_csv data/raw/train_pairs.csv \
    --out_pt data/processed/train_graphs.pt \
    --scaler_out checkpoints/train_scaler.json

# Prepare test set (use same scaler!)
python -m scripts.prepare_data \
    --users_csv data/raw/test_users.csv \
    --pairs_csv data/raw/test_pairs.csv \
    --out_pt data/processed/test_graphs.pt \
    --scaler_out checkpoints/train_scaler.json  # Reuse train scaler!
```

### Example 4: Inspect Processed Graphs

```python
import torch
from torch_geometric.data import Data

# Load graphs
graphs = torch.load("data/processed/graph_dataset.pt")

# Statistics
print(f"Total graphs: {len(graphs)}")
print(f"Avg nodes per graph: {sum(g.num_nodes for g in graphs) / len(graphs):.1f}")
print(f"Avg pairs per graph: {sum(g.edge_index_pos.size(1) for g in graphs) / len(graphs):.1f}")

# Inspect first graph
g = graphs[0]
print(f"\nFirst graph:")
print(f"  Nodes: {g.num_nodes}")
print(f"  Positive edges: {g.edge_index_pos.size(1)}")
print(f"  Feature dim: {g.x.size(1)}")
print(f"  Avg sum-rate: {g.y_pos_rsum.mean():.4f} bits/Hz")
print(f"  Avg alpha: {g.y_pos_alpha.mean():.4f}")

# Feature statistics (should be normalized)
print(f"\nFeature statistics (normalized):")
print(f"  Mean: {g.x.mean(dim=0)}")
print(f"  Std: {g.x.std(dim=0)}")
# Should be close to [0, 0, ..., 0] and [1, 1, ..., 1]
```

---

## 🔍 Data Validation

### Pre-Processing Checks

```python
import pandas as pd

# Load raw CSVs
users_df = pd.read_csv("data/raw/merged_h_values.csv")
pairs_df = pd.read_csv("data/raw/merged_pairs.csv")

# 1. Check for missing values
print("Missing values in users CSV:")
print(users_df.isnull().sum())

print("\nMissing values in pairs CSV:")
print(pairs_df.isnull().sum())

# 2. Check Graph_ID consistency
user_graph_ids = set(users_df["Graph_ID"].unique())
pair_graph_ids = set(pairs_df["Graph_ID"].unique())

assert pair_graph_ids.issubset(user_graph_ids), \
    "Pairs CSV contains Graph_IDs not in users CSV!"

print(f"\n✅ {len(user_graph_ids)} unique graphs found")

# 3. Check User_ID consistency
for gid in pair_graph_ids:
    graph_users = set(users_df[users_df["Graph_ID"]==gid]["User_ID"].unique())
    graph_pairs = pairs_df[pairs_df["Graph_ID"]==gid]
    
    for _, row in graph_pairs.iterrows():
        assert row["User1_ID"] in graph_users, \
            f"User1_ID {row['User1_ID']} not found in graph {gid}"
        assert row["User2_ID"] in graph_users, \
            f"User2_ID {row['User2_ID']} not found in graph {gid}"

print("✅ All User_IDs in pairs exist in users CSV")

# 4. Check value ranges
assert (users_df["h_linear"] > 0).all(), "Invalid h_linear values!"
assert (users_df["distance"] > 0).all(), "Invalid distance values!"
assert (pairs_df["alpha"] >= 0).all() and (pairs_df["alpha"] <= 1).all(), \
    "Alpha must be in [0, 1]!"

print("✅ Value ranges are valid")
```

### Post-Processing Checks

```python
import torch

# Load processed graphs
graphs = torch.load("data/processed/graph_dataset.pt")

# 1. Check feature normalization
all_features = torch.cat([g.x for g in graphs], dim=0)
print(f"Feature mean: {all_features.mean(dim=0)}")
print(f"Feature std: {all_features.std(dim=0)}")
# Should be close to 0 and 1

# 2. Check for NaN/Inf
for i, g in enumerate(graphs):
    assert torch.isfinite(g.x).all(), f"NaN/Inf in graph {i} features"
    assert torch.isfinite(g.y_pos_rsum).all(), f"NaN/Inf in graph {i} sum-rates"
    assert torch.isfinite(g.y_pos_alpha).all(), f"NaN/Inf in graph {i} alphas"

print("✅ No NaN/Inf values in graphs")

# 3. Check edge indices
for i, g in enumerate(graphs):
    assert (g.edge_index_pos[0] < g.num_nodes).all(), \
        f"Invalid source nodes in graph {i}"
    assert (g.edge_index_pos[1] < g.num_nodes).all(), \
        f"Invalid target nodes in graph {i}"

print("✅ Edge indices are valid")

# 4. Check label ranges
for g in graphs:
    assert (g.y_pos_rsum > 0).all(), "Sum-rate must be positive"
    assert (g.y_pos_alpha >= 0).all() and (g.y_pos_alpha <= 1).all(), \
        "Alpha must be in [0, 1]"

print("✅ Label ranges are valid")
```

---

## 🐛 Troubleshooting

### Issue 1: Missing Columns

**Error**:
```
KeyError: 'h_dB' not found in columns
```

**Solution**:
```python
# Check CSV columns
import pandas as pd
df = pd.read_csv("data/raw/merged_h_values.csv")
print("Columns:", df.columns.tolist())

# Ensure all required columns exist:
# ['Graph_ID', 'User_ID', 'x', 'y', 'angle_deg', 'angle_rad', 
#  'distance', 'h_linear', 'h_dB', 'snr_dB', 'snr_linear']
```

### Issue 2: Empty Graphs

**Symptoms**:
```
✅ Saved 0 graphs to graph_dataset.pt
```

**Causes**:
1. No matching Graph_IDs between users and pairs CSVs
2. All pairs filtered out by constraints

**Solutions**:
```python
# Check Graph_ID overlap
users_df = pd.read_csv("data/raw/merged_h_values.csv")
pairs_df = pd.read_csv("data/raw/merged_pairs.csv")

user_gids = set(users_df["Graph_ID"])
pair_gids = set(pairs_df["Graph_ID"])

print(f"User graphs: {len(user_gids)}")
print(f"Pair graphs: {len(pair_gids)}")
print(f"Overlap: {len(user_gids & pair_gids)}")

# If overlap is 0, check for data format issues
```

### Issue 3: Memory Error

**Error**:
```
MemoryError: Unable to allocate array
```

**Solution**:
```python
# Process graphs in batches
from data.dataset import build_graphs_from_merged
import torch

# Get unique Graph_IDs
import pandas as pd
users_df = pd.read_csv("data/raw/merged_h_values.csv")
graph_ids = users_df["Graph_ID"].unique()

# Process in chunks
batch_size = 20
all_graphs = []

for i in range(0, len(graph_ids), batch_size):
    batch_gids = graph_ids[i:i+batch_size]
    
    # Filter CSVs for this batch
    batch_users = users_df[users_df["Graph_ID"].isin(batch_gids)]
    batch_pairs = pairs_df[pairs_df["Graph_ID"].isin(batch_gids)]
    
    # Save temporary CSVs
    batch_users.to_csv("temp_users.csv", index=False)
    batch_pairs.to_csv("temp_pairs.csv", index=False)
    
    # Build graphs
    graphs = build_graphs_from_merged(
        "temp_users.csv", "temp_pairs.csv",
        scaler_outpath="scaler.json" if i == 0 else None
    )
    
    all_graphs.extend(graphs)
    print(f"Processed batch {i//batch_size + 1}: {len(graphs)} graphs")

# Save all graphs
torch.save(all_graphs, "graph_dataset.pt")
```

---

## ✅ Best Practices

### 1. Data Organization
```
project/
├── data/
│   ├── raw/                    # Original CSVs
│   │   ├── merged_h_values.csv
│   │   └── merged_pairs.csv
│   └── processed/              # Generated graphs
│       ├── graph_dataset.pt
│       └── feature_scaler.json
```

### 2. Separate Train/Val/Test
```bash
# Don't split after loading - split at CSV level
# Train set
python -m scripts.prepare_data \
    --users_csv data/raw/train_users.csv \
    --pairs_csv data/raw/train_pairs.csv \
    --out_pt data/processed/train.pt

# Val set (use train scaler!)
python -m scripts.prepare_data \
    --users_csv data/raw/val_users.csv \
    --pairs_csv data/raw/val_pairs.csv \
    --out_pt data/processed/val.pt \
    --scaler_out data/processed/train_scaler.json

# Test set (use train scaler!)
python -m scripts.prepare_data \
    --users_csv data/raw/test_users.csv \
    --pairs_csv data/raw/test_pairs.csv \
    --out_pt data/processed/test.pt \
    --scaler_out data/processed/train_scaler.json
```

### 3. Version Control
```bash
# Track data versions
git lfs track "*.pt"
git lfs track "*.csv"
git add data/raw/*.csv
git commit -m "Add raw data v1.0"
```

### 4. Documentation
```python
# Add metadata to saved graphs
metadata = {
    "created": "2025-10-17",
    "num_graphs": len(graphs),
    "sic_threshold_db": 8.0,
    "min_angle_deg": 25.0,
    "source_files": {
        "users": "merged_h_values.csv",
        "pairs": "merged_pairs.csv"
    }
}

torch.save({
    "graphs": graphs,
    "metadata": metadata
}, "graph_dataset.pt")
```

---

**Last Updated**: October 17, 2025  
**Version**: 1.0.0  
**Author**: NOMA-GNN Development Team
