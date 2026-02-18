<p align="center">
  <img src="https://i.ibb.co/gbVyYG8z/photo-2026-02-17-18-28-50-7607902977038221336.jpg" alt="Advanced File Store Bot Banner" width="100%">
</p>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Montserrat&weight=700&size=28&pause=1200&color=00BFFF&center=true&vCenter=true&width=750&lines=Advanced+File+Sharing+Bot;Premium+%7C+Multi-DB+%7C+Batch+System;Powered+by+Awakeners+Bots" />
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/Awakener_bots/File-Store?style=for-the-badge&color=00BFFF">
  <img src="https://img.shields.io/github/forks/Awakener_bots/File-Store?style=for-the-badge&color=00BFFF">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/MongoDB-Database-green?style=for-the-badge">
</p>

---

# Telegram File Sharing Bot

A powerful Telegram bot for file sharing with advanced features including batch processing, premium memberships, multi-database channel support, URL shortening with token verification, and comprehensive admin controls.

---

## ✨ Features

### Core Features
- 📁 **File Sharing** - Share files via unique links with automatic link generation
- 🔒 **Hybrid Token System** - Secure, random 12-16 char token links with full backward compatibility for legacy Base64 links.
- 📦 **Batch Processing** - Create batches for episodes/seasons with cancel functionality
- 🤖 **Auto Batch** - Automatic batch creation with quality detection and configurable time windows
- 💎 **Premium System** - Full subscription management with pricing tiers and expiry tracking
- 🗄️ **Multi-DB Channels** - Round-robin file distribution across multiple database channels
- 🔗 **URL Shortening** - Integrated URL shortener with multiple provider support

### Admin Features
- 👥 **Premium User Management** - Control panel to add/remove premium users with expiry dates
- 📊 **Statistics Dashboard** - Track bot usage, user stats, and premium subscriptions
- 🔒 **Force Subscribe** - Require channel subscription for file access
- 💳 **Credit System** - Token-based access control with package management
- 🔐 **Security Panel** - Token verification, anti-bypass protection, and bypass logs
- 📢 **Broadcast System** - Send messages to all users or specific groups

### User Experience
- 🎨 **Modern UI** - Small caps font styling with blockquotes for premium look
- ⚡ **Fast Performance** - Optimized file delivery and caching
- 🔔 **Notifications** - Auto-notify users on premium status changes
- 📱 **Mobile Friendly** - Responsive design for all devices

---

## 📋 Requirements

- Python 3.8+
- MongoDB
- Telegram Bot Token (from @BotFather)
- Telegram API ID and Hash (from my.telegram.org)

---

## 🚀 Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Awakener_Bots/file-sharing-bot
cd file-sharing-bot
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Configuration

Create a `config.py` file:

```python
API_ID = 12345678
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

DATABASE_URI = "mongodb://localhost:27017"
DATABASE_NAME = "file_sharing_bot"

DB_CHANNEL = -1001234567890
FORCE_SUB_CHANNELS = []

OWNER_ID = 123456789
ADMINS = [123456789]

PORT = 8080
WEBHOOK = False
```

### 4️⃣ Run the Bot

```bash
python bot.py
```

---

## 📝 Commands

### User Commands
- `/start`
- `/about`
- `/premium`
- `/mypremium`

### Admin Commands
- `/batch`
- `/genlink`
- `/autobatch`
- `/broadcast`
- `/stats`
- `/addpremium <user_id> [days]`
- `/removepremium <user_id>`
- `/settings`

---

## 🗂️ Project Structure

```
file-sharing-bot/
├── bot.py
├── config.py
├── requirements.txt
├── plugins/
├── helper/
└── README.md
```

---

## 👨‍💻 ᴄʀᴇᴅɪᴛs

**ᴅᴇᴠᴇʟᴏᴘᴇʀ**

» [ɢᴘɢ](https://github.com/GPG36)

» [ᴋᴜɴᴀʟ](https://github.com/KunalG932)

**ᴍᴀɪɴᴛᴀɪɴᴇᴅ ʙʏ**  
» [ᴀᴡᴀᴋᴇɴᴇʀs ʙᴏᴛs](https://t.me/Awakeners_Bots)

» [ᴠᴏᴀᴛ](t.me/Awakeners_bots) - [ʙᴀsᴇ ʀᴇᴘᴏ](https://github.com/ArihantSharma/FileStoreBot)
## ⚠️ Disclaimer

This bot is for educational purposes. Ensure compliance with Telegram's Terms of Service and local laws.

---
<p align="center">
  ᴍᴀᴅᴇ ᴡɪᴛʜ ❤️ ʙʏ <a href="https://t.me/Awakeners_Bots">ᴀᴡᴀᴋᴇɴᴇʀs ʙᴏᴛs</a>
</p>

<p align="center">
⭐ Star this repository if you find it helpful!
</p>
