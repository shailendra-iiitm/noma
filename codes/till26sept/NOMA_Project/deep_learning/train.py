import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd

def load_data(data_path, batch_size=32):
    """
    Load and preprocess NOMA data
    """
    # Load data from CSV
    data = pd.read_csv(data_path)
    
    # Split features and targets
    X = data.drop(['target'], axis=1).values
    y = data['target'].values
    
    # Convert to tensors
    X_tensor = torch.FloatTensor(X)
    y_tensor = torch.FloatTensor(y)
    
    # Create dataset and dataloader
    dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    return dataloader

def train_model(model, dataloader, num_epochs=100, learning_rate=0.001):
    """
    Train the NOMA deep learning model
    """
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        for batch_X, batch_y in dataloader:
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            
            # Backward pass and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(dataloader)
        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {avg_loss:.4f}')
