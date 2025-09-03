# backend_api.py
from fastapi import FastAPI, UploadFile, File,Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import pdfplumber
import random
import re
from datetime import datetime
from pydantic import BaseModel
from io import BytesIO
from fastapi.responses import JSONResponse
import requests
import os
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
from google.api_core.exceptions import ResourceExhausted
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.docstore.document import Document
from fastapi import BackgroundTasks



from expenditure_analyser import (
    load_transactions,
    enrich_transactions,
    summarize_overall,
    summarize_by_category,
    summarize_monthly_trends,
    top_merchants,
    detect_anomalies
)

app = FastAPI(title="Personal Expenditure Analyser API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TransactionIn(BaseModel):
    Date: str            # "YYYY-MM-DD"
    Description: str
    Amount: float
    Payment_method: str = "Other"
    Merchant: str = None


transactions_df = pd.DataFrame(columns=[
    "Date", "Amount", "Category", "Description", "Payment_method", "Merchant"
])

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    global transactions_df
    contents = await file.read()
    file_like = BytesIO(contents)

    rows = []

    # Categories mapping
    category_map = {
        "Food": ["Swiggy", "Zomato", "Dominos"],
        "Shopping": ["Amazon", "Flipkart", "Myntra", "Grocery Store"],
        "Travel": ["Uber", "Ola", "Redbus", "IRCTC"],
        "Bills": ["Airtel", "Jio", "TNEB", "Electricity"],
        "Entertainment": ["Netflix", "Spotify", "BookMyShow"],
        "Salary": ["Salary"],
        "Other": ["Wallet", "UPI", "Hospital", "Refund", "Cashback", "John"]
    }

    def infer_category(description: str):
        for cat, keywords in category_map.items():
            for k in keywords:
                if k.lower() in description.lower():
                    return cat, k
        return "Other", "Other"

    # Month prefixes for transaction lines
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    with pdfplumber.open(file_like) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                # ✅ Check if line starts with a month
                if not any(line.startswith(m) for m in months):
                    continue

                parts = line.split()

                # Date part (e.g., "Aug 31, 2025")
                date = " ".join(parts[0:3])

                # Time part (ignored later)
                time = parts[3] + " " + parts[4]

                # Type
                txn_type = parts[5]

                # Amount (after 'n')
                amount_str = parts[6].replace("n", "").replace(",", "")
                amount = float(amount_str)

                if txn_type == "DEBIT":
                    amount = -amount

                # Description is between amount and Transaction ID (starts with 'T')
                try:
                    t_index = [i for i, p in enumerate(parts) if p.startswith("T")][0]
                except IndexError:
                    continue
                description = " ".join(parts[7:t_index])

                # Infer category & merchant
                category, merchant = infer_category(description)

                # Payment method inference
                if "UPI" in description.upper():
                    payment_method = "UPI"
                elif "ATM" in description.upper():
                    payment_method = "ATM"
                elif "NEFT" in description.upper():
                    payment_method = "NEFT"
                else:
                    payment_method = "Other"

                rows.append({
                    "Date": date,
                    "Amount": amount,
                    "Category": category,
                    "Description": description.strip(),
                    "Payment_method": payment_method,
                    "Merchant": merchant
                })

    transactions_df = pd.DataFrame(rows) 
    return {"status": "success", "num_transactions": len(transactions_df)}

@app.post("/add_transaction")
def add_transaction(trx: TransactionIn):
    """
    Adds a new transaction to the global transactions_df and enriches it.
    """
    global transactions_df
    try:
        # Convert incoming data to DataFrame
        df_new = pd.DataFrame([trx.dict()])
        print(df_new)
        # Enrich transaction (calculates Category, Type, AbsAmount, Month)
        df_enriched = enrich_transactions(df_new)
        # Append to global transactions
        transactions_df = pd.concat([transactions_df, df_enriched], ignore_index=True)
        return {"status": "success", "row": df_enriched.to_dict(orient="records")[0]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/transactions")
def get_transactions():
    return JSONResponse(transactions_df.to_dict(orient="records"))

def get_clean_data():
    df=transactions_df.copy()
    df = enrich_transactions(df)
    return df

# ---------- Endpoints ----------
@app.get("/overall")
def get_overall_summary():
    df = get_clean_data()
    return summarize_overall(df)

@app.get("/by_category")
def get_category_summary():
    df = get_clean_data()
    return summarize_by_category(df)

@app.get("/monthly_trends")
def get_monthly_trends():
    df = get_clean_data()
    return summarize_monthly_trends(df)

@app.get("/top_merchants")
def get_top_merchants():
    df = get_clean_data()
    return top_merchants(df)

@app.get("/anomalies")
def get_anomalies():
    df = get_clean_data()
    return detect_anomalies(df)

@app.get("/analyse")
def analyse_transactions():
    df = get_clean_data()
    results = {
        "overall": summarize_overall(df),
        "by_category": summarize_by_category(df),
        "monthly_trends": summarize_monthly_trends(df),
        "top_merchants": top_merchants(df),
        "anomalies": detect_anomalies(df),
    }
    return results

# ---------------- Debits & Loans ---------------- #

debts_df = pd.DataFrame(columns=["person", "amount", "type", "due_date", "notes"])

# Request schema
class Debt(BaseModel):
    person: str
    amount: float
    type: str  # "owe" or "owed"
    due_date: str
    notes: str | None = None


@app.get("/debts")
def get_debts():
    return JSONResponse(debts_df.to_dict(orient="records"))


@app.post("/debts")
def add_debt(debt: Debt):
    global debts_df
    new_entry = pd.DataFrame([debt.dict()])
    debts_df = pd.concat([debts_df, new_entry], ignore_index=True)
    return {"message": "Debt added successfully!"}

reminders_df = pd.DataFrame(columns=["title", "date", "time","Amount", "notes"])

@app.post("/add_reminder")
async def add_reminder(request: Request):
    data: dict = await request.json()
    global reminders_df

    # Ensure the new row has the same columns and fill missing with NaN
    new_row = pd.DataFrame([data]).reindex(columns=reminders_df.columns).fillna(np.nan)

    # Append the new row safely
    reminders_df = pd.concat([reminders_df, new_row], ignore_index=True)

    return {"status": "success", "reminder": data}

@app.get("/reminders")
def get_reminders():
    return JSONResponse(reminders_df.to_dict(orient="records"))



@app.get("/greet")
def greet():
    return {"response": "Hey hi! how can I help you"}


genai.configure(api_key="AIzaSyCbfDRPBQE2Uat9jkIQEJ-BZRtPu4ayuXY")

# Load embedding model
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Example finance knowledge base
knowledge_base = [
    "Expense: Spent 200 on groceries yesterday",
    "Expense: Paid 100 for internet bill",
    "Debt: I owe 5000 to HDFC Bank",
    "Debt: Friend owes me 2000",
    "Reminder: Pay electricity bill tomorrow",
    "Reminder: Rent payment due on 5th"
]

# -------------------- VECTOR DB --------------------
embeddings = embedder.encode(knowledge_base, convert_to_numpy=True)
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)


class ChatRequest(BaseModel):
    message: str

# -------------------- HELPERS --------------------
def retrieve_context(query, top_k=2):
    q_emb = embedder.encode([query], convert_to_numpy=True)
    D, I = index.search(q_emb, top_k)
    return [knowledge_base[i] for i in I[0]]

def handle_local_query(user_msg: str):
    """Answer simple finance queries without Gemini API."""
    user_msg_lower = user_msg.lower()

    # Total spending
    if "total spending" in user_msg_lower or "total expense" in user_msg_lower:
        total = 0
        for item in knowledge_base:
            if item.startswith("Expense"):
                amount = int("".join([c for c in item if c.isdigit()]))
                total += amount
        return f"Your total spending is {total}."

    # Total debt
    if "total debt" in user_msg_lower or "how much do i owe" in user_msg_lower:
        total = 0
        for item in knowledge_base:
            if item.startswith("Debt: I owe"):
                amount = int("".join([c for c in item if c.isdigit()]))
                total += amount
        return f"Your total debt is {total}."

    # Reminders
    if "reminder" in user_msg_lower or "due" in user_msg_lower:
        reminders = [item for item in knowledge_base if item.startswith("Reminder")]
        return "Here are your reminders:\n- " + "\n- ".join(reminders)

    return None  # fallback to Gemini

# -------------------- MAIN CHATBOT --------------------
@app.post("/chatbot")
def chatbot(req: ChatRequest):
    user_msg = req.message

    # Try local handler first
    local_answer = handle_local_query(user_msg)
    if local_answer:
        return {"response": local_answer}

    # Otherwise, try Gemini
    context = retrieve_context(user_msg, top_k=2)
    prompt = f"""
    You are a finance assistant. Use the context below to answer the question.

    Context: {context}

    Question: {user_msg}
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(prompt)
        return {"response": response.text}
    except ResourceExhausted:
        # ✅ Clear message if API limit exceeded
        return {"response": "⚠ Gemini API limit exceeded. Please wait or upgrade your plan."}
    except Exception as e:
        return {"response": f"⚠ Error contacting Gemini API: {str(e)}"}


@app.get("/")
def home():
    return {"message": "Welcome to the Expenditure Analysis Backend"}