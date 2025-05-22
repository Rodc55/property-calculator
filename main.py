import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import base64
import auth

# Set page config
st.set_page_config(
    page_title="Property Development Feasibility Calculator",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication database
auth.init_auth_db()

# Check if user is logged in
if 'session_id' not in st.session_state:
    st.session_state.session_id = None

if st.session_state.session_id:
    user = auth.get_user_from_session(st.session_state.session_id)
    if not user:
        st.session_state.session_id = None
        st.rerun()
else:
    user = None

# Show authentication page if not logged in
if not user:
    auth.auth_page()
    st.stop()

# Display user info and logout in sidebar
with st.sidebar:
    auth.user_info_section()
    
    if st.button("Logout", type="secondary"):
        auth.logout()
        st.rerun()

# Main app title
st.title("🏢 Property Development Feasibility Calculator")
st.markdown("Analyze the profitability of your property development projects")

# Input section
st.header("📊 Project Details")

# Create two columns for inputs
col1, col2 = st.columns(2)

with col1:
    st.subheader("Site Information")
    property_address = st.text_input("Property Address", placeholder="123 Main Street, City, State")
    site_price = st.number_input("Site Purchase Price ($)", min_value=0, value=500000, step=10000)
    gfa = st.number_input("Gross Floor Area - GFA (sqm)", min_value=0, value=200, step=10)
    nsa = st.number_input("Net Sellable Area - NSA (sqm)", min_value=0, value=180, step=10)
    
    st.subheader("Development Details")
    num_dwellings = st.number_input("Number of Dwellings", min_value=1, value=2, step=1)
    expected_revenue = st.number_input("Expected Revenue ($)", min_value=0, value=1200000, step=10000)
    
with col2:
    st.subheader("Construction Costs")
    construction_cost_per_gfa = st.number_input("Construction Cost per GFA ($/sqm)", min_value=0, value=2500, step=50)
    demolition_cost = st.number_input("Demolition Cost ($)", min_value=0, value=20000, step=1000)
    
    st.subheader("Additional Costs")
    consultant_costs = st.number_input("Consultant & Approval Costs ($)", min_value=0, value=50000, step=1000)
    marketing_costs = st.number_input("Marketing Costs ($)", min_value=0, value=15000, step=1000)
    
    st.subheader("Financial Parameters")
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=6.5, step=0.1) / 100
    development_period = st.number_input("Development Period (months)", min_value=1, value=18, step=1)

# Additional costs
agents_fees = expected_revenue * 0.025  # 2.5% of revenue
stamp_duty = site_price * 0.055  # 5.5% of site price
gst_on_sales = expected_revenue * 0.1  # 10% GST
statutory_fees = 5000  # Fixed amount
legal_fees = 8000  # Fixed amount

# Calculate derived metrics
total_build_cost = construction_cost_per_gfa * gfa
avg_dwelling_size = nsa / num_dwellings if num_dwellings > 0 else 0
price_per_dwelling = expected_revenue / num_dwellings if num_dwellings > 0 else 0
land_cost_per_gfa = site_price / gfa if gfa > 0 else 0

# Calculate land holding costs (interest on site purchase)
land_holding_costs = site_price * interest_rate * (development_period / 12)

# Calculate finance costs (interest on construction)
finance_cost = total_build_cost * interest_rate * (development_period / 24)  # Assume half the period for average

# Total costs
total_costs = (site_price + total_build_cost + demolition_cost + consultant_costs + 
               marketing_costs + agents_fees + stamp_duty + gst_on_sales + 
               statutory_fees + legal_fees + land_holding_costs + finance_cost)

# Profit calculations
profit = expected_revenue - total_costs
profit_margin = (profit / expected_revenue * 100) if expected_revenue > 0 else 0
equity_required = total_costs - (total_build_cost * 0.8)  # Assuming 80% construction loan
roe = (profit / equity_required * 100) if equity_required > 0 else 0

# IRR calculation (simplified)
cash_flows = [-equity_required]  # Initial investment
monthly_rate = interest_rate / 12
for month in range(development_period):
    if month < development_period - 1:
        cash_flows.append(0)  # No cash flow during development
    else:
        cash_flows.append(expected_revenue - (total_costs - equity_required))  # Final cash flow

try:
    irr = npf.irr(cash_flows) * 12 * 100 if len(cash_flows) > 1 else 0  # Annualized
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

# Create cost breakdown data
cost_data = {
    'Item': ['Site Purchase', 'Construction', 'Demolition', 'Consultants', 'Marketing', 
             'Agents Fees', 'Stamp Duty', 'GST on Sales', 'Statutory Fees', 'Legal Fees',
             'Land Holding', 'Finance Cost'],
    'Cost': [site_price, total_build_cost, demolition_cost, consultant_costs, marketing_costs,
             agents_fees, stamp_duty, gst_on_sales, statutory_fees, legal_fees, 
             land_holding_costs, finance_cost]
}

cost_df = pd.DataFrame(cost_data)
cost_df = cost_df.sort_values('Cost', ascending=True)

# Create cost breakdown chart
fig = px.bar(cost_df, x='Cost', y='Item', orientation='h',
             title='Cost Breakdown', 
             labels={'Cost': 'Amount ($)', 'Item': 'Cost Category'})
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# Metrics table
st.header("📋 Project Metrics")

metrics_data = {
    'Metric': [
        'Site Purchase Price', 'Gross Floor Area (GFA)', 'Net Sellable Area (NSA)',
        'Number of Dwellings', 'Average Dwelling Size', 'Price per Dwelling',
        'Construction Cost per GFA', 'Land Cost per GFA', 'Total Build Cost',
        'Demolition Cost', 'Consultant & Approval Costs', 'Marketing Costs',
        'Agents Fees', 'Stamp Duty', 'GST on Sales', 'Statutory Fees',
        'Legal Fees', 'Land Holding Costs', 'Finance Cost (Interest)',
        'Total Costs', 'Expected Revenue', 'Profit', 'Profit Margin',
        'Equity Required', 'Return on Equity (ROE)', 'Internal Rate of Return (IRR)'
    ],
    'Value': [
        f"${site_price:,.0f}", f"{gfa:,.0f} sqm", f"{nsa:,.0f} sqm",
        f"{num_dwellings}", f"{avg_dwelling_size:.1f} sqm", f"${price_per_dwelling:,.0f}",
        f"${construction_cost_per_gfa:,.0f}/sqm", f"${land_cost_per_gfa:,.0f}/sqm",
        f"${total_build_cost:,.0f}", f"${demolition_cost:,.0f}", f"${consultant_costs:,.0f}",
        f"${marketing_costs:,.0f}", f"${agents_fees:,.0f}", f"${stamp_duty:,.0f}",
        f"${gst_on_sales:,.0f}", f"${statutory_fees:,.0f}", f"${legal_fees:,.0f}",
        f"${land_holding_costs:,.0f}", f"${finance_cost:,.0f}",
        f"${total_costs:,.0f}", f"${expected_revenue:,.0f}", f"${profit:,.0f}",
        f"{profit_margin:.1f}%", f"${equity_required:,.0f}", f"{roe:.1f}%", f"{irr:.1f}%"
    ]
}

metrics_df = pd.DataFrame(metrics_data)
st.dataframe(metrics_df, use_container_width=True, hide_index=True)

# PDF Export
st.header("📄 Export Report")

# Check access level for PDF export
access_level = auth.check_access_level()

if access_level == "free":
    st.info("🔒 PDF export is available for Basic and Pro subscribers. Please upgrade your subscription to access this feature.")
    if st.button("Upgrade Subscription", type="primary"):
        st.switch_page("pages/subscription.py")
else:
    # Check PDF export limits
    can_export, exports_used, exports_limit = auth.check_pdf_export_limit(user)
    
    if access_level == "basic":
        st.info(f"📊 PDF Exports Used: {exports_used}/{exports_limit} this month")
        
        # Show progress bar
        progress = exports_used / exports_limit if exports_limit > 0 else 0
        st.progress(progress)
        
        if not can_export:
            st.warning("🚫 You've reached your monthly PDF export limit. Upgrade to Pro for unlimited exports!")
            if st.button("Upgrade to Pro", type="primary"):
                st.switch_page("pages/subscription.py")
    
    if can_export or access_level == "pro" or access_level == "admin":
        def create_pdf_report():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Property Development Feasibility Report", 0, 1, "C")
            
            # Add property address if provided
            if property_address:
                pdf.ln(5)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, f"Property: {property_address}", 0, 1, "C")
            
            pdf.ln(8)
            
            # Create metrics list for PDF
            metrics_list = list(zip(metrics_df['Metric'], metrics_df['Value']))
            
            # First group: Site and building details
            site_metrics = ["Site Purchase Price", "Gross Floor Area (GFA)", "Net Sellable Area (NSA)", 
                           "Number of Dwellings", "Average Dwelling Size", "Price per Dwelling",
                           "Construction Cost per GFA", "Land Cost per GFA"]
            
            # Second group: Costs
            cost_metrics = ["Total Build Cost", "Demolition Cost", "Consultant & Approval Costs",
                            "Marketing Costs", "Agents Fees", "Stamp Duty", "GST on Sales", "Statutory Fees", 
                            "Legal Fees", "Land Holding Costs", "Finance Cost (Interest)", "Total Costs"]
            
            # Third group: Profitability
            profit_metrics = ["Expected Revenue", "Profit", "Profit Margin", 
                             "Equity Required", "Return on Equity (ROE)", "Internal Rate of Return (IRR)"]
            
            # Create 2-column layout for each section
            col_width = 90
            
            # Add site metrics in two columns
            for i in range(0, len(site_metrics), 2):
                pdf.set_font("Arial", "B", 10)
                if i == 0:
                    pdf.cell(0, 8, "Site & Building Details:", 0, 1)
                    pdf.ln(2)
                
                # Find metrics in the list
                left_metric = next((item for item in metrics_list if item[0] == site_metrics[i]), None)
                right_metric = next((item for item in metrics_list if i+1 < len(site_metrics) and item[0] == site_metrics[i+1]), None)
                
                if left_metric:
                    pdf.set_font("Arial", "", 9)
                    pdf.cell(col_width, 5, f"{left_metric[0]}: {left_metric[1]}", 0, 0)
                
                if right_metric:
                    pdf.set_font("Arial", "", 9)
                    pdf.cell(col_width, 5, f"{right_metric[0]}: {right_metric[1]}", 0, 1)
                else:
                    pdf.ln(5)
            
            pdf.ln(5)
            
            # Add cost metrics
            for i in range(0, len(cost_metrics), 2):
                pdf.set_font("Arial", "B", 10)
                if i == 0:
                    pdf.cell(0, 8, "Cost Breakdown:", 0, 1)
                    pdf.ln(2)
                
                left_metric = next((item for item in metrics_list if item[0] == cost_metrics[i]), None)
                right_metric = next((item for item in metrics_list if i+1 < len(cost_metrics) and item[0] == cost_metrics[i+1]), None)
                
                if left_metric:
                    pdf.set_font("Arial", "", 9)
                    pdf.cell(col_width, 5, f"{left_metric[0]}: {left_metric[1]}", 0, 0)
                
                if right_metric:
                    pdf.set_font("Arial", "", 9)
                    pdf.cell(col_width, 5, f"{right_metric[0]}: {right_metric[1]}", 0, 1)
                else:
                    pdf.ln(5)
            
            pdf.ln(5)
            
            # Add profit metrics with emphasis
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 8, "Revenue and Profitability:", 0, 1)
            pdf.ln(2)
            
            for metric in profit_metrics:
                metric_data = next((item for item in metrics_list if item[0] == metric), None)
                if metric_data:
                    if metric in ["Expected Revenue", "Profit", "Equity Required"]:
                        pdf.set_font("Arial", "B", 9)
                    else:
                        pdf.set_font("Arial", "", 9)
                    pdf.cell(0, 5, f"{metric_data[0]}: {metric_data[1]}", 0, 1, ln=True)
            
            pdf.ln(8)
            pdf.set_font("Arial", "I", 8)
            pdf.cell(0, 6, "Generated by Property Development Feasibility Calculator", 0, 0, "C")
            
            # Generate the PDF as bytes for download
            pdf_output = pdf.output(dest='S')
            if isinstance(pdf_output, str):
                pdf_bytes = pdf_output.encode('latin-1')
            else:
                pdf_bytes = pdf_output
            pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
            
            return pdf_data

        try:
            pdf_report = create_pdf_report()
            
            # Create download button for PDF report
            pdf_download = f'<a href="data:application/pdf;base64,{pdf_report}" download="property_feasibility_report.pdf">Download PDF Report</a>'
            st.markdown(pdf_download, unsafe_allow_html=True)
            
            # Add a cleaner button-style download option
            if st.button("Generate & Download PDF Report"):
                # Increment PDF export count for basic users
                if access_level == "basic":
                    auth.increment_pdf_export_count(user.id)
                
                st.download_button(
                    label="Click to Download Report",
                    data=base64.b64decode(pdf_report),
                    file_name="property_feasibility_report.pdf",
                    mime="application/pdf"
                )
                st.success("✅ PDF report generated successfully!")
                
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")

# Create a clear separation after the inputs and results
st.markdown("---")
st.markdown("### 💡 Key Insights")

if profit > 0:
    st.success(f"✅ This project shows a profit of ${profit:,.0f} with a {profit_margin:.1f}% margin")
else:
    st.error(f"❌ This project shows a loss of ${abs(profit):,.0f}")

if roe > 15:
    st.success(f"✅ Excellent return on equity of {roe:.1f}%")
elif roe > 10:
    st.info(f"💡 Good return on equity of {roe:.1f}%")
else:
    st.warning(f"⚠️ Low return on equity of {roe:.1f}%")
