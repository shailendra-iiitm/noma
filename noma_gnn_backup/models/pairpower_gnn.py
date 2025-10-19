
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv

class PairPowerGNN(nn.Module):
    """
    GraphSAGE encoder + multi-head edge decoders:
      - edge_logit: pairing existence (BCEWithLogits)
      - edge_rsum:  predicted sum-rate (regression)
      - edge_alpha: predicted weak-user power split (regression in (0,1))
    """
    def __init__(self, in_channels, hidden=128, out_channels=128, num_layers=3, dropout=0.2):
        super().__init__()
        assert num_layers >= 2
        self.dropout = nn.Dropout(dropout)
        self.convs = nn.ModuleList()
        self.convs.append(SAGEConv(in_channels, hidden))
        for _ in range(num_layers-2):
            self.convs.append(SAGEConv(hidden, hidden))
        self.convs.append(SAGEConv(hidden, out_channels))

        edge_in = 2*out_channels

        self.edge_mlp_logit = nn.Sequential(
            nn.Linear(edge_in, out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(out_channels, 1)
        )
        self.edge_mlp_rsum = nn.Sequential(
            nn.Linear(edge_in, out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(out_channels, 1)
        )
        self.edge_mlp_alpha = nn.Sequential(
            nn.Linear(edge_in, out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(out_channels, 1),
            nn.Sigmoid()
        )

    def encode(self, x, edge_index):
        z = x
        for i, conv in enumerate(self.convs):
            z = conv(z, edge_index)
            if i != len(self.convs)-1:
                z = F.relu(z, inplace=True)
                z = self.dropout(z)
        return z

    def _edge_cat(self, z, edge_index):
        src, dst = edge_index
        return torch.cat([z[src], z[dst]], dim=-1)

    def decode_all(self, z, edge_index):
        h = self._edge_cat(z, edge_index)
        logit = self.edge_mlp_logit(h).view(-1)
        rsum = self.edge_mlp_rsum(h).view(-1)
        alpha = self.edge_mlp_alpha(h).view(-1)
        return logit, rsum, alpha

    def forward(self, x, mp_edge_index, edge_index_eval):
        z = self.encode(x, mp_edge_index)
        return self.decode_all(z, edge_index_eval)
