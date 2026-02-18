# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

from aiohttp import web
import asyncio
import time
from plugins import web_server

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import PeerIdInvalid, ChannelInvalid, RPCError
import sys
from datetime import datetime
from config import LOGGER, PORT, OWNER_ID
from helper import MongoDB
from helper.enhanced_credit_db import EnhancedCreditDB

version = "v1.0.0"


class Bot(Client):
    def __init__(self, session, workers, db, fsub, token, admins, messages, auto_del, db_uri, db_name, api_id, api_hash, protect, disable_btn):
        super().__init__(
            name=session,
            api_hash=api_hash,
            api_id=api_id,
            plugins={
                "root": "plugins"
            },
            workers=workers,
            bot_token=token
        )
        self.LOGGER = LOGGER
        self.name = session
        self.db = db
        self.fsub = fsub
        self.owner = OWNER_ID
        self.fsub_dict = {}
        self.admins = admins + [OWNER_ID] if OWNER_ID not in admins else admins
        self.messages = messages
        self.auto_del = auto_del
        self.protect = protect
        self.req_fsub = {}
        self.disable_btn = disable_btn
        self.reply_text = messages.get('REPLY', 'Do not send any useless message in the bot.')
        self.mongodb = MongoDB(db_uri, db_name)
        self.db_uri = db_uri  # Store for EnhancedCreditDB
        self.db_name = db_name  # Store for EnhancedCreditDB
        self.req_channels = []
    
    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()
        if len(self.fsub) > 0:
            for channel in self.fsub:
                try:
                    chat = await self.get_chat(channel[0])
                    name = chat.title
                    link = None
                    if not channel[1]:
                        link = chat.invite_link
                    if not link and not channel[2]:
                        chat_link = await self.create_chat_invite_link(channel[0], creates_join_request=channel[1])
                        link = chat_link.invite_link
                    if not channel[1]:
                        self.fsub_dict[channel[0]] = [name, link, False, 0]
                    if channel[1]:
                        self.fsub_dict[channel[0]] = [name, link, True, 0]
                        self.req_channels.append(channel[0])
                    if channel[2] > 0:
                        self.fsub_dict[channel[0]] = [name, None, channel[1], channel[2]]
                except Exception as e:
                    self.LOGGER(__name__, self.name).warning("Bot can't Export Invite link from Force Sub Channel!")
                    self.LOGGER(__name__, self.name).warning("\nBot Stopped.")
                    await self.stop()
                    return
            await self.mongodb.set_channels(self.req_channels)

        # -----------------------
        # Robust DB channel check
        # -----------------------
        try:
            db_channel = None
            # Try to fetch chat with a few retries to avoid PEER_ID_INVALID cache issues
            for attempt in range(3):
                try:
                    db_channel = await self.get_chat(self.db)
                    break
                except (PeerIdInvalid, ChannelInvalid) as e:
                    self.LOGGER(__name__, self.name).warning(
                        f"Attempt {attempt+1}/3 to load DB channel ({self.db}) failed: {e}"
                    )
                    # short delay to allow Telegram caches to update or propagation after adding bot
                    await asyncio.sleep(1)
                except RPCError as rpc_e:
                    self.LOGGER(__name__, self.name).warning(
                        f"RPC error while getting DB channel ({self.db}): {rpc_e}"
                    )
                    await asyncio.sleep(1)
            if not db_channel:
                # final failure: give clear guidance and stop this bot instance gracefully
                self.LOGGER(__name__, self.name).warning(
                    f"Unable to load DB channel after retries. Check that the bot is added to the channel and the ID is correct. Current value: {self.db}"
                )
                self.LOGGER(__name__, self.name).info("\nBot Stopped. Join https://t.me/Mortal_realm for support")
                await self.stop()
                return

            self.db_channel = db_channel
            self.db_channel_id = db_channel.id  # Store for auto-batch

            # Try sending test message with a couple retries (transient network/API issues can cause failures)
            test = None
            for attempt in range(3):
                try:
                    test = await self.send_message(chat_id=db_channel.id, text="Testing Message by @GPGMS0")
                    # if succeeded, break out
                    break
                except (PeerIdInvalid, ChannelInvalid) as e:
                    self.LOGGER(__name__, self.name).warning(
                        f"Attempt {attempt+1}/3 to send test to DB channel ({self.db}) failed: {e}"
                    )
                    await asyncio.sleep(1)
                except RPCError as rpc_e:
                    self.LOGGER(__name__, self.name).warning(
                        f"RPC error while sending test message to DB channel ({self.db}): {rpc_e}"
                    )
                    await asyncio.sleep(1)
                except Exception as other_e:
                    self.LOGGER(__name__, self.name).warning(
                        f"Unexpected error while sending test message to DB channel ({self.db}): {other_e}"
                    )
                    await asyncio.sleep(1)

            if not test:
                self.LOGGER(__name__, self.name).warning(
                    f"Failed to send test message to DB channel ({self.db}) after retries."
                )
                self.LOGGER(__name__, self.name).warning(
                    f"Make sure the bot is actually a member/admin of the channel and has permission to send messages. Current value: {self.db}"
                )
                self.LOGGER(__name__, self.name).info("\nBot Stopped. Join https://t.me/Mortal_realm for support")
                await self.stop()
                return

            # cleanup test message
            try:
                await test.delete()
            except Exception:
                # ignore deletion errors (permissions may differ), but continue
                pass

        except Exception as e:
            # fallback catch-all: log and stop gracefully
            self.LOGGER(__name__, self.name).warning(e)
            self.LOGGER(__name__, self.name).warning(
                f"Make Sure bot is Admin in DB Channel, and Double check the database channel Value, Current Value {self.db}"
            )
            self.LOGGER(__name__, self.name).info("\nBot Stopped. Join https://t.me/Mortal_realm for support")
            await self.stop()
            return

        # -----------------------
        # End DB channel check
        # -----------------------

        self.LOGGER(__name__, self.name).info("Bot Started!!")
        
        self.username = usr_bot_me.username
        
        # 🔐 Ensure MongoDB indexes for hybrid token system
        try:
            await self.mongodb.ensure_token_indexes()
            self.LOGGER(__name__, self.name).info("Token indexes ensured.")
        except Exception as e:
            self.LOGGER(__name__, self.name).warning(f"Failed to create token indexes: {e}")
        
        try:
            asyncio.create_task(self._broadcast_ttl_worker())
            asyncio.create_task(self._credit_expiry_worker())
        except Exception as e:
            self.LOGGER(__name__, self.name).warning(f"Failed to start background workers: {e}")


    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__, self.name).info("Bot stopped.")

    async def _broadcast_ttl_worker(self):
        """Periodically checks MongoDB for due broadcast TTL jobs and deletes messages."""
        while True:
            try:
                now_ts = int(time.time())
                jobs = await self.mongodb.get_due_broadcast_jobs(now_ts, limit=200)
                if not jobs:
                    await asyncio.sleep(5)
                    continue
                for job in jobs:
                    chat_id = job.get('chat_id')
                    msg_id = job.get('message_id')
                    job_id = job.get('_id')
                    try:
                        await self.delete_messages(chat_id=chat_id, message_ids=msg_id)
                    except Exception as e:
                        self.LOGGER(__name__, self.name).warning(f"TTL delete failed for {chat_id}/{msg_id}: {e}")
                    finally:
                        try:
                            await self.mongodb.remove_broadcast_job(job_id)
                        except Exception as ex:
                            self.LOGGER(__name__, self.name).warning(f"Failed to remove TTL job {job_id}: {ex}")
                await asyncio.sleep(1)
            except Exception as loop_err:
                self.LOGGER(__name__, self.name).warning(f"TTL worker error: {loop_err}")
                await asyncio.sleep(5)
    
    async def _credit_expiry_worker(self):
        """Periodically checks and removes expired credits"""
        while True:
            try:
                from helper.enhanced_credit_db import EnhancedCreditDB
                enhanced_db = EnhancedCreditDB(self.db_uri, self.db_name)
                
                # Cleanup expired credits every hour
                count = await enhanced_db.cleanup_all_expired()
                if count > 0:
                    self.LOGGER(__name__, self.name).info(f"Credit expiry cleanup: removed {count} expired accounts")
                
                # Check for credits expiring in 24 hours and warn users
                expiring_soon = await enhanced_db.get_expiring_soon(hours=24)
                for user_data in expiring_soon:
                    user_id = user_data["_id"]
                    balance = user_data.get("balance", 0)
                    expiry = user_data.get("expiry")
                    
                    if expiry:
                        try:
                            from helper.font_converter import sc
                            await self.send_message(
                                user_id,
                                f"⚠️ **{sc('credit expiry warning')}!**\\n\\n"
                                f"{sc('your')} **{balance} {sc('credits')}** {sc('will expire soon')}!\\n"
                                f"⏰ {sc('expires')}: {expiry.strftime('%Y-%m-%d %H:%M')}\\n\\n"
                                f"{sc('use them before they expire')}!"
                            )
                        except:
                            pass
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
            except Exception as loop_err:
                self.LOGGER(__name__, self.name).warning(f"Credit expiry worker error: {loop_err}")
                await asyncio.sleep(300)  # 5 minutes on error


async def web_app():
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
