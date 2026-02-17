# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest

@Client.on_chat_join_request(filters.channel)
async def handle_join_request(client, join_request: ChatJoinRequest):
    user_id = join_request.from_user.id
    channel_id = join_request.chat.id
    channel_name = join_request.chat.title
    channel = client.fsub_dict.get(channel_id, [])
    is_banned = await client.mongodb.is_banned(user_id)
    if is_banned:
        return
    if channel:
        return await client.mongodb.add_channel_user(channel_id, user_id)
        
