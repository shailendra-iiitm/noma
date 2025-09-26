import numpy as np
import matplotlib.pyplot as plt

# Parameters
np.random.seed(42)
N = 5000
radius = 2000
path_loss_exponent = 3.5
noise_power = 1e-9
total_power = 1.0
sic_threshold_db = 8

# Step 1: User placement
r = np.sqrt(np.random.uniform(0, radius**2, N))
theta = np.random.uniform(0, 2 * np.pi, N)
x_coords = r * np.cos(theta)
y_coords = r * np.sin(theta)
distances = np.sqrt(x_coords**2 + y_coords**2)
fading = np.random.rayleigh(scale=1.0, size=N)
h_values = fading / (distances ** path_loss_exponent)

sorted_indices = np.argsort(h_values)
results_static = []
total_rate_static = 0
used_static = np.zeros(N, dtype=bool)

# Balanced Pairing: i ↔ i + N/2
results_balanced = []
total_rate_balanced = 0
used_balanced = np.zeros(N, dtype=bool)

for i in range(N // 2):
    u1 = sorted_indices[i]
    u2 = sorted_indices[i + N // 2]
    h1, h2 = h_values[u1], h_values[u2]
    delta_db = 10 * np.log10(h2 / h1)
    if delta_db >= sic_threshold_db:
        P1 = total_power * h2 / (h1 + h2)
        P2 = total_power * h1 / (h1 + h2)
        R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))
        R2 = np.log2(1 + (P2 * h2) / noise_power)
        results_balanced.append((u1, u2, R1, R2))
        total_rate_balanced += R1 + R2
        used_balanced[u1] = used_balanced[u2] = True

num_balanced_pairs = len(results_balanced)
num_balanced_oma = N - 2 * num_balanced_pairs

# Plot Balanced Pairing
plt.figure(figsize=(10, 10))
plt.scatter(x_coords, y_coords, s=1, color='gray', label='All Users')
for u1, u2, _, _ in results_balanced:
    plt.plot([x_coords[u1], x_coords[u2]], [y_coords[u1], y_coords[u2]], 'g-', alpha=0.6, linewidth=0.5)
unpaired_bal = [i for i in range(N) if not used_balanced[i]]
plt.plot(x_coords[unpaired_bal], y_coords[unpaired_bal], 'ro', markersize=2, label='OMA Users')
plt.scatter(0, 0, c='black', marker='x', s=100, label='Base Station')
plt.title(f"Balanced Pairing (i ↔ i + N/2)\nNOMA Pairs: {num_balanced_pairs}, OMA Users: {num_balanced_oma}, Total Rate: {total_rate_balanced:.2f} bits/s/Hz")
plt.xlabel("X (m)")
plt.ylabel("Y (m)")
plt.axis('equal')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
