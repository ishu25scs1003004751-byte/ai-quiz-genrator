"""
theme.py — premium look & feel for AI Quiz Arena.

Loaded AFTER the app's base CSS, so these rules refine/override it. Pure CSS + a little HTML:
no extra libraries, nothing to install. Respects light mode and `prefers-reduced-motion`.
"""
import html
from datetime import datetime, timedelta

import i18n

# small text table for the new hero / tiles (hg = Hinglish, en, hi)
TXT = {
    "gm": {"hg": "Suprabhat", "en": "Good morning", "hi": "सुप्रभात"},
    "ga": {"hg": "Namaste", "en": "Good afternoon", "hi": "नमस्कार"},
    "ge": {"hg": "Shubh sandhya", "en": "Good evening", "hi": "शुभ संध्या"},
    "gn": {"hg": "Shubh ratri", "en": "Late-night grind", "hi": "शुभ रात्रि"},
    "guest": {"hg": "Mehmaan", "en": "Guest", "hi": "मेहमान"},
    "lvl": {"hg": "Level", "en": "Level", "hi": "लेवल"},
    "xp_next": {"hg": "agle level tak {n} XP", "en": "{n} XP to next level", "hi": "अगले लेवल तक {n} XP"},
    "t_level": {"hg": "Level", "en": "Level", "hi": "लेवल"},
    "t_xp": {"hg": "Total XP", "en": "Total XP", "hi": "कुल XP"},
    "t_quiz": {"hg": "Quizzes khele", "en": "Quizzes played", "hi": "खेले क्विज़"},
    "t_best": {"hg": "Best score", "en": "Best score", "hi": "सर्वश्रेष्ठ स्कोर"},
    "c1": {"hg": "SSC · NEET · JEE · UP CNET", "en": "SSC · NEET · JEE · UP CNET", "hi": "SSC · NEET · JEE · UP CNET"},
    "c2": {"hg": "Camera se doubt solve", "en": "Solve doubts with camera", "hi": "कैमरे से डाउट हल करो"},
    "c3": {"hg": "3 bhashayein", "en": "3 languages", "hi": "3 भाषाएँ"},
}


def _x(key, **fmt):
    row = TXT[key]
    s = row.get(i18n.cur()) or row["hg"]
    return s.format(**fmt) if fmt else s


def greeting():
    h = (datetime.utcnow() + timedelta(hours=5, minutes=30)).hour  # IST
    return _x("gm" if 5 <= h < 12 else "ga" if 12 <= h < 17 else "ge" if 17 <= h < 22 else "gn")


def _e(s):
    return html.escape(str(s))


def hero_html(app_name, tagline, steps_html="", who=None, level=None, show_chips=True):
    """who = display name (or None for the logged-out hero)."""
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


def tiles_html(level, xp, played, best_pct):
    into = xp % 100
    return (
        "<div class='qf-tiles'>"
        f"<div class='qf-tile t1'><div class='ic'>🎖️</div><div class='v'>{level}</div><div class='l'>{_e(_x('t_level'))}</div>"
        f"<div class='bar' title='{_e(_x('xp_next', n=100 - into))}'><i style='width:{into}%'></i></div></div>"
        f"<div class='qf-tile t2'><div class='ic'>⚡</div><div class='v'>{xp}</div><div class='l'>{_e(_x('t_xp'))}</div></div>"
        f"<div class='qf-tile t3'><div class='ic'>🧠</div><div class='v'>{played}</div><div class='l'>{_e(_x('t_quiz'))}</div></div>"
        f"<div class='qf-tile t4'><div class='ic'>🏆</div><div class='v'>{best_pct}%</div><div class='l'>{_e(_x('t_best'))}</div></div>"
        "</div>"
    )


# Follows the mouse / finger inside the hero (sets --mx / --my). Added once, safe to re-run.
GLOW_JS = """<script>(function(){try{var D=window.parent.document;
if(D.body.dataset.qfGlow==='1')return;D.body.dataset.qfGlow='1';
D.addEventListener('pointermove',function(e){var h=D.querySelector('.qf-hero');if(!h)return;
var r=h.getBoundingClientRect();h.style.setProperty('--mx',(e.clientX-r.left)+'px');h.style.setProperty('--my',(e.clientY-r.top)+'px');},{passive:true});
}catch(e){}})();</script>"""


PREMIUM_CSS = """
<style>
:root{ --card-solid:#111733; --glow:rgba(124,92,255,.38); --ease:cubic-bezier(.2,.8,.2,1); }
::selection{ background:rgba(124,92,255,.45); color:#fff; }
html{ scroll-behavior:smooth; }
*::-webkit-scrollbar{ width:10px; height:10px; }
*::-webkit-scrollbar-thumb{ background:linear-gradient(180deg,#7C5CFF,#22D3EE); border-radius:99px; border:2px solid transparent; background-clip:padding-box; }
*::-webkit-scrollbar-track{ background:transparent; }

/* ── Living background: slow drifting aurora ── */
.stApp{ isolation:isolate; }
.stApp::before{
  content:""; position:fixed; inset:-25%; z-index:-1; pointer-events:none; filter:blur(50px); opacity:.9;
  background:
    radial-gradient(38% 32% at 18% 22%, rgba(124,92,255,.30), transparent 70%),
    radial-gradient(34% 30% at 82% 16%, rgba(34,211,238,.22), transparent 70%),
    radial-gradient(40% 34% at 70% 86%, rgba(255,200,87,.12), transparent 70%),
    radial-gradient(30% 30% at 12% 90%, rgba(251,113,133,.12), transparent 70%);
  animation:qf-drift 26s ease-in-out infinite alternate;
}
@keyframes qf-drift{ from{ transform:translate3d(-2%,-1%,0) scale(1); } to{ transform:translate3d(3%,2%,0) scale(1.08); } }

@keyframes qf-up{ from{ opacity:0; transform:translateY(14px); } to{ opacity:1; transform:none; } }

/* ── HERO ── */
.qf-hero{
  --mx:70%; --my:0%;
  padding:30px 32px 26px; border-radius:30px; border:1px solid rgba(255,255,255,.16);
  background:
    linear-gradient(115deg, rgba(124,92,255,.85), rgba(79,140,255,.55) 45%, rgba(34,211,238,.45) 80%, rgba(124,92,255,.7)) 0 0/220% 220%;
  animation:qf-flow 16s ease-in-out infinite;
  box-shadow:0 30px 70px -28px rgba(124,92,255,.65), inset 0 1px 0 rgba(255,255,255,.25);
}
@keyframes qf-flow{ 0%,100%{ background-position:0% 50%; } 50%{ background-position:100% 50%; } }
.qf-hero:before{
  content:""; position:absolute; inset:0; pointer-events:none; opacity:.55;
  background:
    linear-gradient(rgba(255,255,255,.07) 1px, transparent 1px) 0 0/30px 30px,
    linear-gradient(90deg, rgba(255,255,255,.07) 1px, transparent 1px) 0 0/30px 30px;
  -webkit-mask:radial-gradient(120% 90% at 50% 0%, #000 30%, transparent 85%); mask:radial-gradient(120% 90% at 50% 0%, #000 30%, transparent 85%);
}
.qf-hero .qf-glow{ position:absolute; inset:0; pointer-events:none; background:radial-gradient(380px circle at var(--mx) var(--my), rgba(255,255,255,.22), transparent 60%); mix-blend-mode:soft-light; }
.qf-orb{ position:absolute; border-radius:50%; filter:blur(2px); pointer-events:none; }
.qf-orb.o1{ width:120px; height:120px; right:7%; top:14%; background:radial-gradient(circle at 30% 30%, #fff8, #FFC857aa 45%, transparent 70%); animation:qf-float 7s ease-in-out infinite; }
.qf-orb.o2{ width:64px; height:64px; right:24%; bottom:10%; background:radial-gradient(circle at 30% 30%, #fff9, #22D3EEaa 50%, transparent 72%); animation:qf-float 9s ease-in-out -2s infinite; }
.qf-orb.o3{ width:38px; height:38px; left:46%; top:8%; background:radial-gradient(circle at 30% 30%, #fff9, #FB7185aa 55%, transparent 75%); animation:qf-float 6s ease-in-out -4s infinite; }
@keyframes qf-float{ 0%,100%{ transform:translateY(0) rotate(0); } 50%{ transform:translateY(-14px) rotate(8deg); } }
.qf-hero > *{ position:relative; z-index:1; }
.qf-hero .qf-glow, .qf-hero .qf-orb{ position:absolute; z-index:0; }
.qf-hero-top{ display:flex; align-items:center; gap:12px; margin-bottom:14px; }
.qf-avatar{
  width:46px; height:46px; border-radius:15px; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:1.2rem;
  color:#0B0F1E; background:linear-gradient(135deg,#FFC857,#fff); box-shadow:0 8px 22px rgba(0,0,0,.28); font-family:'Space Grotesk',sans-serif;
}
.qf-greet .g1{ font-size:.82rem; color:rgba(255,255,255,.8); }
.qf-greet .g2{ font-weight:700; font-size:1.05rem; color:#fff; max-width:42vw; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.qf-lvlpill{ margin-left:auto; padding:6px 14px; border-radius:99px; font-weight:700; font-size:.82rem; color:#0B0F1E; background:linear-gradient(135deg,#FFC857,#FFE29A); box-shadow:0 6px 18px rgba(255,200,87,.4); }
.qf-title{ font-size:3.1rem; background:linear-gradient(90deg,#fff 5%,#E6DFFF 50%,#BFF4FF 95%); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; text-shadow:none; }
.qf-sub{ color:rgba(255,255,255,.88); }
.qf-chips{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }
.qf-chips span{ font-size:.78rem; font-weight:600; padding:6px 12px; border-radius:99px; color:#fff; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.22); backdrop-filter:blur(8px); transition:transform .2s var(--ease), background .2s; }
.qf-chips span:hover{ transform:translateY(-2px); background:rgba(255,255,255,.24); }
.qf-step{ color:#fff; border-color:rgba(255,255,255,.35); background:rgba(0,0,0,.18); backdrop-filter:blur(6px); }
.qf-step.on{ box-shadow:0 0 0 4px rgba(255,200,87,.25), 0 8px 20px rgba(255,200,87,.35); }
.qf-step.done{ background:rgba(52,211,153,.18); color:#B6FFE0; border-color:rgba(52,211,153,.6); }

/* ── Stat tiles ── */
.qf-tiles{ gap:14px; }
.qf-tile{
  position:relative; overflow:hidden; border-radius:20px; padding:16px 12px 14px; text-align:center;
  background:linear-gradient(160deg, rgba(255,255,255,.08), rgba(255,255,255,.025)); border:1px solid var(--line);
  transition:transform .25s var(--ease), box-shadow .25s var(--ease), border-color .25s;
}
.qf-tile:hover{ transform:translateY(-5px); border-color:rgba(124,92,255,.7); box-shadow:0 18px 40px -16px var(--glow); }
.qf-tile .ic{ font-size:1.25rem; margin-bottom:2px; }
.qf-tile .v{ font-size:1.75rem; background:linear-gradient(90deg,#fff,#C9BEFF); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
.qf-tile.t2 .v{ background:linear-gradient(90deg,#FFE29A,#FFC857); -webkit-background-clip:text; background-clip:text; }
.qf-tile.t4 .v{ background:linear-gradient(90deg,#B6FFE0,#34D399); -webkit-background-clip:text; background-clip:text; }
.qf-tile .bar{ height:5px; border-radius:99px; background:rgba(255,255,255,.12); margin:9px 8px 0; overflow:hidden; }
.qf-tile .bar i{ display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,#7C5CFF,#22D3EE); transition:width 1s var(--ease); }

/* ── Panels (glass with gradient edge) ── */
.st-key-panel, .st-key-panel_login, .st-key-panel_pyq, .st-key-panel_doubt, .st-key-optbox, .st-key-morebox{
  border:1px solid transparent; border-radius:24px; padding:22px 24px;
  background:
    linear-gradient(160deg, rgba(255,255,255,.055), rgba(255,255,255,.02)) padding-box,
    linear-gradient(135deg, rgba(124,92,255,.55), rgba(255,255,255,.08) 40%, rgba(34,211,238,.4)) border-box;
  box-shadow:0 20px 50px -30px rgba(0,0,0,.7);
  transition:box-shadow .3s var(--ease);
}
.st-key-panel:hover, .st-key-panel_pyq:hover, .st-key-panel_doubt:hover{ box-shadow:0 26px 60px -28px var(--glow); }
.st-key-panel_login{ max-width:520px; margin:6px auto 0; }

/* ── Tabs → segmented pill bar ── */
.stTabs [data-baseweb="tab-list"]{
  gap:6px; padding:6px; border-radius:18px; background:rgba(255,255,255,.05); border:1px solid var(--line);
  overflow-x:auto; scrollbar-width:none;
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{ display:none !important; }
.stTabs button[data-baseweb="tab"]{
  height:46px; padding:0 18px; border-radius:13px; font-weight:700; color:var(--mute); white-space:nowrap;
  transition:background .25s var(--ease), color .2s, transform .15s;
}
.stTabs button[data-baseweb="tab"]:hover{ color:var(--txt); background:rgba(255,255,255,.07); }
.stTabs button[data-baseweb="tab"][aria-selected="true"]{
  color:#fff; background:linear-gradient(135deg,#7C5CFF,#4F8CFF 60%,#22D3EE); box-shadow:0 10px 26px -8px rgba(124,92,255,.8);
}
.stTabs button[data-baseweb="tab"] p{ font-weight:700; }

/* ── Buttons ── */
.stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"]>button{
  position:relative; overflow:hidden; border-radius:15px; min-height:46px;
  transition:transform .15s var(--ease), box-shadow .25s, border-color .2s, background .2s;
}
.stButton>button:hover, .stDownloadButton>button:hover{ box-shadow:0 12px 28px -14px var(--glow); }
.stButton>button:active, .stDownloadButton>button:active{ transform:translateY(0) scale(.98); }
.stButton>button[kind="primary"], [data-testid="stBaseButton-primary"]{
  background:linear-gradient(120deg,#7C5CFF,#4F8CFF 50%,#22D3EE) 0 0/200% 100%; transition:background-position .6s var(--ease), transform .15s, box-shadow .25s;
  box-shadow:0 14px 34px -12px rgba(124,92,255,.85);
}
.stButton>button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover{ background-position:100% 0; box-shadow:0 18px 42px -12px rgba(79,140,255,.9); }
.stButton>button[kind="primary"]::after, [data-testid="stBaseButton-primary"]::after{
  content:""; position:absolute; top:0; left:-60%; width:40%; height:100%; transform:skewX(-20deg);
  background:linear-gradient(90deg, transparent, rgba(255,255,255,.35), transparent); transition:left .7s var(--ease);
}
.stButton>button[kind="primary"]:hover::after, [data-testid="stBaseButton-primary"]:hover::after{ left:130%; }

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stNumberInput input{
  border-radius:14px !important; transition:box-shadow .2s, border-color .2s;
}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus{
  border-color:#7C5CFF !important; box-shadow:0 0 0 4px rgba(124,92,255,.22) !important;
}
div[data-baseweb="select"] > div{ border-radius:14px !important; border-color:var(--line) !important; transition:box-shadow .2s, border-color .2s; }
div[data-baseweb="select"] > div:focus-within{ border-color:#7C5CFF !important; box-shadow:0 0 0 4px rgba(124,92,255,.2); }
[data-testid="stFileUploaderDropzone"]{
  border:1.6px dashed rgba(124,92,255,.55) !important; border-radius:18px !important; background:rgba(124,92,255,.07) !important; transition:background .2s, transform .2s;
}
[data-testid="stFileUploaderDropzone"]:hover{ background:rgba(124,92,255,.14) !important; transform:scale(1.01); }
[data-testid="stCameraInput"] > div, [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img{ border-radius:20px; overflow:hidden; }
[data-testid="stCameraInput"] video{ box-shadow:0 20px 50px -20px rgba(0,0,0,.8); }

/* ── Source pills / radio pills ── */
.st-key-srcpick label[data-baseweb="radio"]{ padding:10px 18px; font-weight:600; transition:all .2s var(--ease); }
.st-key-srcpick label[data-baseweb="radio"]:hover{ transform:translateY(-2px); border-color:var(--cyan); }
.st-key-srcpick label[data-baseweb="radio"]:has(input:checked){ background:linear-gradient(135deg,rgba(124,92,255,.5),rgba(34,211,238,.28)); box-shadow:0 10px 26px -12px var(--glow); }

/* ── Progress ── */
.stProgress > div > div{ background:rgba(255,255,255,.08) !important; border-radius:99px; height:10px; }
.stProgress > div > div > div > div{
  border-radius:99px; background-size:200% 100%; animation:qf-slide 3s linear infinite;
  background-image:linear-gradient(90deg,#7C5CFF,#22D3EE,#7C5CFF);
}
@keyframes qf-slide{ to{ background-position:-200% 0; } }

/* ── Question card & options ── */
.qf-qcard{
  border:1px solid transparent; border-radius:26px; padding:26px 28px;
  background:
    linear-gradient(160deg, rgba(124,92,255,.16), rgba(255,255,255,.02)) padding-box,
    linear-gradient(135deg, rgba(124,92,255,.7), rgba(255,255,255,.08) 45%, rgba(255,200,87,.5)) border-box;
  box-shadow:0 24px 60px -30px var(--glow);
}
.qf-qnum{ letter-spacing:.08em; text-transform:uppercase; }
.qf-qtext{ font-size:1.5rem; }
.qf-tag{ backdrop-filter:blur(6px); background:rgba(255,255,255,.05); }
.st-key-optbox label[data-baseweb="radio"], .st-key-optbox label[data-baseweb="checkbox"]{
  border-radius:16px; padding:14px 16px; cursor:pointer; transition:transform .2s var(--ease), border-color .2s, background .2s, box-shadow .25s;
}
.st-key-optbox label[data-baseweb="radio"]:hover, .st-key-optbox label[data-baseweb="checkbox"]:hover{ transform:translateX(4px); box-shadow:0 10px 26px -16px var(--glow); }
.st-key-optbox label:has(input:checked){ box-shadow:0 0 0 3px rgba(124,92,255,.28), 0 14px 34px -14px var(--glow); transform:translateX(4px); }
.st-key-optbox label[data-baseweb="radio"]::before, .st-key-optbox label[data-baseweb="checkbox"]::before{ width:32px; height:32px; border-radius:11px; transition:transform .2s var(--ease), background .2s; }
.st-key-optbox label:has(input:checked)::before{ transform:scale(1.1) rotate(-4deg); }

/* ── Feedback, hints, alerts ── */
@keyframes qf-pop{ 0%{ opacity:0; transform:scale(.96) translateY(6px); } 100%{ opacity:1; transform:none; } }
.qf-fb{ position:relative; border-radius:18px; padding:16px 20px 16px 22px; animation:qf-pop .35s var(--ease) both; overflow:hidden; }
.qf-fb:before{ content:""; position:absolute; left:0; top:0; bottom:0; width:5px; }
.qf-fb.ok:before{ background:var(--good); } .qf-fb.no:before{ background:var(--bad); } .qf-fb.mid:before{ background:var(--amber); }
.qf-fb.ok{ box-shadow:0 14px 34px -22px rgba(52,211,153,.9); } .qf-fb.no{ box-shadow:0 14px 34px -22px rgba(251,113,133,.9); }
[data-testid="stAlert"]{ border-radius:16px; border:1px solid var(--line); backdrop-filter:blur(6px); animation:qf-pop .35s var(--ease) both; }
div[data-testid="stExpander"]{ border-radius:18px; overflow:hidden; transition:border-color .2s, box-shadow .25s; }
div[data-testid="stExpander"]:hover{ border-color:rgba(124,92,255,.55); box-shadow:0 14px 34px -22px var(--glow); }
.qf-hearts{ font-size:1.3rem; filter:drop-shadow(0 0 8px rgba(251,113,133,.6)); }

/* ── Chat (doubt solver) ── */
[data-testid="stChatMessage"]{
  background:linear-gradient(160deg, rgba(255,255,255,.06), rgba(255,255,255,.02)); border:1px solid var(--line);
  border-radius:20px; padding:14px 16px; margin-bottom:10px;
}

/* ── Result ── */
.qf-ring{ filter:drop-shadow(0 0 22px var(--ring-color)); }
.qf-ring-in .big{ background:linear-gradient(90deg,#fff,#C9BEFF); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
@keyframes qf-badge{ 0%{ transform:scale(.4); opacity:0; } 70%{ transform:scale(1.12); } 100%{ transform:scale(1); opacity:1; } }
.qf-badge{ animation:qf-badge .6s var(--ease) both; box-shadow:0 10px 26px -12px rgba(255,200,87,.7); }
.qf-badge:nth-child(2){ animation-delay:.1s; } .qf-badge:nth-child(3){ animation-delay:.2s; } .qf-badge:nth-child(4){ animation-delay:.3s; }
.qf-flash{ border-radius:28px; box-shadow:0 26px 60px -30px var(--glow); transition:transform .3s var(--ease); }
.qf-flash:hover{ transform:translateY(-3px) rotate(-.4deg); }

/* ── Sidebar ── */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#10163A,#0B0F1E) !important; border-right:1px solid var(--line); box-shadow:10px 0 40px -20px rgba(0,0,0,.7);
}
section[data-testid="stSidebar"] h3{ font-size:1.05rem; margin-top:.6rem; }
section[data-testid="stSidebar"] .stProgress > div > div{ height:8px; }
section[data-testid="stSidebar"] hr{ border-color:var(--line); }
#qf-sb-toggle{ transition:transform .2s var(--ease), box-shadow .2s; }
#qf-sb-toggle:active{ transform:scale(.94); }

/* ── Small screens ── */
@media (max-width:640px){
  .qf-hero{ padding:22px 18px 20px; border-radius:24px; }
  .qf-title{ font-size:2.2rem; }
  .qf-orb.o1{ width:80px; height:80px; right:-10px; }
  .qf-qcard{ padding:20px 18px; } .qf-qtext{ font-size:1.25rem; }
  .qf-tile .v{ font-size:1.45rem; }
  .stTabs button[data-baseweb="tab"]{ padding:0 12px; height:42px; font-size:.86rem; }
  .st-key-panel, .st-key-panel_pyq, .st-key-panel_doubt, .st-key-panel_login{ padding:16px 14px; border-radius:20px; }
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{ animation:none !important; transition:none !important; }
}
</style>
"""

PREMIUM_LIGHT_CSS = """
<style>
:root{ --card-solid:#ffffff; --glow:rgba(124,92,255,.25); }
.stApp::before{ opacity:.55; }
section[data-testid="stSidebar"]{ background:linear-gradient(180deg,#FFFFFF,#F1F2FB) !important; box-shadow:10px 0 40px -24px rgba(30,35,80,.3); }
.st-key-panel, .st-key-panel_login, .st-key-panel_pyq, .st-key-panel_doubt, .st-key-optbox, .st-key-morebox{
  background:
    linear-gradient(160deg, rgba(255,255,255,.95), rgba(255,255,255,.8)) padding-box,
    linear-gradient(135deg, rgba(124,92,255,.5), rgba(30,35,80,.08) 40%, rgba(34,211,238,.4)) border-box;
  box-shadow:0 20px 50px -34px rgba(30,35,80,.45);
}
.qf-qcard{
  background:
    linear-gradient(160deg, rgba(124,92,255,.10), rgba(255,255,255,.95)) padding-box,
    linear-gradient(135deg, rgba(124,92,255,.6), rgba(30,35,80,.08) 45%, rgba(255,200,87,.6)) border-box;
}
.qf-tile{ background:linear-gradient(160deg,#fff,rgba(255,255,255,.7)); }
.qf-tile .v{ background:linear-gradient(90deg,#4B3FD1,#7C5CFF); -webkit-background-clip:text; background-clip:text; }
.qf-tile.t2 .v{ background:linear-gradient(90deg,#B77900,#E39A00); -webkit-background-clip:text; background-clip:text; }
.qf-tile.t4 .v{ background:linear-gradient(90deg,#0B8F63,#34D399); -webkit-background-clip:text; background-clip:text; }
.qf-ring-in .big{ background:linear-gradient(90deg,#4B3FD1,#7C5CFF); -webkit-background-clip:text; background-clip:text; }
.stTabs [data-baseweb="tab-list"]{ background:rgba(255,255,255,.85); }
.stTabs button[data-baseweb="tab"]:hover{ background:rgba(124,92,255,.08); }
[data-testid="stChatMessage"]{ background:rgba(255,255,255,.85); }
</style>
"""
