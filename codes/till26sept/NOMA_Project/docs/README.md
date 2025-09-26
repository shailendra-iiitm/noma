# NOMA Deep Learning Project Documentation

## Project Overview

This directory contains the deep learning implementation for NOMA (Non-Orthogonal Multiple Access) user pairing optimization.

### Project Structure

```
NOMA_Project/
├── clustering/          # Clustering algorithms implementation
├── deep_learning/      # Deep learning models and training
├── docs/              # Documentation
└── results/           # Experimental results
```

## Clustering Module

The clustering module implements three main approaches:
1. Original clustering algorithm (`clustering.py`)
2. Clustering without PNG generation (`clustering_without_png.py`)
3. User placement-based clustering (`clustering_user_placement_modified.py`)

## Deep Learning Module

The deep learning implementation consists of:
1. Neural network architecture (`noma_net.py`)
2. Training pipeline (`train.py`)
3. Data preprocessing utilities

### Neural Network Architecture

- Input layer: User and channel features
- Hidden layers: Fully connected with ReLU activation
- Batch normalization and dropout for regularization
- Output layer: NOMA pairing prediction

### Training Process

1. Data preprocessing
2. Model initialization
3. Training loop with Adam optimizer
4. Performance evaluation

## Results

Experimental results and comparisons between different approaches are stored in the results directory.

## Getting Started

1. Set up Python environment with required packages
2. Prepare dataset in the specified format
3. Run clustering algorithms or train deep learning models
4. Analyze results using provided visualization tools

## Dependencies

- PyTorch
- NumPy
- Pandas
- Matplotlib
- NetworkX (for clustering)
