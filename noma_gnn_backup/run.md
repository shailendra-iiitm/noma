# NOMA-GNN Local Setup & Run Guide

Complete guide for setting up and running the NOMA-GNN project on your local Windows machine.

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Running Inference (Quick Start)](#running-inference-quick-start)
4. [Training New Models](#training-new-models)
5. [Data Preparation](#data-preparation)
6. [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

Before starting, ensure you have:
- **Python 3.8 or higher** (Python 3.9-3.11 recommended)
- **Git** (for cloning the repository)
- **8GB+ RAM** (16GB recommended for training)
- **Optional**: CUDA-compatible GPU (for faster training)

---

## 🚀 Initial Setup

### Step 1: Navigate to Project Directory
```cmd
cd d:\Developer\NOMA_PROJECT\NOMA\noma_gnn_backup
```

### Step 2: Create Virtual Environment (Recommended)

**Option A: Using venv (Built-in)**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Option B: Using conda**
```cmd
conda create -n noma-gnn python=3.9
conda activate noma-gnn
```

### Step 3: Install Dependencies

**For CPU-only (Faster installation)**
```cmd
pip install torch torchvision torchaudio
pip install torch-geometric torch-scatter torch-sparse
pip install pandas numpy scikit-learn networkx matplotlib seaborn tqdm
```

**For GPU (CUDA 11.8+)**
```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install torch-geometric torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.0.0+cu118.html
pip install pandas numpy scikit-learn networkx matplotlib seaborn tqdm
```

**Or simply use requirements.txt**
```cmd
pip install -r requirements.txt
```

### Step 4: Verify Installation
```cmd
python -c "import torch; import torch_geometric; print('✅ PyTorch:', torch.__version__); print('✅ PyG:', torch_geometric.__version__)"
```

**Expected Output:**
```
✅ PyTorch: 2.0.0+cu118
✅ PyG: 2.3.0
```

---

## 🎯 Running Inference (Quick Start)

Use this when you have a trained model and want to predict user pairs for new channel data.

### Command Format
```cmd
cd d:\Developer\NOMA_PROJECT\NOMA\noma_gnn_backup

python -m inference.infer_pairing ^
  --ckpt checkpoints/best_model.pt ^
  --scaler data/processed/feature_scaler.json ^
  --h_values_csv ..\h_values_a.csv ^
  --out_csv data/processed/predicted_pairs.csv
```

### Parameters Explained
- `--ckpt`: Path to trained model checkpoint (`.pt` file)
- `--scaler`: Path to feature normalization parameters (`.json` file)
- `--h_values_csv`: Input CSV with user channel state information (h-values)
- `--out_csv`: Output path for predicted user pairs

### Example Output
```
Loading model from checkpoints/best_model.pt
Processing 100 users...
Generating candidate pairs... 2,450 candidates
Scoring with GNN...
Running greedy matching...
✅ Chosen pairs: 20 | Estimated total throughput: 282.49 Mbps
Saved predicted pairs to data/processed/predicted_pairs.csv
```

### Input CSV Format (`h_values_a.csv`)
Your input CSV should have these columns:
```csv
Graph_ID,User_ID,distance_m,angle_rad,path_loss_dB,shadowing_dB,rayleigh_fading,h_linear,h_dB
0,0,1234.5,2.34,112.3,-3.2,0.89,1.23e-6,-59.2
0,1,2456.7,4.56,118.7,2.1,1.12,5.67e-7,-62.5
```

### Output CSV Format (`predicted_pairs.csv`)
The output will contain:
```csv
User1_ID,User2_ID,h1,h2,predicted_alpha,predicted_sum_rate,confidence_score
0,5,1.23e-6,5.67e-7,0.78,7.42,0.95
2,8,3.45e-7,8.91e-7,0.82,8.15,0.92
```

---

## 🎓 Training New Models

Use this workflow to train the GNN from scratch with your own dataset.

### Step 1: Prepare Training Data

You need two CSV files from your NOMA simulator:

**File 1: `merged_h_values.csv`** (User information)
```csv
Graph_ID,User_ID,distance_m,angle_rad,path_loss_dB,shadowing_dB,rayleigh_fading,h_linear,h_dB
0,0,1234.5,2.34,112.3,-3.2,0.89,1.23e-6,-59.2
0,1,2456.7,4.56,118.7,2.1,1.12,5.67e-7,-62.5
```

**File 2: `merged_pairs.csv`** (Optimal pairs from your optimizer)
```csv
Graph_ID,User1_ID,User2_ID,h1,h2,P1,P2,R1_bitsHz,R2_bitsHz,R_sum_bitsHz,Mode
0,0,1,1.23e-6,5.67e-6,0.82,0.18,3.45,4.12,7.57,NOMA
0,2,5,3.45e-7,8.91e-6,0.89,0.11,2.87,5.34,8.21,NOMA
```

Place these files in `data/raw/` folder.

### Step 2: Preprocess Data (Optional but Recommended)
```cmd
python -m scripts.prepare_data ^
  --users_csv data/raw/merged_h_values.csv ^
  --pairs_csv data/raw/merged_pairs.csv ^
  --out_pt data/processed/bpf_graph_dataset.pt ^
  --scaler_out data/processed/feature_scaler.json
```

### Step 3: Train the Model
```cmd
python -m training.train ^
  --users_csv data/raw/merged_h_values.csv ^
  --pairs_csv data/raw/merged_pairs.csv ^
  --out_dir checkpoints ^
  --scaler_path data/processed/feature_scaler.json ^
  --epochs 60 ^
  --batch_size 2 ^
  --device cuda
```

**For CPU training:**
```cmd
python -m training.train ^
  --users_csv data/raw/merged_h_values.csv ^
  --pairs_csv data/raw/merged_pairs.csv ^
  --out_dir checkpoints ^
  --scaler_path data/processed/feature_scaler.json ^
  --epochs 60 ^
  --batch_size 2 ^
  --device cpu
```

### Training Output
```
Epoch  1/60: Loss=1.234 | Train AUC=0.756 MAE_R=0.12 MAE_α=0.03
Epoch  2/60: Loss=0.987 | Train AUC=0.812 MAE_R=0.09 MAE_α=0.02
...
Epoch 45/60: Loss=0.234 | Train AUC=0.925 MAE_R=0.03 MAE_α=0.01
✅ Best model saved to checkpoints/best_model.pt
```

---

## 📊 Data Preparation

### Generating h-values CSV from Your Simulator

If you have a NOMA simulator, ensure it exports user channel data in this format:

**Required Columns:**
- `Graph_ID`: Scenario identifier (integer)
- `User_ID`: Unique user identifier within scenario (integer)
- `distance_m`: Distance from base station in meters (float)
- `angle_rad`: Angle in radians (float)
- `path_loss_dB`: Path loss in dB (float)
- `shadowing_dB`: Shadowing component in dB (float)
- `rayleigh_fading`: Rayleigh fading coefficient (float)
- `h_linear`: Channel gain in linear scale (float)
- `h_dB`: Channel gain in dB (float)

### Verifying SIC Constraints

After inference, verify that predicted pairs satisfy SIC (Successive Interference Cancellation) constraints:

```cmd
python -m scripts.verify_sic_pairs ^
  --pairs_csv data/processed/predicted_pairs.csv ^
  --sic_threshold_db 8.0
```

---

## 🔧 Troubleshooting

### Issue 1: `ModuleNotFoundError: No module named 'inference'`
**Solution:** Ensure you're running from the `noma_gnn_backup` directory:
```cmd
cd d:\Developer\NOMA_PROJECT\NOMA\noma_gnn_backup
```

### Issue 2: `Weights only load failed` (PyTorch 2.6+)
**Solution:** Already fixed in `inference/infer_pairing.py` by adding `weights_only=False` parameter.

### Issue 3: CUDA Out of Memory
**Solution:** Reduce batch size or use CPU:
```cmd
--batch_size 1 --device cpu
```

### Issue 4: Missing `feature_scaler.json`
**Solution:** This file is generated during training. If missing, retrain the model or copy from a previous training run.

### Issue 5: Import Error for `torch_geometric`
**Solution:** Install PyTorch Geometric properly:
```cmd
pip install torch-geometric torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.0.0+cu118.html
```

### Issue 6: Path Issues on Windows
**Solution:** Use relative paths with `..` or absolute paths with backslashes:
```cmd
--h_values_csv ..\h_values_a.csv
# or
--h_values_csv d:\Developer\NOMA_PROJECT\NOMA\h_values_a.csv
```

---

## 📁 Project Structure Quick Reference

```
noma_gnn_backup/
│
├── checkpoints/              # Trained models
│   ├── best_model.pt        # ← Main trained model
│   └── feature_scaler.json  # ← Normalization parameters
│
├── data/
│   ├── raw/                 # Input CSVs (place your data here)
│   └── processed/           # Preprocessed graphs & outputs
│       ├── bpf_graph_dataset.pt
│       ├── feature_scaler.json
│       └── predicted_pairs.csv  # ← Inference output
│
├── inference/
│   └── infer_pairing.py     # ← Run predictions
│
├── training/
│   ├── train.py             # ← Train models
│   └── losses.py
│
├── scripts/
│   ├── prepare_data.py      # Preprocess data
│   └── verify_sic_pairs.py  # Verify constraints
│
└── models/
    └── pairpower_gnn.py     # GNN architecture
```

---

## 🎯 Common Workflows

### Workflow 1: Quick Prediction on New Data
```cmd
# 1. Place your h_values CSV in the project root
# 2. Run inference
cd d:\Developer\NOMA_PROJECT\NOMA\noma_gnn_backup
python -m inference.infer_pairing ^
  --ckpt checkpoints/best_model.pt ^
  --scaler data/processed/feature_scaler.json ^
  --h_values_csv ..\your_new_data.csv ^
  --out_csv results\predictions.csv
```

### Workflow 2: Full Training Pipeline
```cmd
# 1. Prepare your data
python -m scripts.prepare_data ^
  --users_csv data/raw/merged_h_values.csv ^
  --pairs_csv data/raw/merged_pairs.csv ^
  --out_pt data/processed/dataset.pt ^
  --scaler_out data/processed/scaler.json

# 2. Train model
python -m training.train ^
  --users_csv data/raw/merged_h_values.csv ^
  --pairs_csv data/raw/merged_pairs.csv ^
  --out_dir checkpoints ^
  --epochs 60 ^
  --device cuda

# 3. Run inference
python -m inference.infer_pairing ^
  --ckpt checkpoints/best_model.pt ^
  --scaler data/processed/feature_scaler.json ^
  --h_values_csv test_data.csv ^
  --out_csv predictions.csv

# 4. Verify results
python -m scripts.verify_sic_pairs --pairs_csv predictions.csv
```

---

## 📚 Additional Resources

- **Detailed Documentation**: See `PROJECT_README.md` for comprehensive technical details
- **Configuration Guide**: See `config_README.md` for hyperparameter tuning
- **Module Documentation**: Check `noma_gnn_documentation/` for per-module guides
- **LaTeX Documentation**: See `DOCUMENTATION.tex` for academic paper-style documentation

---

## 💡 Tips for Best Results

1. **Data Quality**: Ensure your input CSVs have no missing values
2. **Feature Scaling**: Always use the same `feature_scaler.json` that was used during training
3. **Batch Size**: Start with batch_size=2 for training, adjust based on your GPU memory
4. **Epochs**: 50-60 epochs usually sufficient, monitor validation metrics
5. **Device**: Use GPU (`--device cuda`) for training, CPU is fine for inference
6. **Checkpoints**: Always keep backup of `best_model.pt` and `feature_scaler.json`

---

## 📧 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section above
2. Review `PROJECT_README.md` for detailed technical information
3. Check configuration in `config.py` for parameter adjustments

---

**Last Updated**: October 21, 2025
**Project**: NOMA-GNN User Pairing & Power Allocation
**Author**: Shailendra (shailendra-iiitm)
