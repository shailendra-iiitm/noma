# Step 1: Navigate to the correct directory
cd C:\Users\shail\Desktop\NOMA_FINAL\noma_gnn_backup

# Step 2: Then run your command

# To compare NOMA_GNN with traditional methods:
python run.py compare           # excludes blossom (faster)
python run.py compare --full    # includes blossom (slower)
python run.py compare --file C:\Users\shail\Desktop\NOMA_FINAL\h_values_a.csv

# To run ONLY the GNN model (inference) on a data file:
python run.py infer C:\Users\shail\Desktop\NOMA_FINAL\h_values_a.csv
# OR with relative path:
python run.py infer test_scenario_500users.csv


