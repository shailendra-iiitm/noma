
"""
Prepare PyG graphs from merged CSVs and save as a .pt file for quick loading.
"""
import os, argparse, torch
from data.dataset import build_graphs_from_merged

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--users_csv", required=True, help="merged_h_values.csv")
    ap.add_argument("--pairs_csv", required=True, help="merged_pairs.csv")
    ap.add_argument("--out_pt", default="bpf_graph_dataset.pt")
    ap.add_argument("--scaler_out", default="feature_scaler.json")
    args = ap.parse_args()

    graphs = build_graphs_from_merged(
        args.users_csv, args.pairs_csv,
        sic_db=8.0, use_angle_guard=True, min_angle_deg=25.0,
        scaler_outpath=args.scaler_out
    )
    torch.save(graphs, args.out_pt)
    print(f"✅ Saved {len(graphs)} graphs to {args.out_pt}")
    print(f"✅ Saved scaler to {args.scaler_out}")

if __name__ == "__main__":
    main()
