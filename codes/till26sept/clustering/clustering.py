import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

# Parameters
np.random.seed(42)
N = 5000
radius = 2000
inner_users = 400
path_loss_exponent = 3.5
noise_power = 1e-9
total_power = 1.0
sic_threshold_db = 8

# Step 1: Generate user positions
inner_r = np.sqrt(np.random.uniform(0, 500**2, inner_users))
inner_theta = np.random.uniform(0, 2 * np.pi, inner_users)
inner_x = inner_r * np.cos(inner_theta)
inner_y = inner_r * np.sin(inner_theta)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Parameters
np.random.seed(42)
N = 50000
radius = 2000
inner_users = 400
path_loss_exponent = 3.5
noise_power = 1e-9
total_power = 1.0
sic_threshold_db = 8

# Step 1: User placement
inner_r = np.sqrt(np.random.uniform(0, 500**2, inner_users))
inner_theta = np.random.uniform(0, 2 * np.pi, inner_users)
inner_x = inner_r * np.cos(inner_theta)
inner_y = inner_r * np.sin(inner_theta)

outer_r = np.sqrt(np.random.uniform(400**2, radius**2, N - inner_users))
outer_theta = np.random.uniform(0, 2 * np.pi, N - inner_users)
outer_x = outer_r * np.cos(outer_theta)
outer_y = outer_r * np.sin(outer_theta)

x_coords = np.concatenate((inner_x, outer_x))
y_coords = np.concatenate((inner_y, outer_y))
distances = np.sqrt(x_coords**2 + y_coords**2)
fading = np.random.rayleigh(scale=1.0, size=N)
h_values = fading / (distances ** path_loss_exponent)

# Step 2: Sort users by h
sorted_indices = np.argsort(h_values)
used = np.zeros(N, dtype=bool)
results = []
cluster_id = 0
i = 0
j = N - 1

while i < j:
    u1 = sorted_indices[i]
    u2 = sorted_indices[j]
    h1, h2 = h_values[u1], h_values[u2]
    delta_db = 10 * np.log10(h2 / h1)

    if delta_db >= sic_threshold_db:
        P1 = total_power * h2 / (h1 + h2)
        P2 = total_power * h1 / (h1 + h2)
        R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))
        R2 = np.log2(1 + (P2 * h2) / noise_power)
        results.append({
            'User1_ID': u1, 'User2_ID': u2,
            'h1': h1, 'h2': h2,
            'P1': P1, 'P2': P2,
            'R1': R1, 'R2': R2,
            'R_sum': R1 + R2,
            'Mode': 'NOMA', 'Cluster_ID': cluster_id
        })
        used[u1] = used[u2] = True
        cluster_id += 1
        i += 1
        j -= 1
    else:
        i += 1  # skip weak user if pairing is not SIC-feasible

# Step 3: OMA fallback
for u in range(N):
    if not used[u]:
        h = h_values[u]
        R = np.log2(1 + (total_power * h) / noise_power)
        results.append({
            'User1_ID': u, 'User2_ID': -1,
            'h1': h, 'h2': 0,
            'P1': total_power, 'P2': 0,
            'R1': R, 'R2': 0,
            'R_sum': R,
            'Mode': 'OMA', 'Cluster_ID': cluster_id
        })
        cluster_id += 1

df_results = pd.DataFrame(results)
df_results.to_csv("noma_oma_pairing_50k.csv", index=False)

# Summary
noma_clusters = df_results[df_results['Mode'] == 'NOMA'].shape[0]
oma_users = df_results[df_results['Mode'] == 'OMA'].shape[0]
avg_noma_rate = df_results[df_results['Mode'] == 'NOMA']['R_sum'].mean()
total_rate = df_results['R_sum'].sum()

print("✔️ Efficient Clustering Done for 50,000 users")
print(f"NOMA Clusters         : {noma_clusters}")
print(f"OMA Users (unpaired)  : {oma_users}")
print(f"Avg NOMA Cluster Rate : {avg_noma_rate:.4f} bits/s/Hz")
print(f"Total System Rate     : {total_rate:.4f} bits/s/Hz")

# Optional: Plot 500 random users for visualization
sample_ids = np.random.choice(N, 500, replace=False)
plt.figure(figsize=(10, 10))
plt.scatter(x_coords[sample_ids], y_coords[sample_ids], c='gray', s=2, label="Sample Users")
plt.scatter(0, 0, c='red', marker='x', s=100, label='Base Station')
plt.title("Random Sample of 50,000 Users in 4km Cell")
plt.xlabel("X (meters)")
plt.ylabel("Y (meters)")
plt.axis('equal')
plt.legend()
plt.grid(True)
plt.show()


outer_r = np.sqrt(np.random.uniform(400**2, radius**2, N - inner_users))
outer_theta = np.random.uniform(0, 2 * np.pi, N - inner_users)
outer_x = outer_r * np.cos(outer_theta)
outer_y = outer_r * np.sin(outer_theta)

x_coords = np.concatenate((inner_x, outer_x))
y_coords = np.concatenate((inner_y, outer_y))
distances = np.sqrt(x_coords**2 + y_coords**2)
fading = np.random.rayleigh(scale=1.0, size=N)
h_values = fading / (distances ** path_loss_exponent)

# Step 2: Build graph with valid NOMA pairings
G = nx.Graph()
for i in range(N):
    for j in range(i + 1, N):
        h1, h2 = sorted([h_values[i], h_values[j]])
        delta_db = 10 * np.log10(h2 / h1)
        if delta_db >= sic_threshold_db:
            P1 = total_power * h2 / (h1 + h2)
            P2 = total_power * h1 / (h1 + h2)
            R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + noise_power))
            R2 = np.log2(1 + (P2 * h2) / noise_power)
            Rsum = R1 + R2
            G.add_edge(i, j, weight=Rsum, h1=h1, h2=h2, P1=P1, P2=P2, R1=R1, R2=R2)

# Step 3: Max-Weight Matching
matches = nx.max_weight_matching(G, maxcardinality=True)
matched_users = set()
results = []
cluster_id = 0

for u, v in matches:
    edge = G[u][v]
    results.append({
        'User1_ID': u, 'User2_ID': v,
        'h1': edge['h1'], 'h2': edge['h2'],
        'P1': edge['P1'], 'P2': edge['P2'],
        'R1': edge['R1'], 'R2': edge['R2'],
        'R_sum': edge['R1'] + edge['R2'],
        'Mode': 'NOMA', 'Cluster_ID': cluster_id
    })
    matched_users.update([u, v])
    cluster_id += 1

# Step 4: OMA fallback for unpaired users
for u in range(N):
    if u not in matched_users:
        h = h_values[u]
        R = np.log2(1 + (total_power * h) / noise_power)
        results.append({
            'User1_ID': u, 'User2_ID': -1,
            'h1': h, 'h2': 0,
            'P1': total_power, 'P2': 0,
            'R1': R, 'R2': 0,
            'R_sum': R,
            'Mode': 'OMA', 'Cluster_ID': cluster_id
        })
        cluster_id += 1

df_results = pd.DataFrame(results)

# Step 5: Save CSV
df_results.to_csv("noma_oma_pairing_5k.csv", index=False)

# Identify matched and unmatched users
noma_df = df_results[df_results['Mode'] == 'NOMA']
oma_df = df_results[df_results['Mode'] == 'OMA']

# Create a plot for all 50,00 users
plt.figure(figsize=(12, 12))
plt.scatter(x_coords, y_coords, s=1, color='lightgray', label="All Users")

# Plot NOMA pairs (blue lines)
for _, row in noma_df.iterrows():
    u1 = int(row['User1_ID'])
    u2 = int(row['User2_ID'])
    x1, y1 = x_coords[u1], y_coords[u1]
    x2, y2 = x_coords[u2], y_coords[u2]
    plt.plot([x1, x2], [y1, y2], 'b-', linewidth=0.5, alpha=0.6)

# Plot unmatched OMA users (red)
for _, row in oma_df.iterrows():
    u = int(row['User1_ID'])
    plt.plot(x_coords[u], y_coords[u], 'ro', markersize=2)

# Base station
plt.scatter(0, 0, c='black', marker='x', s=100, label='Base Station')

# Final touches
plt.title("NOMA Clusters (Blue Lines) & OMA Users (Red Dots) among 50,000 Users")
plt.xlabel("X (meters)")
plt.ylabel("Y (meters)")
plt.axis('equal')
plt.grid(True)
plt.legend(loc='upper right')
plt.tight_layout()
plt.show()
