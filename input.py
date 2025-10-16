import streamlit as st
import requests
import os
import importlib

st.set_page_config(page_title="💰 Personal Expense Analyser")
st.markdown("<div class='header'>💰 Personal Expense Analyser</div>", unsafe_allow_html=True)

BASE_URL = "https://backend.gokulmanisujith.me"

# Initialize session state flag
if "is_analyzed" not in st.session_state:
    st.session_state.is_analyzed = False

# ------------------- 1️⃣ Upload Bank Statement ------------------- #
if not st.session_state.is_analyzed:
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
        st.session_state.is_analyzed = True
        st.experimental_rerun()

# ------------------- 4️⃣ Analysis Page ------------------- #
else:
    st.success("✅ Analysis Dashboard Loaded!")

    # Dynamically import and run your app.py contents
    app = importlib.import_module("app")
    app.run()  # You’ll define run() inside app.py

    if st.button("⬅️ Back to Input Page"):
        st.session_state.is_analyzed = False
        st.experimental_rerun()
