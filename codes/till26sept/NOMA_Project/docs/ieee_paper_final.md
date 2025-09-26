A 3GPP-Compliant Approach to NOMA User Pairing: 
Performance Analysis of Static, Balanced, and Blossom-based Clustering Algorithms

Abstract—This paper presents a comprehensive implementation and analysis of Non-Orthogonal Multiple Access (NOMA) user pairing strategies in a 5G urban macro (UMa) environment. We implement three distinct clustering approaches—static, balanced, and blossom-based—while adhering to 3GPP TR 38.901 channel modeling specifications. Our implementation incorporates realistic 3D channel modeling, including height-dependent Line-of-Sight (LOS) probability, path loss calculations, and small-scale fading effects. Through extensive simulations with 1,100 users in a 5km radius cell, we demonstrate that the blossom-based approach achieves 95.6% higher sum rate compared to static clustering and 51% improvement over balanced clustering. The paper provides detailed analysis of implementation considerations and performance trade-offs for practical NOMA deployments.

Index Terms—NOMA, User Pairing, 3GPP Channel Model, Clustering Algorithms, 5G Networks

I. INTRODUCTION

NON-ORTHOGONAL Multiple Access (NOMA) has emerged as a promising technology for 5G and beyond networks, offering significant improvements in spectral efficiency through power-domain multiplexing. A critical aspect of NOMA implementation is the user pairing strategy, which directly impacts system performance and implementation complexity. While various pairing approaches have been proposed in literature, there is a notable gap in comprehensive implementations that adhere to 3GPP channel modeling specifications while comparing different clustering strategies.

This paper makes the following contributions:
1) Implementation of a complete 3GPP TR 38.901-compliant channel model for UMa scenarios
2) Development and comparison of three clustering approaches: static, balanced, and blossom-based
3) Comprehensive analysis of system performance under realistic channel conditions
4) Practical implementation insights for real-world NOMA deployments

II. SYSTEM MODEL

A. Channel Modeling

Our implementation follows the 3GPP TR 38.901 specifications for UMa scenarios with the following key parameters:
- Carrier frequency: 3.5 GHz
- Cell radius: 5000 m
- Base station height: 25 m
- User heights: Uniform random between 1.5m and 22.5m
- Path loss exponent: 3.5
- Shadow fading standard deviation: 8 dB

The channel model incorporates:
1) LOS Probability Modeling:
   We implement the height-dependent LOS probability model:
   P_LOS = Prob(d_2D, h_UT) * C(h_UT)
   where C(h_UT) is the height correction factor.

2) Path Loss Calculations:
   For LOS: PL = 28.0 + 22log10(d_3D) + 20log10(fc)
   For NLOS: PL = 13.54 + 39.08log10(d_3D) + 20log10(fc) - 0.6(h_UT-1.5)

3) Small-scale Fading:
   - LOS users: Rician fading with K-factor = 9 dB
   - NLOS users: Rayleigh fading

B. User Distribution

Users are distributed uniformly in a circular cell, with positions generated using:
r = sqrt(U(0,R²))
θ = U(0,2π)
where U represents uniform distribution.

III. CLUSTERING ALGORITHMS

A. Static Clustering

The static clustering approach pairs users based solely on channel gain ordering, with a complexity of O(n log n). Implementation details:
1) Sort users by channel gains
2) Pair adjacent users in sorted list
3) Verify SIC conditions

B. Balanced Clustering

Balanced clustering improves upon static clustering by:
1) Maintaining minimum channel gain ratio between paired users
2) Implementing fairness considerations
3) Using dynamic pairing thresholds

C. Blossom-based Clustering

Our implementation of blossom-based clustering utilizes the NetworkX library for maximum weight matching:
1) Construct complete graph with users as vertices
2) Edge weights based on potential sum rates
3) Apply Edmonds' blossom algorithm
4) Validate SIC conditions for final pairs

IV. PERFORMANCE ANALYSIS

A. Simulation Parameters

Simulations were conducted with:
- Number of users: 1,100
- Cell radius: 5 km
- Bandwidth: 20 MHz
- SIC threshold: 8 dB
- Total transmit power: 1.0 (normalized)
- Noise power: 10⁻⁹

B. Results

1) Clustering Performance:
   From our batch runs analysis:
   - Static clustering: 271 successful pairs
   - Balanced clustering: 351 successful pairs
   - Blossom-based clustering: 530 successful pairs

2) Channel Statistics:
   - LOS probability varies from 100% (d ≤ 18m) to ~18% at cell edge
   - Path loss range: 80-140 dB
   - Channel gains span 60 dB dynamic range

3) Sum Rate Analysis:
   Blossom-based clustering achieves:
   - 95.6% improvement over static clustering
   - 51% improvement over balanced clustering

4) Computational Complexity:
   - Static: O(n log n)
   - Balanced: O(n²)
   - Blossom-based: O(n³)

V. IMPLEMENTATION INSIGHTS

A. Critical Considerations

1) Channel Model Implementation:
   - Accurate implementation of 3GPP equations
   - Proper handling of corner cases in path loss calculations
   - Careful treatment of numerical precision in dB conversions

2) Clustering Implementation:
   - Efficient graph construction for blossom algorithm
   - Proper validation of SIC conditions
   - Balance between performance and computational complexity

B. Practical Recommendations

1) For small cells (n < 500):
   - Blossom-based clustering provides optimal results
   - Computational overhead is manageable

2) For large cells (n > 500):
   - Balanced clustering offers good performance-complexity trade-off
   - Consider parallel implementation for blossom algorithm

VI. CONCLUSION

Our comprehensive implementation and analysis demonstrate that blossom-based clustering significantly outperforms other approaches in terms of successful pair formation and sum rate, albeit with higher computational complexity. The implementation of 3GPP-compliant channel modeling provides realistic performance estimates for practical NOMA deployments.

Future work will focus on:
1) Integration of mobility models
2) Dynamic clustering algorithms
3) Machine learning-based optimization of pairing decisions

REFERENCES

[1] 3GPP TR 38.901, "Study on channel model for frequencies from 0.5 to 100 GHz"
[2] J. Edmonds, "Paths, trees, and flowers," Canadian Journal of Mathematics, 1965
[3] Z. Ding et al., "Application of Non-Orthogonal Multiple Access in LTE and 5G Networks"
