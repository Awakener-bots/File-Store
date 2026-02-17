import motor.motor_asyncio
from typing import Any, Optional
from datetime import datetime, timedelta
import secrets
import string

class EnhancedCreditDB:
    """Enhanced credit database with expiry, referrals, and transactions"""
    _instances = {}
    client: Any
    db: Any
    credit_data: Any
    
    def __new__(cls, uri: str, db_name: str):
        if (uri, db_name) not in cls._instances:
            instance = super().__new__(cls)
            instance.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            instance.db = instance.client[db_name]
            instance.credit_data = instance.db["enhanced_credits"]
            cls._instances[(uri, db_name)] = instance
        return cls._instances[(uri, db_name)]
    
    # =====================================================
    # CREDIT MANAGEMENT
    # =====================================================
    
    async def get_credits(self, user_id: int) -> dict:
        """Get user credit info including balance, expiry, etc."""
        data = await self.credit_data.find_one({"_id": user_id})
        if not data:
            return {
                "balance": 0,
                "expiry": None,
                "total_earned": 0,
                "total_spent": 0,
                "referral_code": None,
                "referred_by": None,
                "referral_count": 0
            }
        return {
            "balance": data.get("balance", 0),
            "expiry": data.get("expiry"),
            "total_earned": data.get("total_earned", 0),
            "total_spent": data.get("total_spent", 0),
            "referral_code": data.get("referral_code"),
            "referred_by": data.get("referred_by"),
            "referral_count": data.get("referral_count", 0)
        }
    
    async def add_credits(self, user_id: int, amount: int, expiry_days: Optional[int] = None, reason: str = "added"):
        """Add credits to user account with optional expiry"""
        expiry = None
        if expiry_days and expiry_days > 0:
            expiry = datetime.now() + timedelta(days=expiry_days)
        
        await self.credit_data.update_one(
            {"_id": user_id},
            {
                "$inc": {"balance": amount, "total_earned": amount},
                "$set": {"expiry": expiry} if expiry else {},
                "$push": {
                    "transactions": {
                        "type": "earned",
                        "amount": amount,
                        "reason": reason,
                        "timestamp": datetime.now()
                    }
                }
            },
            upsert=True
        )
    
    async def use_credit(self, user_id: int):
        """Deduct 1 credit from user account"""
        await self.credit_data.update_one(
            {"_id": user_id},
            {
                "$inc": {"balance": -1, "total_spent": 1},
                "$push": {
                    "transactions": {
                        "type": "spent",
                        "amount": 1,
                        "reason": "file_access",
                        "timestamp": datetime.now()
                    }
                }
            }
        )
    
    async def set_credits(self, user_id: int, amount: int, expiry_days: Optional[int] = None):
        """Set exact credit amount"""
        expiry = None
        if expiry_days and expiry_days > 0:
            expiry = datetime.now() + timedelta(days=expiry_days)
        
        await self.credit_data.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "balance": amount,
                    "expiry": expiry
                },
                "$push": {
                    "transactions": {
                        "type": "set",
                        "amount": amount,
                        "reason": "admin_set",
                        "timestamp": datetime.now()
                    }
                }
            },
            upsert=True
        )
    
    async def reset_credits(self, user_id: int):
        """Reset user credits to 0"""
        await self.credit_data.update_one(
            {"_id": user_id},
            {
                "$set": {"balance": 0},
                "$push": {
                    "transactions": {
                        "type": "reset",
                        "amount": 0,
                        "reason": "admin_reset",
                        "timestamp": datetime.now()
                    }
                }
            }
        )
    
    # =====================================================
    # CREDIT EXPIRY
    # =====================================================
    
    async def check_and_remove_expired(self, user_id: int) -> bool:
        """Check if credits expired and remove them. Returns True if expired."""
        data = await self.credit_data.find_one({"_id": user_id})
        if not data:
            return False
        
        expiry = data.get("expiry")
        if expiry and datetime.now() > expiry:
            await self.credit_data.update_one(
                {"_id": user_id},
                {
                    "$set": {"balance": 0, "expiry": None},
                    "$push": {
                        "transactions": {
                            "type": "expired",
                            "amount": data.get("balance", 0),
                            "reason": "credits_expired",
                            "timestamp": datetime.now()
                        }
                    }
                }
            )
            return True
        return False
    
    async def get_expiring_soon(self, hours: int = 24) -> list:
        """Get users whose credits expire within X hours"""
        threshold = datetime.now() + timedelta(hours=hours)
        cursor = self.credit_data.find({
            "expiry": {"$lte": threshold, "$gte": datetime.now()},
            "balance": {"$gt": 0}
        })
        return [doc async for doc in cursor]
    
    async def cleanup_all_expired(self) -> int:
        """Remove all expired credits. Returns count of users affected."""
        now = datetime.now()
        result = await self.credit_data.update_many(
            {"expiry": {"$lte": now}, "balance": {"$gt": 0}},
            {
                "$set": {"balance": 0, "expiry": None},
                "$push": {
                    "transactions": {
                        "type": "expired",
                        "reason": "auto_cleanup",
                        "timestamp": now
                    }
                }
            }
        )
        return result.modified_count
    
    # =====================================================
    # REFERRAL SYSTEM
    # =====================================================
    
    def _generate_referral_code(self, user_id: int) -> str:
        """Generate unique referral code"""
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return f"REF{user_id % 10000:04d}{random_part}"
    
    async def create_referral_code(self, user_id: int) -> str:
        """Create or get referral code for user"""
        data = await self.credit_data.find_one({"_id": user_id})
        
        if data and data.get("referral_code"):
            return data["referral_code"]
        
        code = self._generate_referral_code(user_id)
        await self.credit_data.update_one(
            {"_id": user_id},
            {"$set": {"referral_code": code}},
            upsert=True
        )
        return code
    
    async def apply_referral(self, new_user_id: int, referral_code: str) -> Optional[int]:
        """Apply referral code to new user. Returns referrer ID if successful."""
        # Find referrer by code
        referrer = await self.credit_data.find_one({"referral_code": referral_code})
        if not referrer:
            return None
        
        referrer_id = referrer["_id"]
        
        # Check if user already has a referrer
        new_user_data = await self.credit_data.find_one({"_id": new_user_id})
        if new_user_data and new_user_data.get("referred_by"):
            return None  # Already referred
        
        # Apply referral
        await self.credit_data.update_one(
            {"_id": new_user_id},
            {"$set": {"referred_by": referrer_id}},
            upsert=True
        )
        
        return referrer_id
    
    async def reward_referral(self, referrer_id: int, referred_id: int, reward_amount: int, expiry_days: Optional[int] = None):
        """Give credits to referrer for successful referral"""
        expiry = None
        if expiry_days and expiry_days > 0:
            expiry = datetime.now() + timedelta(days=expiry_days)
        
        await self.credit_data.update_one(
            {"_id": referrer_id},
            {
                "$inc": {"balance": reward_amount, "total_earned": reward_amount, "referral_count": 1},
                "$set": {"expiry": expiry} if expiry else {},
                "$push": {
                    "transactions": {
                        "type": "referral_reward",
                        "amount": reward_amount,
                        "reason": f"referred_user_{referred_id}",
                        "timestamp": datetime.now()
                    }
                }
            }
        )
    
    async def get_referral_stats(self, user_id: int) -> dict:
        """Get referral statistics for user"""
        data = await self.credit_data.find_one({"_id": user_id})
        if not data:
            return {"referral_code": None, "referral_count": 0, "referral_earnings": 0}
        
        # Calculate earnings from referrals
        transactions = data.get("transactions", [])
        referral_earnings = sum(
            t.get("amount", 0) for t in transactions 
            if t.get("type") == "referral_reward"
        )
        
        return {
            "referral_code": data.get("referral_code"),
            "referral_count": data.get("referral_count", 0),
            "referral_earnings": referral_earnings
        }
    
    # =====================================================
    # TRANSACTIONS
    # =====================================================
    
    async def get_transactions(self, user_id: int, limit: int = 10) -> list:
        """Get user's recent transactions"""
        data = await self.credit_data.find_one({"_id": user_id})
        if not data:
            return []
        
        transactions = data.get("transactions", [])
        # Return last N transactions
        return transactions[-limit:][::-1]  # Reverse to show newest first
    
    async def add_transaction(self, user_id: int, trans_type: str, amount: int, reason: str):
        """Add a transaction record"""
        await self.credit_data.update_one(
            {"_id": user_id},
            {
                "$push": {
                    "transactions": {
                        "type": trans_type,
                        "amount": amount,
                        "reason": reason,
                        "timestamp": datetime.now()
                    }
                }
            },
            upsert=True
        )
    
    # =====================================================
    # ADMIN FUNCTIONS
    # =====================================================
    
    async def get_all_users_with_credits(self) -> list:
        """Get all users who have credits"""
        cursor = self.credit_data.find({"balance": {"$gt": 0}})
        return [doc async for doc in cursor]
    
    async def get_credit_statistics(self) -> dict:
        """Get overall credit statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_users": {"$sum": 1},
                    "total_balance": {"$sum": "$balance"},
                    "total_earned": {"$sum": "$total_earned"},
                    "total_spent": {"$sum": "$total_spent"},
                    "total_referrals": {"$sum": "$referral_count"}
                }
            }
        ]
        
        result = await self.credit_data.aggregate(pipeline).to_list(1)
        if not result:
            return {
                "total_users": 0,
                "total_balance": 0,
                "total_earned": 0,
                "total_spent": 0,
                "total_referrals": 0
            }
        
        return result[0]
