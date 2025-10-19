
import os, argparse, random
import numpy as np
import torch
from torch_geometric.loader import DataLoader
from torch_geometric.utils import to_undirected, dense_to_sparse
from sklearn.metrics import roc_auc_score

from models.pairpower_gnn import PairPowerGNN
from utils.metrics import noma_rates
from training.losses import multitask_loss
from data.dataset import build_graphs_from_merged, FEATURE_COLS
from data.normalization import Scaler
from config import CFG

def set_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)

def build_mp_edge_index(x, weak_idx, strong_idx, kind="bipartite_knn", k=8):
    """
    Build message passing graph edges.
    - bipartite_full: connect all weak<->strong
    - bipartite_knn: connect each weak to k strongest (by h_dB in features) & vice versa
    - knn: KNN over all users in feature space (fallback)
    """
    n = x.shape[0]
    if kind == "bipartite_full":
        ws, ss = [], []
        for w in weak_idx:
            for s in strong_idx:
                ws.append(w); ss.append(s)
        edge = torch.tensor([ws+ss, ss+ws], dtype=torch.long)  # undirected
        return edge
    elif kind == "bipartite_knn":
        # feature index of h_dB in FEATURE_COLS
        h_idx = FEATURE_COLS.index("h_dB")
        h = x[:, h_idx]
        # connect each weak to k strongest (highest h)
        strong_sorted = torch.argsort(h[strong_idx], descending=True)
        strong_order = [strong_idx[i.item()] for i in strong_sorted]

        ws, ss = [], []
        k_eff = min(k, len(strong_order))
        for w in weak_idx:
            for s in strong_order[:k_eff]:
                ws.append(w); ss.append(s)
        # also each strong to k weakest
        weak_sorted = torch.argsort(h[weak_idx], descending=False)
        weak_order = [weak_idx[i.item()] for i in weak_sorted]
        k_eff2 = min(k, len(weak_order))
        for s in strong_idx:
            for w in weak_order[:k_eff2]:
                ws.append(w); ss.append(s)

        edge = torch.tensor([ws+ss, ss+ws], dtype=torch.long)  # undirected
        return edge
    else:
        # simple fully connected (heavy) as fallback
        A = torch.ones((n,n), dtype=torch.bool)
        A.fill_diagonal_(False)
        ei = dense_to_sparse(A)[0]
        return ei

def generate_negatives(data, sic_db=8.0, use_angle=True, min_angle_deg=25.0, ratio=1.0):
    """
    Create negative edges: SIC-feasible but not in positives.
    Returns neg_edge_index [2, E_neg]
    """
    import numpy as np
    pos = set([(int(a), int(b)) for a,b in data.edge_index_pos.t().tolist()])
    n = data.num_nodes
    h = data.h_linear.cpu().numpy()
    ang = data.angles.cpu().numpy()
    min_ang = np.deg2rad(min_angle_deg)
    # split by median h_dB for weak/strong
    h_db = data.h_db.cpu().numpy()
    idx_sorted = np.argsort(h_db)
    weak = idx_sorted[:n//2]; strong = idx_sorted[n//2:]

    candidates = []
    for w in weak:
        for s in strong:
            h1 = min(h[w], h[s]); h2 = max(h[w], h[s])
            if h1 <= 0 or h2 <= 0: 
                continue
            if 10*np.log10(h2/h1) < sic_db: 
                continue
            if use_angle:
                # angular guard
                d = np.abs(ang[w]-ang[s]) % (2*np.pi)
                d = min(d, 2*np.pi - d)
                if d < min_ang: 
                    continue
            a,b = (w,s) if h[w]<=h[s] else (s,w)
            if (a,b) in pos:
                continue
            candidates.append((a,b))

    # sample negatives ~ ratio * num_pos
    num_pos = data.edge_index_pos.size(1)
    if len(candidates) == 0:
        return data.edge_index_pos[:, :0]  # empty
    np.random.shuffle(candidates)
    pick = candidates[:int(max(1, ratio*num_pos))]
    ne = torch.tensor(pick, dtype=torch.long).t().contiguous()
    return ne

def train_one_epoch(model, loader, optimizer, device, cfg):
    model.train()
    losses = []
    for data in loader:
        data = data.to(device)
        # split weak/strong by median h_db
        h_db = data.h_db
        idx_sorted = torch.argsort(h_db)
        weak = idx_sorted[:data.num_nodes//2]
        strong = idx_sorted[data.num_nodes//2:]

        mp_edge_index = build_mp_edge_index(data.x, weak, strong, cfg.MP_TOPOLOGY, cfg.MP_K).to(device)

        neg_edge_index = generate_negatives(data, cfg.SIC_THRESHOLD_DB, cfg.USE_ANGLE_GUARD, cfg.MIN_ANGLE_DEG, ratio=1.0).to(device)
        if neg_edge_index.numel() == 0:
            continue

        pos_logit, pos_rsum_pred, pos_alpha_pred = model(data.x, mp_edge_index, data.edge_index_pos.to(device))
        neg_logit, _, _ = model(data.x, mp_edge_index, neg_edge_index)

        loss, parts = multitask_loss(
            pos_logit, neg_logit, 
            pos_rsum_pred, pos_alpha_pred,
            data.y_pos_rsum.to(device), data.y_pos_alpha.to(device),
            cfg.LAMBDA_BCE, cfg.LAMBDA_RSUM, cfg.LAMBDA_ALPHA
        )

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    return float(np.mean(losses)) if losses else 0.0

@torch.no_grad()
def evaluate(model, loader, device, cfg):
    model.eval()
    all_scores, all_labels = [], []
    mae_rsum, mae_alpha, n_batches = 0.0, 0.0, 0
    for data in loader:
        data = data.to(device)
        h_db = data.h_db
        idx_sorted = torch.argsort(h_db)
        weak = idx_sorted[:data.num_nodes//2]
        strong = idx_sorted[data.num_nodes//2:]
        mp_edge_index = build_mp_edge_index(data.x, weak, strong, cfg.MP_TOPOLOGY, cfg.MP_K).to(device)

        # sample some negatives for eval
        neg_edge_index = generate_negatives(data, cfg.SIC_THRESHOLD_DB, cfg.USE_ANGLE_GUARD, cfg.MIN_ANGLE_DEG, ratio=1.0).to(device)
        if neg_edge_index.numel() == 0:
            continue

        pos_logit, pos_rsum_pred, pos_alpha_pred = model(data.x, mp_edge_index, data.edge_index_pos.to(device))
        neg_logit, _, _ = model(data.x, mp_edge_index, neg_edge_index)

        pos_scores = pos_logit.sigmoid().cpu().numpy()
        neg_scores = neg_logit.sigmoid().cpu().numpy()
        scores = np.concatenate([pos_scores, neg_scores])
        labels = np.concatenate([np.ones_like(pos_scores), np.zeros_like(neg_scores)])
        all_scores.append(scores); all_labels.append(labels)

        # regression metrics
        mae_rsum += torch.mean(torch.abs(pos_rsum_pred - data.y_pos_rsum.to(device))).item()
        mae_alpha += torch.mean(torch.abs(pos_alpha_pred - data.y_pos_alpha.to(device))).item()
        n_batches += 1

    if len(all_scores)==0:
        return float('nan'), float('nan'), float('nan')
    scores = np.concatenate(all_scores); labels = np.concatenate(all_labels)
    auc = roc_auc_score(labels, scores)
    mae_r = mae_rsum / max(1,n_batches)
    mae_a = mae_alpha / max(1,n_batches)
    return auc, mae_r, mae_a

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--users_csv", type=str, required=True, help="merged_h_values.csv")
    ap.add_argument("--pairs_csv", type=str, required=True, help="merged_pairs.csv")
    ap.add_argument("--out_dir", type=str, default="./checkpoints")
    ap.add_argument("--scaler_path", type=str, default="./checkpoints/feature_scaler.json")
    ap.add_argument("--epochs", type=int, default=CFG.EPOCHS)
    ap.add_argument("--batch_size", type=int, default=CFG.BATCH_SIZE)
    ap.add_argument("--device", type=str, default=CFG.DEVICE)
    ap.add_argument("--resume_ckpt", type=str, default="", help="path to a .pt to warm-start from")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    set_seed(CFG.SEED)

    graphs = build_graphs_from_merged(
        args.users_csv, args.pairs_csv,
        sic_db=CFG.SIC_THRESHOLD_DB,
        use_angle_guard=CFG.USE_ANGLE_GUARD,
        min_angle_deg=CFG.MIN_ANGLE_DEG,
        scaler_outpath=args.scaler_path
    )

    # split
    n = len(graphs)
    n_train = int(0.7*n); n_val = int(0.15*n); n_test = n - n_train - n_val
    train_set = graphs[:n_train]
    val_set   = graphs[n_train:n_train+n_val]
    test_set  = graphs[n_train+n_val:]

    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True)
    val_loader   = DataLoader(val_set, batch_size=1, shuffle=False)
    test_loader  = DataLoader(test_set, batch_size=1, shuffle=False)

    device = torch.device(args.device if torch.cuda.is_available() and args.device=="cuda" else "cpu")

    model = PairPowerGNN(
        in_channels=len(FEATURE_COLS),
        hidden=CFG.HIDDEN_DIM,
        out_channels=CFG.OUT_DIM,
        num_layers=CFG.NUM_LAYERS,
        dropout=CFG.DROPOUT
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=CFG.LR, weight_decay=CFG.WEIGHT_DECAY)
    # resume / warm-start handling
    start_epoch = 1
    best_auc = -1.0
    ckpt_path = os.path.join(args.out_dir, "best_model.pt")

    if args.resume_ckpt:
        print(f"[RESUME] Loading weights from {args.resume_ckpt}")
        ckpt = torch.load(args.resume_ckpt, map_location=device)
        model.load_state_dict(ckpt["model_state"])
        if "best_auc" in ckpt:
            best_auc = ckpt["best_auc"]
    for epoch in range(1, args.epochs+1):
        tl = train_one_epoch(model, train_loader, opt, device, CFG)
        auc, mae_r, mae_a = evaluate(model, val_loader, device, CFG)
        print(f"Epoch {epoch:03d} | TrainLoss {tl:.4f} | ValAUC {auc:.4f} | Val MAE(Rsum) {mae_r:.4f} | Val MAE(alpha) {mae_a:.4f}")
        if auc == auc and auc > best_auc:
            best_auc = auc
            torch.save({
                "model_state": model.state_dict(),
                "cfg": CFG.__dict__,
                "best_auc": best_auc
            }, ckpt_path)
            print(f"Saved best to {ckpt_path}")

    # final test
    ckpt = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    auc, mae_r, mae_a = evaluate(model, test_loader, device, CFG)
    print(f"[TEST] AUC={auc:.4f}  MAE(Rsum)={mae_r:.4f}  MAE(alpha)={mae_a:.4f}")
    print(f"Best checkpoint: {ckpt_path}")

if __name__ == "__main__":
    main()
