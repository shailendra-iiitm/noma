import numpy as np
import pandas as pd

# Constants
N = 200
noise_power = 1e-9
total_power = 1.0
per_user_power = total_power / N

# Load NOMA results from previous step
noma_df = pd.read_csv('/mnt/data/noma_oma_maxrate_with_failures.csv')
noma_sum_rate = noma_df[noma_df['Mode'] == 'NOMA']['R_sum'].sum()
oma_users = noma_df['User1_ID'].unique()

# Generate fading and distances again to get h
np.random.seed(42)
radius = 500
inner_users = 20
inner_r = np.sqrt(np.random.uniform(0, 100**2, inner_users))
inner_theta = np.random.uniform(0, 2 * np.pi, inner_users)
inner_x = inner_r * np.cos(inner_theta)
inner_y = inner_r * np.sin(inner_theta)
outer_r = np.sqrt(np.random.uniform(100**2, radius**2, N - inner_users))
outer_theta = np.random.uniform(0, 2 * np.pi, N - inner_users)
outer_x = outer_r * np.cos(outer_theta)
outer_y = outer_r * np.sin(outer_theta)
x_coords = np.concatenate((inner_x, outer_x))
y_coords = np.concatenate((inner_y, outer_y))
distances = np.sqrt(x_coords**2 + y_coords**2)
fading = np.random.rayleigh(scale=1.0, size=N)
path_loss_exponent = 3.5
h_values = fading / (distances ** path_loss_exponent)

# OMA: Each user gets 1/N share of time/frequency
oma_rates = [(1/N) * np.log2(1 + (total_power * h) / noise_power) for h in h_values]
oma_sum_rate = np.sum(oma_rates)

# Final comparison
noma_sum_rate, oma_sum_rate
