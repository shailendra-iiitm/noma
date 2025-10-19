# Evaluation Metrics Documentation

## 🎯 Purpose
Comprehensive guide to metrics used for evaluating NOMA-GNN model performance, including classification metrics, regression metrics, and composite scores.

---

## 📊 Metric Categories

### 1. Classification Metrics (Edge Pairing Quality)
### 2. Regression Metrics (Prediction Accuracy)
### 3. Matching Metrics (System-Level Performance)
### 4. Computational Metrics (Efficiency)

---

## 🎯 Classification Metrics

### AUC-ROC (Area Under ROC Curve)

**Full Name**: Area Under the Receiver Operating Characteristic Curve

**Definition**:
$$\text{AUC} = P(\text{score}(\text{positive edge}) > \text{score}(\text{negative edge}))$$

**Interpretation**: Probability that model ranks a random positive edge higher than a random negative edge

**Range**: [0, 1]
- **0.5**: Random guessing
- **0.7-0.8**: Fair performance
- **0.8-0.9**: Good performance
- **0.9-1.0**: Excellent performance

**Why AUC-ROC?**
- ✅ **Threshold-independent**: Evaluates ranking, not classification
- ✅ **Balanced**: Works well with imbalanced classes
- ✅ **Interpretable**: Single number summarizes entire ROC curve
- ✅ **Standard**: Widely used in binary classification

**ROC Curve**:
```
True Positive Rate (TPR) = TP / (TP + FN)  (Recall, Sensitivity)
False Positive Rate (FPR) = FP / (FP + TN)  (1 - Specificity)

ROC plots TPR vs. FPR at different classification thresholds
```

**Implementation**:
```python
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib.pyplot as plt

# Get predictions
pos_scores = model(x, mp_edge, pos_edge)[0].sigmoid().cpu().numpy()
neg_scores = model(x, mp_edge, neg_edge)[0].sigmoid().cpu().numpy()

# Concatenate and label
scores = np.concatenate([pos_scores, neg_scores])
labels = np.concatenate([np.ones_like(pos_scores), np.zeros_like(neg_scores)])

# Compute AUC
auc = roc_auc_score(labels, scores)
print(f"AUC-ROC: {auc:.4f}")

# Plot ROC curve
fpr, tpr, thresholds = roc_curve(labels, scores)
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.4f})')
plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic (ROC) Curve')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('roc_curve.png')
```

**Example Output**:
```
AUC-ROC: 0.9247
```

**Interpreting AUC Values**:
```
AUC = 0.50: Model is no better than random
AUC = 0.75: 75% chance model ranks positive higher than negative
AUC = 0.92: 92% chance model ranks positive higher than negative
AUC = 1.00: Perfect ranking (all positives scored higher than negatives)
```

---

### Precision-Recall Metrics

**Precision**:
$$\text{Precision} = \frac{TP}{TP + FP} = \frac{\text{Correct Positive Predictions}}{\text{All Positive Predictions}}$$

**Recall** (Sensitivity, True Positive Rate):
$$\text{Recall} = \frac{TP}{TP + FN} = \frac{\text{Correct Positive Predictions}}{\text{All Actual Positives}}$$

**F1 Score**:
$$F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

**Implementation**:
```python
from sklearn.metrics import precision_recall_fscore_support, average_precision_score

# Binary predictions (threshold = 0.5)
pred_binary = (scores >= 0.5).astype(int)

# Compute metrics
precision, recall, f1, _ = precision_recall_fscore_support(
    labels, pred_binary, average='binary'
)

print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")

# Average Precision (area under PR curve)
ap = average_precision_score(labels, scores)
print(f"Average Precision: {ap:.4f}")
```

**Example Output**:
```
Precision: 0.8734
Recall: 0.9012
F1 Score: 0.8871
Average Precision: 0.9156
```

**When to Use Precision vs. Recall?**
- **High Precision**: Minimize false positives (prefer quality over quantity)
- **High Recall**: Minimize false negatives (prefer quantity over quality)
- **F1 Score**: Balance between precision and recall

---

### Accuracy

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$

**Warning**: Can be misleading with imbalanced classes!

**Example**:
```
95% negative edges, 5% positive edges
Always predict negative → 95% accuracy (but useless model!)
```

**Use AUC instead for imbalanced data**

---

## 📈 Regression Metrics

### Mean Absolute Error (MAE)

**Definition**:
$$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |y_i - \hat{y}_i|$$

**Interpretation**: Average absolute prediction error (same units as target)

**Sum-Rate MAE**:
```python
mae_rsum = torch.mean(torch.abs(pos_rsum_pred - pos_rsum_true)).item()
print(f"Sum-Rate MAE: {mae_rsum:.4f} bits/Hz")
```

**Power Split MAE**:
```python
mae_alpha = torch.mean(torch.abs(pos_alpha_pred - pos_alpha_true)).item()
print(f"Alpha MAE: {mae_alpha:.4f}")
```

**Example Output**:
```
Sum-Rate MAE: 0.0312 bits/Hz
Alpha MAE: 0.0089
```

**Interpretation**:
- **Rsum MAE = 0.03**: On average, predicted sum-rate is off by 0.03 bits/Hz
- **Alpha MAE = 0.01**: On average, predicted power split is off by 1%

**Good Performance Thresholds**:
| Metric | Excellent | Good | Fair | Poor |
|--------|-----------|------|------|------|
| Rsum MAE | < 0.03 | 0.03-0.05 | 0.05-0.1 | > 0.1 |
| Alpha MAE | < 0.01 | 0.01-0.02 | 0.02-0.05 | > 0.05 |

---

### Mean Squared Error (MSE)

$$\text{MSE} = \frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2$$

**Root Mean Squared Error (RMSE)**:
$$\text{RMSE} = \sqrt{\text{MSE}}$$

**Why We Use MAE Instead**:
- **MAE is robust to outliers** (linear penalty)
- **RMSE is sensitive to outliers** (quadratic penalty)
- **Sum-rate distributions have long tails** → MAE preferred

**Example**:
```python
# Both MAE and RMSE for comparison
mae_rsum = torch.mean(torch.abs(pos_rsum_pred - pos_rsum_true)).item()
rmse_rsum = torch.sqrt(torch.mean((pos_rsum_pred - pos_rsum_true)**2)).item()

print(f"Rsum MAE: {mae_rsum:.4f}")
print(f"Rsum RMSE: {rmse_rsum:.4f}")

# RMSE is always >= MAE, with larger gap indicating more outliers
```

---

### R² Score (Coefficient of Determination)

$$R^2 = 1 - \frac{\sum_{i}(y_i - \hat{y}_i)^2}{\sum_{i}(y_i - \bar{y})^2}$$

**Interpretation**: Fraction of variance explained by model
- **R² = 1**: Perfect predictions
- **R² = 0**: Model as good as predicting mean
- **R² < 0**: Model worse than predicting mean

**Implementation**:
```python
from sklearn.metrics import r2_score

r2_rsum = r2_score(pos_rsum_true.cpu(), pos_rsum_pred.cpu())
r2_alpha = r2_score(pos_alpha_true.cpu(), pos_alpha_pred.cpu())

print(f"R² (Rsum): {r2_rsum:.4f}")
print(f"R² (Alpha): {r2_alpha:.4f}")
```

**Example Output**:
```
R² (Rsum): 0.8234
R² (Alpha): 0.9012
```

---

### Relative Error

$$\text{Relative Error} = \frac{1}{N} \sum_{i=1}^{N} \frac{|y_i - \hat{y}_i|}{|y_i|}$$

**Useful when target values span wide ranges**

**Implementation**:
```python
rel_error_rsum = torch.mean(
    torch.abs(pos_rsum_pred - pos_rsum_true) / 
    (torch.abs(pos_rsum_true) + 1e-6)  # Avoid division by zero
).item()

print(f"Relative Error (Rsum): {rel_error_rsum*100:.2f}%")
```

---

## 🎯 Matching Metrics

These metrics evaluate end-to-end system performance (after greedy matching).

### Matching Accuracy

$$\text{Matching Accuracy} = \frac{\text{Correct Pairings}}{\text{Total Pairings}}$$

**Implementation**:
```python
# Ground truth pairs
gt_pairs = set([(int(a), int(b)) for a,b in data.edge_index_pos.t().tolist()])

# Predicted pairs (after greedy matching)
pred_pairs = set(predicted_pairing)  # From inference

# Compute accuracy
correct = len(gt_pairs & pred_pairs)
total = len(gt_pairs)
accuracy = correct / total

print(f"Matching Accuracy: {accuracy*100:.2f}%")
print(f"Correct: {correct}/{total}")
```

**Example Output**:
```
Matching Accuracy: 87.50%
Correct: 210/240
```

---

### System Sum-Rate

$$R_{\text{system}} = \sum_{(i,j) \in \text{Predicted Pairs}} R_{\text{sum}}(i,j)$$

**Compares predicted pairing to ground truth (Hungarian algorithm)**

**Implementation**:
```python
# Compute sum-rate for predicted pairing
pred_system_rate = sum(compute_sumrate(i, j) for i, j in predicted_pairing)

# Compute sum-rate for ground truth pairing
gt_system_rate = sum(compute_sumrate(i, j) for i, j in gt_pairs)

# Relative performance
relative_perf = pred_system_rate / gt_system_rate

print(f"Predicted System Rate: {pred_system_rate:.2f} bits/Hz")
print(f"Ground Truth System Rate: {gt_system_rate:.2f} bits/Hz")
print(f"Relative Performance: {relative_perf*100:.2f}%")
```

**Example Output**:
```
Predicted System Rate: 245.32 bits/Hz
Ground Truth System Rate: 256.18 bits/Hz
Relative Performance: 95.76%
```

**Interpretation**:
- **> 95%**: Excellent (near-optimal)
- **90-95%**: Good (practical)
- **80-90%**: Fair (some room for improvement)
- **< 80%**: Poor (significant losses)

---

### Pairing Efficiency

$$\text{Efficiency} = \frac{\text{Users Paired}}{\text{Total Users}}$$

**Implementation**:
```python
num_paired = 2 * len(predicted_pairing)  # Each pair has 2 users
num_total = data.num_nodes
efficiency = num_paired / num_total

print(f"Pairing Efficiency: {efficiency*100:.2f}%")
print(f"Paired: {num_paired}/{num_total} users")
```

**Example Output**:
```
Pairing Efficiency: 96.00%
Paired: 480/500 users
```

---

## ⏱️ Computational Metrics

### Training Time

```python
import time

start = time.time()
for epoch in range(num_epochs):
    train_one_epoch(...)
end = time.time()

total_time = end - start
time_per_epoch = total_time / num_epochs

print(f"Total Training Time: {total_time:.2f}s")
print(f"Time per Epoch: {time_per_epoch:.2f}s")
```

---

### Inference Time

```python
# Single graph inference
graph = test_set[0]
start = time.time()
predicted_pairs = infer_pairing(graph, model)
end = time.time()

inference_time = end - start
print(f"Inference Time: {inference_time*1000:.2f}ms")
print(f"Users: {graph.num_nodes}")
print(f"Time per User: {inference_time/graph.num_nodes*1000:.2f}ms")
```

---

### Model Size

```python
# Count parameters
num_params = sum(p.numel() for p in model.parameters())
num_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)

print(f"Total Parameters: {num_params:,}")
print(f"Trainable Parameters: {num_trainable:,}")

# Model size in MB
model_size_mb = num_params * 4 / (1024**2)  # 4 bytes per float32
print(f"Model Size: {model_size_mb:.2f} MB")
```

**Example Output**:
```
Total Parameters: 133,249
Trainable Parameters: 133,249
Model Size: 0.51 MB
```

---

## 📊 Composite Metrics

### Weighted Performance Score

Combine multiple metrics into single score for model selection:

$$\text{Score} = w_1 \cdot \text{AUC} + w_2 \cdot (1 - \text{MAE}_{\text{Rsum}}) + w_3 \cdot (1 - \text{MAE}_{\alpha})$$

**Implementation**:
```python
def composite_score(auc, mae_rsum, mae_alpha, 
                    w_auc=0.5, w_rsum=0.25, w_alpha=0.25):
    """
    Composite score for model selection.
    Higher is better.
    """
    score = (w_auc * auc + 
             w_rsum * (1 - mae_rsum) + 
             w_alpha * (1 - mae_alpha))
    return score

# Example
auc = 0.925
mae_rsum = 0.032
mae_alpha = 0.009

score = composite_score(auc, mae_rsum, mae_alpha)
print(f"Composite Score: {score:.4f}")
```

**Example Output**:
```
Composite Score: 0.9422
```

---

## 📈 Metric Tracking

### Comprehensive Evaluation Function

```python
@torch.no_grad()
def evaluate_comprehensive(model, loader, device, cfg):
    """
    Compute all metrics for thorough evaluation.
    """
    model.eval()
    
    # Collect predictions
    all_pos_scores, all_neg_scores = [], []
    all_pos_rsum_true, all_pos_rsum_pred = [], []
    all_pos_alpha_true, all_pos_alpha_pred = [], []
    
    for data in loader:
        data = data.to(device)
        
        # Build MP graph
        h_db = data.h_db
        idx_sorted = torch.argsort(h_db)
        weak = idx_sorted[:data.num_nodes//2]
        strong = idx_sorted[data.num_nodes//2:]
        mp_edge = build_mp_edge_index(data.x, weak, strong, 
                                       cfg.MP_TOPOLOGY, cfg.MP_K).to(device)
        
        # Generate negatives
        neg_edge = generate_negatives(data, cfg.SIC_THRESHOLD_DB,
                                       cfg.USE_ANGLE_GUARD, 
                                       cfg.MIN_ANGLE_DEG).to(device)
        
        if neg_edge.numel() == 0:
            continue
        
        # Forward pass
        pos_logit, pos_rsum_pred, pos_alpha_pred = model(
            data.x, mp_edge, data.edge_index_pos.to(device)
        )
        neg_logit, _, _ = model(data.x, mp_edge, neg_edge)
        
        # Store predictions
        all_pos_scores.append(pos_logit.sigmoid().cpu().numpy())
        all_neg_scores.append(neg_logit.sigmoid().cpu().numpy())
        all_pos_rsum_true.append(data.y_pos_rsum.cpu().numpy())
        all_pos_rsum_pred.append(pos_rsum_pred.cpu().numpy())
        all_pos_alpha_true.append(data.y_pos_alpha.cpu().numpy())
        all_pos_alpha_pred.append(pos_alpha_pred.cpu().numpy())
    
    # Concatenate all batches
    pos_scores = np.concatenate(all_pos_scores)
    neg_scores = np.concatenate(all_neg_scores)
    rsum_true = np.concatenate(all_pos_rsum_true)
    rsum_pred = np.concatenate(all_pos_rsum_pred)
    alpha_true = np.concatenate(all_pos_alpha_true)
    alpha_pred = np.concatenate(all_pos_alpha_pred)
    
    # Classification metrics
    scores = np.concatenate([pos_scores, neg_scores])
    labels = np.concatenate([np.ones_like(pos_scores), 
                             np.zeros_like(neg_scores)])
    
    auc = roc_auc_score(labels, scores)
    ap = average_precision_score(labels, scores)
    
    pred_binary = (scores >= 0.5).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, pred_binary, average='binary'
    )
    
    # Regression metrics
    mae_rsum = np.mean(np.abs(rsum_pred - rsum_true))
    rmse_rsum = np.sqrt(np.mean((rsum_pred - rsum_true)**2))
    r2_rsum = r2_score(rsum_true, rsum_pred)
    
    mae_alpha = np.mean(np.abs(alpha_pred - alpha_true))
    rmse_alpha = np.sqrt(np.mean((alpha_pred - alpha_true)**2))
    r2_alpha = r2_score(alpha_true, alpha_pred)
    
    # Composite score
    composite = composite_score(auc, mae_rsum, mae_alpha)
    
    return {
        "auc": auc,
        "ap": ap,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mae_rsum": mae_rsum,
        "rmse_rsum": rmse_rsum,
        "r2_rsum": r2_rsum,
        "mae_alpha": mae_alpha,
        "rmse_alpha": rmse_alpha,
        "r2_alpha": r2_alpha,
        "composite_score": composite
    }
```

**Usage**:
```python
metrics = evaluate_comprehensive(model, test_loader, device, CFG)

print("="*60)
print("COMPREHENSIVE EVALUATION RESULTS")
print("="*60)
print("\nClassification Metrics:")
print(f"  AUC-ROC:           {metrics['auc']:.4f}")
print(f"  Average Precision: {metrics['ap']:.4f}")
print(f"  Precision:         {metrics['precision']:.4f}")
print(f"  Recall:            {metrics['recall']:.4f}")
print(f"  F1 Score:          {metrics['f1']:.4f}")

print("\nSum-Rate Regression:")
print(f"  MAE:               {metrics['mae_rsum']:.4f} bits/Hz")
print(f"  RMSE:              {metrics['rmse_rsum']:.4f} bits/Hz")
print(f"  R²:                {metrics['r2_rsum']:.4f}")

print("\nPower Split Regression:")
print(f"  MAE:               {metrics['mae_alpha']:.4f}")
print(f"  RMSE:              {metrics['rmse_alpha']:.4f}")
print(f"  R²:                {metrics['r2_alpha']:.4f}")

print("\nComposite Score:     {:.4f}".format(metrics['composite_score']))
print("="*60)
```

**Example Output**:
```
============================================================
COMPREHENSIVE EVALUATION RESULTS
============================================================

Classification Metrics:
  AUC-ROC:           0.9247
  Average Precision: 0.9156
  Precision:         0.8734
  Recall:            0.9012
  F1 Score:          0.8871

Sum-Rate Regression:
  MAE:               0.0312 bits/Hz
  RMSE:              0.0425 bits/Hz
  R²:                0.8234

Power Split Regression:
  MAE:               0.0089
  RMSE:              0.0123
  R²:                0.9012

Composite Score:     0.9422
============================================================
```

---

## 📊 Visualization

### Learning Curves

```python
import matplotlib.pyplot as plt

def plot_learning_curves(history):
    """
    Plot training and validation metrics over epochs.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Loss
    axes[0, 0].plot(history['train_loss'], label='Train')
    axes[0, 0].plot(history['val_loss'], label='Validation')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].set_title('Training and Validation Loss')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # AUC
    axes[0, 1].plot(history['val_auc'])
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('AUC-ROC')
    axes[0, 1].set_title('Validation AUC-ROC')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Sum-Rate MAE
    axes[1, 0].plot(history['val_mae_rsum'])
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('MAE (bits/Hz)')
    axes[1, 0].set_title('Validation Sum-Rate MAE')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Alpha MAE
    axes[1, 1].plot(history['val_mae_alpha'])
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('MAE')
    axes[1, 1].set_title('Validation Power Split MAE')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('learning_curves.png', dpi=150)
    print("Saved learning_curves.png")
```

---

### Prediction Scatter Plots

```python
def plot_predictions(y_true, y_pred, metric_name):
    """
    Scatter plot of true vs. predicted values.
    """
    plt.figure(figsize=(8, 8))
    plt.scatter(y_true, y_pred, alpha=0.5, s=10)
    
    # Perfect prediction line
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], 
             'r--', label='Perfect Prediction')
    
    plt.xlabel(f'True {metric_name}')
    plt.ylabel(f'Predicted {metric_name}')
    plt.title(f'{metric_name} Prediction Scatter Plot')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f'{metric_name}_scatter.png', dpi=150)
    print(f"Saved {metric_name}_scatter.png")

# Usage
plot_predictions(rsum_true, rsum_pred, "Sum-Rate")
plot_predictions(alpha_true, alpha_pred, "Alpha")
```

---

## ✅ Best Practices

### 1. Use Multiple Metrics
- Don't rely on single metric
- AUC + MAE gives complete picture

### 2. Track Over Time
- Monitor training curves
- Detect overfitting early

### 3. Test Set is Sacred
- Only evaluate on test set once at the end
- Never tune hyperparameters on test set

### 4. Report Confidence Intervals
```python
from scipy import stats

# Bootstrap confidence intervals
n_bootstrap = 1000
aucs = []

for _ in range(n_bootstrap):
    idx = np.random.choice(len(scores), len(scores), replace=True)
    auc_boot = roc_auc_score(labels[idx], scores[idx])
    aucs.append(auc_boot)

ci_low, ci_high = np.percentile(aucs, [2.5, 97.5])
print(f"AUC: {auc:.4f} (95% CI: [{ci_low:.4f}, {ci_high:.4f}])")
```

---

**Last Updated**: October 17, 2025  
**Version**: 1.0.0  
**Author**: NOMA-GNN Development Team
