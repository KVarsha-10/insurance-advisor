import streamlit as st
import os
from agent.tools.extractor import extract_document, parse_insurance_fields

st.set_page_config(page_title="Insurance Advisor AI", page_icon="🏥", layout="wide")
st.title("🏥 Insurance Document Extractor")

data_files = [f for f in os.listdir("data") if f.endswith((".pdf", ".jpg", ".png", ".csv", ".xlsx", ".json"))]

if not data_files:
    st.error("No files found in data/ folder.")
else:
    selected_file = st.selectbox("Select document from data folder", data_files)

    if st.button("📖 Extract Details", type="primary"):
        file_path = os.path.join("data", selected_file)
        raw = extract_document(file_path)
        fields = parse_insurance_fields(raw["raw_text"])

        st.subheader("👤 Policyholder Details")
        if not fields:
            st.text_area("Raw Text", raw["raw_text"][:3000], height=400)
        else:
            for key, value in fields.items():
                st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")