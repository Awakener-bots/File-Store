# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

# ============================================================================
# SECURITY & TOKEN MANAGEMENT PANEL
# ============================================================================

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.font_converter import to_small_caps as sc
from datetime import datetime

@Client.on_callback_query(filters.regex("^security_panel$"))
async def security_panel(client, query):
    """Security and token management panel"""
    if query.from_user.id not in client.admins:
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴀᴄᴄᴇꜱꜱ ᴛʜɪꜱ!", show_alert=True)
    
    # Get credit system status
    credit_enabled = await client.mongodb.is_credit_system_enabled()
    credit_status = "🟢 ᴇɴᴀʙʟᴇᴅ" if credit_enabled else "🔴 ᴅɪꜱᴀʙʟᴇᴅ"
    
    # Get token verification status
    token_enabled = await client.mongodb.get_bot_config('token_verification_enabled', True)
    token_status = "🟢 ᴇɴᴀʙʟᴇᴅ" if token_enabled else "🔴 ᴅɪꜱᴀʙʟᴇᴅ"
    
    # Get token expiry time
    token_expiry = await client.mongodb.get_bot_config('token_expiry_minutes', 10)
    
    msg = f"""**🔒 {sc('security & token management')}**

**💳 {sc('credit system')}:** {credit_status}
**🛡️ {sc('token verification')}:** {token_status}
**⏱️ {sc('token expiry')}:** {token_expiry} ᴍɪɴᴜᴛᴇꜱ
**🚫 {sc('auto-ban threshold')}:** 5 ᴀᴛᴛᴇᴍᴘᴛꜱ

{sc('use the buttons below to manage security settings')}:"""
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💳 {'ᴅɪꜱᴀʙʟᴇ' if credit_enabled else 'ᴇɴᴀʙʟᴇ'} ᴄʀᴇᴅɪᴛꜱ", "toggle_credits")],
        [InlineKeyboardButton("⚙️ ᴛᴏᴋᴇɴ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ", "token_management")],
        [InlineKeyboardButton("📈 ꜱʜᴏʀᴛᴇɴᴇʀ ꜱᴛᴀᴛꜱ", "shortener_stats"), InlineKeyboardButton("📊 ʙʏᴘᴀꜱꜱ ꜱᴛᴀᴛꜱ", "bypass_stats")],
        [InlineKeyboardButton("🗑️ ᴄʟᴇᴀʀ ʙʏᴘᴀꜱꜱ ʟᴏɢꜱ", "clear_bypass_logs")],
        [InlineKeyboardButton("◂ ʙᴀᴄᴋ", "settings")]
    ])
    
    try:
        await query.message.edit_text(msg, reply_markup=buttons)
    except Exception:
        pass  # Ignore if message is the same

@Client.on_callback_query(filters.regex("^toggle_credits$"))
async def toggle_credits(client, query):
    """Toggle credit system on/off"""
    if query.from_user.id not in client.admins:
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
    
    current_status = await client.mongodb.is_credit_system_enabled()
    new_status = not current_status
    await client.mongodb.toggle_credit_system(new_status)
    
    status_text = "ᴇɴᴀʙʟᴇᴅ" if new_status else "ᴅɪꜱᴀʙʟᴇᴅ"
    await query.answer(f"💳 ᴄʀᴇᴅɪᴛ ꜱʏꜱᴛᴇᴍ {status_text}!", show_alert=True)
    
    # Refresh panel
    await security_panel(client, query)

# ============================================================================
# TOKEN MANAGEMENT PANEL
# ============================================================================

@Client.on_callback_query(filters.regex("^token_management$"))
async def token_management(client, query):
    """Token management panel"""
    if query.from_user.id not in client.admins:
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴀᴄᴄᴇꜱꜱ ᴛʜɪꜱ!", show_alert=True)
    
    # Get current settings
    token_enabled = await client.mongodb.get_bot_config('token_verification_enabled', True)
    token_expiry = await client.mongodb.get_bot_config('token_expiry_minutes', 10)
    
    status_emoji = "🟢" if token_enabled else "🔴"
    status_text = "ᴇɴᴀʙʟᴇᴅ" if token_enabled else "ᴅɪꜱᴀʙʟᴇᴅ"
    
    msg = f"""**⚙️ {sc('token management')}**

**ꜱᴛᴀᴛᴜꜱ:** {status_emoji} {status_text}
**ᴄᴜʀʀᴇɴᴛ ᴇxᴘɪʀʏ:** {token_expiry} ᴍɪɴᴜᴛᴇꜱ

{sc('configure token verification settings')}:"""
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🛡️ {'ᴅɪꜱᴀʙʟᴇ' if token_enabled else 'ᴇɴᴀʙʟᴇ'} ᴛᴏᴋᴇɴꜱ", "toggle_token_verification")],
        [InlineKeyboardButton("⏱️ ꜱᴇᴛ ᴇxᴘɪʀʏ ᴛɪᴍᴇ", "set_token_expiry")],
        [InlineKeyboardButton("◂ ʙᴀᴄᴋ", "security_panel")]
    ])
    
    try:
        await query.message.edit_text(msg, reply_markup=buttons)
    except Exception:
        pass

@Client.on_callback_query(filters.regex("^toggle_token_verification$"))
async def toggle_token_verification(client, query):
    """Toggle token verification on/off"""
    if query.from_user.id not in client.admins:
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
    
    current_status = await client.mongodb.get_bot_config('token_verification_enabled', True)
    new_status = not current_status
    await client.mongodb.set_bot_config('token_verification_enabled', new_status)
    
    status_text = "ᴇɴᴀʙʟᴇᴅ" if new_status else "ᴅɪꜱᴀʙʟᴇᴅ"
    await query.answer(f"🛡️ ᴛᴏᴋᴇɴ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ {status_text}!", show_alert=True)
    
    # Refresh panel
    await token_management(client, query)

@Client.on_callback_query(filters.regex("^set_token_expiry$"))
async def set_token_expiry(client, query):
    """Show token expiry options"""
    if query.from_user.id not in client.admins:
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴀᴄᴄᴇꜱꜱ ᴛʜɪꜱ!", show_alert=True)
    
    current_expiry = await client.mongodb.get_bot_config('token_expiry_minutes', 10)
    
    msg = f"""**⏱️ {sc('set token expiry time')}**

**ᴄᴜʀʀᴇɴᴛ:** {current_expiry} ᴍɪɴᴜᴛᴇꜱ

{sc('select new expiry time')}:"""
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("5 ᴍɪɴ", "expiry_5"),
            InlineKeyboardButton("10 ᴍɪɴ", "expiry_10"),
        ],
        [
            InlineKeyboardButton("15 ᴍɪɴ", "expiry_15"),
            InlineKeyboardButton("30 ᴍɪɴ", "expiry_30"),
        ],
        [
            InlineKeyboardButton("1 ʜᴏᴜʀ", "expiry_60"),
            InlineKeyboardButton("2 ʜᴏᴜʀꜱ", "expiry_120"),
        ],
        [InlineKeyboardButton("◂ ʙᴀᴄᴋ", "token_management")]
    ])
    
    try:
        await query.message.edit_text(msg, reply_markup=buttons)
    except Exception:
        pass

@Client.on_callback_query(filters.regex("^expiry_(\d+)$"))
async def update_token_expiry(client, query):
    """Update token expiry time"""
    if query.from_user.id not in client.admins:
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
    
    # Extract minutes from callback data
    minutes = int(query.data.split("_")[1])
    
    # Update in database
    await client.mongodb.set_bot_config('token_expiry_minutes', minutes)
    
    # Show confirmation
    time_text = f"{minutes} ᴍɪɴᴜᴛᴇꜱ" if minutes < 60 else f"{minutes // 60} ʜᴏᴜʀ{'ꜱ' if minutes > 60 else ''}"
    await query.answer(f"⏱️ ᴛᴏᴋᴇɴ ᴇxᴘɪʀʏ ꜱᴇᴛ ᴛᴏ {time_text}!", show_alert=True)
    
    # Go back to token management
    await token_management(client, query)

# ============================================================================
# BYPASS STATISTICS
# ============================================================================

@Client.on_callback_query(filters.regex("^bypass_stats$"))
async def bypass_stats(client, query):
    """Show bypass attempt statistics"""
    if query.from_user.id not in client.admins:
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴠɪᴇᴡ ᴛʜɪꜱ!", show_alert=True)
    
    stats = await client.mongodb.get_bypass_stats()
    
    if not stats:
        msg = f"**📊 {sc('bypass statistics')}**\n\n{sc('no bypass attempts recorded')} ✅"
    else:
        msg = f"**📊 {sc('bypass statistics')}**\n\n{sc('top offenders')}:\n\n"
        
        for i, user_stat in enumerate(stats[:10], 1):
            user_id = user_stat['_id']
            count = user_stat['count']
            last_attempt = user_stat['last_attempt'].strftime("%Y-%m-%d %H:%M")
            
            msg += f"**{i}.** `{user_id}`\n"
            msg += f"   └ {sc('attempts')}: **{count}** | {sc('last')}: {last_attempt}\n\n"
        
        total_attempts = sum(s['count'] for s in stats)
        msg += f"\n**{sc('total attempts')}: {total_attempts}**"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 ʀᴇғʀᴇꜱʜ", "bypass_stats")],
        [InlineKeyboardButton("◂ ʙᴀᴄᴋ", "security_panel")]
    ])
    
    try:
        await query.message.edit_text(msg, reply_markup=buttons)
    except Exception:
        pass  # Ignore if message is the same

@Client.on_callback_query(filters.regex("^shortener_stats$"))
async def shortener_stats(client, query):
    """Show shortener click statistics"""
    if query.from_user.id not in client.admins:
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴠɪᴇᴡ ᴛʜɪꜱ!", show_alert=True)
    
    # Get overall statistics
    stats = await client.mongodb.get_shortener_stats()
    
    # Get top clicked tokens
    top_tokens = await client.mongodb.get_top_clicked_tokens(10)
    
    msg = f"""**📈 {sc('shortener statistics')}**

**📊 {sc('overall stats')}:**
└ {sc('total tokens')}: **{stats['total_tokens']}**
└ {sc('total clicks')}: **{stats['total_clicks']}**
└ {sc('tokens used')}: **{stats['total_used']}**
└ {sc('avg clicks/token')}: **{stats['avg_clicks']:.1f}**

"""
    
    if top_tokens:
        msg += f"**🔥 {sc('top clicked tokens')}:**\n\n"
        for i, token_data in enumerate(top_tokens[:5], 1):
            user_id = token_data['user_id']
            clicks = token_data.get('click_count', 0)
            used = "✅" if token_data.get('used', False) else "⏳"
            
            msg += f"**{i}.** `{user_id}` - {clicks} {sc('clicks')} {used}\n"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 ʀᴇғʀᴇꜱʜ", "shortener_stats")],
        [InlineKeyboardButton("◂ ʙᴀᴄᴋ", "security_panel")]
    ])
    
    try:
        await query.message.edit_text(msg, reply_markup=buttons)
    except Exception:
        pass

@Client.on_callback_query(filters.regex("^clear_bypass_logs$"))
async def clear_bypass_logs(client, query):
    """Clear all bypass logs"""
    if query.from_user.id not in client.admins:
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴅᴏ ᴛʜɪꜱ!", show_alert=True)
    
    # Clear all bypass attempts
    await client.mongodb.bypass_attempts.delete_many({})
    
    await query.answer("🗑️ ᴀʟʟ ʙʏᴘᴀꜱꜱ ʟᴏɢꜱ ᴄʟᴇᴀʀᴇᴅ!", show_alert=True)
    await security_panel(client, query)
