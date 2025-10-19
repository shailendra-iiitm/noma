
import os
import pandas as pd
import numpy as np
import torch
from torch_geometric.data import Data
from typing import List, Tuple, Dict, Optional
from .normalization import Scaler


FEATURE_COLS = ["distance_m", "path_loss_dB", "shadowing_dB", "rayleigh_fading", "h_dB"]
ANGLE_COL = "angle_rad"
USER_ID_COL = "User_ID"

def sic_satisfied(h1: float, h2: float, sic_db: float) -> bool:
    if h1 <= 0 or h2 <= 0:
        return False
    return 10.0 * np.log10(h2 / h1) >= sic_db

def angle_diff_rad(a, b):
    d = np.abs(a - b) % (2*np.pi)
    return np.minimum(d, 2*np.pi - d)

def build_graphs_from_merged(
    users_csv: str,
    pairs_csv: str,
    sic_db: float = 8.0,
    use_angle_guard: bool = True,
    min_angle_deg: float = 25.0,
    scaler_outpath: Optional[str] = None
) -> List[Data]:
    """
    Build a list of PyG Data graphs from merged CSVs.
    Each Data contains:
      - x: [N, F] node features
      - edge_index_pos: positive edges (labels y=1) as attribute
      - y_pos_rsum: optimal R_sum for pos edges
      - y_pos_alpha: optimal power split alpha = P1/(P1+P2) for pos edges
      - aux dicts saved in data for inference (user ids, angles)
    """
    users = pd.read_csv(users_csv)
    pairs = pd.read_csv(pairs_csv)

    # Fit scaler on users FEATURES (global across all graphs)
    scaler = Scaler().fit(users[FEATURE_COLS].values.astype(np.float32))
    if scaler_outpath:
        scaler.save(scaler_outpath)

    graphs: List[Data] = []
    min_angle_rad = np.deg2rad(min_angle_deg)

    for gid, ug in users.groupby("Graph_ID"):
        pg = pairs[pairs["Graph_ID"] == gid]

        # Node features
        x_raw = ug[FEATURE_COLS].values.astype(np.float32)
        x = torch.tensor(scaler.transform(x_raw), dtype=torch.float32)

        # Index mapping for stable node ids 0..N-1
        uid_to_idx = {uid: i for i, uid in enumerate(ug[USER_ID_COL].tolist())}

        # Positive edges (NOMA) from pairs CSV
        pos_df = pg[pg["Mode"] == "NOMA"].copy()
        if len(pos_df) == 0:
            # Skip empty graph
            continue
        # Ensure consistent ordering (weak, strong): h1<=h2
        h1 = pos_df["h1"].values
        h2 = pos_df["h2"].values
        u1 = pos_df["User1_ID"].values
        u2 = pos_df["User2_ID"].values
        # Map to local indices
        a_idx = np.array([uid_to_idx[u] for u in u1], dtype=np.int64)
        b_idx = np.array([uid_to_idx[u] for u in u2], dtype=np.int64)

        edge_index_pos = torch.tensor(np.vstack([a_idx, b_idx]), dtype=torch.long)

        # Labels for regression
        rsum = pos_df["R_sum_bitsHz"].values.astype(np.float32)  # bits/Hz
        P1 = pos_df["P1"].values.astype(np.float32)
        P2 = pos_df["P2"].values.astype(np.float32)
        denom = (P1 + P2 + 1e-12)
        alpha = (P1 / denom).astype(np.float32)

        y_pos_rsum = torch.tensor(rsum, dtype=torch.float32)     # [E_pos]
        y_pos_alpha = torch.tensor(alpha, dtype=torch.float32)   # [E_pos]

        data = Data(x=x)
        data.num_nodes = x.shape[0]
        data.edge_index_pos = edge_index_pos
        data.y_pos_rsum = y_pos_rsum
        data.y_pos_alpha = y_pos_alpha

        # Save auxiliary info needed for candidate generation
        data.user_ids = torch.tensor(ug[USER_ID_COL].values, dtype=torch.long)
        data.h_linear = torch.tensor(ug["h_linear"].values, dtype=torch.float32)
        data.h_db = torch.tensor(ug["h_dB"].values, dtype=torch.float32)
        data.angles = torch.tensor(ug[ANGLE_COL].values, dtype=torch.float32)
        data.graph_id = str(gid)

        graphs.append(data)

    return graphs
