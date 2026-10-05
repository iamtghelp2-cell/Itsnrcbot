cat << 'EOF' > Rexbots/start.py
# Developed by: LastPerson07 × RexBots
# Fixed for Direct String Fallback & Peer ID Resolution
import os
import re
import html as htmllib
import shlex
import asyncio
import random
import shutil
import unicodedata
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import API_ID, API_HASH
try:
    from config import STRING_SESSION
except ImportError:
    STRING_SESSION = None

from database.db import db
from logger import LOGGER

logger = LOGGER(__name__)

SUBSCRIPTION = os.environ.get('SUBSCRIPTION', 'https://graph.org/file/242b7f1b52743938d81f1.jpg')
UPI_ID = os.environ.get("UPI_ID", "your_upi@oksbi")
QR_CODE = os.environ.get("QR_CODE", "https://graph.org/file/242b7f1b52743938d81f1.jpg")

HTML = enums.ParseMode.HTML
REACTIONS = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "⚡", "💯"]

class script(object):
    START_TXT = """<b>👋 Hello {},</b>
<b>🤖 I am <a href=https://t.me/{}>{}</a></b>
<i>Your High-Speed Restricted Content Saver & Topic Router Bot.</i>
<blockquote><b>🚀 System Status: 🟢 Online (Unlimited Mode)</b>
<b>⚡ Performance: Ultra-Fast Server-Side Cloning</b>
<b>🎯 Auto Topic Routing: Fully Enabled</b>
<b>📊 Quota: No Limits (Unlimited Access)</b></blockquote>
<b>👇 नीचे दिए गए मेन्यू से अपनी सेटिंग्स मैनेज करें:</b>
"""
    HELP_TXT = """<b>📚 सम्पूर्ण कमांड और उपयोग गाइड:</b>
• /cancel - चल रहे टास्क को रोकें
• /settings - सेटिंग्स मेन्यू खोलें
"""
    CAPTION = """<b><a href="itsnrcbot"></a></b>\n\n<b>⚜️ Powered By : <a href="itsnrcbot">itsnrcbot 😎</a></b>"""

class batch_temp(object):
    IS_BATCH = {}
    USER_CLEAN_ADS = {}
    USER_PREFIX = {}
    USER_SUFFIX = {}
    USER_TOPIC_MAP = {}
    USER_KEYWORD_MAP = {}
    USER_DEFAULT_TOPIC = {}
    LOADED = set()

_SMALLCAPS = {
    'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ꜰ': 'f', 'ɢ': 'g', 'ʜ': 'h', 'ɪ': 'i',
    'ᴊ': 'j', 'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o', 'ᴘ': 'p', 'ǫ': 'q', 'ʀ': 'r',
    'ꜱ': 's', 'ᴛ': 't', 'ᴜ': 'u', 'ᴠ': 'v', 'ᴡ': 'w', 'ʏ': 'y', 'ᴢ': 'z',
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x', 'у': 'y', 'і': 'i', 'ѕ': 's', 'ј': 'j',
    'А': 'a', 'В': 'b', 'Е': 'e', 'К': 'k', 'М': 'm', 'Н': 'h', 'О': 'o', 'Р': 'p', 'С': 'c', 'Т': 't', 'Х': 'x',
}
_ZERO = {"\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad", "\u180e"}
_FOLD_CACHE = {}

def _fold_char(ch: str) -> str:
    r = _FOLD_CACHE.get(ch)
    if r is not None:
        return r
    cp = ord(ch)
    if ch in _SMALLCAPS:
        r = _SMALLCAPS[ch]
    elif 0x1F150 <= cp <= 0x1F169:
        r = chr(97 + cp - 0x1F150)
    elif 0x1F170 <= cp <= 0x1F189:
        r = chr(97 + cp - 0x1F170)
    elif 0x1F1E6 <= cp <= 0x1F1FF:
        r = chr(97 + cp - 0x1F1E6)
    elif (0x0300 <= cp <= 0x036F) or (0x20D0 <= cp <= 0x20FF) or (0xFE00 <= cp <= 0xFE0F) or ch in _ZERO:
        r = ""
    else:
        r = unicodedata.normalize("NFKC", ch).casefold()
        r = "".join(c for c in r if not (0x0300 <= ord(c) <= 0x036F))
    if len(_FOLD_CACHE) < 50000:
        _FOLD_CACHE[ch] = r
    return r

def fold_with_map(text: str):
    out, idx = [], []
    for i, ch in enumerate(text):
        for c in _fold_char(ch):
            out.append(c)
            idx.append(i)
    return "".join(out), idx

def fold(text: str) -> str:
    return fold_with_map(text)[0]

def smart_replace(text: str, rules) -> str:
    if not text or not rules:
        return text
    for old, new in rules:
        key = fold(old)
        if not key:
            continue
        folded, idx = fold_with_map(text)
        if key not in folded:
            continue
        n = len(text)
        res, pos, start = [], 0, 0
        while True:
            s = folded.find(key, start)
            if s == -1:
                break
            e = s + len(key)
            o_s = idx[s]
            o_e = idx[e - 1] + 1
            while o_e < n and _fold_char(text[o_e]) == "":
                o_e += 1
            start = e
            if o_s < pos:
                continue
            res.append(text[pos:o_s])
            res.append(new)
            pos = o_e
        res.append(text[pos:])
        text = "".join(res)
    return text

_TAG_SPLIT = re.compile(r'(<[^>]+>)')

def map_html_text(h: str, fn) -> str:
    parts = _TAG_SPLIT.split(h)
    for i in range(0, len(parts), 2):
        if parts[i]:
            parts[i] = htmllib.escape(fn(htmllib.unescape(parts[i])), quote=False)
    return "".join(parts)

def plain_len(h: str) -> int:
    return len(htmllib.unescape(re.sub(r'<[^>]+>', '', h)))

def clean_ads_html(h: str) -> str:
    def anchor(m):
        href = m.group(1).lower()
        return "" if ("t.me" in href or "telegram.me" in href or "telegram.dog" in href) else m.group(2)
    h = re.sub(r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>', anchor, h, flags=re.S | re.I)

    def txt(t):
        t = re.sub(r'(?i)\b(join|follow|subscribe)\b\s*[:\-–➤>»]*\s*(?=@|https?://|t\.me|telegram\.me)', '', t)
        t = re.sub(r'(https?://\S+|(?:www\.)?t\.me/\S+|telegram\.(?:me|dog)/\S+)', '', t)
        t = re.sub(r'@[A-Za-z][A-Za-z0-9_]{3,}', '', t)
        return re.sub(r'[ \t]+\n', '\n', t)
    return map_html_text(h, txt)

def process_html(uid: int, h: str, rules, base_link: str = None) -> str:
    if not h:
        return ""
    if batch_temp.USER_CLEAN_ADS.get(uid):
        h = clean_ads_html(h)
    if rules:
        h = map_html_text(h, lambda t: smart_replace(t, rules))
    prefix = batch_temp.USER_PREFIX.get(uid, "")
    suffix = batch_temp.USER_SUFFIX.get(uid, "")
    if prefix:
        h = f"{prefix}\n\n{h}"
    if suffix:
        h = f"{h}\n\n{suffix}"
    return h.strip()

async def build_rules(uid: int):
    rules = []
    try:
        repl = await db.get_replace_words(uid) or {}
        rules.extend(list(repl.items()))
        dels = await db.get_delete_words(uid) or []
        rules.extend((w, "") for w in dels)
    except Exception as e:
        logger.error(f"rules load error: {e}")
    rules.sort(key=lambda r: len(fold(r[0])), reverse=True)
    return rules

async def load_cfg(uid: int):
    if uid in batch_temp.LOADED:
        return
    batch_temp.LOADED.add(uid)

async def with_flood(fn, *a, **kw):
    for _ in range(3):
        try:
            return await fn(*a, **kw)
        except FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
    return await fn(*a, **kw)

def get_message_type(msg):
    if getattr(msg, 'document', None): return "Document"
    if getattr(msg, 'video', None): return "Video"
    if getattr(msg, 'photo', None): return "Photo"
    if getattr(msg, 'audio', None): return "Audio"
    if getattr(msg, 'voice', None): return "Voice"
    if getattr(msg, 'animation', None): return "Animation"
    if getattr(msg, 'video_note', None): return "VideoNote"
    if getattr(msg, 'sticker', None): return "Sticker"
    if getattr(msg, 'text', None): return "Text"
    return None

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    bot = await client.get_me()
    await client.send_message(
        chat_id=message.chat.id,
        text=script.START_TXT.format(message.from_user.mention, bot.username, bot.first_name),
        parse_mode=HTML
    )

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await message.reply_text("🛑 <b>टास्क तुरंत रोक दिया गया।</b>", parse_mode=HTML)

LINK_RE = re.compile(r'https?://t\.me/(?:(c)/)?([A-Za-z0-9_]+)/(?:\d+/)?(\d+)(?:-(\d+))?')

async def send_downloaded(client, mtype, file, msg, caption, common):
    cap_kw = {"caption": caption, "parse_mode": HTML} if caption else {}
    if mtype == "Video":
        v = msg.video
        await client.send_video(video=file, duration=getattr(v, 'duration', 0) or 0,
                                width=getattr(v, 'width', 0) or 0, height=getattr(v, 'height', 0) or 0,
                                supports_streaming=True, **cap_kw, **common)
    elif mtype == "Document":
        await client.send_document(document=file, **cap_kw, **common)
    elif mtype == "Photo":
        await client.send_photo(photo=file, **cap_kw, **common)
    elif mtype == "Audio":
        await client.send_audio(audio=file, **cap_kw, **common)
    elif mtype == "Voice":
        await client.send_voice(voice=file, **cap_kw, **common)
    elif mtype == "Animation":
        await client.send_animation(animation=file, **cap_kw, **common)
    elif mtype == "VideoNote":
        await client.send_video_note(video_note=file, **common)
    elif mtype == "Sticker":
        await client.send_sticker(sticker=file, **common)

async def forward_one(client, acc, sender_app, msg, chat_target, destination_chat, uid, in_group, rules):
    mtype = get_message_type(msg)
    if not mtype:
        return False

    common = {}
    if mtype == "Text":
        h = process_html(uid, msg.text.html, rules)
        if not h:
            return False
        await with_flood(client.send_message, destination_chat, h, parse_mode=HTML, **common)
        return True

    orig_caption = msg.caption.html if msg.caption else ""
    caption = process_html(uid, orig_caption, rules)
    overflow = None
    if caption and plain_len(caption) > 1024:
        overflow, caption = caption, ""

    kw = {"chat_id": destination_chat, "from_chat_id": chat_target, "message_id": msg.id, **common}
    if msg.caption is not None:
        kw["caption"] = caption
        kw["parse_mode"] = HTML

    copied = False
    if acc:
        try:
            await with_flood(acc.copy_message, **kw)
            copied = True
        except Exception:
            pass
    if not copied:
        try:
            await with_flood(client.copy_message, **kw)
            copied = True
        except Exception:
            pass

    if not copied:
        temp_dir = f"downloads/{uid}_{msg.id}"
        os.makedirs(temp_dir, exist_ok=True)
        try:
            file = await sender_app.download_media(msg, file_name=f"{temp_dir}/")
            if not file:
                return False
            await with_flood(send_downloaded, client, mtype, file, msg, caption, {"chat_id": destination_chat, **common})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    if overflow:
        await with_flood(client.send_message, destination_chat, overflow, parse_mode=HTML, **common)
    return True

@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "t.me/" not in message.text:
        return
    uid = message.from_user.id

    m = LINK_RE.search(message.text)
    if not m:
        return await message.reply_text("❌ <b>अमान्य लिंक फ़ॉर्मेट।</b>", parse_mode=HTML)

    if batch_temp.IS_BATCH.get(uid) is False:
        return await message.reply_text("⚠️ <b>एक टास्क पहले से चालू है। /cancel भेजें।</b>", parse_mode=HTML)

    await load_cfg(uid)
    is_private_link = bool(m.group(1))
    chat_target = int("-100" + m.group(2)) if is_private_link else m.group(2)
    fromID = int(m.group(3))
    toID = int(m.group(4)) if m.group(4) else fromID
    if toID < fromID:
        fromID, toID = toID, fromID

    dump_chat = await db.get_dump_chat(uid)
    destination_chat = dump_chat if dump_chat else message.chat.id
    in_group = destination_chat != message.chat.id

    batch_temp.IS_BATCH[uid] = False
    acc = None
    sent = failed = 0
    try:
        if is_private_link:
            # First preference: config.py STRING_SESSION (always guaranteed to work)
            user_session = STRING_SESSION or await db.get_session(uid)
            if not user_session:
                return await message.reply("🔒 <b>प्राइवेट लिंक के लिए सेशन नहीं मिला। /login करें।</b>", parse_mode=HTML)
            try:
                acc = Client(f"acc_{uid}", session_string=user_session, api_hash=API_HASH, api_id=API_ID, in_memory=True)
                await acc.connect()
                # Resolve dialogs to prevent Peer id invalid
                try:
                    async for _ in acc.get_dialogs(limit=50):
                        pass
                except Exception:
                    pass
            except Exception as e:
                acc = None
                return await message.reply(f"❌ अकाउंट कनेक्शन एरर: {e}")

        sender_app = acc if is_private_link else client
        rules = await build_rules(uid)

        for start in range(fromID, toID + 1, 100):
            if batch_temp.IS_BATCH.get(uid):
                break
            ids = list(range(start, min(start + 100, toID + 1)))
            try:
                msgs = await with_flood(sender_app.get_messages, chat_target, ids)
            except Exception as e:
                logger.error(f"fetch error {ids[0]}-{ids[-1]}: {e}")
                failed += len(ids)
                continue
            if not isinstance(msgs, list):
                msgs = [msgs]

            for msg in msgs:
                if batch_temp.IS_BATCH.get(uid):
                    break
                if not msg or msg.empty:
                    continue
                try:
                    ok = await forward_one(client, acc, sender_app, msg, chat_target, destination_chat,
                                           uid, in_group, rules)
                    if ok:
                        sent += 1
                    await asyncio.sleep(0.5)
                except Exception as err:
                    failed += 1
                    logger.error(f"Error on msg {getattr(msg, 'id', '?')}: {err}")
                    await asyncio.sleep(1)

        await message.reply_text(f"✅ <b>काम पूरा:</b> {sent} भेजे गए" + (f", {failed} फेल" if failed else ""), parse_mode=HTML)
    finally:
        if acc:
            try:
                await acc.disconnect()
            except Exception:
                pass
        batch_temp.IS_BATCH[uid] = True
EOF
