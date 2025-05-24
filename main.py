import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy_financial as npf
from fpdf import FPDF
import tempfile
import os
import math

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

# Use CSS to make inputs more compact
st.markdown("""
<style>
.stNumberInput > div > div > input {
    height: 35px !important;
    padding: 4px 8px !important;
}
.stTextInput > div > div > input {
    height: 35px !important;
    padding: 4px 8px !important;
}
.stSelectbox > div > div > select {
    height: 35px !important;
    padding: 4px 8px !important;
}
</style>
""", unsafe_allow_html=True)

with st.expander("📍 Site & Development Details", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**Site Info**")
        property_address = st.text_input("Property Address", value="123 Main Street, City, State")
        site_price = st.number_input("Purchase Price ($)", min_value=0, value=500000, step=10000, format="%d")
        site_size = st.number_input("Site Size (sqm)", min_value=0, value=613, step=10, format="%d")
        # Stamp duty will be calculated automatically based on purchase price
        acquisition_costs = st.number_input("Acquisition Costs ($)", min_value=0, value=15000, step=1000, format="%d")
        gst_rate = st.number_input("GST %", min_value=0.0, value=10.0, step=0.1, format="%.1f") / 100
    with col2:
        st.markdown("**Development**")
        fsr = st.number_input("FSR", min_value=0.0, value=0.7, step=0.1, format="%.2f")
        nsa_ratio = st.number_input("NSA %", min_value=50.0, max_value=100.0, value=85.0, step=1.0, format="%.1f")
        num_dwellings = st.number_input("Dwellings", min_value=1, value=2, step=1, format="%d")
        sales_rate_per_sqm = st.number_input("Sales Rate ($/sqm)", min_value=0, value=2800, step=50, format="%d")
    with col3:
        st.markdown("**Costs**")
        construction_cost_per_gfa = st.number_input("Construction ($/sqm)", min_value=0, value=2500, step=50, format="%d")
        contingency_rate = st.number_input("Contingency %", min_value=0.0, value=5.0, step=0.1, format="%.1f") / 100
        consultant_rate = st.number_input("Consultants %", min_value=0.0, value=3.0, step=0.1, format="%.1f") / 100
        demolition_cost = st.number_input("Demolition ($)", min_value=0, value=20000, step=1000, format="%d")
        development_period = st.number_input("Dev Period (months)", min_value=1, value=18, step=1, format="%d")
    with col4:
        st.markdown("**Marketing Costs**")
        marketing_rate = st.number_input("Marketing %", min_value=0.0, value=2.0, step=0.1, format="%.1f") / 100
        agents_commission_rate = st.number_input("Agents %", min_value=0.0, value=2.5, step=0.1, format="%.1f") / 100

with st.expander("💰 Fees & Financial Settings"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**Professional**")
        professional_fees = st.number_input("Professional ($)", min_value=0, value=25000, step=1000, format="%d")
        solicitor_fees = st.number_input("Solicitor ($)", min_value=0, value=3000, step=500, format="%d")
        utilities_connection = st.number_input("Utilities ($)", min_value=0, value=8000, step=1000, format="%d")
    with col2:
        st.markdown("**Government**")
        council_fees = st.number_input("Council ($)", min_value=0, value=5000, step=500, format="%d")
        da_fees = st.number_input("DA Fees ($)", min_value=0, value=12000, step=1000, format="%d")
        cdc_fees = st.number_input("CDC Fees ($)", min_value=0, value=8000, step=1000, format="%d")
    with col3:
        st.markdown("**Rates & Fees**")
    with col4:
        st.markdown("**Financial**")
        target_profit_margin = st.number_input("Target Profit %", min_value=0.0, value=20.0, step=1.0, format="%.1f") / 100
        minimum_roe = st.number_input("Min ROE %", min_value=0.0, value=15.0, step=1.0, format="%.1f") / 100
        interest_rate = st.number_input("Interest %", min_value=0.0, value=6.5, step=0.1, format="%.1f") / 100

# Calculate stamp duty based on NSW formulas with CEILING function
def calculate_stamp_duty(property_value):
    """Calculate NSW stamp duty based on exact NSW formula with CEILING rounding"""
    def ceiling_to_100(value):
        return math.ceil(value / 100) * 100
    
    if property_value <= 17000:
        return ceiling_to_100(property_value) * 0.0125
    elif property_value <= 36000:
        return 212 + ceiling_to_100(property_value - 17000) * 0.015
    elif property_value <= 97000:
        return 497 + ceiling_to_100(property_value - 36000) * 0.0175
    elif property_value <= 364000:
        return 1564 + ceiling_to_100(property_value - 97000) * 0.035
    elif property_value <= 1212000:
        return 10909 + ceiling_to_100(property_value - 364000) * 0.045
    else:
        return 49069 + ceiling_to_100(property_value - 1212000) * 0.055

stamp_duty = calculate_stamp_duty(site_price)

# Calculate derived metrics first
gfa = site_size * fsr
nsa = gfa * (nsa_ratio / 100)
total_build_cost = construction_cost_per_gfa * gfa
contingency_costs = total_build_cost * contingency_rate

# Calculate expected revenue from sales rate and NSA
expected_revenue = nsa * sales_rate_per_sqm
price_per_dwelling = expected_revenue / num_dwellings if num_dwellings > 0 else 0
avg_dwelling_size = nsa / num_dwellings if num_dwellings > 0 else 0

# Calculate percentage-based costs
consultant_fees = total_build_cost * consultant_rate
marketing_costs = expected_revenue * marketing_rate
agents_fees = expected_revenue * agents_commission_rate
gst_on_sales = expected_revenue * gst_rate

# Calculate finance costs on both site purchase and building costs
site_finance_cost = site_price * interest_rate * (development_period / 12)
building_finance_cost = total_build_cost * interest_rate * (development_period / 24)  # Assume progressive drawdown
total_finance_cost = site_finance_cost + building_finance_cost

# Calculate total costs
total_costs = (
    site_price + 
    stamp_duty + 
    acquisition_costs + 
    total_build_cost + 
    contingency_costs + 
    consultant_fees + 
    demolition_cost + 
    professional_fees + 
    solicitor_fees + 
    utilities_connection + 
    council_fees + 
    da_fees + 
    cdc_fees + 
    marketing_costs + 
    agents_fees + 
    total_finance_cost
)

# Calculate profit and returns
net_revenue = expected_revenue - gst_on_sales
profit = net_revenue - total_costs
profit_margin = (profit / expected_revenue * 100) if expected_revenue > 0 else 0

# Calculate equity required (assuming 70% LVR on land and 80% on construction)
land_loan = site_price * 0.7
construction_loan = total_build_cost * 0.8
total_loan = land_loan + construction_loan
equity_required = total_costs - total_loan

# Calculate ROE and IRR
roe = (profit / equity_required * 100) if equity_required > 0 else 0

# Calculate IRR (Internal Rate of Return)
try:
    # Create cash flows: initial investment (negative), then profit (positive)
    cash_flows = [-equity_required] + [0] * (development_period - 1) + [profit]
    irr = npf.irr(cash_flows) * 12 * 100  # Convert to annual percentage
    if irr is None or not isinstance(irr, (int, float)) or abs(irr) > 1000:
        irr = 0
except:
    irr = 0

# Display results
st.markdown("---")

# Project Metrics (First Section)
st.header("📊 Project Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("GFA", f"{gfa:,.0f} sqm")
    st.metric("NSA", f"{nsa:,.0f} sqm")
    st.metric("Land Cost/GFA", f"${site_price/gfa:,.0f}/sqm" if gfa > 0 else "N/A")

with col2:
    st.metric("Dwellings", f"{num_dwellings}")
    st.metric("Avg Dwelling Size", f"{avg_dwelling_size:,.0f} sqm")
    st.metric("Price/Dwelling", f"${price_per_dwelling:,.0f}")

with col3:
    st.metric("Expected Revenue", f"${expected_revenue:,.0f}")
    st.metric("Net Revenue", f"${net_revenue:,.0f}")
    st.metric("Sales Rate", f"${sales_rate_per_sqm}/sqm")

with col4:
    st.metric("Total Costs", f"${total_costs:,.0f}")
    st.metric("Profit", f"${profit:,.0f}", delta=f"{profit_margin:.1f}% margin")
    st.metric("Equity Required", f"${equity_required:,.0f}")

# Financial Analysis (Second Section)
st.header("💰 Financial Analysis")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Return on Equity", f"{roe:.1f}%", delta="Target: 15%")

with col2:
    st.metric("Internal Rate of Return", f"{irr:.1f}%")

with col3:
    st.metric("Profit Margin", f"{profit_margin:.1f}%", delta=f"Target: {target_profit_margin*100:.1f}%")

with col4:
    st.metric("Development Period", f"{development_period} months")

# Cost Breakdown
with st.expander("💸 Cost Breakdown", expanded=False):
    cost_data = {
        "Category": [
            "Land Purchase", "Stamp Duty", "Acquisition Costs", "Construction", 
            "Contingency", "Consultant Fees", "Demolition", "Professional Fees",
            "Solicitor Fees", "Utilities", "Council Fees", "DA Fees", "CDC Fees",
            "Marketing", "Agents Fees", "Finance Costs"
        ],
        "Amount": [
            site_price, stamp_duty, acquisition_costs, total_build_cost,
            contingency_costs, consultant_fees, demolition_cost, professional_fees,
            solicitor_fees, utilities_connection, council_fees, da_fees, cdc_fees,
            marketing_costs, agents_fees, total_finance_cost
        ]
    }
    
    cost_df = pd.DataFrame(cost_data)
    cost_df["Percentage"] = (cost_df["Amount"] / total_costs * 100).round(1)
    cost_df["Amount"] = cost_df["Amount"].apply(lambda x: f"${x:,.0f}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create pie chart
        fig = px.pie(
            values=cost_data["Amount"], 
            names=cost_data["Category"],
            title="Cost Distribution"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.dataframe(cost_df, use_container_width=True)

# Revenue vs Costs Chart
st.header("📈 Revenue vs Costs Analysis")
comparison_data = {
    "Category": ["Expected Revenue", "Total Costs", "Net Profit"],
    "Amount": [expected_revenue, total_costs, profit],
    "Color": ["green", "red", "blue"]
}

fig = px.bar(
    x=comparison_data["Category"],
    y=comparison_data["Amount"],
    color=comparison_data["Color"],
    title="Revenue vs Costs Comparison",
    labels={"x": "Category", "y": "Amount ($)"}
)
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# PDF Report Generation
def create_pdf_report():
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'Property Development Feasibility Report', 0, 1, 'C')
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    pdf = PDF()
    pdf.add_page()
    
    # Property details
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Property Details", 0, 1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Address: {property_address}", 0, 1)
    pdf.cell(0, 6, f"Site Size: {site_size:,} sqm", 0, 1)
    pdf.cell(0, 6, f"Purchase Price: ${site_price:,}", 0, 1)
    pdf.ln(5)
    
    # Development details
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Development Details", 0, 1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"FSR: {fsr:.2f}", 0, 1)
    pdf.cell(0, 6, f"GFA: {gfa:,.0f} sqm", 0, 1)
    pdf.cell(0, 6, f"NSA: {nsa:,.0f} sqm", 0, 1)
    pdf.cell(0, 6, f"Number of Dwellings: {num_dwellings}", 0, 1)
    pdf.cell(0, 6, f"Average Dwelling Size: {avg_dwelling_size:,.0f} sqm", 0, 1)
    pdf.ln(5)
    
    # Financial summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Financial Summary", 0, 1)
    
    key_metrics = [
        ("Expected Revenue", f"${expected_revenue:,.0f}"),
        ("Total Costs", f"${total_costs:,.0f}"),
        ("Net Revenue", f"${net_revenue:,.0f}"),
        ("Profit", f"${profit:,.0f}"),
        ("Profit Margin", f"{profit_margin:.1f}%"),
        ("Equity Required", f"${equity_required:,.0f}"),
        ("Return on Equity", f"{roe:.1f}%"),
        ("Internal Rate of Return", f"{irr:.1f}%")
    ]
    
    for metric, value in key_metrics:
        pdf.set_font("Arial", "", 10)
        pdf.cell(80, 6, metric, 0, 0)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, value, 0, 1)
    
    return bytes(pdf.output())

st.header("📄 Export Report")
if st.button("Generate PDF Report"):
    try:
        pdf_bytes = create_pdf_report()
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"feasibility_report_{property_address.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        st.success("PDF report generated successfully!")
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")

# Key Insights
st.markdown("---")
st.markdown("### Key Insights")

if profit > 0:
    st.success(f"This project shows a profit of ${profit:,.0f} with a {profit_margin:.1f}% margin")
else:
    st.error(f"This project shows a loss of ${abs(profit):,.0f}")

if roe > 15:
    st.success(f"Excellent return on equity of {roe:.1f}%")
elif roe > 10:
    st.info(f"Good return on equity of {roe:.1f}%")
else:
    st.warning(f"Low return on equity of {roe:.1f}%")

if profit_margin >= target_profit_margin * 100:
    st.success(f"✅ Profit margin of {profit_margin:.1f}% meets target of {target_profit_margin*100:.1f}%")
else:
    st.warning(f"⚠️ Profit margin of {profit_margin:.1f}% below target of {target_profit_margin*100:.1f}%")

if roe >= minimum_roe * 100:
    st.success(f"✅ ROE of {roe:.1f}% meets minimum target of {minimum_roe*100:.1f}%")
else:
    st.warning(f"⚠️ ROE of {roe:.1f}% below minimum target of {minimum_roe*100:.1f}%")
