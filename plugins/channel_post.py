# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from helper.helper_func import encode

# NOTE: The channel_post handler has been removed as it was blocking all non-command messages
# including /start with parameters. If you need this functionality, use a specific command instead.

@Client.on_message(filters.channel & filters.incoming)
async def new_post(client: Client, message: Message):
    main_channel = getattr(client, 'db_channel_id', client.db)
    
    # Check if multi-DB is enabled
    if await client.mongodb.is_multi_db_enabled():
        extra_channels = await client.mongodb.get_db_channels()
        all_channels = [main_channel] + extra_channels
    else:
        all_channels = [main_channel]
    
    if message.chat.id not in all_channels:
        return
        
    if client.disable_btn:
        return

    channel_id = message.chat.id
    msg_id = message.id

    # 🔐 Generate hybrid token (stored in MongoDB)
    try:
        token = await client.mongodb.create_file_token(channel_id, msg_id)
        link = f"https://t.me/{client.username}?start={token}"
    except Exception:
        # Fallback to Base64 if token creation fails
        converted_id = msg_id * abs(channel_id)
        base64_string = await encode(f"get-{converted_id}")
        link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    try:
        await message.edit_reply_markup(reply_markup)
    except Exception as e:
        print(e)
        pass
