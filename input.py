import streamlit as st
import subprocess
import sys
import threading
import uvicorn
from backend_api import app as backend_app
import requests
import os

# ------------------- Start FastAPI Backend on 8001 ------------------- #
def run_backend():
    uvicorn.run(backend_app, host="0.0.0.0", port=8001)

# Start backend in a separate thread
threading.Thread(target=run_backend, daemon=True).start()

# ------------------- Streamlit Page ------------------- #
st.set_page_config(page_title="💰 Personal Expense Analyser")

st.markdown("<div class='header'>💰 Personal Expense Analyser</div>", unsafe_allow_html=True)

# Base URL for backend calls
BASE_URL = "http://127.0.0.1:8001"

# ------------------- 1️⃣ Upload Bank Statement ------------------- #
st.subheader("Upload Bank Statement (PDF)")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file:
    files = {"file": uploaded_file.getvalue()}
    response = requests.post(f"{BASE_URL}/upload_pdf", files=files)
    if response.status_code == 200:
        st.success("✅ PDF uploaded & processed successfully!")
    else:
        st.error("❌ Failed to process PDF.")

# ------------------- 2️⃣ Download Sample PDF ------------------- #
st.subheader("Download Sample Bank Statement")
sample_path = os.path.join("static", "sample.pdf")
if os.path.exists(sample_path):
    with open(sample_path, "rb") as f:
        pdf_data = f.read()

    st.download_button(
        label="📄 Download Sample PDF",
        data=pdf_data,
        file_name="sample.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Sample PDF not found in static/sample.pdf")

# ------------------- 3️⃣ Analyse Button ------------------- #
if st.button("📊 Analyse"):
    st.success("Launching Analysis Dashboard...")
    # Run app.py in a separate process
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"])
