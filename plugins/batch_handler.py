# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

# Batch Link Handler
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.font_converter import to_small_caps as sc
from helper.quality_detector import get_quality_priority

# Use group=1 to give this handler lower priority than /start (which is in group=0 by default)
@Client.on_message(filters.private & filters.text, group=1)
async def batch_link_handler(client: Client, message: Message):
    """Handle batch link access"""
    
    # Only handle batch_ links
    if not message.text or not message.text.startswith("/start batch_"):
        return
    
    text = message.text
    batch_id = text.replace("/start batch_", "").strip()
    
    # Get batch from database
    batch = await client.mongodb.get_batch(batch_id)
    
    if not batch:
        await message.reply(f"❌ {sc('batch not found or expired')}")
        return
    
    user_id = message.from_user.id
    
    # Check if user is premium
    is_premium = await client.mongodb.is_premium(user_id)
    
    # Get user credits
    from helper.enhanced_credit_db import EnhancedCreditDB
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    credit_data = await enhanced_db.get_credits(user_id)
    user_credits = credit_data.get("balance", 0)
    
    # Check if credit system is enabled
    credit_system_enabled = await client.mongodb.is_credit_system_enabled()
    if not credit_system_enabled:
        user_credits = 0 # Disable credit usage logic
    
    # Determine batch type (Season vs Episode)
    qualities = set(f['quality'] for f in batch['files'])
    is_season_batch = len(qualities) <= 1
    
    # Import helpers needed for formatting
    from helper.quality_detector import parse_episode_info, get_series_name
    import humanize
    
    # Sort files
    if is_season_batch:
        # Sort by episode number for season packs
        files = sorted(batch['files'], key=lambda f: parse_episode_info(f['filename']).get('episode', 0) or 0)
    else:
        # Sort by quality for episode packs
        files = sorted(batch['files'], key=lambda f: get_quality_priority(f['quality']))
    
    # If Season Batch -> Send Files Directly
    if is_season_batch:
        # Fetch messages
        file_ids = [int(f['file_id']) for f in files]
        from helper.helper_func import get_messages, delete_files
        
        msg_to_delete = await message.reply(f"{sc('processing')}.. ⏳")
        
        try:
            # Group files by channel_id to optimize fetching
            from collections import defaultdict
            files_by_channel = defaultdict(list)
            for f in files:
                channel_id = f.get('channel_id', int(client.db))
                channel_id = int(str(channel_id).replace("-100", ""))  # Clean ID
                files_by_channel[channel_id].append(int(f['file_id']))
            
            messages = []
            for chat_id, msg_ids in files_by_channel.items():
                # Add -100 prefix if missing
                full_chat_id = int(f"-100{chat_id}")
                msgs = await get_messages(client, msg_ids, full_chat_id)
                messages.extend(msgs)
        except Exception as e:
            await msg_to_delete.edit(f"❌ Error fetching messages: {e}")
            return
            
        if not messages:
            await msg_to_delete.edit("❌ Files not found in DB channel.")
            return
            
        await msg_to_delete.delete()
        
        sent_msgs = []
        for msg in messages:
            # Caption Logic (Mirrors start.py)
            caption = (
                client.messages.get('CAPTION', '').format(
                    previouscaption=f"<blockquote>{msg.caption.html}</blockquote>" if msg.caption else f"<blockquote>{msg.document.file_name}</blockquote>"
                )
                if client.messages.get('CAPTION', '') and msg.document
                else (msg.caption.html if msg.caption else "")
            )
            
            try:
                copied = await msg.copy(
                    chat_id=user_id,
                    caption=caption,
                    protect_content=client.protect
                )
                sent_msgs.append(copied)
            except Exception as e:
                pass
                
        # Auto-Delete Logic
        if sent_msgs and client.auto_del > 0:
            warning = await message.reply(
                f"<b>⚠️ {sc('files will be deleted in')} {humanize.naturaldelta(client.auto_del)}.</b>"
            )
            # Run delete_files in background
            import asyncio
            asyncio.create_task(delete_files(sent_msgs, client, warning, text))
            
        return

    # Else (Episode Pack) -> Show Menu (Existing Logic)
    
    # Build quality selection message
    msg = f"""**📦 {sc('batch download')}**

**{sc('title')}:** {batch['base_name']}
**{sc('type')}:** {sc('episode pack')}

"""
    
    buttons = []
    for file_data in files:
        quality = file_data['quality']
        filename = file_data['filename']
        file_id = file_data['file_id']
        
        # Generator Button Text
        # For Episode Packs: "480p"
        button_text = f"📥 {quality}"
            
        if is_premium or (credit_system_enabled and user_credits > 0):
            button_text += " ✅"
        
        buttons.append([InlineKeyboardButton(
            button_text,
            callback_data=f"batchfile_{batch_id}_{file_id}"
        )])
        
        # List entry (Episode Pack only)
        # msg += f"└ **{quality}** - {filename}\n"
    
    msg += f"\n{sc('select file to download')}"
    
    if not is_premium and user_credits == 0 and credit_system_enabled:
        msg += f"\n\n⚠️ {sc('you need credits or premium to access files')}"
        
    # Auto-delete warning
    if client.auto_del > 0:
        msg += f"\n\n⏳ {sc('files auto-delete in')} {humanize.naturaldelta(client.auto_del)}"
    
    keyboard = InlineKeyboardMarkup(buttons)
    
    await message.reply(msg, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"^batchfile_"))
async def batch_file_callback(client: Client, query):
    """Handle batch file selection"""
    
    data = query.data.split("_")
    batch_id = data[1]
    file_id = data[2]
    
    user_id = query.from_user.id
    
    # Get the actual file message
    batch = await client.mongodb.get_batch(batch_id)
    if not batch:
        await query.answer("❌ Batch expired", show_alert=True)
        return
    
    # Find the file
    file_data = next((f for f in batch['files'] if f['file_id'] == file_id), None)
    if not file_data:
        await query.answer("❌ File not found", show_alert=True)
        return
    
    # Redirect to normal file access with channel + file_id
    # We need to encode the ID so start.py can decode it
    # Pattern expected by start.py: "get-{id * channel_id}" (OR NEW PATTERN FOR MULTI DB)
    
    try:
        msg_id = int(file_id)
        # Use stored channel_id or default DB
        channel_id = file_data.get('channel_id', client.db)
        
        # Ensure channel_id is positive integer for multiplication logic (Old Method)
        # BUT wait! If we have multiple DBs, the logic "id * channel_id" is ambiguous if channel_id varies?
        # Actually start.py logic: 
        # decoded = base64_decode(token) -> "12345678"
        # Since we can't easily reverse "id * channel_id" without knowing channel_id...
        # Wait, start.py logic is FLAWED for multi-DB if it relies on a SINGLE client.db for decoding?
        
        # Let's check start.py logic.
        # If start.py expects "get-INT", and tries to find "INT / client.db" or "INT / abs(client.db)"...
        # If the channel_id is DIFFERENT, division will fail or give wrong Msg ID.
        
        # WE NEED A NEW LINK FORMAT for Multi-DB.
        # Format: "get-CHANNELID-MSGID" ?
        # But start.py needs to support it.
        
        # Current Start.py Logic:
        # 1. "get-{generated_id}"
        # 2. decoded_id = decode(token)
        # 3. msg_id = decoded_id / abs(client.db)  <-- THIS IS THE BOTTLENECK.
        
        # To support Multi-DB, we MUST change start.py to handle "CHANNEL_ID-MSG_ID" format.
        # Or "get-{encoded_string}" where encoded string contains both.
        
        # Proposed Format: "get-BatchFile-{channel_id}-{msg_id}"
        # Or simple: "get-{channel_id}-{msg_id}" (if we can distinguish from old format)
        
        # Old Format: integer (huge)
        # New Format: "CH_ID-MSG_ID" (string)
        
        channel_id = str(channel_id).replace("-100", "") # Remove prefix for shorter link
        token_string = f"get-{channel_id}-{msg_id}" 
        encoded_token = await encode(token_string)
        
        file_link = f"https://t.me/{client.username}?start={encoded_token}"
    except Exception as e:
        client.LOGGER(__name__, client.name).warning(f"Error generating link: {e}")
        file_link = f"https://t.me/{client.username}?start={file_id}"
    
    import humanize
    timer_text = ""
    if client.auto_del > 0:
        timer_text = f"\n\n⏳ **{sc('warning')}:** {sc('file auto-deletes in')} {humanize.naturaldelta(client.auto_del)} {sc('after opening')}"
    
    await query.message.reply(
        f"**📥 {file_data['quality']}**\n"
        f"📄 {file_data['filename']}"
        f"{timer_text}\n\n"
        f"{sc('click below to access')}:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📥 {sc('get file')}", url=file_link)]
        ])
    )
