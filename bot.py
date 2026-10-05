cat << 'EOF' > bot.py
import asyncio
import datetime
import sys
import os
from datetime import timezone, timedelta
from pyrogram import Client, filters, enums
from pyrogram.types import Message, BotCommand
from pyrogram.errors import FloodWait, RPCError
from config import API_ID, API_HASH, BOT_TOKEN, LOG_CHANNEL, ADMINS, OWNER_ID
from database.db import db
from logger import LOGGER

try:
    from keep_alive import keep_alive
except ImportError:
    keep_alive = None

logger = LOGGER(__name__)
IST = timezone(timedelta(hours=5, minutes=30))
USER_CACHE = set()

# सभी एडमिन्स और ओनर को अनुमति
SUDO_USERS = list(set([OWNER_ID, 7951185287, 7732591949, 5886149022] + (ADMINS if isinstance(ADMINS, list) else [])))

LOGO = r"""
  ██████╗  ██╗  ██╗  █████╗  ███╗   ██╗ ██████╗   █████╗  ██╗      
  ██╔══██╗ ██║  ██║ ██╔══██╗ ████╗  ██║ ██╔══██╗ ██╔══██╗ ██║      
  ██║  ██║ ███████║ ███████║ ██╔██╗ ██║ ██████╔╝ ███████║ ██║      
  ██║  ██║ ██╔══██║ ██╔══██║ ██║╚██╗██║ ██╔═══╝  ██╔══██║ ██║      
  ██████╔╝ ██║  ██║ ██║  ██║ ██║ ╚████║ ██║      ██║  ██║ ███████
    𝙱𝙾𝚃 𝚆𝙾𝚁𝙺𝙸𝙽𝙶 𝙿𝚁𝙾𝙿𝙴𝚁𝙻𝚈....
"""

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Rexbots_Login_Bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="Rexbots"),
            workers=50,
            sleep_threshold=15,
            max_concurrent_transmissions=15,
            ipv6=False,
            in_memory=True,
        )
        self._keep_alive_started = False

    async def start(self):
        print(LOGO)

        if keep_alive and not self._keep_alive_started:
            try:
                loop = asyncio.get_running_loop()
                try:
                    keep_alive(loop)
                except TypeError:
                    keep_alive()
                self._keep_alive_started = True
                logger.info("Keep-alive server started.")
            except Exception as e:
                logger.warning(f"Keep-alive failed: {e}")

        await super().start()

        me = await self.get_me()

        try:
            user_count = await db.total_users_count()
            logger.info(f"MongoDB Connected: {user_count} users found.")
        except Exception as e:
            logger.error(f"DB stats failed: {e}")
            user_count = "Unknown"

        now = datetime.datetime.now(IST)
        startup_text = (
            f"<b><i>🤖 Bot Successfully Started ♻️</i></b>\n\n"
            f"<b>Bot:</b> @{me.username}\n"
            f"<b>Time:</b> <code>{now.strftime('%I:%M %p')} IST</code>"
        )

        try:
            await self.send_message(LOG_CHANNEL, startup_text)
            logger.info("Startup log sent.")
        except Exception as e:
            logger.warning(f"Startup log skipped (Check bot admin rights in log channel): {e}")

        try:
            await self.set_bot_commands_list()
        except Exception:
            pass

    async def stop(self, *args):
        await asyncio.shield(super().stop())
        logger.info("Bot stopped cleanly")

    async def set_bot_commands_list(self):
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help"),
            BotCommand("cancel", "Cancel current action"),
            BotCommand("setchat", "Set target chat"),
        ]
        await self.set_bot_commands(commands)

BotInstance = Bot()

@BotInstance.on_message(filters.private & filters.incoming, group=-2)
async def owner_only_guard(bot: Client, message: Message):
    if message.from_user.id not in SUDO_USERS:
        await message.reply_text(
            "<b>⚠️ एक्सेस वर्जित (Access Denied)</b>\n\n"
            "यह बॉट सुरक्षित है।",
            parse_mode=enums.ParseMode.HTML
        )
        message.stop_propagation()

if __name__ == "__main__":
    BotInstance.run()
EOF
