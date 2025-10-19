# Training Loop Documentation

## 📋 File: `training/train.py`

### 🎯 Purpose
Implements the complete training pipeline for the NOMA-GNN model, including:
- Data loading and splitting
- Message-passing graph construction
- Hard negative sampling
- Multi-task loss optimization
- Validation and checkpointing
- Final test evaluation

---

## 🏗️ Training Architecture

### Pipeline Overview
```
Raw CSVs → Build Graphs → Train/Val/Test Split → Data Loaders
                                                       ↓
Model Initialization ← Config Parameters        Train Loop
         ↓                                            ↓
    Optimizer Setup                          Generate MP Graph
         ↓                                            ↓
   Training Epoch ←←←←←←←←←←←←←←←←          Sample Negatives
         ↓                                            ↓
    Validation                                 Forward Pass
         ↓                                            ↓
   Save Best Model                          Compute Loss
         ↓                                            ↓
   Test Evaluation                            Backprop
```

---

## 📊 Key Components

### 1. Message Passing Graph Construction

```python
def build_mp_edge_index(x, weak_idx, strong_idx, kind="bipartite_knn", k=8):
    """
    Build message passing graph for GNN encoding.
    
    Args:
        x: Node features [N, F]
        weak_idx: Indices of weak users (bottom 50% by h_dB)
        strong_idx: Indices of strong users (top 50% by h_dB)
        kind: Graph topology type
        k: Number of neighbors (for KNN variants)
    
    Returns:
        edge_index: Undirected edges [2, E_mp]
    """
```

#### Strategy: Bipartite KNN (Recommended)

**Algorithm**:
```
1. Sort strong users by channel gain (descending)
2. For each weak user:
     Connect to top-K strongest users
3. Sort weak users by channel gain (ascending)
4. For each strong user:
     Connect to bottom-K weakest users
5. Make all edges bidirectional
```

**Mathematical Formulation**:
$$\mathcal{E}_{\text{MP}} = \{(w,s) : w \in \mathcal{W}, s \in \text{top}_K(\mathcal{S})\} \cup \{(s,w) : s \in \mathcal{S}, w \in \text{bottom}_K(\mathcal{W})\}$$

where:
- $\mathcal{W}$ = weak users (h_dB < median)
- $\mathcal{S}$ = strong users (h_dB ≥ median)

**Implementation**:
```python
# Feature index of h_dB
h_idx = FEATURE_COLS.index("h_dB")
h = x[:, h_idx]

# Connect each weak to K strongest
strong_sorted = torch.argsort(h[strong_idx], descending=True)
strong_order = [strong_idx[i.item()] for i in strong_sorted]

ws, ss = [], []
k_eff = min(k, len(strong_order))
for w in weak_idx:
    for s in strong_order[:k_eff]:
        ws.append(w); ss.append(s)

# Connect each strong to K weakest
weak_sorted = torch.argsort(h[weak_idx], descending=False)
weak_order = [weak_idx[i.item()] for i in weak_sorted]
k_eff2 = min(k, len(weak_order))
for s in strong_idx:
    for w in weak_order[:k_eff2]:
        ws.append(w); ss.append(s)

# Bidirectional edges
edge = torch.tensor([ws+ss, ss+ws], dtype=torch.long)
return edge
```

**Complexity**:
- **Time**: $O(N \log N)$ for sorting + $O(NK)$ for edge construction
- **Space**: $O(NK)$ edges (vs $O(N^2)$ for full bipartite)

**Why Bipartite KNN?**
- ✅ **Focused**: Connects plausible pairing candidates
- ✅ **Scalable**: Linear in N (with fixed K)
- ✅ **Effective**: Captures strong-weak relationships
- ✅ **Efficient**: Reduces noise from unlikely pairs

**Alternative: Bipartite Full**
```python
if kind == "bipartite_full":
    ws, ss = [], []
    for w in weak_idx:
        for s in strong_idx:
            ws.append(w); ss.append(s)
    edge = torch.tensor([ws+ss, ss+ws], dtype=torch.long)
    return edge
```
- **Edges**: $O(N^2/4)$ (dense)
- **Use Case**: Small graphs (N < 100) or when K is very large

---

### 2. Hard Negative Sampling

```python
def generate_negatives(data, sic_db=8.0, use_angle=True, min_angle_deg=25.0, ratio=1.0):
    """
    Create SIC-feasible negative edges (not in ground truth).
    
    Critical for discriminative learning!
    
    Args:
        data: PyG Data object
        sic_db: SIC threshold
        use_angle: Apply angular guard
        min_angle_deg: Minimum angular separation
        ratio: Number of negatives = ratio * num_positives
    
    Returns:
        neg_edge_index: [2, E_neg]
    """
```

#### Why Hard Negatives?

**Naive Negatives** (Random non-edges):
```python
# BAD: Too easy to classify
neg_edges = random_sample(all_non_edges)
```
❌ **Problem**: Many violate SIC or angle constraints → model learns to check constraints, not quality

**Hard Negatives** (SIC-feasible but not selected):
```python
# GOOD: Satisfy constraints but not optimal
neg_edges = sample(SIC_feasible & angle_feasible & ~ground_truth)
```
✅ **Benefit**: Forces model to learn subtle differences beyond constraints

#### Algorithm

```
1. Extract positive pairs from ground truth
2. Split users into weak/strong (by median h_dB)
3. For each weak-strong pair:
     a. Check SIC: 10*log10(h_strong/h_weak) >= sic_db
     b. Check angle: |angle_weak - angle_strong| >= min_angle
     c. Skip if in positive set
     d. Add to candidate negatives
4. Randomly sample (ratio * num_positives) negatives
5. Return as edge_index
```

**Implementation**:
```python
pos = set([(int(a), int(b)) for a,b in data.edge_index_pos.t().tolist()])
n = data.num_nodes
h = data.h_linear.cpu().numpy()
ang = data.angles.cpu().numpy()
min_ang = np.deg2rad(min_angle_deg)

# Split by median
h_db = data.h_db.cpu().numpy()
idx_sorted = np.argsort(h_db)
weak = idx_sorted[:n//2]; strong = idx_sorted[n//2:]

candidates = []
for w in weak:
    for s in strong:
        h1 = min(h[w], h[s]); h2 = max(h[w], h[s])
        
        # SIC check
        if h1 <= 0 or h2 <= 0: continue
        if 10*np.log10(h2/h1) < sic_db: continue
        
        # Angle check
        if use_angle:
            d = np.abs(ang[w]-ang[s]) % (2*np.pi)
            d = min(d, 2*np.pi - d)
            if d < min_ang: continue
        
        # Not in positives
        a,b = (w,s) if h[w]<=h[s] else (s,w)
        if (a,b) in pos: continue
        
        candidates.append((a,b))

# Sample with 1:1 ratio
num_pos = data.edge_index_pos.size(1)
np.random.shuffle(candidates)
pick = candidates[:int(max(1, ratio*num_pos))]
ne = torch.tensor(pick, dtype=torch.long).t().contiguous()
return ne
```

**Key Points**:
- **Ratio**: Typically 1.0 (same number as positives)
- **Shuffling**: Random sampling from candidates
- **Empty Check**: Return empty tensor if no candidates

---

### 3. Training Loop

```python
def train_one_epoch(model, loader, optimizer, device, cfg):
    """
    Train for one epoch over all batches.
    
    Returns:
        Average training loss
    """
    model.train()
    losses = []
    
    for data in loader:
        data = data.to(device)
        
        # 1. Build MP graph
        h_db = data.h_db
        idx_sorted = torch.argsort(h_db)
        weak = idx_sorted[:data.num_nodes//2]
        strong = idx_sorted[data.num_nodes//2:]
        mp_edge_index = build_mp_edge_index(
            data.x, weak, strong, cfg.MP_TOPOLOGY, cfg.MP_K
        ).to(device)
        
        # 2. Generate negatives
        neg_edge_index = generate_negatives(
            data, cfg.SIC_THRESHOLD_DB, 
            cfg.USE_ANGLE_GUARD, cfg.MIN_ANGLE_DEG, 
            ratio=1.0
        ).to(device)
        
        if neg_edge_index.numel() == 0:
            continue  # Skip if no negatives
        
        # 3. Forward pass
        pos_logit, pos_rsum_pred, pos_alpha_pred = model(
            data.x, mp_edge_index, data.edge_index_pos.to(device)
        )
        neg_logit, _, _ = model(
            data.x, mp_edge_index, neg_edge_index
        )
        
        # 4. Compute loss
        loss, parts = multitask_loss(
            pos_logit, neg_logit, 
            pos_rsum_pred, pos_alpha_pred,
            data.y_pos_rsum.to(device), 
            data.y_pos_alpha.to(device),
            cfg.LAMBDA_BCE, cfg.LAMBDA_RSUM, cfg.LAMBDA_ALPHA
        )
        
        # 5. Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        losses.append(loss.item())
    
    return float(np.mean(losses)) if losses else 0.0
```

**Step-by-Step Execution**:
```
Batch 1 (2 graphs):
  Graph A: 500 users, 237 pos pairs
  Graph B: 500 users, 245 pos pairs
  
Step 1: Build MP graphs
  → A: [2, 4000] edges (bipartite KNN)
  → B: [2, 4000] edges
  
Step 2: Generate negatives
  → A: Sample 237 hard negatives
  → B: Sample 245 hard negatives
  
Step 3: Forward pass
  → Encode: Learn node embeddings
  → Decode: Score pos + neg edges
  
Step 4: Loss
  → BCE: Classification (pos vs neg)
  → MAE: Regression (Rsum, alpha)
  → Total: Weighted combination
  
Step 5: Optimize
  → Compute gradients
  → Update model weights
  → Zero gradients for next batch
```

---

### 4. Evaluation

```python
@torch.no_grad()
def evaluate(model, loader, device, cfg):
    """
    Evaluate model on validation/test set.
    
    Returns:
        auc: Edge classification AUC-ROC
        mae_rsum: Mean absolute error for sum-rate
        mae_alpha: Mean absolute error for power split
    """
    model.eval()
    all_scores, all_labels = [], []
    mae_rsum, mae_alpha, n_batches = 0.0, 0.0, 0
    
    for data in loader:
        data = data.to(device)
        
        # Build MP graph (same as training)
        h_db = data.h_db
        idx_sorted = torch.argsort(h_db)
        weak = idx_sorted[:data.num_nodes//2]
        strong = idx_sorted[data.num_nodes//2:]
        mp_edge_index = build_mp_edge_index(
            data.x, weak, strong, cfg.MP_TOPOLOGY, cfg.MP_K
        ).to(device)
        
        # Sample negatives
        neg_edge_index = generate_negatives(
            data, cfg.SIC_THRESHOLD_DB, 
            cfg.USE_ANGLE_GUARD, cfg.MIN_ANGLE_DEG, 
            ratio=1.0
        ).to(device)
        
        if neg_edge_index.numel() == 0:
            continue
        
        # Forward pass
        pos_logit, pos_rsum_pred, pos_alpha_pred = model(
            data.x, mp_edge_index, data.edge_index_pos.to(device)
        )
        neg_logit, _, _ = model(
            data.x, mp_edge_index, neg_edge_index
        )
        
        # Classification metrics (AUC)
        pos_scores = pos_logit.sigmoid().cpu().numpy()
        neg_scores = neg_logit.sigmoid().cpu().numpy()
        scores = np.concatenate([pos_scores, neg_scores])
        labels = np.concatenate([
            np.ones_like(pos_scores), 
            np.zeros_like(neg_scores)
        ])
        all_scores.append(scores)
        all_labels.append(labels)
        
        # Regression metrics (MAE)
        mae_rsum += torch.mean(torch.abs(
            pos_rsum_pred - data.y_pos_rsum.to(device)
        )).item()
        mae_alpha += torch.mean(torch.abs(
            pos_alpha_pred - data.y_pos_alpha.to(device)
        )).item()
        n_batches += 1
    
    if len(all_scores) == 0:
        return float('nan'), float('nan'), float('nan')
    
    # Compute AUC-ROC
    scores = np.concatenate(all_scores)
    labels = np.concatenate(all_labels)
    auc = roc_auc_score(labels, scores)
    
    # Average MAEs
    mae_r = mae_rsum / max(1, n_batches)
    mae_a = mae_alpha / max(1, n_batches)
    
    return auc, mae_r, mae_a
```

**Metrics Explained**:

**1. AUC-ROC (Area Under ROC Curve)**:
$$\text{AUC} = P(\text{score}(\text{positive}) > \text{score}(\text{negative}))$$

- **Range**: [0, 1] (0.5 = random, 1.0 = perfect)
- **Interpretation**: Probability model ranks positive higher than negative
- **Robust**: Threshold-independent metric

**2. MAE (Mean Absolute Error)**:
$$\text{MAE} = \frac{1}{N}\sum_{i=1}^N |y_i - \hat{y}_i|$$

- **Sum-Rate MAE**: Error in throughput prediction (bits/Hz)
- **Alpha MAE**: Error in power split (unitless, range [0,1])
- **Robust to outliers**: Better than MSE for this problem

**Why These Metrics?**
- **AUC**: Measures ranking quality (key for matching)
- **MAE**: Interpretable (same units as targets)
- **Complementary**: Classification + regression performance

---

### 5. Main Training Function

```python
def main():
    """
    Complete training pipeline.
    """
    # Parse arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("--users_csv", type=str, required=True)
    ap.add_argument("--pairs_csv", type=str, required=True)
    ap.add_argument("--out_dir", type=str, default="./checkpoints")
    ap.add_argument("--scaler_path", type=str, default="./checkpoints/feature_scaler.json")
    ap.add_argument("--epochs", type=int, default=CFG.EPOCHS)
    ap.add_argument("--batch_size", type=int, default=CFG.BATCH_SIZE)
    ap.add_argument("--device", type=str, default=CFG.DEVICE)
    ap.add_argument("--resume_ckpt", type=str, default="", help="Warm-start from checkpoint")
    args = ap.parse_args()
    
    # Setup
    os.makedirs(args.out_dir, exist_ok=True)
    set_seed(CFG.SEED)
    
    # Build graphs
    graphs = build_graphs_from_merged(
        args.users_csv, args.pairs_csv,
        sic_db=CFG.SIC_THRESHOLD_DB,
        use_angle_guard=CFG.USE_ANGLE_GUARD,
        min_angle_deg=CFG.MIN_ANGLE_DEG,
        scaler_outpath=args.scaler_path
    )
    
    # Split data (70/15/15)
    n = len(graphs)
    n_train = int(0.7*n)
    n_val = int(0.15*n)
    n_test = n - n_train - n_val
    
    train_set = graphs[:n_train]
    val_set = graphs[n_train:n_train+n_val]
    test_set = graphs[n_train+n_val:]
    
    print(f"Dataset: {n_train} train, {n_val} val, {n_test} test")
    
    # Data loaders
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=1, shuffle=False)
    test_loader = DataLoader(test_set, batch_size=1, shuffle=False)
    
    # Device
    device = torch.device(
        args.device if torch.cuda.is_available() and args.device=="cuda" else "cpu"
    )
    print(f"Using device: {device}")
    
    # Model
    model = PairPowerGNN(
        in_channels=len(FEATURE_COLS),
        hidden=CFG.HIDDEN_DIM,
        out_channels=CFG.OUT_DIM,
        num_layers=CFG.NUM_LAYERS,
        dropout=CFG.DROPOUT
    ).to(device)
    
    # Optimizer
    opt = torch.optim.AdamW(
        model.parameters(), 
        lr=CFG.LR, 
        weight_decay=CFG.WEIGHT_DECAY
    )
    
    # Checkpointing
    start_epoch = 1
    best_auc = -1.0
    ckpt_path = os.path.join(args.out_dir, "best_model.pt")
    
    # Resume from checkpoint
    if args.resume_ckpt:
        print(f"[RESUME] Loading weights from {args.resume_ckpt}")
        ckpt = torch.load(args.resume_ckpt, map_location=device)
        model.load_state_dict(ckpt["model_state"])
        if "best_auc" in ckpt:
            best_auc = ckpt["best_auc"]
    
    # Training loop
    for epoch in range(1, args.epochs+1):
        tl = train_one_epoch(model, train_loader, opt, device, CFG)
        auc, mae_r, mae_a = evaluate(model, val_loader, device, CFG)
        
        print(f"Epoch {epoch:03d} | TrainLoss {tl:.4f} | "
              f"ValAUC {auc:.4f} | Val MAE(Rsum) {mae_r:.4f} | "
              f"Val MAE(alpha) {mae_a:.4f}")
        
        # Save best model
        if auc == auc and auc > best_auc:  # auc == auc checks for NaN
            best_auc = auc
            torch.save({
                "model_state": model.state_dict(),
                "cfg": CFG.__dict__,
                "best_auc": best_auc
            }, ckpt_path)
            print(f"✅ Saved best to {ckpt_path}")
    
    # Final test evaluation
    print("\n" + "="*60)
    print("FINAL TEST EVALUATION")
    print("="*60)
    ckpt = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    auc, mae_r, mae_a = evaluate(model, test_loader, device, CFG)
    print(f"[TEST] AUC={auc:.4f}  MAE(Rsum)={mae_r:.4f}  MAE(alpha)={mae_a:.4f}")
    print(f"Best checkpoint: {ckpt_path}")
```

**Data Split Rationale**:
- **Train (70%)**: Main learning set
- **Val (15%)**: Hyperparameter tuning, early stopping
- **Test (15%)**: Final unbiased evaluation

**Checkpoint Format**:
```python
{
    "model_state": OrderedDict(...),  # Model weights
    "cfg": {...},                     # Configuration used
    "best_auc": 0.925                 # Best validation AUC
}
```

---

## 🎯 Usage Examples

### Example 1: Basic Training

```bash
python -m training.train \
    --users_csv data/raw/merged_h_values.csv \
    --pairs_csv data/raw/merged_pairs.csv \
    --out_dir checkpoints \
    --epochs 60 \
    --batch_size 2 \
    --device cuda
```

**Output**:
```
Dataset: 70 train, 15 val, 15 test
Using device: cuda
Epoch 001 | TrainLoss 1.2345 | ValAUC 0.7561 | Val MAE(Rsum) 0.1234 | Val MAE(alpha) 0.0321
Epoch 002 | TrainLoss 0.9876 | ValAUC 0.8123 | Val MAE(Rsum) 0.0987 | Val MAE(alpha) 0.0254
...
Epoch 045 | TrainLoss 0.2341 | ValAUC 0.9254 | Val MAE(Rsum) 0.0312 | Val MAE(alpha) 0.0089
✅ Saved best to checkpoints/best_model.pt
...
============================================================
FINAL TEST EVALUATION
============================================================
[TEST] AUC=0.9187  MAE(Rsum)=0.0345  MAE(alpha)=0.0098
Best checkpoint: checkpoints/best_model.pt
```

### Example 2: Resume from Checkpoint

```bash
python -m training.train \
    --users_csv data/raw/merged_h_values.csv \
    --pairs_csv data/raw/merged_pairs.csv \
    --out_dir checkpoints \
    --resume_ckpt checkpoints/best_model.pt \
    --epochs 100 \
    --device cuda
```

### Example 3: CPU Training (No GPU)

```bash
python -m training.train \
    --users_csv data/raw/merged_h_values.csv \
    --pairs_csv data/raw/merged_pairs.csv \
    --out_dir checkpoints \
    --epochs 20 \
    --batch_size 1 \
    --device cpu
```

### Example 4: Custom Configuration

```python
# Modify config before importing train module
from config import CFG

# Smaller model for faster training
CFG.HIDDEN_DIM = 64
CFG.NUM_LAYERS = 2
CFG.DROPOUT = 0.1

# Less strict constraints for more pairs
CFG.SIC_THRESHOLD_DB = 6.0
CFG.MIN_ANGLE_DEG = 15.0

# Then run training
from training.train import main
main()
```

---

## 📊 Training Dynamics

### Typical Learning Curve

```
Epoch  | Train Loss | Val AUC | Val MAE(R) | Val MAE(α)
-------|------------|---------|------------|------------
1      | 1.234      | 0.756   | 0.123      | 0.032
5      | 0.876      | 0.834   | 0.089      | 0.024
10     | 0.567      | 0.881   | 0.067      | 0.018
20     | 0.345      | 0.912   | 0.045      | 0.012
40     | 0.234      | 0.925   | 0.032      | 0.009
60     | 0.223      | 0.926   | 0.031      | 0.009
```

**Observations**:
1. **Loss**: Decreases rapidly early, plateaus later
2. **AUC**: Reaches 0.9+ after 20-30 epochs
3. **MAE**: Continues improving slowly beyond AUC plateau
4. **Overfitting Check**: Train loss < 0.2, Val AUC > 0.92 is healthy

### Expected Performance

| Metric | Poor | Fair | Good | Excellent |
|--------|------|------|------|-----------|
| Val AUC | < 0.7 | 0.7-0.8 | 0.8-0.9 | > 0.9 |
| MAE(Rsum) | > 0.2 | 0.1-0.2 | 0.05-0.1 | < 0.05 |
| MAE(α) | > 0.05 | 0.02-0.05 | 0.01-0.02 | < 0.01 |

---

## 🐛 Troubleshooting

### Issue 1: Low Validation AUC (< 0.7)

**Potential Causes**:
1. **Insufficient model capacity**
   ```python
   CFG.HIDDEN_DIM = 256  # Increase from 128
   CFG.NUM_LAYERS = 4    # Increase from 3
   ```

2. **Poor negative sampling**
   - Check if negatives are too easy (many violate constraints)
   - Verify hard negatives are SIC-feasible

3. **Inadequate training data**
   - Need diverse scenarios (different SNR, user densities)
   - Minimum 50+ training graphs recommended

### Issue 2: Overfitting (Train AUC >> Val AUC)

**Solutions**:
```python
# Increase regularization
CFG.DROPOUT = 0.4          # From 0.2
CFG.WEIGHT_DECAY = 1e-3    # From 1e-4

# Reduce model size
CFG.HIDDEN_DIM = 64
CFG.NUM_LAYERS = 2

# More training data
# Add data augmentation (feature noise, graph perturbation)
```

### Issue 3: Training Unstable (NaN Loss)

**Solutions**:
```python
# 1. Gradient clipping
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

# 2. Lower learning rate
CFG.LR = 1e-4  # From 1e-3

# 3. Check for extreme values
assert torch.isfinite(loss), "Loss is NaN/Inf!"
```

### Issue 4: Slow Training

**Optimizations**:
```python
# 1. Reduce MP graph size
CFG.MP_K = 5  # From 8

# 2. Larger batch size (if memory allows)
--batch_size 4  # From 2

# 3. Mixed precision training
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()

with autocast():
    loss = train_one_epoch(...)
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()

# 4. Reduce num_workers (if CPU bottleneck)
train_loader = DataLoader(..., num_workers=0)
```

---

## 📚 Advanced Topics

### Early Stopping

```python
# Add to training loop
patience = 10
best_auc = -1.0
epochs_no_improve = 0

for epoch in range(1, max_epochs+1):
    # ... training ...
    auc, _, _ = evaluate(model, val_loader, device, CFG)
    
    if auc > best_auc:
        best_auc = auc
        epochs_no_improve = 0
        # Save checkpoint
    else:
        epochs_no_improve += 1
    
    if epochs_no_improve >= patience:
        print(f"Early stopping at epoch {epoch}")
        break
```

### Learning Rate Scheduling

```python
from torch.optim.lr_scheduler import ReduceLROnPlateau

scheduler = ReduceLROnPlateau(
    opt, mode='max', factor=0.5, patience=5, verbose=True
)

for epoch in range(1, max_epochs+1):
    # ... training ...
    auc, _, _ = evaluate(model, val_loader, device, CFG)
    scheduler.step(auc)  # Reduce LR if AUC plateaus
```

### Data Augmentation

```python
def augment_graph(data, noise_std=0.01):
    """Add Gaussian noise to node features."""
    noise = torch.randn_like(data.x) * noise_std
    data.x = data.x + noise
    return data

# In training loop
for data in loader:
    data = augment_graph(data)
    # ... forward pass ...
```

---

## ✅ Best Practices

### Training
1. **Always use validation set** for model selection
2. **Monitor multiple metrics** (not just loss)
3. **Save best model**, not last model
4. **Log training curves** for debugging
5. **Set random seeds** for reproducibility

### Data
1. **Shuffle training data** each epoch
2. **Don't shuffle validation/test** (consistency)
3. **Check for data leakage** (train/val/test split)
4. **Verify input ranges** (features normalized)

### Debugging
1. **Start with small model** (fast iteration)
2. **Overfit on single batch** first (sanity check)
3. **Visualize predictions** (qualitative assessment)
4. **Profile bottlenecks** (find slowest parts)

---

**Last Updated**: October 17, 2025  
**Version**: 1.0.0  
**Author**: NOMA-GNN Development Team
