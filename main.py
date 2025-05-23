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

# Create three columns for more compact input layout
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📍 Site Information**")
    property_address = st.text_input("Property Address", value="123 Main Street, City, State")
    site_price = st.number_input("Site Purchase Price ($)", min_value=0, value=500000, step=10000)
    site_size = st.number_input("Site Size (sqm)", min_value=0, value=613, step=10)
    fsr = st.number_input("Floor Space Ratio (FSR)", min_value=0.0, value=0.7, step=0.1)
    nsa_ratio = st.number_input("Net Sellable Area Ratio (NSA %)", min_value=50.0, max_value=100.0, value=85.0, step=1.0)
    
    st.markdown("**🏗️ Development Details**")
    num_dwellings = st.number_input("Number of Dwellings", min_value=1, value=2, step=1)
    sales_rate_per_sqm = st.number_input("Sales Rate per sqm ($)", min_value=0, value=2800, step=50)
    
    st.markdown("**🔨 Construction Costs**")
    construction_cost_per_gfa = st.number_input("Construction Cost per GFA ($/sqm)", min_value=0, value=2500, step=50)
    demolition_cost = st.number_input("Demolition Cost ($)", min_value=0, value=20000, step=1000)

with col2:
    st.markdown("**💼 Additional Costs**")
    consultant_costs = st.number_input("Consultant & Approval Costs ($)", min_value=0, value=50000, step=1000)
    marketing_costs = st.number_input("Marketing Costs ($)", min_value=0, value=15000, step=1000)
    insurance_costs = st.number_input("Insurance Costs ($)", min_value=0, value=5000, step=500)
    utilities_connection = st.number_input("Utilities Connection ($)", min_value=0, value=8000, step=1000)
    
    st.markdown("**⚖️ Professional Fees**")
    legal_fees = st.number_input("Legal Fees ($)", min_value=0, value=8000, step=1000)
    statutory_fees = st.number_input("Statutory Fees ($)", min_value=0, value=5000, step=1000)
    council_fees = st.number_input("Council Fees ($)", min_value=0, value=15000, step=1000)
    professional_fees = st.number_input("Professional Fees ($)", min_value=0, value=25000, step=1000)

with col3:
    st.markdown("**💰 Sales & Transaction Costs**")
    agents_commission_rate = st.number_input("Agents Commission Rate (%)", min_value=0.0, value=2.5, step=0.1) / 100
    stamp_duty_rate = st.number_input("Stamp Duty Rate (%)", min_value=0.0, value=5.5, step=0.1) / 100
    gst_rate = st.number_input("GST Rate (%)", min_value=0.0, value=10.0, step=0.1) / 100
    solicitor_fees = st.number_input("Solicitor Fees ($)", min_value=0, value=3000, step=500)
    
    st.markdown("**🎯 Target Returns**")
    target_profit_margin = st.number_input("Target Profit Margin (%)", min_value=0.0, value=20.0, step=1.0) / 100
    minimum_roe = st.number_input("Minimum ROE Target (%)", min_value=0.0, value=15.0, step=1.0) / 100
    
    st.markdown("**📊 Finance & Time**")
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=6.5, step=0.1) / 100
    development_period = st.number_input("Development Period (months)", min_value=1, value=18, step=1)
    contingency_rate = st.number_input("Contingency Rate (%)", min_value=0.0, value=5.0, step=0.1) / 100

# Calculate derived metrics first
gfa = site_size * fsr
nsa = gfa * (nsa_ratio / 100)
total_build_cost = construction_cost_per_gfa * gfa

# Calculate expected revenue from sales rate and NSA
expected_revenue = nsa * sales_rate_per_sqm

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

# Project Metrics in 4 columns
st.header("📋 Project Metrics")

# Create 4 columns for metrics display
col1, col2, col3, col4 = st.columns(4)

# Define all metrics and values
all_metrics = [
    ('Site Address', f"{property_address}"),
    ('Site Purchase Price', f"${site_price:,.0f}"),
    ('Site Size', f"{site_size:,.0f} sqm"),
    ('Floor Space Ratio (FSR)', f"{fsr:.2f}"),
    ('Gross Floor Area (GFA)', f"{gfa:,.2f} sqm"),
    ('Net Sellable Area (NSA)', f"{nsa:,.2f} sqm"),
    ('NSA Ratio', f"{nsa_ratio:.1f}%"),
    ('Number of Dwellings', f"{num_dwellings}"),
    ('Average Dwelling Size', f"{avg_dwelling_size:.1f} sqm"),
    ('Sales Rate per sqm', f"${sales_rate_per_sqm:,.0f}/sqm"),
    ('Price per Dwelling', f"${price_per_dwelling:,.0f}"),
    ('Construction Cost per GFA', f"${construction_cost_per_gfa:,.0f}/sqm"),
    ('Land Cost per GFA', f"${land_cost_per_gfa:,.0f}/sqm"),
    ('Total Build Cost', f"${total_build_cost:,.0f}"),
    ('Demolition Cost', f"${demolition_cost:,.0f}"),
    ('Consultant & Approval Costs', f"${consultant_costs:,.0f}"),
    ('Marketing Costs', f"${marketing_costs:,.0f}"),
    ('Agents Fees', f"${agents_fees:,.0f}"),
    ('Stamp Duty', f"${stamp_duty:,.0f}"),
    ('GST on Sales', f"${gst_on_sales:,.0f}"),
    ('Council Fees', f"${council_fees:,.0f}"),
    ('Statutory Fees', f"${statutory_fees:,.0f}"),
    ('Legal Fees', f"${legal_fees:,.0f}"),
    ('Professional Fees', f"${professional_fees:,.0f}"),
    ('Solicitor Fees', f"${solicitor_fees:,.0f}"),
    ('Insurance Costs', f"${insurance_costs:,.0f}"),
    ('Utilities Connection', f"${utilities_connection:,.0f}"),
    ('Contingency Costs', f"${contingency_costs:,.0f}"),
    ('Land Holding Costs', f"${land_holding_costs:,.0f}"),
    ('Finance Cost (Interest)', f"${finance_cost:,.0f}"),
    ('Total Costs', f"${total_costs:,.0f}"),
    ('Expected Revenue', f"${expected_revenue:,.0f}"),
    ('Profit', f"${profit:,.0f}"),
    ('Profit Margin', f"{profit_margin:.1f}%"),
    ('Target Profit Margin', f"{target_profit_margin*100:.1f}%"),
    ('Minimum ROE Target', f"{minimum_roe*100:.1f}%"),
    ('Equity Required', f"${equity_required:,.0f}"),
    ('Return on Equity (ROE)', f"{roe:.1f}%"),
    ('Internal Rate of Return (IRR)', f"{irr:.1f}%")
]

# Split metrics into 4 columns
metrics_per_col = len(all_metrics) // 4 + (1 if len(all_metrics) % 4 else 0)

columns = [col1, col2, col3, col4]
for col_idx, col in enumerate(columns):
    start_idx = col_idx * metrics_per_col
    end_idx = min(start_idx + metrics_per_col, len(all_metrics))
    
    with col:
        for metric, value in all_metrics[start_idx:end_idx]:
            st.write(f"**{metric}**: {value}")

# Detailed breakdown
st.header("💰 Cost Breakdown")

# Create cost breakdown data
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

# Display cost breakdown chart
fig = px.bar(cost_df, x='Cost', y='Item', orientation='h', 
             title="Cost Breakdown by Category")
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

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
