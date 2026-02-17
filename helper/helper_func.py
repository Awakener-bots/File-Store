import base64
import re
import asyncio
import aiohttp
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant, Forbidden, PeerIdInvalid, ChatAdminRequired, FloodWait
from datetime import datetime, timedelta
from pyrogram import errors
from config import URL_SHORTENERS

async def shorten_url(long_url: str) -> str:
    """
    Shorten URL using configured URL shortener services
    Returns shortened URL or original URL if shortening fails
    """
    for provider_key, provider_config in URL_SHORTENERS.items():
        if not provider_config.get('active', False):
            continue
            
        try:
            api_url = provider_config['api_url']
            api_token = provider_config.get('api_token', '')
            format_param = provider_config.get('format', 'text')
            
            params = {
                'api': api_token,
                'url': long_url,
                'format': format_param
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        short_url = await response.text()
                        short_url = short_url.strip()
                        if short_url and short_url.startswith('http'):
                            return short_url
        except Exception as e:
            print(f"Error with {provider_key}: {e}")
            continue
    
    # If all providers fail, return original URL
    return long_url

async def encode(string):
    string_bytes = string.encode("utf-8")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=") # links generated before this commit will be having = sign, hence striping them to handle padding errors.
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("utf-8")
    return string

async def get_messages(client, message_ids, chat_id=None):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        msgs = []
        try:
            msgs = await client.get_messages(
                chat_id=chat_id if chat_id else int(client.db),
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=chat_id if chat_id else int(client.db),
                message_ids=temb_ids
            )
        # Removed generic except block to see errors
        
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    target_chat_id = getattr(client, 'db_channel_id', client.db)
    if message.forward_from_chat:
        if message.forward_from_chat.id == target_chat_id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern,message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0


def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

async def is_bot_admin(client, channel_id):
    try:
        bot = await client.get_chat_member(channel_id, "me")
        if bot.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            # Check for specific rights if needed, but for DB channel, just being admin is usually enough to read/copy.
            # However, to be safe, we might want rights to post messages if we ever use it for that.
            # For now, basic admin check is fine for "reading" files.
            return True, None
        return False, "Bot is not an admin in the channel."
    except UserNotParticipant:
        return False, "Bot is not in the channel."
    except errors.ChatAdminRequired:
        return False, "Bot lacks permission to access admin information in this channel."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

async def check_subscription(client, user_id):
    """Check if a user is subscribed to all required channels."""
    statuses = {}

    for channel_id, (channel_name, channel_link, request, timer) in client.fsub_dict.items():
        if request:
            send_req = await client.mongodb.is_user_in_channel(channel_id, user_id)
            if send_req:
                statuses[channel_id] = ChatMemberStatus.MEMBER
                continue
        try:
            user = await client.get_chat_member(channel_id, user_id)
            statuses[channel_id] = user.status
        except UserNotParticipant:
            statuses[channel_id] = ChatMemberStatus.BANNED
        except Forbidden:
            client.LOGGER(__name__, client.name).warning(f"Bot lacks permission for {channel_name}.")
            statuses[channel_id] = None
        except Exception as e:
            client.LOGGER(__name__, client.name).warning(f"Error checking {channel_name}: {e}")
            statuses[channel_id] = None

    return statuses


def is_user_subscribed(statuses):
    """Check if user is subscribed to all channels."""
    return all(
        status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
        for status in statuses.values() if status is not None
    ) and bool(statuses)


def force_sub(func):
    """Decorator to enforce force subscription before executing a command."""
    async def wrapper(client: Client, message: Message):
        if not client.fsub_dict:
            return await func(client, message)
        photo = client.messages.get('FSUB_PHOTO', '')
        if photo:
            msg = await message.reply_photo(
                caption="<code>Checking subscription...</code>", 
                photo=photo
            )
        else:
            msg = await message.reply(
                "<code>Checking subscription...</code>"
            )
        user_id = message.from_user.id
        statuses = await check_subscription(client, user_id)

        if is_user_subscribed(statuses):
            await msg.delete()
            return await func(client, message)

        # User is not subscribed to all channels
        buttons = []
        channels_message = f"{client.messages.get('FSUB', '')}\n\n<b>ᴄʜᴀɴɴᴇʟ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ꜱᴛᴀᴛᴜꜱ:</b>\n\n"

        status_emojis = {
            ChatMemberStatus.MEMBER: "✅",
            ChatMemberStatus.ADMINISTRATOR: "🛡️",
            ChatMemberStatus.OWNER: "👑",
            ChatMemberStatus.BANNED: "❌",
            None: "⚠️"
        }
        c = 0
        for channel_id, (channel_name, channel_link, request, timer) in client.fsub_dict.items():
            status = statuses.get(channel_id, None)
            emoji = status_emojis.get(status, "❓")
            status_of_user = "Joined" if emoji in ('✅', '🛡️', '👑') else "Not Joined"
            c = c+1
            channels_message += f"{c}. {emoji} <code>{channel_name}</code> - __{status_of_user}__\n"
            if timer > 0:
                expire_time = datetime.now() + timedelta(minutes=timer)
                invite = await client.create_chat_invite_link(
                    chat_id=channel_id,
                    expire_date=expire_time,
                    creates_join_request=request
                )
                channel_link = invite.invite_link
            if status not in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
                buttons.append(InlineKeyboardButton(channel_name, url=channel_link))
        
        # Add "Try Again" button if needed
        from_link = message.text.split(" ")
        if len(from_link) > 1:
            try_again_link = f"https://t.me/{client.username}/?start={from_link[1]}"
            buttons.append(InlineKeyboardButton("🔄 Try Again!", url=try_again_link))

        # Organize buttons in rows of 2
        buttons_markup = InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])
        buttons_markup = None if not buttons else buttons_markup
        # Edit message with status update and buttons
        try:
            await msg.edit_text(text=channels_message, reply_markup=buttons_markup)
        except Exception as e:
            client.LOGGER(__name__, client.name).warning(f"Error updating message: {e}")

    return wrapper

async def delete_files(messages, client, k, enter):
    auto_del = client.auto_del
    if auto_del > 0:
        await asyncio.sleep(auto_del)

        for msg in messages:
            if msg and msg.chat:
                try:
                    await client.delete_messages(chat_id=msg.chat.id, message_ids=[msg.id])
                except Exception as e:
                    client.LOGGER(__name__, client.name).warning(f"The attempt to delete the media {getattr(msg, 'id', 'Unknown')} was unsuccessful: {e}")
            else:
                client.LOGGER(__name__, client.name).warning("Encountered an empty or deleted message.")
        
        command = enter.split(" ")
        command_part = command[1] if len(command) > 1 else None
        
        
        keyboard = None
    await k.edit_text(
        "<blockquote><b><i>Your Video / File Is Successfully Deleted ✅</i></b></blockquote>",
        reply_markup=keyboard
    )
