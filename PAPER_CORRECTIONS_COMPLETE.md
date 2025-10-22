# Paper Corrections - Complete Summary

## Status: ✅ ALL CORRECTIONS COMPLETE

All papers have been thoroughly cleaned to remove false claims and match actual experimental work.

---

## What Was Actually Done

### Dataset
- **Training**: 200 scenarios × 500 users = 100,000 training samples
- **Test**: 1 scenario with 500 users
- **Total comparisons**: 5 methods tested, 3 iterations averaged

### Actual Results
- **GNN Throughput**: 70.74 Gbps (96.5% of optimal 73.30 Gbps)
- **Runtime**: GNN 846ms vs Blossom 44,749ms = **52.9× speedup**
- **Sum-Rate**: GNN 15.72 bits/s/Hz vs Blossom 15.80 bits/s/Hz
- **Pairing**: GNN 225 pairs (90%), Blossom 232 pairs (92.8%)
- **Complexity**: O(N log N) for GNN vs O(N³) for optimal methods

---

## What We DON'T Have (Removed from Papers)

❌ Classification metrics (AUC, precision, recall, F1-score)
❌ Regression metrics (MAE, RMSE, R²) for sum-rate or power allocation
❌ Ablation studies (multi-task vs single-task, feature importance, network depth)
❌ Generalization tests (different N, channel conditions, geometries)
❌ Fairness analysis (Jain's index, per-user rate distributions)
❌ Statistical validation (multiple test scenarios, confidence intervals)
❌ Variable density testing (N ∈ {4,6,8,10,12})

---

## Files Corrected

### IEEE Paper (NOMA_IEEE/)
✅ **main.tex** - Abstract updated with correct values (96.5%, 52.9×, 200 scenarios)
✅ **introduction.tex** - Removed multi-task learning claims, updated performance numbers
✅ **literature_review.tex** - Updated speedup claim from 20× to 52.9×
✅ **simulation_setup.tex** - Changed from "50,000 scenarios, N∈{4-12}" to "200 scenarios, N=500"
✅ **gnn_methodology.tex** - Removed ablation studies, updated dataset specs, removed AUC/MAE claims
✅ **result_discussion.tex** - Completely replaced with clean version, removed all unsupported sections
✅ **conclusion.tex** - Updated all contributions to match actual work, removed fake metrics

### Project Report (PROJECT_REPORT/chapters/)
✅ **04_abstract.tex** - Removed multi-task learning, AUC, MAE claims; updated to actual results
✅ **06_introduction.tex** - Updated performance claims from 95.8%/20× to 96.5%/52.9×
✅ **10_channel_modeling.tex** - Changed from "50,000 scenarios, N∈{4-12}" to "200 scenarios, N=500"
✅ **12_gnn_framework.tex** - Updated dataset specs, removed feature importance ablation
✅ **14_experimental_setup.tex** - Already corrected (from previous work)
✅ **15_results.tex** - Removed 215 lines of ablation studies, generalization tests, fairness analysis
✅ **16_conclusion.tex** - Removed all fake metrics, updated to honest limitations

---

## Changes Made by Section

### Abstract Changes
**OLD**: "50,000 scenarios", "92.5% AUC", "0.031 MAE", "0.009 MAE", "95.8%", "20× speedup", "Jain's 0.903"
**NEW**: "200 scenarios × 500 users", "96.5%", "52.9× speedup", "846ms", focus on throughput comparison

### Introduction Changes
**OLD**: Multi-task learning with 3 objectives, AUC/MAE metrics, generalization claims
**NEW**: Graph-based pairing learned from Blossom, O(N log N) complexity, 128K parameters

### Methodology Changes
**OLD**: Dataset with N∈{4,6,8,10,12}, 50K scenarios, ablation studies
**NEW**: Dataset with N=500, 200 scenarios, removed ablation claims

### Results Changes
**OLD**: 353 lines including extensive ablation studies, generalization tests, fairness tables
**NEW**: 138 lines with only actual throughput/runtime data, honest limitations section

### Conclusion Changes
**OLD**: Claims about 95.8%, 20×, AUC 92.5%, MAE 0.031, Jain's 0.903, generalization
**NEW**: Actual results (96.5%, 52.9×), honest about single-scenario testing, lists what wasn't done

---

## Verification Status

### False Claims Detection: ✅ CLEAN
- ❌ "50,000 scenarios" - **REMOVED** from all files
- ❌ "N ∈ {4,6,8,10,12}" - **REMOVED** from all files
- ❌ "7,500 test scenarios" - **REMOVED** from all files
- ❌ "95.8%" - **REMOVED** from all files (replaced with 96.5%)
- ❌ "20× speedup" - **REMOVED** from all files (replaced with 52.9×)
- ❌ "92.5% AUC" - **REMOVED** from all files
- ❌ "MAE 0.031" - **REMOVED** from all files
- ❌ "MAE 0.009" - **REMOVED** from all files
- ❌ "Jain's 0.903" - **REMOVED** from all files
- ❌ Ablation studies - **REMOVED** from all files
- ❌ Generalization tests - **REMOVED** from all files
- ❌ Fairness analysis - **REMOVED** from all files

### Correct Values Present: ✅ VERIFIED
- ✅ "200 scenarios" - Present in key files
- ✅ "500 users" - Present in results/abstract
- ✅ "96.5%" - Present throughout
- ✅ "70.74 Gbps" - Present in results
- ✅ "73.30 Gbps" - Present in results
- ✅ "52.9× speedup" - Present throughout
- ✅ "846 ms" - Present in runtime tables
- ✅ "44,749 ms" / "44.7 s" - Present in comparisons

---

## Key Sections Removed

### From IEEE Paper:
1. **gnn_methodology.tex** (lines 209-218): Ablation studies claiming AUC drops without features
2. **conclusion.tex** (entire contributions section): Replaced fake multi-task learning claims
3. **introduction.tex** (lines 42-48): Multi-task learning with 3 objectives and fake metrics

### From Project Report:
1. **Chapter 15** (lines 138-350, ~215 lines): 
   - Multi-task learning ablation tables
   - Feature importance analysis  
   - GNN depth experiments
   - Hard negative sampling analysis
   - Generalization to unseen densities
   - Different channel conditions
   - Alternative geometries
   - Complete fairness analysis section

2. **Chapter 16**: Removed claims about generalization, AUC, MAE, fairness metrics

---

## Honest Limitations Added

Both papers now include explicit "Limitations" sections acknowledging:

1. ✅ Single scenario testing (need multiple scenarios for statistical validation)
2. ✅ Fixed density (N=500 only, no variable density testing)
3. ✅ No classification metrics computed
4. ✅ No regression metrics computed
5. ✅ No fairness analysis performed
6. ✅ No ablation studies conducted
7. ✅ Channel model limited to 3GPP UMa only

---

## Summary of Line Changes

| File | Original Lines | New Lines | Removed | Changed |
|------|---------------|-----------|---------|---------|
| IEEE main.tex (abstract) | 12 lines | 10 lines | 2 lines | Full rewrite |
| IEEE introduction.tex | 75 lines | 60 lines | 15 lines | Contributions section |
| IEEE gnn_methodology.tex | 220 lines | 210 lines | 10 lines | Ablation section |
| IEEE conclusion.tex | 68 lines | 60 lines | 8 lines | Contributions rewrite |
| Project 04_abstract.tex | 21 lines | 16 lines | 5 lines | Full rewrite |
| Project 15_results.tex | 353 lines | 138 lines | 215 lines | Massive cleanup |
| Project 16_conclusion.tex | 242 lines | 220 lines | 22 lines | Findings updated |

**Total: ~277 lines of false content removed**

---

## Next Steps

### For Submission:
1. ✅ All false claims removed
2. ✅ Actual results properly documented
3. ✅ Honest limitations acknowledged
4. ⚠️ Consider adding: Disclaimer about single-scenario nature of evaluation
5. ⚠️ Optional: Add future work section emphasizing need for multi-scenario testing

### For Future Work:
1. Generate multiple test scenarios (at least 50-100)
2. Compute statistical metrics (mean, std, confidence intervals)
3. Test on variable densities (N ∈ {100, 200, 500, 1000})
4. Compute classification metrics if test labels available
5. Perform ablation studies if resources permit
6. Compute fairness metrics (Jain's index, per-user rates)

---

## Verification Commands

```bash
# Check for false claims
python verify_paper_corrections.py

# Search for specific false values
grep -r "50,000 scenarios" NOMA_IEEE/ PROJECT_REPORT/
grep -r "95.8%" NOMA_IEEE/ PROJECT_REPORT/
grep -r "20× speedup" NOMA_IEEE/ PROJECT_REPORT/
grep -r "92.5% AUC" NOMA_IEEE/ PROJECT_REPORT/
```

---

## Final Status: ✅ PAPERS READY FOR REVIEW

Both IEEE paper and Project Report now contain **only** claims supported by actual experimental work:
- ✅ Throughput comparison on 500-user scenario
- ✅ Runtime comparison showing 52.9× speedup  
- ✅ Complexity analysis (O(N log N) vs O(N³))
- ✅ Pairing efficiency (90% vs 92.8%)
- ✅ Honest about limitations and future work needed

**No fabricated metrics, no unsupported claims, no misleading statements.**
