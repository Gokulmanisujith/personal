#!/usr/bin/env python3
"""
CLI for Personal Expenditure Pattern Analyser
Tech: Python, Pandas, Matplotlib, CSV, Regex
"""
import argparse
from pathlib import Path
from expenditure_analyser import (
    load_transactions,
    enrich_transactions,
    summarize_overall,
    summarize_by_category,
    summarize_monthly_trends,
    top_merchants,
    detect_anomalies,
    plot_category_pie,
    plot_monthly_bar,
    export_reports
)

def parse_args():
    p = argparse.ArgumentParser(description="Personal Expenditure Pattern Analyser")
    p.add_argument("--csv", required=True, help="Path to transaction CSV file")
    p.add_argument("--out", default="reports", help="Output directory for reports and charts")
    p.add_argument("--currency", default="₹", help="Currency symbol for labelling charts")
    p.add_argument("--top-merchants", type=int, default=10, help="How many frequent vendors to list")
    p.add_argument("--month-format", default="%Y-%m", help="Month label format for charts")
    p.add_argument("--date-col", default="Date", help="Name of the date column in CSV")
    p.add_argument("--desc-col", default="Description", help="Name of the description column in CSV")
    p.add_argument("--amount-col", default="Amount", help="Name of the amount column in CSV (positive=credit, negative=debit)")
    return p.parse_args()

def main():
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Load & Enrich
    df = load_transactions(
        args.csv, date_col=args.date_col, desc_col=args.desc_col, amount_col=args.amount_col
    )
    df = enrich_transactions(df)

    # 2) Summaries
    overall = summarize_overall(df)
    by_cat = summarize_by_category(df)
    monthly = summarize_monthly_trends(df)
    merchants = top_merchants(df, n=args.top_merchants)
    anomalies = detect_anomalies(df)

    # 3) Plots
    pie_path = out_dir / "expenses_by_category_pie.png"
    bar_path = out_dir / "monthly_expense_bar.png"
    plot_category_pie(by_cat, save_path=pie_path, title="Expenses by Category")
    plot_monthly_bar(monthly, save_path=bar_path, title="Monthly Expenses", month_format=args.month_format)

    # 4) Export
    export_reports(out_dir, df, overall, by_cat, monthly, merchants, anomalies)

    print(f"Done. Reports written to: {out_dir.resolve()}")
    print(f"- Pie chart: {pie_path.resolve()}")
    print(f"- Bar chart: {bar_path.resolve()}")

if __name__ == "__main__":
    main()
