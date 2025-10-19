# Configuration Module Documentation

## File: `config.py`

### Purpose
Provides centralized, type-safe configuration management for the entire NOMA-GNN system using Python dataclasses.

### Overview
The configuration module defines all hyperparameters, physical constants, and system settings in a single location, making it easy to:
- Modify experimental settings
- Track parameter changes
- Ensure consistency across modules
- Prevent errors through type checking

---

## Configuration Structure

### 1. Physics and System Parameters

```python
TOTAL_POWER: float = 1.0
```
**Description**: Total transmit power available for allocation (normalized to 1.0 watt).
**Usage**: Determines the power budget for all user pairs and OMA users.
**Typical Range**: 0.1 - 10.0

```python
NOISE_POWER: float = 1e-9
```
**Description**: Receiver noise power in watts (-90 dBm).
**Usage**: Used in SINR calculations for rate computation.
**Standard Values**: 1e-9 to 1e-10 (depends on bandwidth)

```python
SIC_THRESHOLD_DB: float = 8.0
```
**Description**: Minimum channel gain difference (in dB) required for successful Successive Interference Cancellation.
**Formula**: `10 * log10(h_strong / h_weak) >= SIC_THRESHOLD_DB`
**Typical Range**: 6-10 dB (8 dB is standard)

```python
BANDWIDTH_HZ: float = 20e6
```
**Description**: Total system bandwidth in Hertz (20 MHz).
**Usage**: Converts spectral efficiency (bits/Hz) to throughput (Mbps).
**Standard Values**: 10 MHz, 20 MHz, 40 MHz

---

### 2. Graph Construction Parameters

#### Message Passing Topology
```python
MP_TOPOLOGY: str = "bipartite_knn"
```
**Options**:
- `"bipartite_full"`: All weak users connected to all strong users (dense, slow)
- `"bipartite_knn"`: Each weak user connected to top-K strong users (recommended)
- `"knn"`: Standard KNN in feature space (less domain-specific)

**Recommendation**: Use `"bipartite_knn"` for best balance of performance and speed.

```python
MP_K: int = 8
```
**Description**: Number of neighbors per node in the message-passing graph.
**Impact**:
- Too small (K < 5): Underfitting, limited information propagation
- Too large (K > 20): Noise, computational overhead
- Sweet spot: 5-10 neighbors

#### Candidate Constraints
```python
USE_ANGLE_GUARD: bool = True
```
**Description**: Whether to enforce angular separation between paired users.
**Rationale**: Spatially close users cause excessive interference; angular guard improves channel diversity.

```python
MIN_ANGLE_DEG: float = 25.0
```
**Description**: Minimum angular separation (in degrees) between paired users.
**Formula**: `|angle_user1 - angle_user2| >= MIN_ANGLE_DEG`
**Typical Range**: 15-30 degrees

```python
TOPK_CANDIDATES_PER_NODE: int = 20
```
**Description**: Maximum number of candidate partners to score per user during inference.
**Purpose**: Computational speedup by pruning unlikely pairs before GNN scoring.
**Impact**:
- `None`: Score all feasible pairs (thorough but slow)
- `10-30`: Good balance (recommended)
- `> 50`: Marginal benefit

---

### 3. Model Architecture

```python
IN_CHANNELS: int = 5
```
**Description**: Number of input node features.
**Fixed Features**:
1. `distance_m`: Distance from base station
2. `path_loss_dB`: Large-scale path loss
3. `shadowing_dB`: Log-normal shadowing
4. `rayleigh_fading`: Small-scale fading amplitude
5. `h_dB`: Overall channel gain in dB

**Note**: If you add features, update this value and `FEATURE_COLS` in `dataset.py`.

```python
HIDDEN_DIM: int = 128
OUT_DIM: int = 128
```
**Description**: Dimensions of hidden layers and final node embeddings.
**Guidelines**:
- Smaller (64): Faster, less capacity
- Medium (128-256): Balanced (recommended)
- Larger (512+): High capacity, risk overfitting

```python
NUM_LAYERS: int = 3
```
**Description**: Number of GraphSAGE convolutional layers.
**Guidelines**:
- 2 layers: Minimum for local neighborhood aggregation
- 3-4 layers: Standard depth (recommended)
- 5+ layers: Risk of oversmoothing (node embeddings become too similar)

```python
DROPOUT: float = 0.2
```
**Description**: Dropout probability applied after each GNN layer (except last).
**Purpose**: Regularization to prevent overfitting.
**Typical Range**: 0.1-0.3

---

### 4. Training Hyperparameters

```python
LR: float = 1e-3
```
**Description**: Learning rate for Adam optimizer.
**Schedule**:
- Start: 1e-3
- If plateau: Reduce by 0.5× (e.g., to 5e-4, 2.5e-4)
- Minimum: 1e-5

```python
WEIGHT_DECAY: float = 1e-4
```
**Description**: L2 regularization coefficient for Adam.
**Purpose**: Prevents weight magnitudes from growing too large.

```python
EPOCHS: int = 60
```
**Description**: Maximum number of training epochs.
**Note**: Use early stopping (no validation improvement for 10 epochs) to avoid unnecessary training.

```python
BATCH_SIZE: int = 2
```
**Description**: Number of graphs processed per training step.
**Considerations**:
- Small (1-2): More gradient noise, fits in limited GPU memory
- Large (4-8): More stable gradients, requires more memory
- **Important**: Each "graph" is one full scenario with ~500 users

```python
SEED: int = 42
```
**Description**: Random seed for reproducibility.
**Usage**: Sets seeds for Python, NumPy, PyTorch to ensure deterministic behavior.

```python
DEVICE: str = "cuda"
```
**Options**: `"cuda"` or `"cpu"`
**Description**: Hardware acceleration device.
**Note**: Automatically falls back to CPU if CUDA unavailable.

---

### 5. Loss Function Weights

```python
LAMBDA_BCE: float = 1.0      # Edge existence classification
LAMBDA_RSUM: float = 0.5     # Sum-rate regression
LAMBDA_ALPHA: float = 0.5    # Power split regression
```

**Total Loss**:
```
L_total = LAMBDA_BCE * L_BCE + LAMBDA_RSUM * L_Rsum + LAMBDA_ALPHA * L_alpha
```

**Tuning Guidelines**:
- Start with equal weights (all 1.0)
- If edge classification is poor: Increase `LAMBDA_BCE`
- If power allocation is suboptimal: Increase `LAMBDA_ALPHA`
- If sum-rates are inaccurate: Increase `LAMBDA_RSUM`
- Monitor individual loss components during training

---

## Usage Examples

### Basic Usage
```python
from config import CFG

# Access parameters
print(f"Training for {CFG.EPOCHS} epochs")
print(f"SIC Threshold: {CFG.SIC_THRESHOLD_DB} dB")

# Use in model initialization
model = PairPowerGNN(
    in_channels=CFG.IN_CHANNELS,
    hidden=CFG.HIDDEN_DIM,
    out_channels=CFG.OUT_DIM,
    num_layers=CFG.NUM_LAYERS,
    dropout=CFG.DROPOUT
)
```

### Modifying Configuration
```python
from config import CFG

# Override before importing other modules
CFG.HIDDEN_DIM = 256
CFG.NUM_LAYERS = 4
CFG.EPOCHS = 100

# Now import and use
from training.train import train_model
```

### Creating Configuration Variants
```python
from dataclasses import replace
from config import CFG

# Create a variant for small-scale experiments
cfg_small = replace(CFG, 
    HIDDEN_DIM=64,
    NUM_LAYERS=2,
    BATCH_SIZE=1,
    EPOCHS=20
)

# Save configuration to file
import json
with open("experiment_config.json", "w") as f:
    json.dump(cfg_small.__dict__, f, indent=2)
```

---

## Parameter Interaction Effects

### Memory vs Performance Trade-offs

| Configuration | GPU Memory | Training Speed | Model Capacity |
|---------------|------------|----------------|----------------|
| Small (64-dim, 2-layer, BS=1) | ~2 GB | Fast | Limited |
| Medium (128-dim, 3-layer, BS=2) | ~4 GB | Moderate | Good |
| Large (256-dim, 4-layer, BS=4) | ~8 GB | Slow | High |

### Accuracy vs Speed Trade-offs

| Parameter | Increase → | Accuracy Impact | Speed Impact |
|-----------|------------|-----------------|--------------|
| `HIDDEN_DIM` | ↑ | Better (up to 256) | Slower (quadratic) |
| `NUM_LAYERS` | ↑ | Better (up to 4) | Slower (linear) |
| `MP_K` | ↑ | Better (plateau ~10) | Slower (linear) |
| `TOPK_CANDIDATES` | ↑ | Better (marginal) | Slower (log) |
| `DROPOUT` | ↑ | U-shaped (0.2 optimal) | Negligible |

---

## Best Practices

### For Training
1. **Start with defaults**: The provided defaults work well for most scenarios
2. **Monitor validation metrics**: Adjust hyperparameters if validation AUC < 0.7 after 20 epochs
3. **Use early stopping**: Don't train full 60 epochs if validation plateaus
4. **Log configurations**: Save `CFG` to JSON for experiment tracking

### For Inference
1. **Keep consistency**: Use the same config as training (especially feature-related params)
2. **Optimize for speed**: Reduce `TOPK_CANDIDATES` if inference is bottleneck
3. **Verify constraints**: Check `SIC_THRESHOLD_DB` and `MIN_ANGLE_DEG` match deployment requirements

### For Experimentation
1. **One change at a time**: Modify one parameter to isolate effects
2. **Grid search**: For critical params like `HIDDEN_DIM`, `NUM_LAYERS`, `LR`
3. **Document changes**: Keep a log of configuration variants and their results

---

## Common Issues and Solutions

### Issue: Training unstable (loss oscillates)
**Solution**: 
- Reduce `LR` to 5e-4 or 1e-4
- Increase `BATCH_SIZE` if memory allows
- Add gradient clipping (in training loop)

### Issue: Model overfits (train AUC high, val AUC low)
**Solution**:
- Increase `DROPOUT` to 0.3-0.4
- Reduce `HIDDEN_DIM` or `NUM_LAYERS`
- Add more training data (diverse scenarios)

### Issue: Poor SIC satisfaction rate in inference
**Solution**:
- Increase `SIC_THRESHOLD_DB` slightly (e.g., 8.5 or 9.0)
- Verify `MIN_ANGLE_DEG` is enforced in candidate generation

### Issue: Inference too slow
**Solution**:
- Reduce `TOPK_CANDIDATES_PER_NODE` to 10-15
- Use `MP_TOPOLOGY = "bipartite_knn"` with small `MP_K = 5`
- Export model to ONNX for faster inference

---

## Version History

- **v1.0**: Initial configuration with bipartite KNN topology
- **v1.1**: Added `TOPK_CANDIDATES_PER_NODE` for inference speedup
- **v1.2**: Introduced loss weight tuning parameters

---

## References

1. **GraphSAGE**: Hamilton et al., "Inductive Representation Learning on Large Graphs," NeurIPS 2017
2. **NOMA**: Ding et al., "Application of Non-Orthogonal Multiple Access in LTE and 5G Networks," IEEE CommMag 2017
3. **3GPP Standards**: TR 38.901 for channel modeling parameters

---

**Last Updated**: October 2025  
**Maintained by**: NOMA-GNN Development Team
