
import os, argparse, json
import numpy as np
import torch
from torch_geometric.data import Data
from data.normalization import Scaler
from models.pairpower_gnn import PairPowerGNN
from utils.metrics import sum_throughput_mbps, noma_rates
from utils.matching import greedy_max_weight_matching
from data.dataset import FEATURE_COLS, angle_diff_rad
from config import CFG

def sic_satisfied(h1, h2, sic_db):
    if h1 <= 0 or h2 <= 0: return False
    return 10*np.log10(h2/h1) >= sic_db

def load_scenario_users(h_values_csv, scaler: Scaler):
    import pandas as pd
    df = pd.read_csv(h_values_csv)
    x = torch.tensor(scaler.transform(df[FEATURE_COLS].values.astype(np.float32)), dtype=torch.float32)
    angles = torch.tensor(df["angle_rad"].values, dtype=torch.float32)
    h_lin = torch.tensor(df["h_linear"].values, dtype=torch.float32)
    return x, angles, h_lin, df

def build_mp_edges(x):
    # split weak/strong by h_dB
    h_idx = FEATURE_COLS.index("h_dB")
    h = x[:, h_idx]
    n = x.size(0)
    idx_sorted = torch.argsort(h)
    weak = idx_sorted[:n//2]; strong = idx_sorted[n//2:]
    from training.train import build_mp_edge_index
    return build_mp_edge_index(x, weak, strong, CFG.MP_TOPOLOGY, CFG.MP_K), weak, strong

def candidate_pairs(weak, strong, h_lin, angles, sic_db, use_angle, min_angle_deg, topk=None):
    n = h_lin.numel()
    h = h_lin.cpu().numpy(); ang = angles.cpu().numpy()
    min_ang = np.deg2rad(min_angle_deg)
    # Preorder strong by gain
    strong_sorted = torch.argsort(h_lin[strong], descending=True)
    strong_order = [strong[i.item()] for i in strong_sorted]
    pairs = []
    for w in weak.tolist():
        # preselect topK strong
        cands = strong_order[:topk] if (topk and topk>0) else strong_order
        for s in cands:
            a,b = (w,s) if h[w]<=h[s] else (s,w)
            if not sic_satisfied(h[a], h[b], sic_db): 
                continue
            if use_angle:
                d = float(angle_diff_rad(ang[w], ang[s]))
                if d < min_ang: 
                    continue
            pairs.append((a,b))
    # unique
    pairs = list(set(pairs))
    return torch.tensor(pairs, dtype=torch.long).t().contiguous() if pairs else torch.zeros((2,0), dtype=torch.long)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", type=str, required=True, help="path to best_model.pt")
    ap.add_argument("--scaler", type=str, required=True, help="path to feature_scaler.json")
    ap.add_argument("--h_values_csv", type=str, required=True, help="scenario h_values.csv")
    ap.add_argument("--out_csv", type=str, default="predicted_pairs.csv")
    args = ap.parse_args()

    device = torch.device(CFG.DEVICE if torch.cuda.is_available() and CFG.DEVICE=="cuda" else "cpu")

    scaler = Scaler.load(args.scaler)
    x, angles, h_lin, df = load_scenario_users(args.h_values_csv, scaler)
    mp_edges, weak, strong = build_mp_edges(x)

    model = PairPowerGNN(
        in_channels=len(FEATURE_COLS),
        hidden=CFG.HIDDEN_DIM,
        out_channels=CFG.OUT_DIM,
        num_layers=CFG.NUM_LAYERS,
        dropout=CFG.DROPOUT
    ).to(device)
    ckpt = torch.load(args.ckpt, map_location=device)
    model.load_state_dict(ckpt["model_state"])

    x = x.to(device); mp_edges = mp_edges.to(device)

    cand = candidate_pairs(
        weak, strong, h_lin, angles,
        sic_db=CFG.SIC_THRESHOLD_DB,
        use_angle=CFG.USE_ANGLE_GUARD, min_angle_deg=CFG.MIN_ANGLE_DEG,
        topk=CFG.TOPK_CANDIDATES_PER_NODE
    )
    if cand.numel() == 0:
        print("No feasible candidates found."); return

    with torch.no_grad():
        pos_logit, pos_rsum_pred, pos_alpha_pred = model(x, mp_edges, cand.to(device))
        scores = pos_logit.sigmoid().cpu().numpy()
        rsum_pred = pos_rsum_pred.cpu().numpy()
        alpha_pred = pos_alpha_pred.cpu().numpy()

    # Build weighted edges for matching using scores (or rsum_pred as weights)
    edges = []
    for i in range(cand.size(1)):
        u = int(cand[0,i].item()); v = int(cand[1,i].item())
        w = float(scores[i])  # could use rsum_pred[i] as alternative weight
        edges.append((u,v,w))

    chosen = greedy_max_weight_matching(n_nodes=x.size(0), edges=edges)

    # Compute throughput with predicted alpha
    pairs_alpha = [(u,v,float(alpha_pred[i])) for i,(uu,vv,_) in enumerate(edges) if (uu,vv,_) in chosen]
    # Note: mapping edge index back is simplified here; recompute alpha for chosen:
    alpha_map = {}
    for i,(uu,vv,ww) in enumerate(edges):
        if (uu,vv,ww) in chosen:
            alpha_map[(uu,vv)] = float(alpha_pred[i])
    pairs_alpha = [(u,v,alpha_map[(u,v)]) for (u,v,w) in chosen]

    thr = sum_throughput_mbps(
        pairs_alpha, h_lin.cpu().numpy(), CFG.TOTAL_POWER, CFG.NOISE_POWER, CFG.BANDWIDTH_HZ
    )
    print(f"Chosen pairs: {len(chosen)}  | Estimated total throughput: {thr:.2f} Mbps")

    # Save CSV
    import pandas as pd
    rows = []
    for (u,v,w) in chosen:
        a = float(alpha_map[(u,v)])
        P1 = CFG.TOTAL_POWER * a; P2 = CFG.TOTAL_POWER - P1
        R1,R2,Rsum = noma_rates(float(h_lin[u]), float(h_lin[v]), P1, P2, CFG.NOISE_POWER)
        rows.append({"User1_ID": int(u), "User2_ID": int(v), "alpha": a, "R_sum_bitsHz": Rsum, "score": w})
    pd.DataFrame(rows).to_csv(args.out_csv, index=False)
    print(f"Saved predicted pairs to {args.out_csv}")

if __name__ == "__main__":
    main()
