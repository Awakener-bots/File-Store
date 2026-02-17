import json
from motor.motor_asyncio import AsyncIOMotorClient

# Load Mongo credentials from setup.json
with open("setup.json", "r") as f:
    data = json.load(f)

config = data[0]  # because setup.json is a list

MONGO_URI = config["db_uri"]
DB_NAME = config.get("db_name", "file_share_bot")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

credit_col = db["credits"]


class CreditDB:

    # Get user credit count
    async def get(self, user_id):
        data = await credit_col.find_one({"_id": user_id})
        return data["credits"] if data else 0

    # Add credits
    async def add(self, user_id, amount=3):
        await credit_col.update_one(
            {"_id": user_id},
            {"$inc": {"credits": amount}},
            upsert=True
        )

    # Deduct 1 credit
    async def use(self, user_id):
        await credit_col.update_one(
            {"_id": user_id},
            {"$inc": {"credits": -1}}
        )

    # Reset user credits to zero
    async def reset(self, user_id):
        await credit_col.update_one(
            {"_id": user_id},
            {"$set": {"credits": 0}},
            upsert=True
        )


credit_db = CreditDB()
