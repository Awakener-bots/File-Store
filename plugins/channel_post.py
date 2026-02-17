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
    converted_id = message.id * abs(channel_id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    try:
        await message.edit_reply_markup(reply_markup)
    except Exception as e:
        print(e)
        pass
