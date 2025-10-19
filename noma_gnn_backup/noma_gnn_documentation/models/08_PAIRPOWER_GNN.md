# PairPowerGNN Model Documentation

## 📋 File: `models/pairpower_gnn.py`

### 🎯 Purpose
Implements the core Graph Neural Network architecture for NOMA user pairing and power allocation. This model uses GraphSAGE for node encoding and multiple MLP heads for multi-task edge prediction.

---

## 🏗️ Architecture Overview

### High-Level Structure
```
Input Node Features (x) → GraphSAGE Encoder → Node Embeddings (z) → Edge Decoders → Predictions
                              ↑
                    Message Passing Graph
```

### Components
1. **Node Encoder**: Multi-layer GraphSAGE for learning user representations
2. **Edge Decoders**: Three parallel MLPs for multi-task prediction:
   - **Logit Head**: Binary classification (pair or not)
   - **Sum-Rate Head**: Regression (expected throughput)
   - **Alpha Head**: Regression (power split ratio)

---

## 📊 Mathematical Formulation

### 1. Node Encoding (GraphSAGE)

For each layer $l$, node $i$ updates its representation:

$$\mathbf{h}_i^{(l+1)} = \sigma\left(\mathbf{W}^{(l)} \cdot \text{CONCAT}\left(\mathbf{h}_i^{(l)}, \text{MEAN}\left(\{\mathbf{h}_j^{(l)}, j \in \mathcal{N}(i)\}\right)\right)\right)$$

**Components**:
- $\mathbf{h}_i^{(l)}$: Node $i$ embedding at layer $l$
- $\mathcal{N}(i)$: Neighbors in message-passing graph
- $\text{MEAN}$: Average aggregation (GraphSAGE default)
- $\mathbf{W}^{(l)}$: Learnable weight matrix
- $\sigma$: ReLU activation

**Why GraphSAGE?**
- ✅ Inductive learning (handles new graphs)
- ✅ Scalable to large graphs
- ✅ Efficient sampling-based training
- ✅ Better than GCN for heterogeneous graphs

### 2. Edge Representation

For edge $(i,j)$, concatenate node embeddings:

$$\mathbf{e}_{ij} = \text{CONCAT}(\mathbf{z}_i, \mathbf{z}_j) \in \mathbb{R}^{2D}$$

where $\mathbf{z}_i, \mathbf{z}_j$ are final node embeddings from encoder.

### 3. Multi-Task Prediction

**a) Pairing Existence (Classification)**
$$\text{logit}_{ij} = \text{MLP}_{\text{exist}}(\mathbf{e}_{ij}) \in \mathbb{R}$$
$$p_{ij} = \sigma(\text{logit}_{ij}) \in (0,1)$$

**b) Sum-Rate Prediction (Regression)**
$$\hat{R}_{\text{sum}}^{ij} = \text{ReLU}(\text{MLP}_{\text{rsum}}(\mathbf{e}_{ij})) \in \mathbb{R}_+$$

**c) Power Split Prediction (Bounded Regression)**
$$\hat{\alpha}_{ij} = \sigma(\text{MLP}_{\alpha}(\mathbf{e}_{ij})) \in (0,1)$$

---

## 🔍 Detailed Code Walkthrough

### Class Definition

```python
class PairPowerGNN(nn.Module):
    """
    GraphSAGE encoder + multi-head edge decoders
    
    Multi-task objectives:
    1. edge_logit: Binary pairing existence (BCE loss)
    2. edge_rsum: Sum-rate regression (MAE loss)
    3. edge_alpha: Power split regression (MAE loss)
    """
```

### Constructor (`__init__`)

```python
def __init__(self, in_channels, hidden=128, out_channels=128, num_layers=3, dropout=0.2):
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `in_channels` | int | - | Number of input features (5 for NOMA) |
| `hidden` | int | 128 | Hidden layer dimension |
| `out_channels` | int | 128 | Final node embedding dimension |
| `num_layers` | int | 3 | Number of GraphSAGE layers |
| `dropout` | float | 0.2 | Dropout probability |

**Implementation Details**:

#### 1. GraphSAGE Layers
```python
self.convs = nn.ModuleList()
self.convs.append(SAGEConv(in_channels, hidden))       # Input layer
for _ in range(num_layers-2):
    self.convs.append(SAGEConv(hidden, hidden))        # Hidden layers
self.convs.append(SAGEConv(hidden, out_channels))     # Output layer
```

**Layer Configuration**:
- **Layer 0**: [5] → [128] (expand from features to hidden)
- **Layers 1..L-2**: [128] → [128] (maintain dimension)
- **Layer L-1**: [128] → [128] (final embedding)

**Why This Structure?**
- First layer: Learns feature transformations
- Middle layers: Propagate and aggregate information
- Last layer: Produces discriminative embeddings

#### 2. Edge Decoder MLPs

**Shared Architecture Pattern**:
```python
edge_in = 2 * out_channels  # Concatenated embeddings
```

Each MLP has structure:
```
[2D] → Linear → [D] → ReLU → Dropout → Linear → [1] → Activation
```

**a) Logit MLP (No final activation)**
```python
self.edge_mlp_logit = nn.Sequential(
    nn.Linear(edge_in, out_channels),      # [256] → [128]
    nn.ReLU(inplace=True),                 # Activation
    nn.Dropout(dropout),                   # Regularization
    nn.Linear(out_channels, 1)             # [128] → [1]
)
```
**Output**: Raw logit (passed to BCEWithLogitsLoss)

**b) Sum-Rate MLP**
```python
self.edge_mlp_rsum = nn.Sequential(
    nn.Linear(edge_in, out_channels),
    nn.ReLU(inplace=True),
    nn.Dropout(dropout),
    nn.Linear(out_channels, 1)
)
```
**Output**: Positive real (sum-rate in bits/Hz)

**c) Alpha MLP (Sigmoid activation)**
```python
self.edge_mlp_alpha = nn.Sequential(
    nn.Linear(edge_in, out_channels),
    nn.ReLU(inplace=True),
    nn.Dropout(dropout),
    nn.Linear(out_channels, 1),
    nn.Sigmoid()                           # Maps to (0,1)
)
```
**Output**: Power split ratio $\alpha \in (0,1)$

**Why Sigmoid for Alpha?**
- Ensures valid power allocation: $0 < \alpha < 1$
- Weak user power: $P_1 = \alpha \cdot P_{\text{total}}$
- Strong user power: $P_2 = (1-\alpha) \cdot P_{\text{total}}$

---

## 🚀 Forward Pass Methods

### 1. Node Encoding

```python
def encode(self, x, edge_index):
    """
    Propagate messages through GraphSAGE layers.
    
    Args:
        x: Node features [N, F]
        edge_index: Message-passing edges [2, E_mp]
    
    Returns:
        z: Node embeddings [N, D]
    """
    z = x
    for i, conv in enumerate(self.convs):
        z = conv(z, edge_index)
        if i != len(self.convs)-1:        # Skip activation on last layer
            z = F.relu(z, inplace=True)
            z = self.dropout(z)
    return z
```

**Step-by-Step Execution**:
```
x: [500, 5]   (500 users, 5 features)
   ↓ SAGEConv (layer 0)
h1: [500, 128] → ReLU → Dropout
   ↓ SAGEConv (layer 1)
h2: [500, 128] → ReLU → Dropout
   ↓ SAGEConv (layer 2)
z: [500, 128]  (final embeddings, no activation)
```

**Why No Activation on Last Layer?**
- Final embeddings should span full real space
- Allows both positive and negative feature combinations
- Decoders will apply their own activations

### 2. Edge Feature Construction

```python
def _edge_cat(self, z, edge_index):
    """
    Concatenate node embeddings for each edge.
    
    Args:
        z: Node embeddings [N, D]
        edge_index: Edges to evaluate [2, E]
    
    Returns:
        Edge features [E, 2D]
    """
    src, dst = edge_index         # Source and destination nodes
    return torch.cat([z[src], z[dst]], dim=-1)
```

**Example**:
```python
z = torch.randn(100, 128)          # 100 nodes, 128-dim embeddings
edge_index = torch.tensor([[0, 1], [50, 99]])  # 2 edges
edge_features = _edge_cat(z, edge_index)
# Result: [2, 256] (2 edges, concatenated 128+128)
```

**Ordering Matters**:
- `src`: Weak user (lower channel gain)
- `dst`: Strong user (higher channel gain)
- Consistent ordering ensures model learns directional patterns

### 3. Multi-Task Decoding

```python
def decode_all(self, z, edge_index):
    """
    Predict all three objectives for given edges.
    
    Args:
        z: Node embeddings [N, D]
        edge_index: Edges to score [2, E]
    
    Returns:
        logit: Pairing scores [E]
        rsum: Sum-rates [E]
        alpha: Power splits [E]
    """
    h = self._edge_cat(z, edge_index)        # [E, 2D]
    logit = self.edge_mlp_logit(h).view(-1)  # [E]
    rsum = self.edge_mlp_rsum(h).view(-1)    # [E]
    alpha = self.edge_mlp_alpha(h).view(-1)  # [E]
    return logit, rsum, alpha
```

**Parallel Execution**:
```
Edge Features [E, 256]
        ↓     ↓     ↓
     MLP1  MLP2  MLP3   (Parallel, no dependencies)
        ↓     ↓     ↓
    logit rsum alpha
     [E]   [E]   [E]
```

### 4. Complete Forward Pass

```python
def forward(self, x, mp_edge_index, edge_index_eval):
    """
    End-to-end prediction.
    
    Args:
        x: Node features [N, F]
        mp_edge_index: Message-passing graph [2, E_mp]
        edge_index_eval: Edges to evaluate [2, E_eval]
    
    Returns:
        Tuple of (logit, rsum, alpha) predictions
    """
    z = self.encode(x, mp_edge_index)           # Learn representations
    return self.decode_all(z, edge_index_eval)  # Score edges
```

**Two-Graph Design**:
1. **Message-Passing Graph** (`mp_edge_index`):
   - Used for encoding (information flow)
   - Typically bipartite (weak ↔ strong)
   - Dense enough for good representations

2. **Evaluation Graph** (`edge_index_eval`):
   - Edges to predict/score
   - Can be different from MP graph
   - Usually candidate pairs or test set

**Example Usage**:
```python
model = PairPowerGNN(in_channels=5, hidden=128)

# Training
x = data.x  # [500, 5]
mp_edges = build_bipartite_knn(...)  # [2, 4000]
pos_edges = data.edge_index_pos      # [2, 237] (ground truth)
neg_edges = generate_negatives(...)  # [2, 237] (hard negatives)

# Forward pass
logit_pos, rsum_pos, alpha_pos = model(x, mp_edges, pos_edges)
logit_neg, _, _ = model(x, mp_edges, neg_edges)

# Loss computation
loss = compute_multi_task_loss(logit_pos, logit_neg, rsum_pos, alpha_pos, ...)
```

---

## 🎨 Design Decisions

### Why Three Separate MLPs?

**Option 1: Shared MLP with multi-head output**
```python
# NOT USED (but possible)
self.shared_mlp = nn.Sequential(...)
logit, rsum, alpha = torch.split(self.shared_mlp(h), [1,1,1], dim=-1)
```
❌ **Drawbacks**:
- Forces shared representations
- Different objectives compete
- Harder to tune per-task

**Option 2: Separate MLPs (CHOSEN)**
```python
# USED IN MODEL
self.edge_mlp_logit = nn.Sequential(...)
self.edge_mlp_rsum = nn.Sequential(...)
self.edge_mlp_alpha = nn.Sequential(...)
```
✅ **Benefits**:
- Task-specific feature extraction
- Independent gradient flow
- Easier to debug per-task
- Can tune depth/width separately

### Why In-Place Operations?

```python
z = F.relu(z, inplace=True)
```

**Benefits**:
- Reduces memory footprint (no extra tensor allocation)
- Faster execution (no copy operation)
- Important for large graphs (500+ nodes)

**Trade-off**:
- Can't use original tensor afterward
- Not an issue here (no skip connections)

### Why Dropout in Decoders?

```python
nn.Dropout(dropout)  # Applied in each MLP
```

**Purpose**:
- Prevents overfitting to training pairs
- Forces redundant representations
- Improves generalization to new scenarios

**Placement**:
- After ReLU (standard practice)
- Before final linear layer
- Same rate as encoder (consistency)

---

## 📊 Model Complexity Analysis

### Parameter Count

```python
# Encoder
Layer 0: 5×128 + 128 = 768
Layers 1-2: (128×128 + 128) × 2 = 32,896
Total Encoder: 33,664 parameters

# Decoders (each has same structure)
MLP Layer 1: 256×128 + 128 = 32,896
MLP Layer 2: 128×1 + 1 = 129
Per Decoder: 33,025 parameters
Total Decoders: 99,075 parameters (3 MLPs)

# Grand Total
Total Parameters: ~133K parameters ≈ 532 KB (FP32)
```

### Computational Complexity

**Encoding Phase**:
$$O(|E_{\text{mp}}| \cdot D^2 \cdot L)$$
- $|E_{\text{mp}}|$: Number of message-passing edges
- $D$: Hidden dimension (128)
- $L$: Number of layers (3)

**Decoding Phase**:
$$O(|E_{\text{eval}}| \cdot D^2)$$
- $|E_{\text{eval}}|$: Number of edges to score

**Example (500 users)**:
- MP edges: ~4,000 (bipartite KNN with K=8)
- Eval edges: ~250 (positive + negative pairs)
- Encoding: $4000 \times 128^2 \times 3 \approx 196M$ FLOPs
- Decoding: $250 \times 128^2 \approx 4M$ FLOPs

### Memory Footprint (Inference)

```
Node features: 500 × 5 × 4 bytes = 10 KB
Node embeddings: 500 × 128 × 4 bytes = 256 KB
Edge features: 250 × 256 × 4 bytes = 256 KB
Model weights: 133K × 4 bytes = 532 KB
Total: ~1.1 MB (excluding PyTorch overhead)
```

---

## 🧪 Usage Examples

### Example 1: Model Initialization

```python
from models.pairpower_gnn import PairPowerGNN
import torch

# Standard configuration
model = PairPowerGNN(
    in_channels=5,      # NOMA features
    hidden=128,         # Hidden dimension
    out_channels=128,   # Embedding dimension
    num_layers=3,       # GraphSAGE layers
    dropout=0.2         # Regularization
)

print(f"Model has {sum(p.numel() for p in model.parameters()):,} parameters")
# Output: Model has 133,089 parameters
```

### Example 2: Training Forward Pass

```python
# Prepare data
x = data.x.to(device)                        # [N, 5]
mp_edges = build_mp_graph(data).to(device)   # [2, E_mp]
pos_edges = data.edge_index_pos.to(device)   # [2, E_pos]
neg_edges = generate_negatives(data).to(device)  # [2, E_neg]

# Forward pass
model.train()
logit_pos, rsum_pos, alpha_pos = model(x, mp_edges, pos_edges)
logit_neg, _, _ = model(x, mp_edges, neg_edges)

# Compute loss
loss = multitask_loss(
    logit_pos, logit_neg,
    rsum_pos, alpha_pos,
    data.y_pos_rsum, data.y_pos_alpha
)
```

### Example 3: Inference

```python
model.eval()
with torch.no_grad():
    # Score all candidate pairs
    logit, rsum_pred, alpha_pred = model(x, mp_edges, candidate_edges)
    
    # Get pairing probabilities
    prob = torch.sigmoid(logit)
    
    # Filter high-confidence pairs
    confident = prob > 0.8
    selected_pairs = candidate_edges[:, confident]
    selected_alpha = alpha_pred[confident]
    
    print(f"Selected {selected_pairs.size(1)} pairs with confidence > 0.8")
```

### Example 4: Extracting Node Embeddings

```python
# Get learned representations
model.eval()
with torch.no_grad():
    embeddings = model.encode(x, mp_edges)  # [N, 128]
    
# Use for visualization or analysis
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

embeddings_2d = TSNE(n_components=2).fit_transform(embeddings.cpu().numpy())
plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], 
            c=data.h_db, cmap='viridis')
plt.colorbar(label='Channel Gain (dB)')
plt.title('Learned User Embeddings (t-SNE)')
plt.show()
```

### Example 5: Fine-Tuning Specific Heads

```python
# Freeze encoder, only train alpha head
for param in model.convs.parameters():
    param.requires_grad = False
for param in model.edge_mlp_logit.parameters():
    param.requires_grad = False
for param in model.edge_mlp_rsum.parameters():
    param.requires_grad = False

# Only alpha head parameters will be updated
optimizer = torch.optim.Adam(
    filter(lambda p: p.requires_grad, model.parameters()),
    lr=1e-4
)
```

---

## 🔧 Customization Guide

### Adding a New Decoder Head

```python
# In __init__
self.edge_mlp_custom = nn.Sequential(
    nn.Linear(edge_in, out_channels),
    nn.ReLU(inplace=True),
    nn.Dropout(dropout),
    nn.Linear(out_channels, 1),
    nn.Sigmoid()  # Or appropriate activation
)

# In decode_all
def decode_all(self, z, edge_index):
    h = self._edge_cat(z, edge_index)
    logit = self.edge_mlp_logit(h).view(-1)
    rsum = self.edge_mlp_rsum(h).view(-1)
    alpha = self.edge_mlp_alpha(h).view(-1)
    custom = self.edge_mlp_custom(h).view(-1)  # New output
    return logit, rsum, alpha, custom
```

### Using Different Aggregation

```python
from torch_geometric.nn import GCNConv, GATConv

# Replace SAGEConv with GCNConv
self.convs.append(GCNConv(in_channels, hidden))

# Or use Graph Attention
self.convs.append(GATConv(in_channels, hidden, heads=4))
```

### Adding Skip Connections

```python
def encode(self, x, edge_index):
    z = x
    z_skip = None
    for i, conv in enumerate(self.convs):
        z = conv(z, edge_index)
        if i == 0:
            z_skip = z.clone()  # Save first layer
        if i != len(self.convs)-1:
            z = F.relu(z, inplace=False)  # Can't use inplace with skip
            z = self.dropout(z)
    z = z + z_skip  # Add skip connection
    return z
```

---

## 🐛 Common Issues and Solutions

### Issue 1: NaN Loss During Training

**Symptoms**:
```
Epoch 5: Loss=nan
```

**Causes & Solutions**:
1. **Exploding gradients**
   ```python
   # Add gradient clipping
   torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
   ```

2. **Learning rate too high**
   ```python
   # Reduce learning rate
   optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)  # Instead of 1e-3
   ```

3. **Numerical instability in sigmoid**
   ```python
   # Use BCEWithLogitsLoss (combines sigmoid + BCE, more stable)
   loss = F.binary_cross_entropy_with_logits(logit, labels)
   ```

### Issue 2: Overfitting (High Train, Low Val AUC)

**Solutions**:
```python
# 1. Increase dropout
model = PairPowerGNN(..., dropout=0.4)

# 2. Add weight decay
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-3)

# 3. Reduce model capacity
model = PairPowerGNN(..., hidden=64, num_layers=2)
```

### Issue 3: Slow Training

**Optimization strategies**:
```python
# 1. Use mixed precision training
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()

with autocast():
    logit, rsum, alpha = model(x, mp_edges, eval_edges)
    loss = compute_loss(...)
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()

# 2. Reduce MP graph size
CFG.MP_K = 5  # Fewer neighbors per node

# 3. Enable cuDNN benchmarking
torch.backends.cudnn.benchmark = True
```

### Issue 4: Memory Overflow

**Solutions**:
```python
# 1. Reduce batch size
CFG.BATCH_SIZE = 1

# 2. Reduce hidden dimension
model = PairPowerGNN(..., hidden=64)

# 3. Use gradient checkpointing (PyTorch Geometric 2.0+)
from torch_geometric.utils import checkpoint
z = checkpoint(model.encode, x, edge_index)
```

---

## 📚 References

### GraphSAGE
- Hamilton et al., "Inductive Representation Learning on Large Graphs," NeurIPS 2017
- Paper: https://arxiv.org/abs/1706.02216

### Multi-Task Learning
- Caruana, "Multitask Learning," Machine Learning 1997
- Ruder, "An Overview of Multi-Task Learning," arXiv 2017

### NOMA Background
- Ding et al., "Application of NOMA in 5G and Beyond," IEEE CommMag 2017

---

## ✅ Testing Checklist

Before deploying:
- [ ] Model initializes without errors
- [ ] Forward pass produces expected shapes
- [ ] Gradients flow to all parameters
- [ ] Loss decreases during training
- [ ] Predictions are in valid ranges (alpha ∈ (0,1))
- [ ] Inference is faster than training
- [ ] Model can save/load correctly

---

**Last Updated**: October 17, 2025  
**Version**: 1.0.0  
**Author**: NOMA-GNN Development Team
