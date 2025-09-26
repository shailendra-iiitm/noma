# NOMA User Pairing Project

## Project Structure
```
NOMA_Project/
├── clustering/               # NOMA clustering implementation
│   ├── modules/             # Modular components
│   │   ├── channel.py      # Channel modeling
│   │   ├── user.py         # User placement and properties
│   │   ├── pairing.py      # Pairing algorithms
│   │   └── utils.py        # Utility functions
│   ├── configs/            # Configuration files
│   └── main.py            # Main clustering execution
├── deep_learning/          # Deep learning implementation
│   ├── models/            # Model architectures
│   ├── training/          # Training scripts
│   ├── utils/             # Utilities
│   └── notebooks/         # Colab notebooks
├── docs/                  # Documentation
│   ├── clustering/        # Clustering documentation
│   └── deep_learning/     # DL documentation
└── results/              # Results storage
    ├── clustering/       # Clustering results
    └── deep_learning/   # Model results
```

## Running on Google Colab

1. **Setup**:
   - Upload project to Google Drive
   - Mount Drive in Colab
   - Install requirements

2. **Clustering**:
   - Run clustering/notebooks/clustering_demo.ipynb

3. **Deep Learning**:
   - Run deep_learning/notebooks/train_model.ipynb

## Project Components

### 1. Clustering Module
- Channel modeling (3GPP standards)
- User placement
- Three clustering strategies:
  - Static
  - Balanced
  - Blossom

### 2. Deep Learning Module
- GNN-based user pairing
- Training on clustering results
- Performance comparison

## Requirements
- Python 3.8+
- PyTorch
- NumPy
- Pandas
- NetworkX
- Matplotlib
- See requirements.txt for full list
