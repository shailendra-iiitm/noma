"""
Data preparation and feature extraction for NOMA deep learning framework
This script generates training data for the deep learning model
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from tqdm import tqdm
import os
import pickle
from sklearn.model_selection import train_test_split

# Create directories
os.makedirs("data", exist_ok=True)
os.makedirs("plots", exist_ok=True)

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

def generate_channel_scenario(seed=None):
    """Generate a single channel scenario with user placement and channel gains"""
    if seed is not None:
        np.random.seed(seed)
        
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
    h_db = 10 * np.log10(h_values**2 + 1e-12)  # Channel gain in dB
    h_norm = h_values / np.max(h_values)  # Normalized channel gain
    
    scenario = {
        'h_values': h_values,
        'h_db': h_db,
        'h_norm': h_norm,
        'x_coords': x_coords,
        'y_coords': y_coords,
        'distances': r,
        'theta': theta,
        'shadowing': shadowing,
        'path_loss_db': pl_db,
        'fading': fading
    }
    
    return scenario

def calc_pair_rate(h1, h2):
    """Calculate achievable rates for a NOMA pair"""
    # Power allocation based on channel gain ratio
    P1 = total_power * h2 / (h1 + h2)
    P2 = total_power * h1 / (h1 + h2)
    
    # Rate calculations with SIC
    R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))  # Weaker user experiences interference
    R2 = np.log2(1 + (P2 * h2) / noise_power)  # Stronger user decodes weaker user's signal first
    
    return P1, P2, R1, R2, R1 + R2

def run_static_clustering(h_values):
    """Run Static clustering algorithm"""
    sorted_indices = np.argsort(h_values)
    pairs = []
    used = np.zeros(N, dtype=bool)
    total_rate = 0
    
    for i in range(N//2):
        u1, u2 = sorted_indices[i], sorted_indices[N-1-i]  # Pair worst with best
        h1, h2 = h_values[u1], h_values[u2]
        
        # Check if SIC threshold is satisfied
        if 10*np.log10(h2/h1) >= sic_threshold_db:
            P1, P2, R1, R2, R_sum = calc_pair_rate(h1, h2)
            pairs.append((u1, u2))
            total_rate += R_sum
            used[u1] = used[u2] = True
    
    return pairs, used, total_rate

def run_balanced_clustering(h_values):
    """Run Balanced clustering algorithm"""
    sorted_indices = np.argsort(h_values)
    pairs = []
    used = np.zeros(N, dtype=bool)
    total_rate = 0
    
    for i in range(N//2):
        u1, u2 = sorted_indices[i], sorted_indices[i + N//2]
        h1, h2 = h_values[u1], h_values[u2]
        
        # Check if SIC threshold is satisfied
        delta_db = 10 * np.log10(h2/h1)
        if delta_db >= sic_threshold_db:
            P1, P2, R1, R2, R_sum = calc_pair_rate(h1, h2)
            pairs.append((u1, u2))
            total_rate += R_sum
            used[u1] = used[u2] = True
    
    return pairs, used, total_rate

def run_blossom_clustering(h_values):
    """Run Blossom clustering algorithm"""
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
    matches = list(nx.max_weight_matching(G, maxcardinality=True))
    pairs = []
    used = np.zeros(N, dtype=bool)
    total_rate = 0
    
    # Process matching results
    for u1, u2 in matches:
        h1, h2 = h_values[u1], h_values[u2]
        
        # Ensure h1 is the weaker channel
        if h1 > h2:
            h1, h2 = h2, h1
            
        P1, P2, R1, R2, R_sum = calc_pair_rate(h1, h2)
        pairs.append((u1, u2))
        total_rate += R_sum
        used[u1] = used[u2] = True
    
    return pairs, used, total_rate

def extract_features(scenario):
    """Extract features for each user in the scenario"""
    features = np.zeros((N, 10))
    
    for i in range(N):
        features[i, 0] = scenario['h_values'][i]            # Linear channel gain
        features[i, 1] = scenario['h_db'][i]                # Channel gain in dB
        features[i, 2] = scenario['h_norm'][i]              # Normalized channel gain
        features[i, 3] = scenario['x_coords'][i]            # X coordinate
        features[i, 4] = scenario['y_coords'][i]            # Y coordinate
        features[i, 5] = scenario['distances'][i]           # Distance from BS
        features[i, 6] = scenario['distances'][i]/radius    # Normalized distance
        features[i, 7] = scenario['shadowing'][i]           # Shadowing (dB)
        features[i, 8] = scenario['path_loss_db'][i]        # Path loss (dB)
        features[i, 9] = scenario['fading'][i]              # Rayleigh fading
    
    return features

def create_clustering_matrix(pairs, N):
    """Create binary adjacency matrix from user pairs"""
    matrix = np.zeros((N, N), dtype=np.float32)
    
    for u1, u2 in pairs:
        matrix[u1, u2] = 1
        matrix[u2, u1] = 1
        
    return matrix

def extract_power_allocation(pairs, h_values):
    """Extract power allocation coefficients from pairs and channel gains"""
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

def calculate_throughput(pairs, used, h_values):
    """Calculate system throughput based on user pairing"""
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
            
        P1, P2, R1, R2, R_sum = calc_pair_rate(h1, h2)
        throughput = R_sum * B_pair / 1e6
        total_throughput += throughput
    
    # OMA users
    for u in range(N):
        if not used[u]:
            h = h_values[u]
            R1_oma = np.log2(1 + (total_power * h) / noise_power)
            throughput = R1_oma * B_pair / 1e6
            total_throughput += throughput
    
    return total_throughput

def generate_dataset(num_scenarios=1000, save=True):
    """Generate dataset for training the deep learning model"""
    features_list = []
    static_clusters = []
    balanced_clusters = []
    blossom_clusters = []
    static_powers = []
    balanced_powers = []
    blossom_powers = []
    throughputs = {
        'static': [],
        'balanced': [],
        'blossom': []
    }
    
    print(f"Generating {num_scenarios} scenarios...")
    for i in tqdm(range(num_scenarios)):
        # Generate new scenario
        scenario = generate_channel_scenario(seed=i)
        h_values = scenario['h_values']
        
        # Extract features
        features = extract_features(scenario)
        features_list.append(features)
        
        # Run clustering algorithms
        static_pairs, static_used, static_rate = run_static_clustering(h_values)
        balanced_pairs, balanced_used, balanced_rate = run_balanced_clustering(h_values)
        blossom_pairs, blossom_used, blossom_rate = run_blossom_clustering(h_values)
        
        # Create clustering matrices
        static_matrix = create_clustering_matrix(static_pairs, N)
        balanced_matrix = create_clustering_matrix(balanced_pairs, N)
        blossom_matrix = create_clustering_matrix(blossom_pairs, N)
        
        # Store clustering matrices
        static_clusters.append(static_matrix)
        balanced_clusters.append(balanced_matrix)
        blossom_clusters.append(blossom_matrix)
        
        # Extract power allocation
        static_power = extract_power_allocation(static_pairs, h_values)
        balanced_power = extract_power_allocation(balanced_pairs, h_values)
        blossom_power = extract_power_allocation(blossom_pairs, h_values)
        
        # Store power allocation
        static_powers.append(static_power)
        balanced_powers.append(balanced_power)
        blossom_powers.append(blossom_power)
        
        # Calculate throughput
        static_tp = calculate_throughput(static_pairs, static_used, h_values)
        balanced_tp = calculate_throughput(balanced_pairs, balanced_used, h_values)
        blossom_tp = calculate_throughput(blossom_pairs, blossom_used, h_values)
        
        # Store throughput
        throughputs['static'].append(static_tp)
        throughputs['balanced'].append(balanced_tp)
        throughputs['blossom'].append(blossom_tp)
    
    # Create dataset
    dataset = {
        'features': features_list,
        'static_clustering': static_clusters,
        'balanced_clustering': balanced_clusters,
        'blossom_clustering': blossom_clusters,
        'static_power': static_powers,
        'balanced_power': balanced_powers,
        'blossom_power': blossom_powers,
        'throughputs': throughputs
    }
    
    # Save dataset
    if save:
        with open("data/noma_dataset.pkl", "wb") as f:
            pickle.dump(dataset, f)
        
        print(f"Dataset saved to data/noma_dataset.pkl")
        
        # Plot throughput comparison
        plt.figure(figsize=(10, 6))
        plt.boxplot([throughputs['static'], throughputs['balanced'], throughputs['blossom']], 
                   labels=['Static', 'Balanced', 'Blossom'])
        plt.ylabel('Throughput (Mbps)')
        plt.title('Throughput Comparison Across Methods')
        plt.grid(alpha=0.3)
        plt.savefig("plots/throughput_comparison_boxplot.png")
        
        # Plot average throughput
        avg_throughputs = [np.mean(throughputs['static']), 
                          np.mean(throughputs['balanced']), 
                          np.mean(throughputs['blossom'])]
        
        plt.figure(figsize=(10, 6))
        plt.bar(['Static', 'Balanced', 'Blossom'], avg_throughputs)
        plt.ylabel('Average Throughput (Mbps)')
        plt.title('Average Throughput Comparison')
        for i, v in enumerate(avg_throughputs):
            plt.text(i, v + 0.5, f"{v:.2f}", ha='center')
        plt.savefig("plots/avg_throughput_comparison.png")
    
    return dataset

if __name__ == "__main__":
    # Generate dataset with 1000 scenarios
    dataset = generate_dataset(num_scenarios=1000)
    
    # Split the dataset
    features = dataset['features']
    labels = dataset['blossom_clustering']  # Use blossom as the target
    powers = dataset['blossom_power']
    
    X_train, X_test, y_train, y_test, p_train, p_test = train_test_split(
        features, labels, powers, test_size=0.2, random_state=42
    )
    
    # Save training and test sets separately
    train_data = {
        'features': X_train,
        'clustering': y_train,
        'power': p_train
    }
    
    test_data = {
        'features': X_test,
        'clustering': y_test,
        'power': p_test
    }
    
    with open("data/train_data.pkl", "wb") as f:
        pickle.dump(train_data, f)
    
    with open("data/test_data.pkl", "wb") as f:
        pickle.dump(test_data, f)
    
    print("Dataset split and saved to data/train_data.pkl and data/test_data.pkl")
