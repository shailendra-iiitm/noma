@echo off
REM Quick comparison test on 500 users (no Blossom)
echo Running NOMA Pairing Methods Comparison...
echo.

python compare_methods.py ^
  --h-values ..\test_scenario_500users.csv ^
  --ckpt ..\checkpoints\best_model.pt ^
  --scaler ..\data\processed\feature_scaler.json ^
  --output comparison_results_500users.csv ^
  --iterations 3

echo.
echo Done! Check comparison_results_500users.csv
pause
