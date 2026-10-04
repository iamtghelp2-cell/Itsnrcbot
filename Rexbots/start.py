cat << 'EOF' > Rexbots/start.py
# Developed by: LastPerson07 × RexBots
# Topic Router + Persistent User Login + Restricted Content Saver
import os
import re
import json
import time
import asyncio
import shutil
import unicodedata

from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired, PasswordHashInvalid
from pyrogram.types import Message

from config import API_ID, API_HASH, BOT_TOKEN
from database.db import db
from logger import LOGGER

logger = LOGGER(__name__)

HTML = enums.ParseMode.HTML
ENABLE_LIMIT = os.environ.get("ENABLE_LIMIT", "0") == "1"
SETTINGS_FILE = os.environ.get("SETTINGS_FILE", "user_settings.json")

RUNNING = set()
CANCEL = set()
LOGIN_STEPS = {}  # temporary login state

app = Client(
    "Itsnrcbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def _default_settings():
    return {
        "keywords": {},
        "topic_map": {},
        "default_topic": None,
        "clean_ads": False,
        "prefix": "",
        "suffix": "",
        "replace": {},
        "delete": [],
    }

class Settings:
    def __init__(self, path):
        self.path = path
        self.data = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            raw = {}
        for uid, s in raw.items():
            d = _default_settings()
            d.update(s)
            d["keywords"] = {k: int(v) for k, v in d["keywords"].items()}
            d["topic_map"] = {int(k): int(v) for k, v in d["topic_map"].items()}
            self.data[int(uid)] = d

    def get(self, uid):
        if uid not in self.data:
            self.data[uid] = _default_settings()
        return self.data[uid]

    def save(self):
        try:
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({str(k): v for k, v in self.data.items()}, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.path)
        except Exception as e:
            logger.error(f"Settings save failed: {e}")

SETTINGS = Settings(SETTINGS_FILE)

SMALL_CAPS = str.maketrans("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡʏᴢ", "abcdefghijklmnopqrstuvwyz")
INVISIBLE = set("\u200b\u200c\u200d\u2060\ufeff\ufe0f\u00ad")

def norm_map(text: str):
    out, idx = [], []
    for i, ch in enumerate(text):
        if ch in INVISIBLE:
            continue
        n = unicodedata.normalize("NFKC", ch).translate(SMALL_CAPS).lower()
        for c in n:
            out.append(c)
            idx.append(i)
    return "".join(out), idx

def replace_fancy(text: str, old: str, new: str) -> str:
    old_n, _ = norm_map(str(old).strip())
    if not old_n or not text:
        return text
    norm, idx = norm_map(text)
    spans, last_end = [], -1
    for m in re.finditer(re.escape(old_n), norm):
        s = idx[m.start()]
        e = idx[m.end() - 1] + 1
        if s < last_end:
            continue
        spans.append((s, e))
        last_end = e
    for s, e in reversed(spans):
        text = text[:s] + str(new) + text[e:]
    return text

TAG_RE = re.compile(r"(<[^>]+>)")

def map_text_parts(html: str, fn):
    parts = TAG_RE.split(html)
    return "".join(p if i % 2 else fn(p) for i, p in enumerate(parts))

def clean_ads(html: str) -> str:
    html = re.sub(r'<a\s+href="[^"]*">.*?</a>', "", html, flags=re.S | re.I)
    html = re.sub(r"(https?://[^\s<]+|(?:www\.)?t\.me/[^\s<]+|telegram\.me/[^\s<]+)", "", html, flags=re.I)
    html = re.sub(r"(?i)join\s*(?:us)?\s*[:\-]?\s*@\w+", "", html)
    html = re.sub(r"@\w{4,}", "", html)
    return html

async def build_caption(uid: int, html: str) -> str:
    s = SETTINGS.get(uid)
    html = (html or "").replace("\xa0", " ").replace("\u200b", "")
    if s["clean_ads"]:
        html = clean_ads(html)

    repl = {}
    try:
        repl.update(await db.get_replace_words(uid) or {})
    except Exception:
        pass
    repl.update(s["replace"])

    dels = []
    try:
        dels.extend(await db.get_delete_words(uid) or [])
    except Exception:
        pass
    dels.extend(s["delete"])

    def fn(t):
        for o, n in repl.items():
            t = replace_fancy(t, o, n)
        for d in dels:
            t = replace_fancy(t, d, "")
        return t

    html = map_text_parts(html, fn)
    parts = [p for p in (s["prefix"], html.strip(), s["suffix"]) if p]
    return "\n\n".join(parts).strip()

def fit_caption(c: str) -> str:
    plain = re.sub(r"<[^>]+>", "", c)
    return c if len(plain) <= 1024 else plain[:1024]

def humanbytes(size):
    if not size: return "0 B"
    power, n = 1024, 0
    units = {0: "", 1: "K", 2: "M", 3: "G", 4: "T"}
    size = float(size)
    while size >= power and n < 4:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}B"

def time_formatter(seconds: float) -> str:
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    out = (f"{d}d " if d else "") + (f"{h}h " if h else "") + (f"{m}m " if m else "") + (f"{s}s" if s or not (d or h or m) else "")
    return out.strip()

def make_progress(uid: int, tg_client: Client, status_msg: Message, label: str):
    state = {"start": time.time(), "last": 0.0}

    async def cb(current, total):
        if uid in CANCEL:
            tg_client.stop_transmission()
        now = time.time()
        if now - state["last"] < 4 and current != total:
            return
        state["last"] = now
        if not total:
            return
        elapsed = max(now - state["start"], 0.001)
        speed = current / elapsed
        eta = (total - current) / speed if speed > 0 else 0
        pct = current * 100 / total
        filled = int(pct // 10)
        bar = "▰" * filled + "▱" * (10 - filled)
        text = (
            f"<b>{label}</b>\n\n[{bar}] {pct:.1f}%\n"
            f"<b>Size:</b> {humanbytes(current)} / {humanbytes(total)}\n"
            f"<b>Speed:</b> {humanbytes(speed)}/s\n"
            f"<b>ETA:</b> {time_formatter(eta)}"
        )
        try:
            await status_msg.edit_text(text, parse_mode=HTML)
        except Exception:
            pass

    return cb

async def retry_flood(fn, *a, **k):
    for _ in range(3):
        try:
            return await fn(*a, **k)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
    return await fn(*a, **k)

def get_message_type(msg):
    for attr, name in (
        ("animation", "Animation"), ("sticker", "Sticker"), ("video_note", "VideoNote"),
        ("voice", "Voice"), ("audio", "Audio"), ("video", "Video"),
        ("photo", "Photo"), ("document", "Document"),
    ):
        if getattr(msg, attr, None):
            return name
    if getattr(msg, "text", None):
        return "Text"
    return None

def media_name(msg) -> str:
    for a in ("video", "document", "audio", "animation"):
        m = getattr(msg, a, None)
        if m and getattr(m, "file_name", None):
            return m.file_name
    return ""

def detect_topic(uid: int, msg: Message, source_topic):
    s = SETTINGS.get(uid)
    if source_topic and source_topic in s["topic_map"]:
        return s["topic_map"][source_topic]
    if s["keywords"]:
        blob = f"{msg.caption or msg.text or ''} {media_name(msg)}"
        hay = norm_map(blob)[0]
        hay = re.sub(r"[_.\-]+", " ", hay)
        for kw in sorted(s["keywords"], key=len, reverse=True):
            if re.search(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", hay):
                return s["keywords"][kw]
    return s["default_topic"]

# ───────────────────────── Login & Logout System ─────────────────────────
@app.on_message(filters.command(["login"]) & filters.private)
async def login_cmd(client: Client, message: Message):
    uid = message.from_user.id
    if await db.get_session(uid):
        return await message.reply_text("✅ आप पहले से लॉगिन हैं! अगर नया अकाउंट जोड़ना है तो पहले <code>/logout</code> करें।", parse_mode=HTML)
    
    LOGIN_STEPS[uid] = {"step": "phone"}
    await message.reply_text(
        "📱 <b>कृपया अपना फ़ोन नंबर कंट्री कोड के साथ भेजें:</b>\n<i>उदाहरण: +919876543210</i>",
        parse_mode=HTML
    )

@app.on_message(filters.command(["logout"]) & filters.private)
async def logout_cmd(client: Client, message: Message):
    uid = message.from_user.id
    await db.set_session(uid, None)
    LOGIN_STEPS.pop(uid, None)
    await message.reply_text("🚪 <b>आप सफलतापूर्वक लॉगआउट हो गए हैं।</b>", parse_mode=HTML)

# ───────────────────────── General Commands ─────────────────────────
TOPIC_HELP = """<b>📚 सम्पूर्ण कमांड गाइड</b>

<b>🔐 लॉगिन सिस्टम:</b>
• <code>/login</code> - अपना टेलीग्राम अकाउंट लॉगिन करें (हमेशा सेव रहेगा)
• <code>/logout</code> - अकाउंट लॉगआउट करें

<b>🎯 टारगेट / टॉपिक:</b>
• <code>/setchat -100xxxxxxxxxx</code> - टारगेट ग्रुप सेट करें
• <code>/clearchat</code> - फॉरवर्डिंग बंद करें
• <code>/settopic &lt;topic_id&gt;</code> - डिफ़ॉल्ट टॉपिक
• <code>/set_topics</code> - विषय: लिंक सेट करें
• <code>/show_topics</code> - सेटिंग्स देखें
• <code>/reset_topics</code> - सब साफ़ करें

<b>⚙️️ कैप्शन:</b>
• <code>/replace 'पुराना' 'नया'</code> - शब्द बदलें
• <code>/delword शब्द</code> - शब्द हटाएं
• <code>/clean_ads on|off</code> - ऐड्स हटाएं
• <code>/cancel</code> - टास्क रोकें
"""

@app.on_message(filters.command(["start", "help", "topichelp"]) & filters.private)
async def help_cmd(client: Client, message: Message):
    await message.reply_text(TOPIC_HELP, parse_mode=HTML)

@app.on_message(filters.command(["setchat"]) & filters.private)
async def set_chat_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("<code>/setchat -100xxxxxxxxxx</code>", parse_mode=HTML)
    try:
        chat_id = int(args[1])
        chat = await client.get_chat(chat_id)
        await db.set_dump_chat(message.from_user.id, chat_id)
        await message.reply_text(f"✅ टारगेट ग्रुप: <code>{chat_id}</code> ({chat.title})", parse_mode=HTML)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@app.on_message(filters.command(["clearchat"]) & filters.private)
async def clear_chat_cmd(client: Client, message: Message):
    await db.set_dump_chat(message.from_user.id, None)
    await message.reply_text("✅ फॉरवर्डिंग बंद। अब फाइलें इसी चैट में आएंगी।")

@app.on_message(filters.command(["settopic"]) & filters.private)
async def set_topic_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        return await message.reply_text("<code>/settopic 12</code>", parse_mode=HTML)
    SETTINGS.get(message.from_user.id)["default_topic"] = int(args[1])
    SETTINGS.save()
    await message.reply_text(f"✅ डिफ़ॉल्ट टॉपिक: <code>{args[1]}</code>", parse_mode=HTML)

@app.on_message(filters.command(["set_topics"]) & filters.private)
async def set_topics_cmd(client: Client, message: Message):
    text = re.sub(r"^/set_topics(@\w+)?", "", message.text).strip()
    if not text:
        return await message.reply_text(
            "<b>फॉर्मेट:</b>\n<code>/set_topics\nMaths: https://t.me/c/123/7\nReasoning: https://t.me/c/123/8</code>",
            parse_mode=HTML,
        )
    mapping = {}
    for line in text.splitlines():
        if ":" not in line: continue
        name, link = line.split(":", 1)
        name = norm_map(name.strip())[0]
        m = re.search(r"(\d+)\s*/?\s*$", link.strip())
        if name and m:
            mapping[name] = int(m.group(1))
    if not mapping:
        return await message.reply_text("❌ कोई सही लाइन नहीं मिली।")
    SETTINGS.get(message.from_user.id)["keywords"] = mapping
    SETTINGS.save()
    out = "<b>✅ सभी विषय सेट हो गए:</b>\n\n" + "\n".join(
        f"• <b>{n.title()}</b> ➔ <code>{t}</code>" for n, t in mapping.items()
    )
    await message.reply_text(out, parse_mode=HTML)

@app.on_message(filters.command(["show_topics"]) & filters.private)
async def show_topics_cmd(client: Client, message: Message):
    s = SETTINGS.get(message.from_user.id)
    out = "<b>📋 टॉपिक सेटिंग्स</b>\n\n"
    out += f"<b>डिफ़ॉल्ट:</b> <code>{s['default_topic']}</code>\n\n<b>विषय:</b>\n"
    out += "\n".join(f"• {k.title()} ➔ <code>{v}</code>" for k, v in s["keywords"].items()) or "—"
    out += f"\n\n<b>Clean Ads:</b> {'ON' if s['clean_ads'] else 'OFF'}"
    await message.reply_text(out, parse_mode=HTML)

@app.on_message(filters.command(["reset_topics"]) & filters.private)
async def reset_topics_cmd(client: Client, message: Message):
    s = SETTINGS.get(message.from_user.id)
    s["keywords"], s["topic_map"], s["default_topic"] = {}, {}, None
    SETTINGS.save()
    await message.reply_text("✅ सभी टॉपिक सेटिंग्स साफ़ हो गईं।")

@app.on_message(filters.command(["replace"]) & filters.private)
async def replace_cmd(client: Client, message: Message):
    args = re.sub(r"^/replace(@\w+)?", "", message.text).strip()
    found = re.findall(r"""['"“”‘’](.*?)['"“”‘’]""", args)
    if len(found) < 2 or not found[0].strip():
        return await message.reply_text("<code>/replace 'पुराना' 'नया'</code>", parse_mode=HTML)
    SETTINGS.get(message.from_user.id)["replace"][found[0]] = found[1]
    SETTINGS.save()
    await message.reply_text(f"✅ <code>{found[0]}</code> ➔ <code>{found[1]}</code>", parse_mode=HTML)

@app.on_message(filters.command(["clean_ads"]) & filters.private)
async def clean_ads_cmd(client: Client, message: Message):
    args = message.text.split()
    s = SETTINGS.get(message.from_user.id)
    if len(args) > 1 and args[1].lower() in ("on", "off"):
        s["clean_ads"] = args[1].lower() == "on"
    else:
        s["clean_ads"] = not s["clean_ads"]
    SETTINGS.save()
    await message.reply_text(f"🧹 Clean Ads: <b>{'ON' if s['clean_ads'] else 'OFF'}</b>", parse_mode=HTML)

@app.on_message(filters.command(["cancel"]) & filters.private)
async def cancel_cmd(client: Client, message: Message):
    uid = message.from_user.id
    if uid in RUNNING:
        CANCEL.add(uid)
        await message.reply_text("🛑 <b>टास्क रोका जा रहा है...</b>", parse_mode=HTML)
    else:
        await message.reply_text("ℹ️ कोई टास्क चालू नहीं है।")

# ───────────────────────── Download + Upload Handler ─────────────────────────
async def download_and_upload(client, sender, msg, msg_type, dest, topic, caption, uid, status, tag) -> bool:
    temp_dir = f"downloads/{uid}_{msg.id}_{int(time.time())}"
    os.makedirs(temp_dir, exist_ok=True)
    try:
        file = await sender.download_media(
            msg, file_name=f"{temp_dir}/",
            progress=make_progress(uid, sender, status, f"📥 डाउनलोड {tag}"),
        )
        if not file or uid in CANCEL:
            return False

        thumb = None
        try:
            if msg_type == "Video" and msg.video.thumbs:
                thumb = await sender.download_media(msg.video.thumbs[0].file_id, file_name=f"{temp_dir}/thumb.jpg")
            elif msg_type == "Document" and msg.document.thumbs:
                thumb = await sender.download_media(msg.document.thumbs[0].file_id, file_name=f"{temp_dir}/thumb.jpg")
        except Exception:
            thumb = None

        kw = {"chat_id": dest}
        if topic: kw["message_thread_id"] = topic
        cap = {"caption": fit_caption(caption), "parse_mode": HTML}
        up = make_progress(uid, client, status, f"📤 अपलोड {tag}")

        if msg_type == "Video":
            r = await client.send_video(video=file, duration=msg.video.duration or 0, width=msg.video.width or 0,
                                        height=msg.video.height or 0, thumb=thumb, supports_streaming=True,
                                        progress=up, **kw, **cap)
        elif msg_type == "Document":
            r = await client.send_document(document=file, thumb=thumb, progress=up, **kw, **cap)
        elif msg_type == "Audio":
            r = await client.send_audio(audio=file, duration=msg.audio.duration or 0, performer=msg.audio.performer,
                                        title=msg.audio.title, thumb=thumb, progress=up, **kw, **cap)
        elif msg_type == "Voice":
            r = await client.send_voice(voice=file, duration=msg.voice.duration or 0, progress=up, **kw, **cap)
        elif msg_type == "Photo":
            r = await client.send_photo(photo=file, **kw, **cap)
        else:
            return False
        return bool(r)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

LINK_RE = re.compile(
    r"t\.me/(?:(c)/(\d+)|(b)/([A-Za-z0-9_]+)|([A-Za-z0-9_]{4,}))/(?:(\d+)/)?(\d+)(?:-(\d+))?"
)

# ───────────────────────── Main Text & Link Router ─────────────────────────
@app.on_message(filters.private & filters.text & ~filters.regex(r"^/"))
async def message_router(client: Client, message: Message):
    uid = message.from_user.id

    # 1. Login State Handling
    if uid in LOGIN_STEPS:
        step_data = LOGIN_STEPS[uid]
        step = step_data.get("step")

        if step == "phone":
            phone = message.text.strip().replace(" ", "")
            login_client = Client(f"login_{uid}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await login_client.connect()
            try:
                code_hash = await login_client.send_code(phone)
                LOGIN_STEPS[uid] = {
                    "step": "otp",
                    "client": login_client,
                    "phone": phone,
                    "phone_code_hash": code_hash.phone_code_hash
                }
                return await message.reply_text("📩 <b>ओटीपी (OTP) दर्ज करें:</b>\n<i>ओटीपी के बीच में स्पेस लगाकर भेजें (जैसे: 1 2 3 4 5)</i>", parse_mode=HTML)
            except Exception as e:
                await login_client.disconnect()
                LOGIN_STEPS.pop(uid, None)
                return await message.reply_text(f"❌ नंबर भेजने में त्रुटि: {e}")

        elif step == "otp":
            otp = message.text.strip().replace(" ", "")
            login_client = step_data["client"]
            try:
                await login_client.sign_in(step_data["phone"], step_data["phone_code_hash"], otp)
                sess = await login_client.export_session_string()
                await db.set_session(uid, sess)
                await login_client.disconnect()
                LOGIN_STEPS.pop(uid, None)
                return await message.reply_text("🎉 <b>सफलतापूर्वक लॉगिन हो गए!</b>\nअब आप प्राइवेट चैनल के लिंक भेजकर जितने चाहे वीडियो निकाल सकते हैं। यह तब तक लॉगिन रहेगा जब तक आप <code>/logout</code> नहीं करते।", parse_mode=HTML)
            except SessionPasswordNeeded:
                LOGIN_STEPS[uid]["step"] = "2fa"
                return await message.reply_text("🔐 <b>आपके अकाउंट पर 2-Step Verification लगा है। कृपया अपना पासवर्ड भेजें:</b>", parse_mode=HTML)
            except (PhoneCodeInvalid, PhoneCodeExpired) as e:
                return await message.reply_text("❌ गलत या एक्सपायर्ड OTP! दोबारा सही OTP भेजें:")
            except Exception as e:
                await login_client.disconnect()
                LOGIN_STEPS.pop(uid, None)
                return await message.reply_text(f"❌ लॉगिन फेल: {e}")

        elif step == "2fa":
            password = message.text.strip()
            login_client = step_data["client"]
            try:
                await login_client.check_password(password)
                sess = await login_client.export_session_string()
                await db.set_session(uid, sess)
                await login_client.disconnect()
                LOGIN_STEPS.pop(uid, None)
                return await message.reply_text("🎉 <b>2FA सफलतापूर्वक वेरीफाई हुआ और आप लॉगिन हो गए!</b>\nअब प्राइवेट वीडियो लिंक भेजना शुरू करें।", parse_mode=HTML)
            except PasswordHashInvalid:
                return await message.reply_text("❌ गलत 2FA पासवर्ड! दोबारा सही पासवर्ड भेजें:")
            except Exception as e:
                await login_client.disconnect()
                LOGIN_STEPS.pop(uid, None)
                return await message.reply_text(f"❌ एरर: {e}")

    # 2. Telegram Link Forwarding Handling
    m = LINK_RE.search(message.text or "")
    if not m:
        return

    if uid in RUNNING:
        return await message.reply_text("⚠️ एक टास्क पहले से चालू है। /cancel भेजें।")

    is_private = bool(m.group(1))
    if is_private:
        chat_target = int("-100" + m.group(2))
    else:
        chat_target = m.group(4) or m.group(5)

    link_topic = int(m.group(6)) if m.group(6) else None
    from_id = int(m.group(7))
    to_id = int(m.group(8)) if m.group(8) else from_id
    if to_id < from_id:
        from_id, to_id = to_id, from_id

    dump_chat = await db.get_dump_chat(uid)
    dest = dump_chat if dump_chat else message.chat.id

    RUNNING.add(uid)
    CANCEL.discard(uid)
    acc = None
    status = None
    done = skipped = failed = 0
    try:
        session = await db.get_session(uid)
        if is_private and not session:
            return await message.reply_text("🔒 <b>यह एक प्राइवेट चैनल है!</b>\nपहले <code>/login</code> कमांड से अपना अकाउंट लॉगिन करें (सिर्फ एक बार करना होगा)।", parse_mode=HTML)

        if session:
            try:
                acc = Client(f"user_{uid}", session_string=session, api_id=API_ID, api_hash=API_HASH, in_memory=True, no_updates=True)
                await acc.connect()
            except Exception as e:
                acc = None
                if is_private:
                    return await message.reply_text(f"❌ लॉगिन सेशन एक्सपायर हो गया है: {e}\nकृपया <code>/logout</code> करके दोबारा <code>/login</code> करें।", parse_mode=HTML)

        sender = acc if acc else client
        status = await message.reply_text("⚡ <b>टास्क शुरू हो रहा है...</b>", parse_mode=HTML)
        total = to_id - from_id + 1

        for n, msgid in enumerate(range(from_id, to_id + 1), 1):
            if uid in CANCEL: break
            tag = f"{n}/{total}"
            try:
                msg = await retry_flood(sender.get_messages, chat_target, msgid)
                if not msg or msg.empty:
                    skipped += 1
                    continue
                msg_type = get_message_type(msg)
                if not msg_type:
                    skipped += 1
                    continue

                src_topic = getattr(msg, "message_thread_id", None) or link_topic
                topic = detect_topic(uid, msg, src_topic) if dest != message.chat.id else None
                topic_kw = {"message_thread_id": topic} if topic else {}

                if msg_type == "Text":
                    text = await build_caption(uid, msg.text.html)
                    if not text:
                        skipped += 1
                        continue
                    await retry_flood(client.send_message, chat_id=dest, text=text, parse_mode=HTML, **topic_kw)
                    done += 1
                    continue

                caption = await build_caption(uid, msg.caption.html if msg.caption else "")
                protected = getattr(msg, "has_protected_content", False)
                sent = False
                if not protected:
                    try:
                        await retry_flood(sender.copy_message, chat_id=dest, from_chat_id=chat_target,
                                          message_id=msgid, caption=fit_caption(caption),
                                          parse_mode=HTML, **topic_kw)
                        sent = True
                    except Exception:
                        pass
                if not sent:
                    sent = await download_and_upload(client, sender, msg, msg_type, dest, topic, caption, uid, status, tag)

                if sent: done += 1
                elif uid not in CANCEL: failed += 1
                await asyncio.sleep(0.5)

            except Exception as err:
                failed += 1
                logger.error(f"Error on msg {msgid}: {err}")
                await asyncio.sleep(1)

        cancelled = uid in CANCEL
        summary = (f"{'🛑 <b>टास्क रोक दिया गया</b>' if cancelled else '✅ <b>सभी फाइलें प्रोसेस हो गईं!</b>'}\n\n"
                   f"✔️ भेजे: {done}  |  ⏭ स्किप: {skipped}  |  ❌ फेल: {failed}")
        try:
            await status.edit_text(summary, parse_mode=HTML)
        except Exception:
            await message.reply_text(summary, parse_mode=HTML)
    finally:
        if acc:
            try: await acc.disconnect()
            except Exception: pass
        RUNNING.discard(uid)
        CANCEL.discard(uid)

if __name__ == "__main__":
    print("🚀 Bot Started Successfully with Persistent Login & Topic Router!")
    app.run()
EOF
