import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import subprocess
import sys

BASE_URL = "http://127.0.0.1:8000"

# -------------------------------
# Page Config & Header
# -------------------------------
st.set_page_config(page_title="💰 Personal Expense Analyser")
st.markdown("<div class='header'>💰 Personal Expense Analyser</div>", unsafe_allow_html=True)

# -------------------------------
# 1️⃣ Upload Bank Statement
# -------------------------------
st.subheader("Upload Bank Statement (PDF)")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file:
    files = {"file": uploaded_file.getvalue()}
    response = requests.post(f"{BASE_URL}/upload_pdf", files=files)

    if response.status_code == 200:
        st.success("✅ PDF uploaded & processed successfully!")
    else:
        st.error("❌ Failed to process PDF.")

# -------------------------------
# 2️⃣ Download Sample PDF
# -------------------------------
st.subheader("Download Sample Bank Statement")
with open("static/sample.pdf", "rb") as f:  # path to your PDF
    pdf_data = f.read()

st.download_button(
    label="📄 Download Sample PDF",
    data=pdf_data,
    file_name="sample.pdf",  # name when downloaded
    mime="application/pdf"
)

# -------------------------------
# 3️⃣ Analyse Button
# -------------------------------
if st.button("📊 Analyse"):
    st.success("Launching Analysis Dashboard...")

    # Run app1.py in a new process
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app1.py"])
