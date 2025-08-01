import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ===================== Parameters =====================
np.random.seed(42)
N = 500                   # number of users
radius = 5000             # cell radius in meters
fc = 3.5e9                # carrier frequency (Hz) - 3.5 GHz typical for 5G
c = 3e8                   # speed of light
lambda_c = c / fc         # wavelength
n = 3.5                   # path-loss exponent (urban macro)
shadowing_std_db = 8      # log-normal shadowing std dev in dB
scale_rayleigh = 1.0      # Rayleigh fading scale

# ===================== User Placement =====================
r = np.sqrt(np.random.uniform(0, radius**2, N))  # random distance
theta = np.random.uniform(0, 2 * np.pi, N)
x_coords = r * np.cos(theta)
y_coords = r * np.sin(theta)

# ===================== Large-Scale Path Loss =====================
pl_1m_db = 20 * np.log10(4 * np.pi * 1 / lambda_c)
shadowing = np.random.normal(0, shadowing_std_db, N)
pl_db = pl_1m_db + 10 * n * np.log10(r) + shadowing
pl_linear = 10 ** (-pl_db / 10)

# ===================== Small-Scale Fading =====================
rayleigh_fading = np.random.rayleigh(scale=scale_rayleigh, size=N)

# ===================== Channel Gain h =====================
h_values = rayleigh_fading * np.sqrt(pl_linear)
h_db = 10 * np.log10(h_values**2 + 1e-12)
h_norm = h_values / np.max(h_values)

# ===================== Save to DataFrame =====================
df = pd.DataFrame({
    "User_ID": np.arange(1, N + 1),
    "x": x_coords,
    "y": y_coords,
    "theta_rad": theta,
    "distance_m": r,
    "shadowing_dB": shadowing,
    "path_loss_dB": pl_db,
    "path_loss_linear": pl_linear,
    "fading_rayleigh": rayleigh_fading,
    "h_linear": h_values,
    "h_dB": h_db,
    "h_normalized": h_norm
})
# ===================== Save DataFrame to CSV =====================
csv_path = "h_values_3gpp_uma.csv"
df.to_csv(csv_path, index=False)
print(f"Data successfully saved to: {csv_path}")


# ===================== Plot User Distribution =====================
plt.figure(figsize=(8, 8))
plt.scatter(x_coords, y_coords, c=h_norm, cmap='viridis', s=20)
plt.colorbar(label='Normalized h')
plt.xlabel("X position (m)")
plt.ylabel("Y position (m)")
plt.title("User Distribution with Normalized Channel Gains")
plt.grid(True)
plt.show()

# ===================== Plot h Distributions =====================
plt.figure(figsize=(15, 5))

plt.subplot(1, 3, 1)
plt.hist(h_values, bins=40, color='blue', alpha=0.7)
plt.xlabel("h (linear)")
plt.ylabel("Count")
plt.title("Raw Channel Gain Distribution")

plt.subplot(1, 3, 2)
plt.hist(h_norm, bins=40, color='green', alpha=0.7)
plt.xlabel("h_normalized")
plt.ylabel("Count")
plt.title("Normalized Channel Gain Distribution")

plt.subplot(1, 3, 3)
plt.hist(h_db, bins=40, color='orange', alpha=0.7)
plt.xlabel("h (dB)")
plt.ylabel("Count")
plt.title("Channel Gain in dB Distribution")

plt.tight_layout()
plt.show()


