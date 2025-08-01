import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import networkx as nx

# Parameters
np.random.seed(42)
N = 500
radius = 5000
fc = 3.5e9
c = 3e8
lambda_c = c / fc
path_loss_exp = 3.5
shadow_std_db = 8
noise_power = 1e-9
total_power = 1.0
sic_threshold_db = 8
B_total = 20e6

# User Placement
r = np.sqrt(np.random.uniform(0, radius**2, N))
theta = np.random.uniform(0, 2*np.pi, N)
x_coords = r * np.cos(theta)
y_coords = r * np.sin(theta)

# Path Loss & Shadowing
pl_1m_db = 20 * np.log10(4 * np.pi / lambda_c)
shadowing = np.random.normal(0, shadow_std_db, N)
pl_db = pl_1m_db + 10 * path_loss_exp * np.log10(r) + shadowing
pl_linear = 10**(-pl_db/10)

# Small-Scale Fading (Rayleigh)
fading = np.random.rayleigh(scale=1.0, size=N)

# Channel Gain
h_values = fading * np.sqrt(pl_linear)
h_db = 10*np.log10(h_values**2 + 1e-12)
h_norm = h_values / np.max(h_values)

# Saving CSV
df_h = pd.DataFrame({
    "User_ID": np.arange(N),
    "x": x_coords, "y": y_coords,
    "theta_rad": theta, "distance_m": r,
    "shadowing_dB": shadowing, "path_loss_dB": pl_db,
    "fading_rayleigh": fading, "h_linear": h_values,
    "h_dB": h_db, "h_normalized": h_norm
})
df_h.to_csv("h_values_3gpp_uma.csv", index=False)
print("h values saved to h_values_3gpp_uma.csv")

# Visualizations
plt.figure(figsize=(8,8))
plt.scatter(x_coords,y_coords,c=h_norm,cmap='viridis',s=10)
plt.colorbar(label='Normalized h')
plt.title("User Distribution with Normalized h")
plt.grid(); plt.xlabel("X (m)"); plt.ylabel("Y (m)")
plt.show()

# Clustering Preparations
sorted_indices = np.argsort(h_values)

# Rate calculation function
def calc_pair_rate(h1,h2):
    P1=total_power*h2/(h1+h2)
    P2=total_power*h1/(h1+h2)
    R1=np.log2(1+(P1*h1)/(P2*h1+noise_power))
    R2=np.log2(1+(P2*h2)/noise_power)
    return P1,P2,R1,R2,R1+R2

summary=[]

# Common save function
def save_results(data,name):
    cols=["User1_ID","User2_ID","h1","h2","P1","P2",
          "R1_bitsHz","R2_bitsHz","R_sum_bitsHz",
          "Throughput_Mbps","Mode"]
    pd.DataFrame(data,columns=cols).to_csv(name,index=False)

# Static Pairing
static_pairs=[]; static_data=[]; used_static=np.zeros(N,bool)
for i in range(N//2):
    u1,u2=sorted_indices[i],sorted_indices[N-1-i]
    h1,h2=h_values[u1],h_values[u2]
    if 10*np.log10(h2/h1)>=sic_threshold_db:
        P1,P2,R1,R2,Rsum=calc_pair_rate(h1,h2)
        static_pairs.append((u1,u2)); used_static[[u1,u2]]=True

num_pairs_static=len(static_pairs)
num_oma_static=N-2*num_pairs_static
B_pair=B_total/(num_pairs_static+num_oma_static)

for u1,u2 in static_pairs:
    h1,h2=h_values[u1],h_values[u2]
    P1,P2,R1,R2,Rsum=calc_pair_rate(h1,h2)
    throughput=Rsum*B_pair/1e6
    static_data.append([u1,u2,h1,h2,P1,P2,R1,R2,Rsum,throughput,"NOMA"])

for u in range(N):
    if not used_static[u]:
        h=h_values[u];R1=np.log2(1+total_power*h/noise_power)
        throughput=R1*B_pair/1e6
        static_data.append([u,-1,h,0,total_power,0,R1,0,R1,throughput,"OMA"])
        
save_results(static_data,"static_clustering.csv")

# Visualization of Static Pairing
plt.figure(figsize=(8,8))
for u1,u2 in static_pairs:
    plt.plot([x_coords[u1],x_coords[u2]],
             [y_coords[u1],y_coords[u2]],'b-',linewidth=0.5)
plt.scatter(x_coords[~used_static],y_coords[~used_static],c='red',s=5)
plt.title("Static Pairing"); plt.grid(); plt.show()

# (Balanced & Blossom clustering implementations follow similarly...)

print("Integration complete, CSVs & plots saved.")

# ===================== Method 2: Balanced Pairing =====================
pairs_balanced = []
balanced_data = []
used_balanced = np.zeros(N, dtype=bool)
total_rate_balanced = 0
total_throughput_balanced = 0

for i in range(N // 2):
    u1, u2 = sorted_indices[i], sorted_indices[i + N // 2]
    h1, h2 = h_values[u1], h_values[u2]
    delta_db = 10 * np.log10(h2 / h1)
    if delta_db >= sic_threshold_db:
        P1, P2, R1, R2, R_sum = calc_pair_rate(h1, h2)
        pairs_balanced.append((u1, u2))
        total_rate_balanced += R_sum
        used_balanced[u1] = used_balanced[u2] = True

num_pairs_balanced = len(pairs_balanced)
num_oma_balanced = N - 2 * num_pairs_balanced
B_pair = B_total / (num_pairs_balanced + num_oma_balanced)

# Fill NOMA pairs
for u1, u2 in pairs_balanced:
    h1, h2 = h_values[u1], h_values[u2]
    P1, P2, R1, R2, R_sum = calc_pair_rate(h1, h2)
    throughput = R_sum * B_pair / 1e6
    total_throughput_balanced += throughput
    balanced_data.append([u1, u2, h1, h2, P1, P2, R1, R2, R_sum, throughput, "NOMA"])

# OMA fallback
for u in range(N):
    if not used_balanced[u]:
        h = h_values[u]
        R1_oma = np.log2(1 + (total_power * h) / noise_power)
        throughput = R1_oma * B_pair / 1e6
        total_throughput_balanced += throughput
        balanced_data.append([u, -1, h, 0, total_power, 0, R1_oma, 0, R1_oma, throughput, "OMA"])

avg_pair_rate_balanced = total_rate_balanced / (num_pairs_balanced + num_oma_balanced)
avg_user_rate_balanced = total_rate_balanced / N
summary.append(["Balanced", num_pairs_balanced, num_oma_balanced, total_rate_balanced, avg_pair_rate_balanced, avg_user_rate_balanced, total_throughput_balanced])
save_results(balanced_data, "balanced_clustering.csv")

# Plot Balanced
plt.figure(figsize=(10, 10))
plt.scatter(x_coords, y_coords, s=1, color='gray')
for u1, u2 in pairs_balanced:
    plt.plot([x_coords[u1], x_coords[u2]], [y_coords[u1], y_coords[u2]], 'g-', alpha=0.6, linewidth=0.5)
plt.plot(x_coords[~used_balanced], y_coords[~used_balanced], 'ro', markersize=2)
plt.scatter(0, 0, c='black', marker='x', s=100)
plt.title(f"Balanced Pairing: Noma_Pairs:{num_pairs_balanced} OMA_Users:{num_oma_balanced} Total Throughput={total_throughput_balanced:.2f} Mbps")
plt.axis('equal'); plt.grid(True); plt.tight_layout(); plt.show()

# ===================== Method 3: Blossom Pairing =====================
G = nx.Graph()
for i in range(N):
    for j in range(i + 1, N):
        h1, h2 = sorted([h_values[i], h_values[j]])
        delta_db = 10 * np.log10(h2 / h1)
        if delta_db >= sic_threshold_db:
            _, _, _, _, R_sum = calc_pair_rate(h1, h2)
            G.add_edge(i, j, weight=R_sum)

matches_blossom = list(nx.max_weight_matching(G, maxcardinality=True))
pairs_blossom = []
blossom_data = []
used_blossom = np.zeros(N, dtype=bool)
total_rate_blossom = 0
total_throughput_blossom = 0

for u1, u2 in matches_blossom:
    h1, h2 = h_values[u1], h_values[u2]
    P1, P2, R1, R2, R_sum = calc_pair_rate(min(h1, h2), max(h1, h2))
    pairs_blossom.append((u1, u2))
    total_rate_blossom += R_sum
    used_blossom[u1] = used_blossom[u2] = True

num_pairs_blossom = len(pairs_blossom)
num_oma_blossom = N - 2 * num_pairs_blossom
B_pair = B_total / (num_pairs_blossom + num_oma_blossom)

# Fill NOMA pairs
for u1, u2 in pairs_blossom:
    h1, h2 = h_values[u1], h_values[u2]
    P1, P2, R1, R2, R_sum = calc_pair_rate(min(h1, h2), max(h1, h2))
    throughput = R_sum * B_pair / 1e6
    total_throughput_blossom += throughput
    blossom_data.append([u1, u2, min(h1, h2), max(h1, h2), P1, P2, R1, R2, R_sum, throughput, "NOMA"])

# OMA fallback
for u in range(N):
    if not used_blossom[u]:
        h = h_values[u]
        R1_oma = np.log2(1 + (total_power * h) / noise_power)
        throughput = R1_oma * B_pair / 1e6
        total_throughput_blossom += throughput
        blossom_data.append([u, -1, h, 0, total_power, 0, R1_oma, 0, R1_oma, throughput, "OMA"])

avg_pair_rate_blossom = total_rate_blossom / (num_pairs_blossom + num_oma_blossom)
avg_user_rate_blossom = total_rate_blossom / N
summary.append(["Blossom", num_pairs_blossom, num_oma_blossom, total_rate_blossom, avg_pair_rate_blossom, avg_user_rate_blossom, total_throughput_blossom])
save_results(blossom_data, "blossom_clustering.csv")

# Plot Blossom
plt.figure(figsize=(10, 10))
plt.scatter(x_coords, y_coords, s=1, color='gray')
for u1, u2 in pairs_blossom:
    plt.plot([x_coords[u1], x_coords[u2]], [y_coords[u1], y_coords[u2]], 'purple', alpha=0.6, linewidth=0.5)
plt.plot(x_coords[~used_blossom], y_coords[~used_blossom], 'ro', markersize=2)
plt.scatter(0, 0, c='black', marker='x', s=100)
plt.title(f"Blossom Pairing: Noma_Pairs:{num_pairs_blossom} OMA_Users:{num_oma_blossom} Total Throughput={total_throughput_blossom:.2f} Mbps")
plt.axis('equal'); plt.grid(True); plt.tight_layout(); plt.show()

# ===================== Summary Table =====================
df_summary = pd.DataFrame(summary, columns=["Method", "NOMA Pairs", "OMA Users", "Total Rate (bits/s/Hz)", "Avg Pair Rate (bits/s/Hz)", "Avg User Rate (bits/s/Hz)", "Total Throughput (Mbps)"])
print("\nComparison of Clustering Methods:")
print(df_summary)
df_summary.to_csv("clustering_summary.csv", index=False)
