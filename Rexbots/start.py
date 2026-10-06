# ==============================================================================
# Ultra-Fast Universal Content Saver & Topic Router Bot (100% Working)
# Supports: Public Channels/Groups, Private Channels/Topics, Forum Supergroups
# ==============================================================================

import os
import re
import shlex
import asyncio
import shutil
import logging
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from config import API_ID, API_HASH, BOT_TOKEN
from database.db import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

bot = Client("UltraFastRouterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

class State:
    IS_BUSY = {}
    CLEAN_ADS = {}
    PREFIX = {}
    SUFFIX = {}
    TOPIC_KEYWORD_MAP = {}   # {user_id: {"keyword": topic_id}}
    DEFAULT_TOPIC = {}       # {user_id: topic_id}

# --- 1. सटीक लिंक पार्सर (सभी तरह के टेलीग्राम लिंक्स के लिए) ---
def parse_tg_link(url: str):
    url = url.split("?")[0].strip()
    
    # 1. Private Forum Topic Link: t.me/c/CHAT_ID/TOPIC_ID/MSG_ID
    m_priv_topic = re.search(r"t\.me/c/(\d+)/(\d+)/(\d+)", url)
    if m_priv_topic:
        return int("-100" + m_priv_topic.group(1)), int(m_priv_topic.group(3)), int(m_priv_topic.group(2))
        
    # 2. Private Normal Link: t.me/c/CHAT_ID/MSG_ID
    m_priv = re.search(r"t\.me/c/(\d+)/(\d+)", url)
    if m_priv:
        return int("-100" + m_priv.group(1)), int(m_priv.group(2)), None
        
    # 3. Public Forum Topic Link: t.me/USERNAME/TOPIC_ID/MSG_ID
    m_pub_topic = re.search(r"t\.me/([^/]+)/(\d+)/(\d+)", url)
    if m_pub_topic:
        return m_pub_topic.group(1), int(m_pub_topic.group(3)), int(m_pub_topic.group(2))
        
    # 4. Public Normal Link: t.me/USERNAME/MSG_ID
    m_pub = re.search(r"t\.me/([^/]+)/(\d+)", url)
    if m_pub:
        return m_pub.group(1), int(m_pub.group(2)), None
        
    return None, None, None

def get_media_type(msg: Message):
    for media_type in ['video', 'document', 'photo', 'audio', 'voice', 'text']:
        if getattr(msg, media_type, None):
            return media_type.capitalize()
    return None

def resolve_target_topic(user_id: int, msg: Message, source_topic: int = None) -> int:
    kw_map = State.TOPIC_KEYWORD_MAP.get(user_id, {})
    if kw_map:
        search_str = (msg.caption or msg.text or "").lower()
        if msg.video and getattr(msg.video, 'file_name', None):
            search_str += " " + msg.video.file_name.lower()
        elif msg.document and getattr(msg.document, 'file_name', None):
            search_str += " " + msg.document.file_name.lower()

        for keyword, t_id in kw_map.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', search_str, re.IGNORECASE) or keyword in search_str:
                return t_id

    if source_topic:
        return source_topic

    return State.DEFAULT_TOPIC.get(user_id, None)

async def clean_and_format_caption(user_id: int, caption: str) -> str:
    if not caption:
        return ""
    if State.CLEAN_ADS.get(user_id, False):
        caption = re.sub(r'(https?://\S+|t\.me/\S+)', '', caption)
        caption = re.sub(r'@[a-zA-Z0-9_]+', '', caption)
        caption = re.sub(r'Join\s*:\s*\S+', '', caption, flags=re.IGNORECASE)

    try:
        replace_dict = await db.get_replace_words(user_id)
        if replace_dict:
            for old, new in replace_dict.items():
                caption = caption.replace(old, new)
        del_words = await db.get_delete_words(user_id)
        if del_words:
            for w in del_words:
                caption = caption.replace(w, "")
    except Exception:
        pass

    prefix = State.PREFIX.get(user_id, "")
    suffix = State.SUFFIX.get(user_id, "")
    if prefix: caption = f"{prefix}\n\n{caption}"
    if suffix: caption = f"{caption}\n\n{suffix}"
    return caption.strip()

# --- 2. यूजर कमांड्स ---

@bot.on_message(filters.command(["start"]))
async def start_handler(_, message: Message):
    text = (
        f"👋 <b>नमस्ते {message.from_user.mention}!</b>\n\n"
        "⚡ <b>फास्ट टॉपिक व चैनल फॉरवर्डिंग बॉट एक्टिव है।</b>\n\n"
        "• अपना टारगेट चैनल/ग्रुप सेट करें: <code>/setchat -100xxxxxxxxxx</code>\n"
        "• विषय अनुसार टॉपिक सेट करें: <code>/set_topics</code>\n"
        "• डिफ़ॉल्ट टॉपिक सेट करें: <code>/settopic &lt;topic_id&gt;</code>\n"
        "• प्राइवेट लिंक लॉगिन करें: <code>/login</code>\n"
        "• चालू टास्क रोकें: <code>/cancel</code>"
    )
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command(["setchat"]) & filters.private)
async def set_dump_chat(_, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("उपयोग: <code>/setchat -100xxxxxxxxxx</code>", parse_mode=enums.ParseMode.HTML)
    try:
        dest_id = int(args[1])
        chat = await bot.get_chat(dest_id)
        await db.set_dump_chat(message.from_user.id, dest_id)
        await message.reply_text(f"✅ <b>टारगेट सेट हुआ:</b> {chat.title} [<code>{dest_id}</code>]", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ चैट नहीं मिली। सुनिश्चित करें कि बॉट चैनल/ग्रुप में एडमिन है।\nएरर: {e}")

@bot.on_message(filters.command(["set_topics"]) & filters.private)
async def set_topics_bulk(_, message: Message):
    content = message.text.replace("/set_topics", "").strip()
    if not content:
        return await message.reply_text(
            "<b>फॉर्मेट उदाहरण:</b>\n"
            "<code>/set_topics\n"
            "Maths: https://t.me/c/3635348530/7\n"
            "Reasoning: https://t.me/c/3635348530/8\n"
            "History: https://t.me/c/3635348530/11</code>",
            parse_mode=enums.ParseMode.HTML
        )
    mapping = {}
    for line in content.split("\n"):
        if ":" in line:
            name, link = line.split(":", 1)
            name = name.strip().lower()
            match = re.search(r"/(\d+)$", link.strip())
            if match:
                mapping[name] = int(match.group(1))

    if not mapping:
        return await message.reply_text("❌ कोई मान्य टॉपिक लिंक नहीं मिला।")

    State.TOPIC_KEYWORD_MAP[message.from_user.id] = mapping
    res = "<b>✅ टॉपिक कीवर्ड्स मैप हो गए:</b>\n\n"
    for k, v in mapping.items():
        res += f"• <b>{k.title()}</b> ➔ Topic ID: <code>{v}</code>\n"
    await message.reply_text(res, parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command(["settopic"]) & filters.private)
async def set_single_topic(_, message: Message):
    args = message.text.split()
    if len(args) < 2 or args[1].lower() == "clear":
        State.DEFAULT_TOPIC.pop(message.from_user.id, None)
        return await message.reply_text("✅ डिफ़ॉल्ट टॉपिक हटा दिया गया।")
    try:
        t_id = int(args[1])
        State.DEFAULT_TOPIC[message.from_user.id] = t_id
        await message.reply_text(f"✅ डिफ़ॉल्ट टॉपिक सेट हुआ: <code>{t_id}</code>")
    except ValueError:
        await message.reply_text("❌ कृपया केवल संख्यात्मक ID दर्ज करें।")

@bot.on_message(filters.command(["clearchat"]) & filters.private)
async def clear_chat_cmd(_, message: Message):
    await db.del_dump_chat(message.from_user.id)
    State.DEFAULT_TOPIC.pop(message.from_user.id, None)
    await message.reply_text("✅ टारगेट चैट हटा दी गई है। फाइलें अब पर्सनल बॉट DM में आएँगी।")

@bot.on_message(filters.command(["cancel"]) & filters.private)
async def cancel_task(_, message: Message):
    State.IS_BUSY[message.from_user.id] = False
    await message.reply_text("🛑 <b>फॉरवर्डिंग टास्क को रोक दिया गया है।</b>", parse_mode=enums.ParseMode.HTML)

# --- 3. कोर फास्ट फॉरवर्डिंग और एक्सट्रैक्टर इंजन ---

@bot.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def universal_forwarder(_, message: Message):
    if "t.me/" not in message.text:
        return

    user_id = message.from_user.id
    if State.IS_BUSY.get(user_id, False):
        return await message.reply_text("⚠️ एक टास्क पहले से चालू है। इसे रोकने के लिए <code>/cancel</code> भेजें।")

    raw_text = message.text.strip()
    range_match = re.search(r"-(\d+)$", raw_text)
    to_msg_id = int(range_match.group(1)) if range_match else None
    base_link = re.sub(r"-\d+$", "", raw_text)

    source_chat, from_msg_id, link_topic_id = parse_tg_link(base_link)
    if not source_chat or not from_msg_id:
        return await message.reply_text("❌ <b>अमान्य टेलीग्राम लिंक।</b> सही लिंक भेजें।")

    to_msg_id = to_msg_id or from_msg_id
    if to_msg_id < from_msg_id:
        to_msg_id = from_msg_id

    # टारगेट चैट और फोरम सपोर्ट डिटेक्शन
    target_chat = await db.get_dump_chat(user_id) or message.chat.id
    is_forum = False
    try:
        t_obj = await bot.get_chat(target_chat)
        if t_obj.type == enums.ChatType.SUPERGROUP and getattr(t_obj, 'is_forum', False):
            is_forum = True
    except Exception:
        pass

    # यूजर सेशन लोड (प्राइवेट कंटेंट और रेस्ट्रिक्टेड फाइलों के लिए आवश्यक)
    user_client = None
    session_str = await db.get_session(user_id)
    if session_str:
        try:
            user_client = Client(f"user_session_{user_id}", session_string=session_str, api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await user_client.connect()
        except Exception as e:
            logger.warning(f"Session connect error: {e}")
            user_client = None

    if isinstance(source_chat, int) and not user_client:
        return await message.reply_text("🔒 <b>प्राइवेट चैनल/ग्रुप से फाइल निकालने के लिए पहले <code>/login</code> करें।</b>")

    State.IS_BUSY[user_id] = True
    progress_msg = await message.reply_text(f"🚀 <b>टास्क शुरू हुआ:</b> <code>{from_msg_id}</code> से <code>{to_msg_id}</code>")

    success_count = 0
    for current_id in range(from_msg_id, to_msg_id + 1):
        if not State.IS_BUSY.get(user_id, False):
            break

        msg = None
        # पहले यूजर सेशन से, फिर बॉट से मैसेज ढूंढें
        for client_instance in [user_client, bot]:
            if not client_instance:
                continue
            try:
                msg = await client_instance.get_messages(source_chat, current_id)
                if msg and not msg.empty:
                    break
            except FloodWait as f:
                await asyncio.sleep(f.value + 1)
                msg = await client_instance.get_messages(source_chat, current_id)
                break
            except RPCError:
                continue

        if not msg or msg.empty:
            continue

        media_type = get_media_type(msg)
        if not media_type:
            continue

        # टॉपिक का चुनाव
        source_topic = link_topic_id or getattr(msg, "message_thread_id", None)
        topic_to_post = resolve_target_topic(user_id, msg, source_topic)
        final_topic_id = topic_to_post if (is_forum and target_chat != message.chat.id) else None

        # 1. टेक्स्ट मैसेज
        if media_type == "Text":
            new_text = await clean_and_format_caption(user_id, msg.text or "")
            kwargs = {"chat_id": target_chat, "text": new_text}
            if final_topic_id:
                kwargs["message_thread_id"] = final_topic_id
            try:
                await bot.send_message(**kwargs)
                success_count += 1
            except Exception as e:
                logger.error(f"Text send failed: {e}")
            await asyncio.sleep(0.3)
            continue

        # 2. सुपर-फास्ट सर्वर-साइड कॉपी
        new_caption = await clean_and_format_caption(user_id, msg.caption or "")
        copy_kwargs = {
            "chat_id": target_chat,
            "from_chat_id": source_chat,
            "message_id": current_id
        }
        if new_caption:
            copy_kwargs["caption"] = new_caption
        if final_topic_id:
            copy_kwargs["message_thread_id"] = final_topic_id

        copied = False
        for cl in [bot, user_client]:
            if not cl:
                continue
            try:
                await cl.copy_message(**copy_kwargs)
                copied = True
                success_count += 1
                break
            except Exception:
                pass

        # 3. रेस्ट्रिक्टेड कंटेंट बाईपास (डाउनलोड और री-अपलोड)
        if not copied:
            temp_path = f"downloads/{user_id}_{current_id}"
            os.makedirs(temp_path, exist_ok=True)
            downloader = user_client if user_client else bot
            try:
                dl_file = await downloader.download_media(msg, file_name=f"{temp_path}/")
                send_kwargs = {"chat_id": target_chat, "caption": new_caption}
                if final_topic_id:
                    send_kwargs["message_thread_id"] = final_topic_id

                if media_type == "Video":
                    await bot.send_video(**send_kwargs, video=dl_file, duration=getattr(msg.video, 'duration', 0))
                elif media_type == "Document":
                    await bot.send_document(**send_kwargs, document=dl_file)
                elif media_type == "Photo":
                    await bot.send_photo(**send_kwargs, photo=dl_file)
                elif media_type == "Audio":
                    await bot.send_audio(**send_kwargs, audio=dl_file)
                elif media_type == "Voice":
                    await bot.send_voice(**send_kwargs, voice=dl_file)

                success_count += 1
            except Exception as dl_err:
                logger.error(f"Download/Upload error on {current_id}: {dl_err}")
            finally:
                if os.path.exists(temp_path):
                    shutil.rmtree(temp_path, ignore_errors=True)

        await asyncio.sleep(0.4)

    if user_client:
        try:
            await user_client.disconnect()
        except Exception:
            pass

    State.IS_BUSY[user_id] = False
    await progress_msg.edit_text(f"✅ <b>टास्क पूरा हुआ!</b> कुल <code>{success_count}</code> मैसेज सफलतापूर्वक भेजे गए।")
