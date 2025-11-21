import numpy as np
from typing import List, Tuple

def noma_rates(h1, h2, P1, P2, noise):
    R1 = np.log2(1.0 + (P1*h1) / (P2*h1 + noise))
    R2 = np.log2(1.0 + (P2*h2) / noise)
    return float(R1), float(R2), float(R1+R2)

def sum_throughput_mbps(pairs_with_alpha, h_linear, total_power, noise_power, bandwidth_hz):
    """
    pairs_with_alpha: List[(u_weak, v_strong, alpha)]
    Return total throughput in Mbps using equal PRB split across (pairs + OMA users).
    """
    n = len(h_linear)
    used = np.zeros(n, dtype=bool)
    rates = []
    for (uw, vs, alpha) in pairs_with_alpha:
        used[uw]=used[vs]=True
        P1 = total_power * alpha
        P2 = total_power - P1
        R1,R2,Rsum = noma_rates(h_linear[uw], h_linear[vs], P1, P2, noise_power)
        rates.append(Rsum)

    # OMA users
    oma_rates = []
    for u in range(n):
        if not used[u]:
            R_oma = np.log2(1.0 + total_power*h_linear[u]/noise_power)
            oma_rates.append(R_oma)

    total_entities = len(rates) + len(oma_rates)
    if total_entities == 0:
        return 0.0
    B_unit = bandwidth_hz / total_entities

    total_bits_per_s = (np.sum(rates) + np.sum(oma_rates)) * B_unit
    return float(total_bits_per_s/1e6)
