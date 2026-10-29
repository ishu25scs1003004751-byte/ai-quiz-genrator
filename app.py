# i18n.py

ADMIN_HELP = "🛠️ Admin: Shared PYQ bank me sawal upload kar sakte hain."
EMAIL_SVC_MSG = "Email OTP service configured."
SVC_MSG = "Service status operational."

LANG_ORDER = ["Hinglish", "English", "Hindi"]
QUIZ_LANG_OF = {"Hinglish": "Hinglish", "English": "English", "Hindi": "Hindi"}

LANGS = {
    "English": {
        "hero_sub": "Provide a Topic, PDF, or photo of notes — AI generates quizzes instantly.",
        "generate_btn": "✨ Generate Quiz",
    },
    "Hinglish": {
        "hero_sub": "Topic, PDF ya notes ki photo do — AI turant quiz banata hai.",
        "generate_btn": "✨ Quiz banao",
    },
    "Hindi": {
        "hero_sub": "विषय, पीडीएफ या नोट्स की फोटो दें — एआई तुरंत क्विज़ बनाता है।",
        "generate_btn": "✨ क्विज़ बनाएं",
    }
}

def tr(key, lang="Hinglish"):
    return LANGS.get(lang, LANGS["Hinglish"]).get(key, key)

def init_ui_lang():
    pass

def set_ui_lang(lang):
    pass

def all_forms():
    return []
