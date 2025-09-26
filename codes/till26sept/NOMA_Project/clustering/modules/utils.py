import os
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

def create_results_dir(base_dir: str = "results") -> Path:
    """Create timestamped results directory"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(base_dir) / f"results_{timestamp}"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

def save_results(results: Dict[str, Any], save_dir: Path, prefix: str = "") -> None:
    """Save clustering results to CSV"""
    # Save pairs data
    pairs_df = pd.DataFrame(results['pairs'])
    pairs_df.to_csv(save_dir / f"{prefix}pairs.csv", index=False)
    
    # Save metrics
    metrics_df = pd.DataFrame([results['metrics']])
    metrics_df.to_csv(save_dir / f"{prefix}metrics.csv", index=False)

def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def save_user_data(user_info: Dict, channel_info: Dict, save_dir: Path) -> None:
    """Save comprehensive user data"""
    data = {
        'User_ID': np.arange(len(user_info['r'])),
        'x_coord_m': user_info['x_coords'],
        'y_coord_m': user_info['y_coords'],
        'distance_m': user_info['r'],
        'angle_rad': user_info['theta'],
        'height_m': user_info['h_UTs'],
        'distance_3D_m': user_info['d_3D'],
        'LOS_status': channel_info['is_LOS'],
        'LOS_probability': channel_info['P_LOS_users'],
        'path_loss_dB_no_shadow': channel_info['PL_dB_no_shadow'],
        'path_loss_dB': channel_info['PL_dB'],
        'shadowing_dB': channel_info['shadowing'],
        'fading': channel_info['fading'],
        'h_linear': channel_info['h_values'],
        'h_dB': channel_info['h_db']
    }
    
    pd.DataFrame(data).to_csv(save_dir / "user_data.csv", index=False)
