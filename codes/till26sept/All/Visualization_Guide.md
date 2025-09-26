# NOMA Clustering Simulation - Visualization Guide

## Quick Reference for### 5. Pairing Visualizations (`{method}_pairing.png`)
One plot for each clustering method showing how users are paired:

#### Static Pairing (`static_pairing.png`)
- **Strategy**: Best user paired with worst user
- **Lines**: Connect paired users (strong colors = NOMA pairs)
- **Gray dots**: Unpaired users (served via OMA)
- **Pattern**: Long lines connecting distant users

#### Balanced Pairing (`balanced_pairing.png`)
- **Strategy**: Moderate channel gain differences
- **Pattern**: Medium-length connecting lines
- **More uniform**: Distribution of pair qualities

#### Blossom Pairing (`blossom_pairing.png`)
- **Strategy**: Optimal throughput maximization
- **Pattern**: Complex pairing pattern optimized for sum rate
- **May have**: Shorter lines but better overall performance

### 6. Clustering Comparison (`clustering_comparison.png`)### 1. User Distribution Plot (`user_distribution.png`)
**What it shows**: Spatial distribution of all 500 users within the circular cell
- **X/Y axes**: Position coordinates in meters
- **Colors**: Channel gain in dB (blue = weak, yellow = strong)
- **Dashed circle**: Cell boundary (5000m radius)
- **Purpose**: Understand spatial-channel correlation

### 2. Channel Characteristics (`channel_characteristics.png`)
Four-panel analysis of channel properties:

#### Top Left: Channel Gain Histogram
- Shows distribution of channel gains across all users
- X-axis: Channel gain in dB
- Y-axis: Number of users

#### Top Right: Path Loss vs Distance
- Scatter plot showing relationship between distance and path loss
- X-axis: Distance from base station (m)
- Y-axis: Path loss (dB)
- Expected trend: Higher path loss at greater distances

#### Bottom Left: Rayleigh Fading Distribution
- Histogram of small-scale fading coefficients
- Should follow Rayleigh distribution pattern
- X-axis: Fading coefficient value

#### Bottom Right: Sorted Channel Gains
- Line plot of channel gains sorted from worst to best
- X-axis: User index (sorted)
- Y-axis: Channel gain (dB)
- Shows channel quality variation across users

### 3. Channel Components Analysis (`channel_components_analysis.png`)
Four-panel detailed analysis of channel modeling:

#### Top Left: Path Loss vs Distance
- Scatter plot with theoretical path loss curve overlay
- Shows how well the 3GPP model fits the simulated data
- Red dots = actual path loss, black dashed line = theoretical

#### Top Right: Spatial Shadowing Distribution
- Shows how shadowing varies across the cell area
- Color-coded spatial map of shadowing effects
- Helps identify shadowing hotspots and patterns

#### Bottom Left: Channel Component Contributions
- Box plots comparing magnitudes of different channel effects
- Shows relative importance of path loss, shadowing, and fading
- Useful for understanding dominant channel effects

#### Bottom Right: Distance vs Overall Channel Gain
- Combined effect of all channel components
- Shows actual channel quality variation with distance
- Includes statistics summary box

### 4. User Positioning Analysis (`user_positioning_analysis.png`)
Four-panel spatial analysis:

#### Top Left: Radial Distribution
- Histogram showing how users are distributed by distance
- Should show uniform distribution for proper simulation

#### Top Right: Angular Distribution  
- Histogram of user angular positions
- Should be uniform for proper circular distribution

#### Bottom Left: Polar View
- Polar plot showing user positions with channel quality color-coding
- Provides intuitive view of spatial-channel correlation

#### Bottom Right: Angle vs Distance
- Cartesian view of user positions with channel quality
- Useful for identifying sector-based patterns
One plot for each clustering method showing how users are paired:

#### Static Pairing (`static_pairing.png`)
- **Strategy**: Best user paired with worst user
- **Lines**: Connect paired users (strong colors = NOMA pairs)
- **Gray dots**: Unpaired users (served via OMA)
- **Pattern**: Long lines connecting distant users

#### Balanced Pairing (`balanced_pairing.png`)
- **Strategy**: Moderate channel gain differences
- **Pattern**: Medium-length connecting lines
- **More uniform**: Distribution of pair qualities

#### Blossom Pairing (`blossom_pairing.png`)
- **Strategy**: Optimal throughput maximization
- **Pattern**: Complex pairing pattern optimized for sum rate
- **May have**: Shorter lines but better overall performance

### 4. Clustering Comparison (`clustering_comparison.png`)
Four-panel performance comparison:

#### Top Left: Total Throughput Comparison
- Bar chart comparing total system throughput
- Y-axis: Total throughput (Mbps)
- **Interpretation**: Higher bars = better overall performance

#### Top Right: NOMA vs OMA Distribution
- Grouped bar chart showing user distribution
- Blue bars: NOMA pairs count
- Orange bars: OMA users count
- **Interpretation**: More NOMA pairs ≠ necessarily better throughput

#### Bottom Left: Average Rates Comparison
- Compares average data rates for NOMA and OMA users
- Green bars: Average NOMA pair rate
- Purple bars: Average OMA user rate
- **Interpretation**: Shows per-user performance quality

#### Bottom Right: Throughput Share Pie Chart
- Shows percentage contribution of each method
- **Interpretation**: Visual representation of relative performance

## Key Metrics in Console Output

### Per-Method Statistics
```
STATIC CLUSTERING:
- NOMA Pairs: 150          # Number of user pairs using NOMA
- OMA Users: 200           # Number of users using OMA
- Total Throughput: 45.2 Mbps  # System-wide throughput
- NOMA Coverage: 60.0%     # Percentage of users in NOMA pairs
```

### Performance Indicators

#### High NOMA Coverage (>70%)
- **Good**: Many users benefit from NOMA
- **Risk**: May sacrifice overall throughput

#### High Total Throughput
- **Good**: System efficiency maximized
- **Trade-off**: May favor strong users

#### Balanced Performance
- **Good**: Fair resource distribution
- **Moderate**: Throughput and coverage

## Interpretation Guidelines

### Best Case Scenarios

#### For Static Clustering
- **High NOMA coverage** (users with very different channel qualities)
- **Good for fairness** (weak users paired with strong users)

#### For Balanced Clustering
- **Moderate performance across metrics**
- **Most predictable and stable results**

#### For Blossom Clustering
- **Highest total throughput** (optimal mathematical solution)
- **Best for system capacity maximization**

### Red Flags to Look For

#### Low NOMA Coverage (<30%)
- **Cause**: SIC threshold too high or poor channel conditions
- **Solution**: Reduce SIC threshold or increase user density

#### Huge Performance Gaps
- **Cause**: Extreme channel variations
- **Observation**: Some methods may fail completely

#### Similar Performance Across Methods
- **Cause**: Limited NOMA opportunities
- **Observation**: Channel conditions not suitable for NOMA benefits

## CSV Data Interpretation

### Enhanced h_values.csv Structure

The enhanced channel data file now includes comprehensive information:

```csv
User_ID,x_coord_m,y_coord_m,distance_m,angle_rad,path_loss_dB,path_loss_linear,shadowing_dB,rayleigh_fading,h_linear,h_dB
0,1234.5,-2341.2,2678.3,1.234,-95.4,2.88e-10,-3.2,1.234,3.46e-10,-119.99
```

#### Key Columns for Analysis

##### Spatial Information
- **`x_coord_m`, `y_coord_m`**: User positions for spatial analysis
- **`distance_m`**: Distance from base station (useful for coverage analysis)
- **`angle_rad`**: Angular position (useful for sector analysis)

##### Channel Components
- **`path_loss_dB`**: Large-scale path loss (distance-dependent)
- **`shadowing_dB`**: Log-normal shadowing component (environmental effects)
- **`rayleigh_fading`**: Small-scale fading coefficient (multipath effects)
- **`h_linear`**: Final channel gain = fading × √(path_loss_linear)
- **`h_dB`**: Channel gain in dB = 10×log₁₀(h_linear²)

### Analysis Examples

#### Spatial-Channel Correlation
```python
# Load enhanced data
df = pd.read_csv('simulation_results/.../h_values.csv')

# Analyze distance vs channel quality
plt.scatter(df['distance_m'], df['h_dB'])
plt.xlabel('Distance from BS (m)')
plt.ylabel('Channel Gain (dB)')

# Find users in specific regions
center_users = df[df['distance_m'] < 1000]  # Users near center
edge_users = df[df['distance_m'] > 4000]    # Users near edge
```

#### Channel Component Analysis
```python
# Separate effects of different channel components
plt.figure(figsize=(12, 8))

# Path loss effect
plt.subplot(2,2,1)
plt.scatter(df['distance_m'], df['path_loss_dB'])
plt.title('Path Loss vs Distance')

# Shadowing distribution
plt.subplot(2,2,2)
plt.hist(df['shadowing_dB'], bins=30)
plt.title('Shadowing Distribution')

# Fading distribution
plt.subplot(2,2,3)
plt.hist(df['rayleigh_fading'], bins=30)
plt.title('Rayleigh Fading Distribution')

# Overall channel gain
plt.subplot(2,2,4)
plt.hist(df['h_dB'], bins=30)
plt.title('Overall Channel Gain Distribution')
```

## Troubleshooting Common Issues

### No NOMA Pairs Found
- **Check**: SIC threshold too high (reduce from 8 dB to 3-5 dB)
- **Check**: User distribution too uniform

### Poor Performance Across All Methods
- **Check**: Channel model parameters
- **Check**: Noise power too high relative to signal power

### Visualization Issues
- **Missing plots**: Check file permissions in results/ directory
- **Empty plots**: Verify data generation completed successfully

## Next Steps for Analysis

### Detailed Performance Analysis
1. **Load and compare** all CSV files
2. **Calculate fairness indices** across user rates
3. **Analyze spatial patterns** in pairing decisions

### Parameter Sensitivity
1. **Vary SIC threshold** (3-12 dB) and observe impact
2. **Change user density** and see coverage changes
3. **Modify power allocation** strategies

### Advanced Visualizations
1. **Heat maps** of channel quality vs position
2. **Time-series analysis** for dynamic scenarios
3. **3D visualizations** for multi-dimensional analysis

---

*This guide helps interpret all generated visualizations and metrics from the NOMA clustering simulation.*
