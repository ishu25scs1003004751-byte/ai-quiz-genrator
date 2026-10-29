# i18n.py

TRANSLATIONS = {
    "English": {
        "app_title": "App Portal",
        "nav_home": "Home",
        "nav_login": "Login",
        "nav_settings": "Settings",
        "lang_selector_label": "Select Language / भाषा चुनें",
        
        # OTP / Auth Messages
        "otp_error_title": "⚠️ OTP Service Not Configured",
        "otp_error_msg": "OTP service isn't set up yet. The app admin must add SMTP / SMS settings in Secrets.",
        "admin_guide_title": "🛠️ Admin Configuration Guide",
        "admin_guide_text": "To enable OTP service, add the following parameters in `.streamlit/secrets.toml`:",
        "email_placeholder": "Enter your email address",
        "send_otp_btn": "Send OTP",
        "enter_otp_placeholder": "Enter Received OTP",
        "verify_otp_btn": "Verify OTP",
        "auth_success": "🎉 Authentication successful!",
        "auth_failed": "❌ Invalid OTP. Please try again.",
        "demo_mode_alert": "Demo Mode Active. Your OTP is: ",
    },
    "Hindi": {
        "app_title": "ऐप पोर्टल",
        "nav_home": "होम",
        "nav_login": "लॉगिन",
        "nav_settings": "सेटिंग्स",
        "lang_selector_label": "भाषा चुनें / Select Language",
        
        # OTP / Auth Messages
        "otp_error_title": "⚠️ ओटीपी सेवा सेट अप नहीं है",
        "otp_error_msg": "OTP service abhi set up nahi hai. App admin ko Secrets mein SMTP / SMS settings jodni hogi.",
        "admin_guide_title": "🛠️ एडमिन कॉन्फ़िगरेशन गाइड",
        "admin_guide_text": "OTP service chalu karne ke liye `.streamlit/secrets.toml` mein ye details add karein:",
        "email_placeholder": "अपना ईमेल पता दर्ज करें",
        "send_otp_btn": "ओटीपी भेजें",
        "enter_otp_placeholder": "प्राप्त ओटीपी दर्ज करें",
        "verify_otp_btn": "ओटीपी सत्यापित करें",
        "auth_success": "🎉 प्रमाणन सफल रहा!",
        "auth_failed": "❌ अमान्य ओटीपी। कृपया पुनः प्रयास करें।",
        "demo_mode_alert": "डेमो मोड सक्रिय है। आपका OTP है: ",
    }
}

def get_text(lang: str, key: str) -> str:
    """Helper function to fetch text according to current language."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["Hindi"]).get(key, key)
