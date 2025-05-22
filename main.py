import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy_financial as npf
from fpdf import FPDF
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="Property Development Feasibility Calculator",
    page_icon="🏗️",
    layout="wide",
    menu_items={
        'Get Help': 'mailto:rodc31@gmail.com',
        'Report a bug': 'mailto:rodc31@gmail.com',
        'About': 'Property Development Feasibility Calculator helps real estate professionals evaluate development projects and make informed investment decisions.'
    }
)

st.title("🏗️ Property Development Feasibility Calculator")
st.markdown("""
This calculator helps property developers evaluate the feasibility of development projects
by calculating key financial metrics based on input parameters.
""")

# Create two columns for inputs
col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Site Information")
    property_address = st.text_input("Property Address", value="123 Main Street, City, State")
    site_price = st.number_input("Site Purchase Price ($)", min_value=0, value=500000, step=10000)
    site_size = st.number_input("Site Size (sqm)", min_value=0, value=613, step=10)
    fsr = st.number_input("Floor Space Ratio (FSR)", min_value=0.0, value=0.7, step=0.1)
    nsa_ratio = st.number_input("Net Sellable Area Ratio (NSA %)", min_value=50.0, max_value=100.0, value=85.0, step=1.0)
    
    st.subheader("🏗️ Development Details")
    num_dwellings = st.number_input("Number of Dwellings", min_value=1, value=2, step=1)
    expected_revenue = st.number_input("Expected Revenue ($)", min_value=0, value=1200000, step=10000)
    
    st.subheader("🔨 Construction Costs")
    construction_cost_per_gfa = st.number_input("Construction Cost per GFA ($/sqm)", min_value=0, value=2500, step=50)
    demolition_cost = st.number_input("Demolition Cost ($)", min_value=0, value=20000, step=1000)
    
    st.subheader("💼 Additional Costs")
    consultant_costs = st.number_input("Consultant & Approval Costs ($)", min_value=0, value=50000, step=1000)
    marketing_costs = st.number_input("Marketing Costs ($)", min_value=0, value=15000, step=1000)

with col2:
    st.subheader("⚖️ Professional Fees")
    legal_fees = st.number_input("Legal Fees ($)", min_value=0, value=8000, step=1000)
    statutory_fees = st.number_input("Statutory Fees ($)", min_value=0, value=5000, step=1000)
    council_fees = st.number_input("Council Fees ($)", min_value=0, value=15000, step=1000)
    professional_fees = st.number_input("Professional Fees ($)", min_value=0, value=25000, step=1000)
    
    st.subheader("💰 Sales & Transaction Costs")
    agents_commission_rate = st.number_input("Agents Commission Rate (%)", min_value=0.0, value=2.5, step=0.1) / 100
    stamp_duty_rate = st.number_input("Stamp Duty Rate (%)", min_value=0.0, value=5.5, step=0.1) / 100
    gst_rate = st.number_input("GST Rate (%)", min_value=0.0, value=10.0, step=0.1) / 100
    solicitor_fees = st.number_input("Solicitor Fees ($)", min_value=0, value=3000, step=500)
    
    st.subheader("🎯 Target Returns")
    target_profit_margin = st.number_input("Target Profit Margin (%)", min_value=0.0, value=20.0, step=1.0) / 100
    minimum_roe = st.number_input("Minimum ROE Target (%)", min_value=0.0, value=15.0, step=1.0) / 100
    
    st.subheader("📊 Finance & Time")
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=6.5, step=0.1) / 100
    development_period = st.number_input("Development Period (months)", min_value=1, value=18, step=1)
    contingency_rate = st.number_input("Contingency Rate (%)", min_value=0.0, value=5.0, step=0.1) / 100
    
    st.subheader("🔧 Other Costs")
    insurance_costs = st.number_input("Insurance Costs ($)", min_value=0, value=5000, step=500)
    utilities_connection = st.number_input("Utilities Connection ($)", min_value=0, value=8000, step=1000)

# Calculate derived metrics first
gfa = site_size * fsr
nsa = gfa * (nsa_ratio / 100)
total_build_cost = construction_cost_per_gfa * gfa

# Calculate variable costs based on user inputs
agents_fees = expected_revenue * agents_commission_rate
stamp_duty = site_price * stamp_duty_rate
gst_on_sales = expected_revenue * gst_rate
contingency_costs = (site_price + total_build_cost + demolition_cost + consultant_costs + marketing_costs) * contingency_rate
avg_dwelling
