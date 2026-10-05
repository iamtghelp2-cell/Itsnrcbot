# Developed by: LastPerson07 × RexBots
# Optimized for: Unlimited Fast Multi-Topic Forwarding & Keyword Smart Router
# FIXED: font-proof replace (any Unicode style), safe link rewrite, HTML-preserving captions,
#        batch fetch, persistent settings, callback handler conflict, many small bugs.
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

<blockquote><b>🎯 1. टॉपिक और ग्रुप फॉरवर्डिंग (Smart Routing):</b></blockquote>
• <code>/setchat -100xxxxxxxxxx</code> - अपना टारगेट सुपरग्रुप सेट करें
• <code>/clearchat</code> - फॉरवर्डिंग बंद करें (फाइलें बॉट DM में आएँगी)
• <code>/settopic &lt;topic_id&gt;</code> - डिफ़ॉल्ट टॉपिक ID सेट करें
• <code>/set_topics</code> - एक बार में सभी विषयों के लिंक सेट करें (नीचे उदाहरण देखें)
• <code>/map_topic &lt;सामने_का_id&gt; &lt;आपका_id&gt;</code> - सीधे टॉपिक ID मैपिंग
• <code>/show_topics</code> - एक्टिव टॉपिक लिस्ट देखें
• <code>/reset_topics</code> - सभी टॉपिक मैपिंग साफ़ करें

<blockquote><b>📝 /set_topics का सही फॉर्मेट:</b></blockquote>
<code>/set_topics
Maths, गणित: https://t.me/c/3635348530/7
Reasoning: https://t.me/c/3635348530/8
Polity: https://t.me/c/3635348530/11
Current Affairs: https://t.me/c/3635348530/4</code>
<i>(एक टॉपिक के कई नाम कॉमा से अलग करके लिख सकते हैं)</i>

<blockquote><b>⚙️ 2. ऑटो क्लीनर व कैप्शन:</b></blockquote>
• <code>/setting</code> - पूरा इनलाइन सेटिंग्स डैशबोर्ड खोलें
• <code>/clean_ads</code> - अन्य चैनलों के लिंक, @username व प्रोमो ऑटो-डिलीट करें
• <code>/replace 'पुराना' 'नया'</code> - शब्द बदलें (किसी भी फॉन्ट स्टाइल में हो, बदल जाएगा)
• <code>/delword 'शब्द'</code> - शब्द हमेशा हटाएँ
• <code>/show_replace</code> - सेव की हुई रिप्लेसमेंट लिस्ट देखें
• <code>/clear_replace</code> - सभी रिप्लेसमेंट साफ़ करें
• <code>/prefix 'टेक्स्ट'</code> - कैप्शन के ऊपर नाम जोड़ें
• <code>/suffix 'टेक्स्ट'</code> - कैप्शन के नीचे नाम जोड़ें

<blockquote><b>🛑 3. टास्क कंट्रोल:</b></blockquote>
• <code>/cancel</code> - चल रहे बैच टास्क को तुरंत रोकें
"""
    CAPTION = """<b><a href="itsnrcbot"></a></b>\n\n<b>⚜️ Powered By : <a href="itsnrcbot">itsnrcbot 😎</a></b>"""


def humanbytes(size):
    if not size:
        return "0B"
    power = 2 ** 10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power and n < 4:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


class batch_temp(object):
    IS_BATCH = {}             # False = task running, True = idle/cancelled
    USER_CLEAN_ADS = {}
    USER_PREFIX = {}
    USER_SUFFIX = {}
    USER_TOPIC_MAP = {}       # {user_id: {source_topic_id: target_topic_id}}
    USER_KEYWORD_MAP = {}     # {user_id: {subject_keyword: target_topic_id}}
    USER_DEFAULT_TOPIC = {}   # {user_id: default_topic_id}
    LOADED = set()


# =====================================================================
#  FONT-PROOF TEXT FOLDING  (𝗕𝗼𝗹𝗱 / 𝓘𝓽𝓪𝓵𝓲𝓬 / 𝕕𝕠𝕦𝕓𝕝𝕖 / ⓒⓘⓡⓒⓛⓔ / ｆｕｌｌ / ꜱᴍᴀʟʟᴄᴀᴘꜱ / 🅱🅾🆇 ...)
#  सब कुछ मैचिंग के लिए साधारण a-z में बदला जाता है, पर रिप्लेस ओरिजिनल टेक्स्ट पर होता है।
# =====================================================================
_SMALLCAPS = {
    'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ꜰ': 'f', 'ɢ': 'g', 'ʜ': 'h', 'ɪ': 'i',
    'ᴊ': 'j', 'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o', 'ᴘ': 'p', 'ǫ': 'q', 'ʀ': 'r',
    'ꜱ': 's', 'ᴛ': 't', 'ᴜ': 'u', 'ᴠ': 'v', 'ᴡ': 'w', 'ʏ': 'y', 'ᴢ': 'z',
    # Cyrillic look-alikes
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
    elif 0x1F150 <= cp <= 0x1F169:          # negative circled 🅐
        r = chr(97 + cp - 0x1F150)
    elif 0x1F170 <= cp <= 0x1F189:          # negative squared 🅰
        r = chr(97 + cp - 0x1F170)
    elif 0x1F1E6 <= cp <= 0x1F1FF:          # regional indicators 🇦
        r = chr(97 + cp - 0x1F1E6)
    elif (0x0300 <= cp <= 0x036F) or (0x20D0 <= cp <= 0x20FF) or (0xFE00 <= cp <= 0xFE0F) or ch in _ZERO:
        r = ""                               # strike/underline/combining marks, zero-width
    else:
        r = unicodedata.normalize("NFKC", ch).casefold()
        r = "".join(c for c in r if not (0x0300 <= ord(c) <= 0x036F))
    if len(_FOLD_CACHE) < 50000:
        _FOLD_CACHE[ch] = r
    return r


def fold_with_map(text: str):
    """Returns (folded_text, origin_index_list) — folded[i] originally came from text[origin[i]]."""
    out, idx = [], []
    for i, ch in enumerate(text):
        for c in _fold_char(ch):
            out.append(c)
            idx.append(i)
    return "".join(out), idx


def fold(text: str) -> str:
    return fold_with_map(text)[0]


def smart_replace(text: str, rules) -> str:
    """rules = [(old, new), ...]  — old किसी भी फॉन्ट/केस में हो सकता है, मैच हो जाएगा।"""
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
            while o_e < n and _fold_char(text[o_e]) == "":   # पीछे लगे strike/underline मार्क भी हटाओ
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


# ---------------- HTML helpers (formatting बचाकर रिप्लेस) ----------------
_TAG_SPLIT = re.compile(r'(<[^>]+>)')


def map_html_text(h: str, fn) -> str:
    parts = _TAG_SPLIT.split(h)
    for i in range(0, len(parts), 2):          # even index = सिर्फ टेक्स्ट, tags नहीं
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
    if base_link:
        h = rewrite_links(h, base_link)
    prefix = batch_temp.USER_PREFIX.get(uid, "")
    suffix = batch_temp.USER_SUFFIX.get(uid, "")
    if prefix:
        h = f"{prefix}\n\n{h}"
    if suffix:
        h = f"{h}\n\n{suffix}"
    return h.strip()


_TME_LINK = re.compile(r'https?://(?:t|telegram)\.me/(?:c/\d+|joinchat/[\w-]+|\+[\w-]+|\w+)(?:/(\d+))?')


def rewrite_links(h: str, base_link: str) -> str:
    # एक ही pass में — पहले वाले bug (दोबारा रिप्लेस होकर लिंक टूटना) ठीक किया गया
    def repl(m):
        post = m.group(1)
        return f"{base_link}/{post}" if post else base_link
    return _TME_LINK.sub(repl, h)


async def get_base_link(client: Client, destination_chat: int):
    if destination_chat > 0:          # प्राइवेट चैट में लिंक रिराइट का मतलब नहीं
        return None
    try:
        chat = await client.get_chat(destination_chat)
        if chat.username:
            return f"https://t.me/{chat.username}"
        return f"https://t.me/c/{str(destination_chat).replace('-100', '')}"
    except Exception as e:
        logger.error(f"Link rewrite error: {e}")
        return None


async def build_rules(uid: int):
    rules = []
    try:
        repl = await db.get_replace_words(uid) or {}
        rules.extend(list(repl.items()))
        dels = await db.get_delete_words(uid) or []
        rules.extend((w, "") for w in dels)
    except Exception as e:
        logger.error(f"rules load error: {e}")
    rules.sort(key=lambda r: len(fold(r[0])), reverse=True)    # लंबे शब्द पहले
    return rules


# =====================================================================
#  PERSISTENT SETTINGS (रीस्टार्ट पर गायब नहीं होंगी)
# =====================================================================
async def load_cfg(uid: int):
    if uid in batch_temp.LOADED:
        return
    batch_temp.LOADED.add(uid)
    try:
        doc = await db.col.find_one({'id': uid}, {'router_cfg': 1})
        cfg = (doc or {}).get('router_cfg') or {}
        batch_temp.USER_KEYWORD_MAP[uid] = {k: int(v) for k, v in cfg.get('kw', [])}
        batch_temp.USER_TOPIC_MAP[uid] = {int(k): int(v) for k, v in cfg.get('ids', [])}
        if cfg.get('default'):
            batch_temp.USER_DEFAULT_TOPIC[uid] = int(cfg['default'])
        batch_temp.USER_PREFIX[uid] = cfg.get('prefix', '')
        batch_temp.USER_SUFFIX[uid] = cfg.get('suffix', '')
        batch_temp.USER_CLEAN_ADS[uid] = bool(cfg.get('clean_ads', False))
    except Exception as e:
        logger.error(f"cfg load error: {e}")


async def save_cfg(uid: int):
    cfg = {
        'kw': [[k, v] for k, v in batch_temp.USER_KEYWORD_MAP.get(uid, {}).items()],
        'ids': [[k, v] for k, v in batch_temp.USER_TOPIC_MAP.get(uid, {}).items()],
        'default': batch_temp.USER_DEFAULT_TOPIC.get(uid),
        'prefix': batch_temp.USER_PREFIX.get(uid, ''),
        'suffix': batch_temp.USER_SUFFIX.get(uid, ''),
        'clean_ads': batch_temp.USER_CLEAN_ADS.get(uid, False),
    }
    try:
        await db.col.update_one({'id': uid}, {'$set': {'router_cfg': cfg}}, upsert=True)
    except Exception as e:
        logger.error(f"cfg save error: {e}")


# =====================================================================
#  UTILS
# =====================================================================
_QUOTES = str.maketrans({"“": '"', "”": '"', "„": '"', "‘": "'", "’": "'", "‚": "'"})


def arg_text(message: Message) -> str:
    parts = (message.text or "").split(None, 1)
    if len(parts) < 2:
        return ""
    t = parts[1].strip().translate(_QUOTES)
    if len(t) >= 2 and t[0] in "'\"" and t[-1] == t[0]:
        t = t[1:-1]
    return t


def parse_two_args(message: Message):
    parts = (message.text or "").split(None, 1)
    if len(parts) < 2:
        return None
    rest = parts[1].translate(_QUOTES)     # मोबाइल कीबोर्ड के घुमावदार quotes भी चलेंगे
    try:
        args = shlex.split(rest)
    except ValueError:
        args = []
    if len(args) == 2:
        return args
    if "|" in rest:                         # fallback:  /replace पुराना | नया
        a, b = rest.split("|", 1)
        return [a.strip().strip("'\""), b.strip().strip("'\"")]
    return None


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


def _route_norm(s: str) -> str:
    f = fold(s or "")
    return re.sub(r'[\s_\-.,;:|/\\()\[\]{}]+', ' ', f).strip()


def detect_target_topic(user_id: int, msg: Message, source_topic: int = None):
    # 1. सीधे ID मैपिंग (/map_topic)
    if source_topic:
        mapped_id = batch_temp.USER_TOPIC_MAP.get(user_id, {}).get(source_topic)
        if mapped_id:
            return mapped_id

    # 2. कैप्शन / फ़ाइलनेम / टेक्स्ट से कीवर्ड मैचिंग (/set_topics) — हर फॉन्ट में चलेगा
    keyword_map = batch_temp.USER_KEYWORD_MAP.get(user_id, {})
    if keyword_map:
        raw = (msg.caption or msg.text or "")
        for attr in ("video", "document", "audio"):
            obj = getattr(msg, attr, None)
            if obj and getattr(obj, 'file_name', None):
                raw += " " + obj.file_name
        hay = " " + _route_norm(raw) + " "
        for kw, target_id in sorted(keyword_map.items(), key=lambda x: len(x[0]), reverse=True):
            k = _route_norm(kw)
            if not k:
                continue
            if len(k) <= 3:                       # छोटे शब्द (gk, hin) → पूरा शब्द मैच
                if f" {k} " in hay:
                    return target_id
            elif k in hay:
                return target_id

    # 3. डिफ़ॉल्ट टॉपिक
    return batch_temp.USER_DEFAULT_TOPIC.get(user_id, None)


# =====================================================================
#  TOPIC ROUTING COMMANDS
# =====================================================================
@Client.on_message(filters.command(["set_topics"]) & filters.private)
async def set_topics_bulk_cmd(client: Client, message: Message):
    uid = message.from_user.id
    await load_cfg(uid)
    parts = (message.text or "").split(None, 1)
    text = parts[1].strip() if len(parts) > 1 else ""
    if not text:
        return await message.reply_text(
            "<b>📌 Topic Setup Format:</b>\n\n"
            "<code>/set_topics\n"
            "Maths, गणित: https://t.me/c/3635348530/7\n"
            "Reasoning: https://t.me/c/3635348530/8\n"
            "Polity: https://t.me/c/3635348530/11\n"
            "Current Affairs: https://t.me/c/3635348530/4</code>",
            parse_mode=HTML
        )

    mapping = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        names, link = line.split(":", 1)
        link = link.strip()
        m = re.search(r't\.me/c/\d+/(\d+)', link) or re.search(r'/(\d+)/?(?:\?.*)?$', link) or re.fullmatch(r'(\d+)', link)
        if not m:
            continue
        topic_id = int(m.group(1))
        for name in re.split(r'[,|،]', names):
            name = name.strip().lower()
            if name:
                mapping[name] = topic_id

    if not mapping:
        return await message.reply_text("❌ कोई मान्य टॉपिक लिंक नहीं मिला। सही प्रारूप में भेजें।")

    batch_temp.USER_KEYWORD_MAP[uid] = mapping
    await save_cfg(uid)

    out = "<b>✅ सभी विषय और उनके टॉपिक ID सफलतापूर्वक सेट हो गए:</b>\n\n"
    for name, t_id in mapping.items():
        out += f"• <b>{htmllib.escape(name.title())}</b> ➔ Topic ID: <code>{t_id}</code>\n"
    await message.reply_text(out, parse_mode=HTML)


@Client.on_message(filters.command(["map_topic"]) & filters.private)
async def map_topic_cmd(client: Client, message: Message):
    uid = message.from_user.id
    await load_cfg(uid)
    args = message.text.split()
    if len(args) < 3:
        return await message.reply_text(
            "<b>📌 Topic Map Usage:</b>\n"
            "<code>/map_topic &lt;सामने_का_topic_id&gt; &lt;आपका_topic_id&gt;</code>\n\n"
            "<i>उदा:</i> <code>/map_topic 4 15</code>",
            parse_mode=HTML
        )
    try:
        s_id, t_id = int(args[1]), int(args[2])
    except ValueError:
        return await message.reply_text("❌ केवल संख्या डालें।")
    batch_temp.USER_TOPIC_MAP.setdefault(uid, {})[s_id] = t_id
    await save_cfg(uid)
    await message.reply_text(
        f"<b>✅ मैपिंग सेव हो गई:</b>\nस्रोत टॉपिक <code>{s_id}</code> ➔ आपका टॉपिक <code>{t_id}</code>",
        parse_mode=HTML
    )


@Client.on_message(filters.command(["show_topics"]) & filters.private)
async def show_topics_cmd(client: Client, message: Message):
    uid = message.from_user.id
    await load_cfg(uid)
    kw_mapping = batch_temp.USER_KEYWORD_MAP.get(uid, {})
    id_mapping = batch_temp.USER_TOPIC_MAP.get(uid, {})
    default_top = batch_temp.USER_DEFAULT_TOPIC.get(uid, "सेट नहीं")

    out = "<b>📋 आपकी एक्टिव टॉपिक सेटिंग्स:</b>\n\n"
    out += f"<b>डिफ़ॉल्ट टॉपिक:</b> <code>{default_top}</code>\n\n"

    if kw_mapping:
        out += "<b>🔸 ऑटो-कीवर्ड विषय:</b>\n"
        for s, t in kw_mapping.items():
            out += f"• {htmllib.escape(s.title())} ➔ Topic ID: <code>{t}</code>\n"
        out += "\n"
    if id_mapping:
        out += "<b>🔸 डायरेक्ट ID मैपिंग:</b>\n"
        for s, t in id_mapping.items():
            out += f"• स्रोत ID <code>{s}</code> ➔ आपका Topic ID: <code>{t}</code>\n"
    if not kw_mapping and not id_mapping:
        out += "<i>ℹ️ अभी कोई कस्टम टॉपिक सेट नहीं है।</i>"
    await message.reply_text(out, parse_mode=HTML)


@Client.on_message(filters.command(["reset_topics"]) & filters.private)
async def reset_topics_cmd(client: Client, message: Message):
    uid = message.from_user.id
    await load_cfg(uid)
    batch_temp.USER_TOPIC_MAP[uid] = {}
    batch_temp.USER_KEYWORD_MAP[uid] = {}
    batch_temp.USER_DEFAULT_TOPIC.pop(uid, None)
    await save_cfg(uid)
    await message.reply_text("🧹 <b>सभी टॉपिक मैपिंग और कीवर्ड्स साफ़ कर दिए गए हैं।</b>", parse_mode=HTML)


@Client.on_message(filters.command(["settopic"]) & filters.private)
async def set_default_topic(client: Client, message: Message):
    uid = message.from_user.id
    await load_cfg(uid)
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("<code>/settopic &lt;topic_id&gt;</code> या <code>/settopic clear</code>", parse_mode=HTML)
    if args[1].lower() == "clear":
        batch_temp.USER_DEFAULT_TOPIC.pop(uid, None)
        await save_cfg(uid)
        return await message.reply_text("✅ डिफ़ॉल्ट टॉपिक हटा दिया गया।")
    try:
        t_id = int(args[1])
    except ValueError:
        return await message.reply_text("❌ केवल संख्या डालें।")
    batch_temp.USER_DEFAULT_TOPIC[uid] = t_id
    await save_cfg(uid)
    await message.reply_text(f"✅ <b>डिफ़ॉल्ट टॉपिक सेट हुआ:</b> <code>{t_id}</code>", parse_mode=HTML)


# =====================================================================
#  CORE USER SETTINGS & TOOLS
# =====================================================================
async def open_settings_panel_impl(message: Message):
    buttons = [
        [InlineKeyboardButton("Set Chat ID", callback_data="set_chat_help"),
         InlineKeyboardButton("Reset Chat ID", callback_data="clearchat_call")],
        [InlineKeyboardButton("Set Rename Tag", callback_data="rename_tag_help"),
         InlineKeyboardButton("Caption", callback_data="caption_help")],
        [InlineKeyboardButton("Replace Words", callback_data="replace_help"),
         InlineKeyboardButton("Clean Ads", callback_data="toggle_clean_ads_call")],
        [InlineKeyboardButton("Session Login", callback_data="login_help"),
         InlineKeyboardButton("Close Menu ❌", callback_data="close_btn")]
    ]
    cap = "<b>⚙️ Settings & Configuration Dashboard</b>\n\n<i>नीचे दिए गए विकल्पों से अपने बोट को कस्टमाइज़ करें:</i>"
    markup = InlineKeyboardMarkup(buttons)
    try:
        await message.reply_photo(photo="https://i.ibb.co/3kX9tjGXP/settings.jpg", caption=cap,
                                  reply_markup=markup, parse_mode=HTML)
    except Exception:
        await message.reply_text(cap, reply_markup=markup, parse_mode=HTML)   # फोटो फेल हो तो भी पैनल खुले


@Client.on_message(filters.command(["setting", "settings"]) & filters.private)
async def open_settings_panel(client: Client, message: Message):
    await open_settings_panel_impl(message)


@Client.on_message(filters.command(["replace", "r"]) & filters.private)
async def easy_replace_command(client: Client, message: Message):
    args = parse_two_args(message)
    if not args:
        return await message.reply_text(
            "<code>/replace 'Old Word' 'New Word'</code>\n<code>/replace पुराना | नया</code>\n\n"
            "<i>पुराना शब्द किसी भी फॉन्ट/केस में हो, बदल जाएगा। नया शब्द खाली '' दें तो हट जाएगा।</i>",
            parse_mode=HTML)
    old, new = args
    try:
        words = await db.get_replace_words(message.from_user.id) or {}
        words[old] = new
        await db.set_replace_words(message.from_user.id, words)
        await message.reply_text(
            f"✅ <b>Replacement Saved:</b> <code>{htmllib.escape(old)}</code> ➔ <code>{htmllib.escape(new)}</code>",
            parse_mode=HTML)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@Client.on_message(filters.command(["delword"]) & filters.private)
async def delete_word_command(client: Client, message: Message):
    word = arg_text(message)
    if not word:
        return await message.reply_text("<code>/delword 'शब्द'</code>", parse_mode=HTML)
    await db.col.update_one({'id': message.from_user.id}, {'$addToSet': {'delete_words': word}}, upsert=True)
    await message.reply_text(f"✅ <b>अब यह शब्द हमेशा हटेगा:</b> <code>{htmllib.escape(word)}</code>", parse_mode=HTML)


@Client.on_message(filters.command(["show_replace"]) & filters.private)
async def show_replace_command(client: Client, message: Message):
    uid = message.from_user.id
    repl = await db.get_replace_words(uid) or {}
    dels = await db.get_delete_words(uid) or []
    if not repl and not dels:
        return await message.reply_text("ℹ️ कोई रिप्लेसमेंट सेव नहीं है।")
    out = "<b>🔁 आपकी रिप्लेसमेंट लिस्ट:</b>\n\n"
    for o, n in repl.items():
        out += f"• <code>{htmllib.escape(o)}</code> ➔ <code>{htmllib.escape(n)}</code>\n"
    for d in dels:
        out += f"• 🗑 <code>{htmllib.escape(d)}</code>\n"
    await message.reply_text(out, parse_mode=HTML)


@Client.on_message(filters.command(["clear_replace"]) & filters.private)
async def clear_replace_command(client: Client, message: Message):
    await db.col.update_one({'id': message.from_user.id}, {'$set': {'replace_words': {}, 'delete_words': []}})
    await message.reply_text("🧹 <b>सभी रिप्लेसमेंट साफ़ कर दिए गए।</b>", parse_mode=HTML)


@Client.on_message(filters.command(["clean_ads"]) & filters.private)
async def toggle_clean_ads(client: Client, message: Message):
    uid = message.from_user.id
    await load_cfg(uid)
    c = batch_temp.USER_CLEAN_ADS.get(uid, False)
    batch_temp.USER_CLEAN_ADS[uid] = not c
    await save_cfg(uid)
    await message.reply_text(f"<b>Ad Cleaner:</b> {'🟢 चालू' if not c else '🔴 बंद'}", parse_mode=HTML)


@Client.on_message(filters.command(["prefix"]) & filters.private)
async def set_prefix(client: Client, message: Message):
    uid = message.from_user.id
    await load_cfg(uid)
    t = arg_text(message)
    batch_temp.USER_PREFIX[uid] = t
    await save_cfg(uid)
    if not t:
        return await message.reply_text("Prefix हटा दिया गया।")
    await message.reply_text(f"✅ Prefix सेट हुआ: <code>{htmllib.escape(t)}</code>", parse_mode=HTML)


@Client.on_message(filters.command(["suffix"]) & filters.private)
async def set_suffix(client: Client, message: Message):
    uid = message.from_user.id
    await load_cfg(uid)
    t = arg_text(message)
    batch_temp.USER_SUFFIX[uid] = t
    await save_cfg(uid)
    if not t:
        return await message.reply_text("Suffix हटा दिया गया।")
    await message.reply_text(f"✅ Suffix सेट हुआ: <code>{htmllib.escape(t)}</code>", parse_mode=HTML)


@Client.on_message(filters.command(["setchat"]) & filters.private)
async def set_dump_chat_command(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("<code>/setchat -100xxxxxxxxxx</code>", parse_mode=HTML)
    if args[1].lower() == "clear":
        await db.del_dump_chat(message.from_user.id)
        return await message.reply_text("✅ Dump Chat हटा दी गई।")
    try:
        chat_id = int(args[1])
        chat = await client.get_chat(chat_id)
        await db.set_dump_chat(message.from_user.id, chat_id)
        await message.reply_text(f"✅ <b>टारगेट ग्रुप सेट:</b> <code>{chat_id}</code> ({htmllib.escape(chat.title or '')})", parse_mode=HTML)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@Client.on_message(filters.command(["clearchat"]) & filters.private)
async def reset_my_dump_chat(client: Client, message: Message):
    uid = message.from_user.id
    await load_cfg(uid)
    await db.del_dump_chat(uid)
    batch_temp.USER_DEFAULT_TOPIC.pop(uid, None)
    batch_temp.USER_TOPIC_MAP[uid] = {}
    batch_temp.USER_KEYWORD_MAP[uid] = {}
    await save_cfg(uid)
    await message.reply_text("✅ <b>ग्रुप फॉरवर्डिंग बंद कर दी गई है! फाइलें अब पर्सनल चैट में आएँगी।</b>", parse_mode=HTML)


@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except Exception:
        pass
    buttons = [
        [InlineKeyboardButton("⚙️ Settings Panel", callback_data="settings_btn")],
        [InlineKeyboardButton("🆘 Help & Guide", callback_data="help_btn")]
    ]
    bot = await client.get_me()
    await client.send_message(
        chat_id=message.chat.id,
        text=script.START_TXT.format(message.from_user.mention, bot.username, bot.first_name),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=HTML
    )


@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await message.reply_text(script.HELP_TXT, parse_mode=HTML)


@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await message.reply_text("🛑 <b>टास्क तुरंत रोक दिया गया।</b>", parse_mode=HTML)


# =====================================================================
#  UNLIMITED SUPER-FAST TOPIC FORWARDING ENGINE
# =====================================================================
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


async def forward_one(client, acc, sender_app, msg, chat_target, destination_chat, uid, in_group, rules, base_link):
    mtype = get_message_type(msg)
    if not mtype:
        return False

    # 1. ऑटोमैटिक टॉपिक पहचान (ID मैपिंग + कीवर्ड + डिफ़ॉल्ट)
    target_topic = None
    if in_group:
        target_topic = detect_target_topic(uid, msg, getattr(msg, "message_thread_id", None))
    common = {"message_thread_id": target_topic} if target_topic else {}

    # 2. टेक्स्ट / इंडेक्स मैसेज
    if mtype == "Text":
        h = process_html(uid, msg.text.html, rules, base_link)
        if not h:
            return False
        await with_flood(client.send_message, destination_chat, h, parse_mode=HTML, **common)
        return True

    # 3. मीडिया — कैप्शन (फॉर्मेटिंग बचाकर)
    orig_caption = msg.caption.html if msg.caption else ""
    caption = process_html(uid, orig_caption, rules)
    overflow = None
    if caption and plain_len(caption) > 1024:      # 1024 से लंबा कैप्शन अलग मैसेज में
        overflow, caption = caption, ""

    kw = {"chat_id": destination_chat, "from_chat_id": chat_target, "message_id": msg.id, **common}
    if msg.caption is not None:                    # खाली "" भी भेजा जाएगा, ताकि पुराना कैप्शन न बचे
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

    # प्रयास 3: चैनल में रेस्ट्रिक्शन हो तभी डाउनलोड → अपलोड
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
        return await message.reply_text("❌ <b>लिंक पहचाना नहीं गया।</b> पोस्ट का लिंक भेजें (जैसे <code>https://t.me/c/123/45</code>)।", parse_mode=HTML)

    if batch_temp.IS_BATCH.get(uid) is False:
        return await message.reply_text("⚠️ <b>एक टास्क पहले से चालू है। /cancel भेजकर नया शुरू करें।</b>", parse_mode=HTML)

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
            user_data = await db.get_session(uid)
            if not user_data:
                return await message.reply("🔒 <b>प्राइवेट लिंक के लिए पहले /login करें।</b>", parse_mode=HTML)
            try:
                acc = Client(f"fast_{uid}", session_string=user_data, api_hash=API_HASH, api_id=API_ID, in_memory=True)
                await acc.connect()
            except Exception as e:
                acc = None
                return await message.reply(f"❌ लॉगिन एरर: {e}")

        sender_app = acc if is_private_link else client
        rules = await build_rules(uid)
        base_link = await get_base_link(client, destination_chat)

        for start in range(fromID, toID + 1, 100):          # 100-100 के बैच में एक साथ fetch (तेज़)
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
                                           uid, in_group, rules, base_link)
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
        batch_temp.IS_BATCH[uid] = True      # कोई भी error हो, यूज़र अटकेगा नहीं


# =====================================================================
#  INLINE CALLBACKS  (सिर्फ अपने बटन — दूसरे plugins के callbacks नहीं रोकेगा)
# =====================================================================
_TIPS = {
    "set_chat_help": "टारगेट ग्रुप के लिए भेजें: /setchat -100xxxxxxxxxx",
    "rename_tag_help": "नाम बदलने के लिए /replace 'पुराना' 'नया' भेजें।",
    "caption_help": "कैप्शन के लिए /prefix 'टेक्स्ट' और /suffix 'टेक्स्ट' भेजें।",
    "replace_help": "/replace 'पुराना' 'नया' — किसी भी फॉन्ट में हो, बदल जाएगा। /delword से हटाएँ।",
    "login_help": "प्राइवेट चैनल के लिए /login भेजकर लॉगिन करें।",
}


@Client.on_callback_query(filters.regex(
    r"^(settings_btn|help_btn|close_btn|clearchat_call|toggle_clean_ads_call|set_chat_help|rename_tag_help|caption_help|replace_help|login_help)$"))
async def callback_handlers(client: Client, query: CallbackQuery):
    data = query.data
    uid = query.from_user.id
    if data == "settings_btn":
        await open_settings_panel_impl(query.message)
    elif data == "help_btn":
        await query.message.reply_text(script.HELP_TXT, parse_mode=HTML)
    elif data == "close_btn":
        await query.message.delete()
    elif data == "clearchat_call":
        await load_cfg(uid)
        await db.del_dump_chat(uid)
        return await query.answer("ग्रुप फॉरवर्डिंग बंद कर दी गई!", show_alert=True)
    elif data == "toggle_clean_ads_call":
        await load_cfg(uid)
        c = batch_temp.USER_CLEAN_ADS.get(uid, False)
        batch_temp.USER_CLEAN_ADS[uid] = not c
        await save_cfg(uid)
        return await query.answer(f"Ad Cleaner: {'🟢 ON' if not c else '🔴 OFF'}", show_alert=True)
    elif data in _TIPS:
        return await query.answer(_TIPS[data], show_alert=True)
    await query.answer()      # हर रास्ते पर सिर्फ एक बार answer
