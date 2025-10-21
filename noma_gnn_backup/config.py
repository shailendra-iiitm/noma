
"""
Global configuration for NOMA-GNN.
Edit these values or override via CLI args.
"""
from dataclasses import dataclass

@dataclass
class Config:
    # Physics / system
    TOTAL_POWER: float = 1.0
    NOISE_POWER: float = 1e-9
    SIC_THRESHOLD_DB: float = 8.0
    BANDWIDTH_HZ: float = 20e6

    # Graph/message passing
    MP_TOPOLOGY: str = "bipartite_knn"   # ["bipartite_full", "bipartite_knn", "knn"]
    MP_K: int = 8                         # neighbors per node for MP graph (if *_knn)

    # Candidate generation
    USE_ANGLE_GUARD: bool = True
    MIN_ANGLE_DEG: float = 25.0
    TOPK_CANDIDATES_PER_NODE: int = 2000    # pre-prune candidates per node before scoring (None for all feasible)

    # Model
    IN_CHANNELS: int = 5                  # distance_m, path_loss_dB, shadowing_dB, rayleigh_fading, h_dB
    HIDDEN_DIM: int = 128
    OUT_DIM: int = 128
    NUM_LAYERS: int = 3
    DROPOUT: float = 0.2

    # Training
    LR: float = 1e-3
    WEIGHT_DECAY: float = 1e-4
    EPOCHS: int = 60
    BATCH_SIZE: int = 2
    SEED: int = 42
    DEVICE: str = "cuda"    # "cuda" or "cpu"

    # Loss weights
    LAMBDA_BCE: float = 1.0     # pair existence
    LAMBDA_RSUM: float = 0.5    # sum-rate regression
    LAMBDA_ALPHA: float = 0.5   # power split regression

CFG = Config()
