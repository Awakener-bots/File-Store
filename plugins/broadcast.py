# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

from pyrogram import Client, filters
from pyrogram.raw.types import MessageActionPinMessage
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant, Forbidden, PeerIdInvalid, ChatAdminRequired
import asyncio
import re
import time


def _parse_ttl_token(token: str) -> int:
    """Parse a TTL token like '1d', '12h', '30m', '45s' or digits-only as days.
    Returns seconds (int). Invalid inputs return 0.
    """
    if not token:
        return 0
    t = token.strip().lower()
    if t.isdigit():
        # Treat plain number as days per request
        try:
            return int(t) * 24 * 60 * 60
        except Exception:
            return 0
    m = re.match(r"^(\d+)([smhd])$", t)
    if not m:
        return 0
    value = int(m.group(1))
    unit = m.group(2)
    if unit == 's':
        return value
    if unit == 'm':
        return value * 60
    if unit == 'h':
        return value * 60 * 60
    if unit == 'd':
        return value * 24 * 60 * 60
    return 0

@Client.on_message(filters.command('users'))
async def user_count(client, message):
    if not message.from_user.id in client.admins:
        return await client.send_message(message.from_user.id, client.reply_text)
    total_users = await client.mongodb.full_userbase()
    await message.reply(f"**{len(total_users)} Users are using this bot currently!**")

@Client.on_message(filters.private & filters.command('broadcast'))
async def send_text(client, message):
    """
    Usage:
            - Reply to any message and use /broadcast --action send (default) to send to all users.
            - Reply to any message and use /broadcast --action pin to send and pin the message.
            - Optional auto-delete timer: add --ttl 1d (or 12h/30m/45s). Example: /broadcast --action pin --ttl 1d
    """
    admin_ids = client.admins
    user_id = message.from_user.id
    if user_id not in admin_ids:
        return

    # Parse action and ttl from command arguments
    action = "send"
    args = []
    ttl_seconds = 0
    try:
        # message.command is provided by pyrogram for /commands
        args = message.command[1:] if hasattr(message, "command") and message.command else []
    except Exception:
        args = (message.text.split()[1:]) if message.text else []

    # Support forms:
    #   action: --action pin | --action=pin | -a pin | just 'pin'
    #   ttl: --ttl 1d | --ttl=1d | -t 1d | bare token like 1d/12h/30m/45s
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--help", "-h", "help"):
            usage = (
                "<b>Broadcast usage</b>\n"
                "Reply to a message and send:\n"
                "• /broadcast --action send\n"
                "• /broadcast --action pin\n"
                "\nOptions:\n"
                "• --action [send|pin] (default: send)\n"
                "• --ttl <duration> (auto-delete). Examples: 1d, 12h, 30m, 45s\n"
                "  You can also pass just a duration token: /broadcast 1d\n"
            )
            return await message.reply(usage)
        if arg.startswith("--action="):
            action = arg.split("=", 1)[1]
        elif arg in ("--action", "-a") and i + 1 < len(args):
            action = args[i + 1]
            i += 1
        elif arg.lower() in ("send", "pin") and len(args) == 1:
            action = arg
        elif arg.startswith("--ttl="):
            ttl_token = arg.split("=", 1)[1]
            ttl_seconds = 0 if not ttl_token else _parse_ttl_token(ttl_token)
        elif arg in ("--ttl", "-t") and i + 1 < len(args):
            ttl_token = args[i + 1]
            ttl_seconds = 0 if not ttl_token else _parse_ttl_token(ttl_token)
            i += 1
        else:
            # bare token like 1d / 12h / 30m / 45s
            maybe = _parse_ttl_token(arg)
            if maybe:
                ttl_seconds = maybe
        i += 1

    # If help was requested, it has already returned above.

    # Must be used as a reply to a message to broadcast
    if not message.reply_to_message:
        msg = await message.reply("Use this as a reply. Example: /broadcast --action send | pin | --ttl 1d\nUse /broadcast --help for details.")
        await asyncio.sleep(8)
        return await msg.delete()

    action = (action or "send").lower().strip()
    if action not in ("send", "pin"):
        msg = await message.reply("Invalid action. Use one of: send, pin\nExample: /broadcast --action pin --ttl 1d")
        await asyncio.sleep(8)
        return await msg.delete()

    query = await client.mongodb.full_userbase()
    broadcast_msg = message.reply_to_message
    total = 0
    successful = 0
    blocked = 0
    deleted = 0
    unsuccessful = 0

    pls_wait = await message.reply("<blockquote><i>Broadcasting Message.. This will Take Some Time</i></blockquote>")

    async def _schedule_delete_after(chat_id: int, msg_id: int, delay: int):
        try:
            await asyncio.sleep(delay)
            await client.delete_messages(chat_id=chat_id, message_ids=msg_id)
        except Exception as e:
            print(f"Failed to auto-delete message {msg_id} in {chat_id}: {e}")

    for chat_id in query:
        try:
            sent_msg = await broadcast_msg.copy(chat_id)
            if action == "pin":
                # Try to pin; both_sides for private chats when possible
                try:
                    await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                except Exception:
                    # Fallback without both_sides if not supported
                    await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id)
            # schedule deletion if ttl provided
            if ttl_seconds and ttl_seconds > 0:
                delete_ts = int(time.time()) + int(ttl_seconds)
                asyncio.create_task(_schedule_delete_after(chat_id, sent_msg.id, ttl_seconds))
                # persist job for reliability across restarts
                try:
                    await client.mongodb.add_broadcast_ttl_job(chat_id, sent_msg.id, delete_ts)
                except Exception as db_e:
                    print(f"Failed to persist TTL job for {chat_id}/{sent_msg.id}: {db_e}")
            successful += 1
        except FloodWait as e:
            await asyncio.sleep(getattr(e, 'value', 1))
            try:
                sent_msg = await broadcast_msg.copy(chat_id)
                if action == "pin":
                    try:
                        await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                    except Exception:
                        await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id)
                if ttl_seconds and ttl_seconds > 0:
                    delete_ts = int(time.time()) + int(ttl_seconds)
                    asyncio.create_task(_schedule_delete_after(chat_id, sent_msg.id, ttl_seconds))
                    try:
                        await client.mongodb.add_broadcast_ttl_job(chat_id, sent_msg.id, delete_ts)
                    except Exception as db_e:
                        print(f"Failed to persist TTL job for {chat_id}/{sent_msg.id}: {db_e}")
                successful += 1
            except Exception as ex:
                print(f"Failed to send after floodwait to {chat_id}: {ex}")
                unsuccessful += 1
        except UserIsBlocked:
            await client.mongodb.del_user(chat_id)
            blocked += 1
        except InputUserDeactivated:
            await client.mongodb.del_user(chat_id)
            deleted += 1
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")
            unsuccessful += 1
        total += 1

    status = f"""<blockquote><b><u>Broadcast Completed</u></b></blockquote>
<blockquote expandable><b>Total Users :</b> <code>{total}</code>
<b>Successful :</b> <code>{successful}</code>
<b>Blocked Users :</b> <code>{blocked}</code>
<b>Deleted Accounts :</b> <code>{deleted}</code>
<b>Unsuccessful :</b> <code>{unsuccessful}</code><blockquote>"""

    return await pls_wait.edit(status)



# Deprecated: old /pbroadcast command removed in favor of unified /broadcast --action pin
    
