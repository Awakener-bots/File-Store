# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper.helper_func import encode, get_message_id
from helper.font_converter import to_small_caps as sc

@Client.on_message(filters.private & filters.command('batch'))
async def batch(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)
        
    cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton(f"❌ {sc('cancel')}", callback_data="cancel_batch_process")]])
    
    # Step 1: First Message
    while True:
        try:
            ask_msg = await message.reply(f"{sc('forward the')} **{sc('first message')}** {sc('from db channel (with quotes)')}..\n\n{sc('or send the db channel post link')}", reply_markup=cancel_btn)
            first_response = await client.listen(chat_id=message.from_user.id, filters=filters.user(message.from_user.id), timeout=60)
        except Exception:
            return
            
        if isinstance(first_response, CallbackQuery):
            if first_response.data == 'cancel_batch_process':
                await first_response.answer(sc("cancelled"), show_alert=True)
                await first_response.message.delete()
                await message.reply(f"❌ **{sc('batch process cancelled.')}**")
                return
            else:
                # Ignore other callbacks or handle them?
                await first_response.answer(sc("wrong button"), show_alert=True)
                continue
            
        f_msg_id = await get_message_id(client, first_response)
        if f_msg_id:
            await ask_msg.delete() 
            break
        else:
            await first_response.reply(f"❌ {sc('error')}\n\n{sc('this forwarded post is not from my db channel or this link is taken from db channel')}", quote = True)
            continue

    # Step 2: Last Message
    while True:
        try:
            ask_msg = await message.reply(f"{sc('forward the')} **{sc('last message')}** {sc('from db channel (with quotes)')}..\n{sc('or send the db channel post link')}", reply_markup=cancel_btn)
            second_response = await client.listen(chat_id=message.from_user.id, filters=filters.user(message.from_user.id), timeout=60)
        except Exception:
            return
        
        if isinstance(second_response, CallbackQuery):
            if second_response.data == 'cancel_batch_process':
                await second_response.answer(sc("cancelled"), show_alert=True)
                await second_response.message.delete()
                await message.reply(f"❌ **{sc('batch process cancelled.')}**")
                return
            else:
                await second_response.answer(sc("wrong button"), show_alert=True)
                continue

        s_msg_id = await get_message_id(client, second_response)
        if s_msg_id:
            await ask_msg.delete()
            break
        else:
            await second_response.reply(f"❌ {sc('error')}\n\n{sc('this forwarded post is not from my db channel or this link is taken from db channel')}", quote = True)
            continue


    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"🔁 {sc('share url')}", url=f'https://telegram.me/share/url?url={link}')]])
    await second_response.reply_text(f"<b>{sc('here is your link')}</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Client.on_message(filters.private & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)
        
    cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton(f"❌ {sc('cancel')}", callback_data="cancel_batch_process")]])
        
    while True:
        try:
            ask_msg = await message.reply(f"{sc('forward message from the db channel (with quotes)')}..\n{sc('or send the db channel post link')}", reply_markup=cancel_btn)
            channel_message = await client.listen(chat_id = message.from_user.id, filters=filters.user(message.from_user.id), timeout=60)
        except:
            return
            
        if isinstance(channel_message, CallbackQuery):
            if channel_message.data == 'cancel_batch_process':
                await channel_message.answer(sc("cancelled"), show_alert=True)
                await channel_message.message.delete()
                await message.reply(f"❌ **{sc('process cancelled.')}**")
                return
            else:
                await channel_message.answer(sc("wrong button"), show_alert=True)
                continue
            
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            await ask_msg.delete() 
            break
        else:
            await channel_message.reply(f"❌ {sc('error')}\n\n{sc('this forwarded post is not from my db channel or this link is not taken from db channel')}", quote = True)
            continue

    channel_id = getattr(client, 'db_channel_id', client.db)
    base64_string = await encode(f"get-{msg_id * abs(channel_id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"🔁 {sc('share url')}", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(f"<b>{sc('here is your link')}</b>\n\n{link}", quote=True, reply_markup=reply_markup)

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio) & ~filters.command(["start", "batch", "genlink"]))
async def single_file_gen_handler(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return

    # Skip if message is a command (handled by other handlers)
    if message.text and message.text.startswith("/"):
        return

    try:
        msg = await message.reply(f"🔄 {sc('processing')}...", quote=True)
        
        main_channel = getattr(client, 'db_channel_id', client.db)
        
        # If message is forwarded from DB Channel, use existing ID
        if message.forward_origin and message.forward_origin.type == "channel":
            forwarded_channel_id = message.forward_origin.chat.id
            # Check if it's from any of our DB channels
            extra_channels = await client.mongodb.get_db_channels()
            all_db_channels = [main_channel] + extra_channels
            
            if forwarded_channel_id in all_db_channels:
                msg_id = message.forward_origin.message_id
                channel_id = forwarded_channel_id
            else:
                # Not from our DB, copy to selected channel
                channel_id = await client.mongodb.get_next_db_channel(main_channel)
                post = await message.copy(chat_id=channel_id, caption=message.caption)
                msg_id = post.id
        else:
            # Copy to selected DB Channel using round-robin
            channel_id = await client.mongodb.get_next_db_channel(main_channel)
            post = await message.copy(chat_id=channel_id, caption=message.caption)
            msg_id = post.id
            
        # Generate Link
        base64_string = await encode(f"get-{msg_id * abs(channel_id)}")
        link = f"https://t.me/{client.username}?start={base64_string}"
        
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"🔁 {sc('share url')}", url=f'https://telegram.me/share/url?url={link}')]])
        
        await msg.edit_text(f"<b>{sc('here is your link')}</b>\n\n{link}", reply_markup=reply_markup)
        
    except Exception as e:
        print(f"Error in single_file_gen: {e}")
        await message.reply(f"❌ {sc('error')}: {e}")
