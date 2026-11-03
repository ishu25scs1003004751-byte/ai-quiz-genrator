"""
i18n.py — Complete language translation module for AI Quiz Arena.
Handles English 🇬🇧 and हिन्दी 🇮🇳 language switching seamlessly.
"""
import functools
import streamlit as st

LANGS = {"English 🇬🇧": "en", "हिन्दी 🇮🇳": "hi"}
LANG_ORDER = ["English 🇬🇧", "हिन्दी 🇮🇳"]
DEFAULT = "en"

QUIZ_LANG_OF = {
    "en": "English",
    "hi": "Hindi",
    "English 🇬🇧": "English",
    "हिन्दी 🇮🇳": "Hindi"
}

TABLE = [
    ("### ⚙️ Quiz Settings", "### ⚙️ क्विज़ सेटिंग्स"),
    ("Questions", "प्रश्नों की संख्या"),
    ("Difficulty", "कठिनाई"),
    ("Easy", "आसान"),
    ("Medium", "मध्यम"),
    ("Hard", "कठिन"),
    ("🎚️ Adaptive difficulty", "🎚️ अनुकूल कठिनाई"),
    ("Question types", "प्रश्नों के प्रकार"),
    ("Language", "भाषा"),
    ("Mode", "मोड"),
    ("Practice", "प्रैक्टिस"),
    ("Exam", "एग्ज़ाम"),
    ("Survival", "सर्वाइवल"),
    ("🧠 Quiz Arena", "🧠 क्विज़ एरीना"),
    ("🏛️ Govt Exam PYQs", "🏛️ सरकारी परीक्षा PYQ"),
    ("🔍 Doubt Solver", "🔍 डाउट सॉल्वर"),
    ("Where will the content come from?", "सामग्री कहाँ से आएगी?"),
    ("💡 Topic", "💡 टॉपिक"),
    ("📄 PDF", "📄 PDF"),
    ("🖼️ Photo / Camera", "🖼️ फ़ोटो / कैमरा"),
    ("📝 Notes", "📝 नोट्स"),
    ("Which topic do you want a quiz on?", "किस टॉपिक पर क्विज़ चाहिए?"),
    ("Make quiz", "✨ क्विज़ बनाओ"),
    ("Write your doubt here", "अपना डाउट यहाँ लिखो"),
    ("💡 Explain", "💡 समझाओ"),
]

KEYS = {
    "app_tag": {
        "en": "Provide a topic, PDF or notes photo — AI generates quizzes instantly.",
        "hi": "टॉपिक, PDF या नोट्स की फ़ोटो दो — AI तुरंत क्विज़ बनाता है।"
    }
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
