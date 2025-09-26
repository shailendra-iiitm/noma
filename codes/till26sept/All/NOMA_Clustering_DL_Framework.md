# NOMA/OMA User Clustering and Deep Learning Framework

This document provides a detailed explanation of the [`clustering.py`](clustering.py) implementation and outlines how to proceed with implementing a deep learning framework for joint user clustering and dynamic power allocation in hybrid PD-NOMA/OMA systems.

## 1. Current Implementation Overview

The current script implements three different user clustering methods for Power-Domain Non-Orthogonal Multiple Access (PD-NOMA) in a wireless communication system:

1. **Static Pairing**: Pairs users with highest and lowest channel gains
2. **Balanced Pairing**: Pairs users by dividing them into two equal groups by channel gain
3. **Blossom Pairing**: Uses maximum weight matching algorithm to find optimal pairs

### 1.1 System Model

- **Cell Model**: Single-cell system with N=500 users uniformly distributed in a circular area
- **Channel Model**: Combines path loss, shadowing, and small-scale fading
  - Path loss based on distance with exponent 3.5
  - Log-normal shadowing with 8 dB standard deviation
  - Rayleigh fading for small-scale effects
- **System Parameters**:
  - Carrier frequency: 3.5 GHz
  - Total bandwidth: 20 MHz
  - SIC (Successive Interference Cancellation) threshold: 8 dB

### 1.2 User Placement and Channel Generation

The script generates user locations and channel gains:
- Users placed with uniform distribution in a circular cell (radius 5000m)
- Path loss calculated based on 3GPP model
- Complete channel gain combines path loss, shadowing, and small-scale fading

```python
# User Placement - uniform distribution within a circular cell
r = np.sqrt(np.random.uniform(0, radius**2, N))
theta = np.random.uniform(0, 2*np.pi, N)
x_coords = r * np.cos(theta)
y_coords = r * np.sin(theta)

# Path Loss & Shadowing calculation
pl_1m_db = 20 * np.log10(4 * np.pi / lambda_c)  # Path loss at 1m reference distance
shadowing = np.random.normal(0, shadow_std_db, N)  # Log-normal shadowing
pl_db = pl_1m_db + 10 * path_loss_exp * np.log10(r) + shadowing  # Total path loss in dB
pl_linear = 10**(-pl_db/10)  # Convert path loss from dB to linear scale

# Small-Scale Fading (Rayleigh)
fading = np.random.rayleigh(scale=1.0, size=N)

# Total Channel Gain
h_values = fading * np.sqrt(pl_linear)  # Combine large and small-scale fading
```

### 1.3 Rate Calculation for NOMA Pairs

A key function calculates the achievable rates for NOMA user pairs:

```python
def calc_pair_rate(h1, h2):
    """
    Calculate achievable rates for a NOMA pair
    
    Args:
        h1: Channel gain of weaker user
        h2: Channel gain of stronger user
        
    Returns:
        P1, P2: Power allocation
        R1, R2: Achievable rates
        R_sum: Sum rate
    """
    # Power allocation based on channel gain ratio
    P1 = total_power * h2 / (h1 + h2)
    P2 = total_power * h1 / (h1 + h2)
    
    # Rate calculations with SIC
    R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))  # Weaker user experiences interference
    R2 = np.log2(1 + (P2 * h2) / noise_power)  # Stronger user decodes weaker user's signal first
    
    return P1, P2, R1, R2, R1 + R2
```

### 1.4 Clustering Methods

#### 1.4.1 Static Pairing
- Pairs users with the worst and best channel gains
- Ensures each pair satisfies the SIC threshold
- Unpaired users are allocated OMA resources

```python
# Pair users with the best and worst channel gains
for i in range(N//2):
    u1, u2 = sorted_indices[i], sorted_indices[N-1-i]  # Pair worst with best
    h1, h2 = h_values[u1], h_values[u2]
    
    # Check if SIC threshold is satisfied
    if 10*np.log10(h2/h1) >= sic_threshold_db:
        P1, P2, R1, R2, R_sum = calc_pair_rate(h1, h2)
        static_pairs.append((u1, u2))
        total_rate_static += R_sum
        used_static[[u1, u2]] = True
```

#### 1.4.2 Balanced Pairing
- Divides users into two equal groups based on channel gain
- Pairs users from each group
- Ensures each pair satisfies the SIC threshold
- Unpaired users are allocated OMA resources

```python
# Divide users into two equal groups based on channel gain
for i in range(N // 2):
    u1, u2 = sorted_indices[i], sorted_indices[i + N // 2]
    h1, h2 = h_values[u1], h_values[u2]
    
    # Check if SIC threshold is satisfied
    delta_db = 10 * np.log10(h2 / h1)
    if delta_db >= sic_threshold_db:
        P1, P2, R1, R2, R_sum = calc_pair_rate(h1, h2)
        pairs_balanced.append((u1, u2))
        total_rate_balanced += R_sum
        used_balanced[u1] = used_balanced[u2] = True
```

#### 1.4.3 Blossom Pairing (Maximum Weight Matching)
- Creates a graph where nodes are users and edge weights are sum rates
- Only edges between users that satisfy SIC threshold are added
- Uses the Blossom algorithm to find maximum weight matching
- Results in optimal pairing for maximum sum rate
- Unpaired users are allocated OMA resources

```python
# Create graph for max-weight matching
G = nx.Graph()

# Add all possible edges between users that satisfy SIC
for i in range(N):
    for j in range(i + 1, N):
        h1, h2 = h_values[i], h_values[j]
        
        # Ensure h1 is the weaker channel
        if h1 > h2:
            h1, h2 = h2, h1
            
        delta_db = 10 * np.log10(h2 / h1)
        if delta_db >= sic_threshold_db:
            _, _, _, _, R_sum = calc_pair_rate(h1, h2)
            G.add_edge(i, j, weight=R_sum)

# Find max-weight matching using blossom algorithm
matches_blossom = list(nx.max_weight_matching(G, maxcardinality=True))
```

### 1.5 Resource Allocation and Throughput Calculation

For each clustering method:
1. Calculate number of NOMA pairs and OMA users
2. Allocate bandwidth equally among all pairs and individual OMA users
3. Calculate throughput for NOMA pairs using sum rate
4. Calculate throughput for OMA users using standard Shannon capacity

```python
# Bandwidth allocation
B_pair = B_total / (num_pairs + num_oma_users)

# NOMA pair throughput
throughput = R_sum * B_pair / 1e6  # Convert to Mbps

# OMA user throughput
R1_oma = np.log2(1 + (total_power * h) / noise_power)
throughput = R1_oma * B_pair / 1e6
```

### 1.6 Performance Metrics

The script calculates various performance metrics:
- Number of NOMA pairs formed
- Number of OMA users
- Total system rate (bits/s/Hz)
- Average pair rate (bits/s/Hz)
- Average user rate (bits/s/Hz)
- Total throughput (Mbps)
- Performance improvement compared to static pairing (%)

### 1.7 Visualization

Multiple visualizations are generated:
- User distribution with channel gain
- NOMA pairing results for each method (Static, Balanced, Blossom)
- Comparative performance bar charts

## 2. Deep Learning Framework Implementation

Based on your current clustering implementation, here's how to proceed with a deep learning-based framework:

### 2.1 Deep Learning System Design

#### 2.1.1 Overall Architecture

```
[Channel Data] → [Feature Engineering] → [Deep Learning Model] → [User Clustering + Power Allocation]
```

#### 2.1.2 Input Features

For each user, consider including:
- Channel gain (h_values)
- Location information (x, y coordinates)
- Distance from BS
- Normalized channel gain
- Channel gain in dB

#### 2.1.3 Output Format

Two main components:
1. **Clustering Decision**: Binary matrix or adjacency list indicating which users are paired
2. **Power Allocation**: Power coefficients for each paired user

### 2.2 Model Selection

Consider these neural network architectures:

1. **Graph Neural Networks (GNN)**
   - Well-suited for user pairing problems
   - Can directly model user-to-user relationships
   - Example frameworks: PyTorch Geometric, DGL

2. **Transformer-based models**
   - Can capture complex relationships between all users
   - Self-attention mechanism helps identify optimal pairs
   - Provides flexibility for varying numbers of users

3. **Custom CNN/MLP Hybrid**
   - CNN layers to extract spatial features from user distribution
   - MLP layers to predict clustering and power allocation

### 2.3 Implementation Steps

#### 2.3.1 Data Preparation

```python
def prepare_training_data(num_scenarios=1000):
    """Generate multiple scenarios for training data"""
    features = []
    clustering_labels = []
    power_labels = []
    
    for i in range(num_scenarios):
        # Generate new user locations and channel gains
        # Use your existing channel generation code
        
        # For labels, run your Blossom algorithm to get optimal pairing
        # This serves as "ground truth" for supervised learning
        
        # Extract features for each user
        scenario_features = extract_features(h_values, x_coords, y_coords, r)
        features.append(scenario_features)
        
        # Extract clustering decisions from Blossom
        clustering_decision = create_clustering_matrix(pairs_blossom)
        clustering_labels.append(clustering_decision)
        
        # Extract power allocation decisions
        power_allocation = extract_power_allocation(pairs_blossom, h_values)
        power_labels.append(power_allocation)
    
    return features, clustering_labels, power_labels
```

#### 2.3.2 Model Definition (PyTorch Example for GNN)

```python
import torch
import torch.nn as nn
import torch_geometric as pyg

class NOMAClusteringGNN(nn.Module):
    def __init__(self, feature_dim):
        super(NOMAClusteringGNN, self).__init__()
        
        # GNN layers for user relationship modeling
        self.conv1 = pyg.nn.GCNConv(feature_dim, 64)
        self.conv2 = pyg.nn.GCNConv(64, 128)
        self.conv3 = pyg.nn.GCNConv(128, 64)
        
        # MLP for clustering decisions
        self.clustering_mlp = nn.Sequential(
            nn.Linear(64*2, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 2)  # Binary classification: to pair or not to pair
        )
        
        # MLP for power allocation
        self.power_mlp = nn.Sequential(
            nn.Linear(64*2, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 2)  # Power allocation coefficients for each user in pair
        )
    
    def forward(self, x, edge_index):
        # Node feature transformation
        x = torch.relu(self.conv1(x, edge_index))
        x = torch.relu(self.conv2(x, edge_index))
        x = self.conv3(x, edge_index)
        
        # For each potential pair, predict clustering decision and power allocation
        src, dst = edge_index
        pair_features = torch.cat([x[src], x[dst]], dim=1)
        
        # Clustering decision (0 = don't pair, 1 = pair)
        clustering_logits = self.clustering_mlp(pair_features)
        
        # Power allocation (2 values per pair)
        power_allocation = torch.sigmoid(self.power_mlp(pair_features))
        
        return clustering_logits, power_allocation
```

#### 2.3.3 Loss Function

```python
def noma_loss(clustering_pred, power_pred, clustering_true, power_true, throughput_fn):
    """
    Custom loss function that combines:
    1. Binary cross-entropy for clustering decisions
    2. MSE for power allocation
    3. Negative throughput as a reward signal
    """
    # BCE for clustering
    clustering_loss = nn.BCEWithLogitsLoss()(clustering_pred, clustering_true)
    
    # MSE for power allocation (only for actually paired users)
    paired_mask = clustering_true.bool()
    if torch.any(paired_mask):
        power_loss = nn.MSELoss()(
            power_pred[paired_mask], 
            power_true[paired_mask]
        )
    else:
        power_loss = 0
    
    # Throughput reward (negative because we want to maximize)
    # Apply predicted clustering and power allocation and calculate throughput
    throughput = throughput_fn(clustering_pred, power_pred)
    throughput_loss = -throughput.mean()
    
    # Combine losses with weights
    total_loss = clustering_loss + 0.5 * power_loss + 0.3 * throughput_loss
    
    return total_loss, {
        'clustering_loss': clustering_loss.item(),
        'power_loss': power_loss.item() if torch.is_tensor(power_loss) else power_loss,
        'throughput_loss': throughput_loss.item(),
        'throughput': -throughput_loss.item()
    }
```

#### 2.3.4 Training Loop

```python
def train_noma_model(model, train_loader, val_loader, epochs=100):
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, factor=0.5, patience=5, verbose=True
    )
    
    best_val_throughput = 0
    for epoch in range(epochs):
        # Training
        model.train()
        train_losses = []
        for batch in train_loader:
            optimizer.zero_grad()
            
            # Forward pass
            clustering_pred, power_pred = model(batch.x, batch.edge_index)
            
            # Compute loss
            loss, metrics = noma_loss(
                clustering_pred, power_pred, 
                batch.clustering_y, batch.power_y,
                calculate_throughput
            )
            
            # Backward pass
            loss.backward()
            optimizer.step()
            train_losses.append(metrics)
        
        # Validation
        model.eval()
        val_metrics = []
        with torch.no_grad():
            for batch in val_loader:
                clustering_pred, power_pred = model(batch.x, batch.edge_index)
                _, metrics = noma_loss(
                    clustering_pred, power_pred, 
                    batch.clustering_y, batch.power_y,
                    calculate_throughput
                )
                val_metrics.append(metrics)
        
        # Print metrics
        train_metrics = {k: np.mean([d[k] for d in train_losses]) for k in train_losses[0]}
        val_metrics = {k: np.mean([d[k] for d in val_metrics]) for k in val_metrics[0]}
        
        print(f"Epoch {epoch+1}/{epochs}:")
        print(f"  Train: loss={train_metrics['total_loss']:.4f}, throughput={train_metrics['throughput']:.4f}")
        print(f"  Val: loss={val_metrics['total_loss']:.4f}, throughput={val_metrics['throughput']:.4f}")
        
        # Save best model
        if val_metrics['throughput'] > best_val_throughput:
            best_val_throughput = val_metrics['throughput']
            torch.save(model.state_dict(), "best_noma_model.pth")
        
        # Update learning rate
        scheduler.step(val_metrics['total_loss'])
```

### 2.4 Evaluation and Comparison

Compare DL model performance with your existing clustering methods:

```python
def evaluate_models():
    # Load test data
    test_data = prepare_test_data(100)  # 100 test scenarios
    
    # Evaluate traditional methods
    static_results = evaluate_static_pairing(test_data)
    balanced_results = evaluate_balanced_pairing(test_data)
    blossom_results = evaluate_blossom_pairing(test_data)
    
    # Evaluate DL model
    model = load_trained_model()
    dl_results = evaluate_dl_model(model, test_data)
    
    # Compare results
    plot_comparison([
        ("Static", static_results),
        ("Balanced", balanced_results),
        ("Blossom", blossom_results),
        ("Deep Learning", dl_results)
    ])
```

### 2.5 Advanced Extensions

1. **Reinforcement Learning Approach**
   - Model the problem as a Markov Decision Process
   - Use Deep Q-Networks (DQN) or Policy Gradient methods
   - Reward: System throughput or sum rate

2. **Transfer Learning**
   - Train on small-scale scenarios and transfer to larger networks
   - Fine-tune for different environment parameters

3. **Multi-cell Extension**
   - Expand to multi-cell scenarios with inter-cell interference
   - Add features for neighboring cell information

4. **Dynamic User Scenarios**
   - Add support for users joining/leaving the system
   - Develop online learning methods for real-time adaptation

5. **QoS Constraints**
   - Add minimum rate requirements for users
   - Modify loss function to penalize QoS violations

## 3. Implementation Roadmap

1. **Data Generation & Preparation** (2-3 weeks)
   - Generate large dataset of scenarios
   - Extract relevant features
   - Create ground truth labels using existing Blossom algorithm

2. **Model Development** (3-4 weeks)
   - Implement and test different model architectures
   - Design custom loss functions
   - Implement evaluation metrics

3. **Training & Hyperparameter Tuning** (2-3 weeks)
   - Train models with different hyperparameters
   - Cross-validation to avoid overfitting
   - Learning rate scheduling and regularization

4. **Evaluation & Comparison** (1-2 weeks)
   - Compare with baseline clustering methods
   - Analyze performance across different scenarios
   - Assess computational complexity and runtime efficiency

5. **Documentation & Publication** (2-3 weeks)
   - Document model architecture and training process
   - Prepare visualizations and performance analyses
   - Draft research paper on findings

## 4. Required Libraries and Tools

- **PyTorch**: Core deep learning framework
- **PyTorch Geometric**: For GNN implementations
- **NetworkX**: For graph-based operations
- **NumPy/SciPy**: For numerical operations
- **Pandas**: For data management
- **Matplotlib/Seaborn**: For visualization
- **tqdm**: For progress tracking
- **Scikit-learn**: For metrics and preprocessing

## 5. Conclusion

The current clustering implementation provides a solid foundation for developing a deep learning-based framework for joint user clustering and power allocation in NOMA systems. By leveraging deep learning, you can potentially overcome the limitations of traditional approaches:

1. **Computational Efficiency**: DL models can make predictions quickly after training
2. **Adaptability**: Can adapt to changing channel conditions
3. **Integrated Optimization**: Joint optimization of clustering and power allocation
4. **Feature Learning**: Can discover patterns in channel data that hand-designed algorithms might miss

The main challenge will be designing a model that generalizes well across different scenarios and channel conditions. This will require careful feature selection, architecture design, and training strategies.
