import streamlit as st
import pandas as pd
import yaml
from pathlib import Path
from io import BytesIO
import datetime
import json

CDM_FIELDS = [
    
    {"id": "1A", "name": "Patient ID", "data_type": "uuid", "values":"", "preferred_standard": None, "description": "A unique patient identification number."},
    {"id": "2A", "name": "Primary Intervention", "data_type": "categorical", "values":  ["HIPPR","TOTKNIE","HMKNIE"], "preferred_standard": None, "description": "Primary total hip replacement or primary total or hemi knee replacement performed within surveillance period."},
    {"id": "3A", "name": "Date of Surgery", "data_type": "date", "values": "dd/mm/yyyy", "preferred_standard": None, "description": "Date the primary hip or knee replacement was performed."},
    {"id": "4A", "name": "Operation Side", "data_type": "categorical", "values": ["left","right"], "preferred_standard": None, "description": "Was the surgery performed in the left or right joint?"},
    {"id": "5A", "name": "Previous Intervention", "data_type": "bool", "values": ["yes","no"], "preferred_standard": None, "description": "Previous operations on the hip or knee joint in question that are considered exclusion criteria (i.e., not arthroscopy, meniscectomy or cruciate ligament reconstruction)."},
    {"id": "6A", "name": "Discharge Date", "data_type": "date", "values": "dd/mm/yyyy", "preferred_standard": "SCT (442864001)", "description": "Discharge date of admission in which indicator intervention took place."},
    {"id": "7A", "name": "Readmission Date", "data_type": "date", "values": "dd/mm/yyyy", "preferred_standard": None, "description": "Date of admission of any readmission to the treating specialty indicator procedure within 120 days after the main procedure."},
    {"id": "8A", "name": "Treating Specialty", "data_type": "categorical", "values": ["orthopedic surgeon", "general surgeon","trauma surgeon"], "preferred_standard": "SCT (69280009)", "description": "Specialty where the patient has been readmitted."},
    {"id": "9A", "name": "Reoperation Date", "data_type": "date", "values": "dd/mm/yyyy", "preferred_standard": None, "description": "Date of any necessary orthopedic reoperation within 120 days after the indicator procedure."},
    {"id": "10A", "name": "Reoperation Specialty", "data_type": "categorical", "values": ["orthopedic surgeon", "general surgeon","trauma surgeon"], "preferred_standard": "SCT (69280009)", "description": "Specialty that performed the reoperation."},
    {"id": "11A", "name": "Culture Collection Date", "data_type": "date", "values": "dd/mm/yyyy", "preferred_standard": None, "description": "Date of culture for microbiological examination from day 1 after the indicator procedure up to and including 120 days after the main procedure."},
    {"id": "12A", "name": "Sample number culture collection", "data_type": "number", "values": "", "preferred_standard": "SCT (260385009)", "description": "Identification number of the material taken for microbiological examination within 120 days after the main procedure."},
    {"id": "13A", "name": "Breeding Material", "data_type": "categorical", "values": ["blood (sample)","wound fluid sample (sample)"], "preferred_standard": "SCT (61594008)", "description": "The material taken for microbiological examination within 120 days after the main procedure."},
    {"id": "14A", "name": "Result", "data_type": "categorical", "values": ["positive","negative"], "preferred_standard": "SCT (260385009)", "description": "Result of the microbiological examination within 120 days after the main procedure."},
    {"id": "15A", "name": "Antibiotic Code", "data_type": "number", "values": "ATCDDD - ATC/DDD Index (fhi.no)", "preferred_standard": "SCT (281789004)", "description": "Code of any antibiotics used in the period up to 120 days after the primary hip or knee prosthesis."},
    {"id": "16A", "name": "Prescription Start Date", "data_type": "date", "values": "dd/mm/yyyy", "preferred_standard": "SCT (413946009)", "description": "Start date of any use of antibiotics in the period up to 120 days after the primary hip or knee prosthesis."},
    {"id": "17A", "name": "Prescription End Date", "data_type": "date", "values": "dd/mm/yyyy", "preferred_standard": "SCT (413947000)", "description": "End date of any use of antibiotics in the period up to 120 days after the primary hip or knee prosthesis."}
]

st.title("CDM Transformer with FAIR Metadata")

def read_data(uploaded_file):
    """Read data from CSV, Excel, or JSON into a DataFrame."""
    if uploaded_file is None:
        return None
    ext = Path(uploaded_file.name).suffix.lower()
    if ext == '.csv':
        df = pd.read_csv(uploaded_file)
    elif ext in ['.xls', '.xlsx']:
        df = pd.read_excel(uploaded_file)
    elif ext == '.json':
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file type. Supported: CSV, XLS, XLSX, JSON")
        return None
    return df

def load_mapping(mapping_file):
    """Load the YAML mapping file."""
    if mapping_file is None:
        return {}
    try:
        mappings = yaml.safe_load(mapping_file)
        return mappings.get('mappings', {})
    except Exception as e:
        st.error(f"Error reading YAML mapping: {e}")
        return {}

def apply_transformations(df, mappings):
    """Apply transformations as defined in the YAML mappings, including date formatting."""
    transformed_df = pd.DataFrame()

    # Ensure transformed data follows the CDM_FIELDS order
    for field in CDM_FIELDS:
        cdm_field = field["name"]
        data_type = field["data_type"]

        # Find the original column mapping
        original_col = None
        for col, info in mappings.items():
            if info.get("cdm_field") == cdm_field:
                original_col = col
                break

        # If original column is not in df, fill with NaN
        if original_col is None or original_col not in df.columns:
            transformed_df[cdm_field] = pd.Series([pd.NA] * len(df))
            continue

        col_data = df[original_col]

        # Apply transformations
        transformation = mappings.get(original_col, {}).get("transformation", {})

        # Handle date formatting for date columns
        if data_type == "date":
            try:
                col_data = pd.to_datetime(col_data, errors="coerce").dt.strftime("%d/%m/%Y")
            except Exception as e:
                st.warning(f"Error formatting date in column '{original_col}': {e}")
                col_data = pd.Series([pd.NA] * len(df))

        # Handle value mappings for categorical fields
        if "value_mapping" in transformation:
            value_mapping = transformation["value_mapping"]
            col_data = col_data.map(value_mapping).fillna(col_data)  # Map values and keep original if no match

        transformed_df[cdm_field] = col_data

    return transformed_df




def generate_metadata(cdm_df, data_filename, mapping_filename):
    """Generate metadata JSON file according to FAIR principles (basic example)."""
    # Example metadata fields (customize as needed):
    metadata = {
        "title": "CDM-Compliant Healthcare Dataset",
        "description": "A dataset transformed into a Common Data Model (CDM) format for healthcare procedures.",
        "created": datetime.datetime.utcnow().isoformat() + "Z",
        "creator": {
            "name": "Your Organization",
            "contact": "contact@yourorg.com"
        },
        "license": "CC-BY-4.0",
        "provenance": {
            "source_data_file": data_filename,
            "mapping_file_used": mapping_filename,
            "transformation_tool": "CDM Transformer App",
            "transformation_date": datetime.datetime.utcnow().isoformat() + "Z"
        },
        "schema": []
    }

    # Add schema information (column names, data types)
    for col in cdm_df.columns:
        col_info = {
            "name": col,
            "data_type": str(cdm_df[col].dtype),
            "description": f"CDM field {col}"
        }
        metadata["schema"].append(col_info)

    return metadata

data_file = st.file_uploader("Upload the data file (CSV, Excel, JSON)", type=["csv", "xls", "xlsx", "json"])
mapping_file = st.file_uploader("Upload the YAML mapping file", type=["yaml", "yml"])

if data_file and mapping_file:
    # Once both files are uploaded, process them
    df = read_data(data_file)
    mappings = load_mapping(mapping_file)

    if df is not None and mappings:
        st.success("Data and mappings loaded successfully!")
        
        # Apply transformations
        cdm_df = apply_transformations(df, mappings)

        # Display summary info
        st.subheader("Transformed CDM Data Summary")
        st.write("**Preview of the transformed data:**")
        st.dataframe(cdm_df.head(10))

        st.write("**Missing Values per Column:**")
        missing_info = cdm_df.isna().sum().reset_index()
        missing_info.columns = ["Column", "Missing Values"]
        st.table(missing_info)

        # Generate FAIR metadata
        metadata = generate_metadata(cdm_df, data_file.name, mapping_file.name)

        # Prepare transformed data for download
        output_buffer = BytesIO()
        cdm_df.to_csv(output_buffer, index=False)
        output_buffer.seek(0)

        # Prepare metadata for download as JSON
        metadata_buffer = BytesIO()
        metadata_buffer.write(json.dumps(metadata, indent=4).encode('utf-8'))
        metadata_buffer.seek(0)

        st.download_button(
            label="Download Transformed CDM CSV",
            data=output_buffer,
            file_name="cdm_compliant_data.csv",
            mime="text/csv"
        )

        st.download_button(
            label="Download Metadata JSON",
            data=metadata_buffer,
            file_name="cdm_metadata.json",
            mime="application/json"
        )

    elif df is None:
        st.error("Failed to load the data file.")
    elif not mappings:
        st.error("No valid mappings found in the YAML file.")
else:
    st.info("Please upload both a data file and a YAML mapping file to proceed.")

