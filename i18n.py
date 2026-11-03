"""
i18n.py — Complete language translation module for AI Quiz Arena.
Handles English 🇬🇧 and हिन्दी 🇮🇳 language switching seamlessly.
"""
import functools
import streamlit as st

# Service & Info Constants
ADMIN_HELP = {
    "en": "🛠️ Admin: You can upload and manage questions in the shared PYQ bank.",
    "hi": "🛠️ एडमिन: साझा PYQ बैंक में सवाल अपलोड और प्रबंधित कर सकते हैं।"
}
EMAIL_SVC_MSG = {
    "en": "Email OTP service is active.",
    "hi": "ईमेल OTP सेवा सक्रिय है।"
}
SVC_MSG = {
    "en": "System operational.",
    "hi": "सिस्टम क्रियाशील है।"
}

LANGS = {"English 🇬🇧": "en", "हिन्दी 🇮🇳": "hi"}
LANG_ORDER = ["English 🇬🇧", "हिन्दी 🇮🇳"]
DEFAULT = "en"

QUIZ_LANG_OF = {
    "en": "English",
    "hi": "Hindi",
    "English 🇬🇧": "English",
    "हिन्दी 🇮🇳": "Hindi"
}

# Translation Table Mapping (English -> Hindi)
TABLE = [
    # ── Sidebar ──
    ("### ⚙️ Quiz Settings", "### ⚙️ क्विज़ सेटिंग्स"),
    ("Questions", "प्रश्नों की संख्या"),
    ("Over 10 questions are made in batches, so it can take a little longer.", "10 से ज़्यादा प्रश्न बैच में बनते हैं, थोड़ा समय लग सकता है।"),
    ("Difficulty", "कठिनाई"),
    ("Easy", "आसान"),
    ("Medium", "मध्यम"),
    ("Hard", "कठिन"),
    ("🎚️ Adaptive difficulty", "🎚️ अनुकूल कठिनाई"),
    ("Questions get harder when you answer right and easier when you miss.", "सही उत्तर देने पर प्रश्न कठिन और गलत देने पर आसान हो जाएंगे।"),
    ("Question types", "प्रश्नों के प्रकार"),
    ("Language", "भाषा"),
    ("Quiz language", "क्विज़ की भाषा"),
    ("Mode", "मोड"),
    ("Practice: instant answer after every question.\nExam: result at the end.\nSurvival: only 3 lives — 3 wrong answers and it's game over!",
     "प्रैक्टिस: हर प्रश्न के बाद तुरंत उत्तर।\nएग्ज़ाम: परिणाम अंत में।\nसर्वाइवल: सिर्फ़ 3 जीवन — 3 गलत उत्तर पर गेम ओवर!"),
    ("Practice", "प्रैक्टिस"),
    ("Exam", "एग्ज़ाम"),
    ("Survival", "सर्वाइवल"),
    ("**⏱️ Timer**", "**⏱️ टाइमर**"),
    ("Timer type", "टाइमर का प्रकार"),
    ("Off", "बंद"),
    ("Per question", "प्रति प्रश्न"),
    ("Whole quiz", "पूरे क्विज़ का"),
    ("Seconds per question", "प्रति प्रश्न सेकंड"),
    ("Minutes (whole quiz)", "मिनट (पूरे क्विज़ के)"),
    ("Custom", "कस्टम"),
    ("Custom seconds", "कस्टम सेकंड"),
    ("Custom minutes", "कस्टम मिनट"),
    ("The answer is submitted automatically when time runs out.", "समय खत्म होते ही उत्तर अपने आप जमा हो जाता है।"),
    ("The timer needs Streamlit ≥ 1.37.", "टाइमर के लिए Streamlit ≥ 1.37 चाहिए।"),
    ("**🎯 Marking**", "**🎯 अंकन**"),
    ("Marks per correct answer", "प्रति सही उत्तर अंक"),
    ("Negative marking (on wrong)", "नेगेटिव मार्किंग (गलत होने पर)"),
    ("A wrong answer loses this fraction of the marks. Skipped = 0. Short answers get partial marks, never negative.",
     "गलत उत्तर पर सही-अंकों का इतना हिस्सा कटेगा। छोड़ने पर 0। छोटे उत्तर में आंशिक अंक मिलते हैं, नेगेटिव नहीं।"),
    ("None", "कोई नहीं"),
    ("🔊 Sound & Look", "🔊 आवाज़ और लुक"),
    ("Sound effects", "साउंड इफ़ेक्ट"),
    ("Read questions aloud automatically", "प्रश्न खुद पढ़कर सुनाओ"),
    ("If there's no sound, click once on the page or press the 🔊 button.", "अगर आवाज़ न आए तो पहले पेज पर एक क्लिक करो या 🔊 बटन दबाओ।"),
    ("Speaking speed", "बोलने की गति"),
    ("☀️ Light mode", "☀️ लाइट मोड"),
    ("Advanced", "उन्नत सेटिंग्स"),
    ("AI model", "AI मॉडल"),
    ("120b = most accurate. 8b-instant = fastest.", "120b = सबसे सटीक। 8b-instant = सबसे तेज़।"),
    ("### 🔖 Saved questions", "### 🔖 सहेजे हुए प्रश्न"),
    ("Press 🔖 during a quiz and the question is saved here.", "क्विज़ के दौरान 🔖 दबाओ, प्रश्न यहाँ सहेज जाएगा।"),
    ("Study with flashcards", "📇 फ़्लैशकार्ड से पढ़ो"),
    ("### 🏆 My History", "### 🏆 मेरी हिस्ट्री"),
    ("Clear history", "हिस्ट्री साफ़ करो"),
    ("No quiz taken yet. Make your first one!", "अभी कोई क्विज़ नहीं दिया। पहला क्विज़ बनाओ!"),
    ("### 💾 Progress backup", "### 💾 प्रोग्रेस बैकअप"),
    ("Your XP, history and saved questions are saved to your account automatically. You can also keep a file backup here.",
     "आपका XP, हिस्ट्री और सहेजे प्रश्न आपके अकाउंट में अपने आप सेव होते हैं। यहाँ फ़ाइल बैकअप भी रख सकते हैं।"),
    ("Download progress", "⬇️ प्रोग्रेस डाउनलोड करो"),
    ("Load progress", "प्रोग्रेस लोड करो"),

    # ── Tabs / Setup ──
    ("🧠 Quiz Arena", "🧠 क्विज़ एरीना"),
    ("🏛️ Govt Exam PYQs", "🏛️ सरकारी परीक्षा PYQ"),
    ("🔍 Doubt Solver", "🔍 डाउट सॉल्वर"),
    ("Where will the content come from?", "सामग्री कहाँ से आएगी?"),
    ("💡 Topic", "💡 टॉपिक"),
    ("📄 PDF", "📄 PDF"),
    ("🖼️ Photo / Camera", "🖼️ फ़ोटो / कैमरा"),
    ("📝 Notes", "📝 नोट्स"),
    ("Which topic do you want a quiz on?", "किस टॉपिक पर क्विज़ चाहिए?"),
    ("e.g. Machine Learning basics, Indian Constitution, Python lists…", "जैसे: मशीन लर्निंग बेसिक्स, भारतीय संविधान, Python lists…"),
    ("Quick picks", "त्वरित चुनाव"),
    ("Upload a PDF", "PDF अपलोड करो"),
    ("Page range", "पेज रेंज"),
    ("Upload a photo or click one directly with the camera.", "फ़ोटो अपलोड करो या कैमरे से सीधे क्लिक करो।"),
    ("Photo mode", "फ़ोटो मोड"),
    ("📁 Upload File", "📁 फ़ाइल अपलोड"),
    ("📸 Live Camera Click", "📸 लाइव कैमरा क्लिक"),
    ("Upload a photo", "फ़ोटो अपलोड करो"),
    ("Take a live photo", "लाइव फ़ोटो खींचो"),
    ("Paste your notes / article here", "अपने नोट्स / लेख यहाँ पेस्ट करो"),
    ("Chapter text, notes or any article…", "अध्याय का टेक्स्ट, नोट्स या कोई भी लेख…"),
    ("Make quiz", "✨ क्विज़ बनाओ"),
    ("First write a topic, upload/click a photo or paste notes.", "पहले टॉपिक लिखो, फ़ोटो अपलोड/क्लिक करो या नोट्स पेस्ट करो।"),
    ("AI is making questions…", "AI प्रश्न बना रहा है…"),
    ("Making questions…", "प्रश्न बन रहे हैं…"),
    ("Couldn't make valid questions. Please try again.", "सही प्रश्न नहीं बन पाए। दोबारा कोशिश करो।"),
    ("Couldn't understand the AI response. Try again or pick another model.", "AI का जवाब समझ नहीं आया। दोबारा कोशिश करो या दूसरा मॉडल चुनो।"),
    ("No text found in this PDF (looks scanned). Try a photo of the page.", "इस PDF से टेक्स्ट नहीं निकला (स्कैन लगता है)। उस पेज की फ़ोटो लेकर देखो।"),
    ("The photo is over 15 MB. Use a smaller one.", "फ़ोटो 15 MB से बड़ी है। छोटी फ़ोटो इस्तेमाल करो।"),
    ("Still too big after compression. Use a lower-resolution photo.", "कंप्रेस होने के बाद भी बहुत बड़ी है। कम रेज़ोल्यूशन की फ़ोटो लो।"),

    # ── Govt Exams ──
    ("### 🏛️ Govt & Entrance Exam Practice", "### 🏛️ सरकारी एवं प्रवेश परीक्षा अभ्यास"),
    ("Target exam", "लक्ष्य परीक्षा"),
    ("Subject", "विषय"),
    ("Year (optional)", "वर्ष (वैकल्पिक)"),
    ("Fill the rest with AI if the dataset runs short", "डेटासेट में कम पड़े तो AI से भरो"),
    ("Marking scheme", "अंकन योजना"),
    ("📋 Official (as in the exam)", "📋 आधिकारिक (परीक्षा जैसी)"),
    ("⚙️ From sidebar", "⚙️ साइडबार वाली"),
    ("Negative marking", "नेगेटिव मार्किंग"),
    ("📝 Full mock test (exam pattern + timer)", "📝 पूरा मॉक टेस्ट (परीक्षा जैसा पैटर्न + टाइमर)"),
    ("➕ Add your own PYQ dataset (JSON / CSV)", "➕ अपना PYQ डेटासेट जोड़ो (JSON / CSV)"),
    ("📄 Template (JSON)", "📄 टेम्पलेट (JSON)"),
    ("PYQ file", "PYQ फ़ाइल"),
    ("🗑️ Remove uploaded PYQs", "🗑️ अपलोड किए PYQ हटाओ"),
    ("Preparing questions…", "प्रश्न तैयार हो रहे हैं…"),

    # ── Doubt Solver ──
    ("### 🔍 AI Doubt Solver", "### 🔍 AI डाउट सॉल्वर"),
    ("Answer language", "उत्तर की भाषा"),
    ("Style", "शैली"),
    ("How do you want to ask?", "डाउट कैसे पूछना है?"),
    ("📝 Text", "📝 टेक्स्ट"),
    ("📸 Live Camera", "📸 लाइव कैमरा"),
    ("🖼️ Photo Upload", "🖼️ फ़ोटो अपलोड"),
    ("Write your doubt here", "अपना डाउट यहाँ लिखो"),
    ("Take a live photo of the question", "प्रश्न की लाइव फ़ोटो खींचो"),
    ("💡 Explain", "💡 समझाओ"),
    ("First write a doubt or give a photo.", "पहले डाउट लिखो या फ़ोटो दो।"),
    ("🔁 Regenerate answer", "🔁 उत्तर दोबारा बनाओ"),
    ("Ask a follow-up", "फ़ॉलो-अप पूछो"),
    ("Send ➤", "भेजो ➤"),
    ("🧹 New doubt", "🧹 नया डाउट"),
    ("📝 Make a quiz on this", "📝 इस पर क्विज़ बनाओ"),
    ("⬇️ Notes (.md)", "⬇️ नोट्स (.md)"),
    ("Thinking…", "सोच रहा हूँ…"),

    # ── Quiz Stage ──
    ("Choose your answer", "अपना उत्तर चुनो"),
    ("Choose all correct options", "एक से ज़्यादा सही विकल्प चुनो"),
    ("Numerical answer", "संख्यात्मक उत्तर"),
    ("Fill in the blank", "खाली जगह भरो"),
    ("Write your answer (1-3 lines)", "अपना उत्तर लिखो (1-3 पंक्तियाँ)"),
    ("✖ Quit quiz", "✖ क्विज़ छोड़ो"),
    ("💡 Hint (−5 XP)", "💡 संकेत (−5 XP)"),
    ("🧠 Explain in more detail", "🧠 और विस्तार से समझाओ"),
    ("⬅️ Back", "⬅️ पीछे"),
    ("Check answer", "उत्तर जाँचो"),
    ("Skip ⏭️", "छोड़ो ⏭️"),
    ("## 📇 Flashcards", "## 📇 फ़्लैशकार्ड"),
    ("🔁 New quiz", "🔁 नया क्विज़"),
    ("🎯 Redo only wrong ones", "🎯 सिर्फ़ गलत दोबारा"),
    ("🔄 Same quiz again", "🔄 वही क्विज़ फिर से"),
    ("🆕 New questions (same source)", "🆕 नए प्रश्न (वही स्रोत)"),
    ("📇 Flashcards of this quiz", "📇 इस क्विज़ के फ़्लैशकार्ड"),
    ("### 📊 Topic-wise performance", "### 📊 टॉपिक-वार प्रदर्शन"),
    ("🧭 Make AI study plan", "🧭 AI स्टडी प्लान बनाओ"),
    ("### 🔍 Review", "### 🔍 समीक्षा"),
    ("### 📥 Download", "### 📥 डाउनलोड"),
]

KEYS = {
    "app_tag": {
        "en": "Provide a topic, PDF or notes photo — AI generates quizzes instantly.",
        "hi": "टॉपिक, PDF या नोट्स की फ़ोटो दो — AI तुरंत क्विज़ बनाता है।"
    },
    "app_language": {"en": "🌐 App language", "hi": "🌐 ऐप की भाषा"},
    "account": {"en": "### 👤 My account", "hi": "### 👤 मेरा अकाउंट"},
    "logout": {"en": "🚪 Log out", "hi": "🚪 लॉगआउट"},
}

_LOOKUP = {src: hi for src, hi in TABLE}

def cur():
    try:
        return st.session_state.get("ui_lang", DEFAULT)
    except Exception:
        return DEFAULT

def init_ui_lang():
    if "ui_lang" not in st.session_state:
        st.session_state["ui_lang"] = DEFAULT

def set_ui_lang(lang_code):
    st.session_state["ui_lang"] = lang_code

def tr(s):
    if not isinstance(s, str):
        return s
    lang = cur()
    if lang == "en":
        return s
    return _LOOKUP.get(s, s)

def t(key, **fmt):
    row = KEYS.get(key, {})
    txt = row.get(cur(), row.get("en", key))
    return txt.format(**fmt) if fmt else txt

def all_forms():
    return []

# Monkey-patching Streamlit UI elements for automatic translation
_TEXT_FIRST = (
    "markdown", "caption", "success", "info", "warning", "error", "subheader", "header", "title",
    "button", "download_button", "form_submit_button", "toggle", "checkbox", "slider", "select_slider",
    "selectbox", "radio", "multiselect", "text_input", "text_area", "number_input", "file_uploader",
    "camera_input", "expander", "spinner", "progress",
)
_OPTION_WIDGETS = ("selectbox", "radio", "multiselect", "select_slider")
_STR_KWARGS = ("help", "placeholder", "text", "label")

def _fmt_func(o):
    return tr(str(o))

def _wrap(fn, name, is_method):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        if cur() == "hi":
            args = list(args)
            pos = 1 if is_method else 0
            if name == "tabs":
                if len(args) > pos and isinstance(args[pos], (list, tuple)):
                    args[pos] = [tr(x) for x in args[pos]]
            else:
                if len(args) > pos:
                    args[pos] = tr(args[pos])
                for k in _STR_KWARGS:
                    if isinstance(kwargs.get(k), str):
                        kwargs[k] = tr(kwargs[k])
                if name in _OPTION_WIDGETS and "format_func" not in kwargs and len(args) <= pos + 3:
                    kwargs["format_func"] = _fmt_func
        return fn(*args, **kwargs)

    inner._qf_wrapped = True
    return inner

def install():
    if getattr(st, "_qf_i18n_installed", False):
        return
    try:
        from streamlit.delta_generator import DeltaGenerator
    except Exception:
        DeltaGenerator = None

    for name in _TEXT_FIRST + ("tabs",):
        try:
            f = getattr(st, name)
            if not getattr(f, "_qf_wrapped", False):
                setattr(st, name, _wrap(f, name, False))
        except Exception:
            pass

        if DeltaGenerator is not None:
            try:
                m = getattr(DeltaGenerator, name)
                if not getattr(m, "_qf_wrapped", False):
                    setattr(DeltaGenerator, name, _wrap(m, name, True))
            except Exception:
                pass
    st._qf_i18n_installed = True

install()
