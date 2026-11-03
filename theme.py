"""
theme.py — premium look & feel for AI Quiz Arena.
Pure CSS + HTML helpers with dynamic language switching support and modern Glassmorphism Sidebar.
"""
import html
from datetime import datetime, timedelta
import i18n

TXT = {
    "gm": {"en": "Good morning", "hi": "सुप्रभात"},
    "ga": {"en": "Good afternoon", "hi": "नमस्कार"},
    "ge": {"en": "Good evening", "hi": "शुभ संध्या"},
    "gn": {"en": "Late-night grind", "hi": "शुभ रात्रि"},
    "guest": {"en": "Guest", "hi": "मेहमान"},
    "lvl": {"en": "Level", "hi": "लेवल"},
    "xp_next": {"en": "{n} XP to next level", "hi": "अगले लेवल तक {n} XP"},
    "t_level": {"en": "Level", "hi": "लेवल"},
    "t_xp": {"en": "Total XP", "hi": "कुल XP"},
    "t_quiz": {"en": "Quizzes played", "hi": "खेले क्विज़"},
    "t_best": {"en": "Best score", "hi": "सर्वश्रेष्ठ स्कोर"},
    "c1": {"en": "SSC · NEET · JEE · UP CNET", "hi": "SSC · NEET · JEE · UP CNET"},
    "c2": {"en": "Solve doubts with camera", "hi": "कैमरे से डाउट हल करो"},
    "c3": {"en": "English & Hindi Support", "hi": "अंग्रेज़ी एवं हिन्दी सहायता"},
}

def _x(key, **fmt):
    row = TXT[key]
    lang = i18n.cur()
    s = row.get(lang, row["en"])
    return s.format(**fmt) if fmt else s

def greeting():
    h = (datetime.utcnow() + timedelta(hours=5, minutes=30)).hour
    return _x("gm" if 5 <= h < 12 else "ga" if 12 <= h < 17 else "ge" if 17 <= h < 22 else "gn")

def _e(s):
    return html.escape(str(s))

def hero_html(app_name, tagline, steps_html="", who=None, level=None, show_chips=True):
    top = ""
    if who is not None:
        initial = (_e(who)[:1] or "?").upper()
        top = (
            f"<div class='qf-hero-top'><div class='qf-avatar'>{initial}</div>"
            f"<div class='qf-greet'><div class='g1'>{_e(greeting())} 👋</div><div class='g2'>{_e(who)}</div></div>"
            + (f"<div class='qf-lvlpill'>⭐ {_x('lvl')} {level}</div>" if level else "")
            + "</div>"
        )
    chips = (
        f"<div class='qf-chips'><span>🏛️ {_e(_x('c1'))}</span><span>📸 {_e(_x('c2'))}</span><span>🌐 {_e(_x('c3'))}</span></div>"
        if show_chips
        else ""
    )
    return (
        "<div class='qf-hero'><span class='qf-glow'></span>"
        "<span class='qf-orb o1'></span><span class='qf-orb o2'></span><span class='qf-orb o3'></span>"
        f"{top}<div class='qf-title qf-display'>{_e(app_name)}</div>"
        f"<div class='qf-sub'>{_e(tagline)}</div>{chips}"
        f"<div class='qf-steps'>{steps_html}</div></div>"
    )

PREMIUM_CSS = """
<style>
:root{ --card-solid:#111733; --glow:rgba(124,92,255,.38); --ease:cubic-bezier(.2,.8,.2,1); }
::selection{ background:rgba(124,92,255,.45); color:#fff; }
html{ scroll-behavior:smooth; }

/* ── MODERN GLASS SIDEBAR STYLING ── */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0F172A 0%, #0B0F1E 100%) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
  padding-top: 1rem;
}

.sidebar-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 14px;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.sidebar-card:hover {
  border-color: rgba(124, 92, 255, 0.4);
  transform: translateY(-2px);
}

.sidebar-card h3 {
  font-size: 0.95rem !important;
  font-weight: 700 !important;
  color: #A5B4FC !important;
  margin-bottom: 10px !important;
}

/* ── GENERAL UI ELEMENTS ── */
.stApp{ isolation:isolate; }
.qf-hero{
  padding:30px 32px 26px; border-radius:30px; border:1px solid rgba(255,255,255,.16);
  background: linear-gradient(115deg, rgba(124,92,255,.85), rgba(79,140,255,.55) 45%, rgba(34,211,238,.45) 80%, rgba(124,92,255,.7));
  box-shadow:0 30px 70px -28px rgba(124,92,255,.65);
}
.qf-title{ font-size:3.1rem; background:linear-gradient(90deg,#fff 5%,#E6DFFF 50%,#BFF4FF 95%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.stButton>button, [data-testid="stFormSubmitButton"]>button{
  border-radius:14px; min-height:46px; font-weight:700;
}
.stTabs button[data-baseweb="tab"][aria-selected="true"]{
  color:#fff; background:linear-gradient(135deg,#7C5CFF,#4F8CFF 60%,#22D3EE);
}
</style>
"""

PREMIUM_LIGHT_CSS = """
<style>
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #F8FAFC 0%, #E2E8F0 100%) !important;
}
.sidebar-card {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
}
.sidebar-card h3 {
  color: #4F46E5 !important;
}
</style>
"""
