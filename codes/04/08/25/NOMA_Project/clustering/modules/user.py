import numpy as np
from typing import Tuple, List

class UserPlacement:
    def __init__(self, num_users: int, radius: float, h_BS: float = 25):
        """
        Initialize user placement parameters
        Args:
            num_users: Number of users to place
            radius: Cell radius in meters
            h_BS: Base station height in meters
        """
        self.N = num_users
        self.radius = radius
        self.h_BS = h_BS
        
    def generate_positions(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate random user positions in circular cell"""
        # Generate r and theta
        r = np.sqrt(np.random.uniform(0, self.radius**2, self.N))
        theta = np.random.uniform(0, 2*np.pi, self.N)
        
        # Convert to Cartesian coordinates
        x_coords = r * np.cos(theta)
        y_coords = r * np.sin(theta)
        
        # Generate heights (1.5m – 22.5m per 3GPP UMa)
        h_UTs = np.random.uniform(1.5, 22.5, self.N)
        
        return r, theta, h_UTs
    
    def get_3D_distances(self, r: np.ndarray, h_UTs: np.ndarray) -> np.ndarray:
        """Calculate 3D distances between BS and users"""
        return np.sqrt(r**2 + (self.h_BS - h_UTs)**2)
    
    def get_cartesian_coords(self, r: np.ndarray, theta: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Get x,y coordinates from polar coordinates"""
        return r * np.cos(theta), r * np.sin(theta)

    def get_user_info(self) -> dict:
        """Generate complete user placement information"""
        # Generate basic positions
        r, theta, h_UTs = self.generate_positions()
        x_coords, y_coords = self.get_cartesian_coords(r, theta)
        d_3D = self.get_3D_distances(r, h_UTs)
        
        return {
            'r': r,
            'theta': theta,
            'h_UTs': h_UTs,
            'x_coords': x_coords,
            'y_coords': y_coords,
            'd_3D': d_3D,
            'h_BS': self.h_BS
        }
