import motor.motor_asyncio
from typing import Any
from datetime import datetime, timedelta

class MongoDB:
    _instances = {}
    client: Any
    db: Any
    user_data: Any
    channel_data: Any
    broadcast_jobs: Any

    def __new__(cls, uri: str, db_name: str):
        if (uri, db_name) not in cls._instances:
            instance = super().__new__(cls)
            instance.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            instance.db = instance.client[db_name]
            instance.user_data = instance.db["users"]
            instance.channel_data = instance.db["channels"]
            instance.broadcast_jobs = instance.db["broadcast_jobs"]
            instance.access_tokens = instance.db["access_tokens"]  # Enhanced token tracking
            instance.bypass_attempts = instance.db["bypass_attempts"]  # Bypass logging
            instance.bot_config = instance.db["bot_config"]  # Bot configuration
            instance.batch_groups = instance.db["batch_groups"]  # Auto-batch groups
            instance.pending_files = instance.db["pending_files"]  # Files pending grouping
            cls._instances[(uri, db_name)] = instance
        return cls._instances[(uri, db_name)]

    # =====================================================
    # CHANNEL MANAGEMENT
    # =====================================================

    async def set_channels(self, channels: list[int]):
        await self.user_data.update_one(
            {"_id": 1},
            {"$set": {"channels": channels}},
            upsert=True
        )

    async def get_channels(self) -> list[int]:
        data = await self.user_data.find_one({"_id": 1})
        return data.get("channels", []) if data else []

    async def add_channel(self, channel_id: int):
        await self.user_data.update_one(
            {"_id": 1},
            {"$addToSet": {"channels": channel_id}},
            upsert=True
        )

    async def remove_channel(self, channel_id: int):
        await self.user_data.update_one(
            {"_id": 1},
            {"$pull": {"channels": channel_id}}
        )

    async def total_channels(self) -> int:
        data = await self.user_data.find_one({"_id": 1})
        return len(data.get("channels", [])) if data else 0

    # =====================================================
    # DB CHANNEL MANAGEMENT (MULTI-DB)
    # =====================================================

    async def get_db_channels(self) -> list[int]:
        """Get list of configured DB channels"""
        data = await self.bot_config.find_one({"_id": "db_channels"})
        return data.get("value", []) if data else []

    async def add_db_channel(self, channel_id: int):
        """Add a DB channel"""
        await self.bot_config.update_one(
            {"_id": "db_channels"},
            {"$addToSet": {"value": channel_id}},
            upsert=True
        )

    async def remove_db_channel(self, channel_id: int):
        """Remove a DB channel"""
        await self.bot_config.update_one(
            {"_id": "db_channels"},
            {"$pull": {"value": channel_id}}
        )

    async def is_multi_db_enabled(self) -> bool:
        """Check if multi-DB channel system is enabled"""
        return await self.get_bot_config('multi_db_enabled', False)

    async def toggle_multi_db(self) -> bool:
        """Toggle multi-DB system on/off"""
        current = await self.is_multi_db_enabled()
        await self.set_bot_config('multi_db_enabled', not current)
        return not current

    async def get_next_db_channel(self, main_channel_id: int) -> int:
        """Get next DB channel using round-robin distribution"""
        # Check if multi-DB is enabled
        if not await self.is_multi_db_enabled():
            return main_channel_id
        
        extra_channels = await self.get_db_channels()
        
        if not extra_channels:
            # No extra channels, use main
            return main_channel_id
        
        # Combine main + extra channels
        all_channels = [main_channel_id] + extra_channels
        
        # Get current index (stored in bot_config)
        data = await self.bot_config.find_one({"_id": "db_channel_index"})
        current_index = data.get("value", 0) if data else 0
        
        # Select channel
        selected_channel = all_channels[current_index % len(all_channels)]
        
        # Update index for next time
        next_index = (current_index + 1) % len(all_channels)
        await self.bot_config.update_one(
            {"_id": "db_channel_index"},
            {"$set": {"value": next_index}},
            upsert=True
        )
        
        return selected_channel

    # =====================================================
    # ADMIN MANAGEMENT
    # =====================================================

    async def set_admins(self, admins: list[int]):
        await self.user_data.update_one(
            {"_id": 2},
            {"$set": {"admins": admins}},
            upsert=True
        )

    async def get_admins(self) -> list[int]:
        data = await self.user_data.find_one({"_id": 2})
        return data.get("admins", []) if data else []

    # =====================================================
    # USER MANAGEMENT
    # =====================================================

    async def present_user(self, user_id: int) -> bool:
        user = await self.user_data.find_one({'_id': user_id})
        return bool(user)

    async def add_user(self, user_id: int, ban: bool = False):
        await self.user_data.insert_one({'_id': user_id, 'ban': ban})

    async def full_userbase(self) -> list[int]:
        return [doc['_id'] async for doc in self.user_data.find()]

    async def del_user(self, user_id: int):
        await self.user_data.delete_one({'_id': user_id})

    async def ban_user(self, user_id: int):
        await self.user_data.update_one({'_id': user_id}, {'$set': {'ban': True}})

    async def unban_user(self, user_id: int):
        await self.user_data.update_one({'_id': user_id}, {'$set': {'ban': False}})

    async def is_banned(self, user_id: int) -> bool:
        user = await self.user_data.find_one({'_id': user_id})
        return user.get('ban', False) if user else False

    # =====================================================
    # PREMIUM SYSTEM
    # =====================================================

    async def add_premium(self, user_id: int, expire_date=None):
        await self.user_data.update_one(
            {'_id': user_id},
            {"$set": {
                "is_premium": True,
                "premium_expire": expire_date
            }},
            upsert=True
        )

    async def remove_premium(self, user_id: int):
        await self.user_data.update_one(
            {'_id': user_id},
            {"$set": {
                "is_premium": False,
                "premium_expire": None
            }}
        )

    async def is_premium(self, user_id: int) -> bool:
        user = await self.user_data.find_one({'_id': user_id})
        if not user or not user.get("is_premium", False):
            return False
        
        expire_date = user.get("premium_expire")
        if expire_date and datetime.now() > expire_date:
            await self.remove_premium(user_id)
            return False
        
        return True

    async def get_premium_users(self) -> list[int]:
        cursor = self.user_data.find({'is_premium': True})
        return [doc['_id'] async for doc in cursor]

    # =====================================================
    # BROADCAST TTL JOBS
    # =====================================================

    async def add_broadcast_ttl_job(self, chat_id: int, message_id: int, delete_ts: int):
        await self.broadcast_jobs.insert_one({
            'chat_id': chat_id,
            'message_id': message_id,
            'delete_ts': delete_ts
        })

    async def get_due_broadcast_jobs(self, now_ts: int, limit: int = 200):
        cursor = self.broadcast_jobs.find({'delete_ts': {'$lte': now_ts}}).limit(limit)
        return [doc async for doc in cursor]

    async def remove_broadcast_job(self, job_id):
        await self.broadcast_jobs.delete_one({'_id': job_id})

    # =====================================================
    # ENHANCED TOKEN ACCESS SYSTEM + ANTI-BYPASS
    # =====================================================

    async def create_access_token(self, user_id: int, base64_string: str, token: str):
        """Create access token with expiry and one-time use"""
        # Get expiry time from config (default 10 minutes)
        expiry_minutes = await self.get_bot_config('token_expiry_minutes', 10)
        
        await self.access_tokens.insert_one({
            'user_id': user_id,
            'base64': base64_string,
            'token': token,
            'created': datetime.now(),
            'used': False,
            'use_count': 0,
            'click_count': 0,  # Track shortener clicks
            'expires': datetime.now() + timedelta(minutes=expiry_minutes)
        })

    async def verify_access_token(self, user_id: int, token: str, base64_string: str) -> str:
        """
        Enhanced token verification with one-time use
        Returns: OK, BYPASS, INVALID, ALREADY_USED, EXPIRED
        """
        token_data = await self.access_tokens.find_one({
            'user_id': user_id,
            'token': token,
            'base64': base64_string
        })

        if not token_data:
            await self.log_bypass_attempt(user_id, "INVALID_TOKEN")
            return "INVALID"

        # Check if token expired
        if datetime.now() > token_data.get('expires', datetime.now()):
            await self.log_bypass_attempt(user_id, "EXPIRED_TOKEN")
            return "EXPIRED"

        # Check if already used (one-time use)
        if token_data.get('used', False):
            await self.log_bypass_attempt(user_id, "TOKEN_REUSE")
            return "ALREADY_USED"

        # Check minimum solve time (Anti-Bypass)
        bypass_check_enabled = await self.get_bot_config('bypass_check_enabled', True)
        if bypass_check_enabled:
            bypass_timer = await self.get_bot_config('bypass_timer', 60)
            created = token_data.get('created', datetime.now())
            if datetime.now() < created + timedelta(seconds=bypass_timer):
                await self.log_bypass_attempt(user_id, "BYPASS_ATTEMPT")
                return "BYPASS"

        # Mark token as used
        await self.access_tokens.update_one(
            {'_id': token_data['_id']},
            {
                '$set': {'used': True, 'used_at': datetime.now()},
                '$inc': {'use_count': 1}
            }
        )

        return "OK"

    async def clear_access_token(self, user_id: int):
        """Delete all tokens for user"""
        await self.access_tokens.delete_many({'user_id': user_id})

    async def cleanup_old_tokens(self):
        """Remove expired tokens"""
        result = await self.access_tokens.delete_many({
            'expires': {'$lt': datetime.now()}
        })
        return result.deleted_count

    async def increment_token_clicks(self, user_id: int, token: str):
        """Increment click count for a token"""
        await self.access_tokens.update_one(
            {'user_id': user_id, 'token': token},
            {'$inc': {'click_count': 1}}
        )

    async def get_shortener_stats(self):
        """Get shortener click statistics"""
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'total_tokens': {'$sum': 1},
                    'total_clicks': {'$sum': '$click_count'},
                    'total_used': {
                        '$sum': {
                            '$cond': [{'$eq': ['$used', True]}, 1, 0]
                        }
                    },
                    'avg_clicks': {'$avg': '$click_count'}
                }
            }
        ]
        result = await self.access_tokens.aggregate(pipeline).to_list(1)
        return result[0] if result else {
            'total_tokens': 0,
            'total_clicks': 0,
            'total_used': 0,
            'avg_clicks': 0
        }

    async def get_top_clicked_tokens(self, limit: int = 10):
        """Get tokens with most clicks"""
        cursor = self.access_tokens.find().sort('click_count', -1).limit(limit)
        return [doc async for doc in cursor]

    # =====================================================
    # BYPASS ATTEMPT TRACKING & AUTO-BAN
    # =====================================================

    async def log_bypass_attempt(self, user_id: int, attempt_type: str):
        """Log bypass attempt"""
        await self.bypass_attempts.insert_one({
            'user_id': user_id,
            'type': attempt_type,
            'timestamp': datetime.now()
        })

    async def get_bypass_count(self, user_id: int, hours: int = 24) -> int:
        """Get bypass attempt count for user in last X hours"""
        threshold = datetime.now() - timedelta(hours=hours)
        count = await self.bypass_attempts.count_documents({
            'user_id': user_id,
            'timestamp': {'$gte': threshold}
        })
        return count

    async def get_all_bypass_attempts(self, limit: int = 100):
        """Get recent bypass attempts for admin review"""
        cursor = self.bypass_attempts.find().sort('timestamp', -1).limit(limit)
        return [doc async for doc in cursor]

    async def get_bypass_stats(self):
        """Get bypass statistics"""
        pipeline = [
            {
                '$group': {
                    '_id': '$user_id',
                    'count': {'$sum': 1},
                    'types': {'$push': '$type'},
                    'last_attempt': {'$max': '$timestamp'}
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': 50}
        ]
        result = await self.bypass_attempts.aggregate(pipeline).to_list(50)
        return result

    async def clear_bypass_attempts(self, user_id: int):
        """Clear bypass attempts for user"""
        await self.bypass_attempts.delete_many({'user_id': user_id})

    async def check_and_auto_ban(self, user_id: int, max_attempts: int = 5) -> bool:
        """
        Check if user should be auto-banned for bypass attempts
        Returns True if user was banned
        """
        count = await self.get_bypass_count(user_id, hours=24)
        if count >= max_attempts:
            await self.ban_user(user_id)
            return True
        return False

    # =====================================================
    # BOT CONFIGURATION
    # =====================================================

    async def get_bot_config(self, key: str, default=None):
        """Get bot configuration value"""
        config = await self.bot_config.find_one({'_id': key})
        return config.get('value', default) if config else default

    async def set_bot_config(self, key: str, value):
        """Set bot configuration value"""
        await self.bot_config.update_one(
            {'_id': key},
            {'$set': {'value': value, 'updated': datetime.now()}},
            upsert=True
        )

    async def is_credit_system_enabled(self) -> bool:
        """Check if credit system is enabled"""
        return await self.get_bot_config('credit_system_enabled', True)

    async def toggle_credit_system(self, enabled: bool):
        """Enable/disable credit system"""
        await self.set_bot_config('credit_system_enabled', enabled)

    # =====================================================
    # AUTO-BATCH SYSTEM
    # =====================================================

    async def add_pending_file(self, file_id: str, filename: str, base_name: str, quality: str, user_id: int, channel_id: int):
        """Add file to pending batch queue"""
        import secrets
        await self.pending_files.insert_one({
            'file_id': file_id,
            'filename': filename,
            'base_name': base_name,
            'quality': quality,
            'user_id': user_id,
            'channel_id': channel_id,
            'timestamp': datetime.now()
        })

    async def get_pending_files(self, time_window_seconds: int = 30):
        """Get files pending batch grouping within time window"""
        threshold = datetime.now() - timedelta(seconds=time_window_seconds)
        cursor = self.pending_files.find({
            'timestamp': {'$gte': threshold}
        })
        return [doc async for doc in cursor]

    async def create_batch(self, base_name: str, files: list) -> str:
        """Create a batch group from files"""
        import secrets
        batch_id = secrets.token_hex(8)
        
        await self.batch_groups.insert_one({
            'batch_id': batch_id,
            'base_name': base_name,
            'files': files,  # List of {file_id, filename, quality, channel_id}
            'created': datetime.now()
        })
        
        # Remove files from pending
        file_ids = [f['file_id'] for f in files]
        await self.pending_files.delete_many({'file_id': {'$in': file_ids}})
        
        return batch_id

    async def get_batch(self, batch_id: str):
        """Get batch by ID"""
        return await self.batch_groups.find_one({'batch_id': batch_id})

    async def cleanup_old_pending(self, max_age_seconds: int = 120):
        """Remove old pending files"""
        threshold = datetime.now() - timedelta(seconds=max_age_seconds)
        await self.pending_files.delete_many({
            'timestamp': {'$lt': threshold}
        })
