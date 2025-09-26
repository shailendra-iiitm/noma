import numpy as np
import matplotlib.pyplot as plt

# Parameters
np.random.seed(42)
N = 2000
radius = 5000
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

# Method 1: i to (n-1-i) pairing
for i in range(N // 2):
    u1 = sorted_indices[i]
    u2 = sorted_indices[N - 1 - i]
    h1, h2 = h_values[u1], h_values[u2]
    delta_db = 10 * np.log10(h2 / h1)
    if delta_db >= sic_threshold_db:
        P1 = total_power * h2 / (h1 + h2)
        P2 = total_power * h1 / (h1 + h2)
        R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))
        R2 = np.log2(1 + (P2 * h2) / noise_power)
        results_static.append((u1, u2, R1, R2))
        total_rate_static += R1 + R2
        used_static[u1] = used_static[u2] = True

num_pairs = len(results_static)
num_oma = N - 2 * num_pairs

# Plot Static Pairing
plt.figure(figsize=(10, 10))
plt.scatter(x_coords, y_coords, s=1, color='gray', label='All Users')
for u1, u2, _, _ in results_static:
    plt.plot([x_coords[u1], x_coords[u2]], [y_coords[u1], y_coords[u2]], 'b-', alpha=0.6, linewidth=0.5)
unpaired = [i for i in range(N) if not used_static[i]]
plt.plot(x_coords[unpaired], y_coords[unpaired], 'ro', markersize=2, label='OMA Users')
plt.scatter(0, 0, c='black', marker='x', s=100, label='Base Station')
plt.title(f"i ↔ n-1-i Pairing\nNOMA Pairs: {num_pairs}, OMA Users: {num_oma}, Total Rate: {total_rate_static:.2f} bits/s/Hz")
plt.xlabel("X (m)")
plt.ylabel("Y (m)")
plt.axis('equal')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
