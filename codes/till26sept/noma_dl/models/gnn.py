import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv, global_mean_pool
from torch_geometric.nn import MessagePassing
from typing import Optional, Tuple

class EdgeConv(MessagePassing):
    def __init__(self, node_dim: int, edge_dim: int, out_dim: int):
        super().__init__(aggr='add')
        self.node_mlp = nn.Sequential(
            nn.Linear(2 * node_dim + edge_dim, out_dim),
            nn.ReLU(),
            nn.Linear(out_dim, out_dim)
        )
        
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_attr: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index, x=x, edge_attr=edge_attr)
    
    def message(self, x_i: torch.Tensor, x_j: torch.Tensor,
                edge_attr: torch.Tensor) -> torch.Tensor:
        # Concatenate node features and edge features
        tmp = torch.cat([x_i, x_j, edge_attr], dim=1)
        return self.node_mlp(tmp)

class NOMAGNN(nn.Module):
    def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int,
                 num_layers: int, dropout: float = 0.1):
        super().__init__()
        self.num_layers = num_layers
        
        # Initial node embedding
        self.node_embedding = nn.Linear(node_dim, hidden_dim)
        
        # Edge embedding
        self.edge_embedding = nn.Linear(edge_dim, hidden_dim)
        
        # Graph convolution layers
        self.conv_layers = nn.ModuleList([
            EdgeConv(hidden_dim, hidden_dim, hidden_dim)
            for _ in range(num_layers)
        ])
        
        # Edge prediction layers
        self.edge_pred = nn.Sequential(
            nn.Linear(2 * hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, data) -> torch.Tensor:
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        
        # Initial embeddings
        x = self.node_embedding(x)
        edge_attr = self.edge_embedding(edge_attr)
        
        # Graph convolution layers
        for conv in self.conv_layers:
            x_new = conv(x, edge_index, edge_attr)
            x = F.relu(x_new) + x  # Residual connection
            x = self.dropout(x)
        
        # Edge prediction
        row, col = edge_index
        edge_features = torch.cat([x[row], x[col]], dim=1)
        pred = self.edge_pred(edge_features)
        
        return torch.sigmoid(pred)
    
    def get_attention_weights(self, data) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get attention weights for visualization"""
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        
        # Initial embeddings
        x = self.node_embedding(x)
        edge_attr = self.edge_embedding(edge_attr)
        
        attention_weights = []
        node_embeddings = []
        
        # Store intermediate attention weights
        for conv in self.conv_layers:
            x_new = conv(x, edge_index, edge_attr)
            attention = F.cosine_similarity(x[edge_index[0]], x[edge_index[1]], dim=1)
            attention_weights.append(attention)
            node_embeddings.append(x.clone())
            x = F.relu(x_new) + x
            x = self.dropout(x)
        
        return torch.stack(attention_weights), torch.stack(node_embeddings)

class NOMAGNNWithPerformance(NOMAGNN):
    def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int,
                 num_layers: int, dropout: float = 0.1):
        super().__init__(node_dim, edge_dim, hidden_dim, num_layers, dropout)
        
        # Additional layers for performance prediction
        self.performance_pred = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 2)  # Predict throughput and SINR
        )
        
    def forward(self, data) -> Tuple[torch.Tensor, torch.Tensor]:
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        
        # Initial embeddings
        x = self.node_embedding(x)
        edge_attr = self.edge_embedding(edge_attr)
        
        # Graph convolution layers
        for conv in self.conv_layers:
            x_new = conv(x, edge_index, edge_attr)
            x = F.relu(x_new) + x
            x = self.dropout(x)
        
        # Edge prediction
        row, col = edge_index
        edge_features = torch.cat([x[row], x[col]], dim=1)
        pair_pred = torch.sigmoid(self.edge_pred(edge_features))
        
        # Performance prediction
        graph_embedding = global_mean_pool(x, batch=data.batch)
        performance = self.performance_pred(graph_embedding)
        
        return pair_pred, performance
