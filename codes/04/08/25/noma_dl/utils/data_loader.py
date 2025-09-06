import os
import pandas as pd
import numpy as np
import torch
from torch_geometric.data import Data, Dataset
from typing import List, Tuple, Dict
from pathlib import Path

class NOMADataPreprocessor:
    def __init__(self, base_path: str):
        """
        Initialize the NOMA data preprocessor
        Args:
            base_path: Path to the directory containing batch_runs
        """
        self.base_path = Path(base_path)
        self.processed_data_path = self.base_path / "noma_dl" / "data" / "processed"
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
        
    def process_run(self, run_dir: Path) -> Dict:
        """Process a single simulation run"""
        # Read files
        h_values = pd.read_csv(run_dir / "h_values.csv")
        static = pd.read_csv(run_dir / "static_pairs.csv")
        balanced = pd.read_csv(run_dir / "balanced_pairs.csv")
        blossom = pd.read_csv(run_dir / "blossom_pairs.csv")
        
        # Extract features
        node_features = self._extract_node_features(h_values)
        edge_index, edge_features = self._create_edge_features(h_values)
        
        # Create labels from different pairing strategies
        labels = {
            'static': self._create_pair_labels(static, h_values.shape[0]),
            'balanced': self._create_pair_labels(balanced, h_values.shape[0]),
            'blossom': self._create_pair_labels(blossom, h_values.shape[0])
        }
        
        return {
            'node_features': node_features,
            'edge_index': edge_index,
            'edge_features': edge_features,
            'labels': labels
        }
    
    def _extract_node_features(self, h_values: pd.DataFrame) -> torch.Tensor:
        """Extract node features from user data"""
        features = [
            'h_linear',
            'h_dB',
            'distance_m',
            'height_m',
            'path_loss_dB',
            'shadowing_dB',
            'rayleigh_fading',
            'LOS_probability',
            'x_coord_m',
            'y_coord_m',
            'distance_3D_m',
            'LOS_status'
        ]
        
        return torch.tensor(h_values[features].values, dtype=torch.float32)
    
    def _create_edge_features(self, h_values: pd.DataFrame) -> Tuple[torch.Tensor, torch.Tensor]:
        """Create edge features for all potential user pairs"""
        N = h_values.shape[0]
        edge_index = []
        edge_features = []
        
        for i in range(N):
            for j in range(i+1, N):
                edge_index.append([i, j])
                
                # Calculate edge features
                h_ratio = h_values.loc[i, 'h_linear'] / h_values.loc[j, 'h_linear']
                distance_diff = abs(h_values.loc[i, 'distance_m'] - h_values.loc[j, 'distance_m'])
                angle_diff = abs(
                    np.arctan2(h_values.loc[i, 'y_coord_m'], h_values.loc[i, 'x_coord_m']) -
                    np.arctan2(h_values.loc[j, 'y_coord_m'], h_values.loc[j, 'x_coord_m'])
                )
                height_diff = abs(h_values.loc[i, 'height_m'] - h_values.loc[j, 'height_m'])
                
                edge_features.append([h_ratio, distance_diff, angle_diff, height_diff])
        
        return (
            torch.tensor(edge_index, dtype=torch.long).t().contiguous(),
            torch.tensor(edge_features, dtype=torch.float32)
        )
    
    def _create_pair_labels(self, pairs_df: pd.DataFrame, num_nodes: int) -> torch.Tensor:
        """Create binary labels for user pairs"""
        N = num_nodes
        labels = torch.zeros((N, N), dtype=torch.float32)
        
        for _, row in pairs_df.iterrows():
            if row['Mode'] == 'NOMA':
                u1, u2 = int(row['User1_ID']), int(row['User2_ID'])
                labels[u1, u2] = labels[u2, u1] = 1.0
        
        return labels
    
    def process_all_runs(self) -> None:
        """Process all simulation runs and save to disk"""
        batch_runs_dir = self.base_path / "batch_runs"
        
        for run_dir in sorted(batch_runs_dir.glob("run_*")):
            try:
                data_dict = self.process_run(run_dir)
                run_id = int(run_dir.name.split('_')[1])
                
                # Save processed data
                torch.save(
                    data_dict,
                    self.processed_data_path / f"processed_run_{run_id:03d}.pt"
                )
                print(f"Processed {run_dir.name}")
            except Exception as e:
                print(f"Error processing {run_dir.name}: {str(e)}")

class NOMADataset(Dataset):
    def __init__(self, processed_dir: str, split: str = 'train',
                 train_ratio: float = 0.7, val_ratio: float = 0.15):
        """
        NOMA Dataset for loading processed data
        Args:
            processed_dir: Directory containing processed .pt files
            split: One of ['train', 'val', 'test']
            train_ratio: Ratio of data for training
            val_ratio: Ratio of data for validation
        """
        super().__init__()
        self.processed_dir = Path(processed_dir)
        self.split = split
        
        # Get all processed files
        self.file_list = sorted(self.processed_dir.glob("processed_run_*.pt"))
        
        # Split indices
        n_files = len(self.file_list)
        indices = np.random.permutation(n_files)
        
        n_train = int(n_files * train_ratio)
        n_val = int(n_files * val_ratio)
        
        if split == 'train':
            self.indices = indices[:n_train]
        elif split == 'val':
            self.indices = indices[n_train:n_train+n_val]
        else:  # test
            self.indices = indices[n_train+n_val:]
    
    def len(self) -> int:
        return len(self.indices)
    
    def get(self, idx: int) -> Data:
        file_idx = self.indices[idx]
        data_dict = torch.load(self.file_list[file_idx])
        
        # Convert to PyG Data object
        data = Data(
            x=data_dict['node_features'],
            edge_index=data_dict['edge_index'],
            edge_attr=data_dict['edge_features'],
            y=data_dict['labels']['blossom']  # Using blossom as ground truth
        )
        
        return data

if __name__ == "__main__":
    # Test the preprocessing pipeline
    base_path = "c:/Users/shail/Developer/MAJOR_PROJECT/codes/04/08/25"
    preprocessor = NOMADataPreprocessor(base_path)
    preprocessor.process_all_runs()
    
    # Test the dataset
    dataset = NOMADataset(
        processed_dir=preprocessor.processed_data_path,
        split='train'
    )
    print(f"Dataset size: {len(dataset)}")
    print(f"Sample data: {dataset[0]}")
