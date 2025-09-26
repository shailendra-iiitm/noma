# NOMA Clustering Simulation: Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Model](#system-model)
3. [Implementation Flow](#implementation-flow)
4. [Clustering Algorithms](#clustering-algorithms)
5. [Visualization Features](#visualization-features)
6. [Performance Metrics](#performance-metrics)
7. [File Structure](#file-structure)
8. [Usage Instructions](#usage-instructions)
9. [Technical References](#technical-references)

## Overview

This simulation implements and compares three different user clustering strategies for Non-Orthogonal Multiple Access (NOMA) systems in cellular networks. The code simulates a downlink cellular scenario where users are paired for NOMA transmission or served individually via Orthogonal Multiple Access (OMA) based on their channel conditions.

### Key Features
- **Realistic Channel Modeling**: Based on 3GPP TR 38.901 standards
- **Multiple Clustering Strategies**: Static, Balanced, and Blossom algorithms
- **Comprehensive Visualizations**: User distribution, channel characteristics, pairing strategies, and performance comparisons
- **Performance Analysis**: Detailed metrics comparing throughput, coverage, and efficiency

## System Model

### Network Setup
- **Cell Structure**: Single circular cell with radius 5000m
- **User Distribution**: 500 users uniformly distributed within the cell
- **Base Station**: Located at the center (0,0)

### Channel Model Components

#### 1. Path Loss (3GPP TR 38.901)
```
PL(dB) = PL_1m + 10 × α × log10(d) + χ
```
Where:
- `PL_1m`: Path loss at 1 meter reference distance
- `α = 3.5`: Path loss exponent for urban macrocell
- `d`: Distance from base station
- `χ`: Log-normal shadowing (σ = 8 dB)

#### 2. Small-Scale Fading
- **Rayleigh Fading**: Models multipath propagation
- **Channel Gain**: `h = √(fading × path_loss_linear)`

#### 3. System Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| Carrier Frequency | 3.5 GHz | 5G NR Band |
| Total Power | 1.0 W | Base station transmit power |
| Noise Power | 1e-9 W | AWGN power |
| SIC Threshold | 8 dB | Successive interference cancellation threshold |
| Total Bandwidth | 20 MHz | System bandwidth |

## Implementation Flow

### Phase 1: System Initialization
```python
# 1. User Placement
r = sqrt(uniform(0, radius²))  # Random radius
θ = uniform(0, 2π)            # Random angle
x, y = r×cos(θ), r×sin(θ)     # Cartesian coordinates

# 2. Channel Calculation
h_values = fading × sqrt(path_loss_linear)

# 3. User Sorting
sorted_indices = argsort(h_values)  # Sort by channel quality
```

### Phase 2: Visualization Generation
1. **User Distribution Plot**: Shows spatial distribution with channel gain color-coding
2. **Channel Characteristics**: Histograms and distributions of channel parameters

### Phase 3: Clustering Execution
Each clustering method follows this pattern:
1. Generate user pairs based on specific strategy
2. Check SIC feasibility for each pair
3. Calculate NOMA rates for feasible pairs
4. Assign remaining users to OMA
5. Generate pairing visualization
6. Save results and metrics

### Phase 4: Performance Analysis
1. Compare throughput across methods
2. Analyze NOMA vs OMA distribution
3. Generate comprehensive comparison plots
4. Create summary statistics

## Clustering Algorithms

### 1. Static Clustering
**Strategy**: Pairs users with maximum channel gain difference
```python
pairs = [(best_user_i, worst_user_(N-1-i)) for i in range(N//2)]
```
**Advantages**: 
- Maximizes channel gain diversity
- High SIC success rate
**Disadvantages**: 
- May not optimize overall system throughput

### 2. Balanced Clustering
**Strategy**: Pairs users with moderate channel gain difference
```python
pairs = [(sorted_user_i, sorted_user_(i+N//2)) for i in range(N//2)]
```
**Advantages**: 
- Balanced performance across user pairs
- More uniform resource allocation
**Disadvantages**: 
- May sacrifice peak performance for fairness

### 3. Blossom Algorithm (Maximum Weight Matching)
**Strategy**: Finds optimal pairing that maximizes total system throughput
```python
# Build weighted graph
G.add_edge(i, j, weight=sum_rate(i,j))
# Find maximum weight matching
optimal_pairs = max_weight_matching(G)
```
**Advantages**: 
- Theoretically optimal throughput
- Considers all possible pairing combinations
**Disadvantages**: 
- Higher computational complexity O(N³)

## Visualization Features

### 1. User Distribution Plot (`user_distribution.png`)
- **Purpose**: Visualize spatial user placement and channel quality
- **Features**: 
  - Scatter plot with channel gain color-coding
  - Cell boundary visualization
  - Coordinate system with proper scaling

### 2. Channel Characteristics (`channel_characteristics.png`)
- **Subplots**:
  - Channel gain histogram
  - Path loss vs distance scatter plot
  - Rayleigh fading distribution
  - Sorted channel gains curve

### 3. Pairing Visualizations (`{method}_pairing.png`)
- **Purpose**: Show how each clustering method pairs users
- **Features**:
  - Lines connecting paired users
  - Color-coded pairs
  - Unpaired users shown in gray

### 4. Clustering Comparison (`clustering_comparison.png`)
- **Subplots**:
  - Total throughput bar chart
  - NOMA vs OMA distribution
  - Average rate comparisons
  - Performance share pie chart

## Performance Metrics

### Primary Metrics
1. **Total System Throughput (Mbps)**: Sum of all user throughputs
2. **NOMA Pairs Count**: Number of successfully paired users
3. **OMA Users Count**: Number of users served individually
4. **NOMA Coverage (%)**: Percentage of users served via NOMA

### Secondary Metrics
1. **Average NOMA Rate**: Mean rate for NOMA pairs
2. **Average OMA Rate**: Mean rate for OMA users
3. **Spectral Efficiency**: Bits per Hz per user
4. **Fairness Index**: Distribution of rates across users

### Rate Calculations

#### NOMA Pair Rates
For users with channel gains h₁ ≤ h₂:
```
P₁ = P_total × h₂/(h₁ + h₂)  # Power for weak user
P₂ = P_total × h₁/(h₁ + h₂)  # Power for strong user

R₁ = log₂(1 + P₁h₁/(P₂h₁ + N₀))  # Weak user rate
R₂ = log₂(1 + P₂h₂/N₀)           # Strong user rate
```

#### OMA Rate
```
R_OMA = log₂(1 + P_total × h/N₀)
```

#### SIC Condition
NOMA is feasible if: `10×log₁₀(h₂/h₁) ≥ SIC_threshold_dB`

## File Structure

```
simulation_results/
├── YYYYMMDD_HHMMSS/              # Timestamped run directory
│   ├── user_distribution.png          # Spatial user distribution with channel gains
│   ├── channel_characteristics.png    # Basic channel analysis plots
│   ├── channel_components_analysis.png # Detailed channel component analysis
│   ├── user_positioning_analysis.png  # Spatial positioning and polar analysis
│   ├── static_pairing.png             # Static clustering visualization
│   ├── balanced_pairing.png           # Balanced clustering visualization
│   ├── blossom_pairing.png            # Blossom clustering visualization
│   ├── clustering_comparison.png      # Performance comparison
│   ├── h_values.csv                   # Comprehensive user data with coordinates
│   ├── static_clustering.csv          # Static clustering results
│   ├── balanced_clustering.csv        # Balanced clustering results
│   ├── blossom_clustering.csv         # Blossom clustering results
│   └── clustering_summary.csv         # Performance summary
├── 20250804_143022/              # Example: Previous run
│   └── ... (same structure)
└── runs_comparison.png           # Multi-run comparison (optional)
```

### Timestamped Directory Benefits
- **No Data Loss**: Each simulation run creates a unique folder
- **Easy Comparison**: Multiple runs can be compared side-by-side
- **Version Control**: Track parameter changes and their effects
- **Organized Results**: Clear separation between different experiments

### Directory Naming Convention
Format: `YYYYMMDD_HHMMSS`
- `YYYY`: 4-digit year
- `MM`: 2-digit month
- `DD`: 2-digit day
- `HH`: 2-digit hour (24-hour format)
- `MM`: 2-digit minute
- `SS`: 2-digit second

Example: `20250804_143022` = August 4, 2025 at 2:30:22 PM

### CSV File Format

#### User Channel Data (`h_values.csv`)
| Column | Description |
|--------|-------------|
| User_ID | Unique user identifier (0 to N-1) |
| x_coord_m | X-coordinate position in meters |
| y_coord_m | Y-coordinate position in meters |
| distance_m | Distance from base station in meters |
| angle_rad | Angle from base station in radians |
| path_loss_dB | Path loss component in dB |
| path_loss_linear | Path loss in linear scale |
| shadowing_dB | Log-normal shadowing component in dB |
| rayleigh_fading | Rayleigh fading coefficient |
| h_linear | Overall channel gain (linear) |
| h_dB | Overall channel gain in dB |

#### Clustering Results (`{method}_clustering.csv`)
| Column | Description |
|--------|-------------|
| User1_ID | First user in NOMA pair (or OMA user) |
| User2_ID | Second user in NOMA pair (-1 for OMA) |
| h1, h2 | Channel gains |
| P1, P2 | Allocated powers |
| R1_bitsHz, R2_bitsHz | Individual rates |
| R_sum_bitsHz | Sum rate |
| Mode | "NOMA" or "OMA" |
| Throughput_Mbps | Actual throughput considering bandwidth |

## Usage Instructions

### Prerequisites
```bash
pip install -r requirements.txt
```
Or manually install:
```bash
pip install numpy matplotlib pandas networkx tqdm
```

### Running the Simulation
```bash
python clustering.py
```

### Managing Results
Use the results manager for organized analysis:
```bash
python results_manager.py
```

### Expected Output
1. **Console**: Real-time progress and performance summaries
2. **Timestamped Directory**: All files organized by run time
3. **CSV Files**: Detailed numerical results
4. **PNG Files**: Comprehensive visualizations

### Results Directory Structure
Each run creates a new timestamped folder in `simulation_results/`:
- Format: `simulation_results/YYYYMMDD_HHMMSS/`
- Contains all plots, CSV files, and summary data
- Prevents overwriting previous results

### Customization Options
Modify parameters in the initialization section:
```python
N = 500              # Number of users
radius = 5000        # Cell radius (m)
sic_threshold_db = 8 # SIC threshold (dB)
B_total = 20e6       # Bandwidth (Hz)
```

### Results Management Features
The `results_manager.py` script provides:
1. **List Runs**: View all simulation runs with timestamps
2. **View Summary**: Detailed performance metrics for any run
3. **Compare Runs**: Side-by-side comparison of multiple runs
4. **Cleanup**: Remove old runs while keeping recent ones

## Technical References

1. **3GPP TR 38.901**: "Study on channel model for frequencies from 0.5 to 100 GHz"
2. **Chen et al. (2021)**: "NOMA-Based Multi-Pair Two-Way Relay Networks With Rate Splitting and Group Decoding", IEEE Transactions on Wireless Communications
3. **Edmonds (1965)**: "Maximum matching and a polyhedron with 0,1-vertices", Journal of Research of the National Bureau of Standards

## Algorithm Complexity Analysis

| Algorithm | Time Complexity | Space Complexity | Optimality |
|-----------|----------------|------------------|------------|
| Static | O(N log N) | O(N) | Suboptimal |
| Balanced | O(N log N) | O(N) | Suboptimal |
| Blossom | O(N³) | O(N²) | Optimal |

## Performance Insights

### Typical Results (N=500 users)
- **Static**: ~60-70% NOMA coverage, moderate throughput
- **Balanced**: ~50-60% NOMA coverage, balanced performance
- **Blossom**: ~40-50% NOMA coverage, highest throughput

### Trade-offs
- **Coverage vs Throughput**: Higher NOMA coverage doesn't always mean higher throughput
- **Complexity vs Performance**: Blossom algorithm provides best performance at highest computational cost
- **Fairness vs Efficiency**: Balanced approach provides more uniform user experience

## Future Enhancements

1. **Dynamic Scenarios**: Time-varying channels and user mobility
2. **Imperfect SIC**: Realistic interference cancellation modeling
3. **Power Control**: Optimized power allocation strategies
4. **Multi-Cell**: Inter-cell interference consideration
5. **Machine Learning**: AI-based clustering optimization

---

*This documentation provides a complete understanding of the NOMA clustering simulation framework. For technical questions or enhancements, refer to the implementation comments and cited references.*
