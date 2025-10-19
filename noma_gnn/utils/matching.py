
from typing import List, Tuple, Dict
import numpy as np

def greedy_max_weight_matching(n_nodes: int, edges: List[Tuple[int,int,float]]) -> List[Tuple[int,int,float]]:
    """
    Greedy matching for speed: sort edges by weight desc; pick if both endpoints free.
    edges: list of (u, v, w). Nodes are 0..n_nodes-1
    Returns chosen edges with weights.
    """
    chosen = []
    used = np.zeros(n_nodes, dtype=bool)
    for (u,v,w) in sorted(edges, key=lambda t: t[2], reverse=True):
        if not used[u] and not used[v]:
            used[u]=used[v]=True
            chosen.append((u,v,w))
    return chosen
