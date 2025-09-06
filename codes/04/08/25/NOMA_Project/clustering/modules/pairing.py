import numpy as np
import networkx as nx
from typing import List, Tuple, Dict
from tqdm import tqdm

class NOMAUserPairing:
    def __init__(self, noise_power: float = 1e-9, total_power: float = 1.0,
                 sic_threshold_db: float = 8, B_total: float = 20e6):
        """
        Initialize NOMA user pairing parameters
        Args:
            noise_power: Noise power
            total_power: Total transmission power
            sic_threshold_db: SIC threshold in dB
            B_total: Total bandwidth
        """
        self.noise_power = noise_power
        self.total_power = total_power
        self.sic_threshold_db = sic_threshold_db
        self.B_total = B_total
    
    def sic_satisfied(self, h1: float, h2: float) -> bool:
        """Check if SIC decoding is possible for a pair of users"""
        # Determine strong and weak users
        h_strong = max(h1, h2)
        h_weak = min(h1, h2)
        
        # Power allocation
        P_weak = self.total_power * h_strong / (h_strong + h_weak)
        P_strong = self.total_power * h_weak / (h_strong + h_weak)
        
        # SINR calculation
        SINR = (h_strong * P_weak) / (h_strong * P_strong + self.noise_power)
        SINR_dB = 10 * np.log10(SINR)
        
        return SINR_dB >= self.sic_threshold_db
    
    def calc_pair_rate(self, h1: float, h2: float) -> Tuple[float, float, float, float, float]:
        """Calculate rates for a NOMA pair"""
        # Ensure h1 <= h2
        if h1 > h2:
            h1, h2 = h2, h1
        
        # Power allocation
        P1 = self.total_power * h2 / (h1 + h2)  # Power for weak user
        P2 = self.total_power * h1 / (h1 + h2)  # Power for strong user
        
        # Rate calculations
        R1 = np.log2(1 + (P1 * h1) / (P2 * h1 + self.noise_power))
        R2 = np.log2(1 + (P2 * h2) / self.noise_power)
        R_sum = R1 + R2
        
        return P1, P2, R1, R2, R_sum
    
    def static_clustering(self, h_values: np.ndarray) -> List[Tuple[int, int]]:
        """Implement static clustering strategy"""
        sorted_indices = np.argsort(h_values)
        N = len(h_values)
        return [(sorted_indices[i], sorted_indices[N-1-i]) for i in range(N//2)]
    
    def balanced_clustering(self, h_values: np.ndarray) -> List[Tuple[int, int]]:
        """Implement balanced clustering strategy"""
        sorted_indices = np.argsort(h_values)
        N = len(h_values)
        return [(sorted_indices[i], sorted_indices[i + N//2]) for i in range(N//2)]
    
    def blossom_clustering(self, h_values: np.ndarray) -> List[Tuple[int, int]]:
        """Implement blossom clustering strategy"""
        N = len(h_values)
        G = nx.Graph()
        
        # Build graph
        for i in tqdm(range(N), desc="Building graph"):
            for j in range(i+1, N):
                if self.sic_satisfied(h_values[i], h_values[j]):
                    _, _, _, _, R_sum = self.calc_pair_rate(
                        min(h_values[i], h_values[j]),
                        max(h_values[i], h_values[j])
                    )
                    G.add_edge(i, j, weight=R_sum)
        
        # Find maximum weight matching
        if G.number_of_edges() > 0:
            matching = nx.max_weight_matching(G, maxcardinality=True)
            return list(matching)
        return []
    
    def process_pairs(self, pairs: List[Tuple[int, int]], h_values: np.ndarray,
                     user_info: Dict) -> Dict:
        """Process pairs and calculate performance metrics"""
        N = len(h_values)
        used = np.zeros(N, bool)
        results = []
        
        for u1, u2 in pairs:
            if used[u1] or used[u2]:
                continue
            
            h1, h2 = h_values[u1], h_values[u2]
            if self.sic_satisfied(h1, h2):
                P1, P2, R1, R2, R_sum = self.calc_pair_rate(
                    min(h1, h2),
                    max(h1, h2)
                )
                used[[u1, u2]] = True
                
                results.append({
                    'user1_id': u1,
                    'user2_id': u2,
                    'h1': h1,
                    'h2': h2,
                    'P1': P1,
                    'P2': P2,
                    'R1': R1,
                    'R2': R2,
                    'R_sum': R_sum,
                    'mode': 'NOMA'
                })
        
        # Handle remaining OMA users
        for u in range(N):
            if not used[u]:
                h = h_values[u]
                R = np.log2(1 + self.total_power * h / self.noise_power)
                
                results.append({
                    'user1_id': u,
                    'user2_id': -1,
                    'h1': h,
                    'h2': 0,
                    'P1': self.total_power,
                    'P2': 0,
                    'R1': R,
                    'R2': 0,
                    'R_sum': R,
                    'mode': 'OMA'
                })
        
        # Calculate throughput
        num_pairs = sum(1 for r in results if r['mode'] == 'NOMA')
        num_oma = sum(1 for r in results if r['mode'] == 'OMA')
        B_pair = self.B_total / (num_pairs + num_oma) if (num_pairs + num_oma) > 0 else self.B_total
        
        # Add throughput to results
        for r in results:
            r['throughput'] = r['R_sum'] * B_pair / 1e6  # Convert to Mbps
        
        return {
            'pairs': results,
            'metrics': {
                'noma_pairs': num_pairs,
                'oma_users': num_oma,
                'total_throughput': sum(r['throughput'] for r in results),
                'noma_coverage': (num_pairs * 2) / N * 100
            }
        }
