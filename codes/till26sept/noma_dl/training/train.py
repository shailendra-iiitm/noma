import os
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.loader import DataLoader
from pathlib import Path
from typing import Dict, Any, Tuple

from models.gnn import NOMAGNN, NOMAGNNWithPerformance
from utils.data_loader import NOMADataset

class Trainer:
    def __init__(self, config_path: str):
        """
        Initialize the NOMA GNN trainer
        Args:
            config_path: Path to the config YAML file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.device = torch.device(self.config['system']['device'])
        torch.manual_seed(self.config['system']['seed'])
        
        self._setup_data()
        self._setup_model()
        self._setup_training()
    
    def _setup_data(self):
        """Setup data loaders"""
        data_config = self.config['data']
        
        # Create datasets
        processed_dir = Path("data/processed")
        self.train_dataset = NOMADataset(
            processed_dir=processed_dir,
            split='train',
            train_ratio=data_config['train_split'],
            val_ratio=data_config['val_split']
        )
        self.val_dataset = NOMADataset(
            processed_dir=processed_dir,
            split='val',
            train_ratio=data_config['train_split'],
            val_ratio=data_config['val_split']
        )
        self.test_dataset = NOMADataset(
            processed_dir=processed_dir,
            split='test',
            train_ratio=data_config['train_split'],
            val_ratio=data_config['val_split']
        )
        
        # Create data loaders
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=data_config['batch_size'],
            shuffle=True,
            num_workers=data_config['num_workers']
        )
        self.val_loader = DataLoader(
            self.val_dataset,
            batch_size=data_config['batch_size'],
            shuffle=False,
            num_workers=data_config['num_workers']
        )
        self.test_loader = DataLoader(
            self.test_dataset,
            batch_size=data_config['batch_size'],
            shuffle=False,
            num_workers=data_config['num_workers']
        )
    
    def _setup_model(self):
        """Setup the GNN model"""
        model_config = self.config['model']
        
        self.model = NOMAGNNWithPerformance(
            node_dim=model_config['node_features'],
            edge_dim=model_config['edge_features'],
            hidden_dim=model_config['hidden_dim'],
            num_layers=model_config['num_layers'],
            dropout=model_config['dropout']
        ).to(self.device)
        
        # Loss functions
        self.pair_criterion = nn.BCELoss()
        self.performance_criterion = nn.MSELoss()
        
        # Optimizer
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=model_config['learning_rate']
        )
    
    def _setup_training(self):
        """Setup training parameters"""
        self.epochs = self.config['training']['epochs']
        self.patience = self.config['training']['patience']
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        
        # Create checkpoint directory
        self.checkpoint_dir = Path(self.config['training']['checkpoint_dir'])
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def train_epoch(self) -> Dict[str, float]:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        pair_losses = 0
        perf_losses = 0
        
        for batch in self.train_loader:
            batch = batch.to(self.device)
            self.optimizer.zero_grad()
            
            # Forward pass
            pair_pred, performance = self.model(batch)
            
            # Calculate losses
            pair_loss = self.pair_criterion(pair_pred, batch.y)
            perf_loss = self.performance_criterion(
                performance,
                batch.performance_metrics
            )
            loss = pair_loss + perf_loss
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            # Update metrics
            total_loss += loss.item()
            pair_losses += pair_loss.item()
            perf_losses += perf_loss.item()
        
        return {
            'total_loss': total_loss / len(self.train_loader),
            'pair_loss': pair_losses / len(self.train_loader),
            'perf_loss': perf_losses / len(self.train_loader)
        }
    
    def validate(self) -> Dict[str, float]:
        """Validate the model"""
        self.model.eval()
        total_loss = 0
        pair_losses = 0
        perf_losses = 0
        
        with torch.no_grad():
            for batch in self.val_loader:
                batch = batch.to(self.device)
                
                # Forward pass
                pair_pred, performance = self.model(batch)
                
                # Calculate losses
                pair_loss = self.pair_criterion(pair_pred, batch.y)
                perf_loss = self.performance_criterion(
                    performance,
                    batch.performance_metrics
                )
                loss = pair_loss + perf_loss
                
                # Update metrics
                total_loss += loss.item()
                pair_losses += pair_loss.item()
                perf_losses += perf_loss.item()
        
        return {
            'total_loss': total_loss / len(self.val_loader),
            'pair_loss': pair_losses / len(self.val_loader),
            'perf_loss': perf_losses / len(self.val_loader)
        }
    
    def train(self) -> Dict[str, Any]:
        """Main training loop"""
        train_losses = []
        val_losses = []
        
        for epoch in range(self.epochs):
            # Train
            train_metrics = self.train_epoch()
            train_losses.append(train_metrics)
            
            # Validate
            val_metrics = self.validate()
            val_losses.append(val_metrics)
            
            # Print progress
            if epoch % self.config['training']['log_interval'] == 0:
                print(f"Epoch {epoch}:")
                print(f"  Train Loss: {train_metrics['total_loss']:.4f}")
                print(f"  Val Loss: {val_metrics['total_loss']:.4f}")
            
            # Check early stopping
            if val_metrics['total_loss'] < self.best_val_loss:
                self.best_val_loss = val_metrics['total_loss']
                self.patience_counter = 0
                
                # Save checkpoint
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'train_loss': train_metrics['total_loss'],
                    'val_loss': val_metrics['total_loss']
                }, self.checkpoint_dir / 'best_model.pt')
            else:
                self.patience_counter += 1
                if self.patience_counter >= self.patience:
                    print("Early stopping!")
                    break
        
        return {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'best_val_loss': self.best_val_loss
        }
    
    def test(self) -> Dict[str, float]:
        """Test the model on the test set"""
        # Load best model
        checkpoint = torch.load(self.checkpoint_dir / 'best_model.pt')
        self.model.load_state_dict(checkpoint['model_state_dict'])
        
        self.model.eval()
        total_loss = 0
        pair_losses = 0
        perf_losses = 0
        
        predictions = []
        true_labels = []
        
        with torch.no_grad():
            for batch in self.test_loader:
                batch = batch.to(self.device)
                
                # Forward pass
                pair_pred, performance = self.model(batch)
                
                # Calculate losses
                pair_loss = self.pair_criterion(pair_pred, batch.y)
                perf_loss = self.performance_criterion(
                    performance,
                    batch.performance_metrics
                )
                loss = pair_loss + perf_loss
                
                # Update metrics
                total_loss += loss.item()
                pair_losses += pair_loss.item()
                perf_losses += perf_loss.item()
                
                # Store predictions
                predictions.append(pair_pred.cpu())
                true_labels.append(batch.y.cpu())
        
        # Calculate metrics
        predictions = torch.cat(predictions)
        true_labels = torch.cat(true_labels)
        
        return {
            'total_loss': total_loss / len(self.test_loader),
            'pair_loss': pair_losses / len(self.test_loader),
            'perf_loss': perf_losses / len(self.test_loader),
            'predictions': predictions,
            'true_labels': true_labels
        }

if __name__ == "__main__":
    # Train the model
    trainer = Trainer("configs/model_config.yaml")
    training_results = trainer.train()
    
    # Test the model
    test_results = trainer.test()
    
    print("\nTest Results:")
    print(f"Total Loss: {test_results['total_loss']:.4f}")
    print(f"Pair Loss: {test_results['pair_loss']:.4f}")
    print(f"Performance Loss: {test_results['perf_loss']:.4f}")
