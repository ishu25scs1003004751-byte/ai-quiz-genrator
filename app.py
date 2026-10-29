import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

# -----------------------------------------------------------------------------
# 1. LANGUAGE TRANSLATIONS DICTIONARY
# -----------------------------------------------------------------------------
TRANSLATIONS = {
    "Hindi": {
        "page_title": "ओटीपी प्रमाणीकरण प्रणाली",
        "sidebar_lang": "भाषा चुनें / Select Language",
        "app_header": "एप्लिकेशन लॉगिन एवं ओटीपी सेवा",
        "otp_error_title": "⚠️ OTP service abhi set up nahi hai.",
        "otp_error_msg": "App admin ko Secrets (secrets.toml) mein SMTP / SMS settings add karni hogi.",
        "admin_guide_title": "🛠️ Admin Settings / Setup Guide",
        "admin_guide_text": "OTP Email feature chalu karne ke liye `.streamlit/secrets.toml` file mein ye details add karein:",
        "email_label": "अपना ईमेल पता दर्ज करें (Enter Email):",
        "send_otp_btn": "ओटीपी भेजें (Send OTP)",
        "otp_sent_success": "OTP safaltapurvak {email} par bhej diya gaya hai!",
        "demo_otp_msg": "Demo Mode: Aapka OTP hai: ",
        "otp_input_label": "प्राप्त हुआ OTP दर्ज करें (Enter OTP):",
        "verify_btn": "सत्यापित करें (Verify OTP)",
        "auth_success": "🎉 Pramaanikaran safal hua! App mein aapka swagat hai.",
        "auth_failed": "❌ Galat OTP. Kripya dobara koshish karein.",
        "enter_email_warning": "Kripya ek valid email address darj karein."
    },
    "English": {
        "page_title": "OTP Authentication System",
        "sidebar_lang": "Select Language / भाषा चुनें",
        "app_header": "Application Login & OTP Service",
        "otp_error_title": "⚠️ OTP service isn't set up yet.",
        "otp_error_msg": "The app admin must add SMTP / SMS settings in Secrets.",
        "admin_guide_title": "🛠️ Admin Settings / Setup Guide",
        "admin_guide_text": "To enable OTP Emails, add the following configuration to `.streamlit/secrets.toml`:",
        "email_label": "Enter your Email Address:",
        "send_otp_btn": "Send OTP",
        "otp_sent_success": "OTP sent successfully to {email}!",
        "demo_otp_msg": "Demo Mode Active: Your OTP is: ",
        "otp_input_label": "Enter Received OTP:",
        "verify_btn": "Verify OTP",
        "auth_success": "🎉 Authentication successful! Welcome to the application.",
        "auth_failed": "❌ Invalid OTP. Please try again.",
        "enter_email_warning": "Please enter a valid email address."
    }
}

# -----------------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def check_otp_service_status():
    """Checks whether SMTP settings exist in st.secrets."""
    if "smtp" in st.secrets:
        smtp_conf = st.secrets["smtp"]
        if smtp_conf.get("enabled", False) and smtp_conf.get("email") and smtp_conf.get("password"):
            return True
    return False

def send_smtp_email(to_email, otp_code):
    """Sends OTP via email if secrets are configured."""
    try:
        smtp_conf = st.secrets["smtp"]
        msg = MIMEMultipart()
        msg['From'] = smtp_conf["email"]
        msg['To'] = to_email
        msg['Subject'] = "OTP Verification Code"
        
        body = f"Your OTP for login is: {otp_code}"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_conf.get("server", "smtp.gmail.com"), smtp_conf.get("port", 587))
        server.starttls()
        server.login(smtp_conf["email"], smtp_conf["password"])
        server.send_message(msg)
        server.quit()
        return True, None
    except Exception as e:
        return False, str(e)

# -----------------------------------------------------------------------------
# 3. STREAMLIT APP & LANGUAGE SETTING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="OTP System", page_icon="🔐", layout="centered")

# Language Selection in Sidebar
if "lang" not in st.session_state:
    st.session_state.lang = "Hindi"

selected_lang = st.sidebar.selectbox(
    "🌐 Language Settings",
    options=["Hindi", "English"],
    index=0 if st.session_state.lang == "Hindi" else 1
)
st.session_state.lang = selected_lang

# Load translations for the active language
t = TRANSLATIONS[st.session_state.lang]

# Main UI
st.title(t["app_header"])

# Check OTP Setup
is_configured = check_otp_service_status()

if not is_configured:
    # Error Message when OTP service is not set up
    st.error(f"**{t['otp_error_title']}**")
    st.info(t["otp_error_msg"])
    
    # Admin Guide Section
    with st.expander(t["admin_guide_title"]):
        st.write(t["admin_guide_text"])
        st.code("""
[smtp]
enabled = true
server = "smtp.gmail.com"
port = 587
email = "your-email@gmail.com"
password = "your-app-password"
""", language="toml")

st.divider()

# -----------------------------------------------------------------------------
# 4. OTP GENERATION & VERIFICATION FORM
# -----------------------------------------------------------------------------
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False

user_email = st.text_input(t["email_label"])

if st.button(t["send_otp_btn"]):
    if user_email:
        otp = str(random.randint(100000, 999999))
        st.session_state.generated_otp = otp
        
        if is_configured:
            success, err = send_smtp_email(user_email, otp)
            if success:
                st.success(t["otp_sent_success"].format(email=user_email))
                st.session_state.otp_sent = True
            else:
                st.error(f"Email Error: {err}")
        else:
            # Fallback Demo Mode if OTP settings aren't added yet
            st.warning(f"{t['demo_otp_msg']} **{otp}**")
            st.session_state.otp_sent = True
    else:
        st.warning(t["enter_email_warning"])

# Verify OTP Section
if st.session_state.otp_sent:
    user_otp = st.text_input(t["otp_input_label"])
    if st.button(t["verify_btn"]):
        if user_otp == st.session_state.generated_otp:
            st.balloons()
            st.success(t["auth_success"])
        else:
            st.error(t["auth_failed"])
