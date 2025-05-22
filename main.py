import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import base64
from fpdf import FPDF
import datetime
import numpy_financial as npf

# Set page configuration
st.set_page_config(
    page_title="Property Development Feasibility Calculator",
    page_icon="🏢",
    layout="wide"
)

# Title and description
st.title("Property Development Feasibility Calculator")
st.markdown("""
This calculator helps property developers evaluate the feasibility of development projects
by calculating key financial metrics based on input parameters.
""")

# Set up the initial layout with more space for results
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Input Parameters")
    
    # Site details
    st.subheader("Site Details")
    site_address = st.text_input("Site Address", value="123 Property Street, Suburb", 
                              help="The street address of the development site")
    
    site_price = st.number_input("Site Purchase Price (AUD)", 
                               min_value=0, value=4900000, step=100000,
                               format="%d", help="The cost to purchase the development site")
    
    site_size = st.number_input("Site Size (sqm)", 
                              min_value=0, value=613, step=10,
                              format="%d", help="The total area of the site in square meters")
    
    fsr = st.number_input("Floor Space Ratio (FSR)", 
                        min_value=0.0, value=0.7, step=0.1,
                        format="%.2f", help="The ratio of a building's total floor area to the size of the land")
    
    nsa_ratio = st.number_input("Net Sellable Area Ratio (NSA %)", 
                              min_value=50.0, max_value=100.0, value=85.0, step=1.0,
                              format="%.1f", help="The percentage of Gross Floor Area that is sellable (excluding common areas)")
    
    num_dwellings = st.number_input("Number of Dwellings", 
                                  min_value=1, value=4, step=1,
                                  format="%d", help="The total number of dwellings to be built")
    
    # Construction costs
    st.subheader("Construction & Costs")
    demolition_cost = st.number_input("Demolition Cost (AUD)", 
                                     min_value=0, value=0, step=10000,
                                     format="%d", help="Fixed cost for demolition of existing structures")
    
    construction_cost = st.number_input("Construction Cost per sqm (AUD)", 
                                      min_value=0, value=8000, step=100,
                                      format="%d", help="The construction cost per square meter")
    
    consultant_costs_pct = st.number_input("Consultant & Approval Costs (%)", 
                                        min_value=0.0, value=10.0, step=0.5,
                                        format="%.1f", help="Percentage of construction cost allocated to consultants and approvals")
    
    marketing_costs_pct = st.number_input("Marketing Costs (%)", 
                                       min_value=0.0, value=1.5, step=0.1,
                                       format="%.1f", help="Percentage of expected revenue allocated to marketing")
    
    agents_fees_pct = st.number_input("Agents Fees (%)", 
                                    min_value=0.0, value=1.5, step=0.1,
                                    format="%.1f", help="Percentage of expected revenue paid as agents fees")
    
    gst_pct = st.number_input("GST on Sales Revenue (%)", 
                           min_value=0.0, value=10.0, step=0.5,
                           format="%.1f", help="Percentage of sales revenue for Goods and Services Tax (GST)")
    
    # Additional fees
    statutory_fees_pct = st.number_input("Statutory Fees (% of total cost)", 
                                  min_value=0.0, value=1.0, step=0.1,
                                  format="%.1f", help="Government and authority fees as a percentage of total project cost")
    
    legal_fees_pct = st.number_input("Legal Fees (% of development cost)", 
                              min_value=0.0, value=0.5, step=0.1,
                              format="%.1f", help="Legal costs as a percentage of total development cost (site purchase + construction)")
    
    land_holding_cost_pct = st.number_input("Land Holding Cost (% of site price p.a.)", 
                                      min_value=0.0, value=5.0, step=0.5,
                                      format="%.1f", help="Annual holding cost as a percentage of site purchase price")
    
    # Financial parameters
    st.subheader("Financial Parameters")
    lvr_pct = st.number_input("Loan-to-Value Ratio (LVR %)", 
                           min_value=0.0, max_value=100.0, value=65.0, step=1.0,
                           format="%.1f", help="The percentage of the site price that can be borrowed")
    
    interest_rate_pct = st.number_input("Finance Interest Rate (%)", 
                                      min_value=0.0, value=7.0, step=0.25,
                                      format="%.2f", help="Annual interest rate on the loan")
    
    project_timeline = st.number_input("Project Timeline (Months)", 
                                     min_value=1, value=24, step=1,
                                     format="%d", help="Total duration of the project in months")
    
    # Sales parameters
    st.subheader("Sales Parameters")
    avg_sale_price = st.number_input("Average Sale Price per sqm (AUD)", 
                                   min_value=0, value=38000, step=1000,
                                   format="%d", help="Expected average sale price per square meter")
    
    stamp_duty_pct = st.number_input("Stamp Duty (%)", 
                                  min_value=0.0, value=5.5, step=0.1,
                                  format="%.1f", help="Percentage of site price that must be paid as stamp duty")

# Perform calculations
gfa = site_size * fsr
nsa = gfa * (nsa_ratio / 100)  # Calculate Net Sellable Area
avg_dwelling_size = nsa / num_dwellings if num_dwellings > 0 else 0
build_cost_per_sqm = construction_cost  # Cost per sqm of GFA
land_cost_per_gfa = site_price / gfa if gfa > 0 else 0  # Land cost per sqm of GFA
total_build_cost = gfa * construction_cost
consultant_costs = gfa * construction_cost * (consultant_costs_pct / 100)
expected_revenue = nsa * avg_sale_price  # Revenue based on sellable area
gst = expected_revenue * (gst_pct / 100)  # GST on sales revenue
price_per_dwelling = expected_revenue / num_dwellings if num_dwellings > 0 else 0
# Calculate both marketing costs and agents fees separately
marketing_costs = expected_revenue * (marketing_costs_pct / 100)
agents_fees = expected_revenue * (agents_fees_pct / 100)
stamp_duty = site_price * (stamp_duty_pct / 100)

# Calculate finance costs on both site price and building costs
site_finance_cost = site_price * (lvr_pct / 100) * (interest_rate_pct / 100) * (project_timeline / 12)

# Assume building costs are spread over half the project timeline (progressive drawdown)
# This is a simplified assumption that construction happens over the latter half of the project
building_finance_cost = (total_build_cost + consultant_costs + demolition_cost) * (lvr_pct / 100) * (interest_rate_pct / 100) * (project_timeline / 24)

finance_cost = site_finance_cost + building_finance_cost

# Calculate total land holding costs as percentage of site price over the project timeline
# Convert annual percentage to total for the project duration
annual_land_holding_rate = land_holding_cost_pct / 100
project_duration_years = project_timeline / 12
total_land_holding_costs = site_price * annual_land_holding_rate * project_duration_years

# Calculate legal fees as a percentage of development cost (site price + construction)
development_cost = site_price + total_build_cost
legal_fees = development_cost * (legal_fees_pct / 100)

# We need to calculate statutory fees which depends on total costs, but total costs include statutory fees
# To resolve this circular dependency, we'll calculate a subtotal first, then apply the percentage
subtotal_costs = site_price + total_build_cost + consultant_costs + marketing_costs + agents_fees + stamp_duty + finance_cost + demolition_cost + gst + legal_fees + total_land_holding_costs
statutory_fees = subtotal_costs * (statutory_fees_pct / 100)

total_costs = subtotal_costs + statutory_fees
profit = expected_revenue - total_costs
profit_margin_pct = (profit / expected_revenue) * 100 if expected_revenue > 0 else 0
equity_required = (site_price + total_build_cost + consultant_costs + demolition_cost) * (1 - (lvr_pct / 100))
roe_pct = (profit / equity_required) * 100 if equity_required > 0 else 0

# Calculate Internal Rate of Return (IRR)
annual_project_duration = project_timeline / 12
if annual_project_duration > 0 and equity_required > 0:
    # Create cash flow array: initial investment (negative) followed by profit (positive)
    cash_flows = [-equity_required] + [0] * (int(project_timeline) - 1) + [profit + equity_required]
    
    try:
        # Calculate monthly IRR then convert to annual
        monthly_rate = npf.irr(cash_flows)
        annual_rate = (1 + monthly_rate) ** 12 - 1
        irr_pct = annual_rate * 100
    except:
        # Fallback if IRR calculation fails (can happen with certain cash flow patterns)
        irr_pct = ((profit / equity_required) ** (1 / annual_project_duration) - 1) * 100
else:
    irr_pct = 0

# Display results in the second column (right side)
with col2:
    st.header("Feasibility Results")
    
    # Create a DataFrame for the metrics
    metrics_df = pd.DataFrame({
        'Metric': [
            'Site Address',
            'Site Purchase Price', 
            'Gross Floor Area (GFA)',
            'Net Sellable Area (NSA)',
            'NSA Ratio',
            'Number of Dwellings',
            'Average Dwelling Size',
            'Price per Dwelling',
            'Construction Cost per GFA',
            'Land Cost per GFA',
            'Total Build Cost',
            'Demolition Cost',
            'Consultant & Approval Costs',
            'Marketing Costs',
            'Agents Fees',
            'Stamp Duty',
            'GST on Sales',
            'Statutory Fees',
            'Legal Fees',
            'Land Holding Costs',
            'Finance Cost (Interest)',
            'Total Costs',
            'Expected Revenue',
            'Profit',
            'Profit Margin',
            'Equity Required',
            'Return on Equity (ROE)',
            'Internal Rate of Return (IRR)'
        ],
        'Value': [
            f"{site_address}",
            f"${site_price:,.0f}",
            f"{gfa:,.2f} sqm",
            f"{nsa:,.2f} sqm",
            f"{nsa_ratio:.1f}%",
            f"{num_dwellings}",
            f"{avg_dwelling_size:,.2f} sqm",
            f"${price_per_dwelling:,.0f}",
            f"${build_cost_per_sqm:,.0f}/sqm",
            f"${land_cost_per_gfa:,.0f}/sqm",
            f"${total_build_cost:,.0f}",
            f"${demolition_cost:,.0f}",
            f"${consultant_costs:,.0f}",
            f"${marketing_costs:,.0f}",
            f"${agents_fees:,.0f}",
            f"${stamp_duty:,.0f}",
            f"${gst:,.0f}",
            f"${statutory_fees:,.0f}",
            f"${legal_fees:,.0f}",
            f"${total_land_holding_costs:,.0f}",
            f"${finance_cost:,.0f}",
            f"${total_costs:,.0f}",
            f"${expected_revenue:,.0f}",
            f"${profit:,.0f}",
            f"{profit_margin_pct:.2f}%",
            f"${equity_required:,.0f}",
            f"{roe_pct:.2f}%",
            f"{irr_pct:.2f}% p.a."
        ]
    })
    
    # Group metrics by categories for better display without scrolling
    # Create categories
    site_details = metrics_df[metrics_df['Metric'].isin(['Site Address', 'Site Purchase Price', 'Gross Floor Area (GFA)', 
                                             'Net Sellable Area (NSA)', 'NSA Ratio', 'Land Cost per GFA'])]
    
    building_details = metrics_df[metrics_df['Metric'].isin(['Number of Dwellings', 'Average Dwelling Size', 'Price per Dwelling', 
                                                 'Construction Cost per GFA'])]
    
    # Filter metrics for costs
    construction_costs = metrics_df[metrics_df['Metric'].isin(['Total Build Cost', 'Demolition Cost', 'Consultant & Approval Costs',
                                                 'Marketing Costs', 'Agents Fees', 'Stamp Duty'])]
    
    additional_costs = metrics_df[metrics_df['Metric'].isin(['GST on Sales', 'Statutory Fees', 'Legal Fees', 
                                               'Land Holding Costs', 'Finance Cost (Interest)', 'Total Costs'])]
    
    profitability = metrics_df[metrics_df['Metric'].isin(['Expected Revenue', 'Profit', 'Profit Margin', 
                                               'Equity Required', 'Return on Equity (ROE)', 'Internal Rate of Return (IRR)'])]
    
    # Display metrics in organized sections with two columns for costs
    st.subheader("Site Details")
    st.dataframe(site_details, use_container_width=True, hide_index=True)
    
    st.subheader("Building Details")
    st.dataframe(building_details, use_container_width=True, hide_index=True)
    
    # Split costs into two sections to avoid scrolling
    st.subheader("Costs")
    
    cost_col1, cost_col2 = st.columns(2)
    
    with cost_col1:
        st.caption("Construction Costs")
        st.dataframe(construction_costs, use_container_width=True, hide_index=True)
        
    with cost_col2:
        st.caption("Additional Costs & Fees")
        st.dataframe(additional_costs, use_container_width=True, hide_index=True)
    
    st.subheader("Profitability")
    st.dataframe(profitability, use_container_width=True, hide_index=True)
    
    # Function to create PDF report
    def create_pdf_report():
        pdf = FPDF()
        pdf.add_page()
        
        # Set up the PDF with smaller margins
        pdf.set_margins(10, 10, 10)
        
        # Set up the PDF header
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Property Development Feasibility Report", ln=True, align="C")
        
        # Add date in smaller font
        pdf.set_font("Arial", "", 8)
        report_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.cell(0, 4, f"Report generated: {report_date}", ln=True)
        
        # Project details section - using a single column layout
        pdf.ln(2)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Project Details", ln=True)
        pdf.set_font("Arial", "", 9)
        
        # Project details in a single column
        pdf.cell(0, 5, f"Site Size: {site_size} sqm", ln=True)
        pdf.cell(0, 5, f"FSR: {fsr}", ln=True)
        pdf.cell(0, 5, f"Number of Dwellings: {num_dwellings}", ln=True)
        pdf.cell(0, 5, f"NSA Ratio: {nsa_ratio:.1f}%", ln=True)
        pdf.cell(0, 5, f"Project Timeline: {project_timeline} months", ln=True)
        pdf.cell(0, 5, f"Avg. Dwelling Size: {avg_dwelling_size:.2f} sqm", ln=True)
        pdf.ln(3)
        
        # Financial metrics section - making this more compact
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Financial Summary", ln=True)
        pdf.set_font("Arial", "", 9)
        
        # Loop through metrics dataframe to add values
        metrics_list = list(zip(metrics_df['Metric'], metrics_df['Value']))
        
        # First group: Site and building details
        site_metrics = ["Site Address", "Site Purchase Price", "Gross Floor Area (GFA)", "Net Sellable Area (NSA)", 
                       "NSA Ratio", "Number of Dwellings", "Average Dwelling Size", "Price per Dwelling",
                       "Construction Cost per GFA", "Land Cost per GFA"]
        
        # Second group: Costs
        cost_metrics = ["Total Build Cost", "Demolition Cost", "Consultant & Approval Costs", 
                       "Marketing & Sales Costs", "Stamp Duty", "GST on Sales", "Statutory Fees",
                       "Legal Fees", "Land Holding Costs", "Finance Cost (Interest)", "Total Costs"]
        
        # Third group: Revenue and profit
        profit_metrics = ["Expected Revenue", "Profit", "Profit Margin", 
                         "Equity Required", "Return on Equity (ROE)", "Internal Rate of Return (IRR)"]
        
        # Display site metrics in a single column with clear spacing
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Site and Building Details:", ln=True)
        pdf.set_font("Arial", "", 9)
        
        for metric, value in metrics_list:
            if metric in site_metrics:
                pdf.cell(0, 5, f"{metric}: {value}", ln=True)
        
        # Display cost metrics in two groups for better organization
        pdf.ln(3)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Construction Costs:", ln=True)
        pdf.set_font("Arial", "", 9)
        
        construction_cost_metrics = ["Total Build Cost", "Demolition Cost", "Consultant & Approval Costs", 
                                    "Marketing Costs", "Agents Fees", "Stamp Duty"]
        
        for metric, value in metrics_list:
            if metric in construction_cost_metrics:
                pdf.cell(0, 5, f"{metric}: {value}", ln=True)
                
        pdf.ln(3)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Additional Costs & Fees:", ln=True)
        pdf.set_font("Arial", "", 9)
        
        additional_cost_metrics = ["GST on Sales", "Statutory Fees", "Legal Fees", 
                                  "Land Holding Costs", "Finance Cost (Interest)", "Total Costs"]
        
        for metric, value in metrics_list:
            if metric in additional_cost_metrics:
                pdf.cell(0, 5, f"{metric}: {value}", ln=True)
        
        # Display profit metrics with emphasis
        pdf.ln(3)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Revenue and Profitability:", ln=True)
        pdf.set_font("Arial", "B", 9)
        
        for metric, value in metrics_list:
            if metric in profit_metrics:
                pdf.cell(0, 5, f"{metric}: {value}", ln=True)
        
        # Convert to bytes for download
        # Generate the PDF as bytes for download
pdf_output = pdf.output(dest='S')
if isinstance(pdf_output, str):
    pdf_bytes = pdf_output.encode('latin-1')
else:
    pdf_bytes = pdf_output
pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
if isinstance(pdf_output, str):
    pdf_bytes = pdf_output.encode('latin-1')
else:
    pdf_bytes = pdf_output
pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
        return pdf_data
    
    # Create download button for PDF report
    pdf_report = create_pdf_report()
    b64_pdf = base64.b64encode(pdf_report).decode("utf-8")
    pdf_download = f'<a href="data:application/pdf;base64,{b64_pdf}" download="property_feasibility_report.pdf">Download PDF Report</a>'
    st.markdown(pdf_download, unsafe_allow_html=True)
    
    # Add a cleaner button-style download option
    if st.button("Generate & Download PDF Report"):
        st.download_button(
            label="Click to Download Report",
            data=pdf_report,
            file_name="property_feasibility_report.pdf",
            mime="application/pdf"
        )

# Create a clear separation after the inputs and results
st.write("")
st.write("---")

# Add visualizations
st.header("Visualizations")

# Create cost breakdown pie chart
cost_items = [
    ('Site Purchase', site_price),
    ('Construction', total_build_cost),
    ('Demolition', demolition_cost),
    ('Consultants', consultant_costs),
    ('Marketing', marketing_costs),
    ('Stamp Duty', stamp_duty),
    ('GST on Sales', gst),
    ('Statutory Fees', statutory_fees),
    ('Legal Fees', legal_fees),
    ('Land Holding', total_land_holding_costs),
    ('Finance Cost', finance_cost)
]

# Sort costs from highest to lowest for better visualization
cost_items.sort(key=lambda x: x[1], reverse=True)

# Create two columns for charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Cost Breakdown")
    
    # Filter out costs that are too small to display clearly (less than 1% of total)
    significant_costs = [(name, cost) for name, cost in cost_items if cost > total_costs * 0.01]
    other_costs = sum(cost for name, cost in cost_items if cost <= total_costs * 0.01)
    
    # Add "Other" category if needed
    if other_costs > 0:
        significant_costs.append(('Other', other_costs))
        
    cost_names = [item[0] for item in significant_costs]
    cost_values = [item[1] for item in significant_costs]
    
    fig = px.pie(
        values=cost_values,
        names=cost_names,
        title="Cost Distribution",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("Profit Analysis")
    
    # Create a waterfall chart showing how revenue becomes profit
    revenue_to_profit = [
        {"Category": "Revenue", "Amount": expected_revenue, "Type": "absolute"},
        {"Category": "Site Cost", "Amount": -site_price, "Type": "relative"},
        {"Category": "Construction", "Amount": -total_build_cost, "Type": "relative"},
        {"Category": "Other Costs", "Amount": -(total_costs - site_price - total_build_cost), "Type": "relative"},
        {"Category": "Profit", "Amount": profit, "Type": "total"}
    ]
    
    df_waterfall = pd.DataFrame(revenue_to_profit)
    
    fig = go.Figure(go.Waterfall(
        name = "Profit Breakdown",
        orientation = "v",
        measure = df_waterfall["Type"],
        x = df_waterfall["Category"],
        y = df_waterfall["Amount"],
        text = [f"${abs(val):,.0f}" for val in df_waterfall["Amount"]],
        textposition = "outside",
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        decreasing = {"marker":{"color":"#EF553B"}},
        increasing = {"marker":{"color":"#00CC96"}},
        totals = {"marker":{"color":"#636EFA"}}
    ))
    
    fig.update_layout(
        title = "From Revenue to Profit",
        showlegend = False
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Create new layout for investment summary and KPIs (full width)
st.header("Investment Summary")
summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

with summary_col1:
    st.metric(
        label="Equity Required", 
        value=f"${equity_required:,.0f}",
        help="The amount of money required from investors (not covered by loans)"
    )

with summary_col2:
    st.metric(
        label="Debt Financing", 
        value=f"${(site_price + total_build_cost + consultant_costs + demolition_cost) * (lvr_pct / 100):,.0f}",
        help="The amount of money borrowed through loans"
    )

with summary_col3:
    st.metric(
        label="Profit", 
        value=f"${profit:,.0f}",
        delta=f"{profit_margin_pct:.1f}%" if profit_margin_pct > 0 else f"{profit_margin_pct:.1f}%",
        delta_color="normal",
        help="The expected profit from the development"
    )

with summary_col4:
    st.metric(
        label="IRR (p.a.)", 
        value=f"{irr_pct:.2f}%",
        delta=f"ROE: {roe_pct:.1f}%",
        delta_color="normal",
        help="Internal Rate of Return (annualized) and Return on Equity"
    )
