@echo off
REM Full comparison including Blossom (SLOW!)
echo Running FULL NOMA Pairing Methods Comparison (including Blossom)...
echo WARNING: This will take ~40 seconds for Blossom on 500 users
echo.

python compare_methods.py ^
  --h-values ..\test_scenario_500users.csv ^
  --ckpt ..\checkpoints\best_model.pt ^
  --scaler ..\data\processed\feature_scaler.json ^
  --output comparison_results_500users_full.csv ^
  --iterations 3 ^
  --run-blossom

echo.
echo Done! Check comparison_results_500users_full.csv
pause
