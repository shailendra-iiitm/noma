import os
import torch
from pathlib import Path
from utils.data_loader import NOMADataPreprocessor
from training.train import Trainer

def main():
    # Set base paths
    base_path = Path(os.path.dirname(os.path.abspath(__file__)))
    data_path = base_path.parent
    
    # 1. Preprocess data
    print("Preprocessing data...")
    preprocessor = NOMADataPreprocessor(data_path)
    preprocessor.process_all_runs()
    
    # 2. Train model
    print("\nTraining model...")
    trainer = Trainer(base_path / "configs" / "model_config.yaml")
    training_results = trainer.train()
    
    # 3. Test model
    print("\nTesting model...")
    test_results = trainer.test()
    
    # 4. Print results
    print("\nFinal Results:")
    print("-" * 50)
    print(f"Best Validation Loss: {training_results['best_val_loss']:.4f}")
    print("\nTest Metrics:")
    print(f"Total Loss: {test_results['total_loss']:.4f}")
    print(f"Pairing Loss: {test_results['pair_loss']:.4f}")
    print(f"Performance Loss: {test_results['perf_loss']:.4f}")

if __name__ == "__main__":
    main()
