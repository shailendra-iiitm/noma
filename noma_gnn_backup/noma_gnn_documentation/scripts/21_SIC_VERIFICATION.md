# SIC Verification Script Documentation

## 📋 File: `scripts/verify_sic_pairs.py`

### 🎯 Purpose
Validates that predicted user pairs satisfy the **Successive Interference Cancellation (SIC) feasibility constraint**. This is a critical post-processing step to ensure predictions are physically realizable in NOMA systems.

---

## 🔬 SIC Feasibility Criterion

### Mathematical Condition

For a pair $(i, j)$ where $i$ is the weak user and $j$ is the strong user:

$$\text{SIC Feasible} \iff 10 \log_{10}\left(\frac{h_j}{h_i}\right) \geq \text{Threshold}_{\text{dB}}$$

where:
- $h_i$ = channel gain of weak user (linear scale)
- $h_j$ = channel gain of strong user (linear scale)
- $\text{Threshold}_{\text{dB}}$ = minimum gain difference (typically 8 dB)

### Physical Interpretation

**Why 8 dB?**
- Strong user must decode weak user's signal first (SIC)
- Requires **6.3x** power ratio ($10^{8/10} = 6.31$)
- Provides sufficient margin for interference cancellation
- Standard in 3GPP specifications

**What Happens if Violated?**
- Strong user cannot reliably decode weak user's message
- SIC fails → both users experience high error rates
- System degrades to interference-limited regime

---

## 🏗️ Script Functionality

### Complete Implementation

```python
import argparse
import sys
from typing import Optional
import pandas as pd

def verify_sic(
    h_values_csv: str,
    pairs_csv: str,
    threshold_db: float = 8.0,
    out_report_csv: Optional[str] = None,
    strict: bool = False,
) -> int:
    """
    Verify SIC feasibility for predicted pairs.
    
    Args:
        h_values_csv: Path to CSV with 'User_ID' and 'h_dB' columns
        pairs_csv: Path to CSV with 'User1_ID' and 'User2_ID' columns
        threshold_db: Minimum |h_dB difference| for SIC (default: 8.0)
        out_report_csv: Optional output CSV with per-pair details
        strict: If True, exit with code 1 when any pair fails
    
    Returns:
        Exit code: 0 if all pass (or strict=False), 1 otherwise
    """
    # 1. Load channel gains
    try:
        h_df = pd.read_csv(h_values_csv, usecols=["User_ID", "h_dB"])
    except ValueError:
        h_df = pd.read_csv(h_values_csv)
        h_df.columns = [str(c).strip() for c in h_df.columns]
        if "User_ID" not in h_df.columns or "h_dB" not in h_df.columns:
            raise RuntimeError(
                f"h_values.csv must contain 'User_ID' and 'h_dB'. "
                f"Found: {', '.join(h_df.columns)}"
            )
    
    # Ensure unique User_IDs
    h_df = h_df.drop_duplicates(subset=["User_ID"], keep="first")
    h_df = h_df.set_index("User_ID")
    
    # 2. Load pairs
    pairs_df = pd.read_csv(pairs_csv)
    pairs_df.columns = [str(c).strip() for c in pairs_df.columns]
    
    expected_cols = {"User1_ID", "User2_ID"}
    if not expected_cols.issubset(set(pairs_df.columns)):
        raise RuntimeError(
            f"{pairs_csv} must contain {sorted(expected_cols)}. "
            f"Found: {list(pairs_df.columns)}"
        )
    
    # 3. Join channel gains
    pairs = pairs_df.copy()
    pairs["h1_dB"] = pairs["User1_ID"].map(h_df["h_dB"])
    pairs["h2_dB"] = pairs["User2_ID"].map(h_df["h_dB"])
    
    # 4. Compute SIC feasibility
    pairs["h_diff_dB"] = (pairs["h1_dB"] - pairs["h2_dB"]).abs()
    pairs["sic_ok"] = pairs["h_diff_dB"] >= threshold_db
    
    # 5. Handle missing channel gains
    pairs["missing_h"] = pairs[["h1_dB", "h2_dB"]].isna().any(axis=1)
    pairs.loc[pairs["missing_h"], "sic_ok"] = False
    
    # 6. Compute statistics
    total = len(pairs)
    num_missing = int(pairs["missing_h"].sum())
    num_pass = int(pairs["sic_ok"].sum())
    num_fail = total - num_pass
    pass_pct = (num_pass / total * 100.0) if total else 0.0
    
    # 7. Print summary
    print("="*60)
    print("SIC VERIFICATION SUMMARY")
    print("="*60)
    print(f"Pairs file:      {pairs_csv}")
    print(f"Users file:      {h_values_csv}")
    print(f"SIC Threshold:   {threshold_db:.2f} dB")
    print(f"Total pairs:     {total}")
    print(f"✅ Pass:         {num_pass} ({pass_pct:.2f}%)")
    print(f"❌ Fail:         {num_fail}")
    if num_missing:
        print(f"⚠️  Missing h_dB:  {num_missing} (counted as Fail)")
    print("="*60)
    
    # 8. Show failing examples
    failing_examples = pairs.loc[~pairs["sic_ok"]].head(10)
    if not failing_examples.empty:
        print("\nFailing pairs (first 10):")
        cols = ["User1_ID", "User2_ID", "h1_dB", "h2_dB", 
                "h_diff_dB", "missing_h"]
        print(failing_examples[cols].to_string(index=False))
        print()
    
    # 9. Save report (optional)
    if out_report_csv:
        pairs.to_csv(out_report_csv, index=False)
        print(f"✅ Saved detailed report to {out_report_csv}\n")
    
    # 10. Exit code
    if strict and num_fail > 0:
        print("❌ STRICT MODE: Exiting with code 1 due to failures")
        return 1
    
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="Verify SIC feasibility of predicted pairs"
    )
    parser.add_argument(
        "--h_values_csv", 
        required=True,
        help="CSV with User_ID and h_dB columns"
    )
    parser.add_argument(
        "--pairs_csv",
        required=True,
        help="CSV with User1_ID and User2_ID columns"
    )
    parser.add_argument(
        "--threshold_db",
        type=float,
        default=8.0,
        help="Minimum h_dB difference for SIC (default: 8.0)"
    )
    parser.add_argument(
        "--out_report_csv",
        type=str,
        default=None,
        help="Output CSV with per-pair pass/fail details"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any pair fails"
    )
    
    args = parser.parse_args()
    
    exit_code = verify_sic(
        h_values_csv=args.h_values_csv,
        pairs_csv=args.pairs_csv,
        threshold_db=args.threshold_db,
        out_report_csv=args.out_report_csv,
        strict=args.strict
    )
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
```

---

## 🎯 Usage Examples

### Example 1: Basic Verification

```bash
python -m scripts.verify_sic_pairs \
    --h_values_csv data/raw/test_h_values.csv \
    --pairs_csv results/predicted_pairs.csv \
    --threshold_db 8.0
```

**Output**:
```
============================================================
SIC VERIFICATION SUMMARY
============================================================
Pairs file:      results/predicted_pairs.csv
Users file:      data/raw/test_h_values.csv
SIC Threshold:   8.00 dB
Total pairs:     240
✅ Pass:         228 (95.00%)
❌ Fail:         12
============================================================

Failing pairs (first 10):
 User1_ID  User2_ID  h1_dB   h2_dB  h_diff_dB  missing_h
      123       456 -39.23  -46.45       7.22      False
      234       567 -40.12  -47.58       7.46      False
      345       678 -38.89  -46.67       7.78      False
      456       789 -41.23  -48.87       7.64      False
      ...
```

### Example 2: Generate Detailed Report

```bash
python -m scripts.verify_sic_pairs \
    --h_values_csv data/raw/test_h_values.csv \
    --pairs_csv results/predicted_pairs.csv \
    --threshold_db 8.0 \
    --out_report_csv results/sic_verification_report.csv
```

**Output CSV** (`sic_verification_report.csv`):
```csv
User1_ID,User2_ID,alpha,R_sum_bitsHz,score,h1_dB,h2_dB,h_diff_dB,sic_ok,missing_h
0,250,0.72,2.345,0.945,-39.23,-31.12,8.11,True,False
1,251,0.68,2.123,0.923,-40.12,-32.45,7.67,False,False
2,252,0.75,2.456,0.912,-38.89,-30.67,8.22,True,False
...
```

### Example 3: Strict Mode (CI/CD)

```bash
# Exit with error code if any pair fails (for automated testing)
python -m scripts.verify_sic_pairs \
    --h_values_csv data/raw/test_h_values.csv \
    --pairs_csv results/predicted_pairs.csv \
    --threshold_db 8.0 \
    --strict

# Check exit code
if [ $? -ne 0 ]; then
    echo "❌ SIC verification failed!"
    exit 1
fi
```

### Example 4: Relaxed Threshold

```bash
# Use 6 dB threshold (more permissive)
python -m scripts.verify_sic_pairs \
    --h_values_csv data/raw/test_h_values.csv \
    --pairs_csv results/predicted_pairs.csv \
    --threshold_db 6.0
```

**Expected**: Higher pass rate (~98%)

### Example 5: Batch Verification

```bash
# Verify multiple prediction files
for pred_file in results/*_pairs.csv; do
    echo "Verifying $pred_file..."
    python -m scripts.verify_sic_pairs \
        --h_values_csv data/raw/test_h_values.csv \
        --pairs_csv "$pred_file" \
        --threshold_db 8.0 \
        --out_report_csv "${pred_file%.csv}_sic_report.csv"
    echo ""
done
```

---

## 📊 Interpreting Results

### Pass Rate Guidelines

| Pass Rate | Interpretation | Action |
|-----------|----------------|--------|
| 100%      | Perfect! All pairs satisfy SIC | Deploy model |
| 95-99%    | Excellent (few edge cases) | Review failures, may deploy |
| 90-94%    | Good (some issues) | Investigate patterns in failures |
| 80-89%    | Fair (significant issues) | Retrain with stricter constraints |
| < 80%     | Poor (major problem) | Debug model/data pipeline |

### Common Failure Patterns

**1. Boundary Cases** (h_diff = 7.8-7.9 dB):
```
User1: h_dB = -39.2
User2: h_dB = -31.4
Diff: 7.8 dB (just below 8.0)
```
**Cause**: Model learned threshold ~7.5 dB from training data  
**Solution**: Add hard constraint during candidate generation

**2. Similar Channel Gains**:
```
User1: h_dB = -38.5
User2: h_dB = -37.2
Diff: 1.3 dB (far below threshold)
```
**Cause**: Model paired based on spatial proximity, ignored SIC  
**Solution**: Increase SIC weight in loss function

**3. Missing Data**:
```
User1: h_dB = -39.2
User2: h_dB = NaN
Diff: NaN
```
**Cause**: User ID in pairs CSV not found in h_values CSV  
**Solution**: Fix data alignment issue

---

## 🐛 Troubleshooting

### Issue 1: Column Not Found

**Error**:
```
RuntimeError: h_values.csv must contain 'User_ID' and 'h_dB'. Found: userid, hdb
```

**Solution**:
```python
# Check column names
import pandas as pd
df = pd.read_csv("data/raw/test_h_values.csv")
print(df.columns.tolist())

# Rename if needed
df = df.rename(columns={"userid": "User_ID", "hdb": "h_dB"})
df.to_csv("data/raw/test_h_values_fixed.csv", index=False)
```

### Issue 2: All Pairs Fail

**Symptoms**:
```
✅ Pass: 0 (0.00%)
❌ Fail: 240
```

**Potential Causes**:

**Cause 1: Wrong unit (linear vs dB)**
```python
# Check if h_dB values are actually linear
df = pd.read_csv("h_values.csv")
print(df["h_dB"].describe())

# If max > 1, likely linear scale
if df["h_dB"].max() > 1:
    df["h_dB"] = 10 * np.log10(df["h_dB"])
    df.to_csv("h_values_fixed.csv", index=False)
```

**Cause 2: Threshold too strict**
```bash
# Try lower threshold
python -m scripts.verify_sic_pairs ... --threshold_db 5.0
```

**Cause 3: User ID mismatch**
```python
# Check if User IDs in pairs exist in h_values
h_df = pd.read_csv("h_values.csv")
pairs_df = pd.read_csv("pairs.csv")

h_users = set(h_df["User_ID"])
pair_users = set(pairs_df["User1_ID"]) | set(pairs_df["User2_ID"])

missing = pair_users - h_users
if missing:
    print(f"Missing User_IDs: {missing}")
```

### Issue 3: High Failure Rate (80-90%)

**Diagnosis Script**:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load report
report = pd.read_csv("sic_verification_report.csv")

# Plot distribution of h_diff_dB
plt.figure(figsize=(10, 6))
plt.hist(report["h_diff_dB"], bins=50, alpha=0.7, edgecolor='black')
plt.axvline(8.0, color='r', linestyle='--', label='Threshold (8 dB)')
plt.xlabel('Channel Gain Difference (dB)')
plt.ylabel('Number of Pairs')
plt.title('SIC Feasibility Distribution')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('sic_distribution.png')

# Statistics
print(f"Mean h_diff: {report['h_diff_dB'].mean():.2f} dB")
print(f"Median h_diff: {report['h_diff_dB'].median():.2f} dB")
print(f"Min h_diff: {report['h_diff_dB'].min():.2f} dB")
print(f"Max h_diff: {report['h_diff_dB'].max():.2f} dB")

# If mean < 8, model needs retraining with stricter constraints
```

---

## ✅ Best Practices

### 1. Always Verify After Inference
```bash
# Add to inference workflow
python -m inference.infer_pairing ... 
python -m scripts.verify_sic_pairs \
    --h_values_csv data/raw/scenario.csv \
    --pairs_csv results/predicted_pairs.csv \
    --out_report_csv results/sic_report.csv
```

### 2. Use Strict Mode in CI/CD
```yaml
# .github/workflows/test.yml
- name: Run inference
  run: python -m inference.infer_pairing ...

- name: Verify SIC feasibility
  run: |
    python -m scripts.verify_sic_pairs \
      --h_values_csv test_data/h_values.csv \
      --pairs_csv results/predicted_pairs.csv \
      --strict
```

### 3. Track Pass Rates Over Time
```python
# Log verification results
import json
from datetime import datetime

results = {
    "timestamp": datetime.now().isoformat(),
    "pairs_file": "predicted_pairs.csv",
    "total_pairs": 240,
    "pass_count": 228,
    "pass_rate": 95.0,
    "threshold_db": 8.0
}

with open("sic_verification_log.json", "a") as f:
    f.write(json.dumps(results) + "\n")
```

### 4. Filter Out Failing Pairs
```python
import pandas as pd

# Load report
report = pd.read_csv("sic_verification_report.csv")

# Keep only passing pairs
valid_pairs = report[report["sic_ok"] == True]

# Save filtered results
valid_pairs.to_csv("predicted_pairs_sic_verified.csv", index=False)

print(f"Filtered: {len(report)} → {len(valid_pairs)} pairs")
print(f"Removed: {len(report) - len(valid_pairs)} invalid pairs")
```

---

## 🔬 Advanced Analysis

### Correlation with Model Confidence

```python
import pandas as pd
import matplotlib.pyplot as plt

report = pd.read_csv("sic_verification_report.csv")

# Separate passing and failing pairs
passing = report[report["sic_ok"] == True]
failing = report[report["sic_ok"] == False]

# Plot score distributions
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(passing["score"], bins=30, alpha=0.6, label='Passing', color='green')
ax.hist(failing["score"], bins=30, alpha=0.6, label='Failing', color='red')
ax.set_xlabel('GNN Score')
ax.set_ylabel('Number of Pairs')
ax.set_title('Score Distribution: Passing vs Failing SIC')
ax.legend()
plt.savefig('sic_score_correlation.png')

# If failing pairs have high scores, model is overconfident!
print(f"Passing pairs - Mean score: {passing['score'].mean():.4f}")
print(f"Failing pairs - Mean score: {failing['score'].mean():.4f}")
```

---

**Last Updated**: October 17, 2025  
**Version**: 1.0.0  
**Author**: NOMA-GNN Development Team
