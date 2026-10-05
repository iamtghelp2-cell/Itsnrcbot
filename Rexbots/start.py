# Developed by: LastPerson07 × RexBots
# Optimized for: Unlimited Fast Multi-Topic Forwarding & Keyword Smart Router
import os
import re
import shlex
import asyncio
import random
import time
import shutil
import pyrogram
import requests
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant,
    InviteHashExpired, UsernameNotOccupied, AuthKeyUnregistered
)
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, InputMediaPhoto
from config import API_ID, API_HASH
from database.db import db
from logger import LOGGER

logger = LOGGER(__name__)

SUBSCRIPTION = os.environ.get('SUBSCRIPTION', 'https://graph.org/file/242b7f1b52743938d81f1.jpg')
UPI_ID = os.environ.get("UPI_ID", "your_upi@oksbi")
QR_CODE = os.environ.get("QR_CODE", "https://graph.org/file/242b7f1b52743938d81f1.jpg")

REACTIONS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "⚡", "💯"
]

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
• <code>/show_topics</code> - एक्टिव टॉपिक लिस्ट देखें
• <code>/reset_topics</code> - सभी टॉपिक मैपिंग साफ़ करें

<blockquote><b>📝 /set_topics का सही फॉर्मेट:</b></blockquote>
<code>/set_topics
Maths: https://t.me/c/3635348530/7
Reasoning: https://t.me/c/3635348530/8
Polity: https://t.me/c/3635348530/11
Current Affairs: https://t.me/c/3635348530/4</code>

<blockquote><b>⚙️ 2. ऑटो क्लीनर व कैप्शन:</b></blockquote>
• <code>/setting</code> - पूरा इनलाइन सेटिंग्स डैशबोर्ड खोलें
• <code>/clean_ads</code> - अन्य चैनलों के लिंक व प्रोमो ऑटो-डिलीट करें
• <code>/replace 'पुराना' 'नया'</code> - शब्द या नाम बदलें
• <code>/clear_replace</code> - सभी रिप्लेसमेंट साफ़ करें
• <code>/prefix 'टेक्स्ट'</code> - कैप्शन के ऊपर नाम जोड़ें
• <code>/suffix 'टेक्स्ट'</code> - कैप्शन के नीचे नाम जोड़ें

<blockquote><b>🛑 3. टास्क कंट्रोल:</b></blockquote>
• <code>/cancel</code> - चल रहे बैच टास्क को तुरंत रोकें
"""
    CAPTION = """<b><a href="itsnrcbot"></a></b>\n\n<b>⚜️ Powered By : <a href="itsnrcbot">itsnrcbot 😎</a></b>"""

def humanbytes(size):
    if not size: return "0B"
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

class batch_temp(object):
    IS_BATCH = {}
    USER_CLEAN_ADS = {}
    USER_PREFIX = {}
    USER_SUFFIX = {}
    USER_TOPIC_MAP = {}       # {user_id: {source_topic_id: target_topic_id}}
    USER_KEYWORD_MAP = {}     # {user_id: {subject_keyword: target_topic_id}}
    USER_DEFAULT_TOPIC = {}   # {user_id: default_topic_id}

def get_message_type(msg):
    if getattr(msg, 'document', None): return "Document"
    if getattr(msg, 'video', None): return "Video"
    if getattr(msg, 'photo', None): return "Photo"
    if getattr(msg, 'audio', None): return "Audio"
    if getattr(msg, 'text', None): return "Text"
    return None

def detect_target_topic(user_id: int, msg: Message, source_topic: int = None) -> int:
    # 1. सीधे ID मैपिंग की जाँच (/map_topic)
    if source_topic:
        mapped_id = batch_temp.USER_TOPIC_MAP.get(user_id, {}).get(source_topic)
        if mapped_id:
            return mapped_id

    # 2. कैप्शन / फ़ाइलनेम / टेक्स्ट से कीवर्ड मैचिंग (/set_topics)
    keyword_map = batch_temp.USER_KEYWORD_MAP.get(user_id, {})
    if keyword_map:
        searchable_text = (msg.caption or msg.text or "").lower()
        if msg.video and getattr(msg.video, 'file_name', None):
            searchable_text += " " + msg.video.file_name.lower()
        elif msg.document and getattr(msg.document, 'file_name', None):
            searchable_text += " " + msg.document.file_name.lower()

        for kw, target_id in keyword_map.items():
            if re.search(r'\b' + re.escape(kw) + r'\b', searchable_text, re.IGNORECASE) or kw in searchable_text:
                return target_id

    # 3. डिफ़ॉल्ट टॉपिक
    return batch_temp.USER_DEFAULT_TOPIC.get(user_id, None)

async def apply_caption_replacements(user_id: int, caption: str) -> str:
    if not caption: return ""
    if batch_temp.USER_CLEAN_ADS.get(user_id, False):
        caption = re.sub(r'(https?://\S+|t\.me/\S+)', '', caption)
        caption = re.sub(r'Join\s*:\s*@\S+', '', caption, flags=re.IGNORECASE)

    repl_words = await db.get_replace_words(user_id)
    if repl_words:
        for old_w, new_w in repl_words.items():
            caption = caption.replace(old_w, new_w)
            
    del_words = await db.get_delete_words(user_id)
    if del_words:
        for del_w in del_words:
            caption = caption.replace(del_w, "")

    prefix = batch_temp.USER_PREFIX.get(user_id, "")
    suffix = batch_temp.USER_SUFFIX.get(user_id, "")
    if prefix: caption = f"{prefix}\n\n{caption}"
    if suffix: caption = f"{caption}\n\n{suffix}"
    return caption.strip()

async def rewrite_text_and_links(client: Client, text_content: str, entities, destination_chat: int, user_id: int):
    if not text_content: return "", []
    text_content = await apply_caption_replacements(user_id, text_content)
    try:
        dest_chat_obj = await client.get_chat(destination_chat)
        if dest_chat_obj.username:
            my_base_link = f"https://t.me/{dest_chat_obj.username}"
        else:
            clean_dest_id = str(destination_chat).replace("-100", "")
            my_base_link = f"https://t.me/c/{clean_dest_id}"
            
        text_content = re.sub(r'https?://t\.me/(?:c/\d+|[a-zA-Z0-9_]+)/(\d+)', rf'{my_base_link}/\1', text_content)
        text_content = re.sub(r'https?://t\.me/(?:joinchat/|\+)?([a-zA-Z0-9_]+)', my_base_link, text_content)

        if entities:
            for ent in entities:
                if ent.type == enums.MessageEntityType.TEXT_LINK and ent.url:
                    post_match = re.search(r'/(\d+)$', ent.url)
                    if post_match:
                        ent.url = f"{my_base_link}/{post_match.group(1)}"
                    else:
                        ent.url = my_base_link
    except Exception as e:
        logger.error(f"Link rewrite error: {e}")
    return text_content, entities

# --- TOPIC ROUTING COMMANDS ---

@Client.on_message(filters.command(["set_topics"]) & filters.private)
async def set_topics_bulk_cmd(client: Client, message: Message):
    text = message.text.replace("/set_topics", "").strip()
    if not text:
        return await message.reply_text(
            "<b>📌 Topic Setup Format:</b>\n\n"
            "<code>/set_topics\n"
            "Maths: https://t.me/c/3635348530/7\n"
            "Reasoning: https://t.me/c/3635348530/8\n"
            "Polity: https://t.me/c/3635348530/11\n"
            "Current Affairs: https://t.me/c/3635348530/4</code>",
            parse_mode=enums.ParseMode.HTML
        )
    
    mapping = {}
    lines = text.split("\n")
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            name = parts[0].strip().lower()
            link = parts[1].strip()
            match = re.search(r"/(\d+)$", link)
            if match:
                topic_id = int(match.group(1))
                mapping[name] = topic_id

    if not mapping:
        return await message.reply_text("❌ कोई मान्य टॉपिक लिंक नहीं मिला। सही प्रारूप में भेजें।")

    batch_temp.USER_KEYWORD_MAP[message.from_user.id] = mapping
    
    out = "<b>✅ सभी विषय और उनके टॉपिक ID सफलतापूर्वक सेट हो गए:</b>\n\n"
    for name, t_id in mapping.items():
        out += f"• <b>{name.title()}</b> ➔ Topic ID: <code>{t_id}</code>\n"
    await message.reply_text(out, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["map_topic"]) & filters.private)
async def map_topic_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 3:
        return await message.reply_text(
            "<b>📌 Topic Map Usage:</b>\n"
            "<code>/map_topic &lt;सामने_का_topic_id&gt; &lt;आपका_topic_id&gt;</code>\n\n"
            "<i>उदा:</i> <code>/map_topic 4 15</code>",
            parse_mode=enums.ParseMode.HTML
        )
    try:
        s_id = int(args[1])
        t_id = int(args[2])
        if message.from_user.id not in batch_temp.USER_TOPIC_MAP:
            batch_temp.USER_TOPIC_MAP[message.from_user.id] = {}
        batch_temp.USER_TOPIC_MAP[message.from_user.id][s_id] = t_id
        await message.reply_text(
            f"<b>✅ मैपिंग सेव हो गई:</b>\nस्रोत टॉपिक <code>{s_id}</code> ➔ आपका टॉपिक <code>{t_id}</code>",
            parse_mode=enums.ParseMode.HTML
        )
    except ValueError:
        await message.reply_text("❌ केवल संख्या डालें।")

@Client.on_message(filters.command(["show_topics"]) & filters.private)
async def show_topics_cmd(client: Client, message: Message):
    kw_mapping = batch_temp.USER_KEYWORD_MAP.get(message.from_user.id, {})
    id_mapping = batch_temp.USER_TOPIC_MAP.get(message.from_user.id, {})
    default_top = batch_temp.USER_DEFAULT_TOPIC.get(message.from_user.id, "सेट नहीं")

    out = f"<b>📋 आपकी एक्टिव टॉपिक सेटिंग्स:</b>\n\n"
    out += f"<b>डिफ़ॉल्ट टॉपिक:</b> <code>{default_top}</code>\n\n"

    if kw_mapping:
        out += "<b>🔸 ऑटो-कीवर्ड विषय:</b>\n"
        for s, t in kw_mapping.items():
            out += f"• {s.title()} ➔ Topic ID: <code>{t}</code>\n"
        out += "\n"

    if id_mapping:
        out += "<b>🔸 डायरेक्ट ID मैपिंग:</b>\n"
        for s, t in id_mapping.items():
            out += f"• स्रोत ID <code>{s}</code> ➔ आपका Topic ID: <code>{t}</code>\n"

    if not kw_mapping and not id_mapping:
        out += "<i>ℹ️ अभी कोई कस्टम टॉपिक सेट नहीं है।</i>"

    await message.reply_text(out, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["reset_topics"]) & filters.private)
async def reset_topics_cmd(client: Client, message: Message):
    batch_temp.USER_TOPIC_MAP[message.from_user.id] = {}
    batch_temp.USER_KEYWORD_MAP[message.from_user.id] = {}
    batch_temp.USER_DEFAULT_TOPIC.pop(message.from_user.id, None)
    await message.reply_text("🧹 <b>सभी टॉपिक मैपिंग और कीवर्ड्स साफ़ कर दिए गए हैं।</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["settopic"]) & filters.private)
async def set_default_topic(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("<code>/settopic &lt;topic_id&gt;</code> या <code>/settopic clear</code>", parse_mode=enums.ParseMode.HTML)
    if args[1].lower() == "clear":
        batch_temp.USER_DEFAULT_TOPIC.pop(message.from_user.id, None)
        return await message.reply_text("✅ डिफ़ॉल्ट टॉपिक हटा दिया गया।")
    try:
        t_id = int(args[1])
        batch_temp.USER_DEFAULT_TOPIC[message.from_user.id] = t_id
        await message.reply_text(f"✅ <b>डिफ़ॉल्ट टॉपिक सेट हुआ:</b> <code>{t_id}</code>", parse_mode=enums.ParseMode.HTML)
    except ValueError:
        await message.reply_text("❌ केवल संख्या डालें।")

# --- CORE USER SETTINGS & TOOLS ---

@Client.on_message(filters.command(["setting", "settings"]) & filters.private)
async def open_settings_panel(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton("Set Chat ID", callback_data="set_chat_help"),
            InlineKeyboardButton("Reset Chat ID", callback_data="clearchat_call")
        ],
        [
            InlineKeyboardButton("Set Rename Tag", callback_data="rename_tag_help"),
            InlineKeyboardButton("Caption", callback_data="caption_help")
        ],
        [
            InlineKeyboardButton("Replace Words", callback_data="replace_help"),
            InlineKeyboardButton("Clean Ads", callback_data="toggle_clean_ads_call")
        ],
        [
            InlineKeyboardButton("Session Login", callback_data="login_help"),
            InlineKeyboardButton("Close Menu ❌", callback_data="close_btn")
        ]
    ]
    img = "https://i.ibb.co/3kX9tjGXP/settings.jpg"
    await message.reply_photo(
        photo=img,
        caption="<b>⚙️ Settings & Configuration Dashboard</b>\n\n<i>नीचे दिए गए विकल्पों से अपने बोट को कस्टमाइज़ करें:</i>",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command(["replace", "r"]) & filters.private)
async def easy_replace_command(client: Client, message: Message):
    try:
        args = shlex.split(message.text)
        if len(args) < 3:
            return await message.reply_text("<code>/replace 'Old Word' 'New Word'</code>", parse_mode=enums.ParseMode.HTML)
        await db.set_replace_words(message.from_user.id, {args[1]: args[2]})
        await message.reply_text(f"✅ <b>Replacement Saved:</b> <code>{args[1]}</code> ➔ <code>{args[2]}</code>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command(["clear_replace"]) & filters.private)
async def clear_replace_command(client: Client, message: Message):
    await db.col.update_one({'id': message.from_user.id}, {'$set': {'replace_words': {}, 'delete_words': []}})
    await message.reply_text("🧹 <b>सभी रिप्लेसमेंट साफ़ कर दिए गए।</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["clean_ads"]) & filters.private)
async def toggle_clean_ads(client: Client, message: Message):
    c = batch_temp.USER_CLEAN_ADS.get(message.from_user.id, False)
    batch_temp.USER_CLEAN_ADS[message.from_user.id] = not c
    await message.reply_text(f"<b>Ad Cleaner:</b> {'🟢 चालू' if not c else '🔴 बंद'}", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["prefix"]) & filters.private)
async def set_prefix(client: Client, message: Message):
    args = shlex.split(message.text)
    if len(args) < 2:
        batch_temp.USER_PREFIX[message.from_user.id] = ""
        return await message.reply_text("Prefix हटा दिया गया।")
    batch_temp.USER_PREFIX[message.from_user.id] = args[1]
    await message.reply_text(f"✅ Prefix सेट हुआ: <code>{args[1]}</code>")

@Client.on_message(filters.command(["suffix"]) & filters.private)
async def set_suffix(client: Client, message: Message):
    args = shlex.split(message.text)
    if len(args) < 2:
        batch_temp.USER_SUFFIX[message.from_user.id] = ""
        return await message.reply_text("Suffix हटा दिया गया।")
    batch_temp.USER_SUFFIX[message.from_user.id] = args[1]
    await message.reply_text(f"✅ Suffix सेट हुआ: <code>{args[1]}</code>")

@Client.on_message(filters.command(["setchat"]) & filters.private)
async def set_dump_chat_command(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("<code>/setchat -100xxxxxxxxxx</code>", parse_mode=enums.ParseMode.HTML)
    if args[1].lower() == "clear":
        await db.del_dump_chat(message.from_user.id)
        return await message.reply_text("✅ Dump Chat हटा दी गई।")
    try:
        chat_id = int(args[1])
        chat = await client.get_chat(chat_id)
        await db.set_dump_chat(message.from_user.id, chat_id)
        await message.reply_text(f"✅ <b>टारगेट ग्रुप सेट:</b> <code>{chat_id}</code> ({chat.title})", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command(["clearchat"]) & filters.private)
async def reset_my_dump_chat(client: Client, message: Message):
    await db.del_dump_chat(message.from_user.id)
    batch_temp.USER_DEFAULT_TOPIC.pop(message.from_user.id, None)
    batch_temp.USER_TOPIC_MAP[message.from_user.id] = {}
    batch_temp.USER_KEYWORD_MAP[message.from_user.id] = {}
    await message.reply_text("✅ <b>ग्रुप फॉरवर्डिंग बंद कर दी गई है! फाइलें अब पर्सनल चैट में आएँगी।</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
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
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await message.reply_text(script.HELP_TXT, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await message.reply_text("🛑 <b>टास्क तुरंत रोक दिया गया।</b>", parse_mode=enums.ParseMode.HTML)

# --- UNLIMITED SUPER-FAST TOPIC FORWARDING ENGINE ---

@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" not in message.text:
        return

    if batch_temp.IS_BATCH.get(message.from_user.id) is False:
        return await message.reply_text("⚠️ <b>एक टास्क पहले से चालू है। /cancel भेजकर नया शुरू करें।</b>", parse_mode=enums.ParseMode.HTML)

    dump_chat = await db.get_dump_chat(message.from_user.id)
    destination_chat = dump_chat if dump_chat else message.chat.id

    datas = message.text.split("/")
    temp = datas[-1].replace("?single", "").split("-")
    fromID = int(temp[0].strip())
    try:
        toID = int(temp[1].strip())
    except:
        toID = fromID

    batch_temp.IS_BATCH[message.from_user.id] = False
    is_private_link = "https://t.me/c/" in message.text

    acc = None
    if is_private_link:
        user_data = await db.get_session(message.from_user.id)
        if not user_data:
            batch_temp.IS_BATCH[message.from_user.id] = True
            return await message.reply("🔒 <b>प्राइवेट लिंक के लिए पहले /login करें।</b>", parse_mode=enums.ParseMode.HTML)
        try:
            acc = Client("unlimited_fast", session_string=user_data, api_hash=API_HASH, api_id=API_ID, in_memory=True)
            await acc.connect()
        except Exception as e:
            batch_temp.IS_BATCH[message.from_user.id] = True
            return await message.reply(f"❌ लॉगिन एरर: {e}")

    chat_target = int("-100" + datas[4]) if is_private_link else datas[3]
    sender_app = acc if is_private_link else client

    for msgid in range(fromID, toID + 1):
        if batch_temp.IS_BATCH.get(message.from_user.id):
            break

        try:
            try:
                msg: Message = await sender_app.get_messages(chat_target, msgid)
            except FloodWait as fw:
                await asyncio.sleep(fw.value)
                msg = await sender_app.get_messages(chat_target, msgid)

            if not msg or msg.empty or not get_message_type(msg):
                continue

            # 1. ऑटोमैटिक टॉपिक पहचान (Keyword + Mapping + Default)
            source_topic = getattr(msg, "message_thread_id", None)
            target_topic = detect_target_topic(message.from_user.id, msg, source_topic)

            # 2. टेक्स्ट और इंडेक्स मैसेज
            msg_type = get_message_type(msg)
            if msg_type == "Text":
                text_content, entities = await rewrite_text_and_links(
                    client, msg.text or "", msg.entities, destination_chat, message.from_user.id
                )
                kw = {"chat_id": destination_chat, "text": text_content, "entities": entities, "parse_mode": None}
                if target_topic and destination_chat != message.chat.id:
                    kw["message_thread_id"] = target_topic
                await client.send_message(**kw)
                await asyncio.sleep(0.5)
                continue

            # 3. 1-सेकंड डायरेक्ट सर्वर-साइड क्लोन
            caption = await apply_caption_replacements(message.from_user.id, msg.caption or "")
            kw = {
                "chat_id": destination_chat,
                "from_chat_id": chat_target,
                "message_id": msgid
            }
            if caption:
                kw["caption"] = caption
            if target_topic and destination_chat != message.chat.id:
                kw["message_thread_id"] = target_topic

            copied = False

            # प्रयास 1: यूजर अकाउंट से डायरेक्ट कॉपी (सुपर-फ़ास्ट)
            if acc:
                try:
                    await acc.copy_message(**kw)
                    copied = True
                except Exception:
                    pass

            # प्रयास 2: बॉट से कॉपी
            if not copied:
                try:
                    await client.copy_message(**kw)
                    copied = True
                except Exception:
                    pass

            # प्रयास 3: केवल तब डाउनलोड जब चैनल में रेस्ट्रिक्शन लगा हो
            if not copied:
                temp_dir = f"downloads/{message.id}_{msgid}"
                os.makedirs(temp_dir, exist_ok=True)
                try:
                    file = await sender_app.download_media(msg, file_name=f"{temp_dir}/")
                    send_kw = {"chat_id": destination_chat, "caption": caption}
                    if target_topic and destination_chat != message.chat.id:
                        send_kw["message_thread_id"] = target_topic

                    if msg_type == "Video":
                        await client.send_video(**send_kw, video=file, duration=msg.video.duration if msg.video else 0)
                    elif msg_type == "Document":
                        await client.send_document(**send_kw, document=file)
                    elif msg_type == "Photo":
                        await client.send_photo(**send_kw, photo=file)
                    elif msg_type == "Audio":
                        await client.send_audio(**send_kw, audio=file)
                finally:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)

            await asyncio.sleep(0.5)

        except Exception as err:
            logger.error(f"Error on msg {msgid}: {err}")
            await asyncio.sleep(1)

    if acc:
        await acc.disconnect()

    batch_temp.IS_BATCH[message.from_user.id] = True

# --- INLINE CALLBACKS ---
@Client.on_callback_query()
async def callback_handlers(client: Client, query: CallbackQuery):
    data = query.data
    if data == "settings_btn":
        await open_settings_panel(client, query.message)
    elif data == "help_btn":
        await query.message.reply_text(script.HELP_TXT, parse_mode=enums.ParseMode.HTML)
    elif data == "close_btn":
        await query.message.delete()
    elif data == "clearchat_call":
        await db.del_dump_chat(query.from_user.id)
        await query.answer("ग्रुप फॉरवर्डिंग बंद कर दी गई!", show_alert=True)
    elif data == "toggle_clean_ads_call":
        c = batch_temp.USER_CLEAN_ADS.get(query.from_user.id, False)
        batch_temp.USER_CLEAN_ADS[query.from_user.id] = not c
        await query.answer(f"Ad Cleaner: {'🟢 ON' if not c else '🔴 OFF'}", show_alert=True)
    elif data in ["set_chat_help", "rename_tag_help", "caption_help", "replace_help", "login_help"]:
        await query.answer("कमांड की जानकारी के लिए /help देखें।", show_alert=True)
    await query.answer()
