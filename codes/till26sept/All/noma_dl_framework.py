"""
Deep Learning Framework for NOMA User Clustering and Power Allocation

This module implements a deep learning-based approach for joint user clustering
and power allocation in PD-NOMA/OMA systems, building on the traditional
clustering methods in clustering.py.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import networkx as nx
from tqdm import tqdm
import os
import pickle
from sklearn.model_selection import train_test_split
import time

# Check if GPU is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Create directories for models and results
os.makedirs("models", exist_ok=True)
os.makedirs("dl_results", exist_ok=True)

# System parameters (match with clustering.py)
N = 500  # Number of users
radius = 5000  # Cell radius in meters
fc = 3.5e9  # Carrier frequency (3.5 GHz)
c = 3e8  # Speed of light
lambda_c = c / fc  # Wavelength
path_loss_exp = 3.5  # Path loss exponent
shadow_std_db = 8  # Shadow fading standard deviation in dB
noise_power = 1e-9  # Noise power
total_power = 1.0  # Total power budget
sic_threshold_db = 8  # Minimum channel gain difference for SIC in dB
B_total = 20e6  # Total bandwidth in Hz

# ===================== Feature Engineering Functions =====================

def extract_features(h_values, x_coords, y_coords, distances):
    """
    Extract features for each user in the scenario
    
    Args:
        h_values: Channel gains
        x_coords, y_coords: User locations
        distances: Distances from BS
        
    Returns:
        features: Array of features for each user [N, feature_dim]
    """
    N = len(h_values)
    h_db = 10 * np.log10(h_values**2 + 1e-12)
    h_norm = h_values / np.max(h_values)
    
    # Basic features
    features = np.zeros((N, 7))
    for i in range(N):
        features[i, 0] = h_values[i]             # Linear channel gain
        features[i, 1] = h_db[i]                 # Channel gain in dB
        features[i, 2] = h_norm[i]               # Normalized channel gain
        features[i, 3] = x_coords[i]             # X coordinate
        features[i, 4] = y_coords[i]             # Y coordinate
        features[i, 5] = distances[i]            # Distance from BS
        features[i, 6] = distances[i]/radius     # Normalized distance
    
    return features

def create_clustering_matrix(pairs):
    """
    Create binary adjacency matrix from user pairs
    
    Args:
        pairs: List of user pairs (u1, u2)
        
    Returns:
        matrix: Binary adjacency matrix [N, N]
    """
    N = 500  # Total number of users
    matrix = np.zeros((N, N), dtype=np.float32)
    
    for u1, u2 in pairs:
        matrix[u1, u2] = 1
        matrix[u2, u1] = 1
        
    return matrix

def extract_power_allocation(pairs, h_values):
    """
    Extract power allocation coefficients from pairs and channel gains
    
    Args:
        pairs: List of user pairs (u1, u2)
        h_values: Channel gains
        
    Returns:
        power_alloc: Power allocation matrix [N, N, 2]
                    [i,j,0] = power for user i in pair (i,j)
                    [i,j,1] = power for user j in pair (i,j)
    """
    N = 500  # Total number of users
    power_alloc = np.zeros((N, N, 2), dtype=np.float32)
    
    for u1, u2 in pairs:
        h1, h2 = h_values[u1], h_values[u2]
        
        # Ensure h1 is the weaker channel
        if h1 > h2:
            h1, h2 = h2, h1
            u1, u2 = u2, u1
            
        # Power allocation based on channel gain ratio
        P1 = total_power * h2 / (h1 + h2)
        P2 = total_power * h1 / (h1 + h2)
        
        power_alloc[u1, u2, 0] = P1
        power_alloc[u1, u2, 1] = P2
        power_alloc[u2, u1, 0] = P2
        power_alloc[u2, u1, 1] = P1
        
    return power_alloc

# ===================== Data Generation Functions =====================

def generate_channel_scenario():
    """Generate a single channel scenario with user placement and channel gains"""
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
    
    return h_values, x_coords, y_coords, r, theta

def run_blossom_clustering(h_values):
    """Run Blossom clustering algorithm to get optimal pairs"""
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
                # Calculate rate for this pair
                P1 = total_power * h2 / (h1 + h2)
                P2 = total_power * h1 / (h1 + h2)
                
                # Rate calculations with SIC
                R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))  # Weaker user
                R2 = np.log2(1 + (P2 * h2) / noise_power)  # Stronger user
                R_sum = R1 + R2
                
                G.add_edge(i, j, weight=R_sum)
    
    # Find max-weight matching using blossom algorithm
    matches = list(nx.max_weight_matching(G, maxcardinality=True))
    
    return matches

def prepare_training_data(num_scenarios=1000):
    """Generate multiple scenarios for training data"""
    features_list = []
    clustering_labels = []
    power_labels = []
    
    print(f"Generating {num_scenarios} training scenarios...")
    for i in tqdm(range(num_scenarios)):
        # Generate new channel scenario
        h_values, x_coords, y_coords, r, _ = generate_channel_scenario()
        
        # Extract features
        features = extract_features(h_values, x_coords, y_coords, r)
        features_list.append(features)
        
        # Run Blossom algorithm to get optimal pairing
        pairs = run_blossom_clustering(h_values)
        
        # Create clustering matrix
        cluster_matrix = create_clustering_matrix(pairs)
        clustering_labels.append(cluster_matrix)
        
        # Extract power allocation
        power_matrix = extract_power_allocation(pairs, h_values)
        power_labels.append(power_matrix)
    
    # Save the generated data
    os.makedirs("data", exist_ok=True)
    with open("data/training_data.pkl", "wb") as f:
        pickle.dump({
            "features": features_list,
            "clustering": clustering_labels,
            "power": power_labels
        }, f)
    
    print("Training data saved to data/training_data.pkl")
    
    return features_list, clustering_labels, power_labels

# ===================== Dataset and DataLoader =====================

class NOMADataset(Dataset):
    """Dataset for NOMA user clustering and power allocation"""
    
    def __init__(self, features, clustering_labels, power_labels):
        self.features = features
        self.clustering_labels = clustering_labels
        self.power_labels = power_labels
        
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        # Convert to PyTorch tensors
        x = torch.tensor(self.features[idx], dtype=torch.float32)
        y_cluster = torch.tensor(self.clustering_labels[idx], dtype=torch.float32)
        y_power = torch.tensor(self.power_labels[idx], dtype=torch.float32)
        
        return x, y_cluster, y_power

# ===================== GNN-based Model =====================

class NOMAGraphDataset(Dataset):
    """Graph dataset for NOMA with GNN models"""
    
    def __init__(self, features, clustering_labels, power_labels):
        self.features = features
        self.clustering_labels = clustering_labels
        self.power_labels = power_labels
        
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        # Get data for this scenario
        node_features = self.features[idx]
        cluster_matrix = self.clustering_labels[idx]
        power_matrix = self.power_labels[idx]
        
        # Create a fully connected graph
        N = len(node_features)
        edge_index = []
        edge_attr = []
        
        for i in range(N):
            for j in range(i+1, N):
                # Add edge (i,j)
                edge_index.append([i, j])
                
                # Edge features: channel gain difference in dB
                h_i = node_features[i, 0]  # Channel gain for user i
                h_j = node_features[j, 0]  # Channel gain for user j
                db_diff = abs(10 * np.log10((h_j + 1e-10) / (h_i + 1e-10)))
                
                edge_attr.append([db_diff, cluster_matrix[i, j]])
        
        # Convert to PyTorch tensors
        x = torch.tensor(node_features, dtype=torch.float32)
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_attr, dtype=torch.float32)
        
        # Labels
        y_cluster = torch.tensor(cluster_matrix, dtype=torch.float32)
        y_power = torch.tensor(power_matrix, dtype=torch.float32)
        
        return x, edge_index, edge_attr, y_cluster, y_power

# This is just a placeholder for GNN model
# For actual implementation, you'll need PyTorch Geometric installed
class NOMAGraphModel(nn.Module):
    """Graph Neural Network for NOMA clustering and power allocation"""
    
    def __init__(self, input_dim, hidden_dim=64):
        super(NOMAGraphModel, self).__init__()
        
        self.node_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        self.edge_encoder = nn.Sequential(
            nn.Linear(2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Graph convolution layers would go here
        # This is just a placeholder
        
        self.clustering_decoder = nn.Sequential(
            nn.Linear(hidden_dim*2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
        
        self.power_decoder = nn.Sequential(
            nn.Linear(hidden_dim*2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 2),
            nn.Sigmoid()
        )
    
    def forward(self, x, edge_index, edge_attr):
        # This is a simplified placeholder forward pass
        # In a real GNN implementation, you'd use proper graph convolutions
        
        # Encode node features
        node_features = self.node_encoder(x)
        
        # Encode edge features
        edge_features = self.edge_encoder(edge_attr)
        
        # Placeholder for graph convolutions
        # ...
        
        # For the placeholder model, we'll just use the encoded features directly
        src, dst = edge_index
        src_features = node_features[src]
        dst_features = node_features[dst]
        
        # Concatenate source and destination node features
        pair_features = torch.cat([src_features, dst_features], dim=1)
        
        # Predict clustering decisions
        clustering_pred = self.clustering_decoder(pair_features)
        
        # Predict power allocation
        power_pred = self.power_decoder(pair_features)
        
        return clustering_pred, power_pred

# ===================== MLP-based Model =====================

class NOMAClusteringMLP(nn.Module):
    """Simple MLP for predicting clustering and power allocation"""
    
    def __init__(self, input_dim, hidden_dim=256):
        super(NOMAClusteringMLP, self).__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        self.clustering_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, N*N),
            nn.Sigmoid()
        )
        
        self.power_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, N*N*2),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        batch_size = x.size(0)
        
        # Flatten the input
        x_flat = x.view(batch_size, -1)
        
        # Encode features
        encoded = self.encoder(x_flat)
        
        # Predict clustering matrix (reshape to batch_size, N, N)
        clustering = self.clustering_head(encoded)
        clustering = clustering.view(batch_size, N, N)
        
        # Make clustering matrix symmetric
        clustering = (clustering + clustering.transpose(1, 2)) / 2
        
        # Predict power allocation (reshape to batch_size, N, N, 2)
        power = self.power_head(encoded)
        power = power.view(batch_size, N, N, 2)
        
        return clustering, power

# ===================== Loss Functions =====================

def calculate_throughput(clustering_matrix, power_allocation, h_values):
    """
    Calculate throughput based on clustering decisions and power allocation
    
    Args:
        clustering_matrix: Binary matrix indicating which users are paired [N, N]
        power_allocation: Power allocation coefficients [N, N, 2]
        h_values: Channel gains [N]
        
    Returns:
        throughput: System throughput in Mbps
    """
    N = len(h_values)
    used = np.zeros(N, dtype=bool)
    pairs = []
    
    # Extract pairs from clustering matrix
    for i in range(N):
        for j in range(i+1, N):
            if clustering_matrix[i, j] > 0.5:  # Threshold
                pairs.append((i, j))
                used[i] = used[j] = True
    
    # Count NOMA pairs and OMA users
    num_pairs = len(pairs)
    num_oma = N - 2 * num_pairs
    
    # Bandwidth allocation
    B_pair = B_total / (num_pairs + num_oma)
    total_throughput = 0
    
    # Calculate throughput for NOMA pairs
    for u1, u2 in pairs:
        h1, h2 = h_values[u1], h_values[u2]
        
        # Ensure h1 is the weaker channel
        if h1 > h2:
            h1, h2 = h2, h1
            u1, u2 = u2, u1
        
        # Get power allocation from the predicted values
        P1 = power_allocation[u1, u2, 0] * total_power
        P2 = power_allocation[u1, u2, 1] * total_power
        
        # Ensure power sum to total_power
        P_sum = P1 + P2
        if P_sum > 0:
            P1 = P1 / P_sum * total_power
            P2 = P2 / P_sum * total_power
        else:
            P1 = P2 = total_power / 2
        
        # Rate calculations with SIC
        R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))
        R2 = np.log2(1 + (P2 * h2) / noise_power)
        R_sum = R1 + R2
        
        throughput = R_sum * B_pair / 1e6
        total_throughput += throughput
    
    # OMA fallback for unpaired users
    for u in range(N):
        if not used[u]:
            h = h_values[u]
            R1_oma = np.log2(1 + (total_power * h) / noise_power)
            throughput = R1_oma * B_pair / 1e6
            total_throughput += throughput
    
    return total_throughput

def noma_loss(clustering_pred, power_pred, clustering_true, power_true, h_values):
    """
    Custom loss function that combines:
    1. Binary cross-entropy for clustering decisions
    2. MSE for power allocation
    3. Negative throughput as a reward signal
    """
    # BCE for clustering
    clustering_loss = F.binary_cross_entropy(clustering_pred, clustering_true)
    
    # MSE for power allocation (only for actually paired users)
    paired_mask = (clustering_true > 0.5)
    if torch.any(paired_mask):
        power_loss = F.mse_loss(
            power_pred[paired_mask], 
            power_true[paired_mask]
        )
    else:
        power_loss = torch.tensor(0.0, device=clustering_pred.device)
    
    # Throughput calculation and loss
    # This would need to be implemented for batched predictions
    # For now, we'll use a placeholder
    throughput_loss = torch.tensor(0.0, device=clustering_pred.device)
    
    # Combine losses with weights
    total_loss = clustering_loss + 0.5 * power_loss + 0.3 * throughput_loss
    
    return total_loss, {
        'clustering_loss': clustering_loss.item(),
        'power_loss': power_loss.item(),
        'throughput_loss': throughput_loss.item(),
        'total_loss': total_loss.item()
    }

# ===================== Training Functions =====================

def train_noma_model(model, train_loader, val_loader, epochs=100):
    """Train the NOMA clustering and power allocation model"""
    
    # Move model to device
    model = model.to(device)
    
    # Optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, factor=0.5, patience=5, verbose=True
    )
    
    # Training history
    history = {
        'train_loss': [],
        'val_loss': [],
        'val_throughput': []
    }
    
    # Best model tracking
    best_val_loss = float('inf')
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_losses = []
        
        for batch_features, batch_cluster, batch_power in train_loader:
            # Move data to device
            batch_features = batch_features.to(device)
            batch_cluster = batch_cluster.to(device)
            batch_power = batch_power.to(device)
            
            # Zero gradients
            optimizer.zero_grad()
            
            # Forward pass
            cluster_pred, power_pred = model(batch_features)
            
            # Compute loss
            loss, metrics = noma_loss(
                cluster_pred, power_pred,
                batch_cluster, batch_power,
                batch_features[:, :, 0]  # h_values are the first feature
            )
            
            # Backward pass
            loss.backward()
            
            # Update weights
            optimizer.step()
            
            # Record loss
            train_losses.append(metrics)
        
        # Calculate average training loss
        avg_train_loss = np.mean([x['total_loss'] for x in train_losses])
        history['train_loss'].append(avg_train_loss)
        
        # Validation
        model.eval()
        val_losses = []
        
        with torch.no_grad():
            for batch_features, batch_cluster, batch_power in val_loader:
                # Move data to device
                batch_features = batch_features.to(device)
                batch_cluster = batch_cluster.to(device)
                batch_power = batch_power.to(device)
                
                # Forward pass
                cluster_pred, power_pred = model(batch_features)
                
                # Compute loss
                loss, metrics = noma_loss(
                    cluster_pred, power_pred,
                    batch_cluster, batch_power,
                    batch_features[:, :, 0]  # h_values are the first feature
                )
                
                # Record loss
                val_losses.append(metrics)
        
        # Calculate average validation loss
        avg_val_loss = np.mean([x['total_loss'] for x in val_losses])
        history['val_loss'].append(avg_val_loss)
        
        # Print epoch results
        print(f"Epoch {epoch+1}/{epochs}:")
        print(f"  Train Loss: {avg_train_loss:.4f}")
        print(f"  Val Loss: {avg_val_loss:.4f}")
        
        # Save best model
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), "models/best_noma_model.pth")
            print("  Saved new best model!")
        
        # Update learning rate
        scheduler.step(avg_val_loss)
    
    # Save training history
    with open("models/training_history.pkl", "wb") as f:
        pickle.dump(history, f)
    
    # Save final model
    torch.save(model.state_dict(), "models/final_noma_model.pth")
    
    # Plot training history
    plt.figure(figsize=(10, 6))
    plt.plot(history['train_loss'], label='Training Loss')
    plt.plot(history['val_loss'], label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.savefig("dl_results/training_history.png")
    
    return history

# ===================== Evaluation Functions =====================

def evaluate_model(model, test_loader):
    """Evaluate the model on test data"""
    
    model = model.to(device)
    model.eval()
    
    test_losses = []
    test_throughputs = []
    
    with torch.no_grad():
        for batch_features, batch_cluster, batch_power in test_loader:
            # Move data to device
            batch_features = batch_features.to(device)
            batch_cluster = batch_cluster.to(device)
            batch_power = batch_power.to(device)
            
            # Forward pass
            cluster_pred, power_pred = model(batch_features)
            
            # Compute loss
            loss, metrics = noma_loss(
                cluster_pred, power_pred,
                batch_cluster, batch_power,
                batch_features[:, :, 0]  # h_values are the first feature
            )
            
            # Record metrics
            test_losses.append(metrics)
            
            # Calculate throughput for each sample in batch
            for i in range(len(batch_features)):
                h_values = batch_features[i, :, 0].cpu().numpy()
                cluster = cluster_pred[i].cpu().numpy()
                power = power_pred[i].cpu().numpy()
                
                throughput = calculate_throughput(cluster, power, h_values)
                test_throughputs.append(throughput)
    
    # Calculate average metrics
    avg_test_loss = np.mean([x['total_loss'] for x in test_losses])
    avg_throughput = np.mean(test_throughputs)
    
    print(f"Test Results:")
    print(f"  Avg Loss: {avg_test_loss:.4f}")
    print(f"  Avg Throughput: {avg_throughput:.2f} Mbps")
    
    return avg_test_loss, avg_throughput, test_throughputs

def compare_with_traditional(test_data):
    """Compare DL model with traditional clustering methods"""
    
    # Results dict
    results = {
        'Method': [],
        'Throughput (Mbps)': [],
        'NOMA Pairs': [],
        'OMA Users': [],
        'Runtime (ms)': []
    }
    
    # Function to evaluate a clustering method
    def evaluate_method(name, clustering_fn):
        throughputs = []
        pairs_counts = []
        runtimes = []
        
        for i in range(len(test_data['features'])):
            h_values = test_data['features'][i][:, 0]  # First feature is h_values
            
            # Measure runtime
            start_time = time.time()
            pairs = clustering_fn(h_values)
            runtime = (time.time() - start_time) * 1000  # Convert to ms
            
            # Count pairs
            num_pairs = len(pairs)
            num_oma = N - 2 * num_pairs
            
            # Create clustering matrix and power allocation
            cluster_matrix = create_clustering_matrix(pairs)
            power_matrix = extract_power_allocation(pairs, h_values)
            
            # Calculate throughput
            throughput = calculate_throughput(cluster_matrix, power_matrix, h_values)
            
            throughputs.append(throughput)
            pairs_counts.append(num_pairs)
            runtimes.append(runtime)
        
        # Record results
        results['Method'].append(name)
        results['Throughput (Mbps)'].append(np.mean(throughputs))
        results['NOMA Pairs'].append(np.mean(pairs_counts))
        results['OMA Users'].append(N - 2 * np.mean(pairs_counts))
        results['Runtime (ms)'].append(np.mean(runtimes))
    
    # Evaluate traditional methods
    
    # 1. Static Pairing
    def static_clustering(h_values):
        sorted_indices = np.argsort(h_values)
        pairs = []
        used = np.zeros(N, dtype=bool)
        
        for i in range(N//2):
            u1, u2 = sorted_indices[i], sorted_indices[N-1-i]
            h1, h2 = h_values[u1], h_values[u2]
            
            if 10*np.log10(h2/h1) >= sic_threshold_db:
                pairs.append((u1, u2))
                used[u1] = used[u2] = True
        
        return pairs
    
    # 2. Balanced Pairing
    def balanced_clustering(h_values):
        sorted_indices = np.argsort(h_values)
        pairs = []
        used = np.zeros(N, dtype=bool)
        
        for i in range(N//2):
            u1, u2 = sorted_indices[i], sorted_indices[i + N//2]
            h1, h2 = h_values[u1], h_values[u2]
            
            delta_db = 10 * np.log10(h2/h1)
            if delta_db >= sic_threshold_db:
                pairs.append((u1, u2))
                used[u1] = used[u2] = True
        
        return pairs
    
    # 3. Blossom Pairing
    def blossom_clustering(h_values):
        return run_blossom_clustering(h_values)
    
    # 4. Deep Learning model
    def dl_clustering(h_values):
        # Load model
        model = NOMAClusteringMLP(7 * N)  # Adjust input dim based on your features
        model.load_state_dict(torch.load("models/best_noma_model.pth"))
        model = model.to(device)
        model.eval()
        
        # Prepare input
        x_coords = np.zeros(N)
        y_coords = np.zeros(N)
        r = np.zeros(N)
        features = extract_features(h_values, x_coords, y_coords, r)
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(device)
        
        # Forward pass
        with torch.no_grad():
            cluster_pred, _ = model(features_tensor)
        
        # Extract pairs from predicted clustering matrix
        cluster_matrix = cluster_pred[0].cpu().numpy()
        pairs = []
        used = np.zeros(N, dtype=bool)
        
        for i in range(N):
            for j in range(i+1, N):
                if cluster_matrix[i, j] > 0.5 and not used[i] and not used[j]:
                    pairs.append((i, j))
                    used[i] = used[j] = True
        
        return pairs
    
    # Evaluate each method
    evaluate_method("Static", static_clustering)
    evaluate_method("Balanced", balanced_clustering)
    evaluate_method("Blossom", blossom_clustering)
    
    try:
        evaluate_method("Deep Learning", dl_clustering)
    except:
        print("DL model evaluation failed - model may not be trained yet")
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    print("\nComparison of Methods:")
    print(results_df)
    
    # Save results
    results_df.to_csv("dl_results/method_comparison.csv", index=False)
    
    # Plot comparison
    plt.figure(figsize=(12, 6))
    plt.bar(results_df['Method'], results_df['Throughput (Mbps)'])
    plt.ylabel('Throughput (Mbps)')
    plt.title('Throughput Comparison Across Methods')
    plt.savefig("dl_results/throughput_comparison.png")
    
    plt.figure(figsize=(12, 6))
    plt.bar(results_df['Method'], results_df['Runtime (ms)'])
    plt.ylabel('Runtime (ms)')
    plt.title('Runtime Comparison Across Methods')
    plt.savefig("dl_results/runtime_comparison.png")
    
    return results_df

# ===================== Main Function =====================

def main():
    """Main function to run the training and evaluation"""
    
    # Check if data exists, otherwise generate it
    if not os.path.exists("data/training_data.pkl"):
        print("Generating training data...")
        features, clustering, power = prepare_training_data(num_scenarios=1000)
    else:
        print("Loading existing training data...")
        with open("data/training_data.pkl", "rb") as f:
            data = pickle.load(f)
            features = data['features']
            clustering = data['clustering']
            power = data['power']
    
    # Split data into train, validation, and test sets
    X_train, X_test, y_cluster_train, y_cluster_test, y_power_train, y_power_test = train_test_split(
        features, clustering, power, test_size=0.2, random_state=42
    )
    
    X_train, X_val, y_cluster_train, y_cluster_val, y_power_train, y_power_val = train_test_split(
        X_train, y_cluster_train, y_power_train, test_size=0.25, random_state=42
    )
    
    # Create datasets
    train_dataset = NOMADataset(X_train, y_cluster_train, y_power_train)
    val_dataset = NOMADataset(X_val, y_cluster_val, y_power_val)
    test_dataset = NOMADataset(X_test, y_cluster_test, y_power_test)
    
    # Create dataloaders
    batch_size = 16
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    test_loader = DataLoader(test_dataset, batch_size=batch_size)
    
    # Create model
    input_dim = 7 * N  # Adjust based on your feature extraction
    model = NOMAClusteringMLP(input_dim)
    
    # Train model
    print("\nTraining model...")
    history = train_noma_model(model, train_loader, val_loader, epochs=50)
    
    # Evaluate model
    print("\nEvaluating model...")
    test_loss, test_throughput, _ = evaluate_model(model, test_loader)
    
    # Compare with traditional methods
    print("\nComparing with traditional methods...")
    test_data = {
        'features': X_test
    }
    comparison = compare_with_traditional(test_data)
    
    return comparison

if __name__ == "__main__":
    main()
