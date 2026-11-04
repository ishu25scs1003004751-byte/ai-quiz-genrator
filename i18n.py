"""
i18n.py — translation system for AI Quiz Arena (English 🇬🇧 + हिंदी 🇮🇳).

How it works
────────────
* ONE catalog (`_S`): every UI string lives here once as  key -> (English, हिंदी).
  Because both languages sit side by side, a string can never exist in only one of them.
* `tr("key", n=3)` returns the string in the active language (English is the default).
* `fmt("prefix")` builds a `format_func` for widgets whose option VALUES must stay language-independent
  (e.g. mode "Survival", difficulty "Hard") while the LABEL shown to the user is translated.
* The active language lives in `st.session_state["ui_lang"]`; switching it re-runs the script, so the whole
  app changes instantly — no page refresh.
* Persistence: the choice is saved in the browser's localStorage (`qa_lang`) and restored on the next visit
  by a tiny JS bridge (see `bridge_js`). First-time visitors get English.
* `render_switcher(slot)` draws the responsive pill switcher (login page, top bar and sidebar).
"""
import json
import re
import time

import streamlit as st

# ─────────────────────────────────────────────────────────────
# LANGUAGES
# ─────────────────────────────────────────────────────────────
LANGS = {
    "en": {"label": "🇬🇧 English", "html": "en", "tts": "en-IN", "ai": "English", "quiz": "English", "doubt": "Simple English"},
    "hi": {"label": "🇮🇳 हिंदी", "html": "hi", "tts": "hi-IN", "ai": "Hindi", "quiz": "Hindi", "doubt": "Hindi"},
}
LANG_ORDER = ["en", "hi"]
DEFAULT = "en"
STORAGE_KEY = "qa_lang"
SLOTS = ("login", "top", "side")  # places where a switcher can be drawn
_LABEL2CODE = {v["label"]: k for k, v in LANGS.items()}

# Words the keyboard-shortcut script looks for on buttons (both languages, so shortcuts work in either).
SHORTCUTS = {
    "enter": ["Check answer", "Next", "Finish", "View results", "Submit", "उत्तर जाँचें", "अगला", "समाप्त", "परिणाम देखें"],
    "hint": ["Hint", "संकेत"],
    "skip": ["Skip", "छोड़ें"],
}

# Spoken (text-to-speech) helper words — these follow the QUIZ content language, not the UI language.
SPEECH = {
    "English": {"blank": "blank", "option": "Option", "tf": "True or False?"},
    "Hindi": {"blank": "रिक्त स्थान", "option": "विकल्प", "tf": "सही या गलत?"},
    "Hinglish": {"blank": "blank", "option": "Option", "tf": "True ya False?"},
}

HI_MONTHS = {
    "Jan": "जन॰", "Feb": "फ़र॰", "Mar": "मार्च", "Apr": "अप्रैल", "May": "मई", "Jun": "जून",
    "Jul": "जुल॰", "Aug": "अग॰", "Sep": "सित॰", "Oct": "अक्टू॰", "Nov": "नव॰", "Dec": "दिस॰",
}

# ─────────────────────────────────────────────────────────────
# CATALOG   key: (English, हिंदी)
# ─────────────────────────────────────────────────────────────
_S = {
    # ── language switcher ──
    "lang.switch_label": ("Language / भाषा", "Language / भाषा"),
    "lang.app_title": ("### 🌐 App language", "### 🌐 ऐप की भाषा"),
    "lang.quiz": ("Quiz language", "क्विज़ की भाषा"),
    "lang.quiz_help": (
        "Language in which the AI writes the questions, options and explanations.",
        "जिस भाषा में AI प्रश्न, विकल्प और स्पष्टीकरण लिखेगा।",
    ),
    "qlang.English": ("English", "अंग्रेज़ी"),
    "qlang.Hindi": ("Hindi", "हिन्दी"),
    "qlang.Hinglish": ("Hinglish", "हिंग्लिश"),

    # ── common ──
    "common.custom": ("Custom", "कस्टम"),
    "unit.sec": ("s", " सेकंड"),
    "time.fmt": ("{m}m {s:02d}s", "{m} मि {s:02d} से"),

    # ── errors (generic) ──
    "err.no_api_key": (
        "API key not found. Add `GROQ_API_KEY` in your Streamlit Cloud **Secrets**.",
        "API key नहीं मिली। अपने Streamlit Cloud के **Secrets** में `GROQ_API_KEY` जोड़ें।",
    ),
    "err.rate": (
        "Groq rate limit reached. Please wait 20-30 seconds and try again, or choose a smaller model.",
        "Groq की रेट लिमिट लग गई है। 20-30 सेकंड रुककर दोबारा प्रयास करें, या छोटा मॉडल चुनें।",
    ),
    "err.apikey": (
        "The API key looks invalid. Please check `GROQ_API_KEY` in Secrets.",
        "API key गलत लग रही है। Secrets में `GROQ_API_KEY` जाँचें।",
    ),
    "err.model": (
        "This model is not available right now. Choose another model in Sidebar → Advanced.",
        "यह मॉडल अभी उपलब्ध नहीं है। साइडबार → उन्नत में दूसरा मॉडल चुनें।",
    ),
    "err.generic": ("Error: {msg}", "त्रुटि: {msg}"),
    "err.no_supabase": (
        "The `supabase` package is not installed. Add `supabase` and `extra-streamlit-components` to requirements.txt.",
        "`supabase` पैकेज इंस्टॉल नहीं है। requirements.txt में `supabase` और `extra-streamlit-components` जोड़ें।",
    ),
    "err.bad_file": ("The file format is invalid.", "फ़ाइल का फ़ॉर्मेट गलत है।"),
    "err.load_failed": ("Could not load: {e}", "लोड नहीं हो सका: {e}"),
    "err.photo_big": (
        "The photo is larger than 15 MB. Use a smaller photo.",
        "फ़ोटो 15 MB से बड़ी है। छोटी फ़ोटो इस्तेमाल करें।",
    ),
    "err.photo_big2": (
        "Still too big after compression. Use a lower-resolution photo.",
        "कंप्रेस करने के बाद भी बहुत बड़ी है। कम रेज़ोल्यूशन वाली फ़ोटो लें।",
    ),
    "err.no_valid": (
        "Couldn't make valid questions. Please try again.",
        "सही प्रश्न नहीं बन पाए। कृपया दोबारा प्रयास करें।",
    ),
    "err.ai_parse": (
        "Couldn't understand the AI's response. Try again or pick another model.",
        "AI का जवाब समझ नहीं आया। दोबारा प्रयास करें या दूसरा मॉडल चुनें।",
    ),

    # ── login / OTP ──
    "auth.sms": (
        "An SMS provider (like Twilio) must be set up in Supabase for phone OTP. Please log in with email for now.",
        "फ़ोन OTP के लिए Supabase में SMS प्रोवाइडर (जैसे Twilio) सेट होना चाहिए। अभी ईमेल से लॉगिन करें।",
    ),
    "auth.ratelimit": (
        "Too many OTP requests. Please wait a few minutes before trying again.",
        "बहुत जल्दी-जल्दी OTP माँगा गया। कुछ मिनट बाद दोबारा प्रयास करें।",
    ),
    "auth.otp_bad": (
        "The OTP is invalid or has expired. Please request a new OTP.",
        "OTP गलत है या एक्सपायर हो गया है। कृपया नया OTP मँगवाएँ।",
    ),
    "auth.signup_off": (
        "Sign-ups for new users are currently disabled (Supabase setting).",
        "नए यूज़र्स का साइन-अप अभी बंद है (Supabase सेटिंग)।",
    ),
    "login.sub": (
        "Log in — your history, XP and saved questions will always stay safe, and you'll get fresh questions every time.",
        "लॉगिन करें — आपकी हिस्ट्री, XP और सहेजे गए प्रश्न हमेशा सुरक्षित रहेंगे, और हर बार नए प्रश्न मिलेंगे।",
    ),
    "login.how": ("How would you like to log in?", "आप कैसे लॉगिन करना चाहेंगे?"),
    "login.email": ("📧 By email", "📧 ईमेल से"),
    "login.phone": ("📱 By mobile number", "📱 मोबाइल नंबर से"),
    "login.email_label": ("Email address", "ईमेल पता"),
    "login.phone_label": ("Mobile number", "मोबाइल नंबर"),
    "login.phone_ph": ("98765 43210  (or +91…)", "98765 43210  (या +91…)"),
    "login.phone_hint": (
        "For an Indian number, just enter the 10 digits. For other countries, add the +country code.",
        "भारतीय नंबर के लिए सिर्फ़ 10 अंक लिखें। दूसरे देश के लिए +कंट्री कोड जोड़ें।",
    ),
    "login.send": ("📨 Send OTP", "📨 OTP भेजें"),
    "login.bad_email": ("Enter a valid email address.", "सही ईमेल पता लिखें।"),
    "login.bad_phone": ("Enter a valid mobile number.", "सही मोबाइल नंबर लिखें।"),
    "login.sending": ("Sending OTP…", "OTP भेजा जा रहा है…"),
    "login.sent": ("OTP sent to: **{to}**", "OTP यहाँ भेजा गया: **{to}**"),
    "login.enter_otp": ("Enter OTP", "OTP दर्ज करें"),
    "login.verify": ("✅ Verify", "✅ सत्यापित करें"),
    "login.need_otp": ("Please enter the OTP first.", "पहले OTP दर्ज करें।"),
    "login.verifying": ("Verifying…", "सत्यापित किया जा रहा है…"),
    "login.resend": ("🔁 Resend OTP", "🔁 OTP दोबारा भेजें"),
    "login.wait": ("Try again in {n} seconds.", "{n} सेकंड बाद दोबारा प्रयास करें।"),
    "login.resent": ("A new OTP has been sent.", "नया OTP भेज दिया गया है।"),
    "login.back": ("← Change email / number", "← ईमेल / नंबर बदलें"),

    # ── hero & tiles ──
    "hero.step1": ("Choose content", "सामग्री चुनें"),
    "hero.step2": ("Play quiz", "क्विज़ खेलें"),
    "hero.step3": ("See results", "परिणाम देखें"),
    "hero.sub": (
        "Give a topic, a PDF or a photo of your notes — AI makes a quiz instantly. Learn with voice, timer, lives, XP and badges.",
        "कोई विषय, PDF या नोट्स की फ़ोटो दें — AI तुरंत क्विज़ बना देता है। आवाज़, टाइमर, लाइव्स, XP और बैज के साथ सीखें।",
    ),
    "tile.level": ("Level", "लेवल"),
    "tile.xp": ("Total XP", "कुल XP"),
    "tile.played": ("Quizzes played", "खेले गए क्विज़"),
    "tile.best": ("Best score", "सर्वश्रेष्ठ स्कोर"),

    # ── sidebar ──
    "side.level": ("### 🎖️ Level {n}", "### 🎖️ लेवल {n}"),
    "side.xp": ("{xp} XP · {n} to next level", "{xp} XP · अगले लेवल तक {n}"),
    "side.settings": ("### ⚙️ Quiz Settings", "### ⚙️ क्विज़ सेटिंग्स"),
    "side.questions": ("Questions", "प्रश्नों की संख्या"),
    "side.questions_help": (
        "More than 10 questions are made in batches, so it can take a little longer.",
        "10 से ज़्यादा प्रश्न बैच में बनते हैं, इसलिए थोड़ा समय लग सकता है।",
    ),
    "side.difficulty": ("Difficulty", "कठिनाई"),
    "diff.Easy": ("Easy", "आसान"),
    "diff.Medium": ("Medium", "मध्यम"),
    "diff.Hard": ("Hard", "कठिन"),
    "side.adaptive": ("🎚️ Adaptive difficulty", "🎚️ अनुकूली कठिनाई"),
    "side.adaptive_help": (
        "Questions get harder as you answer correctly and easier when you miss.",
        "सही उत्तर देने पर प्रश्न कठिन और गलत होने पर आसान होते जाएँगे।",
    ),
    "side.qtypes": ("Question types", "प्रश्नों के प्रकार"),
    "qtype.long.mcq": ("Multiple Choice", "बहुविकल्पीय (MCQ)"),
    "qtype.long.tf": ("True / False", "सही / गलत"),
    "qtype.long.multi": ("Multi-select", "बहु-चयन"),
    "qtype.long.blank": ("Fill in the blank", "रिक्त स्थान भरें"),
    "qtype.long.short": ("Short answer (AI check)", "संक्षिप्त उत्तर (AI जाँच)"),
    "qtype.long.num": ("Numerical value", "संख्यात्मक मान"),
    "qtype.mcq": ("MCQ", "MCQ"),
    "qtype.tf": ("True/False", "सही/गलत"),
    "qtype.multi": ("Multi-select", "बहु-चयन"),
    "qtype.blank": ("Fill in the blank", "रिक्त स्थान"),
    "qtype.short": ("Short answer", "संक्षिप्त उत्तर"),
    "qtype.num": ("Numerical", "संख्यात्मक"),
    "side.mode": ("Mode", "मोड"),
    "mode.Practice": ("Practice", "अभ्यास"),
    "mode.Exam": ("Exam", "परीक्षा"),
    "mode.Survival": ("Survival", "सर्वाइवल"),
    "side.mode_help": (
        "Practice: instant answer after every question.\nExam: result at the end.\nSurvival: only 3 lives — 3 wrong answers and it's game over!",
        "अभ्यास: हर प्रश्न के बाद तुरंत उत्तर।\nपरीक्षा: परिणाम अंत में।\nसर्वाइवल: सिर्फ़ 3 लाइव्स — 3 गलत उत्तर पर गेम ओवर!",
    ),
    "side.timer": ("**⏱️ Timer**", "**⏱️ टाइमर**"),
    "side.timer_type": ("Timer type", "टाइमर का प्रकार"),
    "timer.off": ("Off", "बंद"),
    "timer.per_q": ("Per question", "हर प्रश्न पर"),
    "timer.whole": ("Whole quiz", "पूरे क्विज़ का"),
    "side.secs": ("Seconds per question", "प्रति प्रश्न सेकंड"),
    "side.secs_custom": ("Custom seconds", "कस्टम सेकंड"),
    "side.secs_help": (
        "The answer is submitted automatically when time runs out.",
        "समय खत्म होते ही उत्तर अपने आप जमा हो जाता है।",
    ),
    "side.mins": ("Minutes (whole quiz)", "मिनट (पूरे क्विज़ के लिए)"),
    "side.mins_custom": ("Custom minutes", "कस्टम मिनट"),
    "side.mins_cap": (
        "≈ {n} sec per question. The quiz is submitted automatically when time runs out.",
        "≈ प्रति प्रश्न {n} सेकंड। समय खत्म होते ही क्विज़ अपने आप जमा हो जाएगा।",
    ),
    "side.timer_need": ("The timer needs Streamlit ≥ 1.37.", "टाइमर के लिए Streamlit ≥ 1.37 चाहिए।"),
    "side.marking": ("**🎯 Marking**", "**🎯 अंकन**"),
    "side.marks_per": ("Marks per correct answer", "प्रति सही उत्तर अंक"),
    "side.neg": ("Negative marking (on wrong)", "नेगेटिव मार्किंग (गलत उत्तर पर)"),
    "neg.none": ("None", "कोई नहीं"),
    "neg.full": ("Full (−1)", "पूरा (−1)"),
    "side.neg_help": (
        "A wrong answer loses this fraction of the marks. Skipped = 0. Short answers get partial marks, never negative.",
        "गलत उत्तर पर सही-उत्तर के अंकों का इतना हिस्सा कटेगा। छोड़ने पर 0। संक्षिप्त उत्तर में आंशिक अंक मिलते हैं, नेगेटिव नहीं।",
    ),
    "side.marks_cap": ("+{c} correct · −{w} wrong · 0 skipped", "+{c} सही · −{w} गलत · 0 छोड़ा"),
    "side.sound_look": ("🔊 Sound & Look", "🔊 आवाज़ और लुक"),
    "side.sound": ("Sound effects", "साउंड इफ़ेक्ट"),
    "side.auto_read": ("Read questions aloud automatically", "प्रश्न अपने आप पढ़कर सुनाएँ"),
    "side.auto_read_help": (
        "If there's no sound, click once on the page or press the 🔊 button.",
        "अगर आवाज़ न आए तो पेज पर एक बार क्लिक करें या 🔊 बटन दबाएँ।",
    ),
    "side.speed": ("Speaking speed", "बोलने की गति"),
    "side.light": ("☀️ Light mode", "☀️ लाइट मोड"),
    "side.advanced": ("Advanced", "उन्नत"),
    "side.model": ("AI model", "AI मॉडल"),
    "side.model_help": ("120b = most accurate. 8b-instant = fastest.", "120b = सबसे सटीक। 8b-instant = सबसे तेज़।"),
    "side.saved": ("### 🔖 Saved questions", "### 🔖 सहेजे गए प्रश्न"),
    "side.saved_n": ("{n} question(s) saved", "{n} प्रश्न सहेजे गए"),
    "side.flash_btn": ("📇 Study with flashcards", "📇 फ़्लैशकार्ड से पढ़ें"),
    "side.saved_hint": (
        "Press 🔖 during a quiz and the question is saved here.",
        "क्विज़ के दौरान 🔖 दबाएँ, प्रश्न यहाँ सहेज लिया जाएगा।",
    ),
    "side.history": ("### 🏆 My History", "### 🏆 मेरी हिस्ट्री"),
    "side.hist_item": ("{marks}/{max} marks · {acc}% acc · {diff}", "{marks}/{max} अंक · {acc}% सटीकता · {diff}"),
    "side.best": ("⭐ Best score: {n}%", "⭐ सर्वश्रेष्ठ स्कोर: {n}%"),
    "side.clear_hist": ("Clear history", "हिस्ट्री साफ़ करें"),
    "side.no_hist": (
        "No quiz taken yet. Make your first one!",
        "अभी तक कोई क्विज़ नहीं दिया। अपना पहला क्विज़ बनाएँ!",
    ),
    "side.account": ("### 👤 Account", "### 👤 अकाउंट"),
    "side.logged_in": ("Logged in", "लॉग इन है"),
    "side.admin": (
        "🛠️ Admin — you can add questions to the PYQ bank",
        "🛠️ एडमिन — आप PYQ बैंक में प्रश्न जोड़ सकते हैं",
    ),
    "side.db_warn": (
        "There was a problem saving to the database. Check the Supabase SQL / keys.",
        "डेटाबेस में सेव करने में समस्या आई। Supabase SQL / keys जाँचें।",
    ),
    "side.logout": ("🚪 Log out", "🚪 लॉग आउट"),
    "side.guest": (
        "Guest mode: login/database is not set up, so your history is lost when the browser is closed.",
        "गेस्ट मोड: लॉगिन/डेटाबेस सेट नहीं है, इसलिए ब्राउज़र बंद होते ही हिस्ट्री चली जाएगी।",
    ),
    "side.backup": ("### 💾 Progress backup", "### 💾 प्रोग्रेस बैकअप"),
    "side.backup_cap": (
        "Save your XP, history and saved questions to a file and load them back any time.",
        "अपना XP, हिस्ट्री और सहेजे गए प्रश्न फ़ाइल में सेव करें और जब चाहें वापस लोड करें।",
    ),
    "side.backup_dl": ("⬇️ Download progress", "⬇️ प्रोग्रेस डाउनलोड करें"),
    "side.backup_up": ("Load progress", "प्रोग्रेस लोड करें"),
    "side.backup_ok": (
        "✅ Restored {h} quiz history entries and {b} saved questions.",
        "✅ {h} क्विज़ हिस्ट्री और {b} सहेजे गए प्रश्न वापस आ गए।",
    ),

    # ── history labels (stored in English, shown translated) ──
    "lbl.pasted": ("Pasted notes", "चिपकाए गए नोट्स"),
    "lbl.pdf": ("PDF: {n}", "PDF: {n}"),
    "lbl.photo": ("Photo: {n}", "फ़ोटो: {n}"),
    "lbl.retry": ("Retry · {n}", "पुनः प्रयास · {n}"),
    "lbl.doubt": ("Doubt: {n}", "डाउट: {n}"),
    "lbl.mock": ("{n} · Mock", "{n} · मॉक"),
    "lbl.pyq": ("{n} · PYQ", "{n} · PYQ"),

    # ── tabs ──
    "tab.quiz": ("🧠 Quiz Arena", "🧠 क्विज़ एरीना"),
    "tab.pyq": ("🏛️ Govt Exam PYQs", "🏛️ सरकारी परीक्षा PYQ"),
    "tab.doubt": ("🔍 Doubt Solver", "🔍 डाउट सॉल्वर"),

    # ── quiz tab ──
    "src.topic": ("💡 Topic", "💡 विषय"),
    "src.pdf": ("📄 PDF", "📄 PDF"),
    "src.photo": ("🖼️ Photo / Camera", "🖼️ फ़ोटो / कैमरा"),
    "src.notes": ("📝 Notes", "📝 नोट्स"),
    "qt.where": ("Where is the content from?", "सामग्री कहाँ से आएगी?"),
    "qt.topic_label": ("Which topic do you want a quiz on?", "किस विषय पर क्विज़ चाहिए?"),
    "qt.topic_ph": (
        "e.g. Machine Learning basics, Indian Constitution, Python lists…",
        "जैसे: मशीन लर्निंग की मूल बातें, भारतीय संविधान, Python lists…",
    ),
    "qt.quick": ("Quick picks", "त्वरित चयन"),
    "pick.1": ("Python Basics", "Python की मूल बातें"),
    "pick.2": ("World History", "विश्व इतिहास"),
    "pick.3": ("Human Biology", "मानव जीव विज्ञान"),
    "pick.4": ("Indian Economy", "भारतीय अर्थव्यवस्था"),
    "qt.selected_topic": ("Selected topic: **{t}**", "चुना गया विषय: **{t}**"),
    "qt.upload_pdf": ("Upload PDF", "PDF अपलोड करें"),
    "qt.page_range": ("Page range", "पेज रेंज"),
    "qt.pdf_ok": ("✅ Read {n} page(s) · {c:,} characters", "✅ {n} पेज पढ़े गए · {c:,} अक्षर"),
    "qt.pdf_long": (
        "The text is long — only the first {m:,} characters will be used. Narrow the page range.",
        "टेक्स्ट बहुत लंबा है — सिर्फ़ पहले {m:,} अक्षर इस्तेमाल होंगे। पेज रेंज छोटी करें।",
    ),
    "qt.pdf_scanned": (
        "No text could be read from this PDF (it looks scanned). Try a **photo** of the page instead.",
        "इस PDF से टेक्स्ट नहीं निकला (शायद यह स्कैन किया हुआ है)। उस पेज की **फ़ोटो** लेकर आज़माएँ।",
    ),
    "qt.pdf_err": ("Could not read the PDF: {e}", "PDF पढ़ा नहीं जा सका: {e}"),
    "qt.photo_cap": (
        "Upload a photo or take one directly with the camera.",
        "फ़ोटो अपलोड करें या कैमरे से सीधे खींचें।",
    ),
    "qt.photo_mode": ("Photo mode", "फ़ोटो मोड"),
    "photo.upload": ("📁 Upload file", "📁 फ़ाइल अपलोड"),
    "photo.camera": ("📸 Live camera", "📸 लाइव कैमरा"),
    "qt.photo_up": ("Upload a photo", "फ़ोटो अपलोड करें"),
    "qt.photo_cam": ("Take a live photo", "लाइव फ़ोटो खींचें"),
    "qt.selected_photo": ("Selected photo", "चुनी गई फ़ोटो"),
    "qt.notes_label": ("Paste your notes / article here", "अपने नोट्स / लेख यहाँ पेस्ट करें"),
    "qt.notes_ph": ("Chapter text, notes or any article…", "अध्याय का टेक्स्ट, नोट्स या कोई भी लेख…"),
    "qt.chars": ("{n:,} characters", "{n:,} अक्षर"),
    "qt.make": ("✨ Create quiz", "✨ क्विज़ बनाएँ"),
    "qt.need_input": (
        "First write a topic, upload/take a photo or paste notes.",
        "पहले विषय लिखें, फ़ोटो अपलोड करें/खींचें या नोट्स पेस्ट करें।",
    ),
    "qt.spinner": ("AI is making questions…", "AI प्रश्न बना रहा है…"),
    "gen.making": ("Making questions…", "प्रश्न बन रहे हैं…"),
    "gen.progress": ("{done} / {total} questions generated…", "{done} / {total} प्रश्न बन गए…"),

    # ── PYQ tab ──
    "pyq.title": ("### 🏛️ Govt & Entrance Exam — PYQ Practice", "### 🏛️ सरकारी एवं प्रवेश परीक्षा — PYQ अभ्यास"),
    "pyq.intro": (
        "Here you get **real questions from previous years (PYQs)** from the PYQ bank (marked with a 📜 tag). "
        "PYQs you've already done won't repeat. Marking follows each exam's rules.",
        "यहाँ **पिछले वर्षों के असली प्रश्न (PYQ)** आते हैं, PYQ बैंक से (📜 टैग के साथ)। "
        "जो PYQ आप पहले कर चुके हैं वे दोबारा नहीं आएँगे। अंकन हर परीक्षा के नियमों के अनुसार होता है।",
    ),
    "pyq.exam": ("Target exam", "लक्ष्य परीक्षा"),
    "pyq.subject": ("Subject", "विषय"),
    "subj.All subjects": ("All subjects", "सभी विषय"),
    "pyq.year": ("Year (optional)", "वर्ष (वैकल्पिक)"),
    "pyq.no_dataset": (
        "The PYQ bank has no questions for **{exam}** yet. Ask an admin to upload PYQs (see the 'PYQ bank' box below).",
        "PYQ बैंक में **{exam}** के प्रश्न अभी नहीं हैं। एडमिन से PYQ अपलोड करवाएँ (नीचे 'PYQ बैंक' वाला बॉक्स देखें)।",
    ),
    "pyq.no_pool": (
        "No PYQs found for this subject/year. Change the filter.",
        "इस विषय/वर्ष के लिए PYQ नहीं मिले। फ़िल्टर बदलें।",
    ),
    "pyq.all_done": (
        "You've already done all {n} PYQs for this filter.",
        "आप इस फ़िल्टर के सभी {n} PYQ कर चुके हैं।",
    ),
    "pyq.reset_seen": (
        "🔁 Reset seen list (PYQs will appear again)",
        "🔁 देखी हुई सूची रीसेट करें (PYQ फिर से आएँगे)",
    ),
    "pyq.avail": (
        "✅ {n} new PYQs available ({d} already done).",
        "✅ {n} नए PYQ उपलब्ध हैं ({d} आप पहले कर चुके हैं)।",
    ),
    "pyq.fill_ai": (
        "Fill with AI practice questions if PYQs run short (these are not real PYQs)",
        "PYQ कम पड़ें तो AI अभ्यास प्रश्नों से भरें (ये असली PYQ नहीं होते)",
    ),
    "pyq.fill_help": (
        "If off, only real PYQs appear — you'll get fewer questions if there aren't enough.",
        "बंद रखने पर सिर्फ़ असली PYQ आएँगे — कम होने पर प्रश्न भी कम मिलेंगे।",
    ),
    "pyq.mark_scheme": ("Marking scheme", "अंकन योजना"),
    "mark.official": ("📋 Official (as in the exam)", "📋 आधिकारिक (परीक्षा जैसी)"),
    "mark.sidebar": ("⚙️ From sidebar", "⚙️ साइडबार वाली"),
    "pyq.official_cap": (
        "+{m} correct · −{p} wrong · 0 unattempted. {note}",
        "+{m} सही · −{p} गलत · 0 अनुत्तरित। {note}",
    ),
    "pyq.adjust": (
        "Adjust marking if your notification is different",
        "नोटिफ़िकेशन में अलग हो तो अंकन बदलें",
    ),
    "pyq.neg": ("Negative marking", "नेगेटिव मार्किंग"),
    "negc.Official": ("Official", "आधिकारिक"),
    "negc.None": ("No negative marking", "कोई नेगेटिव मार्किंग नहीं"),
    "negc.Full": ("Full (−1×)", "पूरा (−1×)"),
    "pyq.num_neg": (
        "Apply negative marking to numerical questions too",
        "संख्यात्मक प्रश्नों पर भी नेगेटिव मार्किंग लगाएँ",
    ),
    "pyq.sidebar_marking": (
        "The sidebar marking will be used for this option.",
        "इस विकल्प में साइडबार वाला अंकन लगेगा।",
    ),
    "pyq.mock": (
        "📝 Full mock test (exam pattern + timer)",
        "📝 पूरा मॉक टेस्ट (परीक्षा जैसा पैटर्न + टाइमर)",
    ),
    "pyq.mock_size": ("Mock size", "मॉक का आकार"),
    "size.Full": ("Full", "पूरा"),
    "size.Half": ("Half (50%)", "आधा (50%)"),
    "size.Quarter": ("Quarter (25%)", "चौथाई (25%)"),
    "pyq.mock_info": (
        "🧾 Mock: {n} questions · {m} min · max {mx} marks · +{a} / −{b}",
        "🧾 मॉक: {n} प्रश्न · {m} मिनट · अधिकतम {mx} अंक · +{a} / −{b}",
    ),
    "pyq.mock_short": (
        "ℹ️ Only {n} new PYQs are available right now, so the mock will be that short (AI filling is off).",
        "ℹ️ अभी सिर्फ़ {n} नए PYQ हैं, इसलिए मॉक उतना ही छोटा बनेगा (AI से भरना बंद है)।",
    ),
    "pyq.practice_cap": (
        "Practice will have {n} questions (change this with the 'Questions' slider in the sidebar).",
        "अभ्यास में {n} प्रश्न आएँगे (साइडबार के 'प्रश्नों की संख्या' स्लाइडर से बदलें)।",
    ),
    "pyq.bank": (
        "📚 PYQ bank / add your own dataset (JSON / CSV)",
        "📚 PYQ बैंक / अपना डेटासेट जोड़ें (JSON / CSV)",
    ),
    "pyq.bank_cap": (
        "Each question needs: exam, subject, year, question, options, answer (text or A-D), explanation. "
        "For numerical questions use `type: num` and a number as the answer. "
        "The `exam` name must be one of: {exams}. "
        "Put the file in the repo as `pyq_data.json` to keep it permanently.",
        "हर प्रश्न में ये होने चाहिए: exam, subject, year, question, options, answer (टेक्स्ट या A-D), explanation। "
        "संख्यात्मक प्रश्न के लिए `type: num` और उत्तर में संख्या लिखें। "
        "`exam` का नाम इनमें से एक हो: {exams}। "
        "फ़ाइल को repo में `pyq_data.json` नाम से रखेंगे तो वह हमेशा रहेगी।",
    ),
    "pyq.admin_ok": (
        "🛠️ You are an admin: after uploading, press 'Save to shared PYQ bank' — the questions will be available to all users.",
        "🛠️ आप एडमिन हैं: अपलोड के बाद 'शेयर्ड PYQ बैंक में सेव करें' दबाएँ — प्रश्न सभी यूज़र्स को मिलेंगे।",
    ),
    "pyq.bank_note": (
        "Only an admin can add questions to the shared bank. The upload below is only for this session.",
        "शेयर्ड बैंक में सिर्फ़ एडमिन प्रश्न जोड़ सकता है। नीचे किया गया अपलोड सिर्फ़ इस सेशन के लिए है।",
    ),
    "pyq.template": ("📄 Template (JSON)", "📄 टेम्पलेट (JSON)"),
    "pyq.file": ("PYQ file", "PYQ फ़ाइल"),
    "pyq.added": (
        "✅ {n} questions added ({d} duplicates skipped).",
        "✅ {n} प्रश्न जोड़े गए ({d} डुप्लिकेट छोड़े गए)।",
    ),
    "pyq.file_err": ("Could not read the file: {e}", "फ़ाइल पढ़ी नहीं जा सकी: {e}"),
    "pyq.save_bank": (
        "📤 Save to shared PYQ bank ({n} questions)",
        "📤 शेयर्ड PYQ बैंक में सेव करें ({n} प्रश्न)",
    ),
    "pyq.bank_saved": (
        "✅ {n} questions saved/updated in the bank.",
        "✅ {n} प्रश्न बैंक में सेव/अपडेट हो गए।",
    ),
    "pyq.bank_fail": (
        "Could not save to the bank (check admin access / SQL): {e}",
        "बैंक में सेव नहीं हो सका (एडमिन एक्सेस / SQL जाँचें): {e}",
    ),
    "pyq.uploaded_n": ("{n} uploaded PYQs in this session.", "इस सेशन में {n} अपलोड किए गए PYQ हैं।"),
    "pyq.clear": ("🗑️ Remove uploaded PYQs", "🗑️ अपलोड किए गए PYQ हटाएँ"),
    "pyq.start_mock": ("🚀 Start {exam} mock test", "🚀 {exam} मॉक टेस्ट शुरू करें"),
    "pyq.start_prac": ("🚀 Start {exam} PYQ practice", "🚀 {exam} PYQ अभ्यास शुरू करें"),
    "pyq.preparing": ("Preparing questions…", "प्रश्न तैयार हो रहे हैं…"),
    "pyq.none_found": ("No questions found right now. {notes}", "अभी कोई प्रश्न नहीं मिला। {notes}"),
    "pyq.got_fewer": (
        "Got only {got} of {plan} questions (that's all the new PYQs there were).",
        "{plan} में से सिर्फ़ {got} प्रश्न मिले (नए PYQ बस इतने ही थे)।",
    ),
    "pyq.ai_fill_fail": (
        "{subj}: couldn't make the remaining questions with AI ({err})",
        "{subj}: बाकी प्रश्न AI से नहीं बन पाए ({err})",
    ),
    "exam.General All Exams": ("General – all exams", "सामान्य – सभी परीक्षाएँ"),
    "exam.Banking (IBPS/SBI)": ("Banking (IBPS/SBI)", "बैंकिंग (IBPS/SBI)"),
    "exam.UP Police Constable": ("UP Police Constable", "UP पुलिस कांस्टेबल"),
    "exam.UP CNET (Nursing)": ("UP CNET (Nursing)", "UP CNET (नर्सिंग)"),
    "note.SSC CGL": ("Tier-I: 100 questions, 60 min, +2 / −0.5.", "टियर-I: 100 प्रश्न, 60 मिनट, +2 / −0.5।"),
    "note.RRB NTPC": ("CBT-1: 100 questions, 90 min, +1 / −⅓.", "CBT-1: 100 प्रश्न, 90 मिनट, +1 / −⅓।"),
    "note.Banking (IBPS/SBI)": (
        "Prelims: 100 questions, 60 min, +1 / −¼.",
        "प्रारंभिक परीक्षा: 100 प्रश्न, 60 मिनट, +1 / −¼।",
    ),
    "note.UP Police Constable": (
        "150 questions, 120 min, +2 / −0.5. Sources differ (some say −0.25 or no negative marking) — check your notification and adjust.",
        "150 प्रश्न, 120 मिनट, +2 / −0.5। स्रोतों में अंतर है (कुछ −0.25 या बिना नेगेटिव मार्किंग लिखते हैं) — अपना नोटिफ़िकेशन देखकर समायोजित करें।",
    ),
    "note.UPSC / State PCS": (
        "Like GS Paper-I: 100 questions, 120 min, +2 / −⅓. Subject-wise counts are approximate.",
        "GS पेपर-I जैसा: 100 प्रश्न, 120 मिनट, +2 / −⅓। विषय-वार संख्या अनुमानित है।",
    ),
    "note.UP CNET (Nursing)": (
        "2026 bulletin: 120 questions, 140 min, +1, no negative marking.",
        "2026 बुलेटिन: 120 प्रश्न, 140 मिनट, +1, कोई नेगेटिव मार्किंग नहीं।",
    ),
    "note.NEET UG": (
        "180 questions (all compulsory), 180 min, +4 / −1, 720 marks.",
        "180 प्रश्न (सभी अनिवार्य), 180 मिनट, +4 / −1, 720 अंक।",
    ),
    "note.JEE Main": (
        "Paper-1: 75 questions (20 MCQ + 5 numerical per subject), 180 min, +4 / −1, 300 marks. "
        "Sources differ on negative marking for numericals — choose with the toggle below.",
        "पेपर-1: 75 प्रश्न (हर विषय में 20 MCQ + 5 संख्यात्मक), 180 मिनट, +4 / −1, 300 अंक। "
        "संख्यात्मक प्रश्नों पर नेगेटिव मार्किंग को लेकर स्रोतों में अंतर है — नीचे दिए टॉगल से चुनें।",
    ),
    # exam subjects (display only; the English names stay as internal values)
    "subj.Reasoning": ("Reasoning", "तर्कशक्ति (रीज़निंग)"),
    "subj.General Awareness": ("General Awareness", "सामान्य जागरूकता"),
    "subj.Quantitative Aptitude": ("Quantitative Aptitude", "मात्रात्मक अभियोग्यता"),
    "subj.English Comprehension": ("English Comprehension", "अंग्रेज़ी बोध"),
    "subj.Mathematics": ("Mathematics", "गणित"),
    "subj.English": ("English", "अंग्रेज़ी"),
    "subj.General Knowledge": ("General Knowledge", "सामान्य ज्ञान"),
    "subj.General Hindi": ("General Hindi", "सामान्य हिंदी"),
    "subj.Numerical Ability": ("Numerical Ability", "संख्यात्मक योग्यता"),
    "subj.History": ("History", "इतिहास"),
    "subj.Polity": ("Polity", "राजव्यवस्था"),
    "subj.Economy": ("Economy", "अर्थव्यवस्था"),
    "subj.Geography": ("Geography", "भूगोल"),
    "subj.Environment": ("Environment", "पर्यावरण"),
    "subj.Science & Tech": ("Science & Tech", "विज्ञान एवं प्रौद्योगिकी"),
    "subj.Current Affairs": ("Current Affairs", "समसामयिकी"),
    "subj.Physics": ("Physics", "भौतिक विज्ञान"),
    "subj.Chemistry": ("Chemistry", "रसायन विज्ञान"),
    "subj.Biology": ("Biology", "जीव विज्ञान"),
    "subj.Botany": ("Botany", "वनस्पति विज्ञान"),
    "subj.Zoology": ("Zoology", "जंतु विज्ञान"),
    "subj.Nursing Aptitude": ("Nursing Aptitude", "नर्सिंग अभिरुचि"),
    "subj.Mixed": ("Mixed", "मिश्रित"),
    "subj.General": ("General", "सामान्य"),

    # ── doubt solver ──
    "doubt.title": ("### 🔍 AI Doubt Solver", "### 🔍 AI डाउट सॉल्वर"),
    "doubt.intro": (
        "Ask a doubt (text, photo, camera or PDF). The answer streams in word by word, and you can ask follow-up questions too.",
        "अपना डाउट पूछें (टेक्स्ट, फ़ोटो, कैमरा या PDF)। उत्तर शब्द-दर-शब्द आता है, और आप फ़ॉलो-अप प्रश्न भी पूछ सकते हैं।",
    ),
    "doubt.lang": ("Answer language", "उत्तर की भाषा"),
    "dlang.Simple English": ("Simple English", "सरल अंग्रेज़ी"),
    "dlang.Hinglish": ("Hinglish", "हिंग्लिश"),
    "dlang.Hindi": ("Hindi", "हिन्दी"),
    "doubt.style": ("Style", "शैली"),
    "depth.Step-by-step": ("Step-by-step", "चरण-दर-चरण"),
    "depth.Quick answer": ("Quick answer", "त्वरित उत्तर"),
    "depth.ELI5": ("Explain like I'm 12 (ELI5)", "बहुत आसान भाषा में (ELI5)"),
    "depth.Exam-ready notes": ("Exam-ready notes", "परीक्षा के लिए नोट्स"),
    "doubt.how": ("How do you want to ask?", "डाउट कैसे पूछना है?"),
    "dsrc.text": ("📝 Text", "📝 टेक्स्ट"),
    "dsrc.camera": ("📸 Live camera", "📸 लाइव कैमरा"),
    "dsrc.photo": ("🖼️ Photo upload", "🖼️ फ़ोटो अपलोड"),
    "dsrc.pdf": ("📄 PDF", "📄 PDF"),
    "doubt.txt": ("Write your doubt here", "अपना डाउट यहाँ लिखें"),
    "doubt.txt_ph": (
        "e.g. How does insertion work in a Binary Search Tree? Explain with an example.",
        "जैसे: Binary Search Tree में insertion कैसे होता है? उदाहरण के साथ समझाएँ।",
    ),
    "doubt.cam_cap": (
        "📸 Allow the camera in your browser and take a clear photo of the question.",
        "📸 ब्राउज़र में कैमरा की अनुमति दें और प्रश्न की साफ़ फ़ोटो लें।",
    ),
    "doubt.cam": ("Take a live photo of the question", "प्रश्न की लाइव फ़ोटो खींचें"),
    "doubt.photo": ("Upload a photo", "फ़ोटो अपलोड करें"),
    "doubt.q_photo": ("Question photo", "प्रश्न की फ़ोटो"),
    "doubt.extra": ("Any extra instruction? (optional)", "कोई अतिरिक्त निर्देश? (वैकल्पिक)"),
    "doubt.extra_ph": ("e.g. Solve only Q3", "जैसे: सिर्फ़ Q3 हल करें"),
    "doubt.pdf": ("Upload a PDF", "PDF अपलोड करें"),
    "doubt.pdf_q": ("What do you want to ask about the PDF?", "PDF के बारे में क्या पूछना है?"),
    "doubt.pdf_q_ph": ("e.g. Give a summary of this chapter", "जैसे: इस अध्याय का सारांश दें"),
    "doubt.pdf_loaded": ("The first 5 pages of the PDF are loaded.", "PDF के पहले 5 पेज लोड हो गए।"),
    "doubt.pdf_empty": (
        "No text found in the PDF. Upload a photo of the page.",
        "PDF से टेक्स्ट नहीं निकला। पेज की फ़ोटो अपलोड करें।",
    ),
    "doubt.pdf_err": ("PDF read error: {e}", "PDF पढ़ने में त्रुटि: {e}"),
    "doubt.explain": ("💡 Explain", "💡 समझाएँ"),
    "doubt.need": ("First write a doubt or give a photo.", "पहले डाउट लिखें या फ़ोटो दें।"),
    "doubt.photo_doubt": ("📷 *Doubt from a photo*", "📷 *फ़ोटो से डाउट*"),
    "doubt.retry": ("🔁 Regenerate answer", "🔁 उत्तर दोबारा बनाएँ"),
    "doubt.follow": ("Ask a follow-up", "फ़ॉलो-अप पूछें"),
    "doubt.follow_ph": (
        "e.g. Explain with another example / Why did this step happen?",
        "जैसे: एक और उदाहरण से समझाएँ / इस चरण में ऐसा क्यों हुआ?",
    ),
    "doubt.send": ("Send ➤", "भेजें ➤"),
    "doubt.new": ("🧹 New doubt", "🧹 नया डाउट"),
    "doubt.make_quiz": ("📝 Make a quiz on this", "📝 इस पर क्विज़ बनाएँ"),
    "doubt.notes_dl": ("⬇️ Notes (.md)", "⬇️ नोट्स (.md)"),
    "doubt.you": ("You", "आप"),
    "doubt.ai": ("AI", "AI"),
    "doubt.thinking": ("Thinking…", "सोच रहा हूँ…"),

    # ── quiz stage ──
    "qz.q_of": ("Question {i} of {n}", "प्रश्न {i} / {n}"),
    "qz.qnum": ("Question {i}", "प्रश्न {i}"),
    "qz.choose": ("Choose your answer", "अपना उत्तर चुनें"),
    "qz.multi_cap": ("Select all correct options", "सभी सही विकल्प चुनें"),
    "qz.num_label": ("Numerical answer", "संख्यात्मक उत्तर"),
    "qz.num_ph": ("Enter just a number, e.g. 12.5", "सिर्फ़ संख्या लिखें, जैसे 12.5"),
    "qz.blank_label": ("Fill in the blank", "रिक्त स्थान भरें"),
    "qz.blank_ph": ("Type your answer…", "अपना उत्तर लिखें…"),
    "qz.short_label": ("Short answer", "संक्षिप्त उत्तर"),
    "qz.short_ph": ("Write your answer (1-3 lines)", "अपना उत्तर लिखें (1-3 पंक्तियाँ)"),
    "tf.True": ("True", "सही"),
    "tf.False": ("False", "गलत"),
    "qz.hint": ("💡 Hint (−5 XP)", "💡 संकेत (−5 XP)"),
    "qz.saved": ("📌 Saved", "📌 सहेजा गया"),
    "qz.save": ("🔖 Save", "🔖 सहेजें"),
    "qz.listen": ("Listen", "सुनें"),
    "qz.listen_tip": ("Listen (R)", "सुनें (R)"),
    "qz.stop": ("Stop", "रोकें"),
    "qz.kbd": (
        "⌨️ <kbd>1</kbd>–<kbd>{n}</kbd> choose · <kbd>Enter</kbd> next · <kbd>H</kbd> hint · {extra}<kbd>R</kbd> listen",
        "⌨️ <kbd>1</kbd>–<kbd>{n}</kbd> चुनें · <kbd>Enter</kbd> आगे · <kbd>H</kbd> संकेत · {extra}<kbd>R</kbd> सुनें",
    ),
    "qz.kbd_skip": ("<kbd>S</kbd> skip · ", "<kbd>S</kbd> छोड़ें · "),
    "qz.game_over": ("💀 All lives are gone! Game over.", "💀 सारी लाइव्स खत्म! गेम ओवर।"),
    "qz.explain": ("🧠 Explain in more detail", "🧠 और विस्तार से समझाएँ"),
    "qz.processing": ("Processing…", "प्रक्रिया जारी है…"),
    "qz.palette": ("🧭 Question palette", "🧭 प्रश्न पैलेट"),
    "qz.palette_cap": (
        "✅ = Answered · Highlighted button = Current question.",
        "✅ = उत्तर दिया · हाइलाइट बटन = वर्तमान प्रश्न।",
    ),
    "qz.back": ("⬅️ Back", "⬅️ पीछे"),
    "qz.check": ("Check answer", "उत्तर जाँचें"),
    "qz.checking": ("Checking answer…", "उत्तर जाँचा जा रहा है…"),
    "qz.checking_short": ("Checking short answers…", "संक्षिप्त उत्तर जाँचे जा रहे हैं…"),
    "qz.skip": ("Skip ⏭️", "छोड़ें ⏭️"),
    "qz.view_results": ("View results 💀", "परिणाम देखें 💀"),
    "qz.finish": ("Finish 🏁", "समाप्त 🏁"),
    "qz.next": ("Next ➡️", "अगला ➡️"),
    "qz.leave": ("✖ Leave quiz", "✖ क्विज़ छोड़ें"),
    "qz.countdown": ("⏱️ {n} sec left", "⏱️ {n} सेकंड बचे हैं"),
    "qz.quiz_countdown": ("⏳ Quiz time left: {m:02d}:{s:02d}", "⏳ क्विज़ का समय बचा: {m:02d}:{s:02d}"),

    # ── answer feedback ──
    "fb.short_ok": ("✅ <b>Great job!</b>", "✅ <b>शाबाश!</b>"),
    "fb.short_bad": ("🟡 <b>Incomplete / incorrect.</b>", "🟡 <b>अधूरा / गलत।</b>"),
    "fb.ai_score": ("AI score:", "AI स्कोर:"),
    "fb.model_ans": ("Model answer:", "आदर्श उत्तर:"),
    "fb.correct": ("✅ <b>Correct answer!</b>", "✅ <b>सही उत्तर!</b>"),
    "fb.timeup": ("⏰ <b>Time's up.</b> ", "⏰ <b>समय समाप्त।</b> "),
    "fb.skipped": ("⏭️ <b>Skipped.</b> ", "⏭️ <b>छोड़ा गया।</b> "),
    "fb.wrong": ("❌ <b>Incorrect.</b> ", "❌ <b>गलत।</b> "),
    "fb.correct_is": ("Correct answer:", "सही उत्तर:"),
    "fb.no_expl": ("No explanation available.", "स्पष्टीकरण उपलब्ध नहीं है।"),
    "grade.none": ("No answer provided.", "कोई उत्तर नहीं लिखा गया।"),
    "grade.fail": (
        "AI grading failed — please compare with the model answer manually.",
        "AI ग्रेडिंग नहीं हो पाई — कृपया आदर्श उत्तर से खुद तुलना करें।",
    ),

    # ── flashcards ──
    "flash.title": ("## 📇 Flashcards", "## 📇 फ़्लैशकार्ड"),
    "flash.card": ("Card {i} of {n}", "कार्ड {i} / {n}"),
    "flash.prev": ("⬅️ Previous", "⬅️ पिछला"),
    "flash.show_ans": ("🔄 Show answer", "🔄 उत्तर दिखाएँ"),
    "flash.show_q": ("🔄 Show question", "🔄 प्रश्न दिखाएँ"),
    "flash.next": ("Next ➡️", "अगला ➡️"),
    "flash.back": ("← Back", "← वापस"),

    # ── result ──
    "res.great": ("Great Job! 🏆", "बहुत बढ़िया! 🏆"),
    "res.great_msg": ("You have a strong grip on this topic.", "इस विषय पर आपकी पकड़ बहुत अच्छी है।"),
    "res.good": ("Good Try! 👍", "अच्छा प्रयास! 👍"),
    "res.good_msg": (
        "A little more practice and you'll hit the top score.",
        "थोड़े और अभ्यास से आप सर्वोच्च स्कोर तक पहुँच जाएँगे।",
    ),
    "res.keep": ("Keep Going 💪", "लगे रहिए 💪"),
    "res.keep_msg": ("Read the explanations and try again.", "स्पष्टीकरण पढ़ें और दोबारा प्रयास करें।"),
    "res.marking": (
        "Marking: +{m} correct · −{p} wrong · 0 skipped{nn}  |  Accuracy = correct ÷ attempted",
        "अंकन: +{m} सही · −{p} गलत · 0 छोड़ा{nn}  |  सटीकता = सही ÷ प्रयास किए",
    ),
    "res.no_neg_num": (" · no negative on numericals", " · संख्यात्मक पर नेगेटिव नहीं"),
    "res.time_up": (
        "⏰ The total quiz time ran out — the remaining questions are counted as skipped.",
        "⏰ क्विज़ का कुल समय खत्म हो गया — बचे हुए प्रश्न छोड़े गए माने गए।",
    ),
    "res.marks_of": ("{a} / {b} marks", "{a} / {b} अंक"),
    "res.marks": ("Marks", "अंक"),
    "res.accuracy": ("Accuracy", "सटीकता"),
    "res.attempted": ("Attempted", "प्रयास किए"),
    "res.neg_marks": ("Negative marks", "नेगेटिव अंक"),
    "res.correct": ("Correct", "सही"),
    "res.wrong": ("Wrong", "गलत"),
    "res.skipped": ("Skipped", "छोड़े गए"),
    "res.total_time": ("Total time", "कुल समय"),
    "res.xp": ("XP earned", "अर्जित XP"),
    "res.best_streak": ("Best streak", "सर्वश्रेष्ठ स्ट्रीक"),
    "res.avg_q": ("Avg / question", "औसत / प्रश्न"),
    "res.hints": ("Hints used", "प्रयुक्त संकेत"),
    "res.level_up": ("🎉 Level up! You are now on **Level {n}**.", "🎉 लेवल अप! अब आप **लेवल {n}** पर हैं।"),
    "badge.perfect": ("💎 Perfect Score", "💎 परफ़ेक्ट स्कोर"),
    "badge.streak": ("🔥 Streak Master", "🔥 स्ट्रीक मास्टर"),
    "badge.speed": ("⚡ Speedster", "⚡ तेज़ रफ़्तार"),
    "badge.nohints": ("🧘 No Hints Needed", "🧘 बिना संकेत के सफल"),
    "badge.hard": ("🦾 Hard Mode Hero", "🦾 हार्ड मोड हीरो"),
    "badge.survivor": ("🛡️ Survivor", "🛡️ सर्वाइवर"),
    "badge.allround": ("🧩 All-rounder", "🧩 ऑल-राउंडर"),
    "badge.regular": ("📚 Regular Learner", "📚 नियमित शिक्षार्थी"),
    "res.more_title": (
        "**➕ Want more questions?**  **{n}** questions so far.",
        "**➕ और प्रश्न चाहिए?**  अब तक **{n}** प्रश्न हो चुके हैं।",
    ),
    "res.more_n": ("How many more questions?", "और कितने प्रश्न?"),
    "res.more_btn": ("➕ Add {n} more questions", "➕ {n} और प्रश्न जोड़ें"),
    "res.more_spin": ("Making new questions…", "नए प्रश्न बन रहे हैं…"),
    "res.more_fail": (
        "Couldn't make new questions. Please try again.",
        "नए प्रश्न नहीं बन पाए। कृपया दोबारा प्रयास करें।",
    ),
    "res.more_note": (
        "New questions are added to this same quiz — marks, accuracy and XP will be calculated for the whole quiz.",
        "नए प्रश्न इसी क्विज़ में जुड़ जाएँगे — अंक, सटीकता और XP पूरे क्विज़ के मिलाकर बनेंगे।",
    ),
    "res.more_note_over": (
        "All lives are gone in Survival mode, so more questions can't be added.",
        "सर्वाइवल मोड में सारी लाइव्स खत्म हो चुकी हैं, इसलिए और प्रश्न नहीं जोड़े जा सकते।",
    ),
    "res.more_note_max": ("A quiz can have at most {n} questions.", "एक क्विज़ में अधिकतम {n} प्रश्न हो सकते हैं।"),
    "res.new_quiz": ("🔁 New quiz", "🔁 नया क्विज़"),
    "res.redo_wrong": ("🎯 Redo only wrong ones", "🎯 सिर्फ़ गलत दोबारा"),
    "res.redo_help": (
        "Re-solve only the wrong/skipped questions",
        "सिर्फ़ गलत/छोड़े गए प्रश्न फिर से हल करें",
    ),
    "res.same_again": ("🔄 Same quiz again", "🔄 वही क्विज़ फिर से"),
    "res.new_qs": ("🆕 New questions (same source)", "🆕 नए प्रश्न (वही स्रोत)"),
    "res.new_qs_fail": ("Couldn't make new questions.", "नए प्रश्न नहीं बन पाए।"),
    "res.flash": ("📇 Flashcards of this quiz", "📇 इस क्विज़ के फ़्लैशकार्ड"),
    "res.topic_perf": ("### 📊 Topic-wise performance", "### 📊 विषय-वार प्रदर्शन"),
    "res.col_topic": ("Topic", "विषय"),
    "res.col_acc": ("Accuracy %", "सटीकता %"),
    "res.strong": ("💪 Strong: {l}", "💪 मज़बूत: {l}"),
    "res.weak": ("📌 Revise: {l}", "📌 दोहराएँ: {l}"),
    "res.plan_btn": ("🧭 Make AI study plan", "🧭 AI स्टडी प्लान बनाएँ"),
    "res.plan_spin": ("Making your study plan…", "स्टडी प्लान बन रहा है…"),
    "res.review": ("### 🔍 Review", "### 🔍 समीक्षा"),
    "res.your_tag": (" (your answer)", " (आपका उत्तर)"),
    "res.missed": (" (you missed this)", " (आपसे छूट गया)"),
    "res.wrong_pick": (" (chosen wrongly)", " (गलत चुना)"),
    "res.your_answer": ("**Your answer:** {a}", "**आपका उत्तर:** {a}"),
    "res.correct_answer": ("**Correct answer:** {a}", "**सही उत्तर:** {a}"),
    "res.ai_score": ("🧪 **AI score:** {s:.1f}/1 — {f}", "🧪 **AI स्कोर:** {s:.1f}/1 — {f}"),
    "res.skipped_note": (
        "This question was skipped / time ran out / game over.",
        "यह प्रश्न छोड़ा गया / समय खत्म हो गया / गेम ओवर हो गया।",
    ),
    "res.marks_line": ("🎯 Marks: {m}", "🎯 अंक: {m}"),
    "res.download": ("### 📥 Download", "### 📥 डाउनलोड"),
    "res.dl_html": ("Report (HTML)", "रिपोर्ट (HTML)"),
    "res.dl_csv": ("Results (CSV)", "परिणाम (CSV)"),
    "res.dl_json": ("Quiz (JSON)", "क्विज़ (JSON)"),

    # ── downloadable report / CSV ──
    "report.title": ("{app} · Result Report", "{app} · परिणाम रिपोर्ट"),
    "report.q": ("Question", "प्रश्न"),
    "report.your": ("Your answer", "आपका उत्तर"),
    "report.correct": ("Correct", "सही उत्तर"),
    "report.expl": ("Explanation", "स्पष्टीकरण"),
    "csv.no": ("No", "क्र.सं."),
    "csv.type": ("Type", "प्रकार"),
    "csv.topic": ("Topic", "विषय"),
    "csv.question": ("Question", "प्रश्न"),
    "csv.options": ("Options", "विकल्प"),
    "csv.your": ("Your answer", "आपका उत्तर"),
    "csv.correct": ("Correct answer", "सही उत्तर"),
    "csv.result": ("Result", "परिणाम"),
    "csv.marks": ("Marks", "अंक"),
    "csv.expl": ("Explanation", "स्पष्टीकरण"),
    "csv.r_ok": ("Correct", "सही"),
    "csv.r_bad": ("Wrong/Skipped", "गलत/छोड़ा गया"),

    # ── theme.py (hero / tiles helpers) ──
    "th.gm": ("Good morning", "सुप्रभात"),
    "th.ga": ("Good afternoon", "नमस्कार"),
    "th.ge": ("Good evening", "शुभ संध्या"),
    "th.gn": ("Late-night grind", "शुभ रात्रि"),
    "th.guest": ("Guest", "मेहमान"),
    "th.lvl": ("Level", "लेवल"),
    "th.xp_next": ("{n} XP to next level", "अगले लेवल तक {n} XP"),
    "th.c1": ("SSC · NEET · JEE · UP CNET", "SSC · NEET · JEE · UP CNET"),
    "th.c2": ("Solve doubts with camera", "कैमरे से डाउट हल करें"),
    "th.c3": ("3 languages", "3 भाषाएँ"),
}


# ─────────────────────────────────────────────────────────────
# CORE API
# ─────────────────────────────────────────────────────────────
def cur():
    """Active UI language code: 'en' or 'hi'."""
    try:
        c = st.session_state.get("ui_lang", DEFAULT)
    except Exception:
        return DEFAULT
    return c if c in LANGS else DEFAULT


def tr(key, **fmt):
    """Translate `key` into the active language. Extra kwargs fill {placeholders}."""
    row = _S.get(key)
    if row is None:
        return key  # a missing key shows up as itself, which makes it easy to spot
    s = row[1] if cur() == "hi" else row[0]
    if fmt:
        try:
            return s.format(**fmt)
        except (KeyError, IndexError, ValueError):
            return s
    return s


def has(key):
    return key in _S


def fmt(prefix):
    """format_func for widgets: shows tr('prefix.<value>') and falls back to the raw value."""
    def _f(v):
        k = f"{prefix}.{v}"
        return tr(k) if k in _S else str(v)

    return _f


def ai_lang():
    """Language name to put in AI prompts so generated text follows the UI language."""
    return LANGS[cur()]["ai"]


def tts_code():
    return LANGS[cur()]["tts"]


def localize_time(s):
    """'03 Nov, 14:30' -> Hindi month abbreviation when the UI is Hindi."""
    s = str(s)
    if cur() != "hi":
        return s
    return re.sub(r"\b(" + "|".join(HI_MONTHS) + r")\b", lambda m: HI_MONTHS[m.group(1)], s)


def shortcut_regex(name):
    return "|".join(re.escape(w) for w in SHORTCUTS[name])


def init():
    """Call once, right after st.set_page_config. English is the default for first-time users."""
    ss = st.session_state
    if ss.get("ui_lang") not in LANGS:
        ss["ui_lang"] = DEFAULT
    ss.setdefault("ui_lang_explicit", False)  # True once the user (or the saved preference) chose a language
    ss.setdefault("language", LANGS[ss["ui_lang"]]["quiz"])  # quiz-content language follows the UI language
    ss.setdefault("d_lang", LANGS[ss["ui_lang"]]["doubt"])  # doubt-solver answer language likewise


def set_lang(code, explicit=True):
    ss = st.session_state
    if code not in LANGS:
        code = DEFAULT
    ss["ui_lang"] = code
    ss["ui_lang_explicit"] = explicit
    ss["language"] = LANGS[code]["quiz"]
    ss["d_lang"] = LANGS[code]["doubt"]
    for slot in SLOTS:  # keep every switcher in sync
        ss[f"lang_sw_{slot}"] = LANGS[code]["label"]


def _on_switch(slot):
    set_lang(_LABEL2CODE.get(st.session_state.get(f"lang_sw_{slot}"), DEFAULT))


def render_switcher(slot):
    """Segmented 🇬🇧 English | 🇮🇳 हिंदी switch. slot: 'login' | 'top' | 'side'."""
    ss = st.session_state
    key = f"lang_sw_{slot}"
    want = LANGS[cur()]["label"]
    if ss.get(key) != want:
        ss[key] = want
    st.radio(
        "Language / भाषा",  # constant label, so the widget keeps its state when the language changes
        [LANGS[c]["label"] for c in LANG_ORDER],
        horizontal=True,
        key=key,
        label_visibility="collapsed",
        on_change=_on_switch,
        args=(slot,),
    )


# ─────────────────────────────────────────────────────────────
# PERSISTENCE (browser localStorage) + <html lang>
# ─────────────────────────────────────────────────────────────
_BRIDGE_JS = r"""
var P = window.parent;
try { P.document.documentElement.setAttribute('lang', C.html); } catch (e) {}
try {
  if (C.explicit) { P.localStorage.setItem(C.key, C.cur); return; }   // user picked a language -> remember it
  var s = P.localStorage.getItem(C.key);                                // first run of a visit -> restore it
  if (!s || s === C.cur || !C.labels[s]) return;
  var word = C.labels[s].split(' ').pop(), n = 0;
  var iv = setInterval(function () {
    n++;
    var root = P.document.querySelector('.st-key-lang_sw_top,.st-key-lang_sw_login,.st-key-lang_sw_side'), hit = null;
    if (root) {
      var ls = root.querySelectorAll('label');
      for (var i = 0; i < ls.length; i++) { if ((ls[i].innerText || '').indexOf(word) > -1) { hit = ls[i]; break; } }
    }
    if (hit) { hit.click(); clearInterval(iv); } else if (n > 40) { clearInterval(iv); }
  }, 150);
} catch (e) {}
"""


def bridge_js():
    """<script> that (a) saves the language to localStorage, (b) restores it on a new visit, (c) sets <html lang>."""
    ss = st.session_state
    cfg = {
        "cur": cur(),
        "explicit": bool(ss.get("ui_lang_explicit")),
        "labels": {c: LANGS[c]["label"] for c in LANG_ORDER},
        "html": LANGS[cur()]["html"],
        "key": STORAGE_KEY,
    }
    return "<script>(function(){var C=" + json.dumps(cfg) + ";" + _BRIDGE_JS + "})();</script><!--" + str(time.time()) + "-->"


# ─────────────────────────────────────────────────────────────
# SWITCHER + DEVANAGARI STYLING (uses the app's CSS variables, so light/dark both work)
# ─────────────────────────────────────────────────────────────
LANG_CSS = """
<style>
.st-key-langbar{ align-items:flex-end; margin:-6px 0 4px; }
.st-key-langbar > div{ width:auto !important; }
.st-key-lang_sw_top div[role="radiogroup"], .st-key-lang_sw_login div[role="radiogroup"], .st-key-lang_sw_side div[role="radiogroup"]{
  display:inline-flex; flex-wrap:nowrap; gap:4px; padding:4px; border-radius:99px;
  background:var(--panel); border:1px solid var(--line); backdrop-filter:blur(6px);
}
.st-key-lang_sw_side div[role="radiogroup"]{ display:flex; width:100%; }
.st-key-lang_sw_side label[data-baseweb="radio"]{ flex:1; justify-content:center; }
.st-key-lang_sw_top label[data-baseweb="radio"], .st-key-lang_sw_login label[data-baseweb="radio"], .st-key-lang_sw_side label[data-baseweb="radio"]{
  margin:0; padding:6px 16px; border-radius:99px; font-weight:700; cursor:pointer; white-space:nowrap;
  transition:background .2s ease, transform .12s ease, box-shadow .2s ease;
}
.st-key-lang_sw_top label[data-baseweb="radio"] > div:first-of-type, .st-key-lang_sw_login label[data-baseweb="radio"] > div:first-of-type,
.st-key-lang_sw_side label[data-baseweb="radio"] > div:first-of-type{ display:none; }
.st-key-lang_sw_top label[data-baseweb="radio"]:hover, .st-key-lang_sw_login label[data-baseweb="radio"]:hover,
.st-key-lang_sw_side label[data-baseweb="radio"]:hover{ background:rgba(124,92,255,.16); transform:translateY(-1px); }
.stApp .st-key-lang_sw_top label:has(input:checked), .stApp .st-key-lang_sw_login label:has(input:checked), .stApp .st-key-lang_sw_side label:has(input:checked){
  background:linear-gradient(135deg,var(--violet),#4F8CFF 55%,var(--cyan)); box-shadow:0 8px 22px -10px rgba(124,92,255,.8);
}
.stApp .st-key-lang_sw_top label:has(input:checked) *, .stApp .st-key-lang_sw_login label:has(input:checked) *,
.stApp .st-key-lang_sw_side label:has(input:checked) *{ color:#fff !important; }
@media (max-width:640px){
  .st-key-lang_sw_top label[data-baseweb="radio"], .st-key-lang_sw_login label[data-baseweb="radio"]{ padding:5px 12px; font-size:.86rem; }
}
</style>
"""
