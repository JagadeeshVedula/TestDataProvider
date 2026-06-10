import io
import pandas as pd
import streamlit as st
from engine import DataEngine
import openpyxl

# Initialize backend engine
engine = DataEngine()

# Page Configurations
st.set_page_config(page_title="MockData Pro - Synthetic Data Generator", layout="wide")

st.title("🤖 MockData Pro")
st.subheader("Design, preview, and export high-quality mock data instantly.")
st.write("---")

# Initialize Session State for tracking schema rows dynamically
if "schema_fields" not in st.session_state:
    st.session_state.schema_fields = [{"col_name": "id", "type": "UUID"}, {"col_name": "name", "type": "Full Name"}]

# Layout splits: Sidebar for controls, Main panel for configuration & preview
sidebar = st.sidebar
sidebar.header("⚙️ Generation Settings")

num_rows = sidebar.slider("Number of Rows to Generate", min_value=10, max_value=5000, value=100, step=10)
export_format = sidebar.selectbox("Export Format", ["EXCEL","CSV", "JSON"])

# Premium Mock Tier Upsell Notice
sidebar.info("💡 **Pro Tier Concept:** Want to sync directly to PostgreSQL or AWS S3? Upgrade to Pro!")

# Main Configurator Dashboard
st.markdown("### 🛠️ Define Your Schema")

# Dynamic UI rows
updated_schema = []
for i, field in enumerate(st.session_state.schema_fields):
    col1, col2, col3 = st.columns([3, 3, 1])
    
    with col1:
        new_name = st.text_input(f"Column Name #{i+1}", value=field["col_name"], key=f"name_{i}")
    with col2:
        available_options = engine.get_available_features()
        # Find index of current type to preserve selection on refresh
        default_idx = available_options.index(field["type"]) if field["type"] in available_options else 0
        new_type = st.selectbox(f"Data Type #{i+1}", options=available_options, index=default_idx, key=f"type_{i}")
    with col3:
        st.markdown("<div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.schema_fields.pop(i)
            st.rerun()
            
    updated_schema.append({"col_name": new_name, "type": new_type})

st.session_state.schema_fields = updated_schema

# Buttons to Add Fields
if st.button("➕ Add New Column"):
    st.session_state.schema_fields.append({"col_name": "new_column", "type": "First Name"})
    st.rerun()

st.write("---")

# Generate & Live Preview Section
st.markdown("### 👀 Live Data Preview (First 5 Rows)")

if updated_schema:
    # Always generate 5 rows for the quick live preview
    preview_df = engine.generate(updated_schema, num_rows=5)
    st.dataframe(preview_df, width="stretch")
    
    # Action Button to generate complete payload
    if st.button("🚀 Generate Full Dataset", type="primary"):
        with st.spinner("Processing synthetic records..."):
            full_df = engine.generate(updated_schema, num_rows=num_rows)
            st.success(f"Successfully generated {num_rows} records!")
            
            # Format converting
            if export_format == "CSV":
                payload = full_df.to_csv(index=False).encode('utf-8')
                mime_type = "text/csv"
                file_ext = "csv"
            elif export_format == "EXCEL":
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    full_df.to_excel(writer, index=False, sheet_name='Sheet1')
                payload = buffer.getvalue()
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                file_ext = "xlsx"
            else:
                payload = full_df.to_json(orient="records", indent=4).encode('utf-8')
                mime_type = "application/json"
                file_ext = "json"
                
            st.download_button(
                label=f"💾 Download {export_format}",
                data=payload,
                file_name=f"mock_data.{file_ext}",
                mime=mime_type
            )
else:
    st.warning("Please add at least one column to generate data.")