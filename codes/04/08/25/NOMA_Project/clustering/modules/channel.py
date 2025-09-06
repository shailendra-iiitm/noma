import numpy as np
from typing import Tuple, Dict

class ChannelModel:
    def __init__(self, fc: float = 3.5e9, shadow_std_db: float = 8):
        """
        Initialize channel model parameters
        Args:
            fc: Carrier frequency in Hz
            shadow_std_db: Shadowing standard deviation in dB
        """
        self.fc = fc
        self.c = 3e8  # Speed of light
        self.lambda_c = self.c / self.fc
        self.shadow_std_db = shadow_std_db
        self.K_factor_LOS_db = 9  # Rician K-factor for LOS
        
        # Path loss reference
        self.pl_1m_db = 20 * np.log10(4 * np.pi / self.lambda_c)
    
    def C_hUT(self, h_UT: float) -> float:
        """Calculate C(h_UT) for LOS probability"""
        if h_UT <= 13:
            return 0
        elif h_UT < 23:
            return ((h_UT - 13) / 10) ** 1.5
        else:
            return ((23 - 13) / 10) ** 1.5
    
    def prob_LOS_UMa(self, d_2D: np.ndarray, h_UT: np.ndarray) -> np.ndarray:
        """Calculate LOS probability for Urban Macro scenario"""
        P_LOS = np.zeros_like(d_2D, dtype=float)
        mask1 = d_2D <= 18
        P_LOS[mask1] = 1.0
        mask2 = ~mask1
        
        C_val = np.array([self.C_hUT(h) for h in h_UT])
        P_LOS[mask2] = (
            (18 / d_2D[mask2]) +
            np.exp(-d_2D[mask2] / 63) * (1 - 18 / d_2D[mask2])
        ) * (
            1 + C_val[mask2] * (5/4) * ((d_2D[mask2] / 100) ** 3) *
            np.exp(-d_2D[mask2] / 150)
        )
        return np.clip(P_LOS, 0, 1)
    
    def PL_UMa_LOS(self, d_3D: np.ndarray) -> np.ndarray:
        """Path loss model for LOS"""
        return 28.0 + 22 * np.log10(d_3D) + 20 * np.log10(self.fc / 1e9)
    
    def PL_UMa_NLOS(self, d_3D: np.ndarray, h_UT: np.ndarray) -> np.ndarray:
        """Path loss model for NLOS"""
        return 13.54 + 39.08 * np.log10(d_3D) + 20 * np.log10(self.fc / 1e9) - \
               0.6 * (h_UT - 1.5)
    
    def generate_channel_gains(self, user_info: Dict) -> Dict:
        """
        Generate complete channel gains for all users
        Args:
            user_info: Dictionary containing user placement information
        Returns:
            Dictionary with channel components
        """
        r = user_info['r']
        h_UTs = user_info['h_UTs']
        d_3D = user_info['d_3D']
        N = len(r)
        
        # Get LOS probabilities
        P_LOS_users = self.prob_LOS_UMa(r, h_UTs)
        
        # Initialize arrays
        PL_dB_no_shadow = np.zeros(N)
        is_LOS = np.zeros(N, dtype=bool)
        
        # Calculate path loss
        for i in range(N):
            if np.random.rand() <= P_LOS_users[i]:
                PL_dB_no_shadow[i] = self.PL_UMa_LOS(d_3D[i])
                is_LOS[i] = True
            else:
                PL_LOS_val = self.PL_UMa_LOS(d_3D[i])
                PL_NLOS_val = self.PL_UMa_NLOS(d_3D[i], h_UTs[i])
                PL_dB_no_shadow[i] = max(PL_LOS_val, PL_NLOS_val)
                is_LOS[i] = False
        
        # Generate shadowing
        shadowing = np.random.normal(0, self.shadow_std_db, N)
        PL_dB = PL_dB_no_shadow + shadowing
        
        # Generate small-scale fading
        K_linear = 10 ** (self.K_factor_LOS_db / 10)
        fading = np.zeros(N)
        
        for i in range(N):
            if is_LOS[i]:
                # Rician fading for LOS
                s = np.sqrt(K_linear / (K_linear + 1))
                sigma = np.sqrt(1 / (2 * (K_linear + 1)))
                complex_fading = np.random.normal(s, sigma) + 1j * np.random.normal(0, sigma)
                fading[i] = np.abs(complex_fading)
            else:
                # Rayleigh fading for NLOS
                fading[i] = np.random.rayleigh(scale=1.0)
        
        # Calculate final channel gains
        pl_linear = 10 ** (-PL_dB / 10)
        h_values = fading * np.sqrt(pl_linear)
        h_db = 20 * np.log10(h_values + 1e-12)
        
        return {
            'PL_dB_no_shadow': PL_dB_no_shadow,
            'PL_dB': PL_dB,
            'shadowing': shadowing,
            'fading': fading,
            'h_values': h_values,
            'h_db': h_db,
            'is_LOS': is_LOS,
            'P_LOS_users': P_LOS_users
        }
