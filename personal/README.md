# Personal Expenditure Pattern Analyser

A Python tool to analyse personal bank transactions from a CSV, auto-categorize with regex, and visualize spending.

## Tech
Python, Pandas, Matplotlib, CSV, Regex

## Files
- `analyse.py` – CLI entry point
- `expenditure_analyser.py` – core logic
- `sample_transactions.csv` – example CSV format
- `reports/` – output directory created on run

## CSV Format
Columns (case-insensitive, configurable via flags): `Date`, `Description`, `Amount`
- `Amount`: positive = credit/income, negative = debit/expense

## Usage
```bash
python3 analyse.py --csv sample_transactions.csv --out reports
```

Optional flags:
- `--date-col`, `--desc-col`, `--amount-col` to map custom CSV column names
- `--top-merchants 15` to list more frequent vendors
- `--month-format "%b %Y"` to change month labels in charts
