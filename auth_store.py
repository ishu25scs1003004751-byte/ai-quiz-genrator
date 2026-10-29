"""
auth_store.py — Email / Phone OTP login + per-user saved data (history, XP, bookmarks).

Pure Python (sqlite3, smtplib, requests). No Streamlit import, so it is easy to test.
Settings are read through `get_setting(name)` which you can override from app.py
(app.py passes st.secrets first, then environment variables).

IMPORTANT (Streamlit Community Cloud): the local disk is wiped on every reboot/redeploy.
SQLite is fine for testing and for a VPS/Docker with a persistent volume. For production on
Streamlit Cloud, point APP_DB_PATH at a persistent volume or swap the small `_db()` layer for
Supabase/Postgres (all SQL here is plain and simple).
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import sqlite3
import time
from contextlib import contextmanager
from email.message import EmailMessage

OTP_LEN = 6
OTP_TTL = 10 * 60          # OTP valid for 10 minutes
OTP_RESEND_GAP = 30        # seconds between two OTP requests for the same email/number
OTP_MAX_TRIES = 5          # wrong attempts before the OTP is burned
OTP_MAX_PER_HOUR = 6       # OTP requests per email/number per hour
SESSION_TTL = 7 * 24 * 3600  # "stay logged in" token lifetime (7 days)

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

_settings_getter = lambda name, default=None: os.getenv(name, default)  # noqa: E731


def set_settings_getter(fn):
    """app.py calls this so secrets from st.secrets are used before environment variables."""
    global _settings_getter
    _settings_getter = fn


def get_setting(name, default=None):
    try:
        v = _settings_getter(name, default)
    except Exception:
        v = default
    return default if v in (None, "") else v


# ───────────────────────── database ─────────────────────────
def _db_path():
    return get_setting("APP_DB_PATH", os.path.join("data", "app.db"))


@contextmanager
def _db():
    path = _db_path()
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                phone TEXT UNIQUE,
                created REAL
            );
            CREATE TABLE IF NOT EXISTS otps(
                ident TEXT PRIMARY KEY,
                code_hash TEXT,
                expires REAL,
                tries INTEGER DEFAULT 0,
                last_sent REAL,
                window_start REAL,
                sent_in_window INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS sessions(
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER,
                expires REAL
            );
            CREATE TABLE IF NOT EXISTS user_state(
                user_id INTEGER PRIMARY KEY,
                data TEXT,
                updated REAL
            );
            """
        )
        yield con
        con.commit()
    finally:
        con.close()


def _h(value: str) -> str:
    """Hash with a server-side pepper so stolen DB rows can't be used directly."""
    pepper = str(get_setting("APP_SECRET", "change-me-in-secrets"))
    return hmac.new(pepper.encode(), value.encode(), hashlib.sha256).hexdigest()


# ───────────────────────── identifiers ─────────────────────────
def normalize_email(s: str):
    s = (s or "").strip().lower()
    return s if _EMAIL_RE.match(s) else None


def normalize_phone(s: str, default_cc="+91"):
    """9876543210, 09876543210, 919876543210, +91 98765 43210 -> +919876543210."""
    raw = re.sub(r"[\s\-()]", "", s or "")
    if not raw:
        return None
    if raw.startswith("+"):
        digits = raw[1:]
        full = "+" + digits
    else:
        digits = raw.lstrip("0")
        if len(digits) == 12 and digits.startswith("91"):
            full = "+" + digits
        elif len(digits) == 10:
            full = default_cc + digits
        else:
            return None
    if not digits.isdigit() or not (8 <= len(full) - 1 <= 15):
        return None
    return full


def mask(ident: str) -> str:
    if "@" in ident:
        name, dom = ident.split("@", 1)
        return (name[:2] + "•••") + "@" + dom
    return ident[:3] + "••••" + ident[-3:]


# ───────────────────────── senders ─────────────────────────
def email_configured() -> bool:
    return bool(get_setting("SMTP_HOST") and get_setting("SMTP_USER") and get_setting("SMTP_PASSWORD"))


def sms_configured() -> bool:
    return bool(get_setting("TWILIO_SID") and get_setting("TWILIO_TOKEN") and get_setting("TWILIO_FROM"))


def dev_show_otp() -> bool:
    return str(get_setting("DEV_SHOW_OTP", "0")).strip().lower() in ("1", "true", "yes")


def _send_email(to: str, code: str, app_name: str):
    msg = EmailMessage()
    msg["Subject"] = f"{app_name} login code: {code}"
    msg["From"] = get_setting("SMTP_FROM", get_setting("SMTP_USER"))
    msg["To"] = to
    msg.set_content(
        f"Your {app_name} login code is {code}.\n"
        f"It is valid for {OTP_TTL // 60} minutes. If you did not request it, ignore this email."
    )
    host, port = get_setting("SMTP_HOST"), int(get_setting("SMTP_PORT", 587))
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=15) as s:
            s.login(get_setting("SMTP_USER"), get_setting("SMTP_PASSWORD"))
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.starttls()
            s.login(get_setting("SMTP_USER"), get_setting("SMTP_PASSWORD"))
            s.send_message(msg)


def _send_sms(to: str, code: str, app_name: str):
    import requests  # imported lazily so email-only setups don't need it

    sid, token = get_setting("TWILIO_SID"), get_setting("TWILIO_TOKEN")
    r = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        data={"From": get_setting("TWILIO_FROM"), "To": to, "Body": f"{app_name} login code: {code}. Valid {OTP_TTL // 60} min."},
        auth=(sid, token),
        timeout=15,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"SMS provider error {r.status_code}")


# ───────────────────────── OTP flow ─────────────────────────
def request_otp(ident: str, kind: str, app_name: str):
    """
    Returns (ok: bool, message_key: str, dev_code: str|None).
    message_key is a short code the UI translates: sent, wait, too_many, not_configured, send_failed, bad_id
    """
    ident = normalize_email(ident) if kind == "email" else normalize_phone(ident)
    if not ident:
        return False, "bad_id", None

    configured = email_configured() if kind == "email" else sms_configured()
    if not configured and not dev_show_otp():
        return False, "not_configured", None

    now = time.time()
    with _db() as con:
        row = con.execute("SELECT * FROM otps WHERE ident=?", (ident,)).fetchone()
        window_start, sent = (now, 0)
        if row:
            if now - (row["last_sent"] or 0) < OTP_RESEND_GAP:
                return False, "wait", None
            if now - (row["window_start"] or 0) < 3600:
                window_start, sent = row["window_start"], row["sent_in_window"] or 0
                if sent >= OTP_MAX_PER_HOUR:
                    return False, "too_many", None
        code = "".join(str(secrets.randbelow(10)) for _ in range(OTP_LEN))
        con.execute(
            "INSERT OR REPLACE INTO otps(ident, code_hash, expires, tries, last_sent, window_start, sent_in_window) VALUES(?,?,?,?,?,?,?)",
            (ident, _h(ident + ":" + code), now + OTP_TTL, 0, now, window_start, sent + 1),
        )

    if configured:
        try:
            (_send_email if kind == "email" else _send_sms)(ident, code, app_name)
        except Exception:
            return False, "send_failed", None
        return True, "sent", None
    return True, "sent", code  # DEV mode: the UI shows the code on screen


def verify_otp(ident: str, kind: str, code: str):
    """Returns (user_id | None, message_key). message_key: ok, expired, wrong, locked, bad_id"""
    ident = normalize_email(ident) if kind == "email" else normalize_phone(ident)
    code = re.sub(r"\D", "", code or "")
    if not ident:
        return None, "bad_id"
    now = time.time()
    with _db() as con:
        row = con.execute("SELECT * FROM otps WHERE ident=?", (ident,)).fetchone()
        if not row or now > (row["expires"] or 0):
            return None, "expired"
        if (row["tries"] or 0) >= OTP_MAX_TRIES:
            return None, "locked"
        if not hmac.compare_digest(row["code_hash"], _h(ident + ":" + code)):
            con.execute("UPDATE otps SET tries = tries + 1 WHERE ident=?", (ident,))
            return None, "wrong"
        con.execute("DELETE FROM otps WHERE ident=?", (ident,))  # one-time use
        col = "email" if kind == "email" else "phone"
        u = con.execute(f"SELECT id FROM users WHERE {col}=?", (ident,)).fetchone()
        if u:
            uid = u["id"]
        else:
            cur = con.execute(f"INSERT INTO users({col}, created) VALUES(?,?)", (ident, now))
            uid = cur.lastrowid
        return uid, "ok"


# ───────────────────────── sessions ─────────────────────────
def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with _db() as con:
        con.execute("DELETE FROM sessions WHERE expires < ?", (time.time(),))
        con.execute("INSERT INTO sessions(token_hash, user_id, expires) VALUES(?,?,?)", (_h(token), user_id, time.time() + SESSION_TTL))
    return token


def user_from_token(token: str):
    """Returns {'id','email','phone'} or None."""
    if not token:
        return None
    with _db() as con:
        s = con.execute("SELECT user_id, expires FROM sessions WHERE token_hash=?", (_h(token),)).fetchone()
        if not s or time.time() > s["expires"]:
            return None
        u = con.execute("SELECT id, email, phone FROM users WHERE id=?", (s["user_id"],)).fetchone()
        return dict(u) if u else None


def end_session(token: str):
    if not token:
        return
    with _db() as con:
        con.execute("DELETE FROM sessions WHERE token_hash=?", (_h(token),))


# ───────────────────────── per-user data ─────────────────────────
def save_state(user_id: int, data: dict):
    blob = json.dumps(data, ensure_ascii=False)
    if len(blob) > 3_000_000:  # keep rows sane
        data = {**data, "history": data.get("history", [])[-100:], "bookmarks": data.get("bookmarks", [])[:100]}
        blob = json.dumps(data, ensure_ascii=False)
    with _db() as con:
        con.execute("INSERT OR REPLACE INTO user_state(user_id, data, updated) VALUES(?,?,?)", (user_id, blob, time.time()))


def load_state(user_id: int):
    with _db() as con:
        r = con.execute("SELECT data FROM user_state WHERE user_id=?", (user_id,)).fetchone()
    if not r:
        return None
    try:
        return json.loads(r["data"])
    except Exception:
        return None
