# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.filters import Filter
import re
from bot import Bot   # IMPORTANT: use Bot, not Client
from config import OWNER_ID

print("[OK] auto_forward.py LOADED")

# --------------------- ADMIN FILTER ---------------------
class A(Filter):
    async def __call__(self, _, m):
        if m.from_user and m.from_user.id == OWNER_ID:
            return True
        try:
            await m.reply("❌ You can't use this.")
        except:
            pass
        return False

a = A()

# --------------------- DEFAULT CONFIG ---------------------
SRC = -1003442682665
DST = -1003497374537

cfg = {}

# =========================================================
#   AUTO FORWARD NEW MESSAGES (WORKS WITH MULTI-BOT SETUP)
# =========================================================
@Bot.on_message(filters.channel & filters.chat(SRC))
async def fwd_new(c, m: Message):
    print("[TRIGGER] HANDLER TRIGGERED:", m.id, m.chat.id)
    try:
        await m.copy(DST)
    except Exception as e:
        print(f"[AUTO-FWD] Error forwarding {m.id}: {e}")

# =========================================================
#         SET CUSTOM SOURCE & DESTINATION (OWNER ONLY)
# =========================================================
@Bot.on_message(filters.command("set_forward_config") & filters.private & a)
async def set_cfg(c, m: Message):
    x = m.text.split()

    if len(x) != 3:
        return await m.reply(
            "Usage: /set_forward_config source_id destination_id"
        )

    try:
        s = int(x[1])
        d = int(x[2])

        cfg[m.from_user.id] = {"src": s, "dst": d}

        await m.reply(
            f"✅ Forward Config Updated\n"
            f"Source: `{s}`\n"
            f"Destination: `{d}`"
        )

    except Exception as e:
        await m.reply(f"⚠️ Error: `{e}`")


# =========================================================
#                  MANUAL OLD MESSAGE FORWARD
# =========================================================
@Bot.on_message(filters.command("forward_old") & filters.private & a)
async def fwd_old(c, m: Message):

    x = m.text.split()

    if len(x) < 3:
        return await m.reply(
            "Usage:\n"
            "`/forward_old start_msg_id end_msg_id`\n"
            "or\n"
            "`/forward_old https://t.me/c/ID/100 https://t.me/c/ID/110`"
        )

    def get_id(v):
        m_ = re.search(r"/([0-9]+)$", v)
        return int(m_.group(1)) if m_ else int(v)

    try:
        s = get_id(x[1])
        e = get_id(x[2])

        if s > e:
            return await m.reply("⚠️ Start ID must be <= End ID.")

        u = m.from_user.id
        c_ = cfg.get(u, {"src": SRC, "dst": DST})

        src = c_["src"]
        dst = c_["dst"]

        await m.reply(
            f"🔄 Forwarding `{s}` → `{e}`\n"
            f"From `{src}` → `{dst}`"
        )

        for msg_id in range(s, e + 1):
            try:
                msg = await c.get_messages(src, msg_id)
                await msg.copy(dst)

            except Exception as ex:
                print(f"[OLD-FWD] Failed {msg_id}: {ex}")

        await m.reply("✅ Done!")

    except Exception as e:
        await m.reply(f"⚠️ Error: `{e}`")
        await m.reply(f"⚠️ Error: {e}")

