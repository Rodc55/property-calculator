import streamlit as st
import hmac
import sqlite3
import uuid
import datetime
from dataclasses import dataclass
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email functions
def send_welcome_email(user_email, user_name, password):
    """Send welcome email to new users with their login details using SendGrid"""
    try:
        # Try to import environment variables for SendGrid (for Streamlit Cloud)
        import os
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        sender_email = os.environ.get('EMAIL_SENDER', 'rodc31@gmaill.com')
        
        # Email body
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to Property Feasibility Calculator!</h2>
            <p>Dear {user_name},</p>
            <p>Thank you for registering with Property Feasibility Calculator. Your account has been successfully created.</p>
            <p><strong>Your login details:</strong></p>
            <ul>
                <li>Email: {user_email}</li>
                <li>Password: {password}</li>
            </ul>
            <p>You can log in at any time using these credentials. We recommend changing your password after your first login.</p>
            <p>If you have any questions or need assistance, please don't hesitate to contact our support team by clicking the "Contact Support" button in the application.</p>
            <p>Best regards,<br>
            Property Feasibility Calculator Team</p>
        </body>
        </html>
        """
        
        # Store in session state for demo purposes
        st.session_state.email_would_be_sent = {
            "to": user_email,
            "subject": "Welcome to Property Feasibility Calculator!",
            "body": html_content
        }
        
        # If we have SendGrid API key, send the email for real
        if sendgrid_api_key:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email=sender_email,
                to_emails=user_email,
                subject='Welcome to Property Feasibility Calculator!',
                html_content=html_content)
            
            sg = SendGridAPIClient(sendgrid_api_key)
            response = sg.send(message)
            
            if response.status_code >= 200 and response.status_code < 300:
                return True
            else:
                print(f"SendGrid error status code: {response.status_code}")
                return False
        else:
            # Demo mode - just pretend we sent it
            print("SendGrid API key not found. Email would be sent in production.")
            return True
    
    except Exception as e:
        print(f"Email error: {e}")
        return False

# Database setup and management
def init_auth_db():
    """Initialize the authentication database"""
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    
    # Check if pdf_exports_count column exists
    try:
        c.execute("SELECT pdf_exports_count FROM users LIMIT 1")
    except sqlite3.OperationalError:
        # Add the new columns if they don't exist
        c.execute("ALTER TABLE users ADD COLUMN pdf_exports_count INTEGER DEFAULT 0")
        c.execute("ALTER TABLE users ADD COLUMN pdf_exports_reset_date DATE")
        conn.commit()
    
    # Create users table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        subscription_tier TEXT DEFAULT 'free',
        subscription_start DATE,
        subscription_end DATE,
        pdf_exports_count INTEGER DEFAULT 0,
        pdf_exports_reset_date DATE
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
    pdf_exports_count: int = 0
    pdf_exports_reset_date: str = None

def get_user_by_email(email):
    """Get user details from email"""
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    c.execute('SELECT id, email, name, subscription_tier, subscription_start, subscription_end, pdf_exports_count, pdf_exports_reset_date FROM users WHERE email = ?', (email,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        return User(
            id=user_data[0],
            email=user_data[1],
            name=user_data[2],
            subscription_tier=user_data[3],
            subscription_start=user_data[4],
            subscription_end=user_data[5],
            pdf_exports_count=user_data[6] if user_data[6] is not None else 0,
            pdf_exports_reset_date=user_data[7]
        )
    return None

def create_user(email, name, password, admin=False):
    """Create a new user"""
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    try:
        if admin:
            # Create admin user with enterprise subscription and extended duration
            today = datetime.date.today()
            end_date = today + datetime.timedelta(days=365)  # 1 year subscription
            c.execute('''INSERT INTO users 
                      (email, name, password, subscription_tier, subscription_start, subscription_end) 
                      VALUES (?, ?, ?, ?, ?, ?)''',
                     (email, name, password, 'enterprise', today.isoformat(), end_date.isoformat()))
        else:
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
    SELECT u.id, u.email, u.name, u.subscription_tier, u.subscription_start, u.subscription_end, 
           u.pdf_exports_count, u.pdf_exports_reset_date
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
            subscription_end=user_data[5],
            pdf_exports_count=user_data[6] if user_data[6] is not None else 0,
            pdf_exports_reset_date=user_data[7]
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

def reset_pdf_export_count_if_needed(user_id):
    """Reset PDF export count if it's a new month"""
    today = datetime.date.today()
    first_of_month = today.replace(day=1)
    
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    
    # Get current reset date
    c.execute('SELECT pdf_exports_reset_date FROM users WHERE id = ?', (user_id,))
    reset_date = c.fetchone()[0]
    
    # If reset date is None or it's from a previous month, reset the count
    if not reset_date or datetime.datetime.strptime(reset_date, '%Y-%m-%d').date() < first_of_month:
        c.execute('''
        UPDATE users 
        SET pdf_exports_count = 0, pdf_exports_reset_date = ?
        WHERE id = ?
        ''', (first_of_month.isoformat(), user_id))
        conn.commit()
        
    conn.close()

def increment_pdf_export_count(user_id):
    """Increment the PDF export count for a user"""
    # First check if we need to reset the count for a new month
    reset_pdf_export_count_if_needed(user_id)
    
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    
    # Increment the count
    c.execute('''
    UPDATE users 
    SET pdf_exports_count = pdf_exports_count + 1
    WHERE id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    
def check_pdf_export_limit(user):
    """Check if user has reached their PDF export limit
    Returns: (can_export, exports_used, exports_limit)
    """
    # Pro users have unlimited exports
    if user.subscription_tier == 'pro' or user.subscription_tier == 'enterprise':
        return True, user.pdf_exports_count, "Unlimited"
    
    # Basic users have 10 exports per month
    PDF_LIMIT_BASIC = 10
    
    # Reset count if needed (new month)
    if user.id:
        reset_pdf_export_count_if_needed(user.id)
        
    # Get fresh user data with current count
    conn = sqlite3.connect('property_calculator_auth.db')
    c = conn.cursor()
    c.execute('SELECT pdf_exports_count FROM users WHERE id = ?', (user.id,))
    current_count = c.fetchone()[0]
    conn.close()
    
    # Check if user is within their limit
    can_export = current_count < PDF_LIMIT_BASIC
    
    return can_export, current_count, PDF_LIMIT_BASIC

# Authentication UI components
def login_form():
    """Display login form"""
    st.subheader("Login")
    
    # Check for saved email in session state
    saved_email = ""
    if "saved_email" in st.session_state:
        saved_email = st.session_state.saved_email
    
    with st.form("login_form"):
        email = st.text_input("Email", value=saved_email)
        password = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember me on this device", value=True)
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if verify_password(email, password):
                user = get_user_by_email(email)
                # Create a longer session if "remember me" is checked
                expiry_days = 90 if remember_me else 1
                session_id = create_session(user.id, expiry_days=expiry_days)
                st.session_state.session_id = session_id
                st.session_state.user = user
                
                # Save email for next login if remember me is checked
                if remember_me:
                    st.session_state.saved_email = email
                
                st.success(f"Welcome back, {user.name}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid email or password")
                
    # Add forgot password link
    st.markdown("<div style='text-align: center'><a href='#' style='color:#0068c9;text-decoration:none;font-size:0.8em;'>Forgot password?</a></div>", unsafe_allow_html=True)

def register_form():
    """Display registration form"""
    st.subheader("Register")
    
    # Special admin code field (hidden unless toggled)
    show_admin_field = st.checkbox("I have a special access code", value=False)
    
    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        # Special admin code field
        admin_code = ""
        if show_admin_field:
            admin_code = st.text_input("Special Access Code", type="password")
        
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if password != confirm_password:
                st.error("Passwords do not match")
            elif not email or not password or not name:
                st.error("All fields are required")
            else:
                # Check if this is an admin or tester registration
                is_admin = False
                if show_admin_field and admin_code == "PropertyPro2025":  # Special code for admin/testers
                    is_admin = True
                
                user_id = create_user(email, name, password, admin=is_admin)
                if user_id:
                    # Send welcome email with login details
                    email_sent = send_welcome_email(email, name, password)
                    
                    if is_admin:
                        st.success("Special access granted! All features unlocked. Please login.")
                    else:
                        if email_sent:
                            st.success("Registration successful! Login details have been sent to your email.")
                        else:
                            st.success("Registration successful! Please login.")
                    
                    time.sleep(1)
                    st.session_state.show_register = False
                    st.rerun()
                else:
                    st.error("Email already registered")

def subscription_page():
    """Display subscription options"""
    st.title("Upgrade Your Account")
    
    # Back button at the top
    if st.button("← Back to Calculator"):
        st.session_state.show_subscription = False
        st.rerun()
    
    # If the user already has an active subscription, show their current plan
    if "user" in st.session_state and st.session_state.user:
        user = st.session_state.user
        subscription_active = check_subscription_active(user)
        
        if subscription_active:
            tier_colors = {
                "basic": "#4CAF50",  # Green
                "pro": "#2196F3",    # Blue
                "enterprise": "#9C27B0"  # Purple
            }
            tier_color = tier_colors.get(user.subscription_tier, "#4CAF50")
            
            st.markdown(f"""
            <div style="background-color:#f0f2f6; padding:15px; border-radius:5px; margin-bottom:20px;">
                <h3 style="margin-top:0;">Your Current Plan</h3>
                <div style="background-color:{tier_color}; padding:10px; border-radius:5px; color:white; display:inline-block; margin-bottom:10px;">
                    <strong>{user.subscription_tier.title()} Plan</strong>
                </div>
                <p>Expires: {user.subscription_end}</p>
                <p>You can upgrade or extend your current plan below.</p>
            </div>
            """, unsafe_allow_html=True)
            
    st.write("Choose a subscription plan to unlock all features:")
    
    # Simplified to just two plans: Basic and Pro
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Basic")
        st.write("$9.99/month")
        st.write("• Basic calculations")
        st.write("• 10 PDF exports per month")
        st.write("• Standard support")
        # Add unique key to button
        if st.button("Select Basic", key="basic_monthly"):
            handle_payment("basic", 9.99, 1)
    
    with col2:
        st.subheader("Pro")
        st.write("$19.99/month")
        st.write("• All Basic features")
        st.write("• Advanced visualizations")
        st.write("• Export unlimited reports")
        st.write("• Priority support")
        # Add unique key to button
        if st.button("Select Pro", key="pro_monthly"):
            handle_payment("pro", 19.99, 1)
    
    st.markdown("---")
    
    # Annual options with discount - also simplified
    st.subheader("Save with annual billing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Basic Annual")
        st.write("$99.99/year (Save 17%)")
        # Add unique key to button
        if st.button("Select Basic Annual", key="basic_annual"):
            handle_payment("basic", 99.99, 12)
    
    with col2:
        st.write("Pro Annual")
        st.write("$199.99/year (Save 17%)")
        # Add unique key to button
        if st.button("Select Pro Annual", key="pro_annual"):
            handle_payment("pro", 199.99, 12)
            
    # Back button at the bottom too
    st.markdown("---")
    if st.button("← Return to Calculator", key="bottom_back"):
        st.session_state.show_subscription = False
        st.rerun()

def handle_payment(tier, amount, months):
    """Handle payment processing"""
    st.session_state.payment_tier = tier
    st.session_state.payment_amount = amount
    st.session_state.payment_months = months
    st.session_state.show_payment = True
    st.session_state.show_subscription = False
    st.rerun()
    
def payment_form():
    """Display payment form"""
    st.title("Complete Your Purchase")
    
    # Add back button at the top
    if st.button("← Back to Plans"):
        st.session_state.show_payment = False
        st.session_state.show_subscription = True
        st.rerun()
    
    tier = st.session_state.payment_tier
    amount = st.session_state.payment_amount
    months = st.session_state.payment_months
    
    # Show plan details
    st.subheader("Plan Details")
    plan_col1, plan_col2 = st.columns(2)
    with plan_col1:
        st.markdown(f"**Selected plan:** {tier.title()}")
        if months == 1:
            st.markdown(f"**Billing cycle:** Monthly")
        else:
            st.markdown(f"**Billing cycle:** Annual")
            
        features = {
            "basic": ["Basic calculations", "PDF export"],
            "pro": ["All Basic features", "Advanced visualizations", "Unlimited reports", "Priority email support"]
        }
        
        st.markdown("**Features included:**")
        for feature in features.get(tier, []):
            st.markdown(f"• {feature}")
            
    with plan_col2:
        # Create a card-like interface for the price
        st.markdown("""
        <div style="background-color:#f0f2f6;padding:20px;border-radius:10px;margin-bottom:20px;">
            <h3 style="margin:0;color:#0068c9;">Payment Summary</h3>
            <div style="margin:15px 0;border-bottom:1px solid #ddd;"></div>
        """, unsafe_allow_html=True)
        
        if months == 1:
            st.markdown(f"<p><strong>Monthly price:</strong> ${amount:.2f}</p>", unsafe_allow_html=True)
            st.markdown(f"<p><strong>Today's total:</strong> ${amount:.2f}</p>", unsafe_allow_html=True)
        else:
            monthly_equivalent = amount / 12
            st.markdown(f"<p><strong>Annual price:</strong> ${amount:.2f} (${monthly_equivalent:.2f}/mo)</p>", unsafe_allow_html=True)
            st.markdown(f"<p><strong>Today's total:</strong> ${amount:.2f}</p>", unsafe_allow_html=True)
            st.markdown("<p><em>Save with annual billing!</em></p>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Add payment options
    payment_method = st.radio("Payment Method", ["Credit Card", "PayPal"], horizontal=True)
    
    # Check if payment was successful to show completion message
    payment_success = False
    
    if payment_method == "Credit Card":
        with st.form("payment_form"):
            st.text_input("Cardholder Name", placeholder="John Smith", value="Test User")
            st.text_input("Card Number", placeholder="4242 4242 4242 4242", value="4242 4242 4242 4242")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.text_input("Expiry Month", placeholder="MM", max_chars=2, value="12")
            with col2:
                st.text_input("Expiry Year", placeholder="YY", max_chars=2, value="25")
            with col3:
                st.text_input("CVV", placeholder="123", max_chars=3, value="123")
                
            st.markdown("<small>Your card information is securely processed. We don't store your full card details.</small>", unsafe_allow_html=True)
            
            # Terms checkbox
            agree = st.checkbox("I agree to the terms and conditions", value=True)
            
            submitted = st.form_submit_button("Complete Payment")
            
            if submitted:
                if not agree:
                    st.error("Please agree to the terms and conditions to proceed.")
                else:
                    # In a real app, you would process the payment here using Stripe or another payment processor
                    # For this demo, we'll just update the subscription
                    if st.session_state.user:
                        # Show processing message
                        with st.spinner("Processing payment..."):
                            # Simulate payment processing delay
                            time.sleep(2)
                            update_subscription(st.session_state.user.id, tier, months)
                            user = get_user_by_email(st.session_state.user.email)
                            st.session_state.user = user
                            st.session_state.payment_success = True
                        
                        # Show success message with confetti
                        st.balloons()
                        st.success("Payment successful! Your subscription has been updated.")
                        st.markdown(f"Your {tier.title()} plan is now active. Enjoy all the features!")
                        payment_success = True
    else:
        # PayPal option with form
        with st.form("paypal_form"):
            st.info("You'll be redirected to PayPal to complete your payment.")
            paypal_submitted = st.form_submit_button("Continue to PayPal")
            
            if paypal_submitted:
                # In a real app, you would redirect to PayPal here
                # For this demo, we'll just update the subscription
                if st.session_state.user:
                    with st.spinner("Connecting to PayPal..."):
                        time.sleep(2)
                        update_subscription(st.session_state.user.id, tier, months)
                        user = get_user_by_email(st.session_state.user.email)
                        st.session_state.user = user
                        st.session_state.payment_success = True
                    
                    st.balloons()
                    st.success("PayPal payment successful! Your subscription has been updated.")
                    payment_success = True
                    
    # Return to calculator button outside of both forms
    st.markdown("---")
    
    # Only show this if payment not completed yet
    if not payment_success and not st.session_state.get("payment_success"):
        st.write("Need more time? You can return to the calculator and upgrade later.")
        if st.button("Cancel and Return to Calculator"):
            st.session_state.show_payment = False
            st.rerun()
    # If payment completed successfully, show button to return
    elif payment_success or st.session_state.get("payment_success"):
        if st.button("Continue to Calculator"):
            if "payment_success" in st.session_state:
                del st.session_state.payment_success
            st.session_state.show_payment = False
            st.rerun()

def contact_support_form():
    """Display contact support form"""
    st.title("Contact Support")
    
    # Add back button
    if st.button("← Back to Calculator"):
        st.session_state.show_contact_form = False
        st.rerun()
    
    st.write("Please fill out the form below to contact our support team. We'll get back to you as soon as possible.")
    
    # Check if message was sent successfully
    message_sent = False
    
    with st.form("contact_form"):
        # Get user info if available
        email = ""
        name = ""
        if "user" in st.session_state:
            email = st.session_state.user.email
            name = st.session_state.user.name
            
        # Contact form fields
        name = st.text_input("Your Name", value=name)
        email = st.text_input("Your Email", value=email)
        subject = st.selectbox("Subject", 
            ["General Question", "Technical Support", "Billing Issue", "Feature Request", "Bug Report", "Other"])
        message = st.text_area("Your Message", height=150)
        
        # Submit button
        submitted = st.form_submit_button("Send Message")
        
        if submitted:
            if not name or not email or not message:
                st.error("Please fill out all required fields.")
            else:
                # Store the message details in session state
                st.session_state.support_message_sent = {
                    "name": name,
                    "email": email,
                    "subject": subject,
                    "message": message,
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Try to send the support email using SendGrid
                try:
                    import os
                    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
                    receiver_email = os.environ.get('EMAIL_SENDER', 'rodc31@gmaill.com')
                    
                    if sendgrid_api_key:
                        from sendgrid import SendGridAPIClient
                        from sendgrid.helpers.mail import Mail
                        
                        # Create formatted HTML email content
                        html_content = f"""
                        <html>
                        <body>
                            <h2>Support Request from Property Calculator</h2>
                            <p><strong>From:</strong> {name} ({email})</p>
                            <p><strong>Subject:</strong> {subject}</p>
                            <p><strong>Date:</strong> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                            <hr>
                            <h3>Message:</h3>
                            <p>{message}</p>
                        </body>
                        </html>
                        """
                        
                        email_message = Mail(
                            from_email=email,
                            to_emails=receiver_email,
                            subject=f'Support Request: {subject}',
                            html_content=html_content)
                        
                        sg = SendGridAPIClient(sendgrid_api_key)
                        response = sg.send(email_message)
                        
                        if response.status_code < 200 or response.status_code >= 300:
                            print(f"Support email could not be sent. Status code: {response.status_code}")
                    else:
                        print("SendGrid API key not found. Support email would be sent in production.")
                        
                except Exception as e:
                    print(f"Support email error: {e}")
                
                # Show success message
                st.success("Your message has been sent! Our support team will contact you shortly.")
                st.balloons()
                message_sent = True
    
    # Add return button outside the form
    if message_sent or "support_message_sent" in st.session_state:
        if st.button("Return to Calculator", key="contact_return"):
            st.session_state.show_contact_form = False
            st.rerun()

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
        
    # Initialize state for contact form
    if "show_contact_form" not in st.session_state:
        st.session_state.show_contact_form = False
    
    # We'll handle payment form in main.py instead
    if st.session_state.show_payment:
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
                st.rerun()
    
    with auth_col2:
        if st.session_state.show_register:
            register_form()
            if st.button("Already have an account? Login here"):
                st.session_state.show_register = False
                st.rerun()
    
    # Allow limited trial
    if st.button("Try limited version"):
        # Create a temporary session without login
        st.session_state.trial_mode = True
        st.rerun()
        
    return False

def logout():
    """Log out the current user"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def user_info_section():
    """Display user info and subscription status"""
    if "user" in st.session_state:
        user = st.session_state.user
        
        # Subscription status
        subscription_active = check_subscription_active(user)
        
        # Display user info in sidebar
        with st.sidebar:
            st.write(f"Logged in as: {user.name}")
            
            # Check if this is an admin account (special access code users)
            is_admin_account = user.subscription_tier == 'enterprise' and subscription_active and user.subscription_end and (
                datetime.datetime.strptime(user.subscription_end, '%Y-%m-%d').date() - datetime.date.today()).days >= 300
            
            # Show subscription status with more detail
            if subscription_active:
                tier_colors = {
                    "basic": "#4CAF50",  # Green
                    "pro": "#2196F3",    # Blue
                    "enterprise": "#9C27B0"  # Purple
                }
                tier_color = tier_colors.get(user.subscription_tier, "#4CAF50")
                
                st.markdown(f"""
                <div style="background-color:{tier_color}; padding:10px; border-radius:5px; color:white;">
                    <strong>Active {user.subscription_tier.title()} Plan</strong>
                </div>
                """, unsafe_allow_html=True)
                
                if user.subscription_end:
                    days_left = (datetime.datetime.strptime(user.subscription_end, '%Y-%m-%d').date() - datetime.date.today()).days
                    st.write(f"Expires: {user.subscription_end} ({days_left} days left)")
            elif user.subscription_tier != 'free':
                st.error(f"Subscription: {user.subscription_tier.title()} (Expired)")
                st.write("Your subscription has expired.")
            else:
                st.warning("Free tier (Limited features)")
                
            # Add both upgrade account and contact support buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Upgrade Account"):
                    st.session_state.show_subscription = True
            with col2:
                if st.button("Contact Support"):
                    # Show contact form
                    st.session_state.show_contact_form = True
            
            # Admin testing menu - only for admin accounts
            if is_admin_account:
                st.markdown("---")
                st.write("Admin Testing Menu:")
                if st.button("View Basic Features"):
                    st.session_state.temp_access_level = "basic"
                if st.button("View Pro Features"):
                    st.session_state.temp_access_level = "pro"  
                if st.button("View Enterprise Features"):
                    st.session_state.temp_access_level = "enterprise"
                if st.button("Reset Feature View", key="reset_features"):
                    if "temp_access_level" in st.session_state:
                        del st.session_state.temp_access_level
            
            if st.button("Logout"):
                logout()
                
def check_access_level():
    """Check user's access level for features"""
    # For admin testing - let the admin pick any access level to test
    if "temp_access_level" in st.session_state:
        return st.session_state.temp_access_level
        
    # Trial mode has very limited access
    if "trial_mode" in st.session_state and st.session_state.trial_mode:
        return "trial"
        
    # Check if user is logged in
    if "user" not in st.session_state:
        return "none"
        
    user = st.session_state.user
    subscription_active = check_subscription_active(user)
    
    # Free tier has basic access
    if user.subscription_tier == 'free' or not subscription_active:
        return "free"
        
    # Return the active subscription tier
    return user.subscription_tier
