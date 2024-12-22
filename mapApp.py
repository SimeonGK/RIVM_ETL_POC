import streamlit as st
import pandas as pd
import yaml
from pathlib import Path
from io import BytesIO

# Define the Common Data Model fields
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


def ingest_file(uploaded_file, sheet_name=None):
    """Ingest file from a Streamlit upload widget, optionally specifying a sheet name for Excel."""
    if uploaded_file is not None:
        ext = Path(uploaded_file.name).suffix.lower()
        if ext == '.csv':
            df = pd.read_csv(uploaded_file)
        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name if sheet_name else 0)
        elif ext == '.json':
            df = pd.read_json(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload CSV, JSON, or Excel.")
            return None
        return df
    return None

def generate_mapping_yaml(column_mappings, output_path):
    """Generate YAML from column mappings."""
    with open(output_path, 'w') as yaml_file:
        yaml.dump({"mappings": column_mappings}, yaml_file, default_flow_style=False)

def is_categorical_field(field):
    """Check if the field is categorical based on its data_type."""
    return field['data_type'] == "categorical"

st.title("Healthcare ETL MVP")

# Session state initialization
if 'df' not in st.session_state:
    st.session_state.df = None
if 'show_columns_table' not in st.session_state:
    st.session_state.show_columns_table = False

# Step 1: File upload
uploaded_file = st.file_uploader("Upload a file (CSV, Excel, JSON)", type=["csv", "xlsx", "xls", "json"])
sheet_name = None

# If no DataFrame is loaded yet, allow selecting sheet and loading data
if uploaded_file and st.session_state.df is None:
    ext = Path(uploaded_file.name).suffix.lower()
    sheets = []
    if ext in ['.xls', '.xlsx']:
        try:
            excel_data = uploaded_file.read()
            uploaded_file.seek(0)  # Reset the file pointer
            xls = pd.ExcelFile(BytesIO(excel_data))
            sheets = xls.sheet_names
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")

        if sheets:
            sheet_name = st.selectbox("Select Sheet:", sheets)
        else:
            st.warning("No sheets detected. Please try another file.")
        uploaded_file.seek(0)

    if st.button("Load Data"):
        df = ingest_file(uploaded_file, sheet_name=sheet_name)
        if df is not None:
            st.session_state.df = df
            st.success("Data Loaded Successfully")

# Now, if the DataFrame is loaded into session state, show further options
if st.session_state.df is not None:
    # Change the label of the columns button based on the current state
    columns_button_label = "Hide Columns" if st.session_state.show_columns_table else "See Columns"
    if st.button(columns_button_label):
        # Toggle the state
        st.session_state.show_columns_table = not st.session_state.show_columns_table

    # If the user wants to see the columns, display the table
    if st.session_state.show_columns_table:
        st.subheader("Extracted Columns:")
        df = st.session_state.df
        columns_info = []
        for col in df.columns:
            dtype = df[col].dtype
            sample_values = df[col].head(5).tolist()
            columns_info.append({
                "Column Name": col,
                "Data Type": str(dtype),
                "Sample Values": sample_values
            })

        display_data = {
            "Column Name": [c["Column Name"] for c in columns_info],
            "Data Type": [c["Data Type"] for c in columns_info],
            "Sample Values": [", ".join(str(v) for v in c["Sample Values"]) for c in columns_info]
        }
        st.table(pd.DataFrame(display_data))
        
if st.session_state.df is not None:
    st.subheader("Map CDM Fields to Available Columns")
    df = st.session_state.df
    columns_list = ["Not available"] + list(df.columns)

    column_mappings = {}
    for field in CDM_FIELDS:
        selected_column = st.selectbox(
            f"{field['name']} ({field['id']})", 
            columns_list, 
            key=f"{field['id']}",
            help=f"{field['description']}"
        )

        # If user selects a column, handle mapping and transformations
        if selected_column != "Not available":
            mapping = {"cdm_field": field['name']}
            
            # If it's a categorical field, allow value mapping
            if is_categorical_field(field):
                unique_values = df[selected_column].dropna().unique().tolist()
                value_mapping = {}
                st.markdown(f"**Map values for '{field['name']}'**")
                for value in unique_values:
                    mapped_value = st.selectbox(
                        f"Map '{value}' to CDM value for '{field['name']}'",
                        field['values'] + ["Not available"],
                        key=f"{field['id']}_value_{value}"
                    )
                    if mapped_value != "Not available":
                        value_mapping[value] = mapped_value
                
                mapping["transformation"] = {"value_mapping": value_mapping}

            column_mappings[selected_column] = mapping

    if st.button("Generate Mapping YAML"):
        output_path = "column_mappings.yaml"
        generate_mapping_yaml(column_mappings, output_path)
        st.success(f"Mapping YAML saved to {output_path}")
        # Provide a download button for the generated YAML
        with open(output_path, "rb") as f:
            st.download_button(
                label="Download Mappings YAML",
                data=f,
                file_name="column_mappings.yaml",
                mime="application/x-yaml"
            )