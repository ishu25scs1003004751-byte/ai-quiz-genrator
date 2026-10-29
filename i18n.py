"""
i18n.py — Complete language translation module for AI Quiz Arena.
"""
import functools
import streamlit as st

# Service & Info Constants
ADMIN_HELP = "🛠️ Admin: Shared PYQ bank me sawal upload/manage kar sakte hain."
EMAIL_SVC_MSG = "Email OTP service active hai."
SVC_MSG = "System operational."

LANGS = {"Hinglish": "hg", "English": "en", "हिन्दी": "hi"}
LANG_ORDER = ["Hinglish", "English", "हिन्दी"]
DEFAULT = "hg"

QUIZ_LANG_OF = {
    "hg": "Hinglish",
    "en": "English",
    "hi": "Hindi",
    "Hinglish": "Hinglish",
    "English": "English",
    "हिन्दी": "Hindi"
}

# Source Translation Mapping
TABLE = [
    # ── sidebar ──
    ("### ⚙️ Quiz Settings", None, "### ⚙️ क्विज़ सेटिंग्स"),
    ("Questions", None, "प्रश्नों की संख्या"),
    ("10 se zyada sawal batches me bante hain, thoda time lag sakta hai.", "Over 10 questions are made in batches, so it can take a little longer.", "10 से ज़्यादा प्रश्न बैच में बनते हैं, थोड़ा समय लग सकता है।"),
    ("Difficulty", None, "कठिनाई"),
    ("Easy", None, "आसान"),
    ("Medium", None, "मध्यम"),
    ("Hard", None, "कठिन"),
    ("🎚️ Adaptive difficulty", None, "🎚️ अनुकूल कठिनाई"),
    ("Sahi karte jao to sawal mushkil, galat par aasaan hote jayenge.", "Questions get harder when you answer right and easier when you miss.", "सही करते जाओगे तो प्रश्न कठिन, गलत पर आसान होते जाएँगे।"),
    ("Question types", None, "प्रश्नों के प्रकार"),
    ("Language", "Quiz language", "क्विज़ की भाषा"),
    ("Hindi", None, "हिन्दी"),
    ("Mode", None, "मोड"),
    ("Practice: har sawal ke baad turant answer.\nExam: result end me.\nSurvival: sirf 3 lives — 3 galat answer par game over!",
     "Practice: instant answer after every question.\nExam: result at the end.\nSurvival: only 3 lives — 3 wrong answers and it's game over!",
     "प्रैक्टिस: हर प्रश्न के बाद तुरंत उत्तर।\nएग्ज़ाम: परिणाम अंत में।\nसर्वाइवल: सिर्फ़ 3 जीवन — 3 गलत उत्तर पर गेम ओवर!"),
    ("Practice", None, "प्रैक्टिस"),
    ("Exam", None, "एग्ज़ाम"),
    ("Survival", None, "सर्वाइवल"),
    ("**⏱️ Timer**", None, "**⏱️ टाइमर**"),
    ("Timer type", None, "टाइमर का प्रकार"),
    ("Off", None, "बंद"),
    ("Har sawal par", "Per question", "हर प्रश्न पर"),
    ("Poore quiz ka", "Whole quiz", "पूरे क्विज़ का"),
    ("Seconds per sawal", "Seconds per question", "प्रति प्रश्न सेकंड"),
    ("Minutes (poore quiz ke)", "Minutes (whole quiz)", "मिनट (पूरे क्विज़ के)"),
    ("Custom", None, "कस्टम"),
    ("Custom seconds", None, "कस्टम सेकंड"),
    ("Custom minutes", None, "कस्टम मिनट"),
    ("Time khatam hote hi answer auto-submit ho jata hai.", "The answer is submitted automatically when time runs out.", "समय खत्म होते ही उत्तर अपने आप जमा हो जाता है।"),
    ("Timer ke liye Streamlit ≥ 1.37 chahiye.", "The timer needs Streamlit ≥ 1.37.", "टाइमर के लिए Streamlit ≥ 1.37 चाहिए।"),
    ("**🎯 Marking**", None, "**🎯 अंकन**"),
    ("Marks per sahi answer", "Marks per correct answer", "प्रति सही उत्तर अंक"),
    ("Negative marking (galat par)", "Negative marking (on wrong)", "नेगेटिव मार्किंग (गलत पर)"),
    ("Galat answer par sahi-marks ka itna hissa katega. Skip par 0. Short answer me partial marks milte hain, negative nahi.",
     "A wrong answer loses this fraction of the marks. Skipped = 0. Short answers get partial marks, never negative.",
     "गलत उत्तर पर सही-अंकों का इतना हिस्सा कटेगा। छोड़ने पर 0। छोटे उत्तर में आंशिक अंक मिलते हैं, नेगेटिव नहीं।"),
    ("Nahi", "None", "नहीं"),
    ("🔊 Awaaz & Look", "🔊 Sound & Look", "🔊 आवाज़ और लुक"),
    ("Sound effects", None, "साउंड इफ़ेक्ट"),
    ("Sawal khud padhkar sunao", "Read questions aloud automatically", "प्रश्न खुद पढ़कर सुनाओ"),
    ("Agar awaaz na aaye to pehle page par ek click karo ya 🔊 button dabao.", "If there's no sound, click once on the page or press the 🔊 button.", "अगर आवाज़ न आए तो पहले पेज पर एक क्लिक करो या 🔊 बटन दबाओ।"),
    ("Bolne ki speed", "Speaking speed", "बोलने की गति"),
    ("☀️ Light mode", None, "☀️ लाइट मोड"),
    ("Advanced", None, "उन्नत"),
    ("AI model", None, "AI मॉडल"),
    ("120b = sabse accurate. 8b-instant = sabse fast.", "120b = most accurate. 8b-instant = fastest.", "120b = सबसे सटीक। 8b-instant = सबसे तेज़।"),
    ("### 🔖 Saved questions", None, "### 🔖 सहेजे हुए प्रश्न"),
    ("Quiz ke dauran 🔖 dabao, sawal yahan save ho jayega.", "Press 🔖 during a quiz and the question is saved here.", "क्विज़ के दौरान 🔖 दबाओ, प्रश्न यहाँ सहेज जाएगा।"),
    ("📇 Flashcards se padho", "📇 Study with flashcards", "📇 फ़्लैशकार्ड से पढ़ो"),
    ("### 🏆 Meri History", "### 🏆 My History", "### 🏆 मेरी हिस्ट्री"),
    ("Clear history", None, "हिस्ट्री साफ़ करो"),
    ("Abhi koi quiz nahi diya. Pehla quiz banao!", "No quiz taken yet. Make your first one!", "अभी कोई क्विज़ नहीं दिया। पहला क्विज़ बनाओ!"),
    ("### 💾 Progress backup", None, "### 💾 प्रोग्रेस बैकअप"),
    ("Tumhara XP, history aur saved sawal account me apne aap save hote hain. Chaho to yahan file backup bhi rakh sakte ho.",
     "Your XP, history and saved questions are saved to your account automatically. You can also keep a file backup here.",
     "आपका XP, हिस्ट्री और सहेजे प्रश्न आपके अकाउंट में अपने आप सेव होते हैं। यहाँ फ़ाइल बैकअप भी रख सकते हैं।"),
    ("⬇️ Progress save karo", "⬇️ Download progress", "⬇️ प्रोग्रेस डाउनलोड करो"),
    ("Progress load karo", "Load progress", "प्रोग्रेस लोड करो"),
    # ── tabs / setup ──
    ("🧠 Quiz Arena", None, "🧠 क्विज़ एरीना"),
    ("🏛️ Govt Exam PYQs", None, "🏛️ सरकारी परीक्षा PYQ"),
    ("🔍 Doubt Solver", None, "🔍 डाउट सॉल्वर"),
    ("Content kahan se aayega?", "Where will the content come from?", "सामग्री कहाँ से आएगी?"),
    ("💡 Topic", None, "💡 टॉपिक"),
    ("📄 PDF", None, "📄 PDF"),
    ("🖼️ Photo / Camera", None, "🖼️ फ़ोटो / कैमरा"),
    ("📝 Notes", None, "📝 नोट्स"),
    ("Kis topic par quiz chahiye?", "Which topic do you want a quiz on?", "किस टॉपिक पर क्विज़ चाहिए?"),
    ("e.g. Machine Learning basics, Indian Constitution, Python lists…", None, "जैसे: मशीन लर्निंग बेसिक्स, भारतीय संविधान, Python lists…"),
    ("Quick picks", None, "त्वरित चुनाव"),
    ("PDF upload karo", "Upload a PDF", "PDF अपलोड करो"),
    ("Page range", None, "पेज रेंज"),
    ("Photo upload karo ya camera se seedha click karo.", "Upload a photo or click one directly with the camera.", "फ़ोटो अपलोड करो या कैमरे से सीधे क्लिक करो।"),
    ("Photo mode", None, "फ़ोटो मोड"),
    ("📁 Upload File", None, "📁 फ़ाइल अपलोड"),
    ("📸 Live Camera Click", None, "📸 लाइव कैमरा क्लिक"),
    ("Photo upload karo", "Upload a photo", "फ़ोटो अपलोड करो"),
    ("Live photo click karo", "Take a live photo", "लाइव फ़ोटो खींचो"),
    ("Apne notes / article yahan paste karo", "Paste your notes / article here", "अपने नोट्स / लेख यहाँ पेस्ट करो"),
    ("Chapter ka text, notes, ya koi bhi article…", "Chapter text, notes or any article…", "अध्याय का टेक्स्ट, नोट्स या कोई भी लेख…"),
    ("✨ Quiz banao", "✨ Make quiz", "✨ क्विज़ बनाओ"),
    ("Pehle topic likho, photo upload/click karo ya notes paste karo.", "First write a topic, upload/click a photo or paste notes.", "पहले टॉपिक लिखो, फ़ोटो अपलोड/क्लिक करो या नोट्स पेस्ट करो।"),
    ("AI sawal bana raha hai…", "AI is making questions…", "AI प्रश्न बना रहा है…"),
    ("Sawal ban rahe hain…", "Making questions…", "प्रश्न बन रहे हैं…"),
    ("Valid sawal nahi ban paye. Dobara try karo.", "Couldn't make valid questions. Please try again.", "सही प्रश्न नहीं बन पाए। दोबारा कोशिश करो।"),
    ("AI ka response samajh nahi aaya. Dobara try karo ya doosra model chuno.", "Couldn't understand the AI response. Try again or pick another model.", "AI का जवाब समझ नहीं आया। दोबारा कोशिश करो या दूसरा मॉडल चुनो।"),
    ("Is PDF se text nahi nikla (scanned lagta hai). Uske page ki **photo** lekar try karo.", "No text found in this PDF (looks scanned). Try a **photo** of the page.", "इस PDF से टेक्स्ट नहीं निकला (स्कैन लगता है)। उस पेज की **फ़ोटो** लेकर देखो।"),
    ("Photo 15 MB se badi hai. Chhoti photo use karo.", "The photo is over 15 MB. Use a smaller one.", "फ़ोटो 15 MB से बड़ी है। छोटी फ़ोटो इस्तेमाल करो।"),
    ("Photo compress hone ke baad bhi bahut badi hai. Kam resolution ki photo lo.", "Still too big after compression. Use a lower-resolution photo.", "कंप्रेस होने के बाद भी बहुत बड़ी है। कम रेज़ोल्यूशन की फ़ोटो लो।"),
    # ── govt exams ──
    ("### 🏛️ Govt & Entrance Exam Practice", None, "### 🏛️ सरकारी एवं प्रवेश परीक्षा अभ्यास"),
    ("Target exam", None, "लक्ष्य परीक्षा"),
    ("Subject", None, "विषय"),
    ("Year (optional)", None, "वर्ष (वैकल्पिक)"),
    ("Dataset me kam pade to AI se bharo", "Fill the rest with AI if the dataset runs short", "डेटासेट में कम पड़े तो AI से भरो"),
    ("Marking scheme", None, "अंकन योजना"),
    ("📋 Official (exam jaisi)", "📋 Official (as in the exam)", "📋 आधिकारिक (परीक्षा जैसी)"),
    ("⚙️ Sidebar wali", "⚙️ From sidebar", "⚙️ साइडबार वाली"),
    ("Negative marking", None, "नेगेटिव मार्किंग"),
    ("📝 Full mock test (exam jaisa pattern + timer)", "📝 Full mock test (exam pattern + timer)", "📝 पूरा मॉक टेस्ट (परीक्षा जैसा पैटर्न + टाइमर)"),
    ("➕ Apna PYQ dataset jodo (JSON / CSV)", "➕ Add your own PYQ dataset (JSON / CSV)", "➕ अपना PYQ डेटासेट जोड़ो (JSON / CSV)"),
    ("📄 Template (JSON)", None, "📄 टेम्पलेट (JSON)"),
    ("PYQ file", None, "PYQ फ़ाइल"),
    ("🗑️ Uploaded PYQ hatao", "🗑️ Remove uploaded PYQs", "🗑️ अपलोड किए PYQ हटाओ"),
    ("Sawal taiyaar ho rahe hain…", "Preparing questions…", "प्रश्न तैयार हो रहे हैं…"),
    # ── doubt solver ──
    ("### 🔍 AI Doubt Solver", None, "### 🔍 AI डाउट सॉल्वर"),
    ("Jawab ki bhasha", "Answer language", "उत्तर की भाषा"),
    ("Style", None, "शैली"),
    ("Doubt kaise poochna hai?", "How do you want to ask?", "डाउट कैसे पूछना है?"),
    ("📝 Text", None, "📝 टेक्स्ट"),
    ("📸 Live Camera", None, "📸 लाइव कैमरा"),
    ("🖼️ Photo Upload", None, "🖼️ फ़ोटो अपलोड"),
    ("Apna doubt yahan likho", "Write your doubt here", "अपना डाउट यहाँ लिखो"),
    ("Question ki live photo click karo", "Take a live photo of the question", "प्रश्न की लाइव फ़ोटो खींचो"),
    ("💡 Samjhao", "💡 Explain", "💡 समझाओ"),
    ("Pehle doubt likho ya photo do.", "First write a doubt or give a photo.", "पहले डाउट लिखो या फ़ोटो दो।"),
    ("🔁 Jawab dobara generate karo", "🔁 Regenerate answer", "🔁 उत्तर दोबारा बनाओ"),
    ("Follow-up poochho", "Ask a follow-up", "फ़ॉलो-अप पूछो"),
    ("Bhejo ➤", "Send ➤", "भेजो ➤"),
    ("🧹 Naya doubt", "🧹 New doubt", "🧹 नया डाउट"),
    ("📝 Is par quiz banao", "📝 Make a quiz on this", "📝 इस पर क्विज़ बनाओ"),
    ("⬇️ Notes (.md)", None, "⬇️ नोट्स (.md)"),
    ("Soch raha hoon…", "Thinking…", "सोच रहा हूँ…"),
    # ── quiz stage ──
    ("Apna answer chuno", "Choose your answer", "अपना उत्तर चुनो"),
    ("Ek se zyada sahi options chuno", "Choose all correct options", "एक से ज़्यादा सही विकल्प चुनो"),
    ("Numerical answer", None, "संख्यात्मक उत्तर"),
    ("Khali jagah bharo", "Fill in the blank", "खाली जगह भरो"),
    ("Apna answer likho (1-3 line)", "Write your answer (1-3 lines)", "अपना उत्तर लिखो (1-3 पंक्तियाँ)"),
    ("✖ Quiz chhodo", "✖ Quit quiz", "✖ क्विज़ छोड़ो"),
    ("💡 Hint (−5 XP)", None, "💡 संकेत (−5 XP)"),
    ("🧠 Aur detail me samjhao", "🧠 Explain in more detail", "🧠 और विस्तार से समझाओ"),
    ("⬅️ Back", None, "⬅️ पीछे"),
    ("Check answer", None, "उत्तर जाँचो"),
    ("Skip ⏭️", None, "छोड़ो ⏭️"),
    ("## 📇 Flashcards", None, "## 📇 फ़्लैशकार्ड"),
    ("🔁 Naya quiz", "🔁 New quiz", "🔁 नया क्विज़"),
    ("🎯 Sirf galat dobara", "🎯 Redo only wrong ones", "🎯 सिर्फ़ गलत दोबारा"),
    ("🔄 Wahi quiz phir se", "🔄 Same quiz again", "🔄 वही क्विज़ फिर से"),
    ("🆕 Naye sawal (same source)", "🆕 New questions (same source)", "🆕 नए प्रश्न (वही स्रोत)"),
    ("📇 Is quiz ke flashcards", "📇 Flashcards of this quiz", "📇 इस क्विज़ के फ़्लैशकार्ड"),
    ("### 📊 Topic-wise performance", None, "### 📊 टॉपिक-वार प्रदर्शन"),
    ("🧭 AI study plan banao", "🧭 Make AI study plan", "🧭 AI स्टडी प्लान बनाओ"),
    ("### 🔍 Review", None, "### 🔍 समीक्षा"),
    ("### 📥 Download", None, "### 📥 डाउनलोड"),
]

KEYS = {
    "app_tag": {
        "hg": "Topic, PDF ya notes ki photo do — AI turant quiz banata hai.",
        "en": "Provide a topic, PDF or notes photo — AI generates quizzes instantly.",
        "hi": "टॉपिक, PDF या नोट्स की फ़ोटो दो — AI तुरंत क्विज़ बनाता है।"
    },
    "app_language": {"hg": "🌐 App ki bhasha", "en": "🌐 App language", "hi": "🌐 ऐप की भाषा"},
    "account": {"hg": "### 👤 Mera account", "en": "### 👤 My account", "hi": "### 👤 मेरा अकाउंट"},
    "logout": {"hg": "🚪 Logout", "en": "🚪 Log out", "hi": "🚪 लॉगआउट"},
}

_LOOKUP = {}
for _src, _en, _hi in TABLE:
    _LOOKUP[_src] = {"en": _en if _en is not None else _src, "hi": _hi if _hi is not None else _src}

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
    if lang == DEFAULT:
        return s
    row = _LOOKUP.get(s)
    return row[lang] if row and lang in row else s

def t(key, **fmt):
    row = KEYS.get(key, {})
    txt = row.get(cur()) or row.get("hg", key)
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
        if cur() != DEFAULT:
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

# Auto-install wrapper upon module import
install()
