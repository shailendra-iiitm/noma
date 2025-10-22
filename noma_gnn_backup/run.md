# NOMA-GNN Quick Start Guide

**Simplified workflow for running NOMA pairing comparisons and experiments.**

---

## 🚀 Super Quick Start (3 Commands)

```bash
# 1. Navigate to project
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_gnn_backup

# 2. Run comparison (all methods)
python run.py compare

# 3. Show results
python run.py show
```

**That's it!** ✅ Results will be displayed automatically.

---

## 📋 Table of Contents
1. [Quick Commands](#quick-commands)
2. [Comparison Tool](#comparison-tool)
3. [Training & Inference](#training--inference)
4. [Prerequisites & Setup](#prerequisites--setup)
5. [Troubleshooting](#troubleshooting)

---

## ⚡ Quick Commands

All commands are run from the `noma_gnn_backup` folder:

```bash
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_gnn_backup
```

### Main Commands

| Command | Description | Time |
|---------|-------------|------|
| `python run.py` | Show command menu | Instant |
| `python run.py compare` | Quick comparison (no Blossom) | ~30s |
| `python run.py compare --full` | Full comparison (with Blossom) | ~75s |
| `python run.py show` | Display last results | Instant |
| `python run.py train` | Train the GNN model | Hours |
| `python run.py infer FILE.csv` | Run inference on dataset | Seconds |

---

## 📊 Comparison Tool

### Basic Usage

```bash
# Fast comparison (recommended for N > 500)
python run.py compare

# Full comparison with Blossom optimal baseline
python run.py compare --full

# View last results
python run.py show
```

### Advanced Options

```bash
# Custom dataset
python run.py compare --file path/to/your/data.csv

# More iterations for stable timing
python run.py compare --iterations 5

# Full comparison with custom dataset
python run.py compare --file data.csv --full

# Save to specific output file
python run.py compare --output my_results.csv
```

### Direct Access (Alternative)

You can also run from the comparison folder directly:

```bash
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_gnn_backup\comparison

python run.py              # Quick comparison
python run.py --full       # With Blossom
python run.py --show       # Show results
```

---

## 🎯 What Gets Compared?

The comparison tool evaluates **5 pairing methods** on the same dataset:

| Method | Algorithm | Complexity | Source |
|--------|-----------|------------|--------|
| **Static** | Strongest-Weakest | O(N log N) | noma.py line 678 |
| **Balanced** | Upper-Lower half | O(N log N) | noma.py line 683 |
| **Bipartite** | Graph PF matching | O(N³) | noma.py lines 562-591 |
| **Blossom** | General max matching | O(N³) | noma.py lines 686-703 |
| **NOMA-GNN** | Learned pairing | O(N log N) | Proposed |

### Metrics Evaluated

1. ⏱️ **Execution Time** (ms) - average over multiple iterations
2. 📊 **Number of Pairs** - successful pairings formed
3. 📈 **Pairing Efficiency** (%) - percentage of users paired
4. 🚀 **Total Throughput** (Mbps) - system capacity
5. 📡 **Spectral Efficiency** (bits/s/Hz) - average sum rate

---

## 🔬 Training & Inference

### Train New Model

```bash
python run.py train
```

### Run Inference

```bash
# On test scenario
python run.py infer test_scenario_500users.csv

# On custom dataset
python run.py infer path/to/your/data.csv
```

### Prepare Data

```bash
python run.py prepare
```

---

## ✅ Prerequisites & Setup

### Prerequisites

Before starting, ensure you have:
- **Python 3.8 or higher** (Python 3.9-3.11 recommended)
- **8GB+ RAM** (16GB recommended for training)
- **Optional**: CUDA-compatible GPU (for faster training)

---

## 🚀 Initial Setup

### Step 1: Navigate to Project Directory
```bash
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_gnn_backup
```

### Step 2: Create Virtual Environment (Recommended)

**Option A: Using venv (Built-in)**
```bash
python -m venv venv
venv\Scripts\activate
```

**Option B: Using conda**
```bash
conda create -n noma-gnn python=3.9
conda activate noma-gnn
```

### Step 3: Install Dependencies

```bash
pip install torch torchvision torchaudio
pip install torch-geometric torch-scatter torch-sparse
pip install pandas numpy scikit-learn networkx matplotlib seaborn tqdm
```

**For GPU (CUDA 11.8+)**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install torch-geometric torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.0.0+cu118.html
pip install pandas numpy scikit-learn networkx matplotlib seaborn tqdm
```

**Or simply use requirements.txt**
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -c "import torch; import torch_geometric; print('✅ PyTorch:', torch.__version__); print('✅ PyG:', torch_geometric.__version__)"
```

**Expected Output:**
```
✅ PyTorch: 2.0.0+cu118
✅ PyG: 2.3.0
```

---

## 📂 File Structure

```
noma_gnn_backup/
├── run.py                          # ⭐ Main launcher (START HERE!)
├── SIMPLE_USAGE.md                 # Quick reference guide
├── comparison/
│   ├── run.py                      # ⭐ Comparison launcher
│   ├── compare_methods.py          # Full comparison tool
│   ├── show_results.py             # Results formatter
│   ├── README.md                   # Detailed docs
│   └── QUICK_START.md              # Quick guide
├── training/
│   └── train.py                    # Model training
├── inference/
│   └── infer_pairing.py            # Inference script
├── models/
│   └── pairpower_gnn.py            # GNN architecture
├── data/
│   ├── dataset.py                  # Dataset handling
│   └── normalization.py            # Feature scaling
├── checkpoints/
│   └── best_model.pt               # Trained model
└── test_scenario_500users.csv      # Default test file
```

---

## 💡 Common Workflows

### 1. Quick Performance Test
```bash
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_gnn_backup
python run.py compare
python run.py show
```

### 2. Full Comparison for Paper
```bash
python run.py compare --full --iterations 5
python run.py show
```

### 3. Test on Custom Dataset
```bash
python run.py compare --file my_scenario.csv
```

### 4. Batch Testing
```bash
# PowerShell
Get-ChildItem scenarios\*.csv | ForEach-Object {
    python run.py compare --file $_.FullName --output "results_$($_.BaseName).csv"
}
```

---

## 📊 Understanding Results

### Example Output

```
Method      Time_ms  Pairs  Throughput_Mbps  Avg_Sum_Rate_bps_Hz
Static         0.30    250        40780.83             8.16
Balanced       0.19    250        52795.45            10.56
Bipartite  32927.09    232        73296.08            15.80
Blossom    44749.26    232        73296.09            15.80 [OPTIMAL]
NOMA-GNN     846.31    225        70744.11            15.72
```

**Key Insights:**
- **GNN is 52.9× faster** than Blossom (optimal)
- **GNN achieves 96.5%** of optimal throughput
- **GNN is practical** for real-time deployment (< 1 second)

---

## 🎯 Input File Requirements

Your CSV must have these columns:

| Column | Alternative Names | Required |
|--------|-------------------|----------|
| `h_linear` | - | ✅ Yes |
| `angle` | `angle_rad`, `theta` | ✅ Yes |
| `distance` | `distance_m`, `d_2D` | Optional |
| `is_los` | `is_LOS` | Optional |

**Example:**
```csv
User_ID,h_linear,angle_rad,distance_m
0,0.000123,1.234,1500.5
1,0.000456,2.345,2300.2
...
```

---

## 🆘 Troubleshooting

### Common Issues

**1. "No results file found"**
```bash
# Solution: Run comparison first
python run.py compare
```

**2. "Missing column: angle"**
```bash
# Solution: Your CSV needs 'angle', 'angle_rad', or 'theta' column
```

**3. "Blossom taking too long"**
```bash
# Solution: Use --full only for N ≤ 500 users
python run.py compare              # For N > 500
python run.py compare --full       # For N ≤ 500
```

**4. "Can't find module torch_geometric"**
```bash
# Solution: Install PyG
pip install torch-geometric torch-scatter torch-sparse
```

**5. Command not working**
```bash
# Make sure you're in the right directory
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_gnn_backup
python run.py
```

---

## 🎓 For Research Papers

### Quick Workflow

1. **Run comparison**
   ```bash
   python run.py compare --full --iterations 3
   ```

2. **View results**
   ```bash
   python run.py show
   ```

3. **Copy results**
   - Results are automatically displayed
   - CSV saved to `comparison/comparison_results.csv`
   - "RECOMMENDED TEXT FOR PAPER" section included

### Sample Results for Paper

From the output, you get:
- ✅ Execution time comparison table
- ✅ Speedup analysis (GNN vs baselines)
- ✅ Throughput comparison
- ✅ Spectral efficiency metrics
- ✅ Ready-to-use text snippets

---

## 📚 Additional Resources

- **Detailed Comparison Guide**: `comparison/README.md`
- **Quick Start**: `comparison/QUICK_START.md`
- **Simple Usage**: `SIMPLE_USAGE.md`
- **Project Overview**: `PROJECT_README.md`

---

## 🎯 Quick Command Reference

```bash
# Show menu
python run.py

# Quick comparison (30s)
python run.py compare

# Full comparison (75s)
python run.py compare --full

# View results
python run.py show

# Custom dataset
python run.py compare --file data.csv

# More iterations
python run.py compare --iterations 5

# Train model
python run.py train

# Run inference
python run.py infer test_scenario_500users.csv
```

---

**Made simple for fast research! 🚀**

---

## ❓ Troubleshooting

### Common Issues

**"No module named 'torch'"**
```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**"FileNotFoundError: test_scenario_500users.csv"**
- Check file exists in `noma_gnn_backup/` folder
- Use absolute path: `python run.py compare --file "C:\path\to\file.csv"`

**"RuntimeError: CUDA out of memory"**
```cmd
# Use CPU instead
python run.py train --device cpu
python run.py infer test_scenario_500users.csv --device cpu
```

**"ImportError: networkx"**
```cmd
pip install networkx==3.1
```

**Results file not found when running `show`**
- Make sure you ran `compare` first
- Check `comparison/comparison_results.csv` exists

### Performance Tips

**Slow comparison (>2 minutes for 500 users)?**
- Skip Blossom: `python run.py compare` (default, no --full flag)
- Use smaller dataset for testing
- Consider upgrading CPU

**Training not improving?**
- Check data quality (merged_h_values.csv and merged_pairs.csv format)
- Increase epochs: `python run.py train --epochs 100`
- Adjust learning rate in `config.py`

---

## 📚 Additional Documentation

For more details, see:
- **`comparison/README.md`** - Detailed comparison tool documentation
- **`comparison/QUICK_START.md`** - Quick comparison examples
- **`PROJECT_README.md`** - Full project overview
- **`SIMPLE_USAGE.md`** - Simple usage examples
- **`config_README.md`** - Configuration options

---

## 📞 Support

For issues or questions:
1. Check this guide first
2. Review error messages carefully
3. Verify file paths and formats
4. Check Python environment setup

---

**Last Updated**: January 2025  
**Project**: NOMA-GNN Power Allocation & User Pairing

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
