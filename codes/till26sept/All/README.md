# NOMA Clustering Simulation

A comprehensive simulation framework for Non-Orthogonal Multiple Access (NOMA) user clustering strategies in cellular networks.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Simulation
```bash
python clustering.py
```

### 3. Manage Results
```bash
python results_manager.py
```

**Note**: Results manager works with basic Python libraries. Advanced comparison features require pandas/matplotlib.

## Features

✅ **Realistic Channel Modeling** - Based on 3GPP TR 38.901 standards  
✅ **Multiple Clustering Algorithms** - Static, Balanced, and Blossom methods  
✅ **Comprehensive Visualizations** - Distribution plots, pairing visualizations, performance comparisons  
✅ **Timestamped Results** - Each run saved in unique directories  
✅ **Results Management** - Compare and analyze multiple simulation runs  
✅ **Performance Metrics** - Throughput, coverage, efficiency analysis  

## Output Files

Each simulation run creates a timestamped directory in `simulation_results/`:

```
simulation_results/20250804_143022/
├── 📊 user_distribution.png          # Spatial user layout
├── 📈 channel_characteristics.png    # Channel analysis
├── 🔗 static_pairing.png            # Static clustering pairs
├── 🔗 balanced_pairing.png          # Balanced clustering pairs
├── 🔗 blossom_pairing.png           # Optimal clustering pairs
├── 📊 clustering_comparison.png      # Performance comparison
├── 📄 h_values.csv                  # Channel gain data
├── 📄 static_clustering.csv         # Static results
├── 📄 balanced_clustering.csv       # Balanced results
├── 📄 blossom_clustering.csv        # Blossom results
└── 📄 clustering_summary.csv        # Performance summary
```

## Algorithm Comparison

| Method | Strategy | Complexity | Optimality | Coverage |
|--------|----------|------------|------------|----------|
| **Static** | Max channel difference | O(N log N) | Suboptimal | 60-70% |
| **Balanced** | Moderate difference | O(N log N) | Suboptimal | 50-60% |
| **Blossom** | Maximum weight matching | O(N³) | Optimal | 40-50% |

## Key Parameters

```python
N = 500              # Number of users
radius = 5000        # Cell radius (meters)
fc = 3.5e9          # Carrier frequency (Hz)
sic_threshold_db = 8 # SIC threshold (dB)
B_total = 20e6      # Total bandwidth (Hz)
```

## Results Manager

Interactive tool for managing simulation results:

1. **List Runs** - View all simulation runs with timestamps
2. **View Summary** - Detailed metrics for specific runs  
3. **Compare Runs** - Side-by-side performance comparison
4. **Cleanup** - Remove old runs to save space

## Documentation

📚 **Comprehensive Documentation**: `NOMA_Clustering_Documentation.md`  
📖 **Visualization Guide**: `Visualization_Guide.md`  

## System Requirements

- Python 3.7+
- NumPy, Matplotlib, Pandas, NetworkX, tqdm
- ~50MB storage per simulation run (500 users)

## Example Results

**Typical Performance (N=500 users):**
- Static: 65% NOMA coverage, 45.2 Mbps total throughput
- Balanced: 55% NOMA coverage, 47.8 Mbps total throughput  
- Blossom: 45% NOMA coverage, 52.1 Mbps total throughput

## Technical Background

Based on:
- 3GPP TR 38.901 channel models
- IEEE research on NOMA clustering
- Maximum weight matching algorithms

---

*For detailed technical information, see the comprehensive documentation.*
