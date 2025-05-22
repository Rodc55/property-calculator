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
        pdf_data = pdf.output(dest='S').encode('latin-1')
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

with summary_col4:import streamlit as st
import hmac
import sqlite3
import uuid
import datetime
from dataclasses import dataclass
import time

# Database setup and management
def init_auth_db():
    """Initialize the authentication database"""
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        subscription_tier TEXT DEFAULT 'free',
        subscription_start DATE,
        subscription_end DATE
    )
    ''')
    
    # Create sessions table
    c.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

@dataclass
class User:
    id: int
    email: str
    name: str
    subscription_tier: str
    subscription_start: str = None
    subscription_end: str = None

def get_user_by_email(email):
    """Get user details from email"""
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    c.execute('SELECT id, email, name, subscription_tier, subscription_start, subscription_end FROM users WHERE email = ?', (email,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        return User(
            id=user_data[0],
            email=user_data[1],
            name=user_data[2],
            subscription_tier=user_data[3],
            subscription_start=user_data[4],
            subscription_end=user_data[5]
        )
    return None

def create_user(email, name, password):
    """Create a new user"""
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (email, name, password) VALUES (?, ?, ?)',
                 (email, name, password))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def verify_password(email, password):
    """Verify user password"""
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE email = ?', (email,))
    stored_password = c.fetchone()
    conn.close()
    
    if stored_password and stored_password[0] == password:
        return True
    return False

def create_session(user_id, expiry_days=30):
    """Create a new session for a user"""
    session_id = str(uuid.uuid4())
    expires_at = datetime.datetime.now() + datetime.timedelta(days=expiry_days)
    
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    c.execute('INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)',
             (session_id, user_id, expires_at))
    conn.commit()
    conn.close()
    
    return session_id

def get_user_from_session(session_id):
    """Get user details from session ID"""
    if not session_id:
        return None
        
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    c.execute('''
    SELECT u.id, u.email, u.name, u.subscription_tier, u.subscription_start, u.subscription_end
    FROM sessions s
    JOIN users u ON s.user_id = u.id
    WHERE s.id = ? AND s.expires_at > CURRENT_TIMESTAMP
    ''', (session_id,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        return User(
            id=user_data[0],
            email=user_data[1],
            name=user_data[2],
            subscription_tier=user_data[3],
            subscription_start=user_data[4],
            subscription_end=user_data[5]
        )
    return None

def update_subscription(user_id, tier, months=1):
    """Update user subscription"""
    today = datetime.date.today()
    
    # Get current subscription info
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    c.execute('SELECT subscription_end FROM users WHERE id = ?', (user_id,))
    current_end = c.fetchone()
    
    # Calculate new end date
    if current_end and current_end[0] and datetime.datetime.strptime(current_end[0], '%Y-%m-%d').date() > today:
        start_date = datetime.datetime.strptime(current_end[0], '%Y-%m-%d').date()
    else:
        start_date = today
        
    end_date = start_date + datetime.timedelta(days=30*months)
    
    # Update subscription
    c.execute('''
    UPDATE users 
    SET subscription_tier = ?, subscription_start = ?, subscription_end = ?
    WHERE id = ?
    ''', (tier, today.isoformat(), end_date.isoformat(), user_id))
    
    conn.commit()
    conn.close()
    
def check_subscription_active(user):
    """Check if user has an active subscription"""
    if not user:
        return False
        
    if user.subscription_tier == 'free':
        return False
        
    if not user.subscription_end:
        return False
        
    end_date = datetime.datetime.strptime(user.subscription_end, '%Y-%m-%d').date()
    return end_date >= datetime.date.today()

# Authentication UI components
def login_form():
    """Display login form"""
    st.subheader("Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if verify_password(email, password):
                user = get_user_by_email(email)
                session_id = create_session(user.id)
                st.session_state.session_id = session_id
                st.session_state.user = user
                st.success(f"Welcome back, {user.name}!")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("Invalid email or password")

def register_form():
    """Display registration form"""
    st.subheader("Register")
    
    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if password != confirm_password:
                st.error("Passwords do not match")
            elif not email or not password or not name:
                st.error("All fields are required")
            else:
                user_id = create_user(email, name, password)
                if user_id:
                    st.success("Registration successful! Please login.")
                    time.sleep(1)
                    st.session_state.show_register = False
                    st.experimental_rerun()
                else:
                    st.error("Email already registered")

def subscription_page():
    """Display subscription options"""
    st.title("Upgrade Your Account")
    
    st.write("Choose a subscription plan to unlock all features:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Basic")
        st.write("$9.99/month")
        st.write("• Basic calculations")
        st.write("• PDF export")
        if st.button("Select Basic"):
            handle_payment("basic", 9.99, 1)
    
    with col2:
        st.subheader("Pro")
        st.write("$19.99/month")
        st.write("• All Basic features")
        st.write("• Advanced visualizations")
        st.write("• Export unlimited reports")
        if st.button("Select Pro"):
            handle_payment("pro", 19.99, 1)
    
    with col3:
        st.subheader("Enterprise")
        st.write("$49.99/month")
        st.write("• All Pro features")
        st.write("• Priority support")
        st.write("• Team collaboration")
        if st.button("Select Enterprise"):
            handle_payment("enterprise", 49.99, 1)
    
    st.markdown("---")
    
    # Annual options with discount
    st.subheader("Save with annual billing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("Basic Annual")
        st.write("$99.99/year (Save 17%)")
        if st.button("Select Basic Annual"):
            handle_payment("basic", 99.99, 12)
    
    with col2:
        st.write("Pro Annual")
        st.write("$199.99/year (Save 17%)")
        if st.button("Select Pro Annual"):
            handle_payment("pro", 199.99, 12)
    
    with col3:
        st.write("Enterprise Annual")
        st.write("$499.99/year (Save 17%)")
        if st.button("Select Enterprise Annual"):
            handle_payment("enterprise", 499.99, 12)

def handle_payment(tier, amount, months):
    """Handle payment processing"""
    st.session_state.payment_tier = tier
    st.session_state.payment_amount = amount
    st.session_state.payment_months = months
    st.session_state.show_payment = True
    
def payment_form():
    """Display payment form"""
    st.title("Complete Your Purchase")
    
    tier = st.session_state.payment_tier
    amount = st.session_state.payment_amount
    months = st.session_state.payment_months
    
    st.write(f"Selected plan: {tier.title()}")
    if months == 1:
        st.write(f"Amount: ${amount:.2f}/month")
    else:
        st.write(f"Amount: ${amount:.2f}/year")
    
    with st.form("payment_form"):
        st.text_input("Cardholder Name")
        st.text_input("Card Number")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Expiry Date (MM/YY)")
        with col2:
            st.text_input("CVV", max_chars=4)
        
        submitted = st.form_submit_button("Complete Payment")
        
        if submitted:
            # In a real app, you would process the payment here
            # For this demo, we'll just update the subscription
            if st.session_state.user:
                update_subscription(st.session_state.user.id, tier, months)
                user = get_user_by_email(st.session_state.user.email)
                st.session_state.user = user
                st.success("Payment successful! Your subscription has been updated.")
                st.session_state.show_payment = False
                time.sleep(1)
                st.experimental_rerun()

def auth_page():
    """Main authentication page"""
    init_auth_db()
    
    # Check if user is logged in
    if "session_id" in st.session_state:
        user = get_user_from_session(st.session_state.session_id)
        if user:
            st.session_state.user = user
            return True
            
    # Initialize state for registration form
    if "show_register" not in st.session_state:
        st.session_state.show_register = False
        
    # Initialize state for payment
    if "show_payment" not in st.session_state:
        st.session_state.show_payment = False
    
    # Show payment form if needed
    if st.session_state.show_payment:
        payment_form()
        return False
    
    # Landing page with login/register options
    st.title("Property Feasibility Calculator")
    st.write("A comprehensive property development feasibility calculator with advanced financial analysis features.")
    
    # Show features
    st.markdown("### Key Features")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("• Advanced financial modeling")
        st.markdown("• Percentage-based fee calculations")
        st.markdown("• Interactive visualizations")
    
    with col2:
        st.markdown("• PDF report generation")
        st.markdown("• Comprehensive cost analysis")
        st.markdown("• Return metrics (IRR, ROE)")
    
    st.markdown("---")
    
    # Authentication interface
    auth_col1, auth_col2 = st.columns(2)
    
    with auth_col1:
        if not st.session_state.show_register:
            login_form()
            if st.button("Need an account? Register here"):
                st.session_state.show_register = True
                st.experimental_rerun()
    
    with auth_col2:
        if st.session_state.show_register:
            register_form()
            if st.button("Already have an account? Login here"):
                st.session_state.show_register = False
                st.experimental_rerun()
    
    # Allow limited trial
    if st.button("Try limited version"):
        # Create a temporary session without login
        st.session_state.trial_mode = True
        st.experimental_rerun()
        
    return False

def logout():
    """Log out the current user"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

def user_info_section():
    """Display user info and subscription status"""
    if "user" in st.session_state:
        user = st.session_state.user
        
        # Subscription status
        subscription_active = check_subscription_active(user)
        
        # Display user info in sidebar
        with st.sidebar:
            st.write(f"Logged in as: {user.name}")
            
            if subscription_active:
                st.success(f"Subscription: {user.subscription_tier.title()} (Active)")
                st.write(f"Expires: {user.subscription_end}")
            elif user.subscription_tier != 'free':
                st.error(f"Subscription: {user.subscription_tier.title()} (Expired)")
                if st.button("Renew Subscription"):
                    st.session_state.show_subscription = True
            else:
                st.warning("Free tier (Limited features)")
                if st.button("Upgrade Account"):
                    st.session_state.show_subscription = True
            
            if st.button("Logout"):
                logout()
                
def check_access_level():
    """Check user's access level for features"""
    # Trial mode has very limited access
    if "trial_mode" in st.session_state and st.session_state.trial_mode:
        return "trial"
        
    # Check if user is logged in
    if "user" not in st.session_state:
        return "none"
        # Property Feasibility Calculator

A comprehensive property development feasibility calculator that enables precise financial analysis and project evaluation through advanced computational tools.

## Features

- Advanced financial modeling for real estate development
- Comprehensive cost and profitability calculations
- Dynamic land cost per GFA calculation
- Multiple percentage-based cost calculations (Legal, Statutory, Land Holding)
- Separate tracking of Marketing Costs and Agents Fees
- Interactive data visualizations (cost breakdown and profit analysis)
- PDF report generation with consolidated, clear layout
- Responsive UI with improved information visibility

## Installation

```bash
pip install -e .
```

## Running the Application

```bash
streamlit run app.py
```

## Requirements

- Python 3.8 or higher
- Streamlit
- Pandas
- NumPy
- Plotly
- FPDF

## Deploying to App Stores or Hosting Services

### Option 1: Streamlit Sharing

1. Create a GitHub repository with your app code
2. Push the code to GitHub
3. Go to [Streamlit Sharing](https://streamlit.io/sharing) and log in
4. Click "New app" and point to your GitHub repository
5. Configure your app settings and deploy

### Option 2: Heroku Deployment

1. Create a `Procfile` with:
   ```
   web: streamlit run app.py
   ```
2. Initialize a git repository, commit your files, and push to Heroku:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   heroku create your-app-name
   git push heroku master
   ```

### Option 3: Docker Container

1. Create a `Dockerfile`:
   ```Dockerfile
   FROM python:3.8-slim

   WORKDIR /app

   COPY . /app/
   RUN pip install -e .

   EXPOSE 8501

   CMD ["streamlit", "run", "app.py"]
   ```
2. Build and run the Docker container:
   ```bash
   docker build -t property-calculator .
   docker run -p 8501:8501 property-calculator
   ```

## App Store Distribution

For mobile app stores (iOS/Android), you would need to create a wrapper application using technologies like:

1. **For iOS App Store**:
   - Use frameworks like PyWebView or create a native Swift app with a WebView loading your hosted Streamlit app

2. **For Android Google Play**:
   - Utilize frameworks like PyWebView or create a native Kotlin/Java app with a WebView component loading your hosted Streamlit app

3. **Desktop App Stores**:
   - Package with Electron to create a desktop application
   - Use PyInstaller to create a standalone executable

## Directory Structure

```
property_feasibility_calculator/
├── app.py                   # Main Streamlit application
├── setup.py                 # Setup configuration for installation
├── requirements.txt         # Dependency requirements
├── README.md                # This documentation file
└── deploy/                  # Deployment configuration files
    ├── Dockerfile
    └── Procfile
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
    user = st.session_state.user
    subscription_active = check_subscription_active(user)
    
    # Free tier has basic access
    if user.subscription_tier == 'free' or not subscription_active:
        return "free"
        # Property Feasibility Calculator - Distribution Guide

This guide provides detailed instructions for packaging and distributing your Property Feasibility Calculator app across various platforms and app stores.

## 1. Web-Based Hosting Options

### Streamlit Cloud (Easiest Option)

1. Create a GitHub repository and push your code
2. Visit [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub account
4. Select your repository
5. Configure deploy settings (Python version, requirements)
6. Deploy with one click

### Heroku Deployment

1. Create a Heroku account
2. Install Heroku CLI
3. Run the following commands:
   ```bash
   heroku login
   heroku create your-property-calculator
   git init
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```
4. Your app will be available at `https://your-property-calculator.herokuapp.com`

### AWS Elastic Beanstalk

1. Install AWS CLI and EB CLI
2. Configure AWS credentials
3. Create an application:
   ```bash
   eb init -p python-3.8 property-calculator
   eb create property-calculator-env
   eb deploy
   ```

## 2. Creating Standalone Desktop Applications

### Using PyInstaller (Windows, macOS, Linux)

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Create a wrapper script (e.g., `run_app.py`):
   ```python
   import subprocess
   import os
   import sys
   
   # Get the directory where the executable is located
   if getattr(sys, 'frozen', False):
       application_path = os.path.dirname(sys.executable)
   else:
       application_path = os.path.dirname(os.path.abspath(__file__))
   
   # Change to that directory
   os.chdir(application_path)
   
   # Run the Streamlit app
   subprocess.call([
       "streamlit", "run", 
       os.path.join(application_path, "app.py"),
       "--browser.serverAddress=localhost",
       "--server.headless=true",
       "--server.port=8501"
   ])
   ```

3. Create the executable:
   ```bash
   pyinstaller --name PropertyCalculator --onefile --add-data "app.py:." run_app.py
   ```

4. The executable will be in the `dist` folder

### Using Electron (Cross-platform Desktop App)

1. Create a simple Electron wrapper:
   ```bash
   npm init -y
   npm install electron electron-builder
   ```

2. Create `main.js`:
   ```javascript
   const { app, BrowserWindow } = require('electron');
   const { spawn } = require('child_process');
   const path = require('path');
   
   let streamlitProcess;
   let mainWindow;
   
   function createWindow() {
     mainWindow = new BrowserWindow({
       width: 1200,
       height: 800,
       webPreferences: {
         nodeIntegration: true
       }
     });
   
     // Start Streamlit process
     streamlitProcess = spawn('streamlit', ['run', 'app.py', '--browser.serverAddress=localhost', '--server.headless=true', '--server.port=8501']);
     
     // Wait for Streamlit to start
     setTimeout(() => {
       mainWindow.loadURL('http://localhost:8501');
     }, 3000);
   
     mainWindow.on('closed', function () {
       mainWindow = null;
       streamlitProcess.kill();
     });
   }
   
   app.on('ready', createWindow);
   
   app.on('window-all-closed', function () {
     if (process.platform !== 'darwin') app.quit();
     if (streamlitProcess) streamlitProcess.kill();
   });
   
   app.on('activate', function () {
     if (mainWindow === null) createWindow();
   });
   ```

3. Build the app:
   ```bash
   npx electron-builder --win --mac --linux
   ```

## 3. Mobile App Stores

### iOS App Store Approach

1. Create a simple iOS WebView wrapper in Xcode using Swift:
   ```swift
   import UIKit
   import WebKit
   
   class ViewController: UIViewController, WKNavigationDelegate {
       var webView: WKWebView!
       
       override func viewDidLoad() {
           super.viewDidLoad()
           
           webView = WKWebView(frame: view.bounds)
           webView.navigationDelegate = self
           view.addSubview(webView)
           
           // Replace with your hosted Streamlit app URL
           if let url = URL(string: "https://your-hosted-app-url.com") {
               let request = URLRequest(url: url)
               webView.load(request)
           }
       }
   }
   ```

2. Submit to the App Store through Apple Developer account

### Google Play Store Approach

1. Create an Android WebView app in Android Studio:
   ```kotlin
   // MainActivity.kt
   import android.os.Bundle
   import android.webkit.WebView
   import androidx.appcompat.app.AppCompatActivity
   
   class MainActivity : AppCompatActivity() {
       override fun onCreate(savedInstanceState: Bundle?) {
           super.onCreate(savedInstanceState)
           setContentView(R.layout.activity_main)
           
           val webView = findViewById<WebView>(R.id.webview)
           webView.settings.javaScriptEnabled = true
           webView.loadUrl("https://your-hosted-app-url.com")
       }
   }
   ```

2. Submit to Google Play through Google Play Console

## 4. Monetization Options

1. **Freemium Model**: 
   - Basic calculations free
   - Advanced features (PDF export, detailed analysis) as paid upgrades

2. **Subscription Model**:
   - Monthly/annual subscription for access
   - Different tiers (basic, professional, enterprise)

3. **One-time Purchase**:
   - Flat fee for the app

4. **In-App Purchases**:
   - Pay per PDF report generated
   - Pay for additional analysis templates

## 5. Distribution Package Contents

Your distribution package should include:

```
property_calculator/
├── app.py                     # Main application 
├── setup.py                   # Installation configuration
├── README.md                  # Documentation
├── LICENSE                    # License information
├── .streamlit/                # Streamlit configuration
│   └── config.toml
├── deploy/                    # Deployment configurations
│   ├── Dockerfile
│   ├── Procfile
│   └── app_distribution_guide.md
└── assets/                    # Optional assets like icons, screenshots
    ├── app_icon.png
    ├── screenshot1.png
    └── screenshot2.png
```

## Security Considerations

1. If you integrate with external APIs or databases:
   - Use environment variables for sensitive credentials
   - Implement proper authentication
   - Consider data encryption for sensitive information

2. For data processing:
   - Clear disclosure on data use
   - Privacy policy compliance
   - GDPR considerations if targeting European users

## Post-Launch Support

1. Set up a support email or contact form
2. Consider a feedback mechanism within the app
3. Plan for regular updates and bug fixes
4. Documentation for users on how to use the app
# Deploying Your Property Feasibility Calculator with a Paywall: Comprehensive Guide

This guide provides step-by-step instructions for deploying your property feasibility calculator as a paid app, both as a web application and on app stores.

## 1. Web Deployment with a Paywall

### Setting up the Payment System

Your calculator is already set up with a subscription-based model, but you need to connect it to a payment processor:

1. **Stripe Integration**
   - Create a [Stripe account](https://dashboard.stripe.com/register)
   - Get your API keys from the Stripe Dashboard
   - Add your Stripe keys as environment variables when deploying:
     ```
     STRIPE_SECRET_KEY=sk_xxxxxxxx
     STRIPE_PUBLISHABLE_KEY=pk_xxxxxxxx
     ```
   - Create subscription products in your Stripe dashboard:
     - Basic Plan ($9.99/month)
     - Pro Plan ($19.99/month)
     - Enterprise Plan ($49.99/month)
     - And their annual equivalents

2. **Configure Your Domain**
   - Update the success and cancel URLs in `stripe_integration.py` to use your actual domain
   - Set up webhook handling for subscription events

### Web Hosting Options

1. **Heroku Deployment**
   ```bash
   # Create a Procfile (already done)
   echo "web: streamlit run main.py" > Procfile
   
   # Deploy to Heroku
   heroku create property-calculator
   heroku config:set STRIPE_SECRET_KEY=sk_xxxxxxxx
   heroku config:set STRIPE_PUBLISHABLE_KEY=pk_xxxxxxxx
   git push heroku main
   ```

2. **AWS Elastic Beanstalk**
   - Configure database for user accounts (Amazon RDS)
   - Set up environment variables for Stripe keys
   - Deploy using the EB CLI or AWS Console

3. **Digital Ocean App Platform**
   - Connect your GitHub repository
   - Configure environment variables
   - Select a plan and deploy

### Setting Up a Custom Domain

1. Purchase a domain name (e.g., propertycalculator.com)
2. Configure DNS settings to point to your hosting provider
3. Set up HTTPS with Let's Encrypt or your hosting provider's SSL

## 2. Mobile App Store Deployment

Your app requires a native wrapper to deploy on mobile app stores. We've prepared two approaches:

### For iOS App Store

1. **Create a WebView Wrapper**
   - Set up an Xcode project
   - Create a WebView that loads your web app
   - Add user authentication handling
   - Implement in-app purchases that sync with your web subscriptions

2. **Swift WebView Implementation**
   ```swift
   import UIKit
   import WebKit

   class ViewController: UIViewController, WKNavigationDelegate, WKScriptMessageHandler {
       var webView: WKWebView!
       
       override func viewDidLoad() {
           super.viewDidLoad()
           
           // Create configuration for JavaScript communication
           let config = WKWebViewConfiguration()
           let userContentController = WKUserContentController()
           userContentController.add(self, name: "subscriptionHandler")
           config.userContentController = userContentController
           
           // Create WebView
           webView = WKWebView(frame: view.bounds, configuration: config)
           webView.navigationDelegate = self
           view.addSubview(webView)
           
           // Load your hosted app
           if let url = URL(string: "https://your-domain.com") {
               let request = URLRequest(url: url)
               webView.load(request)
           }
       }
       
       // Handle messages from JavaScript
       func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
           if message.name == "subscriptionHandler" {
               // Process subscription events from the web app
               // Sync with StoreKit for in-app purchases
           }
       }
   }
   ```

3. **App Store Submission**
   - Create app icon and screenshots
   - Write app description and keywords
   - Configure in-app purchases
   - Submit for review

### For Google Play Store

1. **Create an Android WebView Wrapper**
   - Set up an Android Studio project
   - Create a WebView that loads your web app
   - Handle deep linking and state persistence

2. **Kotlin WebView Implementation**
   ```kotlin
   // MainActivity.kt
   import android.os.Bundle
   import android.webkit.WebView
   import android.webkit.WebViewClient
   import android.webkit.JavascriptInterface
   import androidx.appcompat.app.AppCompatActivity

   class MainActivity : AppCompatActivity() {
       override fun onCreate(savedInstanceState: Bundle?) {
           super.onCreate(savedInstanceState)
           setContentView(R.layout.activity_main)
           
           val webView = findViewById<WebView>(R.id.webview)
           webView.settings.javaScriptEnabled = true
           
           // Add JavaScript interface for communication
           webView.addJavascriptInterface(WebAppInterface(this), "Android")
           
           // Load your hosted app
           webView.webViewClient = WebViewClient()
           webView.loadUrl("https://your-domain.com")
       }
   }

   class WebAppInterface(private val context: Context) {
       @JavascriptInterface
       fun processSubscription(subscriptionData: String) {
           // Process subscription from web app
           // Integrate with Google Play Billing
       }
   }
   ```

3. **Google Play Submission**
   - Create app listing with screenshots and description
   - Configure Google Play Billing
   - Submit for review

## 3. Desktop App Store Deployment

For desktop app stores, package your Streamlit app with Electron:

1. **Create Electron Wrapper**
   - Set up an Electron project with npm
   - Create a main.js file that loads your web app

2. **Package for Mac App Store**
   - Sign your app with your Apple Developer ID
   - Use electron-builder to package for macOS
   - Submit to Mac App Store

3. **Package for Microsoft Store**
   - Sign your app with a Microsoft certificate
   - Use electron-builder to package for Windows
   - Submit to Microsoft Store

## 4. Sync User Accounts Across Platforms

To provide a seamless experience:

1. Implement a centralized user database (e.g., Firebase Authentication)
2. Create an API to verify subscription status
3. Sync subscription state between platforms
4. Provide "restore purchases" functionality

## 5. Analytics and Monitoring

1. Set up Google Analytics to track user engagement
2. Implement Stripe webhook handling for subscription events
3. Monitor churn rate and conversion metrics
4. A/B test different pricing strategies

## 6. Marketing Your App

1. Create a landing page highlighting key features
2. Implement SEO best practices
3. Consider paid advertising on relevant platforms
4. Engage with real estate development communities

## Next Steps

1. **First priority**: Set up your Stripe account and test the payment flow
2. Deploy the web version first - this is the foundation for all platforms
3. Choose one mobile platform to start with (iOS or Android)
4. Implement analytics to understand user behavior
5. Iterate based on user feedback

By following this guide, your Property Feasibility Calculator will be available as a paid application across web and app store platforms with a consistent subscription system.
FROM python:3.8-slim

WORKDIR /app

COPY . /app/
RUN pip install -e .

# Expose the port Streamlit will run on
EXPOSE 8501

# Command to run the app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
web: streamlit run app.py
import streamlit as st
import stripe
import os
import sqlite3
import datetime

# This would be set in your environment
# For development, you can use: stripe.api_key = "your_stripe_test_key"
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

def init_payments_db():
    """Initialize the payments database"""
    conn = sqlite3.connect('property_calculator_payments.db')
    c = conn.cursor()
    
    # Create payments table
    c.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        stripe_customer_id TEXT,
        stripe_subscription_id TEXT,
        stripe_payment_id TEXT,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        subscription_tier TEXT NOT NULL,
        subscription_start DATE,
        subscription_end DATE,
        status TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

def create_checkout_session(price_id, user_id, user_email):
    """Create a Stripe checkout session"""
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user_email,
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f'https://your-domain.com/success?session_id={{CHECKOUT_SESSION_ID}}&user_id={user_id}',
            cancel_url='https://your-domain.com/cancel',
            metadata={'user_id': user_id}
        )
        return checkout_session.url
    except Exception as e:
        return None

def verify_subscription(subscription_id):
    """Verify subscription status with Stripe"""
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription.status == 'active'
    except:
        return False

def update_user_subscription_from_webhook(event_data):
    """Process Stripe webhook event to update user subscription"""
    session = event_data['data']['object']
    user_id = session.get('metadata', {}).get('user_id')
    
    if not user_id:
        return False
    
    # Get subscription details
    subscription_id = session.get('subscription')
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    # Get plan details
    plan = subscription.items.data[0].plan
    tier = plan.nickname.lower() if plan.nickname else 'basic'
    amount = plan.amount / 100  # Convert from cents
    
    # Calculate end date based on billing interval
    start_date = datetime.datetime.fromtimestamp(subscription.current_period_start)
    end_date = datetime.datetime.fromtimestamp(subscription.current_period_end)
    
    # Update database
    conn = sqlite3.connect('property_calculator_payments.db')
    c = conn.cursor()
    c.execute('''
    INSERT INTO payments 
    (user_id, stripe_customer_id, stripe_subscription_id, amount, currency, 
    subscription_tier, subscription_start, subscription_end, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, 
        subscription.customer,
        subscription_id,
        amount,
        plan.currency,
        tier,
        start_date.date().isoformat(),
        end_date.date().isoformat(),
        subscription.status
    ))
    conn.commit()
    
    # Update user subscription status
    c.execute('''
    UPDATE users
    SET subscription_tier = ?, subscription_start = ?, subscription_end = ?
    WHERE id = ?
    ''', (tier, start_date.date().isoformat(), end_date.date().isoformat(), user_id))
    conn.commit()
    conn.close()
    
    return True

def display_stripe_prices():
    """Display Stripe price options in Streamlit"""
    # Fetch products and prices from Stripe
    try:
        products = stripe.Product.list(active=True, limit=100)
        
        # Group by product type
        monthly_products = []
        annual_products = []
        
        for product in products.data:
            if product.active:
                prices = stripe.Price.list(product=product.id, active=True)
                for price in prices.data:
                    if price.recurring:
                        product_info = {
                            'id': product.id,
                            'name': product.name,
                            'description': product.description or "",
                            'price_id': price.id,
                            'unit_amount': price.unit_amount / 100,  # Convert from cents
                            'currency': price.currency.upper(),
                            'interval': price.recurring.interval
                        }
                        
                        if price.recurring.interval == 'month':
                            monthly_products.append(product_info)
                        elif price.recurring.interval == 'year':
                            annual_products.append(product_info)
        
        # Sort products by price
        monthly_products.sort(key=lambda x: x['unit_amount'])
        annual_products.sort(key=lambda x: x['unit_amount'])
        
        # Display monthly subscriptions
        st.subheader("Monthly Subscriptions")
        cols = st.columns(len(monthly_products) if monthly_products else 1)
        
        for i, product in enumerate(monthly_products):
            with cols[i]:
                st.markdown(f"### {product['name']}")
                st.markdown(f"**${product['unit_amount']:.2f}/{product['interval']}**")
                st.markdown(product['description'])
                
                if st.button(f"Select {product['name']} Monthly", key=f"monthly_{i}"):
                    if 'user' in st.session_state:
                        user = st.session_state.user
                        checkout_url = create_checkout_session(
                            product['price_id'], 
                            user.id, 
                            user.email
                        )
                        if checkout_url:
                            st.session_state.checkout_url = checkout_url
                            st.experimental_rerun()
                        else:
                            st.error("Could not create checkout session. Please try again.")
                    else:
                        st.error("Please login to subscribe.")
        
        # Display annual subscriptions
        st.subheader("Annual Subscriptions (Save up to 17%)")
        cols = st.columns(len(annual_products) if annual_products else 1)
        
        for i, product in enumerate(annual_products):
            with cols[i]:
                st.markdown(f"### {product['name']}")
                st.markdown(f"**${product['unit_amount']:.2f}/{product['interval']}**")
                st.markdown(product['description'])
                st.markdown(f"*Less than ${product['unit_amount']/12:.2f}/month*")
                
                if st.button(f"Select {product['name']} Annual", key=f"annual_{i}"):
                    if 'user' in st.session_state:
                        user = st.session_state.user
                        checkout_url = create_checkout_session(
                            product['price_id'], 
                            user.id, 
                            user.email
                        )
                        if checkout_url:
                            st.session_state.checkout_url = checkout_url
                            st.experimental_rerun()
                        else:
                            st.error("Could not create checkout session. Please try again.")
                    else:
                        st.error("Please login to subscribe.")
                        
    except Exception as e:
        st.error(f"Error retrieving subscription information: {str(e)}")
        if not stripe.api_key:
            st.warning("Stripe API key is not configured. Please set the STRIPE_SECRET_KEY environment variable.")
    
    # If a checkout URL was created, redirect to it
    if 'checkout_url' in st.session_state and st.session_state.checkout_url:
        checkout_url = st.session_state.checkout_url
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{checkout_url}\'">', unsafe_allow_html=True)
        st.write("Redirecting to payment page...")
        st.session_state.checkout_url = None  # Clear the URL after redirecting
    # Return the active subscription tier
    return user.subscription_tier
    st.metric(
        label="IRR (p.a.)", 
        value=f"{irr_pct:.2f}%",
        delta=f"ROE: {roe_pct:.1f}%",
        delta_color="normal",
        help="Internal Rate of Return (annualized) and Return on Equity"
    )
