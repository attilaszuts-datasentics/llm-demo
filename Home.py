"""
Workshop landing page.
Streamlit Community Cloud entry point — run: streamlit run Home.py
"""
import streamlit as st

st.set_page_config(page_title="Report Extraction Workshop", layout="centered", page_icon="📄")

st.title("📄 Extracting Data from Reports")
st.subheader("Azure Document Intelligence · Azure OpenAI · Databricks")
st.divider()

st.markdown("""
These demos walk through how AI services can automatically extract structured data
from heterogeneous real estate market reports — and how to validate, verify, and
review what the AI found before it enters production.

The source reports are Q1 2025 market publications from Savills, CBRE, Colliers,
Knight Frank, Cushman & Wakefield, Otto Immobilien, and Vienna Research Forum,
covering office, retail, industrial, and investment markets in Austria and Czech Republic.
""")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/1_⚙️_Pipeline.py", label="⚙️ Ingestion Pipeline", icon="⚙️")
    st.caption("Azure Blob → Document Intelligence → OpenAI → Delta Lake")

    st.markdown("")
    st.page_link("pages/2_🔬_Compare.py", label="🔬 Strategy Comparison", icon="🔬")
    st.caption("Raw OCR vs Regex+LLM vs Doc Intelligence vs OpenAI")

with col2:
    st.page_link("pages/3_✅_Review.py", label="✅ Human Review Queue", icon="✅")
    st.caption("Approve, reject, or correct extractions with inline PDF view")

    st.markdown("")
    st.page_link("pages/4_🧞_Genie.py", label="🧞 Databricks Genie", icon="🧞")
    st.caption("Ask questions about the extracted data in plain English")

st.divider()
st.caption("Workshop demo — v0. Service calls are mocked; data is from real broker reports.")
