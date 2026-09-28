# Developed by: LastPerson07 × RexBots
# Telegram: @RexBots_Official | @THEUPDATEDGUYS
import os
import re
import shlex
import asyncio
import random
import time
import shutil
import pyrogram
import requests
import hashlib 
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant,
    InviteHashExpired, UsernameNotOccupied, AuthKeyUnregistered, UserDeactivated, UserDeactivatedBan
)
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, InputMediaPhoto
from config import API_ID, API_HASH, ERROR_MESSAGE
from database.db import db
import math
from logger import LOGGER
logger = LOGGER(__name__)

SUBSCRIPTION = os.environ.get('SUBSCRIPTION', 'https://graph.org/file/242b7f1b52743938d81f1.jpg')
FREE_LIMIT_SIZE = 2 * 1024 * 1024 * 1024
FREE_LIMIT_DAILY = 10
UPI_ID = os.environ.get("UPI_ID", "your_upi@oksbi")
QR_CODE = os.environ.get("QR_CODE", "https://graph.org/file/242b7f1b52743938d81f1.jpg")
REACTIONS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🤬",
    "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊", "🤡", "🥱",
    "🥴", "😍", "🐳", "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡", "🍌"
]

dev_text = "👨‍💻 Mind Behind This Bot:\n• @iamtghelp"
channels_text = "📢 Official Channels:\n• @iamtghelp\n\nStay updated for new features!"

class script(object):
    START_TXT = """<b>👋 Hello {},</b>
<b>🤖 I am <a href=https://t.me/{}>{}</a></b>
<i>Your Professional Restricted Content Saver Bot.</i>
<blockquote><b>🚀 System Status: 🟢 Online</b>
<b>⚡ Performance: 10x High-Speed Processing</b>
<b>🔐 Security: End-to-End Encrypted</b>
<b>📊 Uptime: 99.9% Guaranteed</b></blockquote>
<b>👇 Select an Option Below to Get Started:</b>
"""
    HELP_TXT = """<b>📚 Comprehensive Help & User Guide</b>
<blockquote><b>1️⃣ Auto Topic Routing Commands:</b></blockquote>
• <code>/setchat &lt;group_id&gt;</code> - अपना ग्रुप सेट करें
• <code>/map_topic &lt;सामने_का_topic_id&gt; &lt;आपका_topic_id&gt;</code> - विषय मैच करें
• <code>/show_topics</code> - सेट किए गए सभी टॉपिक्स देखें
• <code>/reset_topics</code> - सभी टॉपिक मैपिंग साफ़ करें
• <code>/clearchat</code> - चैनल/ग्रुप फॉरवर्डिंग बंद करें

<blockquote><b>2️⃣ Text & Link Cleaners:</b></blockquote>
• <code>/clean_ads</code> - अन्य चैनलों के लिंक व प्रोमो ऑटो-डिलीट करें
• <code>/replace 'पुराना' 'नया'</code> - शब्द या नाम बदलें
• <code>/clear_replace</code> - सभी रिप्लेसमेंट साफ़ करें
"""
    ABOUT_TXT = """<b>ℹ️ About This Bot</b>"""
    PREMIUM_TEXT = """<b>💎 Premium Membership Plans</b>\n<b>UPI ID:</b> <code>{}</code>"""
    PROGRESS_BAR = """\
<b>⚡ Processing Task...</b>
<blockquote>
<b>Progress: {bar} {percentage:.1f}%</b>
<b>🚀 Speed:</b> <code>{speed}/s</code>
<b>💾 Size:</b> <code>{current} of {total}</code>
<b>⏱ Elapsed:</b> <code>{elapsed}</code>
<b>⏳ ETA:</b> <code>{eta}</code>
</blockquote>
"""
    CAPTION = """<b><a href="itsnrcbot"></a></b>\n\n<b>⚜️ Powered By : <a href="itsnrcbot">itsnrcbot 😎</a></b>"""
    LIMIT_REACHED = """<b>🚫 Daily Limit Exceeded</b>"""
    SIZE_LIMIT = """<b>⚠️ File Size Exceeded (Max 2GB)</b>"""

def humanbytes(size):
    if not size: return "0B"
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2] if tmp else "0s"

class batch_temp(object):
    IS_BATCH = {}
    USER_CLEAN_ADS = {}
    USER_PREFIX = {}
    USER_SUFFIX = {}
    USER_TOPIC_MAP = {} # {user_id: {source_topic_id: target_topic_id}}
    USER_DEFAULT_TOPIC = {}

def get_message_type(msg):
    if getattr(msg, 'document', None): return "Document"
    if getattr(msg, 'video', None): return "Video"
    if getattr(msg, 'photo', None): return "Photo"
    if getattr(msg, 'audio', None): return "Audio"
    if getattr(msg, 'text', None): return "Text"
    return None

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
        logger.error(f"Error redirecting universal links: {e}")
    return text_content, entities

async def downstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r", encoding='utf-8') as downread:
                txt = downread.read()
            await client.edit_message_text(chat, message.id, f"{txt}")
            await asyncio.sleep(5)
        except:
            await asyncio.sleep(5)

async def upstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r", encoding='utf-8') as upread:
                txt = upread.read()
            await client.edit_message_text(chat, message.id, f"{txt}")
            await asyncio.sleep(5)
        except:
            await asyncio.sleep(5)

def progress(current, total, message, type):
    if batch_temp.IS_BATCH.get(message.from_user.id): raise Exception("Cancelled")
    if not hasattr(progress, "cache"): progress.cache = {}
    now = time.time()
    task_id = f"{message.id}{type}"
    last_time = progress.cache.get(task_id, 0)
    if not hasattr(progress, "start_time"): progress.start_time = {}
    if task_id not in progress.start_time: progress.start_time[task_id] = now
       
    if (now - last_time) > 5 or current == total:
        try:
            percentage = current * 100 / total
            speed = current / (now - progress.start_time[task_id]) if (now - progress.start_time[task_id]) > 0 else 0
            eta = (total - current) / speed if speed > 0 else 0
            elapsed = now - progress.start_time[task_id]
            filled_length = int(percentage / 5)
            bar = '█' * filled_length + ' ' * (20 - filled_length)
           
            status = script.PROGRESS_BAR.format(
                bar=bar,
                percentage=percentage,
                current=humanbytes(current),
                total=humanbytes(total),
                speed=humanbytes(speed),
                elapsed=TimeFormatter(elapsed * 1000),
                eta=TimeFormatter(eta * 1000)
            )
            with open(f'{message.id}{type}status.txt', "w", encoding='utf-8') as fileup:
                fileup.write(status)
            progress.cache[task_id] = now
            if current == total:
                progress.start_time.pop(task_id, None)
                progress.cache.pop(task_id, None)
        except:
            pass

# --- AUTO TOPIC ROUTER COMMANDS ---
@Client.on_message(filters.command(["map_topic"]) & filters.private)
async def map_topic_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 3:
        return await message.reply_text(
            "<b>📌 Topic Map Usage:</b>\n"
            "<code>/map_topic &lt;सामने_का_topic_id&gt; &lt;आपका_topic_id&gt;</code>\n\n"
            "<i>उदा:</i> <code>/map_topic 4 15</code> (Hindi के लिए)",
            parse_mode=enums.ParseMode.HTML
        )
    try:
        s_id = int(args[1])
        t_id = int(args[2])
        if message.from_user.id not in batch_temp.USER_TOPIC_MAP:
            batch_temp.USER_TOPIC_MAP[message.from_user.id] = {}
        batch_temp.USER_TOPIC_MAP[message.from_user.id][s_id] = t_id
        await message.reply_text(
            f"<b>✅ मैपिंग सेट हो गई!</b>\nस्रोत टॉपिक <code>{s_id}</code> ➔ आपका टॉपिक <code>{t_id}</code>",
            parse_mode=enums.ParseMode.HTML
        )
    except ValueError:
        await message.reply_text("❌ कृपया केवल संख्या (ID) डालें।")

@Client.on_message(filters.command(["show_topics"]) & filters.private)
async def show_topics_cmd(client: Client, message: Message):
    mapping = batch_temp.USER_TOPIC_MAP.get(message.from_user.id, {})
    if not mapping:
        return await message.reply_text("ℹ️ अभी कोई टॉपिक मैप नहीं किया गया है।")
    out = "<b>📋 आपकी टॉपिक मैपिंग लिस्ट:</b>\n\n"
    for s, t in mapping.items():
        out += f"• स्रोत <code>{s}</code> ➔ आपका टॉपिक <code>{t}</code>\n"
    await message.reply_text(out, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["reset_topics"]) & filters.private)
async def reset_topics_cmd(client: Client, message: Message):
    batch_temp.USER_TOPIC_MAP[message.from_user.id] = {}
    await message.reply_text("<b>🧹 सभी टॉपिक मैपिंग साफ़ कर दी गई हैं।</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["settopic"]) & filters.private)
async def set_default_topic(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("<code>/settopic &lt;topic_id&gt;</code> या <code>/settopic clear</code>")
    if args[1].lower() == "clear":
        batch_temp.USER_DEFAULT_TOPIC.pop(message.from_user.id, None)
        return await message.reply_text("डिफ़ॉल्ट टॉपिक हटा दिया गया।")
    try:
        t_id = int(args[1])
        batch_temp.USER_DEFAULT_TOPIC[message.from_user.id] = t_id
        await message.reply_text(f"डिफ़ॉल्ट टॉपिक सेट: <code>{t_id}</code>")
    except:
        pass

@Client.on_message(filters.command(["replace", "r"]) & filters.private)
async def easy_replace_command(client: Client, message: Message):
    try:
        args = shlex.split(message.text)
        if len(args) < 3: return
        await db.set_replace_words(message.from_user.id, {args[1]: args[2]})
        await message.reply_text(f"✅ Replacement Saved: <code>{args[1]}</code> ➔ <code>{args[2]}</code>")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command(["clear_replace"]) & filters.private)
async def clear_replace_command(client: Client, message: Message):
    await db.col.update_one({'id': message.from_user.id}, {'$set': {'replace_words': {}, 'delete_words': []}})
    await message.reply_text("🧹 रिप्लेसमेंट साफ़ कर दिए गए।")

@Client.on_message(filters.command(["clean_ads"]) & filters.private)
async def toggle_clean_ads(client: Client, message: Message):
    c = batch_temp.USER_CLEAN_ADS.get(message.from_user.id, False)
    batch_temp.USER_CLEAN_ADS[message.from_user.id] = not c
    await message.reply_text(f"Ad/Link Cleaner: {'🟢 Enabled' if not c else '🔴 Disabled'}")

@Client.on_message(filters.command(["setchat"]) & filters.private)
async def set_dump_chat_command(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2: return
    if args[1].lower() == "clear":
        await db.del_dump_chat(message.from_user.id)
        return await message.reply_text("✅ Dump Chat साफ़ हो गई।")
    try:
        chat_id = int(args[1])
        chat = await client.get_chat(chat_id)
        await db.set_dump_chat(message.from_user.id, chat_id)
        await message.reply_text(f"✅ Dump Chat Set: <code>{chat_id}</code> ({chat.title})")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command(["clearchat"]) & filters.private)
async def reset_my_dump_chat(client: Client, message: Message):
    await db.del_dump_chat(message.from_user.id)
    await message.reply_text("✅ फॉरवर्डिंग बंद कर दी गई है! फाइलें अब पर्सनल चैट में आएँगी।")

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    bot = await client.get_me()
    buttons = [[InlineKeyboardButton("🆘 Help & Guide", callback_data="help_btn")]]
    await message.reply_text(script.START_TXT.format(message.from_user.mention, bot.username, bot.first_name), reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await message.reply_text(script.HELP_TXT, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await message.reply_text("❌ Batch Process Cancelled.")

@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" in message.text:
        if await db.check_limit(message.from_user.id):
            return await message.reply_text(script.LIMIT_REACHED)
       
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text("⚠️ टास्क पहले से चालू है।")
        
        dump_chat = await db.get_dump_chat(message.from_user.id)
        destination_chat = dump_chat if dump_chat else message.chat.id
        
        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        try: toID = int(temp[1].strip())
        except: toID = fromID
            
        batch_temp.IS_BATCH[message.from_user.id] = False
        is_private_link = "https://t.me/c/" in message.text
        is_batch = "https://t.me/b/" in message.text
        is_public_link = not is_private_link and not is_batch

        for msgid in range(fromID, toID + 1):
            if batch_temp.IS_BATCH.get(message.from_user.id): break
           
            # 1. PUBLIC
            if is_public_link:
                username = datas[3]
                try:
                    orig_msg = await client.get_messages(username, msgid)
                    s_topic = getattr(orig_msg, "message_thread_id", None)
                    t_topic = batch_temp.USER_TOPIC_MAP.get(message.from_user.id, {}).get(s_topic)
                    if not t_topic:
                        t_topic = batch_temp.USER_DEFAULT_TOPIC.get(message.from_user.id, None)

                    if orig_msg.text:
                        text_content, entities = await rewrite_text_and_links(client, orig_msg.text, orig_msg.entities, destination_chat, message.from_user.id)
                        await client.send_message(chat_id=destination_chat, text=text_content, entities=entities, message_thread_id=t_topic, parse_mode=None)
                    else:
                        caption = await apply_caption_replacements(message.from_user.id, orig_msg.caption or "")
                        kw = {"chat_id": destination_chat, "from_chat_id": username, "message_id": msgid, "caption": caption}
                        if t_topic: kw["message_thread_id"] = t_topic
                        await client.copy_message(**kw)
                    await db.add_traffic(message.from_user.id)
                    await asyncio.sleep(1)
                    continue
                except Exception as e:
                    logger.error(f"Public Copy Error: {e}")

            # 2. PRIVATE
            user_data = await db.get_session(message.from_user.id)
            if not user_data:
                await message.reply("🔒 पहले /login करें।")
                batch_temp.IS_BATCH[message.from_user.id] = True
                return
            try:
                acc = Client("saverestricted", session_string=user_data, api_hash=API_HASH, api_id=API_ID, in_memory=True, max_concurrent_transmissions=10)
                await acc.connect()
            except Exception as e:
                batch_temp.IS_BATCH[message.from_user.id] = True
                return await message.reply(f"❌ Login error: {e}")
            
            chatid = int("-100" + datas[4]) if is_private_link else datas[4]
            await handle_restricted_content(client, acc, message, chatid, msgid, destination_chat)
            await asyncio.sleep(2)
            
        batch_temp.IS_BATCH[message.from_user.id] = True

async def handle_restricted_content(client: Client, acc, message: Message, chat_target, msgid, destination_chat):
    try:
        msg: Message = await acc.get_messages(chat_target, msgid)
    except Exception as e:
        return
    if msg.empty or not get_message_type(msg): return
    msg_type = get_message_type(msg)

    # --- AUTO TOPIC ROUTING ---
    # चेक करेगा कि मैसेज सामने वाले के किस टॉपिक (Thread ID) से आ रहा है
    source_topic = getattr(msg, "message_thread_id", None)
    target_topic = batch_temp.USER_TOPIC_MAP.get(message.from_user.id, {}).get(source_topic)
    
    # अगर मैप नहीं किया है तो डिफ़ॉल्ट टॉपिक लेगा
    if not target_topic:
        target_topic = batch_temp.USER_DEFAULT_TOPIC.get(message.from_user.id, None)

    # अगर टेक्स्ट/इंडेक्स मैसेज है:
    if msg_type == "Text":
        try:
            text_content, entities = await rewrite_text_and_links(client, msg.text or "", msg.entities, destination_chat, message.from_user.id)
            await client.send_message(destination_chat, text_content, entities=entities, message_thread_id=target_topic, parse_mode=None)
            return
        except Exception as e:
            return

    # मीडिया डाउनलोड व अपलोड
    await db.add_traffic(message.from_user.id)
    smsg = await client.send_message(message.chat.id, '<b>⬇️ Downloading...</b>', reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
    temp_dir = f"downloads/{message.id}"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    try:
        asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, message.chat.id))
        file = await acc.download_media(msg, file_name=f"{temp_dir}/", progress=progress, progress_args=[message, "down"])
        if os.path.exists(f'{message.id}downstatus.txt'): os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        return await smsg.delete()

    try:
        asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, message.chat.id))
        caption = await apply_caption_replacements(message.from_user.id, msg.caption or "")
        send_kw = {"chat_id": destination_chat, "caption": caption}
        if target_topic:
            send_kw["message_thread_id"] = target_topic

        if msg_type == "Document":
            await client.send_document(**send_kw, document=file, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Video":
            await client.send_video(**send_kw, video=file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Audio":
            await client.send_audio(**send_kw, audio=file, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Photo":
            await client.send_photo(**send_kw, photo=file)
    except Exception as e:
        await smsg.edit(f"Upload Failed: {e}")
        
    if os.path.exists(f'{message.id}upstatus.txt'): os.remove(f'{message.id}upstatus.txt')
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    await client.delete_messages(message.chat.id, [smsg.id])

@Client.on_callback_query()
async def button_callbacks(client: Client, callback_query: CallbackQuery):
    if callback_query.data == "help_btn":
        await callback_query.edit_message_text(script.HELP_TXT, parse_mode=enums.ParseMode.HTML)
    await callback_query.answer()
