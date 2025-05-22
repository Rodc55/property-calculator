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

# Calculate dwelling and cost metrics
avg_dwelling_size = nsa / num_dwellings if num_dwellings > 0 else 0
price_per_dwelling = expected_revenue / num_dwellings if num_dwellings > 0 else 0
land_cost_per_gfa = site_price / gfa if gfa > 0 else 0

# Calculate variable costs based on user inputs
agents_fees = expected_revenue * agents_commission_rate
stamp_duty = site_price * stamp_duty_rate
gst_on_sales = expected_revenue * gst_rate
contingency_costs = (site_price + total_build_cost + demolition_cost + consultant_costs + marketing_costs) * contingency_rate

# Calculate land holding costs (interest on site purchase)
land_holding_costs = site_price * interest_rate * (development_period / 12)

# Calculate finance costs (interest on construction)
finance_cost = total_build_cost * interest_rate * (development_period / 24)

# Total costs
total_costs = (site_price + total_build_cost + demolition_cost + consultant_costs + 
               marketing_costs + agents_fees + stamp_duty + gst_on_sales + 
               council_fees + statutory_fees + legal_fees + professional_fees +
               solicitor_fees + insurance_costs + utilities_connection +
               land_holding_costs + finance_cost + contingency_costs)

# Profit calculations
profit = expected_revenue - total_costs
profit_margin = (profit / expected_revenue * 100) if expected_revenue > 0 else 0
equity_required = total_costs - (total_build_cost * 0.8)
roe = (profit / equity_required * 100) if equity_required > 0 else 0

# IRR calculation
cash_flows = [-equity_required]
for month in range(development_period):
    if month < development_period - 1:
        cash_flows.append(0)
    else:
        cash_flows.append(expected_revenue - (total_costs - equity_required))

try:
    irr = npf.irr(cash_flows) * 12 * 100 if len(cash_flows) > 1 else 0
except:
    irr = 0

# Display results
st.header("📈 Financial Analysis")

# Key metrics in columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Expected Revenue", f"${expected_revenue:,.0f}")
    st.metric("Profit", f"${profit:,.0f}", delta=f"{profit_margin:.1f}% margin")

with col2:
    st.metric("Total Costs", f"${total_costs:,.0f}")
    st.metric("Equity Required", f"${equity_required:,.0f}")

with col3:
    st.metric("Return on Equity", f"{roe:.1f}%")
    st.metric("Internal Rate of Return", f"{irr:.1f}%")

with col4:
    st.metric("Number of Dwellings", f"{num_dwellings}")
    st.metric("Price per Dwelling", f"${price_per_dwelling:,.0f}")

# Detailed breakdown
st.header("💰 Cost Breakdown")

cost_data = {
    'Item': ['Site Purchase', 'Construction', 'Demolition', 'Consultants', 'Marketing', 
             'Agents Fees', 'Stamp Duty', 'GST on Sales', 'Council Fees', 'Statutory Fees', 
             'Legal Fees', 'Professional Fees', 'Solicitor Fees', 'Insurance', 'Utilities',
             'Land Holding', 'Finance Cost', 'Contingency'],
    'Cost': [site_price, total_build_cost, demolition_cost, consultant_costs, marketing_costs,
             agents_fees, stamp_duty, gst_on_sales, council_fees, statutory_fees, legal_fees,
             professional_fees, solicitor_fees, insurance_costs, utilities_connection,
             land_holding_costs, finance_cost, contingency_costs]
}

cost_df = pd.DataFrame(cost_data)
cost_df = cost_df.sort_values('Cost', ascending=True)

fig = px.bar(cost_df, x='Cost', y='Item', orientation='h', title="Cost Breakdown by Category")
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

# Metrics table
st.header("📋 Project Metrics")

metrics_data = {
    'Metric': [
        'Site Address', 'Site Purchase Price', 'Site Size', 'Floor Space Ratio (FSR)',
        'Gross Floor Area (GFA)', 'Net Sellable Area (NSA)', 'NSA Ratio',
        'Number of Dwellings', 'Average Dwelling Size', 'Price per Dwelling',
        'Construction Cost per GFA', 'Land Cost per GFA', 'Total Build Cost',
        'Demolition Cost', 'Consultant & Approval Costs', 'Marketing Costs',
        'Agents Fees', 'Stamp Duty', 'GST on Sales', 'Council Fees', 'Statutory Fees',
        'Legal Fees', 'Professional Fees', 'Solicitor Fees', 'Insurance Costs', 'Utilities Connection',
        'Contingency Costs', 'Land Holding Costs', 'Finance Cost (Interest)',
        'Total Costs', 'Expected Revenue', 'Profit', 'Profit Margin',
        'Target Profit Margin', 'Minimum ROE Target', 'Equity Required', 'Return on Equity (ROE)', 'Internal Rate of Return (IRR)'
    ],
    'Value': [
        f"{property_address}", f"${site_price:,.0f}", f"{site_size:,.0f} sqm", f"{fsr:.2f}",
        f"{gfa:,.2f} sqm", f"{nsa:,.2f} sqm", f"{nsa_ratio:.1f}%",
        f"{num_dwellings}", f"{avg_dwelling_size:.1f} sqm", f"${price_per_dwelling:,.0f}",
        f"${construction_cost_per_gfa:,.0f}/sqm", f"${land_cost_per_gfa:,.0f}/sqm",
        f"${total_build_cost:,.0f}", f"${demolition_cost:,.0f}", f"${consultant_costs:,.0f}",
        f"${marketing_costs:,.0f}", f"${agents_fees:,.0f}", f"${stamp_duty:,.0f}",
        f"${gst_on_sales:,.0f}", f"${council_fees:,.0f}", f"${statutory_fees:,.0f}", f"${legal_fees:,.0f}",
        f"${professional_fees:,.0f}", f"${solicitor_fees:,.0f}", f"${insurance_costs:,.0f}", f"${utilities_connection:,.0f}",
        f"${contingency_costs:,.0f}", f"${land_holding_costs:,.0f}", f"${finance_cost:,.0f}",
        f"${total_costs:,.0f}", f"${expected_revenue:,.0f}", f"${profit:,.0f}",
        f"{profit_margin:.1f}%", f"{target_profit_margin*100:.1f}%", f"{minimum_roe*100:.1f}%", f"${equity_required:,.0f}", f"{roe:.1f}%", f"{irr:.1f}%"
    ]
}

metrics_df = pd.DataFrame(metrics_data)
st.dataframe(metrics_df, use_container_width=True, hide_index=True)

# PDF Report Generation
def create_pdf_report():
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Property Development Feasibility Report', 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, f"Project: {property_address}", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Key Financial Metrics", 0, 1)
    pdf.set_font("Arial", "", 10)
    
    key_metrics = [
        ("Expected Revenue", f"${expected_revenue:,.0f}"),
        ("Total Costs", f"${total_costs:,.0f}"),
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
    
    return pdf.output(dest='S').encode('latin-1')

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
