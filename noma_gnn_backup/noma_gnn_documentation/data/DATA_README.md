# Data Module Documentation

## Overview
The data module handles all aspects of converting raw channel measurements into graph-structured data suitable for GNN training and inference. It consists of two primary components:

1. **Dataset Construction** (`dataset.py`): Graph building from CSV files
2. **Feature Normalization** (`normalization.py`): Scaling utilities

---

# dataset.py - Graph Construction

## Purpose
Transforms raw NOMA simulation results (user CSI and optimal pairs) into PyTorch Geometric `Data` objects for GNN processing.

## Key Concepts

### Input Data Format

#### Users CSV (`merged_h_values.csv`)
Each row represents one user in a simulation scenario:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `Graph_ID` | int | Scenario identifier | 0, 1, 2... |
| `User_ID` | int | User identifier within scenario | 0-499 |
| `distance_m` | float | 2D distance from base station (m) | 1234.5 |
| `angle_rad` | float | Polar angle (radians) | 2.34 |
| `path_loss_dB` | float | Large-scale path loss (dB) | 112.3 |
| `shadowing_dB` | float | Log-normal shadowing (dB) | -3.2 |
| `rayleigh_fading` | float | Small-scale fading amplitude | 0.89 |
| `h_linear` | float | Channel gain (linear scale) | 1.23e-6 |
| `h_dB` | float | Channel gain (dB) | -59.2 |

#### Pairs CSV (`merged_pairs.csv`)
Each row represents one NOMA pair or OMA user:

| Column | Type | Description |
|--------|------|-------------|
| `Graph_ID` | int | Links to user graph |
| `User1_ID` | int | Weak user (lower channel gain) |
| `User2_ID` | int | Strong user (higher channel gain) |
| `h1` | float | Weak user channel gain |
| `h2` | float | Strong user channel gain |
| `P1` | float | Power allocated to weak user |
| `P2` | float | Power allocated to strong user |
| `R1_bitsHz` | float | Weak user rate (bits/Hz) |
| `R2_bitsHz` | float | Strong user rate (bits/Hz) |
| `R_sum_bitsHz` | float | Sum rate |
| `Mode` | str | "NOMA" or "OMA" |

### PyTorch Geometric Data Object

Each scenario is converted to a `Data` object with:

```python
data = Data(
    x = [N, F],              # Node features (normalized)
    edge_index_pos = [2, E], # Positive edges (ground-truth pairs)
    y_pos_rsum = [E],        # Target sum-rates
    y_pos_alpha = [E],       # Target power splits
    num_nodes = N,           # Number of users
    
    # Auxiliary information for inference
    user_ids = [N],          # Original user IDs
    h_linear = [N],          # Channel gains (linear)
    h_db = [N],              # Channel gains (dB)
    angles = [N],            # User angles
    graph_id = str           # Scenario identifier
)
```

---

## Core Functions

### 1. SIC Feasibility Check

```python
def sic_satisfied(h1: float, h2: float, sic_db: float) -> bool:
    """
    Check if a pair satisfies Successive Interference Cancellation constraint.
    
    Args:
        h1: Channel gain of weak user (smaller value)
        h2: Channel gain of strong user (larger value)
        sic_db: Minimum gain difference threshold (default: 8 dB)
    
    Returns:
        True if |h2_dB - h1_dB| >= sic_db
    """
    if h1 <= 0 or h2 <= 0:
        return False
    return 10.0 * np.log10(h2 / h1) >= sic_db
```

**Mathematical Basis**:
$$\text{SIC feasible} \iff 10 \log_{10}\left(\frac{h_{\text{strong}}}{h_{\text{weak}}}\right) \geq \gamma_{\text{SIC}}$$

**Example**:
```python
h1 = 1e-6  # -60 dB
h2 = 1e-5  # -50 dB
sic_satisfied(h1, h2, 8.0)  # True (10 dB difference)

h1 = 5e-6  # -53 dB
h2 = 8e-6  # -51 dB  
sic_satisfied(h1, h2, 8.0)  # False (only 2 dB difference)
```

### 2. Angular Separation

```python
def angle_diff_rad(a, b):
    """
    Compute minimum angular difference on circle [0, 2π).
    
    Args:
        a, b: Angles in radians
    
    Returns:
        Minimum angle difference (accounts for wraparound)
    """
    d = np.abs(a - b) % (2*np.pi)
    return np.minimum(d, 2*np.pi - d)
```

**Why Important**: Users at similar angles experience correlated shadowing and interference. Angular separation improves channel diversity.

**Example**:
```python
angle_diff_rad(0.1, 6.2)    # ~0.183 rad (close, despite numeric difference)
angle_diff_rad(0, np.pi)    # π rad (maximum separation)
angle_diff_rad(0, 2*np.pi)  # 0 rad (same point on circle)
```

### 3. Main Graph Builder

```python
def build_graphs_from_merged(
    users_csv: str,
    pairs_csv: str,
    sic_db: float = 8.0,
    use_angle_guard: bool = True,
    min_angle_deg: float = 25.0,
    scaler_outpath: Optional[str] = None
) -> List[Data]:
    """
    Build PyG graph dataset from merged CSV files.
    
    Args:
        users_csv: Path to user features CSV
        pairs_csv: Path to optimal pairs CSV
        sic_db: SIC threshold in dB
        use_angle_guard: Enforce angular separation
        min_angle_deg: Minimum angle separation (degrees)
        scaler_outpath: Path to save feature scaler
    
    Returns:
        List of PyG Data objects (one per scenario)
    """
```

**Algorithm Flow**:

```
1. Load CSVs
   ├── Read users (channel features)
   └── Read pairs (optimal solutions)

2. Fit Feature Scaler
   ├── Compute mean/std across ALL users
   ├── Normalize: (x - μ) / σ
   └── Save scaler for inference consistency

3. For each Graph_ID:
   ├── Extract users for this scenario
   ├── Normalize features using global scaler
   ├── Create user_id → index mapping
   │
   ├── Filter pairs:
   │   ├── Keep only Mode="NOMA"
   │   ├── Ensure weak user first (h1 <= h2)
   │   └── Map user IDs to local indices
   │
   ├── Build positive edge index [2, E_pos]
   ├── Extract regression targets:
   │   ├── y_rsum = R_sum_bitsHz
   │   └── y_alpha = P1 / (P1 + P2)
   │
   ├── Store auxiliary data (angles, channel gains, IDs)
   └── Create Data object

4. Return list of graphs
```

**Example Usage**:
```python
from data.dataset import build_graphs_from_merged

graphs = build_graphs_from_merged(
    users_csv="data/raw/merged_h_values.csv",
    pairs_csv="data/raw/merged_pairs.csv",
    sic_db=8.0,
    use_angle_guard=True,
    min_angle_deg=25.0,
    scaler_outpath="data/processed/feature_scaler.json"
)

print(f"Created {len(graphs)} graphs")
print(f"Graph 0: {graphs[0].num_nodes} users, {graphs[0].edge_index_pos.size(1)} pairs")
```

---

## Implementation Details

### Feature Selection

The 5 node features are carefully chosen to capture different channel aspects:

| Feature | Physical Meaning | Typical Range | Importance |
|---------|------------------|---------------|------------|
| `distance_m` | User location | 100-5000 m | High (determines path loss) |
| `path_loss_dB` | Large-scale loss | 90-140 dB | Critical (primary factor) |
| `shadowing_dB` | Environmental effects | -20 to +20 dB | Medium (adds randomness) |
| `rayleigh_fading` | Small-scale variation | 0.1-3.0 | Medium (fast changes) |
| `h_dB` | Overall channel quality | -80 to -40 dB | High (composite metric) |

**Why These Features?**
- **Redundancy is OK**: `h_dB` is derived from others, but provides a normalized target for the model
- **Physical interpretability**: Each feature corresponds to a known propagation phenomenon
- **Balanced scales**: After normalization, all features contribute equally

### Edge Construction Logic

```python
# Ensure consistent ordering: weak first, strong second
h1 = pos_df["h1"].values
h2 = pos_df["h2"].values
u1 = pos_df["User1_ID"].values
u2 = pos_df["User2_ID"].values

# Map to local indices
a_idx = np.array([uid_to_idx[u] for u in u1], dtype=np.int64)
b_idx = np.array([uid_to_idx[u] for u in u2], dtype=np.int64)

edge_index_pos = torch.tensor(
    np.vstack([a_idx, b_idx]),  # Shape: [2, E]
    dtype=torch.long
)
```

**Critical**: Edge direction matters! Source = weak user, Target = strong user.

### Power Split Calculation

```python
P1 = pos_df["P1"].values.astype(np.float32)
P2 = pos_df["P2"].values.astype(np.float32)
denom = (P1 + P2 + 1e-12)  # Avoid division by zero
alpha = (P1 / denom).astype(np.float32)
```

**Alpha Interpretation**:
- $\alpha \in (0, 1)$: Fraction of total power to weak user
- Typically $\alpha > 0.5$ (weak user gets more power)
- Model predicts this value for new scenarios

---

# normalization.py - Feature Scaling

## Purpose
Provides z-score normalization with persistence for consistent feature scaling across training and inference.

## Z-Score Normalization

### Mathematical Definition

$$x_{\text{norm}} = \frac{x - \mu}{\sigma + \epsilon}$$

where:
- $\mu$ = mean of feature across all training data
- $\sigma$ = standard deviation
- $\epsilon = 10^{-8}$ = small constant to prevent division by zero

### Why Z-Score?

**Advantages**:
1. **Zero-centered**: Mean becomes 0, variance becomes 1
2. **Preserves outliers**: Doesn't squash to fixed range like min-max scaling
3. **Statistically motivated**: Based on Gaussian assumption
4. **Neural network friendly**: Helps with gradient flow and convergence

**Alternative Methods** (not used here):
- Min-Max: $x' = (x - x_{\min}) / (x_{\max} - x_{\min})$ → Sensitive to outliers
- Robust: Use median/IQR → Better for outliers but loses extreme values
- Whitening: Decorrelate features → Computationally expensive

## Scaler Class

```python
class Scaler:
    """
    Simple z-score scaler with save/load functionality.
    """
    
    def __init__(self):
        self.mean_ = None  # Will store [F] array
        self.std_ = None   # Will store [F] array
```

### Methods

#### 1. Fit
```python
def fit(self, X: np.ndarray):
    """
    Compute statistics from training data.
    
    Args:
        X: Feature matrix [N_samples, F_features]
    
    Returns:
        self (for method chaining)
    """
    self.mean_ = X.mean(axis=0)  # [F]
    self.std_ = X.std(axis=0) + 1e-8  # [F], add epsilon
    return self
```

**Example**:
```python
import numpy as np
from data.normalization import Scaler

# Sample data: 100 users, 5 features
X_train = np.random.randn(100, 5) * 10 + 50

scaler = Scaler()
scaler.fit(X_train)

print(scaler.mean_)  # ~[50, 50, 50, 50, 50]
print(scaler.std_)   # ~[10, 10, 10, 10, 10]
```

#### 2. Transform
```python
def transform(self, X: np.ndarray):
    """
    Apply normalization using fitted statistics.
    
    Args:
        X: Feature matrix [N_samples, F_features]
    
    Returns:
        Normalized features (same shape as X)
    """
    return (X - self.mean_) / self.std_
```

**Example**:
```python
X_test = np.array([[50, 60, 40, 55, 45]])
X_norm = scaler.transform(X_test)
print(X_norm)  # ~[[0, 1, -1, 0.5, -0.5]]
```

#### 3. Inverse Transform
```python
def inverse_transform(self, Xn: np.ndarray):
    """
    Reverse normalization (for interpretability).
    
    Args:
        Xn: Normalized features
    
    Returns:
        Original scale features
    """
    return Xn * self.std_ + self.mean_
```

**Use Case**: Converting model predictions back to physical units for visualization.

#### 4. Save
```python
def save(self, path: str):
    """
    Persist scaler parameters to JSON file.
    
    Args:
        path: Output JSON file path
    """
    d = {
        "mean": self.mean_.tolist(),
        "std": self.std_.tolist()
    }
    with open(path, "w") as f:
        json.dump(d, f)
```

**JSON Format**:
```json
{
  "mean": [1234.5, 115.2, 0.0, 0.98, -58.3],
  "std": [1456.3, 8.7, 8.2, 0.35, 12.1]
}
```

#### 5. Load
```python
@classmethod
def load(cls, path: str):
    """
    Load scaler from JSON file.
    
    Args:
        path: Input JSON file path
    
    Returns:
        Initialized Scaler object
    """
    with open(path, "r") as f:
        d = json.load(f)
    s = cls()
    s.mean_ = np.array(d["mean"], dtype=np.float32)
    s.std_ = np.array(d["std"], dtype=np.float32)
    return s
```

---

## Complete Workflow Example

### Training Phase

```python
# Step 1: Build graphs (fits and saves scaler)
from data.dataset import build_graphs_from_merged

graphs = build_graphs_from_merged(
    users_csv="merged_h_values.csv",
    pairs_csv="merged_pairs.csv",
    scaler_outpath="checkpoints/feature_scaler.json"
)

# Scaler statistics computed from ALL graphs
# Saved to checkpoints/feature_scaler.json
```

### Inference Phase

```python
# Step 1: Load scaler
from data.normalization import Scaler
scaler = Scaler.load("checkpoints/feature_scaler.json")

# Step 2: Load new scenario
import pandas as pd
df = pd.read_csv("new_scenario_h_values.csv")
X_raw = df[FEATURE_COLS].values

# Step 3: Normalize using SAME scaler as training
X_norm = scaler.transform(X_raw)

# Step 4: Feed to model
import torch
x = torch.tensor(X_norm, dtype=torch.float32)
# ... model inference ...
```

**Critical**: MUST use same scaler for training and inference, otherwise feature distributions mismatch!

---

## Best Practices

### DO:
✅ Fit scaler on entire training set before splitting train/val
✅ Save scaler immediately after fitting
✅ Use same scaler for all inference scenarios
✅ Version control scaler JSON alongside model checkpoints

### DON'T:
❌ Fit separate scalers for train/val/test
❌ Normalize each scenario independently
❌ Modify scaler after training
❌ Apply different normalization methods inconsistently

---

## Troubleshooting

### Issue: Features have very different scales after normalization
**Cause**: One feature has extremely small/large variance
**Solution**: Check for constant features or outliers; consider robust scaling

### Issue: Model performs poorly on new data
**Cause**: Forgot to normalize inference data or used wrong scaler
**Solution**: Always load and apply the saved training scaler

### Issue: Negative or unrealistic values after inverse_transform
**Cause**: Model predicted values outside training distribution
**Solution**: Add output clipping or train with data augmentation

---

## Advanced Topics

### Custom Normalization

If you need feature-specific normalization:

```python
class CustomScaler(Scaler):
    def transform(self, X):
        X_norm = super().transform(X)
        # Apply log to distance (first feature)
        X_norm[:, 0] = np.log1p(X_norm[:, 0])
        return X_norm
```

### Per-Graph Normalization

For scenarios with vastly different scales:

```python
def normalize_per_graph(graphs):
    for data in graphs:
        # Normalize within each graph
        x_mean = data.x.mean(dim=0, keepdim=True)
        x_std = data.x.std(dim=0, keepdim=True) + 1e-8
        data.x = (data.x - x_mean) / x_std
    return graphs
```

**Trade-off**: Better per-graph, but loses cross-graph comparability.

---

## References

1. **Standardization**: Goodfellow et al., "Deep Learning," Chapter 8 (2016)
2. **Feature Engineering**: Zheng & Casari, "Feature Engineering for Machine Learning," O'Reilly (2018)

---

**Last Updated**: October 2025
**Module Version**: 1.0
