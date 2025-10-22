import pandas as pd
from pathlib import Path

# Check training data
train_file = Path("data/raw/merged_h_values.csv")
if train_file.exists():
    df = pd.read_csv(train_file)
    scenarios = df["Graph_ID"].nunique()
    total_rows = len(df)
    users_per_scenario = total_rows // scenarios
    print(f"=== TRAINING DATA ===")
    print(f"Total rows: {total_rows:,}")
    print(f"Unique scenarios: {scenarios:,}")
    print(f"Users per scenario: {users_per_scenario}")
    print()

# Check test data
test_file = Path("test_scenario_500users.csv")
if test_file.exists():
    df_test = pd.read_csv(test_file)
    test_scenarios = df_test["Graph_ID"].nunique()
    test_rows = len(df_test)
    test_users = test_rows // test_scenarios if test_scenarios > 0 else test_rows
    print(f"=== TEST DATA ===")
    print(f"Total rows: {test_rows:,}")
    print(f"Unique scenarios: {test_scenarios:,}")
    print(f"Users per scenario: {test_users}")
    print()

# Check comparison results
comp_file = Path("comparison/comparison_results_500users.csv")
if comp_file.exists():
    df_comp = pd.read_csv(comp_file)
    print(f"=== COMPARISON RESULTS (500 users) ===")
    for _, row in df_comp.iterrows():
        print(f"{row['Method']:15} | Time: {row['Time_ms']:8.2f} ms | Throughput: {row['Throughput_Mbps']:8.2f} Mbps | Sum-Rate: {row['Avg_Sum_Rate_bps_Hz']:.2f} bps/Hz")
