# Loss Functions Documentation

## 📋 File: `training/losses.py`

### 🎯 Purpose
Implements the multi-task loss function that jointly trains the NOMA-GNN for:
1. **Edge classification**: Predict if a user pair should be formed (binary)
2. **Sum-rate regression**: Predict total throughput of paired users (continuous)
3. **Power allocation**: Predict optimal power split coefficient α (continuous)

---

## 🧮 Mathematical Formulation

### Multi-Task Objective

$$\mathcal{L}_{\text{total}} = \lambda_{\text{BCE}} \cdot \mathcal{L}_{\text{BCE}} + \lambda_{\text{Rsum}} \cdot \mathcal{L}_{\text{Rsum}} + \lambda_{\alpha} \cdot \mathcal{L}_{\alpha}$$

where:
- $\mathcal{L}_{\text{BCE}}$: Binary Cross-Entropy (classification)
- $\mathcal{L}_{\text{Rsum}}$: Mean Absolute Error for sum-rate (regression)
- $\mathcal{L}_{\alpha}$: Mean Absolute Error for power split (regression)
- $\lambda_{\text{BCE}}, \lambda_{\text{Rsum}}, \lambda_{\alpha}$: Task-specific weights

---

## 📊 Component Losses

### 1. Binary Cross-Entropy (BCE)

$$\mathcal{L}_{\text{BCE}} = -\frac{1}{N_{\text{pos}} + N_{\text{neg}}} \sum_{i} \left[ y_i \log(\sigma(z_i)) + (1-y_i) \log(1-\sigma(z_i)) \right]$$

where:
- $z_i$ = logit (raw model output) for edge $i$
- $\sigma(z) = \frac{1}{1+e^{-z}}$ = sigmoid function
- $y_i \in \{0,1\}$ = ground truth label
  - $y_i = 1$ for positive edges (should be paired)
  - $y_i = 0$ for negative edges (should not be paired)
- $N_{\text{pos}}$ = number of positive edges
- $N_{\text{neg}}$ = number of negative edges

**Purpose**: Learn to distinguish high-quality pairs from low-quality/infeasible pairs

**Why BCE?**
- ✅ **Probabilistic**: Outputs interpretable confidence scores
- ✅ **Smooth gradients**: Works well with sigmoid
- ✅ **Balanced**: Treats false positives and false negatives equally
- ✅ **Standard**: Widely used for binary classification

**Implementation**:
```python
# Combine positive and negative edges
pos_labels = torch.ones_like(pos_logits)   # [N_pos]
neg_labels = torch.zeros_like(neg_logits)  # [N_neg]
logits = torch.cat([pos_logits, neg_logits], dim=0)  # [N_pos + N_neg]
labels = torch.cat([pos_labels, neg_labels], dim=0)  # [N_pos + N_neg]

# Binary cross-entropy with logits (numerically stable)
loss_bce = F.binary_cross_entropy_with_logits(logits, labels)
```

**Why `binary_cross_entropy_with_logits`?**
```python
# UNSTABLE (two operations, numerical issues):
probs = torch.sigmoid(logits)
loss = F.binary_cross_entropy(probs, labels)

# STABLE (fused operation, log-sum-exp trick):
loss = F.binary_cross_entropy_with_logits(logits, labels)
```

**Typical Values**:
- **Early training**: 0.6-0.8 (near random guessing)
- **Mid training**: 0.2-0.4 (learning discrimination)
- **Converged**: 0.05-0.15 (strong separation)

---

### 2. Sum-Rate MAE

$$\mathcal{L}_{\text{Rsum}} = \frac{1}{N_{\text{pos}}} \sum_{i=1}^{N_{\text{pos}}} |R_{\text{sum}}^{(i)} - \hat{R}_{\text{sum}}^{(i)}|$$

where:
- $R_{\text{sum}}^{(i)}$ = true sum-rate for positive edge $i$ (bits/Hz)
- $\hat{R}_{\text{sum}}^{(i)}$ = predicted sum-rate (model output)
- MAE = Mean Absolute Error

**Purpose**: Accurately predict throughput benefit of forming a pair

**Why MAE (not MSE)?**

**Mean Absolute Error (L1)**:
$$\text{MAE} = \frac{1}{N}\sum_i |y_i - \hat{y}_i|$$
- ✅ **Robust to outliers**: Linear penalty
- ✅ **Interpretable**: Same units as target (bits/Hz)
- ✅ **Balanced**: Treats over/under-prediction equally

**Mean Squared Error (L2)**:
$$\text{MSE} = \frac{1}{N}\sum_i (y_i - \hat{y}_i)^2$$
- ❌ **Sensitive to outliers**: Quadratic penalty
- ❌ **Less interpretable**: Squared units
- ✅ **Smooth gradients**: Differentiable at 0

**Our Choice**: MAE because sum-rate distributions have long tails (outliers are common)

**Implementation**:
```python
# Only for positive edges (negatives don't have sum-rate labels)
loss_rsum = F.l1_loss(pos_rsum_pred, pos_rsum_true)
```

**Typical Values**:
- **Early training**: 0.3-0.5 bits/Hz (poor prediction)
- **Mid training**: 0.1-0.2 bits/Hz (learning trends)
- **Converged**: 0.02-0.05 bits/Hz (accurate prediction)

---

### 3. Power Split MAE

$$\mathcal{L}_{\alpha} = \frac{1}{N_{\text{pos}}} \sum_{i=1}^{N_{\text{pos}}} |\alpha^{(i)} - \hat{\alpha}^{(i)}|$$

where:
- $\alpha^{(i)}$ = true power split for positive edge $i$ (range [0,1])
- $\hat{\alpha}^{(i)}$ = predicted power split (model output)

**Purpose**: Learn optimal power allocation between weak and strong users

**Power Split Semantics**:
- $\alpha = 0.7$ → 70% power to weak user, 30% to strong user
- $\alpha = 0.5$ → Equal power split
- $\alpha = 0.3$ → 30% power to weak user, 70% to strong user

**Typical Range**: 0.6-0.8 (more power to weak user for fairness)

**Why MAE?**
- ✅ **Bounded target**: $\alpha \in [0,1]$ has limited range
- ✅ **Interpretable**: Direct percentage error
- ✅ **Balanced**: Small errors in α can significantly impact sum-rate

**Implementation**:
```python
loss_alpha = F.l1_loss(pos_alpha_pred, pos_alpha_true)
```

**Typical Values**:
- **Early training**: 0.05-0.10 (10% error)
- **Mid training**: 0.02-0.04 (2-4% error)
- **Converged**: 0.005-0.015 (0.5-1.5% error)

---

## ⚖️ Loss Weighting Strategy

### Default Configuration

```python
lambda_bce = 1.0     # Classification is primary task
lambda_rsum = 0.5    # Sum-rate is secondary
lambda_alpha = 0.5   # Power split is secondary
```

### Rationale

**Why BCE has higher weight (1.0)?**
1. **Core objective**: First decide IF to pair
2. **Harder task**: Binary classification requires more learning
3. **Cascading effect**: Wrong pairing → wrong Rsum/α predictions

**Why Rsum and α have equal weights (0.5)?**
1. **Joint optimization**: Both needed for complete solution
2. **Similar importance**: Both affect final throughput
3. **Balanced training**: Prevents one task from dominating

### Dynamic Weighting (Advanced)

```python
# Task uncertainty weighting
log_var_bce = nn.Parameter(torch.zeros(1))
log_var_rsum = nn.Parameter(torch.zeros(1))
log_var_alpha = nn.Parameter(torch.zeros(1))

loss = (loss_bce / (2*torch.exp(log_var_bce)) + log_var_bce/2 +
        loss_rsum / (2*torch.exp(log_var_rsum)) + log_var_rsum/2 +
        loss_alpha / (2*torch.exp(log_var_alpha)) + log_var_alpha/2)
```

**Reference**: *Multi-Task Learning Using Uncertainty to Weigh Losses* (Kendall et al., 2018)

---

## 🔧 Function Signature

```python
def multitask_loss(
    pos_logits: torch.Tensor,      # [N_pos] - Logits for positive edges
    neg_logits: torch.Tensor,      # [N_neg] - Logits for negative edges
    pos_rsum_pred: torch.Tensor,   # [N_pos] - Predicted sum-rates
    pos_alpha_pred: torch.Tensor,  # [N_pos] - Predicted power splits
    pos_rsum_true: torch.Tensor,   # [N_pos] - True sum-rates (labels)
    pos_alpha_true: torch.Tensor,  # [N_pos] - True power splits (labels)
    lambda_bce: float = 1.0,       # BCE weight
    lambda_rsum: float = 0.5,      # Sum-rate MAE weight
    lambda_alpha: float = 0.5      # Alpha MAE weight
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """
    Multi-task loss for NOMA user pairing.
    
    Returns:
        total_loss: Weighted combination of all losses
        loss_dict: Individual loss values for logging
    """
```

---

## 📝 Complete Implementation

```python
import torch
import torch.nn.functional as F

def multitask_loss(pos_logits, neg_logits, pos_rsum_pred, pos_alpha_pred,
                   pos_rsum_true, pos_alpha_true,
                   lambda_bce=1.0, lambda_rsum=0.5, lambda_alpha=0.5):
    """
    Multi-task loss: BCE for edge classification + MAE for regression.
    
    Args:
        pos_logits: [N_pos] - Raw scores for positive edges
        neg_logits: [N_neg] - Raw scores for negative edges
        pos_rsum_pred: [N_pos] - Predicted sum-rates
        pos_alpha_pred: [N_pos] - Predicted power splits
        pos_rsum_true: [N_pos] - Ground truth sum-rates
        pos_alpha_true: [N_pos] - Ground truth power splits
        lambda_bce: Weight for classification loss
        lambda_rsum: Weight for sum-rate regression loss
        lambda_alpha: Weight for alpha regression loss
    
    Returns:
        total_loss: Scalar tensor for backpropagation
        loss_parts: Dictionary with individual loss components
    """
    # 1. Classification loss (BCE)
    pos_labels = torch.ones_like(pos_logits)   # Positive edges → label 1
    neg_labels = torch.zeros_like(neg_logits)  # Negative edges → label 0
    
    # Concatenate for unified BCE computation
    logits = torch.cat([pos_logits, neg_logits], dim=0)
    labels = torch.cat([pos_labels, neg_labels], dim=0)
    
    # Numerically stable BCE with logits
    loss_bce = F.binary_cross_entropy_with_logits(logits, labels)
    
    # 2. Sum-rate regression loss (MAE)
    loss_rsum = F.l1_loss(pos_rsum_pred, pos_rsum_true)
    
    # 3. Power split regression loss (MAE)
    loss_alpha = F.l1_loss(pos_alpha_pred, pos_alpha_true)
    
    # 4. Weighted combination
    total_loss = (lambda_bce * loss_bce + 
                  lambda_rsum * loss_rsum + 
                  lambda_alpha * loss_alpha)
    
    # 5. Return total loss and components (for logging)
    loss_parts = {
        "bce": loss_bce.item(),
        "rsum": loss_rsum.item(),
        "alpha": loss_alpha.item()
    }
    
    return total_loss, loss_parts
```

---

## 🎯 Usage Examples

### Example 1: Basic Training Step

```python
from training.losses import multitask_loss

# Forward pass (from model)
pos_logit, pos_rsum_pred, pos_alpha_pred = model(x, mp_edge, pos_edge)
neg_logit, _, _ = model(x, mp_edge, neg_edge)

# Compute loss
loss, parts = multitask_loss(
    pos_logit, neg_logit,
    pos_rsum_pred, pos_alpha_pred,
    data.y_pos_rsum, data.y_pos_alpha,
    lambda_bce=1.0, lambda_rsum=0.5, lambda_alpha=0.5
)

# Backpropagation
optimizer.zero_grad()
loss.backward()
optimizer.step()

# Logging
print(f"Total: {loss.item():.4f} | "
      f"BCE: {parts['bce']:.4f} | "
      f"Rsum: {parts['rsum']:.4f} | "
      f"Alpha: {parts['alpha']:.4f}")
```

**Output**:
```
Total: 0.3421 | BCE: 0.1234 | Rsum: 0.0567 | Alpha: 0.0103
```

### Example 2: Custom Weights

```python
# Prioritize classification over regression
loss, parts = multitask_loss(
    pos_logit, neg_logit,
    pos_rsum_pred, pos_alpha_pred,
    data.y_pos_rsum, data.y_pos_alpha,
    lambda_bce=2.0,    # Double weight for classification
    lambda_rsum=0.5,
    lambda_alpha=0.5
)
```

### Example 3: Disable Regression Losses

```python
# Train only classification (initial warm-up)
loss, parts = multitask_loss(
    pos_logit, neg_logit,
    pos_rsum_pred, pos_alpha_pred,
    data.y_pos_rsum, data.y_pos_alpha,
    lambda_bce=1.0,
    lambda_rsum=0.0,  # Disable sum-rate loss
    lambda_alpha=0.0  # Disable alpha loss
)
```

### Example 4: Loss Component Analysis

```python
# Track loss evolution over epochs
import matplotlib.pyplot as plt

history = {"bce": [], "rsum": [], "alpha": [], "total": []}

for epoch in range(num_epochs):
    for batch in train_loader:
        loss, parts = multitask_loss(...)
        history["bce"].append(parts["bce"])
        history["rsum"].append(parts["rsum"])
        history["alpha"].append(parts["alpha"])
        history["total"].append(loss.item())

# Plot
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes[0, 0].plot(history["total"]); axes[0, 0].set_title("Total Loss")
axes[0, 1].plot(history["bce"]); axes[0, 1].set_title("BCE Loss")
axes[1, 0].plot(history["rsum"]); axes[1, 0].set_title("Rsum MAE")
axes[1, 1].plot(history["alpha"]); axes[1, 1].set_title("Alpha MAE")
plt.savefig("loss_curves.png")
```

---

## 📊 Loss Landscape Analysis

### Convergence Patterns

**Epoch 1-10 (Early Training)**:
```
BCE:   0.6-0.4  (learning basic discrimination)
Rsum:  0.3-0.2  (rough estimates)
Alpha: 0.08-0.05 (coarse power allocation)
Total: 1.0-0.6
```

**Epoch 10-30 (Mid Training)**:
```
BCE:   0.4-0.2  (refining boundaries)
Rsum:  0.2-0.1  (improving accuracy)
Alpha: 0.05-0.02 (fine-tuning splits)
Total: 0.6-0.3
```

**Epoch 30-60 (Late Training)**:
```
BCE:   0.2-0.1  (high confidence)
Rsum:  0.1-0.03 (precise predictions)
Alpha: 0.02-0.01 (optimal allocations)
Total: 0.3-0.15
```

### Typical Final Values

| Loss Component | Good Performance | Excellent Performance |
|----------------|------------------|----------------------|
| BCE            | 0.1-0.15         | < 0.1                |
| Rsum MAE       | 0.03-0.05        | < 0.03               |
| Alpha MAE      | 0.01-0.015       | < 0.01               |
| Total          | 0.15-0.20        | < 0.15               |

---

## 🐛 Troubleshooting

### Issue 1: NaN Loss

**Symptoms**:
```python
Total: 0.3421 | BCE: 0.1234 | Rsum: 0.0567 | Alpha: 0.0103
Total: 0.2876 | BCE: 0.0987 | Rsum: 0.0432 | Alpha: 0.0089
Total: nan | BCE: nan | Rsum: nan | Alpha: nan
```

**Causes & Solutions**:

**Cause 1: Exploding gradients**
```python
# Solution: Gradient clipping
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

**Cause 2: Invalid predictions**
```python
# Check for NaNs in predictions
assert torch.isfinite(pos_rsum_pred).all(), "NaN in Rsum predictions"
assert torch.isfinite(pos_alpha_pred).all(), "NaN in Alpha predictions"
```

**Cause 3: Extreme learning rate**
```python
# Solution: Reduce learning rate
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)  # From 1e-3
```

### Issue 2: BCE Not Decreasing

**Symptoms**:
```
Epoch 10: BCE = 0.65
Epoch 20: BCE = 0.63
Epoch 30: BCE = 0.62  (stuck near 0.6)
```

**Causes & Solutions**:

**Cause 1: Negatives are too easy**
```python
# Solution: Use harder negatives
neg_edge_index = generate_negatives(data, sic_db=8.0, ratio=2.0)
```

**Cause 2: Model capacity too low**
```python
# Solution: Increase model size
CFG.HIDDEN_DIM = 256  # From 128
CFG.NUM_LAYERS = 4    # From 3
```

**Cause 3: Imbalanced pos/neg ratio**
```python
# Solution: Use weighted BCE
pos_weight = torch.tensor([num_neg / num_pos])
loss_bce = F.binary_cross_entropy_with_logits(
    logits, labels, pos_weight=pos_weight
)
```

### Issue 3: Rsum/Alpha MAE Not Improving

**Symptoms**:
```
Epoch 10: Rsum MAE = 0.15, Alpha MAE = 0.03
Epoch 30: Rsum MAE = 0.14, Alpha MAE = 0.029  (minimal improvement)
```

**Causes & Solutions**:

**Cause 1: Lambda weights too low**
```python
# Solution: Increase regression weights
lambda_rsum = 1.0  # From 0.5
lambda_alpha = 1.0  # From 0.5
```

**Cause 2: Regression heads underpowered**
```python
# In pairpower_gnn.py, increase decoder size
self.rsum_head = nn.Sequential(
    nn.Linear(2*hidden, hidden),  # Add hidden layer
    nn.ReLU(),
    nn.Dropout(dropout),
    nn.Linear(hidden, 1)
)
```

**Cause 3: Feature normalization issues**
```python
# Check if Rsum/Alpha features are normalized
print(f"Rsum mean: {pos_rsum_true.mean():.4f}, std: {pos_rsum_true.std():.4f}")
print(f"Alpha mean: {pos_alpha_true.mean():.4f}, std: {pos_alpha_true.std():.4f}")

# If std is very large, normalize targets
rsum_scaler = (pos_rsum_true.mean(), pos_rsum_true.std())
pos_rsum_true_norm = (pos_rsum_true - rsum_scaler[0]) / rsum_scaler[1]
```

### Issue 4: Oscillating Loss

**Symptoms**:
```
Epoch 10: Total = 0.35
Epoch 11: Total = 0.25
Epoch 12: Total = 0.40
Epoch 13: Total = 0.22
Epoch 14: Total = 0.38  (unstable)
```

**Causes & Solutions**:

**Cause 1: Learning rate too high**
```python
# Solution: Reduce LR
optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4)  # From 1e-3
```

**Cause 2: Small batch size**
```python
# Solution: Increase batch size
train_loader = DataLoader(dataset, batch_size=4, shuffle=True)  # From 2
```

**Cause 3: High variance in data**
```python
# Solution: Normalize targets
from data.normalization import FeatureScaler
scaler = FeatureScaler()
scaler.fit_rsum_alpha(train_set)
pos_rsum_true_norm = scaler.transform_rsum(pos_rsum_true)
pos_alpha_true_norm = scaler.transform_alpha(pos_alpha_true)
```

---

## 🔬 Advanced Topics

### Loss Weighting Strategies

#### 1. Uncertainty Weighting

```python
class UncertaintyWeightedLoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.log_var_bce = nn.Parameter(torch.zeros(1))
        self.log_var_rsum = nn.Parameter(torch.zeros(1))
        self.log_var_alpha = nn.Parameter(torch.zeros(1))
    
    def forward(self, loss_bce, loss_rsum, loss_alpha):
        precision_bce = torch.exp(-self.log_var_bce)
        precision_rsum = torch.exp(-self.log_var_rsum)
        precision_alpha = torch.exp(-self.log_var_alpha)
        
        loss = (precision_bce * loss_bce + self.log_var_bce +
                precision_rsum * loss_rsum + self.log_var_rsum +
                precision_alpha * loss_alpha + self.log_var_alpha)
        return loss
```

#### 2. Gradient Normalization

```python
def grad_norm_loss(loss_bce, loss_rsum, loss_alpha, model, alpha=1.5):
    """
    GradNorm: Gradient Normalization for Adaptive Loss Balancing
    """
    # Compute gradients for each loss
    grads_bce = torch.autograd.grad(loss_bce, model.parameters(), 
                                     retain_graph=True, create_graph=True)
    grads_rsum = torch.autograd.grad(loss_rsum, model.parameters(), 
                                      retain_graph=True, create_graph=True)
    grads_alpha = torch.autograd.grad(loss_alpha, model.parameters(), 
                                       retain_graph=True, create_graph=True)
    
    # Compute gradient norms
    norm_bce = torch.norm(torch.stack([g.norm() for g in grads_bce]))
    norm_rsum = torch.norm(torch.stack([g.norm() for g in grads_rsum]))
    norm_alpha = torch.norm(torch.stack([g.norm() for g in grads_alpha]))
    
    # Target norm (average)
    mean_norm = (norm_bce + norm_rsum + norm_alpha) / 3
    
    # Adaptive weights (learnable)
    w_bce = nn.Parameter(torch.ones(1))
    w_rsum = nn.Parameter(torch.ones(1))
    w_alpha = nn.Parameter(torch.ones(1))
    
    # Weighted loss
    loss = w_bce*loss_bce + w_rsum*loss_rsum + w_alpha*loss_alpha
    
    # GradNorm loss (for updating weights)
    grad_loss = (torch.abs(norm_bce - mean_norm) +
                 torch.abs(norm_rsum - mean_norm) +
                 torch.abs(norm_alpha - mean_norm))
    
    return loss + alpha * grad_loss
```

#### 3. Dynamic Loss Balancing

```python
class DynamicWeightedLoss:
    def __init__(self, initial_weights=[1.0, 0.5, 0.5]):
        self.weights = initial_weights
        self.loss_history = {"bce": [], "rsum": [], "alpha": []}
    
    def update_weights(self, loss_bce, loss_rsum, loss_alpha):
        # Track losses
        self.loss_history["bce"].append(loss_bce)
        self.loss_history["rsum"].append(loss_rsum)
        self.loss_history["alpha"].append(loss_alpha)
        
        # Compute relative improvement rates (last 10 epochs)
        if len(self.loss_history["bce"]) > 10:
            rate_bce = self._improvement_rate("bce")
            rate_rsum = self._improvement_rate("rsum")
            rate_alpha = self._improvement_rate("alpha")
            
            # Increase weight for slowly improving tasks
            self.weights[0] *= (1 + (1 - rate_bce))
            self.weights[1] *= (1 + (1 - rate_rsum))
            self.weights[2] *= (1 + (1 - rate_alpha))
            
            # Normalize to sum to 2.0
            total = sum(self.weights)
            self.weights = [w * 2.0 / total for w in self.weights]
    
    def _improvement_rate(self, task):
        recent = self.loss_history[task][-10:]
        old = self.loss_history[task][-20:-10]
        return (np.mean(old) - np.mean(recent)) / np.mean(old)
    
    def __call__(self, loss_bce, loss_rsum, loss_alpha):
        self.update_weights(loss_bce, loss_rsum, loss_alpha)
        return (self.weights[0] * loss_bce +
                self.weights[1] * loss_rsum +
                self.weights[2] * loss_alpha)
```

---

## ✅ Best Practices

### 1. Loss Monitoring
- **Log all components** separately (not just total)
- **Plot curves** to visualize convergence
- **Check ratios**: BCE should dominate early, regression later

### 2. Hyperparameter Tuning
- **Start with equal weights** (1.0, 0.5, 0.5)
- **Tune one at a time**: Adjust based on which metric needs improvement
- **Validate on held-out set**: Don't overfit to validation set

### 3. Debugging
- **Assert finite values** after every forward pass
- **Print gradients**: Check if vanishing/exploding
- **Visualize predictions**: Qualitative assessment

### 4. Numerical Stability
- **Use `with_logits` versions**: Avoid explicit sigmoid
- **Gradient clipping**: Prevent explosions
- **Learning rate scheduling**: Reduce LR if loss plateaus

---

**Last Updated**: October 17, 2025  
**Version**: 1.0.0  
**Author**: NOMA-GNN Development Team
