"""
Simple t-SNE Visualization for Multiple Scenarios
Works with any CSV file containing h_dB and distance_m columns
"""

import os
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from torch_geometric.data import Data

import sys
sys.path.insert(0, os.path.dirname(__file__))

from models.pairpower_gnn import PairPowerGNN
from config import CFG


def load_model(checkpoint_path='checkpoints/best_model.pt'):
    """Load trained model"""
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    model = PairPowerGNN(
        in_channels=CFG.IN_CHANNELS,
        hidden=CFG.HIDDEN_DIM,
        out_channels=CFG.OUT_DIM,
        num_layers=CFG.NUM_LAYERS,
        dropout=CFG.DROPOUT
    ).to(device)
    
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    
    if 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
    elif 'model_state' in checkpoint:
        model.load_state_dict(checkpoint['model_state'])
    else:
        model.load_state_dict(checkpoint)
    
    model.eval()
    return model, device


def build_simple_graph(h_csv_path, scaler_path='data/processed/feature_scaler.json'):
    """Build a simple graph from CSV for inference"""
    import json
    
    # Load CSV
    df = pd.read_csv(h_csv_path)
    N = len(df)
    
    # Load scaler
    with open(scaler_path, 'r') as f:
        scaler_data = json.load(f)
    
    mean = np.array(scaler_data['mean'])
    std = np.array(scaler_data['std'])
    
    # Extract features (must match training: distance, path_loss, shadowing, rayleigh, h_dB)
    features = np.stack([
        df['distance_m'].values,
        df['path_loss_dB'].values,
        df['shadowing_dB'].values,
        df['rayleigh_fading'].values,
        df['h_dB'].values
    ], axis=1)
    
    # Normalize
    features_norm = (features - mean) / (std + 1e-8)
    
    # Create simple graph (fully connected for visualization - we just need embeddings)
    x = torch.tensor(features_norm, dtype=torch.float)
    
    # Create k-nearest neighbor edges based on spatial distance
    from sklearn.neighbors import kneighbors_graph
    coords = np.stack([df['x_coord_m'].values, df['y_coord_m'].values], axis=1)
    k = min(20, N-1)
    adj = kneighbors_graph(coords, k, mode='connectivity', include_self=False)
    edge_index = torch.tensor(np.array(adj.nonzero()), dtype=torch.long)
    
    data = Data(x=x, edge_index=edge_index)
    return data, df


def visualize_scenario(h_csv_path, model, device, scenario_name, save_dir='results/tsne'):
    """Process and visualize a single scenario"""
    
    print(f"\n{'='*70}")
    print(f"Processing: {scenario_name}")
    print(f"{'='*70}")
    
    if not os.path.exists(h_csv_path):
        print(f"⚠ File not found: {h_csv_path}")
        return
    
    try:
        # Build graph
        data, h_df = build_simple_graph(h_csv_path)
        data = data.to(device)
        
        N = len(h_df)
        print(f"✓ Loaded {N} users")
        print(f"  - Channel gain: {h_df['h_dB'].min():.2f} to {h_df['h_dB'].max():.2f} dB")
        print(f"  - Distance: {h_df['distance_m'].min():.0f} to {h_df['distance_m'].max():.0f} m")
        
        # Extract embeddings
        with torch.no_grad():
            embeddings = model.encode(data.x, data.edge_index).cpu().numpy()
        
        print(f"✓ Extracted {embeddings.shape[0]} embeddings of dim {embeddings.shape[1]}")
        
        # Run t-SNE
        print(f"Running t-SNE...")
        perplexity = min(30, N // 4)
        tsne = TSNE(n_components=2, perplexity=perplexity, max_iter=1000, random_state=42, verbose=0)
        embeddings_2d = tsne.fit_transform(embeddings)
        print(f"✓ t-SNE complete")
        
        # Categorize users
        h_dB = h_df['h_dB'].values
        distance_m = h_df['distance_m'].values
        
        percentile_33 = np.percentile(h_dB, 33)
        percentile_67 = np.percentile(h_dB, 67)
        categories = np.where(h_dB < percentile_33, 0, np.where(h_dB < percentile_67, 1, 2))
        
        # Create visualization
        os.makedirs(save_dir, exist_ok=True)
        
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.1], hspace=0.25, wspace=0.25,
                            left=0.06, right=0.97, top=0.94, bottom=0.06)
        
        fig.suptitle(f'NOMA-GNN Node Embeddings: {scenario_name.upper()} (N={N})', 
                     fontsize=18, fontweight='bold')
        
        # 1. User Categories (Top-Left)
        ax1 = fig.add_subplot(gs[0, 0])
        colors_map = {0: 'red', 1: 'orange', 2: 'green'}
        labels_map = {0: f'Weak Users (N={np.sum(categories==0)})', 
                      1: f'Medium Users (N={np.sum(categories==1)})',
                      2: f'Strong Users (N={np.sum(categories==2)})'}
        
        for cat_id, color in colors_map.items():
            mask = categories == cat_id
            ax1.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1],
                       c=color, label=labels_map[cat_id], s=50, alpha=0.7,
                       edgecolors='black', linewidth=0.5)
        
        ax1.set_title('Node Embeddings: User Categories', fontsize=13, fontweight='bold')
        ax1.set_xlabel('t-SNE Dimension 1', fontsize=11)
        ax1.set_ylabel('t-SNE Dimension 2', fontsize=11)
        ax1.legend(fontsize=10, loc='best')
        ax1.grid(True, alpha=0.3)
        
        # 2. Spatial Distribution (Top-Right)
        ax2 = fig.add_subplot(gs[0, 1])
        sc2 = ax2.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1],
                         c=distance_m, cmap='plasma', s=50, alpha=0.7,
                         edgecolors='black', linewidth=0.5)
        ax2.set_title('Node Embeddings: Spatial Distribution', fontsize=13, fontweight='bold')
        ax2.set_xlabel('t-SNE Dimension 1', fontsize=11)
        ax2.set_ylabel('t-SNE Dimension 2', fontsize=11)
        ax2.grid(True, alpha=0.3)
        cbar2 = plt.colorbar(sc2, ax=ax2)
        cbar2.set_label('Distance from BS (m)', fontsize=10, rotation=270, labelpad=20)
        
        # 3. Optimal Pairing Structure (Full Bottom Width)
        ax3 = fig.add_subplot(gs[1, :])
        weak_indices = np.where(categories == 0)[0]
        strong_indices = np.where(categories == 2)[0]
        
        # All users in gray background
        ax3.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1],
                   c='lightgray', s=30, alpha=0.4, label='All Users')
        
        # Draw representative pairing connections
        num_pairs = min(len(weak_indices), len(strong_indices), 100)
        paired_users = set()
        
        for i in range(num_pairs):
            w_idx = weak_indices[i % len(weak_indices)]
            s_idx = strong_indices[i % len(strong_indices)]
            
            ax3.plot([embeddings_2d[w_idx, 0], embeddings_2d[s_idx, 0]],
                    [embeddings_2d[w_idx, 1], embeddings_2d[s_idx, 1]],
                    'b-', alpha=0.2, linewidth=0.8)
            paired_users.add(w_idx)
            paired_users.add(s_idx)
        
        # Highlight paired users
        if paired_users:
            paired_list = list(paired_users)
            paired_colors = h_dB[paired_list]
            
            sc3 = ax3.scatter(embeddings_2d[paired_list, 0], embeddings_2d[paired_list, 1],
                             c=paired_colors, cmap='RdYlGn', s=60, 
                             edgecolors='black', linewidth=1, alpha=0.8,
                             label=f'Paired Users (N={len(paired_list)})')
            
            cbar3 = plt.colorbar(sc3, ax=ax3)
            cbar3.set_label('Channel Gain (dB)', fontsize=10, rotation=270, labelpad=20)
        
        ax3.set_title('Node Embeddings: Optimal Pairing Structure', fontsize=13, fontweight='bold')
        ax3.set_xlabel('t-SNE Dimension 1', fontsize=11)
        ax3.set_ylabel('t-SNE Dimension 2', fontsize=11)
        ax3.legend(fontsize=10, loc='best')
        ax3.grid(True, alpha=0.3)
        
        save_path = f'{save_dir}/tsne_{scenario_name}.png'
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")
        plt.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main visualization pipeline"""
    
    print("\n" + "="*70)
    print("NOMA-GNN t-SNE Visualization: Multi-Scenario Analysis")
    print("="*70)
    
    # Load model
    model, device = load_model('checkpoints/best_model.pt')
    print(f"✓ Model loaded (device: {device})")
    
    # Define scenarios
    scenarios = [
        ('500users', 'test_scenario_500users.csv'),
        ('1000users', '../h_values_1000.csv'),
        ('2000users', '../h_values_a.csv'),
    ]
    
    # Process each scenario
    for name, csv_path in scenarios:
        visualize_scenario(csv_path, model, device, name, save_dir='results/tsne')
    
    print("\n" + "="*70)
    print(f"✓ Visualization complete!")
    print(f"✓ Results saved to: results/tsne/")
    print("="*70)


if __name__ == "__main__":
    main()
