"""
Implementation of GNN-based model for NOMA user clustering and power allocation
This script implements a Graph Neural Network (GNN) model for joint user clustering and power allocation
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch_geometric.nn as gnn
from torch_geometric.data import Data, DataLoader
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pickle
from tqdm import tqdm

# Create directories
os.makedirs("models", exist_ok=True)
os.makedirs("gnn_results", exist_ok=True)

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# System parameters
N = 500  # Number of users
radius = 5000  # Cell radius in meters
noise_power = 1e-9  # Noise power
total_power = 1.0  # Total power budget
sic_threshold_db = 8  # Minimum channel gain difference for SIC in dB
B_total = 20e6  # Total bandwidth in Hz

class GNNEncoder(nn.Module):
    """Graph Neural Network encoder for NOMA user features"""
    
    def __init__(self, input_dim, hidden_dim=64, num_layers=3):
        super(GNNEncoder, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Input projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # GNN layers
        self.convs = nn.ModuleList()
        self.batch_norms = nn.ModuleList()
        
        # First layer
        self.convs.append(gnn.GCNConv(hidden_dim, hidden_dim))
        self.batch_norms.append(nn.BatchNorm1d(hidden_dim))
        
        # Additional layers
        for _ in range(num_layers - 1):
            self.convs.append(gnn.GCNConv(hidden_dim, hidden_dim))
            self.batch_norms.append(nn.BatchNorm1d(hidden_dim))
    
    def forward(self, x, edge_index):
        # Input projection
        x = self.input_proj(x)
        x = F.relu(x)
        
        # GNN layers
        for i in range(self.num_layers):
            x = self.convs[i](x, edge_index)
            x = self.batch_norms[i](x)
            x = F.relu(x)
        
        return x

class EdgePredictor(nn.Module):
    """Edge prediction module for NOMA clustering"""
    
    def __init__(self, node_dim, hidden_dim=64):
        super(EdgePredictor, self).__init__()
        
        self.edge_nn = nn.Sequential(
            nn.Linear(node_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x_i, x_j):
        # Concatenate node features for each edge
        edge_features = torch.cat([x_i, x_j], dim=1)
        
        # Predict edge existence probability
        return self.edge_nn(edge_features)

class PowerAllocator(nn.Module):
    """Power allocation module for NOMA user pairs"""
    
    def __init__(self, node_dim, hidden_dim=64):
        super(PowerAllocator, self).__init__()
        
        self.power_nn = nn.Sequential(
            nn.Linear(node_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 2),
            nn.Softmax(dim=1)  # Ensure power coefficients sum to 1
        )
    
    def forward(self, x_i, x_j):
        # Concatenate node features for each edge
        edge_features = torch.cat([x_i, x_j], dim=1)
        
        # Predict power allocation
        return self.power_nn(edge_features)

class NOMAGNNModel(nn.Module):
    """Complete GNN model for NOMA user clustering and power allocation"""
    
    def __init__(self, input_dim, hidden_dim=64, num_layers=3):
        super(NOMAGNNModel, self).__init__()
        
        self.encoder = GNNEncoder(input_dim, hidden_dim, num_layers)
        self.edge_predictor = EdgePredictor(hidden_dim, hidden_dim)
        self.power_allocator = PowerAllocator(hidden_dim, hidden_dim)
    
    def forward(self, x, edge_index):
        # Encode node features
        node_embeddings = self.encoder(x, edge_index)
        
        # Get source and destination nodes for each edge
        src, dst = edge_index
        
        # Get node embeddings for each edge
        src_embeddings = node_embeddings[src]
        dst_embeddings = node_embeddings[dst]
        
        # Predict edge existence probability
        edge_pred = self.edge_predictor(src_embeddings, dst_embeddings)
        
        # Predict power allocation
        power_pred = self.power_allocator(src_embeddings, dst_embeddings)
        
        return edge_pred, power_pred, node_embeddings

def prepare_graph_data(features, clustering_labels=None, power_labels=None, training=True):
    """
    Prepare graph data for GNN model
    
    Args:
        features: User features [N, feature_dim]
        clustering_labels: Binary adjacency matrix [N, N] (optional for inference)
        power_labels: Power allocation matrix [N, N, 2] (optional for inference)
        training: Whether this is for training (True) or inference (False)
        
    Returns:
        data: PyTorch Geometric Data object
    """
    N = features.shape[0]
    
    # Create a fully connected graph (all potential pairs)
    edge_index = []
    edge_attr = []
    edge_label = []
    power_label = []
    
    for i in range(N):
        for j in range(i+1, N):
            # Add edge (i,j)
            edge_index.append([i, j])
            
            # Edge features: channel gain difference in dB
            h_i = features[i, 0]  # Channel gain for user i
            h_j = features[j, 0]  # Channel gain for user j
            db_diff = abs(10 * np.log10((h_j + 1e-10) / (h_i + 1e-10)))
            
            edge_attr.append([db_diff])
            
            if training and clustering_labels is not None:
                edge_label.append(clustering_labels[i, j])
                
                if power_labels is not None:
                    power_label.append(power_labels[i, j])
    
    # Convert to PyTorch tensors
    x = torch.tensor(features, dtype=torch.float32)
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_attr, dtype=torch.float32)
    
    if training and clustering_labels is not None:
        edge_label = torch.tensor(edge_label, dtype=torch.float32)
        
        if power_labels is not None:
            power_label = torch.tensor(power_label, dtype=torch.float32)
            
            return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, 
                       edge_label=edge_label, power_label=power_label)
        else:
            return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, 
                       edge_label=edge_label)
    else:
        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

def prepare_dataloader(data_path, batch_size=1):
    """
    Prepare DataLoader for GNN training
    
    Args:
        data_path: Path to dataset file
        batch_size: Batch size for training
        
    Returns:
        train_loader, val_loader: DataLoaders for training and validation
    """
    # Load data
    with open(data_path, "rb") as f:
        data = pickle.load(f)
    
    features = data['features']
    clustering = data['clustering']
    power = data['power']
    
    # Split into training and validation sets
    num_samples = len(features)
    num_train = int(0.8 * num_samples)
    
    train_features = features[:num_train]
    train_clustering = clustering[:num_train]
    train_power = power[:num_train]
    
    val_features = features[num_train:]
    val_clustering = clustering[num_train:]
    val_power = power[num_train:]
    
    # Prepare graph data
    train_data_list = []
    val_data_list = []
    
    print("Preparing training data...")
    for i in tqdm(range(len(train_features))):
        data = prepare_graph_data(train_features[i], train_clustering[i], train_power[i])
        train_data_list.append(data)
    
    print("Preparing validation data...")
    for i in tqdm(range(len(val_features))):
        data = prepare_graph_data(val_features[i], val_clustering[i], val_power[i])
        val_data_list.append(data)
    
    # Create DataLoaders
    train_loader = DataLoader(train_data_list, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_data_list, batch_size=batch_size)
    
    return train_loader, val_loader

def edge_prediction_loss(pred, target):
    """Binary cross-entropy loss for edge prediction"""
    return F.binary_cross_entropy(pred.squeeze(), target)

def power_allocation_loss(pred, target):
    """Mean squared error loss for power allocation"""
    return F.mse_loss(pred, target)

def train(model, train_loader, val_loader, num_epochs=50, lr=0.001):
    """
    Train the GNN model
    
    Args:
        model: GNN model
        train_loader: DataLoader for training data
        val_loader: DataLoader for validation data
        num_epochs: Number of training epochs
        lr: Learning rate
        
    Returns:
        history: Training history
    """
    # Move model to device
    model = model.to(device)
    
    # Optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    # Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5, verbose=True
    )
    
    # Training history
    history = {
        'train_loss': [],
        'val_loss': [],
        'val_edge_acc': [],
        'val_edge_f1': []
    }
    
    # Best model tracking
    best_val_loss = float('inf')
    
    for epoch in range(num_epochs):
        # Training
        model.train()
        train_loss = 0
        
        for data in train_loader:
            # Move data to device
            data = data.to(device)
            
            # Zero gradients
            optimizer.zero_grad()
            
            # Forward pass
            edge_pred, power_pred, _ = model(data.x, data.edge_index)
            
            # Compute loss
            edge_loss = edge_prediction_loss(edge_pred, data.edge_label)
            power_loss = power_allocation_loss(power_pred, data.power_label)
            
            # Total loss (with weighting)
            loss = edge_loss + 0.5 * power_loss
            
            # Backward pass
            loss.backward()
            
            # Update weights
            optimizer.step()
            
            # Record loss
            train_loss += loss.item() * data.num_graphs
        
        # Calculate average training loss
        train_loss /= len(train_loader.dataset)
        history['train_loss'].append(train_loss)
        
        # Validation
        model.eval()
        val_loss = 0
        edge_preds = []
        edge_targets = []
        
        with torch.no_grad():
            for data in val_loader:
                # Move data to device
                data = data.to(device)
                
                # Forward pass
                edge_pred, power_pred, _ = model(data.x, data.edge_index)
                
                # Compute loss
                edge_loss = edge_prediction_loss(edge_pred, data.edge_label)
                power_loss = power_allocation_loss(power_pred, data.power_label)
                
                # Total loss
                loss = edge_loss + 0.5 * power_loss
                
                # Record loss
                val_loss += loss.item() * data.num_graphs
                
                # Record predictions for metrics
                edge_preds.append(edge_pred.squeeze().cpu().numpy() > 0.5)
                edge_targets.append(data.edge_label.cpu().numpy())
        
        # Calculate average validation loss
        val_loss /= len(val_loader.dataset)
        history['val_loss'].append(val_loss)
        
        # Calculate edge prediction metrics
        edge_preds = np.concatenate(edge_preds)
        edge_targets = np.concatenate(edge_targets)
        
        edge_acc = accuracy_score(edge_targets, edge_preds)
        edge_f1 = f1_score(edge_targets, edge_preds)
        
        history['val_edge_acc'].append(edge_acc)
        history['val_edge_f1'].append(edge_f1)
        
        # Print epoch results
        print(f"Epoch {epoch+1}/{num_epochs}:")
        print(f"  Train Loss: {train_loss:.4f}")
        print(f"  Val Loss: {val_loss:.4f}")
        print(f"  Edge Acc: {edge_acc:.4f}, F1: {edge_f1:.4f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), "models/best_noma_gnn.pth")
            print("  Saved new best model!")
        
        # Update learning rate
        scheduler.step(val_loss)
    
    # Save final model
    torch.save(model.state_dict(), "models/final_noma_gnn.pth")
    
    # Save training history
    with open("gnn_results/training_history.pkl", "wb") as f:
        pickle.dump(history, f)
    
    # Plot training history
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history['val_edge_acc'], label='Edge Accuracy')
    plt.plot(history['val_edge_f1'], label='Edge F1 Score')
    plt.xlabel('Epoch')
    plt.ylabel('Score')
    plt.title('Validation Metrics')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig("gnn_results/training_history.png")
    
    return history

def inference(model, features):
    """
    Run inference with the trained GNN model
    
    Args:
        model: Trained GNN model
        features: User features [N, feature_dim]
        
    Returns:
        pairs: List of user pairs (u1, u2)
        power_allocation: Power allocation for each pair
    """
    # Prepare graph data
    data = prepare_graph_data(features, training=False)
    data = data.to(device)
    
    # Set model to evaluation mode
    model.eval()
    
    # Forward pass
    with torch.no_grad():
        edge_pred, power_pred, _ = model(data.x, data.edge_index)
    
    # Extract predicted pairs
    edge_pred = edge_pred.squeeze().cpu().numpy()
    power_pred = power_pred.cpu().numpy()
    
    # Get source and destination nodes for each edge
    src, dst = data.edge_index.cpu().numpy()
    
    # Extract pairs based on edge prediction threshold
    pairs = []
    power_allocation = {}
    used = np.zeros(N, dtype=bool)
    
    # Sort edges by prediction confidence
    edge_indices = np.argsort(-edge_pred)  # Descending order
    
    for idx in edge_indices:
        u1, u2 = src[idx], dst[idx]
        
        # Check if prediction is above threshold and users are not already paired
        if edge_pred[idx] > 0.5 and not used[u1] and not used[u2]:
            pairs.append((u1, u2))
            power_allocation[(u1, u2)] = power_pred[idx]
            used[u1] = used[u2] = True
    
    return pairs, power_allocation

def calculate_throughput(pairs, power_allocation, h_values):
    """
    Calculate system throughput based on predicted pairs and power allocation
    
    Args:
        pairs: List of user pairs (u1, u2)
        power_allocation: Power allocation for each pair
        h_values: Channel gains [N]
        
    Returns:
        throughput: System throughput in Mbps
    """
    num_pairs = len(pairs)
    num_oma = N - 2 * num_pairs
    
    # Create a mask of paired users
    used = np.zeros(N, dtype=bool)
    for u1, u2 in pairs:
        used[u1] = used[u2] = True
    
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
        
        # Get power allocation from prediction
        P1, P2 = power_allocation[(u1, u2)] * total_power
        
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

def evaluate_model(model, test_data_path):
    """
    Evaluate the trained GNN model on test data
    
    Args:
        model: Trained GNN model
        test_data_path: Path to test data
        
    Returns:
        results: Evaluation results
    """
    # Load test data
    with open(test_data_path, "rb") as f:
        test_data = pickle.load(f)
    
    features = test_data['features']
    clustering = test_data['clustering']
    h_values_list = [f[:, 0] for f in features]  # First feature is h_values
    
    # Results storage
    results = {
        'throughput': [],
        'num_pairs': [],
        'edge_acc': [],
        'edge_precision': [],
        'edge_recall': [],
        'edge_f1': []
    }
    
    print("Evaluating model on test data...")
    for i in tqdm(range(len(features))):
        # Get ground truth
        true_clustering = clustering[i]
        h_values = h_values_list[i]
        
        # Run inference
        pairs, power_allocation = inference(model, features[i])
        
        # Calculate throughput
        throughput = calculate_throughput(pairs, power_allocation, h_values)
        results['throughput'].append(throughput)
        results['num_pairs'].append(len(pairs))
        
        # Calculate edge prediction metrics
        pred_clustering = np.zeros((N, N), dtype=bool)
        for u1, u2 in pairs:
            pred_clustering[u1, u2] = pred_clustering[u2, u1] = True
        
        # Flatten matrices for metric calculation
        true_flat = []
        pred_flat = []
        
        for i in range(N):
            for j in range(i+1, N):  # Only consider upper triangular part
                true_flat.append(true_clustering[i, j])
                pred_flat.append(pred_clustering[i, j])
        
        # Calculate metrics
        acc = accuracy_score(true_flat, pred_flat)
        precision = precision_score(true_flat, pred_flat)
        recall = recall_score(true_flat, pred_flat)
        f1 = f1_score(true_flat, pred_flat)
        
        results['edge_acc'].append(acc)
        results['edge_precision'].append(precision)
        results['edge_recall'].append(recall)
        results['edge_f1'].append(f1)
    
    # Calculate average results
    avg_results = {k: np.mean(v) for k, v in results.items()}
    
    print("\nTest Results:")
    print(f"Avg Throughput: {avg_results['throughput']:.2f} Mbps")
    print(f"Avg Num Pairs: {avg_results['num_pairs']:.2f}")
    print(f"Avg Edge Acc: {avg_results['edge_acc']:.4f}")
    print(f"Avg Edge F1: {avg_results['edge_f1']:.4f}")
    
    # Save results
    with open("gnn_results/test_results.pkl", "wb") as f:
        pickle.dump(results, f)
    
    # Plot histograms of results
    plt.figure(figsize=(12, 10))
    
    plt.subplot(2, 2, 1)
    plt.hist(results['throughput'], bins=20)
    plt.xlabel('Throughput (Mbps)')
    plt.ylabel('Count')
    plt.title('Throughput Distribution')
    
    plt.subplot(2, 2, 2)
    plt.hist(results['num_pairs'], bins=20)
    plt.xlabel('Number of NOMA Pairs')
    plt.ylabel('Count')
    plt.title('NOMA Pairs Distribution')
    
    plt.subplot(2, 2, 3)
    plt.hist(results['edge_acc'], bins=20)
    plt.xlabel('Edge Accuracy')
    plt.ylabel('Count')
    plt.title('Edge Accuracy Distribution')
    
    plt.subplot(2, 2, 4)
    plt.hist(results['edge_f1'], bins=20)
    plt.xlabel('Edge F1 Score')
    plt.ylabel('Count')
    plt.title('Edge F1 Score Distribution')
    
    plt.tight_layout()
    plt.savefig("gnn_results/test_results.png")
    
    return results

def main():
    """Main function to run the GNN-based model"""
    
    # Check if data exists
    if not os.path.exists("data/train_data.pkl"):
        print("Training data not found. Please run noma_data_preparation.py first.")
        return
    
    # Prepare data loaders
    train_loader, val_loader = prepare_dataloader("data/train_data.pkl", batch_size=1)
    
    # Create model
    input_dim = 10  # Number of features per user
    model = NOMAGNNModel(input_dim, hidden_dim=64, num_layers=3)
    
    # Print model summary
    print(model)
    
    # Train model
    print("\nTraining model...")
    history = train(model, train_loader, val_loader, num_epochs=50, lr=0.001)
    
    # Evaluate model
    print("\nEvaluating model...")
    results = evaluate_model(model, "data/test_data.pkl")
    
    return results

if __name__ == "__main__":
    main()
