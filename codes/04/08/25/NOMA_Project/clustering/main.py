import os
from pathlib import Path
from typing import Dict

from modules.user import UserPlacement
from modules.channel import ChannelModel
from modules.pairing import NOMAUserPairing
from modules.utils import create_results_dir, save_results, load_config, save_user_data

def run_clustering(config_path: str = "configs/config.yaml") -> Dict:
    """
    Run complete NOMA clustering simulation
    Args:
        config_path: Path to configuration file
    Returns:
        Dictionary containing all results
    """
    # Load configuration
    config = load_config(config_path)
    
    # Create results directory
    results_dir = create_results_dir()
    print(f"Results will be saved to: {results_dir}")
    
    # Initialize components
    user_placer = UserPlacement(
        num_users=config['system']['num_users'],
        radius=config['system']['radius'],
        h_BS=config['system']['h_BS']
    )
    
    channel_model = ChannelModel(
        fc=config['channel']['fc'],
        shadow_std_db=config['channel']['shadow_std_db']
    )
    
    pairing = NOMAUserPairing(
        noise_power=config['pairing']['noise_power'],
        total_power=config['pairing']['total_power'],
        sic_threshold_db=config['pairing']['sic_threshold_db'],
        B_total=config['pairing']['B_total']
    )
    
    # Generate user placements
    print("Generating user placements...")
    user_info = user_placer.get_user_info()
    
    # Generate channel gains
    print("Calculating channel gains...")
    channel_info = channel_model.generate_channel_gains(user_info)
    
    # Save user data
    save_user_data(user_info, channel_info, results_dir)
    
    # Perform clustering
    h_values = channel_info['h_values']
    results = {}
    
    print("\nPerforming static clustering...")
    static_pairs = pairing.static_clustering(h_values)
    static_results = pairing.process_pairs(static_pairs, h_values, user_info)
    save_results(static_results, results_dir, "static_")
    results['static'] = static_results
    
    print("\nPerforming balanced clustering...")
    balanced_pairs = pairing.balanced_clustering(h_values)
    balanced_results = pairing.process_pairs(balanced_pairs, h_values, user_info)
    save_results(balanced_results, results_dir, "balanced_")
    results['balanced'] = balanced_results
    
    print("\nPerforming blossom clustering...")
    blossom_pairs = pairing.blossom_clustering(h_values)
    blossom_results = pairing.process_pairs(blossom_pairs, h_values, user_info)
    save_results(blossom_results, results_dir, "blossom_")
    results['blossom'] = blossom_results
    
    # Print summary
    print("\nClustering Results Summary:")
    print("=" * 50)
    for method, result in results.items():
        metrics = result['metrics']
        print(f"\n{method.upper()} CLUSTERING:")
        print(f"  NOMA Pairs: {metrics['noma_pairs']}")
        print(f"  OMA Users: {metrics['oma_users']}")
        print(f"  Total Throughput: {metrics['total_throughput']:.2f} Mbps")
        print(f"  NOMA Coverage: {metrics['noma_coverage']:.1f}%")
    
    return results

if __name__ == "__main__":
    results = run_clustering()
