# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

# Auto-Batch Handler for Channel Posts
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.quality_detector import extract_quality, get_base_name, get_quality_priority
from helper.font_converter import to_small_caps as sc
import asyncio

# Store for tracking recent files
recent_files = {}

@Client.on_message(filters.channel & filters.document)
async def auto_batch_handler(client: Client, message: Message):
    """Automatically detect and group quality variants"""
    
    # Check if auto-batch is enabled (Default FALSE now)
    auto_batch_enabled = await client.mongodb.get_bot_config('auto_batch_enabled', False)
    if not auto_batch_enabled:
        return
    
    filename = message.document.file_name
    if not filename:
        return
    
    # Extract quality and base name
    quality = extract_quality(filename)
    if not quality:
        return  # No quality detected, skip
    
    base_name = get_base_name(filename)
    if not base_name:
        return
    
    file_id = message.id
    user_id = message.from_user.id if message.from_user else 0
    
    # Add to pending files
    await client.mongodb.add_pending_file(
        file_id=str(file_id),
        filename=filename,
        base_name=base_name,
        quality=quality,
        user_id=user_id,
        channel_id=message.chat.id
    )
    
    # Wait a bit for more files
    await asyncio.sleep(2)
    
    # Get configured batch mode
    batch_mode = await client.mongodb.get_bot_config('auto_batch_mode', 'episode')
    
    # Import here to avoid circular dependencies
    from helper.quality_detector import get_series_name
    
    # Check for matching files
    time_window = await client.mongodb.get_bot_config('auto_batch_time_window', 30)
    pending = await client.mongodb.get_pending_files(time_window)
    
    # Group files based on mode
    groups = {}
    for file in pending:
        if batch_mode == 'episode':
            # Group by Base Name (Show S01 E01)
            group_key = file['base_name']
        else:
            # Group by Series Name + Quality (Show S01 [720p])
            series_name = get_series_name(file['filename'])
            quality = file['quality']
            group_key = f"{series_name} [{quality}]"
            
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(file)
    
    # Determine current file's group key
    if batch_mode == 'episode':
        current_group_key = base_name
    else:
        current_series = get_series_name(filename)
        current_group_key = f"{current_series} [{quality}]"
    
    # Check if this group has enough files to batch
    if current_group_key in groups and len(groups[current_group_key]) >= 2:
        files = groups[current_group_key]
        
        # Sort files
        if batch_mode == 'episode':
            files.sort(key=lambda f: get_quality_priority(f['quality']))
        else:
            files.sort(key=lambda f: f['filename'])
        
        # Create batch
        # Use group_key as the Batch Name
        batch_id = await client.mongodb.create_batch(current_group_key, [
            {
                'file_id': f['file_id'],
                'filename': f['filename'],
                'quality': f['quality'],
                'channel_id': f.get('channel_id', message.chat.id)
            }
            for f in files
        ])
        
        # Determine display text
        if batch_mode == 'episode':
            display_info = " | ".join([f['quality'] for f in files])
            title_text = f"**{sc('qualities')}:** {display_info}"
        else:
            display_info = f"{len(files)} Episodes"
            title_text = f"**{sc('content')}:** {display_info}"
            
        timer_text = ""
        if client.auto_del > 0:
            import humanize
            timer_text = f"⏳ **{sc('auto delete')}:** {humanize.naturaldelta(client.auto_del)}\n"
            
        batch_text = (
            f"**📦 {sc('batch available')}**\n\n"
            f"**{sc('title')}:** {current_group_key}\n"
            f"{title_text}\n"
            f"{timer_text}\n"
            f"{sc('click below to access')}"
        )
        
        batch_button = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📦 {sc('get batch')}", url=f"https://t.me/{client.username}?start=batch_{batch_id}")]
        ])
        
        await message.reply_text(batch_text, reply_markup=batch_button)
