import torch
import torch.nn as nn

class NOMANet(nn.Module):
    """Neural Network architecture for NOMA user pairing"""
    
    def __init__(self, input_dim=10, hidden_dim=64, output_dim=1):
        super(NOMANet, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.3),
            
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.3),
            
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, x):
        return self.network(x)
