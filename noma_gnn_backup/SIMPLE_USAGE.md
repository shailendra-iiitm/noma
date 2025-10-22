# 🚀 NOMA-GNN - Super Simple Usage Guide

## ⚡ Quick Start (3 Commands)

```bash
# 1. Navigate to project
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_gnn_backup

# 2. Run comparison
python run.py compare

# 3. Show results
python run.py show
```

**That's it!** 🎉

---

## 📊 All Commands (From `noma_gnn_backup` folder)

### Comparison (Most Common)
```bash
python run.py compare              # Fast comparison (no Blossom)
python run.py compare --full       # Full comparison (with Blossom)
python run.py show                 # Show last results
```

### Other Tools
```bash
python run.py train                # Train model
python run.py infer FILE.csv       # Run inference
python run.py prepare              # Prepare data
```

---

## 🎯 Or Use Comparison Folder Directly

```bash
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_gnn_backup\comparison

python run.py              # Quick comparison
python run.py --full       # With Blossom
python run.py --show       # Show results
```

---

## 📝 Examples

### Example 1: Quick Test
```bash
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_gnn_backup
python run.py compare
```

### Example 2: Custom Dataset
```bash
python run.py compare --file my_data.csv
```

### Example 3: Multiple Iterations
```bash
python run.py compare --iterations 5 --full
```

---

## 🔧 Options

```bash
python run.py compare --help

Options:
  --file FILE          Custom dataset
  --full               Include Blossom
  --iterations N       Number of runs (default: 3)
  --output FILE        Save results to FILE
  --show               Just show results
```

---

## ✅ What You Get

Running `python run.py compare` gives you:

1. **Timing comparison** for 5 methods (Static, Balanced, Bipartite, Blossom*, GNN)
2. **Throughput analysis** (Mbps)
3. **Speedup metrics** (GNN vs others)
4. **Spectral efficiency** (bits/s/Hz)
5. **CSV output** for Excel/papers

*Blossom only with `--full` flag

---

## 📁 Files Used (Auto-detected)

- **Dataset**: `test_scenario_500users.csv`
- **Model**: `checkpoints/best_model.pt`
- **Scaler**: `data/processed/feature_scaler.json`
- **Output**: `comparison/comparison_results.csv`

---

## 💡 Pro Tips

1. Start with `python run.py` to see the menu
2. Use `compare` for quick tests (skips slow Blossom)
3. Use `compare --full` for papers (includes optimal baseline)
4. Use `show` anytime to view last results
5. For N > 500 users, skip Blossom (it's too slow!)

---

## 🆘 Common Issues

**"No results file found"**
→ Run `python run.py compare` first

**"Missing column: angle"**
→ Your CSV needs `angle_rad` or `angle` column

**Blossom too slow**
→ Use `--full` only for N ≤ 500

---

## 📚 More Info

- Full docs: `comparison/README.md`
- Quick ref: `comparison/QUICK_START.md`
- Old guide: `run.md` (original)

---

**Made simple for fast research! 🎓**
