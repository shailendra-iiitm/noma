
# NOMA-GNN: Pairing + Power Allocation with Graph Neural Networks

This project trains a GraphSAGE-based GNN to **predict NOMA user pairing** and **power allocation (alpha)** from 3GPP-derived CSI features. It also supports **fast inference** with greedy matching and includes throughput estimation.

## Directory
- `config.py` — global hyperparameters and physics constants.
- `data/`
  - `dataset.py` — build PyG graphs from `merged_h_values.csv` and `merged_pairs.csv`.
  - `normalization.py` — z-score scaler (save/load).
- `models/`
  - `pairpower_gnn.py` — GraphSAGE encoder with three edge heads: existence (logit), sum-rate, alpha.
- `training/`
  - `train.py` — multi-task training (BCE + MAE on Rsum and alpha) with hard negative sampling.
  - `losses.py` — multi-task loss function.
- `inference/`
  - `infer_pairing.py` — load checkpoint, build MP graph, score candidates, greedy match, output CSV and throughput.
- `utils/`
  - `matching.py` — fast greedy max-weight matching.
  - `metrics.py` — NOMA rate/throughput helpers.
- `scripts/`
  - `prepare_data.py` — convert merged CSVs to a .pt list of PyG `Data` graphs and save a feature scaler.

## Data Expectations
Use your existing pipeline to produce:
- `merged_h_values.csv` — concatenated user records with columns: `Graph_ID, User_ID, distance_m, angle_rad, path_loss_dB, shadowing_dB, rayleigh_fading, h_linear, h_dB, ...`.
- `merged_pairs.csv` — concatenated clustering results with columns including `Graph_ID, User1_ID, User2_ID, h1, h2, P1, P2, R1_bitsHz, R2_bitsHz, R_sum_bitsHz, Mode`.

## Quickstart

```bash
# 1) Prepare graphs + scaler
python -m scripts.prepare_data --users_csv merged_h_values.csv --pairs_csv merged_pairs.csv --out_pt dataset.pt --scaler_out feature_scaler.json

# 2) Train
python -m training.train --users_csv merged_h_values.csv --pairs_csv merged_pairs.csv --out_dir checkpoints --scaler_path checkpoints/feature_scaler.json

# 3) Inference on a new scenario (h_values.csv from your simulator)
python -m inference.infer_pairing --ckpt checkpoints/best_model.pt --scaler checkpoints/feature_scaler.json --h_values_csv path/to/h_values.csv --out_csv predicted_pairs.csv
```

## Verify SIC feasibility of predicted pairs

After running inference that outputs a CSV like `predicted_pairs_relaxed.csv`, you can verify whether each predicted pair satisfies the SIC criterion |h1_dB − h2_dB| ≥ 8 dB (configurable):

```bash
python -m scripts.verify_sic_pairs --h-values h_values.csv --pairs predicted_pairs_relaxed.csv --threshold-db 8 --out-report predicted_pairs_relaxed_sic_report.csv
```

The script prints a summary and writes a detailed per-pair report with columns: h1_dB, h2_dB, h_diff_dB, sic_ok, missing_h.

## Notes
- The GNN is trained with **hard negatives** that are **SIC-feasible but not selected** in ground-truth matching.
- Inference constructs a **bipartite KNN** message-passing graph so nodes aggregate information from plausible partners.
- Matching uses a fast greedy algorithm by default; you can replace it with Blossom/Hungarian if needed.
- The model jointly predicts **pair existence**, **sum-rate**, and **power split alpha** for positives — enabling end-to-end learned power allocation.
