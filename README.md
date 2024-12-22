# Proof of Concept: ETL and Transformation Process

This repository demonstrates a proof of concept for mapping healthcare datasets to a Common Data Model (CDM) and transforming them while adhering to FAIR principles.

## Requirements

Make sure you have the following Python packages installed:

- **streamlit**
- **pandas**
- **pyyaml**

You can install them using:

```bash
pip install streamlit pandas pyyaml
```

## Usage

1. **Run the Mapping Application**  
   To launch the mapping interface, run:

   ```bash
   streamlit run mapApp.py
   ```

2. **Run the Transformation Application**  
   After creating your mappings, transform the data by running:
   ```bash
   streamlit run transformApp.py
   ```

Both applications open in your browser, providing an intuitive interface for creating mappings and transforming data according to the CDM.
