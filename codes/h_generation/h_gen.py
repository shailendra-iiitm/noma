import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Set seed for reproducibility
np.random.seed(42)

# Parameters
total_users = 200
inner_circle_users = 20
outer_circle_users = total_users - inner_circle_users
radius = 500  # meters
path_loss_exponent = 3.5

# Generate inner circle users uniformly within 100m
inner_r = np.sqrt(np.random.uniform(0, 100**2, inner_circle_users))
inner_theta = np.random.uniform(0, 2 * np.pi, inner_circle_users)
inner_x = inner_r * np.cos(inner_theta)
inner_y = inner_r * np.sin(inner_theta)

# Generate outer circle users uniformly between 100m and 500m
outer_r = np.sqrt(np.random.uniform(100**2, radius**2, outer_circle_users))
outer_theta = np.random.uniform(0, 2 * np.pi, outer_circle_users)
outer_x = outer_r * np.cos(outer_theta)
outer_y = outer_r * np.sin(outer_theta)

# Combine coordinates
x_coords = np.concatenate((inner_x, outer_x))
y_coords = np.concatenate((inner_y, outer_y))

# Compute distances from base station (0,0)
distances = np.sqrt(x_coords**2 + y_coords**2)

# Simulate Rayleigh fading
fading = np.random.rayleigh(scale=1.0, size=total_users)

# Calculate channel gains h_i = fading / (distance^alpha)
h_values = fading / (distances ** path_loss_exponent)

# Store data in DataFrame
df = pd.DataFrame({
    'User_ID': np.arange(1, total_users + 1),
    'X': x_coords,
    'Y': y_coords,
    'Distance_from_BS': distances,
    'Channel_Gain_h': h_values
})

# Save to CSV (output file for VS Code)
df.to_csv('user_channel_data_200.csv', index=False)

# Plot users and BS
plt.figure(figsize=(8, 8))
plt.scatter(x_coords, y_coords, c='blue', label='Users')
plt.scatter(0, 0, c='red', label='Base Station (0,0)', marker='x')
plt.title("200 User Locations within 500m Cell")
plt.xlabel("X coordinate (m)")
plt.ylabel("Y coordinate (m)")
plt.axis('equal')
plt.grid(True)
plt.legend()
plt.show()
