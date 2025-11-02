"""
Count actual model parameters for accurate reporting in papers
"""
import torch
import sys
sys.path.append('.')
from models.pairpower_gnn import PairPowerGNN

def count_parameters(model):
    """Count trainable parameters"""
    total = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    # Count by component
    encoder_params = 0
    decoder_params = {'logit': 0, 'rsum': 0, 'alpha': 0}
    
    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        
        if 'convs' in name:
            encoder_params += param.numel()
        elif 'edge_mlp_logit' in name:
            decoder_params['logit'] += param.numel()
        elif 'edge_mlp_rsum' in name:
            decoder_params['rsum'] += param.numel()
        elif 'edge_mlp_alpha' in name:
            decoder_params['alpha'] += param.numel()
    
    return {
        'total': total,
        'encoder': encoder_params,
        'decoder_logit': decoder_params['logit'],
        'decoder_rsum': decoder_params['rsum'],
        'decoder_alpha': decoder_params['alpha'],
        'decoders_total': sum(decoder_params.values())
    }

if __name__ == '__main__':
    # Use same config as training
    model = PairPowerGNN(
        in_channels=5,
        hidden=128,
        out_channels=128,
        num_layers=3,
        dropout=0.2
    )
    
    params = count_parameters(model)
    
    print("\n" + "="*60)
    print("NOMA-GNN MODEL PARAMETERS")
    print("="*60)
    print(f"Total trainable parameters: {params['total']:,}")
    print(f"\nBreakdown:")
    print(f"  Encoder (GraphSAGE):      {params['encoder']:,} ({params['encoder']/params['total']*100:.1f}%)")
    print(f"  Pairing Classifier MLP:   {params['decoder_logit']:,} ({params['decoder_logit']/params['total']*100:.1f}%)")
    print(f"  Sum-Rate Regressor MLP:   {params['decoder_rsum']:,} ({params['decoder_rsum']/params['total']*100:.1f}%)")
    print(f"  Power Allocation MLP:     {params['decoder_alpha']:,} ({params['decoder_alpha']/params['total']*100:.1f}%)")
    print(f"  All Decoders:             {params['decoders_total']:,} ({params['decoders_total']/params['total']*100:.1f}%)")
    print("="*60)
    
    # For LaTeX table
    print("\nFor LaTeX table:")
    print(f"Total: {params['total']:,} parameters")
    print(f"Encoder: {params['encoder']:,}")
    print(f"Decoders: {params['decoders_total']:,}")
    print(f"\nMemory footprint: ~{params['total'] * 4 / 1024:.1f} KB (FP32)")
