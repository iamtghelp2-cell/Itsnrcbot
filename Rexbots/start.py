# Developed by: LastPerson07 × RexBots
# Optimized for: Unlimited Fast Multi-Topic Forwarding with Live Progress Bar
import os
import re
import math
import time
import shlex
import asyncio
import random
import shutil
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import API_ID, API_HASH
from database.db import db
from logger import LOGGER

logger = LOGGER(__name__)

SUBSCRIPTION = os.environ.get('SUBSCRIPTION', 'https://graph.org/file/242b7f1b52743938d81f1.jpg')
UPI_ID = os.environ.get("UPI_ID", "your_upi@oksbi")
QR_CODE = os.environ.get("QR_CODE", "https://graph.org/file/242b7f1b52743938d81f1.jpg")

REACTIONS = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "⚡", "💯"]

class script(object):
    START_TXT = """<b>👋 Hello {},</b>
<b>🤖 I am <a href=https://t.me/{}>{}</a></b>
<i>Your High-Speed Restricted Content Saver & Topic Router Bot.</i>
<blockquote><b>🚀 System Status: 🟢 Online (VPS High-Speed Mode)</b>
<b>⚡ Performance: Direct Clone + Chunk Accelerated</b>
<b>🎯 Auto Topic Routing: Fully Enabled</b></blockquote>
"""
    HELP_TXT = """<b>📚 सम्पूर्ण कमांड और उपयोग गाइड:</b>

<blockquote><b>🎯 1. टॉपिक और ग्रुप फॉरवर्डिंग:</b></blockquote>
• <code>/setchat -100xxxxxxxxxx</code> - टारगेट ग्रुप सेट करें
• <code>/clearchat</code> - फॉरवर्डिंग बंद करें
• <code>/settopic &lt;topic_id&gt;</code> - डिफ़ॉल्ट टॉपिक ID सेट करें
• <code>/set_topics</code> - सभी विषयों के टॉपिक लिंक सेट करें
• <code>/show_topics</code> - एक्टिव टॉपिक लिस्ट देखें
• <code>/reset_topics</code> - सभी टॉपिक सेटिंग्स साफ़ करें

<blockquote><b>⚙️ 2. सेटिंग्स व रिप्लेसमेंट:</b></blockquote>
• <code>/replace 'पुराना' 'नया'</code> - शब्द या नाम बदलें
• <code>/clean_ads</code> - अन्य चैनलों के प्रोमो साफ़ करें
• <code>/cancel</code> - चल रहे टास्क को तुरंत रोकें
"""

def humanbytes(size):
    if not size: return "0B"
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s") if seconds else "")
    return tmp or "0s"

# --- लाइव प्रोग्रेस बार मैनेजर ---
async def progress_for_pyrogram(current, total, ud_type, message: Message, start_time):
    now = time.time()
    diff = now - start_time
    if round(diff % 3.5) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000 if speed > 0 else 0
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time_str = time_formatter(elapsed_time)
        estimated_total_time_str = time_formatter(estimated_total_time)

        progress = "[{0}{1}] \n<b>Progress:</b> {2}%\n".format(
            ''.join(["▰" for i in range(math.floor(percentage / 10))]),
            ''.join(["▱" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2))

        tmp = progress + "<b>Processed:</b> {0} of {1}\n<b>Speed:</b> {2}/s\n<b>ETA:</b> {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time_str if estimated_total_time_str != '' else "0s"
        )
        try:
            await message.edit_text(
                text=f"<b>{ud_type}</b>\n\n{tmp}",
                parse_mode=enums.ParseMode.HTML
            )
        except (MessageNotModified, FloodWait):
            pass
        except Exception:
            pass

class batch_temp(object):
    IS_BATCH = {}
    USER_CLEAN_ADS = {}
    USER_PREFIX = {}
    USER_SUFFIX = {}
    USER_TOPIC_MAP = {}
    USER_KEYWORD_MAP = {}
    USER_DEFAULT_TOPIC = {}

def get_message_type(msg):
    if getattr(msg, 'document', None): return "Document"
    if getattr(msg, 'video', None): return "Video"
    if getattr(msg, 'photo', None): return "Photo"
    if getattr(msg, 'audio', None): return "Audio"
    if getattr(msg, 'text', None): return "Text"
    return None

def detect_target_topic(user_id: int, msg: Message, source_topic: int = None) -> int:
    if source_topic:
        mapped_id = batch_temp.USER_TOPIC_MAP.get(user_id, {}).get(source_topic)
        if mapped_id:
            return mapped_id

    keyword_map = batch_temp.USER_KEYWORD_MAP.get(user_id, {})
    if keyword_map:
        searchable_text = (msg.caption or msg.text or "").lower()
        if msg.video and getattr(msg.video, 'file_name', None):
            searchable_text += " " + msg.video.file_name.lower()
        elif msg.document and getattr(msg.document, 'file_name', None):
            searchable_text += " " + msg.document.file_name.lower()

        for kw, target_id in keyword_map.items():
            if kw in searchable_text:
                return target_id

    return batch_temp.USER_DEFAULT_TOPIC.get(user_id, None)

async def apply_caption_replacements(user_id: int, caption: str) -> str:
    if not caption: return ""
    caption = caption.replace('\xa0', ' ').replace('\u200b', '')

    if batch_temp.USER_CLEAN_ADS.get(user_id, False):
        caption = re.sub(r'(https?://\S+|t\.me/\S+)', '', caption)
        caption = re.sub(r'Join\s*:\s*@\S+', '', caption, flags=re.IGNORECASE)

    repl_words = await db.get_replace_words(user_id)
    if repl_words:
        for old_w, new_w in repl_words.items():
            caption = re.sub(re.escape(old_w.strip()), new_w, caption, flags=re.IGNORECASE)
            
    del_words = await db.get_delete_words(user_id)
    if del_words:
        for del_w in del_words:
            caption = re.sub(re.escape(del_w.strip()), "", caption, flags=re.IGNORECASE)

    prefix = batch_temp.USER_PREFIX.get(user_id, "")
    suffix = batch_temp.USER_SUFFIX.get(user_id, "")
    if prefix: caption = f"{prefix}\n\n{caption}"
    if suffix: caption = f"{caption}\n\n{suffix}"
    return caption.strip()

# --- TOPIC ROUTING COMMANDS ---
@Client.on_message(filters.command(["set_topics"]) & filters.private)
async def set_topics_bulk_cmd(client: Client, message: Message):
    text = message.text.replace("/set_topics", "").strip()
    if not text:
        return await message.reply_text("<b>फॉर्मेट:</b>\n<code>/set_topics\nMaths: https://t.me/c/123/7\nReasoning: https://t.me/c/123/8</code>", parse_mode=enums.ParseMode.HTML)
    
    mapping = {}
    lines = text.split("\n")
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            name = parts[0].strip().lower()
            link = parts[1].strip()
            match = re.search(r"/(\d+)$", link)
            if match:
                mapping[name] = int(match.group(1))

    batch_temp.USER_KEYWORD_MAP[message.from_user.id] = mapping
    out = "<b>✅ सभी विषय सेट हो गए:</b>\n\n"
    for name, t_id in mapping.items():
        out += f"• <b>{name.title()}</b> ➔ ID: <code>{t_id}</code>\n"
    await message.reply_text(out, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["setchat"]) & filters.private)
async def set_dump_chat_command(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2: return await message.reply_text("<code>/setchat -100xxxxxxxxxx</code>")
    try:
        chat_id = int(args[1])
        chat = await client.get_chat(chat_id)
        await db.set_dump_chat(message.from_user.id, chat_id)
        await message.reply_text(f"✅ टारगेट ग्रुप: <code>{chat_id}</code> ({chat.title})")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await message.reply_text("🛑 <b>टास्क तुरंत रोक दिया गया।</b>", parse_mode=enums.ParseMode.HTML)

# --- MAIN FORWARDING ENGINE WITH LIVE SCREEN PROGRESS ---
@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" not in message.text: return

    if batch_temp.IS_BATCH.get(message.from_user.id) is False:
        return await message.reply_text("⚠️ एक टास्क पहले से चालू है। /cancel भेजें।")

    dump_chat = await db.get_dump_chat(message.from_user.id)
    destination_chat = dump_chat if dump_chat else message.chat.id

    # URL Parser (हर तरह के लिंक के लिए)
    clean_text = message.text.strip().split("?")[0].replace("?single", "")
    parts = [p for p in clean_text.split("/") if p]
    last_seg = parts[-1].strip()

    if "-" in last_seg:
        fromID = int(last_seg.split("-")[0])
        toID = int(last_seg.split("-")[1])
    else:
        fromID = int(last_seg)
        toID = fromID

    is_private_link = "t.me/c/" in clean_text
    chat_target = int("-100" + parts[parts.index("c") + 1]) if is_private_link else parts[3]

    batch_temp.IS_BATCH[message.from_user.id] = False
    acc = None

    if is_private_link:
        user_data = await db.get_session(message.from_user.id)
        if not user_data:
            batch_temp.IS_BATCH[message.from_user.id] = True
            return await message.reply("🔒 पहले /login करें।")
        try:
            acc = Client(f"vps_{message.from_user.id}", session_string=user_data, api_hash=API_HASH, api_id=API_ID, in_memory=True)
            await acc.connect()
        except Exception as e:
            batch_temp.IS_BATCH[message.from_user.id] = True
            return await message.reply(f"❌ लॉगिन एरर: {e}")

    sender_app = acc if is_private_link else client
    prog_msg = await message.reply_text("⚡ <b>टास्क शुरू हो रहा है...</b>", parse_mode=enums.ParseMode.HTML)

    for msgid in range(fromID, toID + 1):
        if batch_temp.IS_BATCH.get(message.from_user.id): break

        try:
            try:
                msg = await sender_app.get_messages(chat_target, msgid)
            except FloodWait as fw:
                await asyncio.sleep(fw.value)
                msg = await sender_app.get_messages(chat_target, msgid)

            if not msg or msg.empty or not get_message_type(msg): continue

            source_topic = getattr(msg, "message_thread_id", None)
            target_topic = detect_target_topic(message.from_user.id, msg, source_topic)
            msg_type = get_message_type(msg)

            caption = await apply_caption_replacements(message.from_user.id, msg.caption or "")

            kw = {"chat_id": destination_chat, "from_chat_id": chat_target, "message_id": msgid}
            if caption: kw["caption"] = caption
            if target_topic and destination_chat != message.chat.id:
                kw["message_thread_id"] = target_topic

            copied = False
            # 1. सुपरफास्ट डायरेक्ट क्लोन (1 सेकंड)
            if acc:
                try:
                    sent = await acc.copy_message(**kw)
                    copied = True
                except Exception: pass
            if not copied:
                try:
                    sent = await client.copy_message(**kw)
                    copied = True
                except Exception: pass

            # 2. अगर फाइल रेस्ट्रिक्टेड है -> स्क्रीन पर लाइव प्रतिशत के साथ डाउनलोड और अपलोड
            if not copied:
                temp_dir = f"downloads/{message.id}_{msgid}"
                os.makedirs(temp_dir, exist_ok=True)
                try:
                    # डाउनलोड प्रोग्रेस
                    d_start = time.time()
                    file = await sender_app.download_media(
                        msg,
                        file_name=f"{temp_dir}/",
                        progress=progress_for_pyrogram,
                        progress_args=("📥 <b>डाउनलोड हो रहा है...</b>", prog_msg, d_start)
                    )

                    send_kw = {"chat_id": destination_chat, "caption": caption}
                    if target_topic and destination_chat != message.chat.id:
                        send_kw["message_thread_id"] = target_topic

                    # अपलोड प्रोग्रेस
                    u_start = time.time()
                    u_args = ("📤 <b>अपलोड हो रहा है...</b>", prog_msg, u_start)

                    if msg_type == "Video":
                        await client.send_video(**send_kw, video=file, duration=msg.video.duration if msg.video else 0,
                                                progress=progress_for_pyrogram, progress_args=u_args)
                    elif msg_type == "Document":
                        await client.send_document(**send_kw, document=file,
                                                  progress=progress_for_pyrogram, progress_args=u_args)
                    elif msg_type == "Photo":
                        await client.send_photo(**send_kw, photo=file)
                    elif msg_type == "Audio":
                        await client.send_audio(**send_kw, audio=file,
                                                progress=progress_for_pyrogram, progress_args=u_args)
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)

            await asyncio.sleep(0.2)

        except Exception as err:
            logger.error(f"Error on msg {msgid}: {err}")
            await asyncio.sleep(1)

    await prog_msg.edit_text("✅ <b>सभी फाइलें सफलतापूर्वक प्रोसेस हो गईं!</b>", parse_mode=enums.ParseMode.HTML)
    if acc: await acc.disconnect()
    batch_temp.IS_BATCH[message.from_user.id] = True
