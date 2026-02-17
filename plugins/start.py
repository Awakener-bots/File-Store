# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

from helper.helper_func import *
from helper.credit_db import credit_db
from helper.enhanced_credit_db import EnhancedCreditDB
from helper.font_converter import to_small_caps as sc
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import humanize
import secrets
import json

# Load credit configuration
try:
    with open("setup.json", "r") as f:
        setup_data = json.load(f)
        credit_config = setup_data[0].get("credit_config", {})
except:
    credit_config = {}


@Client.on_message(filters.command('start') & filters.private)
@force_sub
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    present = await client.mongodb.present_user(user_id)
    if not present:
        try:
            await client.mongodb.add_user(user_id)
        except Exception as e:
            client.LOGGER(__name__, client.name).warning(f"Error adding a user:\n{e}")

    is_banned = await client.mongodb.is_banned(user_id)
    if is_banned:
        return await message.reply(f"**{sc('You have been banned from using this bot!')}**")
    
    # Premium check
    is_premium_user = await client.mongodb.is_premium(user_id)

    # Enhanced credit system
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    credit_data = await enhanced_db.get_credits(user_id)
    user_credits = credit_data.get("balance", 0)
    
    # Check for expired credits
    await enhanced_db.check_and_remove_expired(user_id)

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1].strip()
        except IndexError:
            return

        # If it's a batch link, let the batch_handler handle it (Group 1)
        if base64_string.startswith("batch_"):
            return
        
        # ============== REFERRAL SYSTEM ==============
        # Check if this is a referral link: /start ref_XXXXXXXX
        if base64_string.startswith("ref_"):
            referral_code = base64_string.replace("ref_", "")
            
            # Apply referral if user is new
            if not present:
                referrer_id = await enhanced_db.apply_referral(user_id, referral_code)
                if referrer_id:
                    # Notify new user
                    await message.reply(
                        f"🎉 **{sc('Welcome!')}**\n\n"
                        f"{sc('You joined using a referral link!')}\n"
                        f"{sc('When you access your first file, your referrer will earn credits!')}"
                    )
            return
            
        access_token = None
        original_base64 = base64_string
        
        # ---------------- TOKEN VERIFIED / SHORTENER SOLVED ----------------
        if "_" in base64_string:
            parts = base64_string.split("_", 1)
            if len(parts) == 2:
                original_base64 = parts[0]
                access_token = parts[1]

                # Check if verification is enabled
                token_verification_enabled = await client.mongodb.get_bot_config('token_verification_enabled', True)

                # ONLY Verify if enabled
                if token_verification_enabled:
                    # Track shortener click
                    await client.mongodb.increment_token_clicks(user_id, access_token)

                    verify_result = await client.mongodb.verify_access_token(
                        user_id, access_token, original_base64
                    )
    
                    # ======================= ANTI-BYPASS LOGIC ======================
                    if verify_result == "BYPASS":
                        # Check for auto-ban (Skip for Admins)
                        if user_id not in client.admins:
                            was_banned = await client.mongodb.check_and_auto_ban(user_id, max_attempts=5)
                            
                            if was_banned:
                                await message.reply(
                                    f"<blockquote>🚫 <b>{sc('you have been banned')}</b></blockquote>\n"
                                    f"<blockquote><b>{sc('reason: multiple bypass attempts detected')}</b></blockquote>\n"
                                    f"<blockquote><b>{sc('contact admin if you think this is a mistake')}</b></blockquote>"
                                )
                                return
                        
                        await message.reply(
                            f"<blockquote>⚠️ <b>{sc('bypass detected')}</b></blockquote>\n"
                            f"<blockquote><b>{sc('how many times have i told you, dont try to outsmart your dad')}🖕</b></blockquote>\n"
                            f"<blockquote><b>{sc('now be a good boy and solve it again, and this time dont get smart !!')}</b></blockquote>"
                        )
    
                        # Notify admin
                        bypass_count = await client.mongodb.get_bypass_count(user_id)
                        await client.send_message(
                            client.owner,
                            f"🚨 <b>{sc('bypass detected')}</b>\n"
                            f"{sc('user')}: <code>{user_id}</code>\n"
                            f"{sc('attempts in 24h')}: <b>{bypass_count}</b>"
                        )
                        return
                    
                    # Handle other error cases
                    if verify_result == "ALREADY_USED":
                        await message.reply(
                            f"<blockquote>❌ <b>{sc('token already used')}</b></blockquote>\n"
                            f"<blockquote><b>{sc('this link can only be used once')}</b></blockquote>\n"
                            f"<blockquote><b>{sc('please get a new link')}</b></blockquote>"
                        )
                        return
                    
                    if verify_result == "EXPIRED":
                        await message.reply(
                            f"<blockquote>⏰ <b>{sc('token expired')}</b></blockquote>\n"
                            f"<blockquote><b>{sc('this link has expired')}</b></blockquote>\n"
                            f"<blockquote><b>{sc('please get a new link')}</b></blockquote>"
                        )
                        return
    
                    if verify_result != "OK":
                        await message.reply(
                            f"<blockquote>❌ <b>{sc('invalid token')}</b></blockquote>\n"
                            f"<blockquote><b>{sc('please get a new link')}</b></blockquote>"
                        )
                        return
    
                    # ---------------- GIVE 3 CREDITS (IF ENABLED) ----------------
                    credit_system_enabled = await client.mongodb.is_credit_system_enabled()
                    
                    if credit_system_enabled:
                        expiry_days = credit_config.get("expiry_days", 30)
                        verification_reward = await client.mongodb.get_bot_config('verification_reward', 3)
                        await enhanced_db.add_credits(user_id, verification_reward, expiry_days, reason="shortener_solved")

                        # Re-fetch credits to ensure accurate count for deduction
                        credit_data = await enhanced_db.get_credits(user_id)
                        user_credits = credit_data.get("balance", 0)
    
                        await message.reply(
                            f"<b>🎉 {sc('verification successful!')}</b>\n"
                            f"✅ <b>{sc(f'you earned {verification_reward} credits!')}</b>\n"
                            f"📂 <b>{sc('sending your file now...')}</b>"
                        )
                    else:
                        await message.reply(
                            f"<b>🎉 {sc('verification successful!')}</b>\n"
                            f"📂 <b>{sc('sending your file now...')}</b>"
                        )

                    # Grant temporary access to bypass the check below
                    is_premium_user = True
                    # Fall through to file sending logic...

        # -------------------------- DECODE FILE --------------------------
        try:
            string = await decode(original_base64)
            argument = string.split("-")
        except Exception:
            return
        
        ids = []
        custom_chat_id = None
        
        if len(argument) == 3:
            try:
                # Check for New Format: get-CHANNEL_ID-MSG_ID
                # Heuristic: Channel IDs (without -100) are usually smaller than the HUGE encoded IDs involved in multiplication?
                # Or better: Try to interpret as multi-db first.
                
                # If it's a batch file link from our new handler, it is DEFINITELY get-CH-MSG.
                # But what about legacy "Batch Range" links (get-START-END)?
                # START = MSG_ID * DB_ID.
                # DB_ID is -100... (negative). But `start` code uses `abs(db)`.
                # So START is positive huge integer.
                
                val1 = int(argument[1])
                val2 = int(argument[2])
                
                # If val2 is small (message ID), it's likely New Format.
                # If val2 is HUGE (encoded), it's Old Format.
                
                # Typical Channel ID (without -100) ~ 10-15 digits.
                # Typical Message ID ~ 1-6 digits.
                # Typical Encoded ID (Msg * Ch) ~ 20+ digits.
                
                if val2 < 1000000: # Message ID < 1 Million (Safe assumption?)
                    # New Format
                    channel_id = val1
                    msg_id = val2
                    custom_chat_id = int(f"-100{channel_id}")
                    ids = [msg_id]
                else:
                    # Old Format (Range)
                    start = int(val1 / abs(client.db))
                    end = int(val2 / abs(client.db))
                    ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except:
                pass
            try:
                # Format: get-CHANNEL_ID-MSG_ID
                # New Logic for Multi-DB
                channel_id = int(argument[1])
                msg_id = int(argument[2])
                
                # Check if it's a range or single file?
                # The format get-CH-MSG implies single file.
                # But existing logic `start = int(int(argument[1]) / abs(client.db))` implies the arguments are ENCODED IDs.
                
                # Wait, if I change the generation to `get-{channel_id}-{msg_id}`, then `argument[1]` is `channel_id`.
                
                # Let's support BOTH old and new formats.
                # Old Format: get-START_ID-END_ID (where START_ID = REAL_ID * DB_ID)
                # New Format: get-CHANNEL_ID-MSG_ID
                
                # Heuristic: 
                # If argument[1] is a small number (channel ID 100xxxx), it might be a channel ID.
                # If argument[1] is a HUGE number, it's an encoded ID.
                
                # Actually, `batch_handler` generates `get-{channel_id}-{msg_id}` now.
                # So `argument` has 3 parts: ["get", "CHANNEL_ID", "MSG_ID"]
                
                arg1 = int(argument[1])
                arg2 = int(argument[2])
                
                # If it's the old Range format (get-START-END), the numbers are likely HUGE.
                # If it's the new Multi-DB format, arg1 is Channel ID, arg2 is Message ID.
                
                # Let's assume new format if arg1 < 100000000000000 (just a guess, or check logic)
                
                # BETTER APPROACH:
                # The new `batch_handler` uses `get-{channel_id}-{msg_id}`.
                # `channel_id` is clean (no -100).
                
                # Let's try to fetch assuming it's new format.
                full_chat_id = int(f"-100{arg1}")
                message_id = arg2
                
                # But wait, `get_messages` takes a LIST of IDs.
                # And `ids` variable is expected to be a list of Message IDs.
                # But existing code does: `messages = await get_messages(client, ids)`
                # And `get_messages` uses `client.db` (Default DB).
                
                # WE NEED TO PASS `chat_id` to `get_messages`.
                # But `get_messages` signature in `start.py` call doesn't support it yet (I just updated helper, but start.py calls it).
                
                # We need to change how `ids` is structured OR how `get_messages` is called.
                
                # If we have a single file from a specific channel:
                ids = [message_id] # This is just the ID.
                # But `get_messages` will use `client.db` by default!
                
                # We need to store the `chat_id` somewhere to use it later.
                # Or call `get_messages` directly here with the explicit chat_id.
                
                custom_chat_id = full_chat_id
                
            except:
                pass

        elif len(argument) == 2:
            try:
                # Format: get-GENERATED_ID
                # Old logic: int(argument[1]) / abs(client.db_channel.id)
                # This only works for Default DB.
                ids = [int(int(argument[1]) / abs(client.db))]
            except:
                return
        
        # Check if credit system is enabled globally
        credit_system_enabled = await client.mongodb.is_credit_system_enabled()
        
        # Check if token verification is enabled
        token_verification_enabled = await client.mongodb.get_bot_config('token_verification_enabled', True)
        
        # ------------------ USER TRYING TO GET FILE ------------------
        
        # Check if this is user's first file access (for referral reward)
        is_first_file = credit_data.get("total_spent", 0) == 0 and not is_premium_user

        # If user has credits → deduct ONE (ONLY IF SYSTEM ENABLED)
        if credit_system_enabled and user_credits > 0 and not is_premium_user:
            await enhanced_db.use_credit(user_id)
            user_credits -= 1
            is_premium_user = True

            await message.reply(
                f"⚡ {sc('1 credit used')}!\n"
                f"{sc('remaining credits')}: {user_credits}"
            )
            
            # Reward referrer if this is first file access
            if is_first_file and credit_data.get("referred_by"):
                # ... (existing code) ...
                
                # Notify referrer
                try:
                    await client.send_message(
                        referrer_id,
                        f"🎉 **{sc('referral reward')}!**\n\n"
                        f"{sc('you earned')} **{reward_amount} {sc('credits')}** {sc('for referring a user')}!\n"
                        f"{sc('user id')}: <code>{user_id}</code>\n\n"
                        f"{sc('keep sharing your referral link to earn more!')}"
                    )
                except:
                    pass

        # If STILL not premium → show shortener (ONLY IF ENABLED)
        if not is_premium_user and token_verification_enabled:
            temp_msg = await message.reply(f"🔄 **{sc('generating your link')}...**")
            
            access_token = secrets.token_hex(16)
            await client.mongodb.create_access_token(user_id, original_base64, access_token)
            
            file_link = f"https://t.me/{client.username}?start={original_base64}_{access_token}"
            shortened_url = await shorten_url(file_link)
            
            await temp_msg.delete()
            
            premium_text = (
                f"<b>🔗 {sc('your file link')}:</b>\n\n"
                f"<blockquote>👉 {sc('solve the shortener to unlock your file')}</blockquote>\n\n"
                f"<b>💎 {sc('want direct access')}?</b> {sc('buy premium')}!"
            )
            
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"⌜{sc('get files')}⌟", url=shortened_url)],
                [
                    InlineKeyboardButton(f"「{sc('tutorial')}」", url="https://t.me/+rKJmAabX6MxmMjg9"),
                    InlineKeyboardButton(f"「{sc('premium')}」", url="https://t.me/Cultured_Support_bot")
                ]
            ])
            
            await client.send_photo(
                chat_id=message.chat.id,
                photo="https://i.ibb.co/FtnfS25/photo-2025-10-31-18-43-10-7567458335163678756.jpg",
                caption=premium_text,
                reply_markup=buttons,
                protect_content=True  #  ✅ ADD THIS LINE
            )
            return
        
        # ------------------ PREMIUM / CREDIT USERS: SEND FILE ------------------
        temp_msg = await message.reply(f"{sc('wait a sec')}..")
        
        try:
            if 'custom_chat_id' in locals() and custom_chat_id:
                # Multi-DB Fetch
                messages = await get_messages(client, ids, custom_chat_id)
            else:
                # Default DB Fetch
                messages = await get_messages(client, ids)
        except:
            await temp_msg.edit_text(f"{sc('something went wrong')}..!")
            return
        finally:
            if messages:
                await temp_msg.delete()
            else:
                await temp_msg.edit(f"{sc('couldnt find the files in database')}.")

        yugen_msgs = []

        for msg in messages:
            caption = (
                client.messages.get('CAPTION', '').format(
                    previouscaption=f"<blockquote>{msg.caption.html}</blockquote>" if msg.caption else f"<blockquote>{msg.document.file_name}</blockquote>"
                )
                if client.messages.get('CAPTION', '') and msg.document
                else (msg.caption.html if msg.caption else "")
            )

            try:
                copied_msg = await msg.copy(
                    chat_id=user_id,
                    caption=caption,
                    protect_content=client.protect
                )
                yugen_msgs.append(copied_msg)
            except:
                pass

        if messages and client.auto_del > 0:
            warning = await client.send_message(
                user_id,
                f"<b>⚠️ {sc('file will be deleted in')} {humanize.naturaldelta(client.auto_del)}.</b>"
            )
            asyncio.create_task(delete_files(yugen_msgs, client, warning, text))
        return

    # ---------------- NORMAL /start UI ----------------
    buttons = [
        [InlineKeyboardButton("💎 ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ", callback_data="premium_plans")],
        [InlineKeyboardButton("⌜ᴡᴇʙsᴇʀɪᴇs ɴᴇᴛᴡᴏʀᴋ⌟", url="https://t.me/Omniseries"),
         InlineKeyboardButton("⌜ɴᴇᴛᴡᴏʀᴋ⌟", url="https://t.me/The_Mortals")],
        [InlineKeyboardButton("⌜ᴀʙᴏᴜᴛ⌟", callback_data="about"),
         InlineKeyboardButton("⌜ᴅᴇᴠ⌟", url="https://t.me/GPGMS0")]
    ]

    if user_id in client.admins:
        buttons.insert(0, [InlineKeyboardButton("⌜ꜱᴇᴛᴛɪɴɢꜱ⌟", callback_data="settings")])
    
    photo = client.messages.get("START_PHOTO", "")
    if photo:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=photo,
            caption=client.messages.get('START', 'No Start Msg').format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=f"@{message.from_user.username}" if message.from_user.username else None,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text=client.messages.get('START', 'No Start Message').format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=f"@{message.from_user.username}" if message.from_user.username else None,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
