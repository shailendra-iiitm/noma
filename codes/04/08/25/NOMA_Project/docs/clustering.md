# Clustering Module Documentation

## Detailed Technical Documentation

### 1. System Parameters & Initialization

#### Physical Parameters
- **Cell Configuration**
  - Users (N): 1100
  - Cell radius: 5000m
  - Base station height (h_BS): 25m
  - User heights (h_UTs): Uniform random between 1.5m – 22.5m (3GPP UMa limits)

#### Radio Parameters
- **Carrier Configuration**
  - Frequency (fc): 3.5 GHz
  - Wavelength (λ): Calculated from speed of light (c/fc)
  - Total bandwidth (B_total): 20 MHz

#### Channel Parameters
- **Path Loss Parameters**
  - Path loss exponent: 3.5
  - Shadow fading std: 8 dB
  - Reference path loss at 1m: 20 log₁₀(4π/λ)

#### System Parameters
- **Power Settings**
  - Noise power: 10⁻⁹
  - Total power: 1.0
  - SIC threshold: 8 dB

### 2. User Placement Implementation

#### Position Generation
```python
r = np.sqrt(np.random.uniform(0, radius**2, N))  # 2D distance from BS
theta = np.random.uniform(0, 2*np.pi, N)
x_coords, y_coords = r * np.cos(theta), r * np.sin(theta)
```

- Uniform distribution in circular cell
- Random height assignment within UMa limits
- Coordinates stored in both polar and Cartesian forms

### 3. Channel Modeling

#### LOS Probability (3GPP TR 38.901)
1. **C_hUT Function**
   ```python
   def C_hUT(h_UT):
       if h_UT <= 13:
           return 0
       elif h_UT < 23:
           return ((h_UT - 13) / 10) ** 1.5
       else:
           return ((23 - 13) / 10) ** 1.5
   ```
   - Corrects probability based on user height
   - Three regimes based on height thresholds

2. **LOS Probability Calculation**
   ```python
   def prob_LOS_UMa(d_2D_out, h_UT):
       # Implementation following 3GPP specification
       # Returns probability between 0 and 1
   ```
   - Based on 2D distance and user height
   - Includes height correction factor

#### Path Loss Models

1. **LOS Path Loss**
   ```python
   def PL_UMa_LOS(d_3D, fc):
       return 28.0 + 22 * np.log10(d_3D) + 20 * np.log10(fc / 1e9)
   ```

2. **NLOS Path Loss**
   ```python
   def PL_UMa_NLOS(d_3D, fc, h_UT):
       return 13.54 + 39.08 * np.log10(d_3D) + 20 * np.log10(fc / 1e9) - 0.6 * (h_UT - 1.5)
   ```

### 4. Fading Implementation

#### Small-Scale Fading
1. **LOS Users**: Rician fading
   - K-factor: 9 dB
   - Complex Gaussian components

2. **NLOS Users**: Rayleigh fading
   - Scale parameter: 1.0

### 5. Channel Gain Calculation

#### Complete Channel Model
1. Path Loss (with shadowing)
2. Small-scale fading
3. Final channel gain calculation:
   ```python
   h_values = fading * np.sqrt(pl_with_shadowing_linear)
   h_db = 20 * np.log10(h_values + 1e-12)
   ```

### 6. NOMA Pairing Logic

#### SIC Condition Check
```python
def sic_satisfied(h1, h2):
    # Determines if SIC is possible between two users
    # Returns boolean based on SINR threshold
```

#### Rate Calculation
```python
def calc_pair_rate(h1, h2):
    # Calculates achievable rates for NOMA pair
    # Returns powers and rates for both users
```

Key Components:
1. Power allocation between users
2. SINR calculation
3. Rate computation for both users

### 7. Data Storage and Analysis

#### User Data Storage
- Comprehensive DataFrame including:
  - Spatial coordinates
  - Channel components
  - Path loss values
  - Fading coefficients
  - Final channel gains

#### Visualization Capabilities
1. **User Distribution Plot**
   - Spatial distribution
   - Channel gain overlay
   - Cell boundary

2. **Channel Characteristics Analysis**
   - Gain distribution
   - Path loss vs. distance
   - Fading distribution
   - Sorted channel gains

### 8. Performance Metrics

1. **Channel Quality Metrics**
   - Path loss range
   - Shadowing distribution
   - Fading statistics

2. **System Performance**
   - Number of LOS/NLOS users
   - Channel gain distribution
   - SIC success rate

### 9. Implementation Notes

#### Key Features
1. Accurate 3GPP channel modeling
2. Comprehensive user data tracking
3. Detailed visualization options
4. Modular rate calculation

#### Best Practices
1. Regular validation of channel components
2. Data persistence for analysis
3. Visualization for debugging
4. Parameter documentation

### 10. Usage Guidelines

1. **Parameter Configuration**
   - Set system parameters
   - Configure cell geometry
   - Adjust channel model parameters

2. **Execution Flow**
   1. Initialize parameters
   2. Generate user positions
   3. Calculate channel components
   4. Perform user pairing
   5. Calculate system performance

3. **Results Analysis**
   - Review generated plots
   - Analyze stored data
   - Validate performance metrics
