import numpy as np
import torch
from sklearn.metrics import mean_squared_error, r2_score

def calculate_metrics(model, data_loader, device):
    """Calculate evaluation metrics for the model"""
    model.eval()
    true_values = []
    predictions = []
    
    with torch.no_grad():
        for data, target in data_loader:
            data = data.to(device)
            output = model(data)
            
            # Move to CPU for numpy operations
            predictions.extend(output.cpu().numpy())
            true_values.extend(target.cpu().numpy())
    
    predictions = np.array(predictions)
    true_values = np.array(true_values)
    
    # Calculate metrics
    metrics = {
        'mse': mean_squared_error(true_values, predictions),
        'rmse': np.sqrt(mean_squared_error(true_values, predictions)),
        'r2': r2_score(true_values, predictions)
    }
    
    return metrics
