# Developed by: LastPerson07 × RexBots
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
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import API_ID, API_HASH
from database.db import db
from logger import LOGGER

logger = LOGGER(__name__)

SUBSCRIPTION = os.environ.get('SUBSCRIPTION', 'https://graph.org/file/242b7f1b52743938d81f1.jpg')
FREE_LIMIT_SIZE = 2 * 1024 * 1024 * 1024

class batch_temp(object):
    IS_BATCH = {}
    USER_CLEAN_ADS = {}
    USER_PREFIX = {}
    USER_SUFFIX = {}
    USER_TOPIC_MAP = {}
    USER_DEFAULT_TOPIC = {}

def get_message_type(msg):
    if getattr(msg, 'document', None): return "Document"
    if getattr(msg, 'video', None): return "Video"
    if getattr(msg, 'photo', None): return "Photo"
    if getattr(msg, 'audio', None): return "Audio"
    if getattr(msg, 'text', None): return "Text"
    return None

async def apply_caption_replacements(user_id: int, caption: str) -> str:
    if not caption:
        return ""
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
    if prefix:
        caption = f"{prefix}\n\n{caption}"
    if suffix:
        caption = f"{caption}\n\n{suffix}"
    return caption.strip()

# --- COMMANDS ---

@Client.on_message(filters.command(["cancel"]) & filters.private)
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await message.reply_text("🛑 <b>चालू प्रोसेस तुरंत रोक दी गई है!</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["clearchat"]) & filters.private)
async def reset_my_dump_chat(client: Client, message: Message):
    await db.del_dump_chat(message.from_user.id)
    batch_temp.USER_DEFAULT_TOPIC.pop(message.from_user.id, None)
    batch_temp.USER_TOPIC_MAP[message.from_user.id] = {}
    await message.reply_text("✅ <b>ग्रुप फॉरवर्डिंग बंद कर दी गई है! अब सारी फाइलें पर्सनल चैट में आएँगी।</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["setchat"]) & filters.private)
async def set_dump_chat_command(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("<code>/setchat &lt;group_id&gt;</code>\nया\n<code>/clearchat</code>", parse_mode=enums.ParseMode.HTML)
    if args[1].lower() == "clear":
        await db.del_dump_chat(message.from_user.id)
        return await message.reply_text("✅ ग्रुप फॉरवर्डिंग हटा दी गई।")
    try:
        chat_id = int(args[1])
        await db.set_dump_chat(message.from_user.id, chat_id)
        await message.reply_text(f"✅ <b>टारगेट ग्रुप सेट:</b> <code>{chat_id}</code>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ त्रुटि: {e}")

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
        await message.reply_text(f"✅ <b>डिफ़ॉल्ट टॉपिक सेट:</b> <code>{t_id}</code>", parse_mode=enums.ParseMode.HTML)
    except ValueError:
        await message.reply_text("❌ कृपया सही संख्या (ID) डालें।")

@Client.on_message(filters.command(["map_topic"]) & filters.private)
async def map_topic_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 3:
        return await message.reply_text("<code>/map_topic &lt;source_topic_id&gt; &lt;your_topic_id&gt;</code>", parse_mode=enums.ParseMode.HTML)
    try:
        s_id = int(args[1])
        t_id = int(args[2])
        if message.from_user.id not in batch_temp.USER_TOPIC_MAP:
            batch_temp.USER_TOPIC_MAP[message.from_user.id] = {}
        batch_temp.USER_TOPIC_MAP[message.from_user.id][s_id] = t_id
        await message.reply_text(f"✅ <b>मैपिंग सेव:</b> स्रोत <code>{s_id}</code> ➔ आपका टॉपिक <code>{t_id}</code>", parse_mode=enums.ParseMode.HTML)
    except ValueError:
        await message.reply_text("❌ केवल संख्या डालें।")

@Client.on_message(filters.command(["clean_ads"]) & filters.private)
async def toggle_clean_ads(client: Client, message: Message):
    c = batch_temp.USER_CLEAN_ADS.get(message.from_user.id, False)
    batch_temp.USER_CLEAN_ADS[message.from_user.id] = not c
    await message.reply_text(f"Ad Cleaner: {'🟢 On' if not c else '🔴 Off'}")

# --- MAIN FAST FORWARD HANDLER ---

@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" not in message.text:
        return

    if batch_temp.IS_BATCH.get(message.from_user.id) is False:
        return await message.reply_text("⚠️ <b>पहले से एक टास्क चालू है। कृपया प्रतीक्षा करें या /cancel भेजें।</b>", parse_mode=enums.ParseMode.HTML)

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

    # User Account Login Connect
    acc = None
    if is_private_link:
        user_data = await db.get_session(message.from_user.id)
        if not user_data:
            batch_temp.IS_BATCH[message.from_user.id] = True
            return await message.reply("🔒 <b>प्राइवेट लिंक के लिए पहले /login करें।</b>", parse_mode=enums.ParseMode.HTML)
        try:
            acc = Client("fast_user_acc", session_string=user_data, api_hash=API_HASH, api_id=API_ID, in_memory=True)
            await acc.connect()
        except Exception as e:
            batch_temp.IS_BATCH[message.from_user.id] = True
            return await message.reply(f"❌ लॉगिन त्रुटि: {e}")

    chat_target = int("-100" + datas[4]) if is_private_link else datas[3]

    for msgid in range(fromID, toID + 1):
        if batch_temp.IS_BATCH.get(message.from_user.id):
            await message.reply_text("🛑 <b>टास्क रोक दिया गया।</b>", parse_mode=enums.ParseMode.HTML)
            break

        try:
            # 1. मैसेज प्राप्त करना
            sender_app = acc if is_private_link else client
            try:
                msg: Message = await sender_app.get_messages(chat_target, msgid)
            except FloodWait as fw:
                await asyncio.sleep(fw.value)
                msg: Message = await sender_app.get_messages(chat_target, msgid)

            if not msg or msg.empty or not get_message_type(msg):
                continue

            # 2. ऑटो टॉपिक पहचानना
            source_topic = getattr(msg, "message_thread_id", None)
            target_topic = batch_temp.USER_TOPIC_MAP.get(message.from_user.id, {}).get(source_topic)
            if not target_topic:
                target_topic = batch_temp.USER_DEFAULT_TOPIC.get(message.from_user.id, None)

            # कैप्शन फ़िल्टर
            caption = await apply_caption_replacements(message.from_user.id, msg.caption or "")

            # 3. डायरेक्ट सर्वर-साइड सुपर-फास्ट क्लोनिंग (बिना डाउनलोड/अपलोड)
            kw = {
                "chat_id": destination_chat,
                "from_chat_id": chat_target,
                "message_id": msgid,
            }
            if caption:
                kw["caption"] = caption
            if target_topic and destination_chat != message.chat.id:
                kw["message_thread_id"] = target_topic

            copied_successfully = False

            # प्रयास 1: यूजर अकाउंट से डायरेक्ट कॉपी (1 सेकंड स्पीड)
            if acc:
                try:
                    await acc.copy_message(**kw)
                    copied_successfully = True
                except Exception as e:
                    logger.warning(f"Acc fast copy failed: {e}")

            # प्रयास 2: बॉट क्लाइंट से डायरेक्ट कॉपी
            if not copied_successfully:
                try:
                    await client.copy_message(**kw)
                    copied_successfully = True
                except Exception as e:
                    logger.warning(f"Bot fast copy failed: {e}")

            # 4. फ़ॉलबैक: केवल तभी डाउनलोड होगा जब चैनल में कॉपी पूरी तरह ब्लॉक हो
            if not copied_successfully:
                temp_dir = f"downloads/{message.id}_{msgid}"
                os.makedirs(temp_dir, exist_ok=True)
                try:
                    file = await sender_app.download_media(msg, file_name=f"{temp_dir}/")
                    send_kw = {"chat_id": destination_chat, "caption": caption}
                    if target_topic and destination_chat != message.chat.id:
                        send_kw["message_thread_id"] = target_topic

                    msg_t = get_message_type(msg)
                    if msg_t == "Video":
                        await client.send_video(**send_kw, video=file)
                    elif msg_t == "Document":
                        await client.send_document(**send_kw, document=file)
                    elif msg_t == "Photo":
                        await client.send_photo(**send_kw, photo=file)
                    elif msg_t == "Audio":
                        await client.send_audio(**send_kw, audio=file)
                    elif msg_t == "Text":
                        await client.send_message(chat_id=destination_chat, text=msg.text, message_thread_id=target_topic)
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
    await message.reply_text("✅ <b>फ़ॉरवर्डिंग सफलतापूर्वक पूरी हो गई!</b>", parse_mode=enums.ParseMode.HTML)
