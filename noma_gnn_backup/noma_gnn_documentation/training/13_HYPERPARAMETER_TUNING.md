# Hyperparameter Tuning Guide

## 🎯 Purpose
Comprehensive guide to tuning NOMA-GNN hyperparameters for optimal performance across different scenarios.

---

## 📊 Hyperparameter Categories

### 1. Model Architecture
### 2. Training Configuration
### 3. Loss Weights
### 4. Data Processing
### 5. Regularization

---

## 🏗️ Model Architecture Hyperparameters

### Hidden Dimension (`HIDDEN_DIM`)

**Description**: Size of learned node embeddings

**Default**: 128

**Impact**:
- **Larger → More capacity** to learn complex patterns
- **Smaller → Faster training**, less overfitting

**Tuning Guide**:
```python
# Small networks (N < 300 users)
CFG.HIDDEN_DIM = 64

# Medium networks (N = 300-500 users)
CFG.HIDDEN_DIM = 128

# Large networks (N > 500 users)
CFG.HIDDEN_DIM = 256
```

**Recommendations**:
| Network Size | Hidden Dim | Parameters | Training Time |
|--------------|------------|------------|---------------|
| Small (< 300) | 64 | ~50K | Fast |
| Medium (300-500) | 128 | ~130K | Medium |
| Large (> 500) | 256 | ~500K | Slow |

**Experiments**:
```python
results = {}
for hidden in [32, 64, 128, 256]:
    model = PairPowerGNN(hidden_dim=hidden, ...)
    auc, mae_r, mae_a = train_and_evaluate(model)
    results[hidden] = {"auc": auc, "mae_rsum": mae_r, "mae_alpha": mae_a}
    
# Expected: 128-256 is sweet spot for most cases
```

---

### Number of Layers (`NUM_LAYERS`)

**Description**: Depth of GraphSAGE encoder

**Default**: 3

**Impact**:
- **More layers** → Larger receptive field, captures higher-order patterns
- **Fewer layers** → Less computational cost, avoids over-smoothing

**Tuning Guide**:
```python
# Sparse graphs (low connectivity)
CFG.NUM_LAYERS = 2

# Dense graphs (high connectivity)
CFG.NUM_LAYERS = 3

# Very large graphs
CFG.NUM_LAYERS = 4  # Caution: over-smoothing risk
```

**Over-Smoothing Problem**:
```
Layer 1: Nodes learn from 1-hop neighbors (K neighbors)
Layer 2: Nodes learn from 2-hop neighbors (K^2 neighbors)
Layer 3: Nodes learn from 3-hop neighbors (K^3 neighbors)
...
Layer L: All nodes have similar embeddings (information loss!)
```

**Recommendations**:
- **Rule of thumb**: Num layers ≤ Graph diameter
- **For bipartite KNN (K=8)**: 2-3 layers is optimal
- **Test performance**: Add layers until validation AUC plateaus

**Experiments**:
```python
for num_layers in [1, 2, 3, 4, 5]:
    model = PairPowerGNN(num_layers=num_layers, ...)
    auc = evaluate_model(model)
    print(f"Layers: {num_layers} → AUC: {auc:.4f}")

# Expected:
# Layers: 1 → AUC: 0.82 (insufficient)
# Layers: 2 → AUC: 0.89 (good)
# Layers: 3 → AUC: 0.92 (optimal)
# Layers: 4 → AUC: 0.91 (over-smoothing)
```

---

### Output Dimension (`OUT_DIM`)

**Description**: Dimension after final GraphSAGE layer (before decoders)

**Default**: 64

**Impact**:
- **Larger** → More expressive edge embeddings
- **Smaller** → Fewer parameters, faster inference

**Tuning Guide**:
```python
# Simple pairing criteria (mostly channel-based)
CFG.OUT_DIM = 32

# Complex pairing criteria (multi-factor)
CFG.OUT_DIM = 64

# Very complex scenarios (interference-heavy)
CFG.OUT_DIM = 128
```

**Recommendations**:
- **Typical**: 64 (balanced)
- **Memory-constrained**: 32
- **Performance-critical**: 128

---

### Dropout Rate (`DROPOUT`)

**Description**: Probability of dropping neurons during training

**Default**: 0.2

**Impact**:
- **Higher → Stronger regularization**, prevents overfitting
- **Lower → Retains more information**, risks overfitting

**Tuning Based on Overfitting**:
```python
# No overfitting (Train AUC ≈ Val AUC)
CFG.DROPOUT = 0.1

# Mild overfitting (Train AUC > Val AUC by 0.02-0.05)
CFG.DROPOUT = 0.2

# Severe overfitting (Train AUC > Val AUC by > 0.1)
CFG.DROPOUT = 0.4
```

**Recommended Schedule**:
```python
# Start with low dropout for fast learning
epochs 1-20: dropout = 0.1
epochs 21-40: dropout = 0.2
epochs 41+: dropout = 0.3
```

---

## 🎓 Training Configuration

### Learning Rate (`LR`)

**Description**: Step size for gradient descent

**Default**: 1e-3 (0.001)

**Impact**:
- **Too high** → Training unstable, loss oscillates, may diverge
- **Too low** → Training slow, may get stuck in local minima

**Tuning Guide**:
```python
# Learning rate range test
lrs = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2]
for lr in lrs:
    model = PairPowerGNN(...)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    losses = train_for_epochs(model, optimizer, num_epochs=10)
    print(f"LR: {lr} → Final Loss: {losses[-1]:.4f}")
```

**Typical Ranges**:
- **AdamW optimizer**: 1e-4 to 1e-3
- **SGD optimizer**: 1e-2 to 1e-1
- **Large batch size**: Higher LR (scale with sqrt(batch_size))
- **Small batch size**: Lower LR

**Learning Rate Schedules**:

**1. Step Decay**:
```python
scheduler = torch.optim.lr_scheduler.StepLR(
    optimizer, step_size=20, gamma=0.5
)
# Reduces LR by 50% every 20 epochs
```

**2. Cosine Annealing**:
```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer, T_max=50, eta_min=1e-6
)
# Smoothly decreases LR following cosine curve
```

**3. Reduce on Plateau**:
```python
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='max', factor=0.5, patience=5, verbose=True
)
# Reduces LR when validation AUC stops improving
```

**Recommended**:
```python
# Best practice: Start high, decay
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='max', factor=0.5, patience=5
)

for epoch in range(num_epochs):
    train_loss = train_one_epoch(...)
    val_auc = evaluate(...)
    scheduler.step(val_auc)  # Adjust LR based on AUC
```

---

### Batch Size (`BATCH_SIZE`)

**Description**: Number of graphs processed together

**Default**: 2

**Impact**:
- **Larger** → More stable gradients, faster training (if fits in memory)
- **Smaller** → More frequent updates, better generalization

**Memory Constraints**:
```python
# Estimate GPU memory usage
memory_per_graph = num_nodes * hidden_dim * num_layers * 4 bytes
total_memory = batch_size * memory_per_graph

# Example: 500 nodes, 128 hidden, 3 layers, batch=2
memory = 2 * 500 * 128 * 3 * 4 = 1.5 MB (negligible)

# Real bottleneck: Edge lists and intermediate activations
# Rule of thumb: Start with batch_size=2, increase if memory allows
```

**Tuning Guide**:
```python
# Small GPU (4 GB)
CFG.BATCH_SIZE = 1

# Medium GPU (8-16 GB)
CFG.BATCH_SIZE = 2

# Large GPU (32+ GB)
CFG.BATCH_SIZE = 4
```

**Batch Size vs. Performance**:
```
Batch Size | Convergence Speed | Generalization
-----------|-------------------|----------------
1          | Slow              | Best
2          | Medium            | Good
4          | Fast              | Fair
8+         | Very Fast         | Poor (for graphs)
```

---

### Number of Epochs (`EPOCHS`)

**Description**: Number of passes through training data

**Default**: 60

**Tuning Guide**:
```python
# Quick experimentation
CFG.EPOCHS = 20

# Standard training
CFG.EPOCHS = 60

# Careful tuning
CFG.EPOCHS = 100

# Always use early stopping!
```

**Early Stopping**:
```python
best_auc = -1.0
patience = 10
epochs_no_improve = 0

for epoch in range(1, max_epochs+1):
    train(...)
    val_auc = evaluate(...)
    
    if val_auc > best_auc:
        best_auc = val_auc
        epochs_no_improve = 0
        save_checkpoint(...)
    else:
        epochs_no_improve += 1
    
    if epochs_no_improve >= patience:
        print(f"Early stopping at epoch {epoch}")
        break
```

---

### Weight Decay (`WEIGHT_DECAY`)

**Description**: L2 regularization strength

**Default**: 1e-4

**Impact**:
- **Higher** → Stronger regularization, smaller weights
- **Lower** → Less regularization, may overfit

**Tuning Guide**:
```python
# No overfitting
CFG.WEIGHT_DECAY = 1e-5

# Mild overfitting
CFG.WEIGHT_DECAY = 1e-4

# Severe overfitting
CFG.WEIGHT_DECAY = 1e-3
```

**Weight Decay vs. Dropout**:
- **Weight decay**: Penalizes large weights (shrinks parameters)
- **Dropout**: Randomly drops neurons (increases robustness)
- **Use both**: Complementary regularization

---

## ⚖️ Loss Weight Hyperparameters

### BCE Weight (`LAMBDA_BCE`)

**Description**: Weight for binary classification loss

**Default**: 1.0

**Tuning**:
```python
# Poor pairing accuracy (AUC < 0.8)
CFG.LAMBDA_BCE = 2.0  # Emphasize classification

# Good pairing, poor regression (AUC > 0.9, MAE > 0.05)
CFG.LAMBDA_BCE = 0.5  # De-emphasize classification
```

### Sum-Rate Weight (`LAMBDA_RSUM`)

**Description**: Weight for sum-rate regression loss

**Default**: 0.5

**Tuning**:
```python
# Poor Rsum prediction (MAE > 0.1)
CFG.LAMBDA_RSUM = 1.0

# Rsum error dominates (BCE is fine, MAE is bad)
CFG.LAMBDA_RSUM = 2.0
```

### Alpha Weight (`LAMBDA_ALPHA`)

**Description**: Weight for power split regression loss

**Default**: 0.5

**Tuning**:
```python
# Poor alpha prediction (MAE > 0.02)
CFG.LAMBDA_ALPHA = 1.0

# Alpha error dominates
CFG.LAMBDA_ALPHA = 2.0
```

**Joint Tuning**:
```python
# Grid search over loss weights
for lambda_bce in [0.5, 1.0, 2.0]:
    for lambda_rsum in [0.25, 0.5, 1.0]:
        for lambda_alpha in [0.25, 0.5, 1.0]:
            CFG.LAMBDA_BCE = lambda_bce
            CFG.LAMBDA_RSUM = lambda_rsum
            CFG.LAMBDA_ALPHA = lambda_alpha
            
            auc, mae_r, mae_a = train_and_evaluate()
            results[(lambda_bce, lambda_rsum, lambda_alpha)] = {
                "auc": auc, "mae_rsum": mae_r, "mae_alpha": mae_a
            }

# Select best by composite score
scores = {k: v["auc"] - 0.5*(v["mae_rsum"] + v["mae_alpha"]) 
          for k, v in results.items()}
best_config = max(scores, key=scores.get)
print(f"Best config: {best_config}")
```

---

## 📊 Data Processing Hyperparameters

### Message Passing Topology (`MP_TOPOLOGY`)

**Description**: How to connect nodes for GNN message passing

**Options**: `"bipartite_knn"`, `"bipartite_full"`, `"full"`

**Default**: `"bipartite_knn"`

**Comparison**:
```python
# Bipartite KNN (recommended)
CFG.MP_TOPOLOGY = "bipartite_knn"
CFG.MP_K = 8
# Pros: Scalable, focused, efficient
# Cons: May miss long-range dependencies
# Edges: O(NK) where N=num_nodes, K=neighbors

# Bipartite Full
CFG.MP_TOPOLOGY = "bipartite_full"
# Pros: Complete weak-strong connections
# Cons: Dense graph, slow for large N
# Edges: O(N^2/4)

# Full graph
CFG.MP_TOPOLOGY = "full"
# Pros: Captures all relationships
# Cons: Very dense, computationally expensive
# Edges: O(N^2)
```

**Tuning Guide**:
```python
# Small graphs (N < 200)
CFG.MP_TOPOLOGY = "bipartite_full"

# Medium graphs (N = 200-500)
CFG.MP_TOPOLOGY = "bipartite_knn"
CFG.MP_K = 8

# Large graphs (N > 500)
CFG.MP_TOPOLOGY = "bipartite_knn"
CFG.MP_K = 5
```

---

### KNN Neighbors (`MP_K`)

**Description**: Number of neighbors in KNN message passing

**Default**: 8

**Impact**:
- **Larger K** → More message passing, better coverage, slower
- **Smaller K** → Faster, but may miss important connections

**Tuning Guide**:
```python
# Sparse scenarios (users far apart)
CFG.MP_K = 12

# Dense scenarios (users clustered)
CFG.MP_K = 5

# Balanced
CFG.MP_K = 8
```

**Experiments**:
```python
for k in [3, 5, 8, 10, 15, 20]:
    CFG.MP_K = k
    auc, runtime = train_and_evaluate_with_timing()
    print(f"K={k} → AUC={auc:.4f}, Time={runtime:.1f}s")

# Expected: Diminishing returns after K=8-10
```

---

### Negative Sampling Ratio

**Description**: Number of negative samples per positive edge

**Default**: 1.0 (equal positives and negatives)

**Impact**:
- **Ratio > 1** → More negatives, harder training
- **Ratio < 1** → Fewer negatives, easier training

**Tuning Guide**:
```python
# Model overfitting on positives
ratio = 2.0  # 2 negatives per positive

# Training too hard
ratio = 0.5  # 1 negative per 2 positives

# Balanced (default)
ratio = 1.0
```

**Implementation**:
```python
neg_edge_index = generate_negatives(
    data, 
    cfg.SIC_THRESHOLD_DB,
    cfg.USE_ANGLE_GUARD,
    cfg.MIN_ANGLE_DEG,
    ratio=1.0  # Tune this parameter
)
```

---

### SIC Threshold (`SIC_THRESHOLD_DB`)

**Description**: Minimum channel gain difference for SIC feasibility (dB)

**Default**: 8.0 dB

**Impact**:
- **Higher** → Stricter constraint, fewer pairs, higher quality
- **Lower** → More pairs, may include infeasible pairs

**Tuning Guide**:
```python
# Conservative (high reliability)
CFG.SIC_THRESHOLD_DB = 10.0

# Balanced
CFG.SIC_THRESHOLD_DB = 8.0

# Aggressive (more pairs, risk SIC failure)
CFG.SIC_THRESHOLD_DB = 6.0
```

**Impact on Pairing**:
```
Threshold | Avg Pairs/Graph | SIC Success Rate
----------|-----------------|------------------
6 dB      | 280            | 85%
8 dB      | 240            | 95%
10 dB     | 180            | 99%
```

---

### Angular Guard (`MIN_ANGLE_DEG`)

**Description**: Minimum angular separation between paired users (degrees)

**Default**: 25.0°

**Impact**:
- **Higher** → Less spatial interference, fewer pairs
- **Lower** → More pairs, higher interference risk

**Tuning Guide**:
```python
# Dense urban (high interference)
CFG.MIN_ANGLE_DEG = 30.0

# Suburban (moderate interference)
CFG.MIN_ANGLE_DEG = 25.0

# Rural (low interference)
CFG.MIN_ANGLE_DEG = 20.0

# Disable angular constraint
CFG.USE_ANGLE_GUARD = False
```

---

## 🔍 Hyperparameter Search Strategies

### 1. Grid Search

```python
import itertools

# Define hyperparameter grid
param_grid = {
    "hidden_dim": [64, 128, 256],
    "num_layers": [2, 3, 4],
    "lr": [1e-4, 5e-4, 1e-3],
    "dropout": [0.1, 0.2, 0.3]
}

# Generate all combinations
configs = list(itertools.product(*param_grid.values()))

results = []
for config in configs:
    hidden, layers, lr, dropout = config
    
    # Set hyperparameters
    CFG.HIDDEN_DIM = hidden
    CFG.NUM_LAYERS = layers
    CFG.LR = lr
    CFG.DROPOUT = dropout
    
    # Train and evaluate
    auc, mae_r, mae_a = train_and_evaluate()
    
    results.append({
        "config": config,
        "auc": auc,
        "mae_rsum": mae_r,
        "mae_alpha": mae_a
    })

# Find best configuration
best = max(results, key=lambda x: x["auc"])
print(f"Best config: {best}")
```

**Pros**: Exhaustive, guaranteed to find best in grid  
**Cons**: Exponential growth (3×3×3×3 = 81 combinations)

---

### 2. Random Search

```python
import random

def sample_config():
    return {
        "hidden_dim": random.choice([64, 128, 256]),
        "num_layers": random.choice([2, 3, 4]),
        "lr": random.uniform(1e-4, 1e-3),
        "dropout": random.uniform(0.1, 0.4)
    }

# Sample N random configurations
num_trials = 20
results = []

for _ in range(num_trials):
    config = sample_config()
    
    # Set hyperparameters
    for key, val in config.items():
        setattr(CFG, key.upper(), val)
    
    # Train and evaluate
    auc, mae_r, mae_a = train_and_evaluate()
    
    results.append({
        "config": config,
        "auc": auc,
        "mae_rsum": mae_r,
        "mae_alpha": mae_a
    })

# Find best
best = max(results, key=lambda x: x["auc"])
print(f"Best config: {best}")
```

**Pros**: More efficient than grid search, explores continuous ranges  
**Cons**: May miss optimal configuration

---

### 3. Bayesian Optimization

```python
from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical

# Define search space
space = [
    Integer(64, 256, name="hidden_dim"),
    Integer(2, 4, name="num_layers"),
    Real(1e-4, 1e-3, prior="log-uniform", name="lr"),
    Real(0.1, 0.4, name="dropout")
]

# Objective function
def objective(params):
    hidden, layers, lr, dropout = params
    
    CFG.HIDDEN_DIM = hidden
    CFG.NUM_LAYERS = layers
    CFG.LR = lr
    CFG.DROPOUT = dropout
    
    auc, _, _ = train_and_evaluate()
    
    return -auc  # Minimize negative AUC (maximize AUC)

# Run Bayesian optimization
result = gp_minimize(
    objective, space, 
    n_calls=30,  # Number of evaluations
    random_state=42
)

print(f"Best AUC: {-result.fun:.4f}")
print(f"Best params: {result.x}")
```

**Pros**: Most sample-efficient, learns from previous trials  
**Cons**: Requires external library (`scikit-optimize`)

---

## 📈 Recommended Tuning Workflow

### Phase 1: Coarse Search (Find Good Region)

```python
# Try 3 values for each major hyperparameter
hidden_dims = [64, 128, 256]
num_layers = [2, 3, 4]
lrs = [1e-4, 5e-4, 1e-3]

# Fix other params at defaults
CFG.DROPOUT = 0.2
CFG.BATCH_SIZE = 2
CFG.EPOCHS = 30  # Shorter for speed

# Evaluate all combinations (27 configs)
for h, l, lr in itertools.product(hidden_dims, num_layers, lrs):
    CFG.HIDDEN_DIM = h
    CFG.NUM_LAYERS = l
    CFG.LR = lr
    
    auc = train_and_evaluate_fast()
    print(f"H={h}, L={l}, LR={lr} → AUC={auc:.4f}")
```

### Phase 2: Fine-Tuning (Refine Best Config)

```python
# Select best from Phase 1 (e.g., H=128, L=3, LR=5e-4)
CFG.HIDDEN_DIM = 128
CFG.NUM_LAYERS = 3
CFG.LR = 5e-4

# Now tune regularization
for dropout in [0.1, 0.15, 0.2, 0.25, 0.3]:
    for weight_decay in [1e-5, 1e-4, 1e-3]:
        CFG.DROPOUT = dropout
        CFG.WEIGHT_DECAY = weight_decay
        
        auc = train_full()  # Full epochs
        print(f"D={dropout}, WD={weight_decay} → AUC={auc:.4f}")
```

### Phase 3: Loss Weight Tuning

```python
# Fix model architecture and training params from Phase 2
# Tune multi-task loss weights
for lambda_bce in [0.5, 1.0, 1.5]:
    for lambda_rsum in [0.25, 0.5, 1.0]:
        CFG.LAMBDA_BCE = lambda_bce
        CFG.LAMBDA_RSUM = lambda_rsum
        CFG.LAMBDA_ALPHA = lambda_rsum  # Keep alpha same as rsum
        
        auc, mae_r, mae_a = train_full()
        print(f"BCE={lambda_bce}, R={lambda_rsum} → "
              f"AUC={auc:.4f}, MAE_R={mae_r:.4f}, MAE_A={mae_a:.4f}")
```

---

## ✅ Best Practices

### 1. Start Simple
- Begin with default config
- Only tune if performance is unsatisfactory

### 2. Tune One Category at a Time
- Model architecture → Training params → Loss weights → Data params

### 3. Use Validation Set
- Never tune on test set!
- Hold out 15% for validation

### 4. Log Everything
```python
import wandb

wandb.init(project="noma-gnn-tuning")
wandb.config.update(CFG.__dict__)

for epoch in range(num_epochs):
    train_loss = train_one_epoch(...)
    val_auc, val_mae_r, val_mae_a = evaluate(...)
    
    wandb.log({
        "epoch": epoch,
        "train_loss": train_loss,
        "val_auc": val_auc,
        "val_mae_rsum": val_mae_r,
        "val_mae_alpha": val_mae_a
    })
```

### 5. Be Patient
- Good hyperparameter search takes time
- But pays off in final performance

---

**Last Updated**: October 17, 2025  
**Version**: 1.0.0  
**Author**: NOMA-GNN Development Team
