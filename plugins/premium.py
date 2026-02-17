# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime, timedelta
from helper.font_converter import to_small_caps as sc
from config import OWNER_ID


# ===============================
#  PREMIUM PRICING PANEL
# ===============================
@Client.on_message(filters.private & filters.command("premium"))
async def premium_command(client: Client, message: Message):
    """Show premium plans"""
    await show_premium_panel(client, message)

@Client.on_callback_query(filters.regex("^premium_panel$"))
async def premium_panel_callback(client: Client, query: CallbackQuery):
    """Show premium panel from callback"""
    await show_premium_panel(client, query.message, is_edit=True)

async def show_premium_panel(client: Client, message: Message, is_edit: bool = False):
    """Display premium pricing panel"""
    
    msg = f"""<blockquote>**💎 {sc('premium membership')}:**</blockquote>

• {sc('which plan do you want to buy')}?

**📜 {sc('pricing')}:**
╭──────────
↻ ₹99 / $1 : 1 {sc('month')}
↻ ₹179 / $2 : 2 {sc('months')}
↻ ₹249 / $3 : 3 {sc('months')} ({sc('most bought')})
↻ ₹399 / $6 : 6 {sc('months')}
↻ ₹699 / $10 : 9 {sc('months')}
↻ ₹999 / $12 : 12 {sc('months')}
╰──────────

**✨ {sc('premium benefits')}:**
• {sc('no ads or verification')}
• {sc('unlimited downloads')}
• {sc('priority support')}
• {sc('early access to new features')}

{sc('contact here for further inquiry')}"""

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💬 {sc('send hi/hello in chat')}", url=f"tg://user?id={OWNER_ID}")],
        [InlineKeyboardButton(f"🔙 {sc('back')}", callback_data="home")]
    ])
    
    if is_edit:
        await message.edit_text(msg, reply_markup=buttons)
    else:
        await message.reply(msg, reply_markup=buttons)


# ===============================
#  ADD PREMIUM
# ===============================
@Client.on_message(filters.private & filters.command("addpremium"))
async def add_premium_command(client: Client, message: Message):

    if message.from_user.id not in client.admins:
        return await message.reply("❌ You are not authorized to use this command!")

    parts = message.text.split()

    if len(parts) < 2:
        return await message.reply(
            "❌ Usage:\n"
            "`/addpremium <user_id> [days]`\n"
            "`/addpremium 123456789 30`"
        )

    try:
        target_user_id = int(parts[1])
    except:
        return await message.reply("❌ Invalid USER ID")

    expire_date = None
    days_text = "Permanent"

    if len(parts) >= 3:
        try:
            days = int(parts[2])
            expire_date = datetime.now() + timedelta(days=days)
            days_text = f"{days} days"
        except:
            return await message.reply("❌ Invalid day value")

    await client.mongodb.add_premium(target_user_id, expire_date)

    reply_text = (
        f"✅ **Premium Added Successfully!**\n\n"
        f"👤 **User ID:** `{target_user_id}`\n"
        f"⏳ **Duration:** {days_text}\n"
    )

    if expire_date:
        reply_text += f"📅 **Expires:** `{expire_date.strftime('%Y-%m-%d %H:%M:%S')}`"
    else:
        reply_text += "♾ **Lifetime Premium**"

    await message.reply(reply_text)

    try:
        await client.send_message(
            target_user_id,
            f"🎉 **You are now PREMIUM!**\n\n"
            f"⏳ Duration: {days_text}\n"
            f"{'📅 Expiry: ' + expire_date.strftime('%Y-%m-%d %H:%M:%S') if expire_date else '♾ Lifetime'}\n\n"
            f"💎 Benefits:\n"
            f"• Direct file access\n"
            f"• No shortener\n"
            f"• Fast support"
        )
    except:
        pass


# ===============================
#  REMOVE PREMIUM
# ===============================
@Client.on_message(filters.private & filters.command("removepremium"))
async def remove_premium_command(client: Client, message: Message):

    if message.from_user.id not in client.admins:
        return await message.reply("❌ You are not authorized")

    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply("❌ Usage: `/removepremium <user_id>`")

    try:
        target_user_id = int(parts[1])
    except:
        return await message.reply("❌ Invalid USER ID")

    await client.mongodb.remove_premium(target_user_id)

    await message.reply(f"🗑 Premium removed for `{target_user_id}`")

    try:
        await client.send_message(
            target_user_id,
            "⚠️ **Your Premium Was Removed**\n"
            "Contact admin if this is a mistake."
        )
    except:
        pass


# ===============================
#  CHECK ANY USER
# ===============================
@Client.on_message(filters.private & filters.command("checkpremium"))
async def check_premium(client: Client, message: Message):

    parts = message.text.split()

    if message.from_user.id in client.admins and len(parts) >= 2:
        try:
            target = int(parts[1])
        except:
            return await message.reply("❌ Invalid ID")
    else:
        target = message.from_user.id

    is_premium = await client.mongodb.is_premium(target)
    data = await client.mongodb.user_data.find_one({"_id": target})

    if not is_premium:
        return await message.reply(f"❌ `{target}` is NOT premium")

    expire = data.get("premium_expire")

    await message.reply(
        f"💎 **PREMIUM ACTIVE**\n"
        f"👤 `{target}`\n"
        f"⏳ Expiry: `{expire.strftime('%Y-%m-%d %H:%M:%S') if expire else '♾ Lifetime'}`"
    )


# ===============================
#  CHECK SELF
# ===============================
@Client.on_message(filters.private & filters.command("mypremium"))
async def my_premium(client: Client, message: Message):

    uid = message.from_user.id

    is_premium = await client.mongodb.is_premium(uid)
    data = await client.mongodb.user_data.find_one({"_id": uid})

    if not is_premium:
        return await message.reply("❌ You are NOT premium.")

    expire = data.get("premium_expire")

    await message.reply(
        f"💎 **Your Premium Status**\n"
        f"⏳ Expiry: `{expire.strftime('%Y-%m-%d %H:%M:%S') if expire else '♾ Lifetime'}`"
    )


# ===============================
#  LIST PREMIUM USERS
# ===============================
@Client.on_message(filters.private & filters.command("premiumusers"))
async def premium_users(client: Client, message: Message):

    if message.from_user.id not in client.admins:
        return await message.reply("❌ You are not authorized")

    users = await client.mongodb.get_premium_users()

    if not users:
        return await message.reply("📭 No premium users found")

    now = datetime.now()
    text = f"💎 **PREMIUM USERS ({len(users)})**\n\n"

    for i, uid in enumerate(users, 1):
        data = await client.mongodb.user_data.find_one({"_id": uid})
        exp = data.get("premium_expire")
        left = (exp - now).days if exp else "∞"
        text += f"**{i}.** `{uid}` — {left} days left\n"

    await message.reply(text)
