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
    "🥴", "😍", "🐳", "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡", "🍌",
    "🏆", "💔", "🤨", "😐", "🍓", "🍾", "💋", "🖕", "😈", "😴",
    "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈", "😇", "😨", "🤝",
    "✍", "🤗", "🫡", "🎅", "🎄", "☃", "💅", "🤪", "🗿", "🆒",
    "💘", "🙉", "🦄", "😘", "💊", "🙊", "😎", "👾", "🤷‍♂️", "🤷‍♀️",
    "😡"
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
<blockquote><b>1️⃣ Public Channels (No Login Required)</b></blockquote>
• Forward or send the post link directly.
• Compatible with any public channel or group.
• <i>Example:</i> <code>https://t.me/channel/123</code>

<blockquote><b>2️⃣ Private/Restricted Channels (Login Required)</b></blockquote>
• Use <code>/login</code> to connect your account.
• Send private links (e.g., <code>t.me/c/123...</code>).

<blockquote><b>3️⃣ Custom Caption & Clean Commands</b></blockquote>
• <code>/replace 'पुराना' 'नया'</code> - शब्द या वाक्य बदलें
• <code>/clear_replace</code> - सभी रिप्लेसमेंट साफ़ करें
• <code>/prefix 'आपका टेक्स्ट'</code> - कैप्शन के ऊपर नाम जोड़ें
• <code>/suffix 'आपका टेक्स्ट'</code> - कैप्शन के नीचे नाम जोड़ें
• <code>/clean_ads</code> - अन्य चैनलों के लिंक व प्रोमो ऑटो-डिलीट करें

<blockquote><b>4️⃣ Dump Chat Commands</b></blockquote>
• <code>/setchat -100xxxxxxxxxx</code> - चैनल में ऑटो-फॉरवर्ड सेट करें
• <code>/clearchat</code> - चैनल फॉरवर्डिंग बंद करके वापस DM में फ़ाइलें मंगाएं

<blockquote><b>🛑 Free User Limitations:</b></blockquote>
• <b>Daily Quota:</b> 10 Files / 24 Hours
• <b>File Size Cap:</b> 2GB Maximum
"""
    ABOUT_TXT = """<b>ℹ️ About This Bot</b>
<blockquote><b>╭────[ 🧩 Technical Stack ]────⍟</b>
<b>├⍟ 🤖 Bot Name : <a href=http://t.me/THEUPDATEDGUYS_Bot>Save Content</a></b>
<b>├⍟ 👨‍💻 Developer : <a href=https://t.me/iamtghelp>iamtghelp</a></b>
<b>├⍟ 📚 Library : <a href='https://docs.pyrogram.org/'>Pyrogram Async</a></b>
<b>├⍟ 🐍 Language : <a href='https://www.python.org/'>Python 3.11+</a></b>
<b>├⍟ 🗄 Database : <a href='https://www.mongodb.com/'>MongoDB Atlas Cluster</a></b>
<b>├⍟ 📡 Hosting : Dedicated High-Speed VPS</b>
<b>╰───────────────⍟</b></blockquote>
"""
    PREMIUM_TEXT = """<b>💎 Premium Membership Plans</b>
<b>Unlock Unlimited Access & Advanced Features!</b>
<blockquote><b>✨ Key Benefits:</b>
<b>♾️ Unlimited Daily Downloads</b>
<b>📂 Support for 4GB+ File Sizes</b>
<b>⚡ Instant Processing (Zero Delay)</b>
<b>🖼 Customizable Thumbnails</b>
<b>📝 Personalized Captions</b>
<b>🛂 24/7 Priority Support</b></blockquote>
<blockquote><b>💳 Pricing Options:</b></blockquote>
• <b>1 Month Plan:</b> ₹50 / $1 (Billed Monthly)
• <b>3 Month Plan:</b> ₹120 / $2.5 (Save 20%)
• <b>Lifetime Access:</b> ₹200 / $4 (One-Time Payment)
<blockquote><b>👇 Secure Payment:</b></blockquote>
<b>💸 UPI ID:</b> <code>{}</code>
<b>📸 QR Code:</b> <a href='{}'>Scan to Pay</a>
<i>After Payment: Send Screenshot to Admin for Instant Activation.</i>
"""
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
    LIMIT_REACHED = """<b>🚫 Daily Limit Exceeded</b>
<b>Your 10 free saves for today have been used.</b>
<i>Quota resets automatically after 24 hours from first download.</i>
<blockquote><b>🔓 Upgrade to Premium for Unlimited Access!</b></blockquote>
Remove all restrictions and enjoy seamless downloading.
"""
    SIZE_LIMIT = """<b>⚠️ File Size Exceeded</b>
<b>Free tier limited to 2GB per file.</b>
<blockquote><b>🔓 Upgrade to Premium</b></blockquote>
Download files up to 4GB and beyond with no limits!
"""

def humanbytes(size):
    if not size:
        return "0B"
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
    if batch_temp.IS_BATCH.get(message.from_user.id):
        raise Exception("Cancelled")
    if not hasattr(progress, "cache"):
        progress.cache = {}
   
    now = time.time()
    task_id = f"{message.id}{type}"
    last_time = progress.cache.get(task_id, 0)
   
    if not hasattr(progress, "start_time"):
        progress.start_time = {}
    if task_id not in progress.start_time:
        progress.start_time[task_id] = now
       
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

# --- CUSTOM COMMANDS ---
@Client.on_message(filters.command(["replace", "r"]) & filters.private)
async def easy_replace_command(client: Client, message: Message):
    try:
        args = shlex.split(message.text)
        if len(args) < 3:
            return await message.reply_text(
                "<b>📌 Replace Command Usage:</b>\n"
                "<code>/replace 'Old Word' 'New Word'</code>",
                parse_mode=enums.ParseMode.HTML
            )
        old_val = args[1]
        new_val = args[2]
        await db.set_replace_words(message.from_user.id, {old_val: new_val})
        await message.reply_text(
            f"<b>✅ Replacement Saved:</b>\n<code>{old_val}</code> ➔ <code>{new_val}</code>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command(["clear_replace", "reset_repl"]) & filters.private)
async def clear_replace_command(client: Client, message: Message):
    try:
        await db.col.update_one({'id': message.from_user.id}, {'$set': {'replace_words': {}, 'delete_words': []}})
        await message.reply_text("<b>🧹 सभी रिप्लेसमेंट साफ़ कर दिए गए हैं।</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command(["clean_ads"]) & filters.private)
async def toggle_clean_ads(client: Client, message: Message):
    current = batch_temp.USER_CLEAN_ADS.get(message.from_user.id, False)
    batch_temp.USER_CLEAN_ADS[message.from_user.id] = not current
    status = "🟢 Enabled (विज्ञापनों को साफ़ किया जाएगा)" if not current else "🔴 Disabled"
    await message.reply_text(f"<b>Ad/Link Cleaner:</b> {status}", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["prefix"]) & filters.private)
async def set_prefix(client: Client, message: Message):
    try:
        args = shlex.split(message.text)
        if len(args) < 2:
            batch_temp.USER_PREFIX[message.from_user.id] = ""
            return await message.reply_text("<b>Prefix हटा दिया गया है।</b>", parse_mode=enums.ParseMode.HTML)
        batch_temp.USER_PREFIX[message.from_user.id] = args[1]
        await message.reply_text(f"<b>✅ Prefix सेट हुआ:</b>\n<code>{args[1]}</code>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command(["suffix"]) & filters.private)
async def set_suffix(client: Client, message: Message):
    try:
        args = shlex.split(message.text)
        if len(args) < 2:
            batch_temp.USER_SUFFIX[message.from_user.id] = ""
            return await message.reply_text("<b>Suffix हटा दिया गया है।</b>", parse_mode=enums.ParseMode.HTML)
        batch_temp.USER_SUFFIX[message.from_user.id] = args[1]
        await message.reply_text(f"<b>✅ Suffix सेट हुआ:</b>\n<code>{args[1]}</code>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# --- DUMP CHAT & CLEAR COMMANDS ---
@Client.on_message(filters.command(["setchat"]) & filters.private)
async def set_dump_chat_command(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text(
            "<b>🗑 Set Dump Chat</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/setchat &lt;chat_id&gt;</code> ➔ Set forward destination\n"
            "<code>/clearchat</code> ➔ Remove dump chat\n\n"
            "<i>Example:</i> <code>/setchat -1001234567890</code>",
            parse_mode=enums.ParseMode.HTML
        )
    target = args[1].strip()
    if target.lower() == "clear":
        await db.del_dump_chat(message.from_user.id)
        return await message.reply_text("<b>✅ Dump Chat साफ़ कर दी गई है। अब सभी फ़ाइलें इसी चैट (DM) में आएँगी।</b>", parse_mode=enums.ParseMode.HTML)
    
    try:
        chat_id = int(target)
        chat = await client.get_chat(chat_id)
        await db.set_dump_chat(message.from_user.id, chat_id)
        await message.reply_text(
            f"<b>✅ Dump Chat Set Successfully</b>\n\n"
            f"<b>Forward To:</b> <code>{chat_id}</code>\n"
            f"<b>Title:</b> <code>{chat.title}</code>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(f"<b>❌ Unable to Access Chat</b>\n<code>{e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["clearchat", "reset_chat"]) & filters.private)
async def reset_my_dump_chat(client: Client, message: Message):
    try:
        await db.del_dump_chat(message.from_user.id)
        await message.reply_text(
            "<b>✅ चैनल फॉरवर्डिंग पूरी तरह बंद कर दी गई है!</b>\n\n<i>अब से सभी वीडियो और पीडीएफ सिर्फ आपके इसी बॉट (DM) में आएँगे।</i>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass
    apis = ["https://api.waifu.pics/sfw/waifu", "https://nekos.life/api/v2/img/waifu"]
    api_url = random.choice(apis)
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        photo_url = response.json()["url"]
    except Exception as e:
        logger.error(f"Failed to fetch image from API: {e}")
        photo_url = "https://i.postimg.cc/kX9tjGXP/16.png"
    buttons = [
        [
            InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium"),
            InlineKeyboardButton("🆘 Help & Guide", callback_data="help_btn")
        ],
        [
            InlineKeyboardButton("⚙️ Settings Panel", callback_data="settings_btn"),
            InlineKeyboardButton("ℹ️ About Bot", callback_data="about_btn")
        ],
        [
            InlineKeyboardButton('📢 Channels', callback_data="channels_info"),
            InlineKeyboardButton('👨‍💻 Developers', callback_data="dev_info")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    bot = await client.get_me()
    await client.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=script.START_TXT.format(message.from_user.mention, bot.username, bot.first_name),
        reply_markup=reply_markup,
        reply_to_message_id=message.id,
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    buttons = [[InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]]
    await client.send_message(
        chat_id=message.chat.id,
        text=script.HELP_TXT,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command(["plan", "myplan", "premium"]))
async def send_plan(client: Client, message: Message):
    buttons = [
        [InlineKeyboardButton("📸 Send Payment Proof", url="https://t.me/iamtghelp")],
        [InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]
    ]
    await client.send_photo(
        chat_id=message.chat.id,
        photo=SUBSCRIPTION,
        caption=script.PREMIUM_TEXT.format(UPI_ID, QR_CODE),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await message.reply_text("❌ Batch Process Cancelled Successfully.")

async def settings_panel(client, callback_query):
    user_id = callback_query.from_user.id
    is_premium = await db.check_premium(user_id)
    badge = "💎 Premium Member" if is_premium else "👤 Standard User"
   
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Command List", callback_data="cmd_list_btn")],
        [InlineKeyboardButton("📊 Usage Stats", callback_data="user_stats_btn")],
        [InlineKeyboardButton("🗑 Dump Chat Settings", callback_data="dump_chat_btn")],
        [InlineKeyboardButton("🖼 Manage Thumbnail", callback_data="thumb_btn")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data="caption_btn")],
        [InlineKeyboardButton("⬅️ Return to Home", callback_data="start_btn")]
    ])
   
    text = f"<b>⚙️ Settings Dashboard</b>\n\n<b>Account Status:</b> {badge}\n<b>User ID:</b> <code>{user_id}</code>\n\n<i>Customize and manage your bot preferences below for an optimized experience:</i>"
   
    await callback_query.edit_message_caption(
        caption=text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" in message.text:
        is_limit_reached = await db.check_limit(message.from_user.id)
        if is_limit_reached:
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade to Premium", callback_data="buy_premium")]])
            return await message.reply_photo(
                photo=SUBSCRIPTION,
                caption=script.LIMIT_REACHED,
                reply_markup=btn,
                parse_mode=enums.ParseMode.HTML
            )
       
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text("<b>⚠️ A Task is Currently Processing.</b>\n<i>Please wait for completion or use /cancel to stop.</i>", parse_mode=enums.ParseMode.HTML)
        
        # Check Dump Chat
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
        is_batch = "https://t.me/b/" in message.text
        is_public_link = not is_private_link and not is_batch

        for msgid in range(fromID, toID + 1):
            if batch_temp.IS_BATCH.get(message.from_user.id):
                break
           
            # --- 1. PUBLIC CHANNEL: FAST COPY ---
            if is_public_link:
                username = datas[3]
                try:
                    orig_msg = await client.get_messages(username, msgid)
                    final_caption = orig_msg.caption or ""
                    
                    if final_caption:
                        final_caption = await apply_caption_replacements(message.from_user.id, final_caption)

                    await client.copy_message(
                        chat_id=destination_chat,
                        from_chat_id=username,
                        message_id=msgid,
                        caption=final_caption
                    )
                    await db.add_traffic(message.from_user.id)
                    await asyncio.sleep(1)
                    continue
                except Exception as e:
                    logger.error(f"Public fast copy fallback: {e}")

            # --- 2. PRIVATE / RESTRICTED CHANNEL ---
            user_data = await db.get_session(message.from_user.id)
            if user_data is None:
                await message.reply(
                    "<b>🔒 Authentication Required</b>\n\n"
                    "<i>Access to this content requires login.</i>\n"
                    "<i>Use /login to securely authorize your account.</i>",
                    parse_mode=enums.ParseMode.HTML
                )
                batch_temp.IS_BATCH[message.from_user.id] = True
                return
            try:
                acc = Client(
                    "saverestricted",
                    session_string=user_data,
                    api_hash=API_HASH,
                    api_id=API_ID,
                    in_memory=True,
                    max_concurrent_transmissions=10
                )
                await acc.connect()
            except Exception as e:
                batch_temp.IS_BATCH[message.from_user.id] = True
                return await message.reply(f"<b>❌ Authentication Failed</b>\n\n<i>Your session may have expired. Please /logout and /login again.</i>\n<code>{e}</code>", parse_mode=enums.ParseMode.HTML)
            
            if is_private_link:
                chatid = int("-100" + datas[4])
                await handle_restricted_content(client, acc, message, chatid, msgid, destination_chat)
            elif is_batch:
                username = datas[4]
                await handle_restricted_content(client, acc, message, username, msgid, destination_chat)
            else:
                username = datas[3]
                await handle_restricted_content(client, acc, message, username, msgid, destination_chat)
            await asyncio.sleep(2)
            
        batch_temp.IS_BATCH[message.from_user.id] = True

async def handle_restricted_content(client: Client, acc, message: Message, chat_target, msgid, destination_chat):
    try:
        msg: Message = await acc.get_messages(chat_target, msgid)
    except Exception as e:
        logger.error(f"Error fetching message: {e}")
        return
    if msg.empty:
        return
   
    msg_type = get_message_type(msg)
    if not msg_type:
        return
    file_size = 0
    if msg_type == "Document": file_size = msg.document.file_size
    elif msg_type == "Video": file_size = msg.video.file_size
    elif msg_type == "Audio": file_size = msg.audio.file_size
   
    if file_size > FREE_LIMIT_SIZE:
        if not await db.check_premium(message.from_user.id):
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade to Premium", callback_data="buy_premium")]])
            await client.send_message(
                message.chat.id,
                script.SIZE_LIMIT,
                reply_markup=btn,
                parse_mode=enums.ParseMode.HTML
            )
            return

    # --- TEXT & INDEX MESSAGE PROCESSING (UNIVERSAL LINK REDIRECTION) ---
    if msg_type == "Text":
        try:
            text_content = msg.text or ""
            text_content = await apply_caption_replacements(message.from_user.id, text_content)
            
            if destination_chat != message.chat.id:
                try:
                    dest_chat_obj = await client.get_chat(destination_chat)
                    if dest_chat_obj.username:
                        my_base_link = f"https://t.me/{dest_chat_obj.username}"
                    else:
                        clean_dest_id = str(destination_chat).replace("-100", "")
                        my_base_link = f"https://t.me/c/{clean_dest_id}"

                    # 1. Plain Text URLs replacement
                    text_content = re.sub(
                        r'https?://t\.me/(?:c/\d+|[a-zA-Z0-9_]+)/(\d+)',
                        rf'{my_base_link}/\1',
                        text_content
                    )
                    text_content = re.sub(
                        r'https?://t\.me/(?:joinchat/|\+)?([a-zA-Z0-9_]+)',
                        my_base_link,
                        text_content
                    )

                    # 2. Hidden Blue Hyperlinks replacement
                    if msg.entities:
                        for entity in msg.entities:
                            if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                                post_match = re.search(r'/(\d+)$', entity.url)
                                if post_match:
                                    post_number = post_match.group(1)
                                    entity.url = f"{my_base_link}/{post_number}"
                                else:
                                    entity.url = my_base_link

                except Exception as universal_err:
                    logger.error(f"Universal Link Replace Error: {universal_err}")

            await client.send_message(
                destination_chat, 
                text_content, 
                entities=msg.entities, 
                parse_mode=None
            )
            return
        except Exception as e:
            logger.error(f"Error sending text content: {e}")
            return

    await db.add_traffic(message.from_user.id)
    smsg = await client.send_message(message.chat.id, '<b>⬇️ Starting Download...</b>', reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
   
    temp_dir = f"downloads/{message.id}"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    try:
        asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, message.chat.id))
       
        file = await acc.download_media(
            msg,
            file_name=f"{temp_dir}/",
            progress=progress,
            progress_args=[message, "down"]
        )
       
        if os.path.exists(f'{message.id}downstatus.txt'): os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        if batch_temp.IS_BATCH.get(message.from_user.id) or "Cancelled" in str(e):
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            return await smsg.edit("❌ **Task Cancelled**")
        return await smsg.delete()

    try:
        asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, message.chat.id))
       
        ph_path = None
        thumb_id = await db.get_thumbnail(message.from_user.id)
       
        if thumb_id:
            try:
                ph_path = await client.download_media(thumb_id, file_name=f"{temp_dir}/custom_thumb.jpg")
            except Exception as e:
                logger.error(f"Failed to download custom thumb: {e}")
        if not ph_path:
            try:
                if msg_type == "Video" and msg.video.thumbs:
                    ph_path = await acc.download_media(msg.video.thumbs[0].file_id, file_name=f"{temp_dir}/thumb.jpg")
                elif msg_type == "Document" and msg.document.thumbs:
                    ph_path = await acc.download_media(msg.document.thumbs[0].file_id, file_name=f"{temp_dir}/thumb.jpg")
            except:
                pass

        custom_caption = await db.get_caption(message.from_user.id)
        if custom_caption:
            final_caption = custom_caption.format(filename=file.split("/")[-1], size=humanbytes(file_size))
        else:
            final_caption = script.CAPTION.format(file_name=file.split("/")[-1])
            if msg.caption:
                final_caption += f"\n\n{msg.caption}"

        final_caption = await apply_caption_replacements(message.from_user.id, final_caption)

        if msg_type == "Document":
            await client.send_document(destination_chat, file, thumb=ph_path, caption=final_caption, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Video":
            await client.send_video(destination_chat, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=final_caption, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Audio":
            await client.send_audio(destination_chat, file, thumb=ph_path, caption=final_caption, progress=progress, progress_args=[message, "up"])
        elif msg_type == "Photo":
            await client.send_photo(destination_chat, file, caption=final_caption)
       
    except Exception as e:
         await smsg.edit(f"Upload Failed: {e}")
    if os.path.exists(f'{message.id}upstatus.txt'): os.remove(f'{message.id}upstatus.txt')
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    await client.delete_messages(message.chat.id, [smsg.id])

@Client.on_callback_query()
async def button_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    message = callback_query.message
    if not message: return
    if data == "dev_info":
        await callback_query.answer(
            text=dev_text,
            show_alert=True
        )
    elif data == "channels_info":
        await callback_query.answer(
            text=channels_text,
            show_alert=True
        )
    elif data == "settings_btn":
        await settings_panel(client, callback_query)
    elif data == "buy_premium":
        buttons = [
            [InlineKeyboardButton("📸 Send Payment Proof", url="https://t.me/iamtghelp")],
            [InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]
        ]
        await client.edit_message_media(
            chat_id=message.chat.id,
            message_id=message.id,
            media=InputMediaPhoto(
                media=SUBSCRIPTION,
                caption=script.PREMIUM_TEXT.format(callback_query.from_user.mention, UPI_ID, QR_CODE)
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "help_btn":
        buttons = [[InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]]
        await client.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.id,
            caption=script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    elif data == "about_btn":
        buttons = [[InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]]
        await client.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.id,
            caption=script.ABOUT_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    elif data == "start_btn":
        bot = await client.get_me()
        apis = ["https://api.waifu.pics/sfw/waifu", "https://nekos.life/api/v2/img/waifu"]
        api_url = random.choice(apis)
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            photo_url = response.json()["url"]
        except Exception as e:
            logger.error(f"Failed to fetch image from API: {e}")
            photo_url = "https://i.postimg.cc/cC7txyhz/15.png"
        buttons = [
            [
                InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium"),
                InlineKeyboardButton("🆘 Help & Guide", callback_data="help_btn")
            ],
            [
                InlineKeyboardButton("⚙️ Settings Panel", callback_data="settings_btn"),
                InlineKeyboardButton("ℹ️ About Bot", callback_data="about_btn")
            ],
            [
                InlineKeyboardButton('📢 Channels', callback_data="channels_info"),
                InlineKeyboardButton('👨‍💻 Developers', callback_data="dev_info")
            ]
        ]
        await client.edit_message_media(
            chat_id=message.chat.id,
            message_id=message.id,
            media=InputMediaPhoto(
                media=photo_url,
                caption=script.START_TXT.format(callback_query.from_user.mention, bot.username, bot.first_name)
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "close_btn":
        await message.delete()
    elif data in ["cmd_list_btn", "user_stats_btn", "dump_chat_btn", "thumb_btn", "caption_btn"]:
        pass
    await callback_query.answer()
