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
    Verify SIC feasibility for predicted pairs using |h_dB(User1) - h_dB(User2)| >= threshold_db.

    Inputs
    - h_values_csv: Path to CSV with columns including 'User_ID' and 'h_dB'.
    - pairs_csv: Path to CSV with columns including 'User1_ID' and 'User2_ID'.
    - threshold_db: Minimum absolute dB difference for SIC to be considered feasible.
    - out_report_csv: Optional output CSV to save per-pair details and pass/fail.
    - strict: If True, exit code will be non-zero when any pair fails the check or has missing h.

    Returns
    - Exit code: 0 on success (all pass or strict=False), 1 otherwise when strict=True and failures exist.
    """
    # Load h values
    try:
        h_df = pd.read_csv(h_values_csv, usecols=["User_ID", "h_dB"])  # type: ignore[arg-type]
    except ValueError:
        # Fallback if other columns exist or case differences
        h_df = pd.read_csv(h_values_csv)
        # Normalize column names
        h_df.columns = [str(c).strip() for c in h_df.columns]
        if "User_ID" not in h_df.columns or "h_dB" not in h_df.columns:
            raise RuntimeError(
                "h_values.csv must contain 'User_ID' and 'h_dB' columns. Found: "
                + ", ".join(h_df.columns)
            )

    # Ensure unique by User_ID; keep first occurrence
    h_df = h_df.drop_duplicates(subset=["User_ID"], keep="first").set_index("User_ID")

    # Load pairs
    pairs_df = pd.read_csv(pairs_csv)
    # Normalize column names to expected
    pairs_df.columns = [str(c).strip() for c in pairs_df.columns]
    expected_cols = {"User1_ID", "User2_ID"}
    if not expected_cols.issubset(set(pairs_df.columns)):
        raise RuntimeError(
            f"{pairs_csv} must contain columns {sorted(expected_cols)}. Found: {list(pairs_df.columns)}"
        )

    # Join h_dB for each user
    pairs = pairs_df.copy()
    pairs["h1_dB"] = pairs["User1_ID"].map(h_df["h_dB"])  # type: ignore[index]
    pairs["h2_dB"] = pairs["User2_ID"].map(h_df["h_dB"])  # type: ignore[index]

    # Compute absolute difference and pass flag
    pairs["h_diff_dB"] = (pairs["h1_dB"] - pairs["h2_dB"]).abs()
    pairs["sic_ok"] = pairs["h_diff_dB"] >= threshold_db

    # Mark rows with missing h values as failures with reason
    pairs["missing_h"] = pairs[["h1_dB", "h2_dB"]].isna().any(axis=1)
    # If missing, force sic_ok False
    pairs.loc[pairs["missing_h"], "sic_ok"] = False

    total = len(pairs)
    num_missing = int(pairs["missing_h"].sum())
    num_pass = int(pairs["sic_ok"].sum())
    num_fail = total - num_pass
    pass_pct = (num_pass / total * 100.0) if total else 0.0

    print("SIC verification summary")
    print("- Pairs file:", pairs_csv)
    print("- Users file:", h_values_csv)
    print(f"- Threshold: {threshold_db:.2f} dB")
    print(f"- Total pairs: {total}")
    print(f"- Pass: {num_pass} ({pass_pct:.2f}%)")
    print(f"- Fail: {num_fail}")
    if num_missing:
        print(f"- Missing h_dB entries: {num_missing} (counted as Fail)")

    # Show a few failing examples
    failing_examples = pairs.loc[~pairs["sic_ok"]].head(10)
    if not failing_examples.empty:
        print("\nFirst failing pairs (up to 10):")
        cols_to_show = [
            "User1_ID",
            "User2_ID",
            "h1_dB",
            "h2_dB",
            "h_diff_dB",
            "missing_h",
        ]
        print(failing_examples[cols_to_show].to_string(index=False))

    # Optional report
    if out_report_csv:
        # Preserve original pair columns then append diagnostics
        report_cols = list(pairs_df.columns) + [
            "h1_dB",
            "h2_dB",
            "h_diff_dB",
            "sic_ok",
            "missing_h",
        ]
        pairs.to_csv(out_report_csv, columns=report_cols, index=False)
        print(f"\nDetailed report written to: {out_report_csv}")

    if strict and (num_fail > 0):
        return 1
    return 0


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Verify SIC feasibility for predicted pairs: "
            "abs(h_dB(User1) - h_dB(User2)) >= threshold (default 8 dB)."
        )
    )
    parser.add_argument(
        "--h-values",
        dest="h_values_csv",
        required=True,
        help="Path to h_values.csv with columns 'User_ID' and 'h_dB'",
    )
    parser.add_argument(
        "--pairs",
        dest="pairs_csv",
        required=True,
        help="Path to predicted_pairs CSV with columns 'User1_ID', 'User2_ID'",
    )
    parser.add_argument(
        "--threshold-db",
        dest="threshold_db",
        type=float,
        default=8.0,
        help="Minimum absolute difference in dB to pass the SIC check (default: 8.0)",
    )
    parser.add_argument(
        "--out-report",
        dest="out_report_csv",
        default=None,
        help="Optional output CSV path to write per-pair results",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code if any pair fails or if any h values are missing",
    )

    args = parser.parse_args(argv)
    code = verify_sic(
        h_values_csv=args.h_values_csv,
        pairs_csv=args.pairs_csv,
        threshold_db=args.threshold_db,
        out_report_csv=args.out_report_csv,
        strict=args.strict,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
