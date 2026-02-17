# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper.enhanced_credit_db import EnhancedCreditDB
from helper.payment import PaymentGateway, get_package_by_id, DEFAULT_PACKAGES
from datetime import datetime
import json

# Load credit configuration from setup.json
try:
    with open("setup.json", "r") as f:
        setup_data = json.load(f)
        credit_config = setup_data[0].get("credit_config", {})
except:
    credit_config = {}

# Initialize payment gateway
payment_gateway = PaymentGateway(credit_config)


# ================================
# USER COMMANDS
# ================================

@Client.on_message(filters.command("credits") & filters.private)
async def check_credits(client: Client, message: Message):
    """Check your credit balance"""
    user_id = message.from_user.id
    
    # Get enhanced credit DB
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    
    # Check for expired credits
    await enhanced_db.check_and_remove_expired(user_id)
    
    # Get credit info
    credit_info = await enhanced_db.get_credits(user_id)
    
    expiry_text = ""
    if credit_info["expiry"]:
        expiry_date = credit_info["expiry"].strftime("%Y-%m-%d %H:%M")
        expiry_text = f"\n⏰ **Expires**: {expiry_date}"
    
    text = (
        f"💳 **Your Credit Balance**\n\n"
        f"💰 **Balance**: {credit_info['balance']} Credits{expiry_text}\n"
        f"📊 **Total Earned**: {credit_info['total_earned']}\n"
        f"📉 **Total Spent**: {credit_info['total_spent']}\n\n"
        f"🎁 **Referrals**: {credit_info['referral_count']} users"
    )
    
    buttons = [
        [InlineKeyboardButton("💰 Buy Credits", callback_data="buy_credits")],
        [InlineKeyboardButton("🎁 Refer & Earn", callback_data="referral_info")],
        [InlineKeyboardButton("📜 Transactions", callback_data="view_transactions")]
    ]
    
    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_message(filters.command("referral") & filters.private)
async def referral_command(client: Client, message: Message):
    """Get your referral link"""
    user_id = message.from_user.id
    
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    
    # Create or get referral code
    referral_code = await enhanced_db.create_referral_code(user_id)
    
    # Get referral stats
    stats = await enhanced_db.get_referral_stats(user_id)
    
    # Create referral link
    referral_link = f"https://t.me/{client.username}?start=ref_{referral_code}"
    
    reward_amount = credit_config.get("referral_reward", 5)
    
    text = (
        f"🎁 **Refer & Earn Credits!**\n\n"
        f"**Your Referral Link**:\n"
        f"`{referral_link}`\n\n"
        f"**How it works**:\n"
        f"1. Share your link with friends\n"
        f"2. They join using your link\n"
        f"3. When they access their first file, you get **{reward_amount} credits**!\n\n"
        f"📊 **Your Stats**:\n"
        f"• Referrals: {stats['referral_count']} users\n"
        f"• Earned: {stats['referral_earnings']} credits"
    )
    
    buttons = [
        [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={referral_link}")],
        [InlineKeyboardButton("🔙 Back", callback_data="credits_menu")]
    ]
    
    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_message(filters.command("buycredits") & filters.private)
async def buy_credits_command(client: Client, message: Message):
    """Buy credits with payment"""
    packages = credit_config.get("packages", DEFAULT_PACKAGES)
    
    text = (
        f"💰 **Buy Credits**\n\n"
        f"Choose a package below:\n"
    )
    
    buttons = []
    for pkg in packages:
        popular = " ⭐" if pkg.get("popular") else ""
        button_text = f"{pkg['credits']} Credits - ₹{pkg['price']}{popular}"
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"buy_pkg_{pkg['id']}")])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="credits_menu")])
    
    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


# ================================
# CALLBACK HANDLERS
# ================================

@Client.on_callback_query(filters.regex("^buy_credits$"))
async def buy_credits_callback(client: Client, query: CallbackQuery):
    """Show credit packages"""
    packages = credit_config.get("packages", DEFAULT_PACKAGES)
    
    text = (
        f"💰 **Buy Credits**\n\n"
        f"Choose a package below:\n"
    )
    
    buttons = []
    for pkg in packages:
        popular = " ⭐" if pkg.get("popular") else ""
        button_text = f"{pkg['credits']} Credits - ₹{pkg['price']}{popular}"
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"buy_pkg_{pkg['id']}")])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="credits_menu")])
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^buy_pkg_"))
async def buy_package_callback(client: Client, query: CallbackQuery):
    """Process package purchase"""
    package_id = query.data.replace("buy_pkg_", "")
    packages = credit_config.get("packages", DEFAULT_PACKAGES)
    package = get_package_by_id(package_id, packages)
    
    if not package:
        await query.answer("Package not found!", show_alert=True)
        return
    
    user_id = query.from_user.id
    
    # Create payment
    payment_details = await payment_gateway.create_payment(user_id, package)
    
    text = payment_details["instructions"]
    
    buttons = []
    if payment_details["method"] == "manual":
        buttons.append([InlineKeyboardButton("✅ I've Paid", callback_data=f"paid_{payment_details['payment_id']}")])
    elif payment_details["method"] == "razorpay":
        buttons.append([InlineKeyboardButton("💳 Pay Now", url=payment_details["payment_link"])])
    elif payment_details["method"] == "telegram_stars":
        # Telegram Stars payment button (requires invoice)
        buttons.append([InlineKeyboardButton("⭐ Pay with Stars", callback_data=f"pay_stars_{package_id}")])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="buy_credits")])
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^referral_info$"))
async def referral_info_callback(client: Client, query: CallbackQuery):
    """Show referral information"""
    user_id = query.from_user.id
    
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    
    # Create or get referral code
    referral_code = await enhanced_db.create_referral_code(user_id)
    
    # Get referral stats
    stats = await enhanced_db.get_referral_stats(user_id)
    
    # Create referral link
    referral_link = f"https://t.me/{client.username}?start=ref_{referral_code}"
    
    reward_amount = credit_config.get("referral_reward", 5)
    
    text = (
        f"🎁 **Refer & Earn Credits!**\n\n"
        f"**Your Referral Link**:\n"
        f"`{referral_link}`\n\n"
        f"**How it works**:\n"
        f"1. Share your link with friends\n"
        f"2. They join using your link\n"
        f"3. When they access their first file, you get **{reward_amount} credits**!\n\n"
        f"📊 **Your Stats**:\n"
        f"• Referrals: {stats['referral_count']} users\n"
        f"• Earned: {stats['referral_earnings']} credits"
    )
    
    buttons = [
        [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={referral_link}")],
        [InlineKeyboardButton("🔙 Back", callback_data="credits_menu")]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^view_transactions$"))
async def view_transactions_callback(client: Client, query: CallbackQuery):
    """View transaction history"""
    user_id = query.from_user.id
    
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    
    transactions = await enhanced_db.get_transactions(user_id, limit=10)
    
    if not transactions:
        text = "📜 **Transaction History**\n\nNo transactions yet."
    else:
        text = "📜 **Transaction History** (Last 10)\n\n"
        
        for trans in transactions:
            trans_type = trans.get("type", "unknown")
            amount = trans.get("amount", 0)
            reason = trans.get("reason", "")
            timestamp = trans.get("timestamp", datetime.now()).strftime("%Y-%m-%d %H:%M")
            
            emoji = {
                "earned": "➕",
                "spent": "➖",
                "referral_reward": "🎁",
                "purchase": "💳",
                "expired": "⏰",
                "reset": "🔄",
                "set": "⚙️"
            }.get(trans_type, "•")
            
            text += f"{emoji} **{trans_type.title()}**: {amount} credits\n"
            text += f"   _{reason}_ - {timestamp}\n\n"
    
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="credits_menu")]]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^credits_menu$"))
async def credits_menu_callback(client: Client, query: CallbackQuery):
    """Show credits main menu"""
    user_id = query.from_user.id
    
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    
    # Check for expired credits
    await enhanced_db.check_and_remove_expired(user_id)
    
    # Get credit info
    credit_info = await enhanced_db.get_credits(user_id)
    
    expiry_text = ""
    if credit_info["expiry"]:
        expiry_date = credit_info["expiry"].strftime("%Y-%m-%d %H:%M")
        expiry_text = f"\n⏰ **Expires**: {expiry_date}"
    
    text = (
        f"💳 **Your Credit Balance**\n\n"
        f"💰 **Balance**: {credit_info['balance']} Credits{expiry_text}\n"
        f"📊 **Total Earned**: {credit_info['total_earned']}\n"
        f"📉 **Total Spent**: {credit_info['total_spent']}\n\n"
        f"🎁 **Referrals**: {credit_info['referral_count']} users"
    )
    
    buttons = [
        [InlineKeyboardButton("💰 Buy Credits", callback_data="buy_credits")],
        [InlineKeyboardButton("🎁 Refer & Earn", callback_data="referral_info")],
        [InlineKeyboardButton("📜 Transactions", callback_data="view_transactions")]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ================================
# ADMIN COMMANDS
# ================================

@Client.on_message(filters.command("addcredit") & filters.private)
async def add_credit(client: Client, message: Message):
    """Admin: Add credits to user"""
    if message.from_user.id not in client.admins:
        return await message.reply("⛔ You are not authorized to use this command.")

    try:
        user_id = int(message.command[1])
        amount = int(message.command[2])
        expiry_days = int(message.command[3]) if len(message.command) > 3 else credit_config.get("expiry_days", 30)
    except:
        return await message.reply(
            "❌ Usage: <code>/addcredit user_id amount [expiry_days]</code>\n"
            "Example: <code>/addcredit 123456789 10 30</code>"
        )

    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    await enhanced_db.add_credits(user_id, amount, expiry_days, reason="admin_added")

    await message.reply(
        f"✅ Added <b>{amount}</b> credits to user <code>{user_id}</code>.\n"
        f"Expires in {expiry_days} days."
    )


@Client.on_message(filters.command("setcredit") & filters.private)
async def set_credit(client: Client, message: Message):
    """Admin: Set exact credit amount"""
    if message.from_user.id not in client.admins:
        return await message.reply("⛔ You are not authorized to use this command.")

    try:
        user_id = int(message.command[1])
        amount = int(message.command[2])
        expiry_days = int(message.command[3]) if len(message.command) > 3 else credit_config.get("expiry_days", 30)
    except:
        return await message.reply(
            "❌ Usage: <code>/setcredit user_id amount [expiry_days]</code>\n"
            "Example: <code>/setcredit 123456789 50 30</code>"
        )

    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    await enhanced_db.set_credits(user_id, amount, expiry_days)

    await message.reply(
        f"✅ Set credits for user <code>{user_id}</code> to <b>{amount}</b>.\n"
        f"Expires in {expiry_days} days."
    )


@Client.on_message(filters.command("removecredit") & filters.private)
async def remove_credit(client: Client, message: Message):
    """Admin: Remove all credits from user"""
    if message.from_user.id not in client.admins:
        return await message.reply("⛔ You are not authorized to use this command.")

    try:
        user_id = int(message.command[1])
    except:
        return await message.reply("❌ Usage: <code>/removecredit user_id</code>")

    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    await enhanced_db.reset_credits(user_id)

    await message.reply(f"🗑️ All credits removed for user <code>{user_id}</code>.")


@Client.on_message(filters.command("listcredits") & filters.private)
async def list_credits(client: Client, message: Message):
    """Admin: List all users with credits"""
    if message.from_user.id not in client.admins:
        return await message.reply("⛔ You are not authorized to use this command.")

    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    users = await enhanced_db.get_all_users_with_credits()

    if not users:
        return await message.reply("📭 No users have credits currently.")

    text = f"💳 **Users with Credits** ({len(users)} total)\n\n"
    
    for user in users[:20]:  # Show first 20
        user_id = user["_id"]
        balance = user.get("balance", 0)
        expiry = user.get("expiry")
        expiry_text = f" (Expires: {expiry.strftime('%Y-%m-%d')})" if expiry else ""
        
        text += f"• <code>{user_id}</code>: {balance} credits{expiry_text}\n"
    
    if len(users) > 20:
        text += f"\n... and {len(users) - 20} more users"

    await message.reply(text)


@Client.on_message(filters.command("creditstats") & filters.private)
async def credit_stats(client: Client, message: Message):
    """Admin: View credit statistics"""
    if message.from_user.id not in client.admins:
        return await message.reply("⛔ You are not authorized to use this command.")

    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    stats = await enhanced_db.get_credit_statistics()

    text = (
        f"📊 **Credit System Statistics**\n\n"
        f"👥 **Total Users**: {stats['total_users']}\n"
        f"💰 **Total Balance**: {stats['total_balance']} credits\n"
        f"📈 **Total Earned**: {stats['total_earned']} credits\n"
        f"📉 **Total Spent**: {stats['total_spent']} credits\n"
        f"🎁 **Total Referrals**: {stats['total_referrals']}\n"
    )

    await message.reply(text)


@Client.on_message(filters.command("approvepayment") & filters.private)
async def approve_payment(client: Client, message: Message):
    """Admin: Approve manual payment"""
    if message.from_user.id not in client.admins:
        return await message.reply("⛔ You are not authorized to use this command.")

    try:
        payment_id = message.command[1]
    except:
        return await message.reply("❌ Usage: <code>/approvepayment payment_id</code>")

    # Verify payment
    result = await payment_gateway.verify_payment(payment_id)
    
    if not result.get("success"):
        return await message.reply(f"❌ {result.get('error', 'Payment not found')}")

    # Add credits to user
    user_id = result["user_id"]
    package = result["package"]
    
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    expiry_days = credit_config.get("expiry_days", 30)
    await enhanced_db.add_credits(user_id, package["credits"], expiry_days, reason=f"purchase_{payment_id}")

    # Approve payment
    await payment_gateway.approve_payment(payment_id)

    # Notify user
    try:
        await client.send_message(
            user_id,
            f"✅ **Payment Approved!**\n\n"
            f"💰 **{package['credits']} credits** have been added to your account!\n"
            f"⏰ Expires in {expiry_days} days\n\n"
            f"Use /credits to check your balance."
        )
    except:
        pass

    await message.reply(
        f"✅ Payment approved!\n"
        f"Added {package['credits']} credits to user <code>{user_id}</code>"
    )
