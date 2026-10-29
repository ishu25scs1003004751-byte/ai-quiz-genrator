"""App-wide UI language support (Hinglish / English / हिन्दी).

Usage in app.py:
    tr("Hinglish text")                 -> text in the user's chosen UI language
    tr("Score: {n}", n=5)               -> same, with .format() applied afterwards
    format_func=tr                      -> translate option labels but keep option VALUES unchanged

The Hinglish text itself is the dictionary key (that is what the app was originally written in).
If a text has no entry it is shown as-is, so a missing translation never crashes the app.
"""
import streamlit as st

LANGS = {"hinglish": "Hinglish", "en": "English", "hi": "हिन्दी"}
LANG_ORDER = list(LANGS)
DEFAULT_LANG = "hinglish"
QUIZ_LANG_OF = {"hinglish": "Hinglish", "en": "English", "hi": "Hindi"}  # default AI-quiz language per UI language

# Widget keys whose value must survive a language switch (Streamlit resets a widget when its label changes).
_SNAP_KEYS = {
    "num_q", "diff_sel", "adaptive_t", "type_sel", "quiz_lang", "mode_sel", "timer_mode", "per_q_pick", "per_q_custom",
    "quiz_pick", "quiz_custom", "marks_sel", "neg_sel", "sound_on", "auto_read", "tts_rate", "light", "model_sel",
    "src_choice", "topic_in", "page_rng", "notes_in", "quiz_photo_mode", "pyq_exam", "d_lang", "d_depth", "d_src",
    "d_txt", "d_img_txt", "d_pdf_txt", "more_n", "login_tab", "login_ch", "login_id_email", "login_id_phone",
    "pw_mode", "pw_email",
}
_SNAP_PREFIXES = ("pyq_subject_", "pyq_years_", "pyq_fill_", "pyq_mark_", "pyq_neg_", "pyq_numneg_", "pyq_pattern_", "pyq_size_")


def ui_lang() -> str:
    return st.session_state.get("lang_ui", DEFAULT_LANG)


def init_ui_lang():
    """Call once at the top of every script run (before any tr())."""
    ss = st.session_state
    if "lang_ui" not in ss:
        code = None
        try:
            code = st.query_params.get("lang")
        except Exception:
            pass
        ss["lang_ui"] = code if code in LANGS else DEFAULT_LANG
    snap = ss.pop("_lang_snap", None)
    if snap:  # put back the widget values saved by set_ui_lang()
        for k, v in snap.items():
            try:
                ss[k] = v
            except Exception:
                pass


def set_ui_lang(code):
    """on_change callback of the language selectors."""
    ss = st.session_state
    if code not in LANGS:
        return
    snap = {}
    for k in list(ss.keys()):
        if isinstance(k, str) and (k in _SNAP_KEYS or k.startswith(_SNAP_PREFIXES)):
            try:
                snap[k] = ss[k]
            except Exception:
                pass
    snap["quiz_lang"] = QUIZ_LANG_OF[code]  # AI quiz language follows the app language
    ss["_lang_snap"] = snap
    ss["lang_ui"] = code
    try:
        st.query_params["lang"] = code
    except Exception:
        pass


def tr(text, **kw):
    if not isinstance(text, str):
        return str(text)
    s = text
    lang = ui_lang()
    if lang != "hinglish":
        pair = STR.get(text)
        if pair:
            s = pair[0] if lang == "en" else pair[1]
    if kw:
        try:
            s = s.format(**kw)
        except Exception:
            pass
    return s


def all_forms(text):
    """Every language version of a text (used for the keyboard-shortcut button matching)."""
    return (text,) + tuple(STR.get(text, ()))


# key (Hinglish) : (English, हिन्दी)
STR = {
    # ───────── generic / backend messages ─────────
    "Groq ki rate limit lag gayi. 20-30 second ruk kar dobara try karo, ya chhota model chuno.": (
        "Groq rate limit reached. Wait 20-30 seconds and try again, or pick a smaller model.",
        "Groq की रेट लिमिट लग गई। 20-30 सेकंड रुककर फिर कोशिश करो, या छोटा मॉडल चुनो।"),
    "API key galat lag rahi hai. Secrets me `GROQ_API_KEY` check karo.": (
        "The API key looks wrong. Check `GROQ_API_KEY` in Secrets.",
        "API key गलत लग रही है। Secrets में `GROQ_API_KEY` जाँचो।"),
    "Ye model abhi available nahi hai. Sidebar → Advanced me doosra model chuno.": (
        "This model is not available right now. Pick another model in Sidebar → Advanced.",
        "यह मॉडल अभी उपलब्ध नहीं है। साइडबार → Advanced में दूसरा मॉडल चुनो।"),
    "Error: {msg}": ("Error: {msg}", "त्रुटि: {msg}"),
    "API key nahi mili. Streamlit Cloud ke **Secrets** me `GROQ_API_KEY` add karein.": (
        "API key not found. Add `GROQ_API_KEY` in your Streamlit Cloud **Secrets**.",
        "API key नहीं मिली। Streamlit Cloud के **Secrets** में `GROQ_API_KEY` जोड़ें।"),
    "Explanation available nahi hai.": ("No explanation available.", "स्पष्टीकरण उपलब्ध नहीं है।"),
    "Koi answer nahi likha.": ("No answer was written.", "कोई उत्तर नहीं लिखा।"),
    "AI grading nahi ho paya — sahi answer se khud compare karo.": (
        "AI grading failed — compare with the correct answer yourself.",
        "AI ग्रेडिंग नहीं हो पाई — सही उत्तर से खुद मिलाओ।"),
    "Short answers check ho rahe hain…": ("Checking short answers…", "छोटे उत्तर जाँचे जा रहे हैं…"),
    "Is sawal ka explanation dataset me nahi hai.": (
        "This question has no explanation in the dataset.", "इस प्रश्न का स्पष्टीकरण डेटासेट में नहीं है।"),
    "File ka format galat hai.": ("The file format is wrong.", "फ़ाइल का फ़ॉर्मैट गलत है।"),

    # badges
    "💎 Perfect Score": ("💎 Perfect Score", "💎 पूरे अंक"),
    "🔥 Streak Master": ("🔥 Streak Master", "🔥 स्ट्रीक मास्टर"),
    "⚡ Speedster": ("⚡ Speedster", "⚡ तेज़ रफ़्तार"),
    "🧘 No Hints Needed": ("🧘 No Hints Needed", "🧘 बिना संकेत के"),
    "🦾 Hard Mode Hero": ("🦾 Hard Mode Hero", "🦾 हार्ड मोड हीरो"),
    "🛡️ Survivor": ("🛡️ Survivor", "🛡️ सर्वाइवर"),
    "🧩 All-rounder": ("🧩 All-rounder", "🧩 ऑल-राउंडर"),
    "📚 Regular Learner": ("📚 Regular Learner", "📚 नियमित विद्यार्थी"),

    # exam notes
    "Tier-I: 100 sawal, 60 min, +2 / −0.5.": ("Tier-I: 100 questions, 60 min, +2 / −0.5.", "टियर-I: 100 प्रश्न, 60 मिनट, +2 / −0.5।"),
    "CBT-1: 100 sawal, 90 min, +1 / −⅓.": ("CBT-1: 100 questions, 90 min, +1 / −⅓.", "CBT-1: 100 प्रश्न, 90 मिनट, +1 / −⅓।"),
    "Prelims: 100 sawal, 60 min, +1 / −¼.": ("Prelims: 100 questions, 60 min, +1 / −¼.", "प्रिलिम्स: 100 प्रश्न, 60 मिनट, +1 / −¼।"),
    "150 sawal, 120 min, +2 / −0.5. Sources me farak hai (kuch −0.25 ya negative nahi likhte) — apni notification dekh kar adjust karo.": (
        "150 questions, 120 min, +2 / −0.5. Sources differ (some say −0.25 or no negative) — adjust as per your notification.",
        "150 प्रश्न, 120 मिनट, +2 / −0.5। स्रोतों में फर्क है (कुछ −0.25 या नेगेटिव नहीं लिखते) — अपनी नोटिफिकेशन देखकर बदलो।"),
    "GS Paper-I jaisa: 100 sawal, 120 min, +2 / −⅓. Subject-wise ginti approximate hai.": (
        "Like GS Paper-I: 100 questions, 120 min, +2 / −⅓. Subject-wise counts are approximate.",
        "GS पेपर-I जैसा: 100 प्रश्न, 120 मिनट, +2 / −⅓। विषय-वार गिनती अनुमानित है।"),
    "2026 bulletin: 120 sawal, 140 min, +1, koi negative marking nahi.": (
        "2026 bulletin: 120 questions, 140 min, +1, no negative marking.",
        "2026 बुलेटिन: 120 प्रश्न, 140 मिनट, +1, कोई नेगेटिव मार्किंग नहीं।"),
    "180 sawal (sab compulsory), 180 min, +4 / −1, 720 marks.": (
        "180 questions (all compulsory), 180 min, +4 / −1, 720 marks.", "180 प्रश्न (सब अनिवार्य), 180 मिनट, +4 / −1, 720 अंक।"),
    "Paper-1: 75 sawal (har subject me 20 MCQ + 5 numerical), 180 min, +4 / −1, 300 marks. Numerical par negative ko lekar sources me farak hai — neeche toggle se chuno.": (
        "Paper-1: 75 questions (20 MCQ + 5 numerical per subject), 180 min, +4 / −1, 300 marks. Sources differ on negative marking for numericals — choose with the toggle below.",
        "पेपर-1: 75 प्रश्न (हर विषय में 20 MCQ + 5 न्यूमेरिकल), 180 मिनट, +4 / −1, 300 अंक। न्यूमेरिकल पर नेगेटिव को लेकर स्रोतों में फर्क है — नीचे टॉगल से चुनो।"),

    # ───────── sidebar ─────────
    "🌐 App language": ("🌐 App language", "🌐 ऐप की भाषा"),
    "🎖️ Level {n}": ("🎖️ Level {n}", "🎖️ स्तर {n}"),
    "{xp} XP · agle level tak {left}": ("{xp} XP · {left} to next level", "{xp} XP · अगले स्तर तक {left}"),
    "### ⚙️ Quiz Settings": ("### ⚙️ Quiz Settings", "### ⚙️ क्विज़ सेटिंग्स"),
    "Questions": ("Questions", "प्रश्न"),
    "10 se zyada sawal batches me bante hain, thoda time lag sakta hai.": (
        "More than 10 questions are made in batches, it may take a little longer.",
        "10 से ज़्यादा प्रश्न बैच में बनते हैं, थोड़ा समय लग सकता है।"),
    "Difficulty": ("Difficulty", "कठिनाई"),
    "Easy": ("Easy", "आसान"), "Medium": ("Medium", "मध्यम"), "Hard": ("Hard", "कठिन"),
    "🎚️ Adaptive difficulty": ("🎚️ Adaptive difficulty", "🎚️ अनुकूली कठिनाई"),
    "Sahi karte jao to sawal mushkil, galat par aasaan hote jayenge.": (
        "Questions get harder as you answer correctly and easier when you go wrong.",
        "सही करते जाओगे तो प्रश्न कठिन, गलत पर आसान होते जाएँगे।"),
    "Question types": ("Question types", "प्रश्न के प्रकार"),
    "Multiple Choice": ("Multiple Choice", "बहुविकल्पीय"),
    "True / False": ("True / False", "सही / गलत"),
    "Multi-select": ("Multi-select", "एक से ज़्यादा सही"),
    "Fill in the blank": ("Fill in the blank", "रिक्त स्थान भरो"),
    "Short answer (AI check)": ("Short answer (AI check)", "छोटा उत्तर (AI जाँच)"),
    "Numerical value": ("Numerical value", "संख्यात्मक उत्तर"),
    "Quiz language": ("Quiz language", "क्विज़ की भाषा"),
    "AI is language me sawal, options aur explanation likhega.": (
        "The AI will write questions, options and explanations in this language.",
        "AI इसी भाषा में प्रश्न, विकल्प और स्पष्टीकरण लिखेगा।"),
    "Mode": ("Mode", "मोड"),
    "Practice": ("Practice", "प्रैक्टिस"), "Exam": ("Exam", "परीक्षा"), "Survival": ("Survival", "सर्वाइवल"),
    "Practice: har sawal ke baad turant answer.\nExam: result end me.\nSurvival: sirf 3 lives — 3 galat answer par game over!": (
        "Practice: instant answer after every question.\nExam: result at the end.\nSurvival: only 3 lives — game over after 3 wrong answers!",
        "प्रैक्टिस: हर प्रश्न के बाद तुरंत उत्तर।\nपरीक्षा: रिज़ल्ट अंत में।\nसर्वाइवल: सिर्फ़ 3 जान — 3 गलत उत्तर पर गेम ओवर!"),
    "**⏱️ Timer**": ("**⏱️ Timer**", "**⏱️ टाइमर**"),
    "Timer type": ("Timer type", "टाइमर का प्रकार"),
    "Off": ("Off", "बंद"), "Har sawal par": ("Per question", "हर प्रश्न पर"), "Poore quiz ka": ("Whole quiz", "पूरे क्विज़ का"),
    "Seconds per sawal": ("Seconds per question", "प्रति प्रश्न सेकंड"),
    "Custom": ("Custom", "कस्टम"),
    "Custom seconds": ("Custom seconds", "कस्टम सेकंड"),
    "Time khatam hote hi answer auto-submit ho jata hai.": (
        "The answer is auto-submitted when time runs out.", "समय खत्म होते ही उत्तर अपने आप सबमिट हो जाता है।"),
    "Minutes (poore quiz ke)": ("Minutes (whole quiz)", "मिनट (पूरे क्विज़ के)"),
    "Custom minutes": ("Custom minutes", "कस्टम मिनट"),
    "≈ {s} sec per sawal. Time khatam to quiz apne aap submit.": (
        "≈ {s} sec per question. The quiz is auto-submitted when time ends.",
        "≈ {s} सेकंड प्रति प्रश्न। समय खत्म होने पर क्विज़ अपने आप सबमिट।"),
    "Timer ke liye Streamlit ≥ 1.37 chahiye.": ("The timer needs Streamlit ≥ 1.37.", "टाइमर के लिए Streamlit ≥ 1.37 चाहिए।"),
    "**🎯 Marking**": ("**🎯 Marking**", "**🎯 मार्किंग**"),
    "Marks per sahi answer": ("Marks per correct answer", "प्रति सही उत्तर अंक"),
    "Negative marking (galat par)": ("Negative marking (for wrong)", "नेगेटिव मार्किंग (गलत पर)"),
    "Nahi": ("None", "नहीं"),
    "Galat answer par sahi-marks ka itna hissa katega. Skip par 0. Short answer me partial marks milte hain, negative nahi.": (
        "This fraction of the correct-marks is deducted for a wrong answer. Skip = 0. Short answers get partial marks, never negative.",
        "गलत उत्तर पर सही-अंक का इतना हिस्सा कटेगा। स्किप पर 0। छोटे उत्तर में आंशिक अंक मिलते हैं, नेगेटिव नहीं।"),
    "+{a} sahi · −{b} galat · 0 skip": ("+{a} correct · −{b} wrong · 0 skip", "+{a} सही · −{b} गलत · 0 स्किप"),
    "🔊 Awaaz & Look": ("🔊 Sound & Look", "🔊 आवाज़ और लुक"),
    "Sound effects": ("Sound effects", "साउंड इफ़ेक्ट"),
    "Sawal khud padhkar sunao": ("Read the question aloud automatically", "प्रश्न खुद पढ़कर सुनाओ"),
    "Agar awaaz na aaye to pehle page par ek click karo ya 🔊 button dabao.": (
        "If you hear no sound, click once on the page first or press the 🔊 button.",
        "अगर आवाज़ न आए तो पहले पेज पर एक क्लिक करो या 🔊 बटन दबाओ।"),
    "Bolne ki speed": ("Speaking speed", "बोलने की गति"),
    "☀️ Light mode": ("☀️ Light mode", "☀️ लाइट मोड"),
    "Advanced": ("Advanced", "एडवांस्ड"),
    "AI model": ("AI model", "AI मॉडल"),
    "120b = sabse accurate. 8b-instant = sabse fast.": (
        "120b = most accurate. 8b-instant = fastest.", "120b = सबसे सटीक। 8b-instant = सबसे तेज़।"),
    "### 🔖 Saved questions": ("### 🔖 Saved questions", "### 🔖 सेव किए प्रश्न"),
    "{n} question(s) saved": ("{n} question(s) saved", "{n} प्रश्न सेव हैं"),
    "📇 Flashcards se padho": ("📇 Study with flashcards", "📇 फ्लैशकार्ड से पढ़ो"),
    "Quiz ke dauran 🔖 dabao, sawal yahan save ho jayega.": (
        "Press 🔖 during a quiz and the question will be saved here.", "क्विज़ के दौरान 🔖 दबाओ, प्रश्न यहाँ सेव हो जाएगा।"),
    "### 🏆 Meri History": ("### 🏆 My History", "### 🏆 मेरी हिस्ट्री"),
    "{a}/{b} marks · {acc}% acc · {d}": ("{a}/{b} marks · {acc}% acc · {d}", "{a}/{b} अंक · {acc}% सटीकता · {d}"),
    "⭐ Best score: {p}%": ("⭐ Best score: {p}%", "⭐ सर्वश्रेष्ठ स्कोर: {p}%"),
    "Clear history": ("Clear history", "हिस्ट्री साफ़ करो"),
    "Abhi koi quiz nahi diya. Pehla quiz banao!": ("No quiz taken yet. Make your first quiz!", "अभी कोई क्विज़ नहीं दिया। पहला क्विज़ बनाओ!"),
    "### 👤 Account": ("### 👤 Account", "### 👤 अकाउंट"),
    "Logged in": ("Logged in", "लॉग इन है"),
    "🛠️ Admin — PYQ bank me sawal jod sakte ho": ("🛠️ Admin — you can add questions to the PYQ bank", "🛠️ एडमिन — तुम PYQ बैंक में प्रश्न जोड़ सकते हो"),
    "Database me save karne me dikkat aayi. Supabase SQL / keys check karo.": (
        "Problem while saving to the database. Check the Supabase SQL / keys.", "डेटाबेस में सेव करने में दिक्कत आई। Supabase SQL / keys जाँचो।"),
    "🚪 Logout": ("🚪 Logout", "🚪 लॉगआउट"),
    "🔑 Login karo": ("🔑 Log in", "🔑 लॉग इन करो"),
    "Guest mode: login/database abhi set nahi hai, isliye history browser band hote hi chali jayegi.": (
        "Guest mode: login/database is not set up, so your history is lost when the browser closes.",
        "गेस्ट मोड: लॉगिन/डेटाबेस सेट नहीं है, इसलिए ब्राउज़र बंद होते ही हिस्ट्री चली जाएगी।"),
    "Guest mode: tumne login nahi kiya, isliye history browser band hote hi chali jayegi. Neeche backup file le lo.": (
        "Guest mode: you are not logged in, so your history is lost when the browser closes. Take a backup file below.",
        "गेस्ट मोड: तुमने लॉगिन नहीं किया, इसलिए ब्राउज़र बंद होते ही हिस्ट्री चली जाएगी। नीचे बैकअप फ़ाइल ले लो।"),
    "### 💾 Progress backup": ("### 💾 Progress backup", "### 💾 प्रोग्रेस बैकअप"),
    "Apna XP, history aur saved questions file me save karo aur kabhi bhi wapas load karo.": (
        "Save your XP, history and saved questions to a file and load them back any time.",
        "अपना XP, हिस्ट्री और सेव किए प्रश्न फ़ाइल में सेव करो और कभी भी वापस लोड करो।"),
    "⬇️ Progress save karo": ("⬇️ Save progress", "⬇️ प्रोग्रेस सेव करो"),
    "Progress load karo": ("Load progress", "प्रोग्रेस लोड करो"),
    "✅ {h} quiz history aur {b} saved sawal wapas aa gaye.": (
        "✅ Restored {h} quiz history entries and {b} saved questions.", "✅ {h} क्विज़ हिस्ट्री और {b} सेव प्रश्न वापस आ गए।"),
    "Load nahi hua: {e}": ("Could not load: {e}", "लोड नहीं हुआ: {e}"),

    # ───────── hero / setup ─────────
    "Content chuno": ("Choose content", "कंटेंट चुनो"),
    "Quiz khelo": ("Play quiz", "क्विज़ खेलो"),
    "Result dekho": ("See result", "रिज़ल्ट देखो"),
    "Topic, PDF ya notes ki photo do — AI turant quiz banata hai. Awaaz, timer, lives, XP aur badges ke saath seekho.": (
        "Give a topic, PDF or a photo of your notes — the AI makes a quiz instantly. Learn with voice, timer, lives, XP and badges.",
        "टॉपिक, PDF या नोट्स की फ़ोटो दो — AI तुरंत क्विज़ बनाता है। आवाज़, टाइमर, जान, XP और बैज के साथ सीखो।"),
    "Level": ("Level", "स्तर"), "Total XP": ("Total XP", "कुल XP"),
    "Quizzes khele": ("Quizzes played", "खेले गए क्विज़"), "Best score": ("Best score", "सर्वश्रेष्ठ स्कोर"),
    "🧠 Quiz Arena": ("🧠 Quiz Arena", "🧠 क्विज़ अरेना"),
    "🏛️ Govt Exam PYQs": ("🏛️ Govt Exam PYQs", "🏛️ सरकारी परीक्षा PYQ"),
    "🔍 Doubt Solver": ("🔍 Doubt Solver", "🔍 डाउट सॉल्वर"),

    # ───────── quiz tab ─────────
    "AI sawal bana raha hai…": ("The AI is making questions…", "AI प्रश्न बना रहा है…"),
    "Valid sawal nahi ban paye. Dobara try karo.": ("Could not make valid questions. Please try again.", "सही प्रश्न नहीं बन पाए। फिर से कोशिश करो।"),
    "AI ka response samajh nahi aaya. Dobara try karo ya doosra model chuno.": (
        "Could not understand the AI response. Try again or pick another model.", "AI का जवाब समझ नहीं आया। फिर कोशिश करो या दूसरा मॉडल चुनो।"),
    "Content kahan se aayega?": ("Where should the content come from?", "कंटेंट कहाँ से आएगा?"),
    "💡 Topic": ("💡 Topic", "💡 टॉपिक"), "📄 PDF": ("📄 PDF", "📄 PDF"),
    "🖼️ Photo / Camera": ("🖼️ Photo / Camera", "🖼️ फ़ोटो / कैमरा"), "📝 Notes": ("📝 Notes", "📝 नोट्स"),
    "Kis topic par quiz chahiye?": ("Which topic do you want a quiz on?", "किस टॉपिक पर क्विज़ चाहिए?"),
    "e.g. Machine Learning basics, Indian Constitution, Python lists…": (
        "e.g. Machine Learning basics, Indian Constitution, Python lists…", "जैसे: मशीन लर्निंग बेसिक्स, भारतीय संविधान, Python lists…"),
    "Quick picks": ("Quick picks", "झटपट चुनो"),
    "Python Basics": ("Python Basics", "Python बेसिक्स"), "World History": ("World History", "विश्व इतिहास"),
    "Human Biology": ("Human Biology", "मानव जीवविज्ञान"), "Indian Economy": ("Indian Economy", "भारतीय अर्थव्यवस्था"),
    "Selected topic: **{topic}**": ("Selected topic: **{topic}**", "चुना गया टॉपिक: **{topic}**"),
    "PDF upload karo": ("Upload a PDF", "PDF अपलोड करो"),
    "Page range": ("Page range", "पेज रेंज"),
    "✅ {n} page(s) padhe · {chars} characters": ("✅ Read {n} page(s) · {chars} characters", "✅ {n} पेज पढ़े · {chars} अक्षर"),
    "Text lamba hai — pehle {max} characters use honge. Page range chhota karo.": (
        "The text is long — only the first {max} characters will be used. Reduce the page range.",
        "टेक्स्ट लंबा है — सिर्फ़ पहले {max} अक्षर इस्तेमाल होंगे। पेज रेंज छोटी करो।"),
    "Is PDF se text nahi nikla (scanned lagta hai). Uske page ki **photo** lekar try karo.": (
        "No text could be extracted from this PDF (it looks scanned). Try a **photo** of its page.",
        "इस PDF से टेक्स्ट नहीं निकला (स्कैन लगता है)। उसके पेज की **फ़ोटो** लेकर कोशिश करो।"),
    "PDF read nahi ho paya: {e}": ("Could not read the PDF: {e}", "PDF पढ़ी नहीं जा सकी: {e}"),
    "Photo upload karo ya camera se seedha click karo.": ("Upload a photo or click one directly with the camera.", "फ़ोटो अपलोड करो या कैमरे से सीधे खींचो।"),
    "Photo mode": ("Photo mode", "फ़ोटो मोड"),
    "📁 Upload File": ("📁 Upload File", "📁 फ़ाइल अपलोड"), "📸 Live Camera Click": ("📸 Live Camera Click", "📸 लाइव कैमरा क्लिक"),
    "Photo upload karo": ("Upload a photo", "फ़ोटो अपलोड करो"),
    "Live photo click karo": ("Take a live photo", "लाइव फ़ोटो खींचो"),
    "Photo 15 MB se badi hai. Chhoti photo use karo.": ("The photo is larger than 15 MB. Use a smaller one.", "फ़ोटो 15 MB से बड़ी है। छोटी फ़ोटो इस्तेमाल करो।"),
    "Photo compress hone ke baad bhi bahut badi hai. Kam resolution ki photo lo.": (
        "The photo is still too large after compression. Use a lower-resolution photo.", "कंप्रेस होने के बाद भी फ़ोटो बहुत बड़ी है। कम रेज़ोल्यूशन की फ़ोटो लो।"),
    "Selected photo": ("Selected photo", "चुनी गई फ़ोटो"),
    "Apne notes / article yahan paste karo": ("Paste your notes / article here", "अपने नोट्स / आर्टिकल यहाँ पेस्ट करो"),
    "Chapter ka text, notes, ya koi bhi article…": ("Chapter text, notes, or any article…", "चैप्टर का टेक्स्ट, नोट्स या कोई भी आर्टिकल…"),
    "{n} characters": ("{n} characters", "{n} अक्षर"),
    "✨ Quiz banao": ("✨ Make quiz", "✨ क्विज़ बनाओ"),
    "Pehle topic likho, photo upload/click karo ya notes paste karo.": (
        "First write a topic, upload/click a photo or paste notes.", "पहले टॉपिक लिखो, फ़ोटो अपलोड/क्लिक करो या नोट्स पेस्ट करो।"),

    # ───────── PYQ tab ─────────
    "### 🏛️ Govt & Entrance Exam — PYQ Practice": ("### 🏛️ Govt & Entrance Exam — PYQ Practice", "### 🏛️ सरकारी व प्रवेश परीक्षा — PYQ प्रैक्टिस"),
    "Yahan **pichhle saalon ke asli sawal (PYQ)** aate hain, PYQ bank se (📜 tag ke saath). Jo PYQ tum pehle kar chuke ho wo dobara nahi aate. Marking har exam ke hisaab se lagti hai.": (
        "Here you get **real previous-year questions (PYQ)** from the PYQ bank (with a 📜 tag). PYQs you have already done never repeat. Marking follows each exam's pattern.",
        "यहाँ PYQ बैंक से **पिछले सालों के असली प्रश्न (PYQ)** आते हैं (📜 टैग के साथ)। जो PYQ तुम कर चुके हो वो दोबारा नहीं आते। मार्किंग हर परीक्षा के हिसाब से लगती है।"),
    "Target exam": ("Target exam", "लक्ष्य परीक्षा"),
    "General All Exams": ("General All Exams", "सामान्य (सभी परीक्षाएँ)"),
    "Subject": ("Subject", "विषय"),
    "All subjects": ("All subjects", "सभी विषय"),
    "Year (optional)": ("Year (optional)", "वर्ष (वैकल्पिक)"),
    "PYQ bank me **{exam}** ke sawal abhi nahi hain. Admin se PYQ upload karwao (neeche 'PYQ bank' wala box dekho).": (
        "The PYQ bank has no **{exam}** questions yet. Ask the admin to upload PYQs (see the 'PYQ bank' box below).",
        "PYQ बैंक में **{exam}** के प्रश्न अभी नहीं हैं। एडमिन से PYQ अपलोड करवाओ (नीचे 'PYQ बैंक' वाला बॉक्स देखो)।"),
    "Is subject/year ke liye PYQ nahi mile. Filter badlo.": ("No PYQs found for this subject/year. Change the filter.", "इस विषय/वर्ष के लिए PYQ नहीं मिले। फ़िल्टर बदलो।"),
    "Tum is filter ke saare {n} PYQ kar chuke ho.": ("You have already done all {n} PYQs for this filter.", "तुम इस फ़िल्टर के सारे {n} PYQ कर चुके हो।"),
    "🔁 Seen list reset karo (PYQ phir se aayenge)": ("🔁 Reset seen list (PYQs will come again)", "🔁 देखी हुई लिस्ट रीसेट करो (PYQ फिर आएँगे)"),
    "✅ {fresh} naye PYQ available ({done} tum pehle kar chuke ho).": (
        "✅ {fresh} new PYQs available ({done} already done by you).", "✅ {fresh} नए PYQ उपलब्ध ({done} तुम पहले कर चुके हो)।"),
    "PYQ kam pade to AI practice sawal se bharo (ye asli PYQ nahi hote)": (
        "If PYQs run short, fill with AI practice questions (these are not real PYQs)", "PYQ कम पड़ें तो AI प्रैक्टिस प्रश्नों से भरो (ये असली PYQ नहीं होते)"),
    "Band rakhoge to sirf asli PYQ aayenge — kam hue to kam sawal milenge.": (
        "If off, only real PYQs appear — you get fewer questions if there are fewer.", "बंद रखोगे तो सिर्फ़ असली PYQ आएँगे — कम हुए तो कम प्रश्न मिलेंगे।"),
    "Marking scheme": ("Marking scheme", "मार्किंग स्कीम"),
    "📋 Official (exam jaisi)": ("📋 Official (like the exam)", "📋 आधिकारिक (परीक्षा जैसी)"),
    "⚙️ Sidebar wali": ("⚙️ From sidebar", "⚙️ साइडबार वाली"),
    "+{a} sahi · −{b} galat · 0 unattempted. {note}": ("+{a} correct · −{b} wrong · 0 unattempted. {note}", "+{a} सही · −{b} गलत · 0 बिना किए। {note}"),
    "Notification me alag ho to marking adjust karo": ("Adjust marking if your notification differs", "नोटिफिकेशन में अलग हो तो मार्किंग बदलो"),
    "Negative marking": ("Negative marking", "नेगेटिव मार्किंग"),
    "Official": ("Official", "आधिकारिक"), "Koi negative nahi": ("No negative", "कोई नेगेटिव नहीं"),
    "Numerical questions par bhi negative lagao": ("Apply negative marking to numerical questions too", "न्यूमेरिकल प्रश्नों पर भी नेगेटिव लगाओ"),
    "Is option me sidebar wali marking lagegi.": ("This option uses the sidebar marking.", "इस विकल्प में साइडबार वाली मार्किंग लगेगी।"),
    "📝 Full mock test (exam jaisa pattern + timer)": ("📝 Full mock test (exam pattern + timer)", "📝 पूरा मॉक टेस्ट (परीक्षा जैसा पैटर्न + टाइमर)"),
    "Mock size": ("Mock size", "मॉक का आकार"),
    "Full": ("Full", "पूरा"), "Half (50%)": ("Half (50%)", "आधा (50%)"), "Quarter (25%)": ("Quarter (25%)", "चौथाई (25%)"),
    "🧾 Mock: {n} sawal · {mins} min · max {mx} marks · +{a} / −{b}": (
        "🧾 Mock: {n} questions · {mins} min · max {mx} marks · +{a} / −{b}", "🧾 मॉक: {n} प्रश्न · {mins} मिनट · अधिकतम {mx} अंक · +{a} / −{b}"),
    "ℹ️ Abhi {n} naye PYQ hain, isliye mock utna hi chhota banega (AI se bharna band hai).": (
        "ℹ️ Only {n} new PYQs are available, so the mock will be that short (AI filling is off).", "ℹ️ अभी {n} नए PYQ हैं, इसलिए मॉक उतना ही छोटा बनेगा (AI से भरना बंद है)।"),
    "Practice me {n} sawal aayenge (sidebar ke 'Questions' slider se badlo).": (
        "Practice will have {n} questions (change with the 'Questions' slider in the sidebar).", "प्रैक्टिस में {n} प्रश्न आएँगे (साइडबार के 'Questions' स्लाइडर से बदलो)।"),
    "📚 PYQ bank / apna dataset jodo (JSON / CSV)": ("📚 PYQ bank / add your own dataset (JSON / CSV)", "📚 PYQ बैंक / अपना डेटासेट जोड़ो (JSON / CSV)"),
    "Har sawal me: exam, subject, year, question, options, answer (text ya A-D), explanation. Numerical sawal ke liye `type: num` aur answer me number. `exam` ka naam in me se ek ho: {exams}. File ko repo me `pyq_data.json` naam se daaloge to wo hamesha rahegi.": (
        "Each question needs: exam, subject, year, question, options, answer (text or A-D), explanation. For numerical questions use `type: num` and a number as the answer. The `exam` name must be one of: {exams}. If you put the file in the repo as `pyq_data.json` it stays permanently.",
        "हर प्रश्न में: exam, subject, year, question, options, answer (टेक्स्ट या A-D), explanation। न्यूमेरिकल प्रश्न के लिए `type: num` और उत्तर में संख्या। `exam` का नाम इनमें से एक हो: {exams}। फ़ाइल को repo में `pyq_data.json` नाम से डालोगे तो वो हमेशा रहेगी।"),
    "🛠️ Tum admin ho: upload ke baad 'Shared PYQ bank me save karo' dabao — sawal sabhi users ko milenge.": (
        "🛠️ You are admin: after uploading press 'Save to shared PYQ bank' — all users will get the questions.",
        "🛠️ तुम एडमिन हो: अपलोड के बाद 'Shared PYQ बैंक में सेव करो' दबाओ — प्रश्न सभी यूज़र्स को मिलेंगे।"),
    "Shared bank me sawal sirf admin jod sakta hai. Neeche upload sirf tumhare is session ke liye hai.": (
        "Only the admin can add questions to the shared bank. The upload below is only for your current session.",
        "शेयर्ड बैंक में प्रश्न सिर्फ़ एडमिन जोड़ सकता है। नीचे का अपलोड सिर्फ़ तुम्हारे इस सेशन के लिए है।"),
    "📄 Template (JSON)": ("📄 Template (JSON)", "📄 टेम्पलेट (JSON)"),
    "PYQ file": ("PYQ file", "PYQ फ़ाइल"),
    "✅ {n} sawal jude ({d} duplicate chhode).": ("✅ Added {n} questions (skipped {d} duplicates).", "✅ {n} प्रश्न जुड़े ({d} डुप्लीकेट छोड़े)।"),
    "File padh nahi paya: {e}": ("Could not read the file: {e}", "फ़ाइल पढ़ नहीं पाया: {e}"),
    "📤 Shared PYQ bank me save karo ({n} sawal)": ("📤 Save to shared PYQ bank ({n} questions)", "📤 शेयर्ड PYQ बैंक में सेव करो ({n} प्रश्न)"),
    "✅ {n} sawal bank me save/update ho gaye.": ("✅ {n} questions saved/updated in the bank.", "✅ {n} प्रश्न बैंक में सेव/अपडेट हो गए।"),
    "Bank me save nahi hua (admin access / SQL check karo): {e}": (
        "Could not save to the bank (check admin access / SQL): {e}", "बैंक में सेव नहीं हुआ (एडमिन एक्सेस / SQL जाँचो): {e}"),
    "Is session me {n} uploaded PYQ hain.": ("There are {n} uploaded PYQs in this session.", "इस सेशन में {n} अपलोड किए PYQ हैं।"),
    "🗑️ Uploaded PYQ hatao": ("🗑️ Remove uploaded PYQs", "🗑️ अपलोड किए PYQ हटाओ"),
    "🚀 {exam} mock test shuru karo": ("🚀 Start {exam} mock test", "🚀 {exam} मॉक टेस्ट शुरू करो"),
    "🚀 {exam} PYQ practice shuru karo": ("🚀 Start {exam} PYQ practice", "🚀 {exam} PYQ प्रैक्टिस शुरू करो"),
    "Sawal taiyaar ho rahe hain…": ("Preparing questions…", "प्रश्न तैयार हो रहे हैं…"),
    "Abhi koi sawal nahi mila. {notes}": ("No questions found right now. {notes}", "अभी कोई प्रश्न नहीं मिला। {notes}"),
    "{total} me se {got} sawal hi mile (naye PYQ itne hi the).": (
        "Got only {got} of {total} questions (that many new PYQs existed).", "{total} में से सिर्फ़ {got} प्रश्न मिले (नए PYQ इतने ही थे)।"),
    "{subj}: AI se baaki sawal nahi ban paye ({err})": (
        "{subj}: the AI could not make the remaining questions ({err})", "{subj}: AI बाकी प्रश्न नहीं बना पाया ({err})"),

    # ───────── doubt solver ─────────
    "### 🔍 AI Doubt Solver": ("### 🔍 AI Doubt Solver", "### 🔍 AI डाउट सॉल्वर"),
    "Doubt poochho (text, photo, camera ya PDF). Jawab word-by-word aata hai, aur tum follow-up sawal bhi pooch sakte ho.": (
        "Ask a doubt (text, photo, camera or PDF). The answer streams word by word and you can ask follow-up questions too.",
        "डाउट पूछो (टेक्स्ट, फ़ोटो, कैमरा या PDF)। जवाब शब्द-दर-शब्द आता है, और तुम फॉलो-अप प्रश्न भी पूछ सकते हो।"),
    "Jawab ki bhasha": ("Answer language", "जवाब की भाषा"),
    "Style": ("Style", "शैली"),
    "Step-by-step": ("Step-by-step", "स्टेप-बाय-स्टेप"), "Quick answer": ("Quick answer", "झटपट जवाब"),
    "ELI5 (bahut simple)": ("ELI5 (very simple)", "ELI5 (बहुत आसान)"), "Exam-ready notes": ("Exam-ready notes", "परीक्षा-तैयार नोट्स"),
    "Doubt kaise poochna hai?": ("How do you want to ask the doubt?", "डाउट कैसे पूछना है?"),
    "📝 Text": ("📝 Text", "📝 टेक्स्ट"), "📸 Live Camera": ("📸 Live Camera", "📸 लाइव कैमरा"),
    "🖼️ Photo Upload": ("🖼️ Photo Upload", "🖼️ फ़ोटो अपलोड"),
    "Apna doubt yahan likho": ("Write your doubt here", "अपना डाउट यहाँ लिखो"),
    "e.g. Binary Search Tree me insertion kaise hota hai? Example ke saath samjhao.": (
        "e.g. How does insertion work in a Binary Search Tree? Explain with an example.", "जैसे: Binary Search Tree में insertion कैसे होता है? उदाहरण के साथ समझाओ।"),
    "📸 Browser me camera allow karo, question ki saaf photo lo (seedhi, achhi roshni me). Phone me back camera chahiye to browser ka camera-switch use karo.": (
        "📸 Allow the camera in your browser and take a clear photo of the question (straight, in good light). On a phone, use the browser's camera switch for the back camera.",
        "📸 ब्राउज़र में कैमरा allow करो, प्रश्न की साफ़ फ़ोटो लो (सीधी, अच्छी रोशनी में)। फ़ोन में पीछे वाला कैमरा चाहिए तो ब्राउज़र का कैमरा-स्विच इस्तेमाल करो।"),
    "Question ki live photo click karo": ("Take a live photo of the question", "प्रश्न की लाइव फ़ोटो खींचो"),
    "Question photo": ("Question photo", "प्रश्न की फ़ोटो"),
    "Koi extra instruction? (optional)": ("Any extra instruction? (optional)", "कोई अतिरिक्त निर्देश? (वैकल्पिक)"),
    "e.g. Sirf Q3 solve karo": ("e.g. Solve only Q3", "जैसे: सिर्फ़ Q3 हल करो"),
    "PDF me se kya poochna hai?": ("What do you want to ask from the PDF?", "PDF में से क्या पूछना है?"),
    "e.g. Is chapter ka summary do": ("e.g. Give a summary of this chapter", "जैसे: इस चैप्टर का सारांश दो"),
    "PDF ke pehle 5 pages load ho gaye.": ("The first 5 pages of the PDF are loaded.", "PDF के पहले 5 पेज लोड हो गए।"),
    "PDF se text nahi nikla. Page ki photo upload karo.": ("No text could be extracted from the PDF. Upload a photo of the page.", "PDF से टेक्स्ट नहीं निकला। पेज की फ़ोटो अपलोड करो।"),
    "PDF read error: {e}": ("PDF read error: {e}", "PDF पढ़ने में त्रुटि: {e}"),
    "💡 Samjhao": ("💡 Explain", "💡 समझाओ"),
    "Pehle doubt likho ya photo do.": ("First write a doubt or give a photo.", "पहले डाउट लिखो या फ़ोटो दो।"),
    "📷 *Photo se doubt*": ("📷 *Doubt from a photo*", "📷 *फ़ोटो से डाउट*"),
    "🔁 Jawab dobara generate karo": ("🔁 Regenerate the answer", "🔁 जवाब दोबारा बनाओ"),
    "Follow-up poochho": ("Ask a follow-up", "फॉलो-अप पूछो"),
    "e.g. Ek aur example se samjhao / Is step me ye kyun hua?": ("e.g. Explain with another example / Why did this happen in this step?", "जैसे: एक और उदाहरण से समझाओ / इस स्टेप में ये क्यों हुआ?"),
    "Bhejo ➤": ("Send ➤", "भेजो ➤"),
    "🧹 Naya doubt": ("🧹 New doubt", "🧹 नया डाउट"),
    "📝 Is par quiz banao": ("📝 Make a quiz on this", "📝 इस पर क्विज़ बनाओ"),
    "⬇️ Notes (.md)": ("⬇️ Notes (.md)", "⬇️ नोट्स (.md)"),
    "Tum": ("You", "तुम"),

    # ───────── quiz stage ─────────
    "⏱️ {s} sec bache hain": ("⏱️ {s} sec left", "⏱️ {s} सेकंड बचे हैं"),
    "⏳ Quiz ka time bacha: {m:02d}:{s:02d}": ("⏳ Quiz time left: {m:02d}:{s:02d}", "⏳ क्विज़ का समय बचा: {m:02d}:{s:02d}"),
    "Question {i} of {n}": ("Question {i} of {n}", "प्रश्न {i} / {n}"),
    "Question {i}": ("Question {i}", "प्रश्न {i}"),
    "MCQ": ("MCQ", "MCQ"), "True/False": ("True/False", "सही/गलत"), "Short answer": ("Short answer", "छोटा उत्तर"),
    "Numerical": ("Numerical", "न्यूमेरिकल"),
    "💡 Hint (−5 XP)": ("💡 Hint (−5 XP)", "💡 संकेत (−5 XP)"),
    "📌 Saved": ("📌 Saved", "📌 सेव्ड"), "🔖 Save": ("🔖 Save", "🔖 सेव"),
    "🔊 Sunao": ("🔊 Listen", "🔊 सुनाओ"), "Sawal sunao (R)": ("Read the question (R)", "प्रश्न सुनाओ (R)"), "Roko": ("Stop", "रोको"),
    "Apna answer chuno": ("Choose your answer", "अपना उत्तर चुनो"),
    "Ek se zyada sahi options chuno": ("Choose more than one correct option", "एक से ज़्यादा सही विकल्प चुनो"),
    "Numerical answer": ("Numerical answer", "संख्यात्मक उत्तर"),
    "Sirf number likho, jaise 12.5": ("Write only a number, like 12.5", "सिर्फ़ संख्या लिखो, जैसे 12.5"),
    "Khali jagah bharo": ("Fill in the blank", "खाली जगह भरो"),
    "Apna answer type karo…": ("Type your answer…", "अपना उत्तर टाइप करो…"),
    "Apna answer likho (1-3 line)": ("Write your answer (1-3 lines)", "अपना उत्तर लिखो (1-3 पंक्तियाँ)"),
    "⌨️ <kbd>1</kbd>–<kbd>{n}</kbd> chuno · <kbd>Enter</kbd> aage · <kbd>H</kbd> hint · {extra}<kbd>R</kbd> sunao": (
        "⌨️ <kbd>1</kbd>–<kbd>{n}</kbd> choose · <kbd>Enter</kbd> next · <kbd>H</kbd> hint · {extra}<kbd>R</kbd> listen",
        "⌨️ <kbd>1</kbd>–<kbd>{n}</kbd> चुनो · <kbd>Enter</kbd> आगे · <kbd>H</kbd> संकेत · {extra}<kbd>R</kbd> सुनो"),
    "<kbd>S</kbd> skip · ": ("<kbd>S</kbd> skip · ", "<kbd>S</kbd> छोड़ो · "),
    "💀 Saari lives khatam! Game over.": ("💀 All lives are gone! Game over.", "💀 सारी जान खत्म! गेम ओवर।"),
    "🧠 Aur detail me samjhao": ("🧠 Explain in more detail", "🧠 और विस्तार से समझाओ"),
    "Soch raha hoon…": ("Thinking…", "सोच रहा हूँ…"),
    "🧭 Question palette (kisi bhi sawal par jao)": ("🧭 Question palette (jump to any question)", "🧭 प्रश्न पैलेट (किसी भी प्रश्न पर जाओ)"),
    "✅ = answer diya hua · baaki khali. Neela button = abhi wala sawal.": (
        "✅ = answered · others empty. Blue button = current question.", "✅ = उत्तर दिया हुआ · बाकी खाली। नीला बटन = अभी वाला प्रश्न।"),
    "⬅️ Back": ("⬅️ Back", "⬅️ पीछे"),
    "Check answer": ("Check answer", "जवाब जाँचो"),
    "AI tumhara answer check kar raha hai…": ("The AI is checking your answer…", "AI तुम्हारा उत्तर जाँच रहा है…"),
    "Skip ⏭️": ("Skip ⏭️", "छोड़ो ⏭️"),
    "Result dekho 💀": ("Result dekho 💀", "रिज़ल्ट देखो 💀"),
    "Finish 🏁": ("Finish 🏁", "खत्म करो 🏁"),
    "Next ➡️": ("Next ➡️", "अगला ➡️"),
    "✖ Quiz chhodo": ("✖ Quit quiz", "✖ क्विज़ छोड़ो"),

    # feedback
    "✅ <b>Badhiya!</b>": ("✅ <b>Well done!</b>", "✅ <b>बढ़िया!</b>"),
    "🟡 <b>Adhura / galat.</b>": ("🟡 <b>Partial / wrong.</b>", "🟡 <b>अधूरा / गलत।</b>"),
    "AI score:": ("AI score:", "AI स्कोर:"),
    "Model answer:": ("Model answer:", "आदर्श उत्तर:"),
    "✅ <b>Sahi jawab!</b>": ("✅ <b>Correct answer!</b>", "✅ <b>सही जवाब!</b>"),
    "⏰ <b>Time khatam.</b> ": ("⏰ <b>Time is up.</b> ", "⏰ <b>समय खत्म।</b> "),
    "⏭️ <b>Skip.</b> ": ("⏭️ <b>Skipped.</b> ", "⏭️ <b>छोड़ा।</b> "),
    "❌ <b>Galat.</b> ": ("❌ <b>Wrong.</b> ", "❌ <b>गलत।</b> "),
    "Sahi answer:": ("Correct answer:", "सही उत्तर:"),

    # flashcards
    "## 📇 Flashcards": ("## 📇 Flashcards", "## 📇 फ्लैशकार्ड"),
    "Card {i} of {n}": ("Card {i} of {n}", "कार्ड {i} / {n}"),
    "⬅️ Pichhla": ("⬅️ Previous", "⬅️ पिछला"),
    "🔄 Answer dikhao": ("🔄 Show answer", "🔄 उत्तर दिखाओ"), "🔄 Sawal dikhao": ("🔄 Show question", "🔄 प्रश्न दिखाओ"),
    "Agla ➡️": ("Next ➡️", "अगला ➡️"),
    "← Wapas jao": ("← Go back", "← वापस जाओ"),

    # ───────── result stage ─────────
    "Zabardast! 🏆": ("Excellent! 🏆", "ज़बरदस्त! 🏆"),
    "Topic par tumhari pakad mast hai.": ("You have a strong grip on the topic.", "टॉपिक पर तुम्हारी पकड़ बढ़िया है।"),
    "Achha try! 👍": ("Good try! 👍", "अच्छा प्रयास! 👍"),
    "Thodi aur practice se top score aa jayega.": ("A little more practice and a top score will come.", "थोड़ी और प्रैक्टिस से टॉप स्कोर आ जाएगा।"),
    "Keep going 💪": ("Keep going 💪", "लगे रहो 💪"),
    "Explanations padho aur dobara try karo.": ("Read the explanations and try again.", "स्पष्टीकरण पढ़ो और फिर कोशिश करो।"),
    "Marking: +{a} sahi · −{b} galat · 0 skip{nn}  |  Accuracy = sahi ÷ attempted": (
        "Marking: +{a} correct · −{b} wrong · 0 skip{nn}  |  Accuracy = correct ÷ attempted",
        "मार्किंग: +{a} सही · −{b} गलत · 0 स्किप{nn}  |  सटीकता = सही ÷ किए गए"),
    " · numerical par negative nahi": (" · no negative on numericals", " · न्यूमेरिकल पर नेगेटिव नहीं"),
    "⏰ Quiz ka total time khatam ho gaya — bache hue sawal skip maane gaye.": (
        "⏰ The total quiz time is over — remaining questions are counted as skipped.", "⏰ क्विज़ का कुल समय खत्म हो गया — बचे प्रश्न स्किप माने गए।"),
    "marks": ("marks", "अंक"),
    "Marks": ("Marks", "अंक"), "Accuracy": ("Accuracy", "सटीकता"), "Attempted": ("Attempted", "किए गए"),
    "Negative marks": ("Negative marks", "नेगेटिव अंक"), "Sahi": ("Correct", "सही"), "Galat": ("Wrong", "गलत"),
    "Skipped": ("Skipped", "छोड़े गए"), "Total time": ("Total time", "कुल समय"), "XP earned": ("XP earned", "कमाए XP"),
    "Best streak": ("Best streak", "सबसे लंबी स्ट्रीक"), "Avg / question": ("Avg / question", "औसत / प्रश्न"),
    "Hints used": ("Hints used", "इस्तेमाल हुए संकेत"),
    "🎉 Level up! Ab tum **Level {n}** par ho.": ("🎉 Level up! You are now on **Level {n}**.", "🎉 लेवल अप! अब तुम **स्तर {n}** पर हो।"),
    "**➕ Aur sawal chahiye?**  Abhi tak **{n}** sawal ho chuke hain.": (
        "**➕ Want more questions?**  **{n}** questions done so far.", "**➕ और प्रश्न चाहिए?**  अभी तक **{n}** प्रश्न हो चुके हैं।"),
    "Kitne aur sawal?": ("How many more questions?", "और कितने प्रश्न?"),
    "➕ {n} aur sawal jodo": ("➕ Add {n} more questions", "➕ {n} और प्रश्न जोड़ो"),
    "Naye sawal ban rahe hain…": ("Making new questions…", "नए प्रश्न बन रहे हैं…"),
    "Naye sawal nahi ban paye. Dobara try karo.": ("Could not make new questions. Please try again.", "नए प्रश्न नहीं बन पाए। फिर से कोशिश करो।"),
    "Naye sawal isi quiz me jud jayenge — marks, accuracy aur XP poore quiz ka milkar banega.": (
        "New questions are added to this same quiz — marks, accuracy and XP are computed for the whole quiz.",
        "नए प्रश्न इसी क्विज़ में जुड़ जाएँगे — अंक, सटीकता और XP पूरे क्विज़ का मिलाकर बनेगा।"),
    "Survival me saari lives khatam ho chuki hain, isliye aur sawal nahi jud sakte.": (
        "All lives are gone in Survival, so more questions cannot be added.", "सर्वाइवल में सारी जान खत्म हो चुकी हैं, इसलिए और प्रश्न नहीं जुड़ सकते।"),
    "Ek quiz me maximum {n} sawal ho sakte hain.": ("A quiz can have at most {n} questions.", "एक क्विज़ में अधिकतम {n} प्रश्न हो सकते हैं।"),
    "🔁 Naya quiz": ("🔁 New quiz", "🔁 नया क्विज़"),
    "🎯 Sirf galat dobara": ("🎯 Redo only wrong ones", "🎯 सिर्फ़ गलत दोबारा"),
    "Sirf galat/skip kiye hue sawal phir se solve karo": ("Solve only the wrong/skipped questions again", "सिर्फ़ गलत/छोड़े हुए प्रश्न फिर से हल करो"),
    "🔄 Wahi quiz phir se": ("🔄 Same quiz again", "🔄 वही क्विज़ फिर से"),
    "🆕 Naye sawal (same source)": ("🆕 New questions (same source)", "🆕 नए प्रश्न (वही स्रोत)"),
    "Naye sawal nahi ban paye.": ("Could not make new questions.", "नए प्रश्न नहीं बन पाए।"),
    "📇 Is quiz ke flashcards": ("📇 Flashcards of this quiz", "📇 इस क्विज़ के फ्लैशकार्ड"),
    "### 📊 Topic-wise performance": ("### 📊 Topic-wise performance", "### 📊 टॉपिक-वार प्रदर्शन"),
    "💪 Strong: ": ("💪 Strong: ", "💪 मज़बूत: "),
    "📌 Revise karo: ": ("📌 Revise: ", "📌 दोहराओ: "),
    "🧭 AI study plan banao": ("🧭 Make an AI study plan", "🧭 AI स्टडी प्लान बनाओ"),
    "Study plan ban raha hai…": ("Making the study plan…", "स्टडी प्लान बन रहा है…"),
    "### 🔍 Review": ("### 🔍 Review", "### 🔍 समीक्षा"),
    "- ❌ ~~{o}~~ (tumhara answer)": ("- ❌ ~~{o}~~ (your answer)", "- ❌ ~~{o}~~ (तुम्हारा उत्तर)"),
    "- ✅ **{o}** (tumne miss kiya)": ("- ✅ **{o}** (you missed it)", "- ✅ **{o}** (तुमसे छूट गया)"),
    "- ❌ ~~{o}~~ (galat chuna)": ("- ❌ ~~{o}~~ (chosen wrongly)", "- ❌ ~~{o}~~ (गलत चुना)"),
    "**Tumhara answer:** {a}": ("**Your answer:** {a}", "**तुम्हारा उत्तर:** {a}"),
    "**Sahi answer:** {a}": ("**Correct answer:** {a}", "**सही उत्तर:** {a}"),
    "🧪 **AI score:** {s:.1f}/1 — {fb}": ("🧪 **AI score:** {s:.1f}/1 — {fb}", "🧪 **AI स्कोर:** {s:.1f}/1 — {fb}"),
    "Ye sawal skip hua / time khatam ho gaya / game over ho gaya.": (
        "This question was skipped / time ran out / game over.", "यह प्रश्न स्किप हुआ / समय खत्म हो गया / गेम ओवर हो गया।"),
    "🎯 Marks: {m}": ("🎯 Marks: {m}", "🎯 अंक: {m}"),
    "### 📥 Download": ("### 📥 Download", "### 📥 डाउनलोड"),
    "Report (HTML)": ("Report (HTML)", "रिपोर्ट (HTML)"), "Results (CSV)": ("Results (CSV)", "नतीजे (CSV)"),
    "Quiz (JSON)": ("Quiz (JSON)", "क्विज़ (JSON)"),

    # report html
    "Result Report": ("Result Report", "रिज़ल्ट रिपोर्ट"),
    "Question": ("Question", "प्रश्न"), "Your answer": ("Your answer", "तुम्हारा उत्तर"),
    "Correct": ("Correct", "सही"), "Explanation": ("Explanation", "स्पष्टीकरण"),
    "Correct answer": ("Correct answer", "सही उत्तर"), "Best streak:": ("Best streak:", "सबसे लंबी स्ट्रीक:"),
    "Marks:": ("Marks:", "अंक:"), "Accuracy:": ("Accuracy:", "सटीकता:"), "Correct:": ("Correct:", "सही:"), "XP:": ("XP:", "XP:"),

    # ───────── login ─────────
    "Login karo — tumhari history, XP aur saved sawal hamesha safe rahenge, aur har baar naye sawal milenge.": (
        "Log in — your history, XP and saved questions stay safe, and you always get fresh questions.",
        "लॉग इन करो — तुम्हारी हिस्ट्री, XP और सेव किए प्रश्न हमेशा सुरक्षित रहेंगे, और हर बार नए प्रश्न मिलेंगे।"),
    "🔢 OTP se login": ("🔢 Login with OTP", "🔢 OTP से लॉगिन"),
    "🔑 Password se login": ("🔑 Login with password", "🔑 पासवर्ड से लॉगिन"),
    "Login kaise karna hai?": ("How do you want to log in?", "लॉगिन कैसे करना है?"),
    "📧 Email se": ("📧 With email", "📧 ईमेल से"), "📱 Mobile number se": ("📱 With mobile number", "📱 मोबाइल नंबर से"),
    "Email address": ("Email address", "ईमेल पता"), "Mobile number": ("Mobile number", "मोबाइल नंबर"),
    "98765 43210  (ya +91…)": ("98765 43210  (or +91…)", "98765 43210  (या +91…)"),
    "India ka number ho to sirf 10 digit likho. Dusre desh ke liye +country code.": (
        "For an Indian number write only the 10 digits. For other countries add +country code.",
        "भारत का नंबर हो तो सिर्फ़ 10 अंक लिखो। दूसरे देश के लिए +कंट्री कोड।"),
    "📨 OTP bhejo": ("📨 Send OTP", "📨 OTP भेजो"),
    "Sahi email likho.": ("Enter a valid email.", "सही ईमेल लिखो।"),
    "Sahi mobile number likho.": ("Enter a valid mobile number.", "सही मोबाइल नंबर लिखो।"),
    "OTP bheja ja raha hai…": ("Sending OTP…", "OTP भेजा जा रहा है…"),
    "OTP bheja gaya: **{who}**": ("OTP sent to: **{who}**", "OTP भेजा गया: **{who}**"),
    "OTP daalo": ("Enter the OTP", "OTP डालो"),
    "✅ Verify karo": ("✅ Verify", "✅ वेरिफ़ाई करो"),
    "Pehle OTP daalo.": ("Enter the OTP first.", "पहले OTP डालो।"),
    "Verify ho raha hai…": ("Verifying…", "वेरिफ़ाई हो रहा है…"),
    "🔁 OTP dobara bhejo": ("🔁 Resend OTP", "🔁 OTP दोबारा भेजो"),
    "{sec} second baad dobara try karo.": ("Try again after {sec} seconds.", "{sec} सेकंड बाद फिर कोशिश करो।"),
    "Naya OTP bhej diya.": ("A new OTP has been sent.", "नया OTP भेज दिया।"),
    "← Email / number badlo": ("← Change email / number", "← ईमेल / नंबर बदलो"),
    "Password": ("Password", "पासवर्ड"),
    "Password (kam se kam 6 characters)": ("Password (at least 6 characters)", "पासवर्ड (कम से कम 6 अक्षर)"),
    "Login": ("Login", "लॉगिन"), "Naya account banao": ("Create a new account", "नया अकाउंट बनाओ"),
    "🔑 Login karo ": ("🔑 Log in ", "🔑 लॉग इन करो "),
    "🆕 Account banao": ("🆕 Create account", "🆕 अकाउंट बनाओ"),
    "Email aur password dono daalo.": ("Enter both email and password.", "ईमेल और पासवर्ड दोनों डालो।"),
    "Password kam se kam 6 characters ka rakho.": ("Keep the password at least 6 characters.", "पासवर्ड कम से कम 6 अक्षर का रखो।"),
    "Logging in…": ("Logging in…", "लॉगिन हो रहा है…"),
    "Account ban gaya! Confirmation email bheji gayi hai — usse confirm karke login karo.": (
        "Account created! A confirmation email was sent — confirm it and then log in.",
        "अकाउंट बन गया! कन्फ़र्मेशन ईमेल भेजी गई है — उसे कन्फ़र्म करके लॉगिन करो।"),
    "🙋 Bina login ke Guest ki tarah chalo": ("🙋 Continue as a guest (no login)", "🙋 बिना लॉगिन के गेस्ट की तरह चलो"),
    "Guest me history sirf is session tak rehti hai (progress ko file me backup kar sakte ho).": (
        "As a guest your history lasts only for this session (you can back up progress to a file).",
        "गेस्ट में हिस्ट्री सिर्फ़ इस सेशन तक रहती है (प्रोग्रेस को फ़ाइल में बैकअप कर सकते हो)।"),
    "OTP service abhi set nahi hai. App admin ko Supabase me SMTP (email) / SMS settings add karni hongi. Tab tak **Password se login** karo ya **Guest** bano.": (
        "The OTP service is not set up yet. The app admin must add SMTP (email) / SMS settings in Supabase. Until then use **Password login** or continue as **Guest**.",
        "OTP सर्विस अभी सेट नहीं है। ऐप एडमिन को Supabase में SMTP (ईमेल) / SMS सेटिंग्स जोड़नी होंगी। तब तक **पासवर्ड से लॉगिन** करो या **गेस्ट** बनो।"),
    "Phone OTP ke liye Supabase me SMS provider (Twilio jaisa) setup hona chahiye. Abhi email se login karo.": (
        "Phone OTP needs an SMS provider (like Twilio) set up in Supabase. Log in with email for now.",
        "फ़ोन OTP के लिए Supabase में SMS प्रोवाइडर (जैसे Twilio) सेट होना चाहिए। अभी ईमेल से लॉगिन करो।"),
    "Bahut jaldi-jaldi OTP maanga. Thodi der (kuch minute) baad dobara try karo.": (
        "You asked for OTPs too quickly. Try again after a few minutes.", "बहुत जल्दी-जल्दी OTP माँगा। थोड़ी देर (कुछ मिनट) बाद फिर कोशिश करो।"),
    "OTP galat hai ya expire ho gaya. Naya OTP mangao.": ("The OTP is wrong or expired. Request a new OTP.", "OTP गलत है या एक्सपायर हो गया। नया OTP मँगाओ।"),
    "Naye users ka signup abhi band hai (Supabase setting).": ("New-user signup is currently off (Supabase setting).", "नए यूज़र्स का साइनअप अभी बंद है (Supabase सेटिंग)।"),
    "Email ya password galat hai.": ("Email or password is wrong.", "ईमेल या पासवर्ड गलत है।"),
    "Email abhi confirm nahi hui. Inbox me confirmation link kholo (ya admin Supabase me 'Confirm email' band kare).": (
        "Email not confirmed yet. Open the confirmation link in your inbox (or the admin can turn off 'Confirm email' in Supabase).",
        "ईमेल अभी कन्फ़र्म नहीं हुई। इनबॉक्स में कन्फ़र्मेशन लिंक खोलो (या एडमिन Supabase में 'Confirm email' बंद करे)।"),
    "Ye email pehle se registered hai. Login karo.": ("This email is already registered. Please log in.", "यह ईमेल पहले से रजिस्टर्ड है। लॉगिन करो।"),
    "🛠️ Admin ke liye: OTP / login kaise chalu karein?": ("🛠️ For the admin: how to enable OTP / login?", "🛠️ एडमिन के लिए: OTP / लॉगिन कैसे चालू करें?"),
    "**Email OTP:** Supabase Dashboard → Authentication → *Emails → SMTP Settings* me apna SMTP daalo (Gmail App Password / Brevo / Resend / SendGrid). Default Supabase mailer bahut limited hota hai (sirf kuch mail/ghanta).\n\n**OTP wali mail:** Authentication → Email Templates me `{{ .Token }}` rakho taaki mail me 6-digit OTP aaye.\n\n**Phone OTP:** Authentication → Sign In / Providers → Phone me SMS provider (Twilio, MessageBird…) enable karo.\n\n**Bina OTP ke:** Authentication → Sign In / Providers → Email me *Confirm email* band karo — tab Password se signup turant chalega.\n\n**Dhyan rahe:** SMTP / SMS settings Supabase dashboard me jaati hain, Streamlit Secrets me nahi. Secrets me sirf `SUPABASE_URL` aur `SUPABASE_ANON_KEY` chahiye. OTP tab chhupana ho to Secrets me `DISABLE_OTP = \"true\"` daalo.": (
        "**Email OTP:** In Supabase Dashboard → Authentication → *Emails → SMTP Settings* add your own SMTP (Gmail App Password / Brevo / Resend / SendGrid). The default Supabase mailer is very limited (only a few mails/hour).\n\n**OTP mail:** In Authentication → Email Templates keep `{{ .Token }}` so the mail contains the 6-digit OTP.\n\n**Phone OTP:** In Authentication → Sign In / Providers → Phone enable an SMS provider (Twilio, MessageBird…).\n\n**Without OTP:** In Authentication → Sign In / Providers → Email turn off *Confirm email* — then password signup works instantly.\n\n**Note:** SMTP / SMS settings go in the Supabase dashboard, not in Streamlit Secrets. Secrets only need `SUPABASE_URL` and `SUPABASE_ANON_KEY`. To hide the OTP tab add `DISABLE_OTP = \"true\"` in Secrets.",
        "**ईमेल OTP:** Supabase Dashboard → Authentication → *Emails → SMTP Settings* में अपना SMTP डालो (Gmail App Password / Brevo / Resend / SendGrid)। डिफ़ॉल्ट Supabase मेलर बहुत सीमित है (घंटे में कुछ ही मेल)।\n\n**OTP वाली मेल:** Authentication → Email Templates में `{{ .Token }}` रखो ताकि मेल में 6-अंकों का OTP आए।\n\n**फ़ोन OTP:** Authentication → Sign In / Providers → Phone में SMS प्रोवाइडर (Twilio, MessageBird…) चालू करो।\n\n**बिना OTP के:** Authentication → Sign In / Providers → Email में *Confirm email* बंद करो — तब पासवर्ड से साइनअप तुरंत चलेगा।\n\n**ध्यान रहे:** SMTP / SMS सेटिंग्स Supabase डैशबोर्ड में जाती हैं, Streamlit Secrets में नहीं। Secrets में सिर्फ़ `SUPABASE_URL` और `SUPABASE_ANON_KEY` चाहिए। OTP टैब छुपाना हो तो Secrets में `DISABLE_OTP = \"true\"` डालो।"),
    "`supabase` package install nahi hai. requirements.txt me `supabase` aur `extra-streamlit-components` add karo.": (
        "The `supabase` package is not installed. Add `supabase` and `extra-streamlit-components` to requirements.txt.",
        "`supabase` पैकेज इंस्टॉल नहीं है। requirements.txt में `supabase` और `extra-streamlit-components` जोड़ो।"),
}

STR.update({
    "Sawal ban rahe hain…": ("Making questions…", "प्रश्न बन रहे हैं…"),
    "{a} / {b} sawal ban gaye…": ("{a} / {b} questions ready…", "{a} / {b} प्रश्न बन गए…"),
    "🎙️ Voice": ("🎙️ Voice", "🎙️ आवाज़"),
    "⏱️ Timer": ("⏱️ Timer", "⏱️ टाइमर"),
    "❤️ Survival": ("❤️ Survival", "❤️ सर्वाइवल"),
    "🏅 XP & Badges": ("🏅 XP & Badges", "🏅 XP और बैज"),
    "📜 PYQ": ("📜 PYQ", "📜 PYQ"),
    "Email service abhi set nahi hai (confirmation mail nahi ja sakti). Admin Supabase me SMTP set kare ya 'Confirm email' band kare. Tab tak Guest bano.": (
        "The email service is not set up (the confirmation mail cannot be sent). The admin should set SMTP in Supabase or turn off 'Confirm email'. Until then continue as Guest.",
        "ईमेल सर्विस सेट नहीं है (कन्फ़र्मेशन मेल नहीं जा सकती)। एडमिन Supabase में SMTP सेट करे या 'Confirm email' बंद करे। तब तक गेस्ट बनो।"),
})

# long texts that app.py needs to reference without retyping them
ADMIN_HELP = next(k for k in STR if k.startswith("**Email OTP:**"))
SVC_MSG = next(k for k in STR if k.startswith("OTP service abhi set nahi hai."))
EMAIL_SVC_MSG = next(k for k in STR if k.startswith("Email service abhi set nahi hai"))
