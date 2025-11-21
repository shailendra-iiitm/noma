import torch

checkpoint = torch.load('checkpoints/best_model.pt', map_location='cpu', weights_only=False)
print("Checkpoint keys:", checkpoint.keys() if isinstance(checkpoint, dict) else "Not a dict")
print("Type:", type(checkpoint))
