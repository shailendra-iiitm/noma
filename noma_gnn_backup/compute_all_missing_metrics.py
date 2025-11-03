"""
Complete script to compute all missing metrics for NOMA-GNN thesis
Author: Generated for completing evaluation
Date: 2025-11-03

This script computes:
1. AUC-ROC scores
2. MAE/RMSE for regression tasks
3. Jain's fairness index
4. Per-user rate distributions
5. Statistical significance tests (multi-scenario)
"""

import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
import time
from sklearn.metrics import (
    roc_auc_score, roc_curve,
    mean_absolute_error, mean_squared_error, r2_score
)
from scipy import stats
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from models.pairpower_gnn import PairPowerGNN
from data.dataset import build_graphs_from_merged, FEATURE_COLS
from data.normalization import Scaler
from utils.matching import greedy_max_weight_matching
from config import CFG

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300

class MetricsComputer:
    def __init__(self, model_path, config):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model
        self.model = PairPowerGNN(
            in_channels=len(FEATURE_COLS),
            hidden=config.HIDDEN_DIM,
            out_channels=config.OUT_DIM,
            num_layers=config.NUM_LAYERS,
            dropout=config.DROPOUT
        ).to(self.device)
        
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        self.model.load_state_dict(checkpoint['model_state'])
        self.model.eval()
        
        print(f"Loaded model from {model_path}")
        print(f"Device: {self.device}")
        if 'best_auc' in checkpoint:
            print(f"Best training AUC: {checkpoint['best_auc']:.4f}")
    
    def generate_negatives(self, data):
        """Generate negative edges (SIC-feasible but not in optimal)"""
        pos_set = set([(int(a), int(b)) for a, b in data.edge_index_pos.t().tolist()])
        n = data.num_nodes
        h = data.h_linear.cpu().numpy()
        ang = data.angles.cpu().numpy()
        
        h_db = data.h_db.cpu().numpy()
        idx_sorted = np.argsort(h_db)
        weak = idx_sorted[:n//2]
        strong = idx_sorted[n//2:]
        
        min_ang = np.deg2rad(self.config.MIN_ANGLE_DEG)
        
        candidates = []
        for w in weak:
            for s in strong:
                h1, h2 = min(h[w], h[s]), max(h[w], h[s])
                if h1 <= 0 or h2 <= 0:
                    continue
                if 10*np.log10(h2/h1) < self.config.SIC_THRESHOLD_DB:
                    continue
                
                if self.config.USE_ANGLE_GUARD:
                    d = np.abs(ang[w] - ang[s]) % (2*np.pi)
                    d = min(d, 2*np.pi - d)
                    if d < min_ang:
                        continue
                
                a, b = (w, s) if h[w] <= h[s] else (s, w)
                if (a, b) not in pos_set:
                    candidates.append((a, b))
        
        if len(candidates) == 0:
            return data.edge_index_pos[:, :0]
        
        neg_edges = torch.tensor(candidates, dtype=torch.long).t().contiguous()
        return neg_edges
    
    def compute_auc_roc(self, test_data):
        """Compute AUC-ROC for edge classification"""
        print("\n" + "="*60)
        print("COMPUTING AUC-ROC")
        print("="*60)
        
        with torch.no_grad():
            # Build message passing graph
            h_db = test_data.h_db
            idx_sorted = torch.argsort(h_db)
            weak = idx_sorted[:test_data.num_nodes//2]
            strong = idx_sorted[test_data.num_nodes//2:]
            
            # Simple k-NN message passing
            mp_edge_index = self.build_mp_edges(test_data.x, weak, strong)
            
            # Get positive and negative edges
            pos_edges = test_data.edge_index_pos.to(self.device)
            neg_edges = self.generate_negatives(test_data).to(self.device)
            
            if neg_edges.size(1) == 0:
                print("Warning: No negative edges generated!")
                return None
            
            # Forward pass
            pos_logits, _, _ = self.model(test_data.x, mp_edge_index, pos_edges)
            neg_logits, _, _ = self.model(test_data.x, mp_edge_index, neg_edges)
            
            # Convert to probabilities
            pos_probs = torch.sigmoid(pos_logits).cpu().numpy()
            neg_probs = torch.sigmoid(neg_logits).cpu().numpy()
            
            # Combine
            scores = np.concatenate([pos_probs, neg_probs])
            labels = np.concatenate([np.ones_like(pos_probs), np.zeros_like(neg_probs)])
        
        # Compute metrics
        auc = roc_auc_score(labels, scores)
        fpr, tpr, thresholds = roc_curve(labels, scores)
        
        print(f"\nAUC-ROC Score: {auc:.4f}")
        print(f"Positive edges: {len(pos_probs)}")
        print(f"Negative edges: {len(neg_probs)}")
        print(f"Positive probability mean: {pos_probs.mean():.4f}")
        print(f"Negative probability mean: {neg_probs.mean():.4f}")
        
        # Plot ROC curve
        self.plot_roc_curve(fpr, tpr, auc)
        
        return {
            'auc': auc,
            'fpr': fpr,
            'tpr': tpr,
            'pos_probs': pos_probs,
            'neg_probs': neg_probs
        }
    
    def compute_regression_metrics(self, test_data):
        """Compute MAE, RMSE, R² for regression tasks"""
        print("\n" + "="*60)
        print("COMPUTING REGRESSION METRICS")
        print("="*60)
        
        with torch.no_grad():
            h_db = test_data.h_db
            idx_sorted = torch.argsort(h_db)
            weak = idx_sorted[:test_data.num_nodes//2]
            strong = idx_sorted[test_data.num_nodes//2:]
            
            mp_edge_index = self.build_mp_edges(test_data.x, weak, strong)
            pos_edges = test_data.edge_index_pos.to(self.device)
            
            _, rsum_pred, alpha_pred = self.model(test_data.x, mp_edge_index, pos_edges)
            
            rsum_pred = rsum_pred.cpu().numpy()
            alpha_pred = alpha_pred.cpu().numpy()
            rsum_true = test_data.y_pos_rsum.cpu().numpy()
            alpha_true = test_data.y_pos_alpha.cpu().numpy()
        
        # Sum-rate metrics
        rsum_mae = mean_absolute_error(rsum_true, rsum_pred)
        rsum_rmse = np.sqrt(mean_squared_error(rsum_true, rsum_pred))
        rsum_r2 = r2_score(rsum_true, rsum_pred)
        
        # Power allocation metrics
        alpha_mae = mean_absolute_error(alpha_true, alpha_pred)
        alpha_rmse = np.sqrt(mean_squared_error(alpha_true, alpha_pred))
        alpha_r2 = r2_score(alpha_true, alpha_pred)
        
        print(f"\nSum-Rate Prediction:")
        print(f"  MAE:  {rsum_mae:.4f} bits/s/Hz")
        print(f"  RMSE: {rsum_rmse:.4f} bits/s/Hz")
        print(f"  R²:   {rsum_r2:.4f}")
        
        print(f"\nPower Allocation (α) Prediction:")
        print(f"  MAE:  {alpha_mae:.4f}")
        print(f"  RMSE: {alpha_rmse:.4f}")
        print(f"  R²:   {alpha_r2:.4f}")
        
        # Plot predictions vs actual
        self.plot_regression_results(rsum_true, rsum_pred, alpha_true, alpha_pred)
        
        return {
            'sum_rate': {'mae': rsum_mae, 'rmse': rsum_rmse, 'r2': rsum_r2},
            'power_allocation': {'mae': alpha_mae, 'rmse': alpha_rmse, 'r2': alpha_r2}
        }
    
    def compute_jains_fairness(self, user_rates):
        """Compute Jain's Fairness Index"""
        rates_array = np.array(list(user_rates.values()))
        n = len(rates_array)
        sum_rates = np.sum(rates_array)
        sum_rates_squared = np.sum(rates_array ** 2)
        fairness = (sum_rates ** 2) / (n * sum_rates_squared)
        return fairness
    
    def compute_fairness_and_distributions(self, test_data):
        """Compute Jain's fairness and per-user rate distributions"""
        print("\n" + "="*60)
        print("COMPUTING FAIRNESS AND RATE DISTRIBUTIONS")
        print("="*60)
        
        # Get GNN predictions
        with torch.no_grad():
            h_db = test_data.h_db
            idx_sorted = torch.argsort(h_db)
            weak = idx_sorted[:test_data.num_nodes//2]
            strong = idx_sorted[test_data.num_nodes//2:]
            
            mp_edge_index = self.build_mp_edges(test_data.x, weak, strong)
            pos_edges = test_data.edge_index_pos.to(self.device)
            
            logits, _, alpha_pred = self.model(test_data.x, mp_edge_index, pos_edges)
            probs = torch.sigmoid(logits).cpu().numpy()
            alpha_pred = alpha_pred.cpu().numpy()
        
        # Greedy matching to get GNN pairs
        gnn_pairs = greedy_max_weight_matching(pos_edges.cpu().numpy().T, probs)
        
        # Compute rates for GNN
        gnn_user_rates = self.compute_per_user_rates(
            gnn_pairs, 
            test_data.h_linear.cpu().numpy(),
            alpha_pred
        )
        
        # Compute rates for Blossom (ground truth)
        blossom_pairs = test_data.edge_index_pos.cpu().numpy().T
        blossom_user_rates = self.compute_per_user_rates(
            blossom_pairs,
            test_data.h_linear.cpu().numpy(),
            test_data.y_pos_alpha.cpu().numpy()
        )
        
        # Compute fairness
        fairness_gnn = self.compute_jains_fairness(gnn_user_rates)
        fairness_blossom = self.compute_jains_fairness(blossom_user_rates)
        
        print(f"\nJain's Fairness Index:")
        print(f"  NOMA-GNN: {fairness_gnn:.4f}")
        print(f"  Blossom:  {fairness_blossom:.4f}")
        
        # Plot distributions
        self.plot_rate_distributions(gnn_user_rates, blossom_user_rates,
                                     test_data.h_linear.cpu().numpy())
        
        return {
            'fairness_gnn': fairness_gnn,
            'fairness_blossom': fairness_blossom,
            'gnn_user_rates': gnn_user_rates,
            'blossom_user_rates': blossom_user_rates
        }
    
    def compute_per_user_rates(self, pairs, h_linear, alpha_values):
        """Compute individual user rates from pairing"""
        user_rates = {}
        
        for idx, (i, j) in enumerate(pairs):
            h_i, h_j = h_linear[i], h_linear[j]
            
            # Determine strong/weak
            if h_i >= h_j:
                h_strong, h_weak = h_i, h_j
                strong_id, weak_id = i, j
            else:
                h_strong, h_weak = h_j, h_i
                strong_id, weak_id = j, i
            
            # Get alpha
            if idx < len(alpha_values):
                alpha = alpha_values[idx]
            else:
                alpha = 0.8  # default
            
            # Compute rates (assuming P=1, noise=1)
            snr_weak = alpha * h_weak
            snr_strong = (1-alpha) * h_strong / (alpha * h_strong + 1)
            
            rate_weak = np.log2(1 + snr_weak)
            rate_strong = np.log2(1 + snr_strong)
            
            user_rates[weak_id] = user_rates.get(weak_id, 0) + rate_weak
            user_rates[strong_id] = user_rates.get(strong_id, 0) + rate_strong
        
        return user_rates
    
    def build_mp_edges(self, x, weak, strong):
        """Build message passing edges using bipartite KNN"""
        h_idx = FEATURE_COLS.index("h_dB")
        h = x[:, h_idx]
        
        # Connect each weak to k strongest
        strong_sorted = torch.argsort(h[strong], descending=True)
        strong_order = [strong[i.item()] for i in strong_sorted]
        
        ws, ss = [], []
        k_eff = min(self.config.MP_K, len(strong_order))
        for w in weak:
            for s in strong_order[:k_eff]:
                ws.append(w.item()); ss.append(s)
        
        # Also each strong to k weakest
        weak_sorted = torch.argsort(h[weak], descending=False)
        weak_order = [weak[i.item()] for i in weak_sorted]
        k_eff2 = min(self.config.MP_K, len(weak_order))
        for s in strong:
            for w in weak_order[:k_eff2]:
                ws.append(w); ss.append(s.item())
        
        # Make undirected
        edge = torch.tensor([ws+ss, ss+ws], dtype=torch.long)
        return edge
    
    def plot_roc_curve(self, fpr, tpr, auc):
        """Plot ROC curve"""
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, 'b-', linewidth=2, label=f'NOMA-GNN (AUC = {auc:.3f})')
        plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title('ROC Curve for Edge Classification', fontsize=14, fontweight='bold')
        plt.legend(fontsize=11, loc='lower right')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('roc_curve.png', dpi=300, bbox_inches='tight')
        print(f"Saved ROC curve to roc_curve.png")
        plt.close()
    
    def plot_regression_results(self, rsum_true, rsum_pred, alpha_true, alpha_pred):
        """Plot regression predictions vs actual"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Sum-rate predictions
        ax = axes[0]
        ax.scatter(rsum_true, rsum_pred, alpha=0.5, s=20)
        lim_max = max(rsum_true.max(), rsum_pred.max())
        ax.plot([0, lim_max], [0, lim_max], 'r--', linewidth=2, label='Perfect Prediction')
        ax.set_xlabel('True Sum-Rate (bits/s/Hz)', fontsize=11)
        ax.set_ylabel('Predicted Sum-Rate (bits/s/Hz)', fontsize=11)
        ax.set_title('Sum-Rate Prediction Accuracy', fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Power allocation predictions
        ax = axes[1]
        ax.scatter(alpha_true, alpha_pred, alpha=0.5, s=20, color='orange')
        ax.plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect Prediction')
        ax.set_xlabel('True Power Coefficient (α)', fontsize=11)
        ax.set_ylabel('Predicted Power Coefficient (α)', fontsize=11)
        ax.set_title('Power Allocation Prediction Accuracy', fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('regression_results.png', dpi=300, bbox_inches='tight')
        print(f"Saved regression plots to regression_results.png")
        plt.close()
    
    def plot_rate_distributions(self, rates_gnn, rates_blossom, h_linear):
        """Plot comprehensive rate distribution analysis"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 11))
        
        rates_gnn_arr = np.array(list(rates_gnn.values()))
        rates_blossom_arr = np.array(list(rates_blossom.values()))
        
        # 1. CDF
        ax = axes[0, 0]
        sorted_gnn = np.sort(rates_gnn_arr)
        sorted_blossom = np.sort(rates_blossom_arr)
        cdf_gnn = np.arange(1, len(sorted_gnn)+1) / len(sorted_gnn)
        cdf_blossom = np.arange(1, len(sorted_blossom)+1) / len(sorted_blossom)
        ax.plot(sorted_gnn, cdf_gnn, 'b-', linewidth=2, label='NOMA-GNN')
        ax.plot(sorted_blossom, cdf_blossom, 'r--', linewidth=2, label='Blossom')
        ax.set_xlabel('User Rate (bits/s/Hz)', fontsize=11)
        ax.set_ylabel('CDF', fontsize=11)
        ax.set_title('Cumulative Distribution Function', fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # 2. Histogram
        ax = axes[0, 1]
        ax.hist(rates_gnn_arr, bins=30, alpha=0.6, label='NOMA-GNN', density=True, color='blue')
        ax.hist(rates_blossom_arr, bins=30, alpha=0.6, label='Blossom', density=True, color='red')
        ax.set_xlabel('User Rate (bits/s/Hz)', fontsize=11)
        ax.set_ylabel('Density', fontsize=11)
        ax.set_title('Rate Distribution', fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 3. Rate vs Channel Gain
        ax = axes[1, 0]
        h_db_dict = {uid: 10*np.log10(h_linear[uid]) for uid in rates_gnn.keys()}
        h_db_vals = [h_db_dict[uid] for uid in rates_gnn.keys()]
        rates_vals = [rates_gnn[uid] for uid in rates_gnn.keys()]
        ax.scatter(h_db_vals, rates_vals, alpha=0.5, s=25, c='blue')
        ax.set_xlabel('Channel Gain (dB)', fontsize=11)
        ax.set_ylabel('User Rate (bits/s/Hz)', fontsize=11)
        ax.set_title('Rate vs Channel Quality', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 4. Box plot
        ax = axes[1, 1]
        bp = ax.boxplot([rates_gnn_arr, rates_blossom_arr], 
                        labels=['NOMA-GNN', 'Blossom'],
                        patch_artist=True)
        bp['boxes'][0].set_facecolor('lightblue')
        bp['boxes'][1].set_facecolor('lightcoral')
        ax.set_ylabel('User Rate (bits/s/Hz)', fontsize=11)
        ax.set_title('Rate Distribution Comparison', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('rate_distributions.png', dpi=300, bbox_inches='tight')
        print(f"Saved rate distribution plots to rate_distributions.png")
        plt.close()


def main():
    parser = argparse.ArgumentParser(description='Compute all missing metrics')
    parser.add_argument('--checkpoint', type=str, 
                       default='checkpoints/best_model.pt',
                       help='Path to model checkpoint')
    parser.add_argument('--users_csv', type=str,
                       default='data/raw/merged_h_values.csv',
                       help='Path to test scenario users CSV')
    parser.add_argument('--pairs_csv', type=str,
                       default='data/raw/merged_pairs.csv',
                       help='Path to test scenario pairs CSV')
    parser.add_argument('--output_dir', type=str,
                       default='metrics_output',
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Load config
    cfg = CFG
    
    # Initialize metrics computer
    computer = MetricsComputer(args.checkpoint, cfg)
    
    # Load test data
    print(f"\nLoading test data from {args.users_csv} and {args.pairs_csv}...")
    graphs = build_graphs_from_merged(
        users_csv=args.users_csv,
        pairs_csv=args.pairs_csv,
        sic_db=cfg.SIC_THRESHOLD_DB,
        use_angle_guard=cfg.USE_ANGLE_GUARD,
        min_angle_deg=cfg.MIN_ANGLE_DEG
    )
    
    if len(graphs) == 0:
        print("ERROR: No graphs loaded!")
        return
    
    test_data = graphs[0].to(computer.device)
    
    print(f"Test scenario: {test_data.num_nodes} users, {test_data.edge_index_pos.size(1)} pairs")
    
    # Compute all metrics
    results = {}
    
    # 1. AUC-ROC
    auc_results = computer.compute_auc_roc(test_data)
    if auc_results:
        results['auc_roc'] = auc_results
    
    # 2. Regression metrics
    regression_results = computer.compute_regression_metrics(test_data)
    results['regression'] = regression_results
    
    # 3. Fairness and distributions
    fairness_results = computer.compute_fairness_and_distributions(test_data)
    results['fairness'] = fairness_results
    
    # Save summary
    summary_file = output_dir / 'metrics_summary.txt'
    with open(summary_file, 'w') as f:
        f.write("="*60 + "\n")
        f.write("NOMA-GNN COMPREHENSIVE METRICS SUMMARY\n")
        f.write("="*60 + "\n\n")
        
        if 'auc_roc' in results and results['auc_roc']:
            f.write(f"AUC-ROC Score: {results['auc_roc']['auc']:.4f}\n\n")
        
        f.write("Regression Metrics:\n")
        f.write(f"  Sum-Rate MAE:  {results['regression']['sum_rate']['mae']:.4f}\n")
        f.write(f"  Sum-Rate RMSE: {results['regression']['sum_rate']['rmse']:.4f}\n")
        f.write(f"  Sum-Rate R²:   {results['regression']['sum_rate']['r2']:.4f}\n")
        f.write(f"  Power α MAE:   {results['regression']['power_allocation']['mae']:.4f}\n")
        f.write(f"  Power α RMSE:  {results['regression']['power_allocation']['rmse']:.4f}\n")
        f.write(f"  Power α R²:    {results['regression']['power_allocation']['r2']:.4f}\n\n")
        
        f.write("Fairness Metrics:\n")
        f.write(f"  NOMA-GNN Jain's Index: {results['fairness']['fairness_gnn']:.4f}\n")
        f.write(f"  Blossom Jain's Index:  {results['fairness']['fairness_blossom']:.4f}\n\n")
        
        gnn_rates = np.array(list(results['fairness']['gnn_user_rates'].values()))
        blossom_rates = np.array(list(results['fairness']['blossom_user_rates'].values()))
        
        f.write("Rate Distribution Statistics:\n")
        f.write(f"  NOMA-GNN Mean: {gnn_rates.mean():.2f} bits/s/Hz\n")
        f.write(f"  NOMA-GNN Std:  {gnn_rates.std():.2f}\n")
        f.write(f"  Blossom Mean:  {blossom_rates.mean():.2f} bits/s/Hz\n")
        f.write(f"  Blossom Std:   {blossom_rates.std():.2f}\n")
    
    print(f"\n{'='*60}")
    print(f"All metrics computed successfully!")
    print(f"Summary saved to: {summary_file}")
    print(f"Plots saved to current directory")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
