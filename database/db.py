import motor.motor_asyncio
import datetime
from config import DB_NAME, DB_URI
from logger import LOGGER

logger = LOGGER(__name__)

class Database:
   
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            session = None,
            daily_usage = 0,
            limit_reset_time = None,
            is_premium = True # नए जुड़ने वाले सभी यूजर्स को डिफ़ॉल्ट प्रीमियम बना दिया
        )
   
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
        logger.info(f"New user added to DB: {id} - {name}")
   
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
   
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})
        logger.info(f"User deleted from DB: {user_id}")

    async def set_session(self, id, session):
        await self.col.update_one({'id': int(id)}, {'$set': {'session': session}})

    async def get_session(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('session')

    # Caption Support
    async def set_caption(self, id, caption):
        await self.col.update_one({'id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('caption', None)

    async def del_caption(self, id):
        await self.col.update_one({'id': int(id)}, {'$unset': {'caption': ""}})

    # Thumbnail Support
    async def set_thumbnail(self, id, thumbnail):
        await self.col.update_one({'id': int(id)}, {'$set': {'thumbnail': thumbnail}})

    async def get_thumbnail(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('thumbnail', None)

    async def del_thumbnail(self, id):
        await self.col.update_one({'id': int(id)}, {'$unset': {'thumbnail': ""}})

    # Premium Support
    async def add_premium(self, id, expiry_date):
        await self.col.update_one({'id': int(id)}, {
            '$set': {
                'is_premium': True,
                'premium_expiry': expiry_date,
                'daily_usage': 0,
                'limit_reset_time': None
            }
        })
        logger.info(f"User {id} granted premium until {expiry_date}")

    async def remove_premium(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'is_premium': False, 'premium_expiry': None}})
        logger.info(f"User {id} removed from premium")

    async def check_premium(self, id):
        # हर यूजर को प्रीमियम दिखाने के लिए हमेशा True जैसा रिस्पॉन्स
        return True 

    async def get_premium_users(self):
        return self.col.find({'is_premium': True})

    # Ban Support
    async def ban_user(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'is_banned': True}})
        logger.warning(f"User banned: {id}")

    async def unban_user(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'is_banned': False}})
        logger.info(f"User unbanned: {id}")

    async def is_banned(self, id):
        user = await self.col.find_one({'id': int(id)})
        if not user: return False
        return user.get('is_banned', False)

    # --------------------------------------------------------
    # FIXED: No More Limits
    # --------------------------------------------------------
    async def check_limit(self, id):
        """
        हमेशा False रिटर्न करेगा ताकि लिमिट का एरर कभी न आए।
        """
        return False # यहाँ बदलाव किया गया है

    async def add_traffic(self, id):
        """
        ट्रैफिक काउंट करने की अब ज़रूरत नहीं है।
        """
        pass # अब कोई लिमिट नहीं बढ़ेगी

db = Database(DB_URI, DB_NAME)
