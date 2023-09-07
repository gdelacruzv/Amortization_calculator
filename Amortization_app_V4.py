# -*- coding: utf-8 -*-
"""
Created on Wed Sep  6 17:20:25 2023

@author: Gilberto
"""

""
# streamlit_app.py
import io
import base64
import streamlit as st
import pandas as pd
from datetime import datetime
from mortgagestyle_v2 import MortgageStyle
from straightline_v2 import StraightLineAmortization
from SOFRDataExtractor import SOFRDataExtractor  # Assuming the previous code is saved in this file

import streamlit as st

def homepage():
    st.title("Amortization Calculator Home")

    # Background Information
    st.header("Background Information")
    st.markdown("""
    This application helps to generate an amortization schedule, which is a table detailing each periodic payment on an 
    amortizing loan.
    
    **Types of Amortization:**
    - **Mortgage Style:**
    - **Hybrid Style:**
    - **Straight Line:**
    """)

    # Application Features
    st.header("Application Features")
    st.markdown("""
    - Calculate Mortgage Style, Hybrid Style, and Straight Line Amortizations.
    - Supports both fixed and floating interest rates.
    - Downloadable amortization schedule in Excel format.
    """)

    # How to Use
    st.header("How to Use")
    st.markdown("""
    1. Enter the required details such as Settlement Date, Maturity Date, Notional Amount, etc.
    2. Choose the type of Amortization: Mortgage Style, Hybrid Style, or Straight Line.
    3. For floating rate, upload the SOFR data file and select the reset frequency.
    4. Click on the "Generate Amortization" button to view the amortization table.
    5. You can also download the table in Excel format using the provided link.
    """)
    
    # Details about SOFR_Data file
    st.header("SOFR Data Formatting and Source")
    st.markdown("""
    **Formatting Requirements for the SOFR Data File:**
    
    - The file should be in `.xls` or `.xlsx` format.
    - Ensure the file contains columns labeled 'Date' and 'Rate'.
    - Data should be sorted chronologically.
    - Rates should be in decimal form (e.g., 0.03 for 3%).
    
    If you don't have the SOFR data file, you can obtain the required data from:
    [Pensford Resources - Forward Curve](https://www.pensford.com/resources/forward-curve)
    """)
   
    # Details about contacting
    st.header("Contact info")
    st.markdown("""
    **If you find any errors or have any question please feel free to reach out via LinkedIn:**
        https://www.linkedin.com/in/gil-de-la-cruz-vazquez-62049b125/""")

def apply_floating_rate(df, f, spread):
    for i in range(len(df)):
        if i == 0:
            continue  # No change for the first period
        df.at[i, 'Period Interest'] = round(df.at[i, 'Outstanding Balance'] * (f(i) + spread) / 12,2)  # Applying spread to the SOFR rate
        df.at[i, 'Period Payment'] = round(df.at[i, 'Period Interest'] + df.at[i, 'Principal Payment'],2)
        df.at[i, 'Outstanding Balance'] = df.at[i-1, 'Outstanding Balance'] - df.at[i, 'Principal Payment']
    return df
    
    

def main():
    st.title("Amortization Calculator")

    # Input parameters
    settlement_date = st.date_input("Settlement Date", datetime(2022, 8, 1))
    maturity_date = st.date_input("Maturity Date", datetime(2032, 8, 1))
    first_payment_date = st.date_input("First Payment Date", datetime(2022, 9, 1))
    notional_amount = st.number_input("Notional Amount", value=600000.0, step=5000.0)
    rate = st.number_input("Rate (%)", value=7.03, step=0.01)
    basis_numerator = st.selectbox("Basis Numerator", ["ACT", "30"])
    basis_denominator = st.selectbox("Basis Denominator", [360, 365])
    payment_frequency = st.selectbox("Frequency", ["1M", "3M", "6M"])
    amortization_years = st.number_input("Amortization Years", value=25, step=1)
    # Output format selection
    output_format = st.selectbox("Output Format", ["Simple Amortization", "P+I"])

    # Choose amortization type
    amortization_type = st.selectbox("Choose Amortization Type", ["Mortgage Style", "Hybrid Style", "Straight Line"])

    rate_type = st.selectbox("Rate Type", ["Fixed", "Floating"])
    
    if rate_type == "Floating":
        sofr_file = st.file_uploader("Upload SOFR Data File", type=['xls', 'xlsx'])
        spread = st.number_input("Enter Spread (%)", min_value=0.0, max_value=10.0, value=0.0, step=0.1) / 100.0  # Spread in percentage
        
        if sofr_file:
            data_extractor = SOFRDataExtractor(sofr_file)
            months_duration = st.selectbox("Reset Frequency", ["1M", "3M", "6M"])
            
            if months_duration == "1M":
                f = data_extractor.interpolate_curve(data_extractor.data_1m)
            elif months_duration == "3M":
                f = data_extractor.interpolate_curve(data_extractor.data_3m)
            else:  # For 6M, using 3M data for simplicity. Ideally, you'd have 6M data
                f = data_extractor.interpolate_curve(data_extractor.data_3m)





    if st.button("Generate Amortization"):
        if amortization_type == "Mortgage Style":
            mortgage = MortgageStyle(
                settlement_date, maturity_date, first_payment_date, notional_amount, 
                rate, basis_numerator, basis_denominator, amortization_years, payment_frequency
            )
            df = mortgage.create_mortgage_style_amort()
        elif amortization_type == "Hybrid Style":
            mortgage = MortgageStyle(
                settlement_date, maturity_date, first_payment_date, notional_amount, 
                rate, basis_numerator, basis_denominator, amortization_years, payment_frequency
            )
            df = mortgage.create_hybrid_style_amort()
        else:
            sla = StraightLineAmortization(
                settlement_date, maturity_date, first_payment_date, notional_amount,
                rate, basis_numerator, basis_denominator, amortization_years, payment_frequency
            )
            df = sla.generate_schedule()
        if rate_type == "Floating":
            df = apply_floating_rate(df, f, spread)
            df['Interest Rate (%)'] = (df['Period Interest'] / df['Outstanding Balance'].shift(1)) * 12 * 100
            df['Interest Rate (%)'] = df['Interest Rate (%)'].round(2)
   
        # Calculate additional columns for P+I
        if 'Period Payment' in df.columns and 'Outstanding Balance' in df.columns:
            df['Remaining Notional Balance'] = df['Outstanding Balance'] - df['Principal Payment']
        if 'Period Payment' in df.columns and 'Principal Payment' in df.columns:
            df['Period Interest'] = df['Period Payment'] - df['Principal Payment']
            
         # Customize output format
        if output_format == "Simple Amortization":
            columns = ['Period Start Date', 'Period End Date', 'Outstanding Balance']
        else:  # "P+I"
            columns = ['Payment Number', 'Period Start Date', 'Period End Date', 'Outstanding Balance', 
                       'Period Payment', 'Principal Payment', 'Period Interest', 'Remaining Notional Balance']
        if rate_type == "Floating":
            df = apply_floating_rate(df, f, spread)
            df['Interest Rate (%)'] = (df['Period Interest'] / df['Outstanding Balance'].shift(1)) * 12 * 100
            df['Interest Rate (%)'] = df['Interest Rate (%)'].round(2)
            columns.append('Interest Rate (%)')  # Only add this column if rate_type is Floating

        df = df[columns]

        # Display the dataframe
        st.write(df)

        # Download link for Excel
        towrite = io.BytesIO()
        downloaded_file = df.to_excel(towrite, encoding='utf-8', index=False, engine='openpyxl')
        towrite.seek(0)
        b64 = base64.b64encode(towrite.read()).decode()
        st.markdown(f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="amortization.xlsx">Download Excel File</a>', unsafe_allow_html=True)

if __name__ == "__main__":
    page = st.sidebar.radio("Select Page", ["Home", "Amortization Calculator"])

    if page == "Home":
        homepage()
    else:
        main()
