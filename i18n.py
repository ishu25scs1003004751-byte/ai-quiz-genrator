"""
i18n.py — language switching engine for AI Quiz Arena   (English 🇬🇧  /  हिंदी 🇮🇳)

What the app needs (3 lines):
    import i18n
    from i18n import T            # T("text") / T("template {n}", n=5)  -> text in the active language
    i18n.setup_language()         # once, right after st.set_page_config(...)
    i18n.language_switcher()      # draw the switcher (sidebar by default)

How it works
* translations.py holds every string (English + Hindi).  tr()/T() look the text up for the active language.
* install() wraps st.markdown / st.button / st.selectbox / st.toast / ... so static labels, headings,
  placeholders, help texts, messages and option lists are translated automatically at render time.
  Dynamic text uses T("template {x}", x=...).
* Switching = a normal Streamlit rerun -> instant, no page refresh.  Values typed / chosen in keyed widgets are
  kept across the switch.
* The choice is saved in the browser's localStorage ("qf_lang") and mirrored in the URL (?lang=hi);
  first-time visitors get English.
"""
import functools
import re

import streamlit as st
import streamlit.components.v1 as components

from translations import ADMIN_HELP, EMAIL_SVC_MSG, KEYS, SVC_MSG, TABLE  # noqa: F401  (re-exported)

# ── Languages ────────────────────────────────────────────────────────────────
DEFAULT = "en"
UI_LANGS = [("en", "🇬🇧", "English"), ("hi", "🇮🇳", "हिंदी")]
_VALID = {c for c, _, _ in UI_LANGS}
LANGS = {"English": "en", "हिंदी": "hi"}          # kept for backward compatibility
LANG_ORDER = ["English", "हिंदी"]
QUIZ_LANG_OF = {"en": "English", "hi": "Hindi", "English": "English", "Hindi": "Hindi", "Hinglish": "Hinglish"}

_LOOKUP = {}
for _src, _en, _hi in TABLE:
    _LOOKUP[_src] = {"en": _en if _en is not None else _src, "hi": _hi if _hi is not None else _src}


# ── State ────────────────────────────────────────────────────────────────────
def cur():
    """Active UI language: 'en' or 'hi'."""
    try:
        v = st.session_state.get("ui_lang", DEFAULT)
    except Exception:
        return DEFAULT
    return v if v in _VALID else DEFAULT


def init_ui_lang():
    """Session -> ?lang= in the URL -> English."""
    if st.session_state.get("ui_lang") in _VALID:
        return
    q = None
    try:
        q = st.query_params.get("lang")
    except Exception:
        pass
    st.session_state["ui_lang"] = q if q in _VALID else DEFAULT


def set_ui_lang(code):
    st.session_state["ui_lang"] = code if code in _VALID else DEFAULT


def content_lang():
    """Language for generated quiz text / AI answers: 'English' | 'Hindi' | 'Hinglish'.
    Follows the app language unless the user picked something else in Sidebar → Advanced."""
    pref = st.session_state.get("content_lang_pref", "Same as app language")
    if pref in ("English", "Hindi", "Hinglish"):
        return pref
    return "Hindi" if cur() == "hi" else "English"


# ── Translation ──────────────────────────────────────────────────────────────
_MISSING = set()
_DONE = set()      # (lang, text) pairs produced by T(..., **fmt): already translated, don't look them up again


def _note_missing(s):
    if len(_MISSING) < 500 and 2 < len(s) < 400 and any(c.isalpha() for c in s) and not s.lstrip().startswith("<") and not re.search("[\u0900-\u097F]", s):
        _MISSING.add(s)


class Raw(str):
    """Marks text that must NEVER be translated (AI-generated quiz content, user text)."""


def raw(s):
    return Raw(s)


def tr(s):
    """Translate one string for the active language (returned unchanged if unknown)."""
    if not isinstance(s, str):
        return s
    if isinstance(s, Raw):
        return str.__str__(s)
    lang = cur()
    if (lang, s) in _DONE:
        return s
    row = _LOOKUP.get(s)
    if row is None and s != s.strip() and s.strip():            # tolerate stray spaces / newlines
        core = _LOOKUP.get(s.strip())
        if core is not None:
            return s[: len(s) - len(s.lstrip())] + core[lang] + s[len(s.rstrip()):]
    if row is None:
        _note_missing(s)
        return s
    return row[lang]


def T(text, **fmt):
    """THE translation function.  T("Check answer")  or  T("{n} question(s) saved", n=3)."""
    out = tr(text)
    if fmt:
        try:
            out = out.format(**fmt)
        except Exception:
            try:
                out = text.format(**fmt)
            except Exception:
                return out
        if len(_DONE) > 3000:
            _DONE.clear()
        _DONE.add((cur(), out))
    return out


tf = T


def t(key, **fmt):
    """Named strings from translations.KEYS."""
    row = KEYS.get(key, {})
    txt = row.get(cur()) or row.get("en") or key
    return txt.format(**fmt) if fmt else txt


_MONTHS_HI = {"Jan": "जन", "Feb": "फ़र", "Mar": "मार्च", "Apr": "अप्रैल", "May": "मई", "Jun": "जून",
              "Jul": "जुल", "Aug": "अग", "Sep": "सित", "Oct": "अक्टू", "Nov": "नव", "Dec": "दिस"}


def loc_date(s):
    """'03 Nov, 14:20' -> '03 नव, 14:20' in Hindi (English text unchanged)."""
    if cur() != "hi" or not isinstance(s, str):
        return s
    return re.sub(r"\b(" + "|".join(_MONTHS_HI) + r")\b", lambda m: _MONTHS_HI[m.group(1)], s)


def all_forms():
    return []


# ── Keep widget values when the language changes ─────────────────────────────
# A widget's identity in Streamlit depends on its label; the label changes with the language, which would
# reset sliders/toggles/inputs.  So: on a switch we snapshot every keyed widget's value and put it back
# (before the widget is created) on the next run.
_STATEFUL = {"toggle", "checkbox", "slider", "select_slider", "selectbox", "radio", "multiselect",
             "text_input", "text_area", "number_input", "pills", "segmented_control", "date_input",
             "time_input", "color_picker"}
try:  # we restore values through the Session State API on purpose -> hide Streamlit's "default value" notice
    from streamlit.elements.lib import policies as _policies
    _policies._shown_default_value_warning = True
except Exception:
    pass


def _remember_key(name, kwargs):
    key = kwargs.get("key")
    if key is None or name not in _STATEFUL:
        return
    ss = st.session_state
    snap = ss.get("_qf_snap")
    if snap and key in snap["vals"]:
        try:
            ss[key] = snap["vals"].pop(key)
        except Exception:
            pass
    ss.setdefault("_qf_keys_now", set()).add(key)


def _take_snapshot():
    ss = st.session_state
    vals = {}
    for k in list(ss.get("_qf_keys_now", ())):
        try:
            if k in ss:
                vals[k] = ss[k]
        except Exception:
            pass
    ss["_qf_snap"] = {"vals": vals, "age": 0}


def _begin_run():
    ss = st.session_state
    snap = ss.get("_qf_snap")
    if snap:
        if snap["age"] >= 1:
            del ss["_qf_snap"]
        else:
            snap["age"] += 1
    ss["_qf_keys_now"] = set()


# ── Automatic translation of Streamlit calls ─────────────────────────────────
_TEXT_FIRST = (
    "markdown", "caption", "success", "info", "warning", "error", "subheader", "header", "title",
    "button", "download_button", "form_submit_button", "toggle", "checkbox", "slider", "select_slider",
    "selectbox", "radio", "multiselect", "text_input", "text_area", "number_input", "file_uploader",
    "camera_input", "expander", "spinner", "progress",
    "toast", "popover", "status", "dialog", "chat_input", "metric", "link_button", "text",
    "pills", "segmented_control", "date_input", "time_input", "color_picker", "write", "image",
)
_OPTION_WIDGETS = ("selectbox", "radio", "multiselect", "select_slider", "pills", "segmented_control")
_STR_KWARGS = ("help", "placeholder", "text", "label", "body", "caption", "title", "message")


def _fmt_func(o):
    return tr(str(o))


def _wrap(fn, name, is_method):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
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
            _remember_key(name, kwargs)
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


# ── Persistence: localStorage <-> server ─────────────────────────────────────
_SYNC_JS = """<script>(function(){try{
var P=window.parent,L=P.localStorage,K='qf_lang',cur='__CUR__',restore=__RESTORE__;
var ok={en:1,hi:1},saved=null;try{saved=L.getItem(K);}catch(e){}
var u=new URL(P.location.href);
if(restore&&saved&&ok[saved]&&saved!==cur&&u.searchParams.get('lang')!==saved){
  u.searchParams.set('lang',saved);P.location.replace(u.toString());return;}
try{L.setItem(K,cur);}catch(e){}
try{P.document.documentElement.lang=cur;}catch(e){}
if(u.searchParams.get('lang')!==cur){u.searchParams.set('lang',cur);P.history.replaceState(null,'',u.toString());}
}catch(e){}})();</script>"""


def _sync_js():
    first = not st.session_state.get("_qf_lang_restored", False)
    st.session_state["_qf_lang_restored"] = True
    code = _SYNC_JS.replace("__CUR__", cur()).replace("__RESTORE__", "true" if first else "false")
    try:
        components.html(code, height=0)
    except Exception:
        pass


# ── Switcher UI ──────────────────────────────────────────────────────────────
_SWITCH_CSS = """<style>
div[data-testid="stElementContainer"]:has(> iframe[height="0"]),
div.element-container:has(> iframe[height="0"]){ position:absolute !important; width:0; height:0; overflow:hidden; margin:0 !important; }
[class*="st-key-qf_lang"]{ margin:2px 0 10px; }
[class*="st-key-qf_lang"].qf-compact, .st-key-qf_lang_login{ max-width:300px; margin-left:auto; }
[class*="st-key-qf_lang"] [role="radiogroup"]{
  display:flex !important; flex-wrap:nowrap; gap:4px; padding:4px; width:100%; border-radius:16px;
  background:rgba(255,255,255,.06); border:1px solid var(--line, rgba(255,255,255,.14)); backdrop-filter:blur(6px);
}
[class*="st-key-qf_lang"] label[data-baseweb="radio"]{
  flex:1 1 0; justify-content:center; margin:0 !important; padding:8px 10px !important; min-height:40px;
  border-radius:12px !important; border:0 !important; background:transparent !important; cursor:pointer;
  transition:background .25s cubic-bezier(.2,.8,.2,1), transform .15s, box-shadow .25s;
}
[class*="st-key-qf_lang"] label[data-baseweb="radio"] > div:first-child{ display:none !important; }
[class*="st-key-qf_lang"] label[data-baseweb="radio"]::before, [class*="st-key-qf_lang"] label[data-baseweb="radio"]::after{ content:none !important; display:none !important; }
[class*="st-key-qf_lang"] label[data-baseweb="radio"] p{ font-weight:700; font-size:.92rem; white-space:nowrap; margin:0; }
[class*="st-key-qf_lang"] label[data-baseweb="radio"]:hover{ background:rgba(124,92,255,.16) !important; transform:translateY(-1px); }
[class*="st-key-qf_lang"] label[data-baseweb="radio"]:has(input:checked){
  background:linear-gradient(135deg,#7C5CFF,#4F8CFF 60%,#22D3EE) !important; box-shadow:0 10px 24px -10px rgba(124,92,255,.85); transform:none;
}
[class*="st-key-qf_lang"] label[data-baseweb="radio"]:has(input:checked) p{ color:#fff !important; }
[class*="st-key-qf_lang"] label[data-baseweb="radio"]:focus-within{ outline:2px solid rgba(124,92,255,.6); outline-offset:2px; }
@media (max-width:640px){
  .st-key-qf_lang_login{ max-width:100%; }
  [class*="st-key-qf_lang"] label[data-baseweb="radio"]{ padding:7px 6px !important; min-height:38px; }
  [class*="st-key-qf_lang"] label[data-baseweb="radio"] p{ font-size:.86rem; }
}
</style>"""


def _label(code):
    for c, flag, name in UI_LANGS:
        if c == code:
            return f"{flag} {name}"
    return code


def _on_pick(widget_key):
    new = st.session_state.get(widget_key)
    if new in _VALID and new != cur():
        _take_snapshot()                       # keep other widgets' values across the switch
        set_ui_lang(new)


def language_switcher(where="sidebar", key="qf_lang", sync=True, show_label=True):
    """Draw the English / हिंदी switcher.  where = "sidebar" | "main".
    Key must start with "qf_lang" (the CSS relies on it).  A second switcher on the same page: other key, sync=False."""
    init_ui_lang()
    host = st.sidebar if where == "sidebar" else st
    host.markdown(_SWITCH_CSS, unsafe_allow_html=True)
    wkey = f"{key}_radio"
    st.session_state[wkey] = cur()
    with host.container(key=key):
        st.radio(
            t("app_language"), [c for c, _, _ in UI_LANGS], format_func=_label, horizontal=True,
            key=wkey, on_change=_on_pick, args=(wkey,),
            label_visibility="visible" if show_label else "collapsed",
        )
    if sync:
        _sync_js()


def setup_language():
    """ONE call that prepares everything language-related.  Put it right after st.set_page_config()."""
    install()
    init_ui_lang()
    _begin_run()


def debug_panel():
    """Optional (end of app): with ?i18n_debug=1 in the URL, lists text that had no translation.
    (AI-generated quiz text and user text also show up here - that is expected.)"""
    try:
        if st.query_params.get("i18n_debug") != "1":
            return
    except Exception:
        return
    with st.sidebar.expander("🐞 i18n: untranslated text"):
        st.code("\n".join(sorted(_MISSING)) or "— nothing missing —", language=None)


install()
