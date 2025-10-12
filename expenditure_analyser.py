"""
Core logic for Personal Expenditure Pattern Analyser
Tech: Python, Pandas, Matplotlib, CSV, Regex
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

# ---------- Configuration: Regex-based categorization rules ----------
# You can extend/modify these patterns.
CATEGORY_RULES: List[Tuple[str, str]] = [
    # pattern (case-insensitive), category
    (r"\b(uber|ola|rapido|in-drive|indrive|Auto)\b", "Transport"),
    (r"\b(swiggy|zomato|domino'?s|kfc|mcdonald|pizza hut|eatfit|chai point|Movie)\b", "Food & Dining"),
    (r"\b(amazon|flipkart|myntra|ajio|tata cliq|meesho|Grocery)\b", "Shopping"),
    (r"\b(bharat pe|phonepe|google pay|gpay|paytm)\b", "Payments"),
    (r"\b(airtel|jio|vi|vodafone|bsnl)\b.*\b(recharge|prepaid|postpaid|bill)\b", "Mobile & Internet"),
    (r"\b(electricity|power|b(es)?com|tneb|tsspdcl|mseb)\b", "Utilities"),
    (r"\b(rent|landlord|lease)\b", "Rent"),
    (r"\b(uber pass|membership|subscription|netflix|prime|spotify|yt premium|youtube premium)\b", "Subscriptions"),
    (r"\b(insurance|premium|policy|Phone EMI)\b", "Insurance"),
    (r"\b(medical|pharmacy|apollo|1mg|practo|pharmeasy|hospital|clinic)\b", "Health"),
    (r"\b(petrol|fuel|hpcl|bpcl|ioc|iocl|shell)\b", "Fuel"),
    (r"\b(salary|payout|credit|refund|reversal|cashback)\b", "Income"),
    (r"\b(atm|cash withdrawal|Concert)\b", "Cash"),
]

# Fallback keywords if regex rules didn't match
KEYWORD_FALLBACKS: Dict[str, List[str]] = {
    "Food & Dining": ["cafe", "restaurant", "hotel", "eat", "coffee", "tea"],
    "Shopping": ["store", "mart", "bazaar", "traders", "garments"],
    "Transport": ["metro", "bus", "cab", "taxi"],
    "Utilities": ["gas", "water", "electric", "utility"],
}
 
def extract_merchant(description: str) -> str:
  
    s = description.lower()
    s = re.sub(r"\d+", " ", s)
    s = re.sub(r"txn|transaction|upi|imps|neft|ref|id|utr|amt|debited|credited|to|from", " ", s)
    s = re.sub(r"[^a-z\s&']+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:60] if s else "unknown"

def categorize(description: str, amount: float) -> str:
    desc = description.lower()
    # Regex rule match
    for pat, cat in CATEGORY_RULES:
        if re.search(pat, desc, flags=re.I):
            return cat
    # Keyword fallback
    for cat, kws in KEYWORD_FALLBACKS.items():
        if any(kw in desc for kw in kws):
            return cat
    # Income vs Expense default
    return "Income" if amount > 0 else "Other Expense"

def enrich_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Ensure Date is datetime before using .dt
    if not np.issubdtype(df["Date"].dtype, np.datetime64):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=False)

    # Merchant: use API field if present, else fallback
    if "Merchant" in df.columns:
        df["Merchant"] = df["Merchant"]
    else:
        df["Merchant"] = df["Description"].apply(extract_merchant)

    # Category from description + amount
    df["Category"] = [categorize(d, a) for d, a in zip(df["Description"], df["Amount"])]

    # Type: Credit/Debit based on amount
    df["Type"] = np.where(df["Amount"] >= 0, "Credit", "Debit")

    # Absolute amount for analysis
    df["AbsAmount"] = df["Amount"].abs()

    # Month for trend analysis (safe since Date is datetime now)
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()

    return df

def summarize_overall(df: pd.DataFrame) -> dict:
    return {
        "Total Income": df.loc[df["Type"] == "Credit", "Amount"].sum(),
        "Total Expense": df.loc[df["Type"] == "Debit", "AbsAmount"].sum(),
        "Net Savings": df["Amount"].sum(),
        "Transactions": len(df)
    }

def summarize_by_category(df: pd.DataFrame) -> dict:
    return df.groupby("Category")["AbsAmount"].sum().sort_values(ascending=False).to_dict()


def summarize_monthly_trends(df: pd.DataFrame) -> dict:
    return df.groupby("Month")["AbsAmount"].sum().reset_index().to_dict(orient="records")


def top_merchants(df: pd.DataFrame, n: int = 5) -> dict:
    return df.groupby("Merchant")["AbsAmount"].sum().nlargest(n).to_dict()


def detect_anomalies(df: pd.DataFrame) -> dict:
    threshold = df["AbsAmount"].mean() + 2 * df["AbsAmount"].std()
    anomalies = df[df["AbsAmount"] > threshold]
    return anomalies[["Date", "Description", "Merchant", "AbsAmount", "Category"]].to_dict(orient="records")


# ---------- Plotting (Matplotlib only, no styles/colors specified) ----------
def plot_category_pie(by_cat: pd.DataFrame, save_path: Path, title: str="Expenses by Category"):
    if by_cat.empty:
        return
    plt.figure()
    plt.pie(by_cat["AbsAmount"], labels=by_cat["Category"], autopct="%1.1f%%", startangle=90,labeldistance=1.1,pctdistance=0.8)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.axis("equal")
    plt.close()

def plot_monthly_bar(monthly: pd.DataFrame, save_path: Path, title: str="Monthly Expenses", month_format: str="%Y-%m"):
    if monthly.empty:
        return
    plt.figure()
    labels = [m.strftime(month_format) for m in monthly["Month"]]
    plt.bar(labels, monthly["expense"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Expense")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()
 