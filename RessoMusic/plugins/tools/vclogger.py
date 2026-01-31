import asyncio
from logging import getLogger
from typing import Dict, Set
import random

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.raw import functions

# --- Project Imports ---
from RessoMusic import app
# Note: Ye line check kar lena, agar tere bot me get_assistant alag jagah hai to path badal dena
from RessoMusic.utils.database import get_assistant
from RessoMusic.misc import mongodb, SUDOERS

LOGGER = getLogger(__name__)

# --- DATABASE SETUP ---
vcloggerdb = mongodb.vclogger
vc_active_users: Dict[int, Set[int]] = {}
active_vc_chats: Set[int] = set()
vc_logging_status: Dict[int, bool] = {}

prefixes = ["/", "!", ".", ",", "?", "@", "#"]

# --- HELPER: ADMIN CHECK (Old Version Safe) ---
async def is_admin(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        # Using Strings instead of Enums for Old Version Compatibility
        if member.status in ["creator", "administrator"]:
            return True
    except:
        pass
    return False

# --- DATABASE FUNCTIONS ---
async def load_vc_logger_status():
    try:
        cursor = vcloggerdb.find({})
        enabled_chats = []
        async for doc in cursor:
            chat_id = doc["chat_id"]
            status = doc["status"]
            vc_logging_status[chat_id] = status
            if status:
                enabled_chats.append(chat_id)
        
        for chat_id in enabled_chats:
            asyncio.create_task(check_and_monitor_vc(chat_id))
        
        LOGGER.info(f"Loaded VC logger for {len(enabled_chats)} chats.")
    except Exception as e:
        LOGGER.error(f"Error loading VC logger: {e}")

async def save_vc_logger_status(chat_id: int, status: bool):
    try:
        await vcloggerdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "status": status}},
            upsert=True
        )
    except Exception as e:
        LOGGER.error(f"Error saving VC logger: {e}")

async def get_vc_logger_status(chat_id: int) -> bool:
    if chat_id in vc_logging_status:
        return vc_logging_status[chat_id]
    try:
        doc = await vcloggerdb.find_one({"chat_id": chat_id})
        if doc:
            status = doc["status"]
            vc_logging_status[chat_id] = status
            return status
    except:
        pass
    return False

# --- SMALL CAPS HELPER ---
def to_small_caps(text):
    mapping = {
        "a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ꜰ","g":"ɢ","h":"ʜ","i":"ɪ","j":"ᴊ",
        "k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ","o":"ᴏ","p":"ᴘ","q":"ǫ","r":"ʀ","s":"s","t":"ᴛ",
        "u":"ᴜ","v":"ᴠ","w":"ᴡ","x":"x","y":"ʏ","z":"ᴢ"
    }
    return "".join(mapping.get(c, c) for c in text.lower())

# --- COMMAND: /vclogger ---
@app.on_message(filters.command(["vclogger", "vclog"], prefixes=prefixes) & filters.group)
async def vclogger_command(_, message: Message):
    chat_id = message.chat.id
    
    # Check Admin
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ You are not an Admin.")

    args = message.text.split()
    status = await get_vc_logger_status(chat_id)
    
    status_text = "ENABLED" if status else "DISABLED"

    if len(args) == 1:
        await message.reply_text(
            f"📌 **VC Logger Status:** `{status_text}`\n\n"
            f"**Usage:**\n`/vclogger on` - Enable\n`/vclogger off` - Disable"
        )
    elif len(args) >= 2:
        arg = args[1].lower()
        if arg in ["on", "enable", "yes"]:
            vc_logging_status[chat_id] = True
            await save_vc_logger_status(chat_id, True)
            await message.reply_text(f"✅ **VC Logging Enabled!**\nI will now notify when someone joins/leaves.")
            asyncio.create_task(check_and_monitor_vc(chat_id))
        
        elif arg in ["off", "disable", "no"]:
            vc_logging_status[chat_id] = False
            await save_vc_logger_status(chat_id, False)
            await message.reply_text(f"🚫 **VC Logging Disabled.**")
            active_vc_chats.discard(chat_id)
            vc_active_users.pop(chat_id, None)
        else:
            await message.reply_text("❌ Use `on` or `off`.")

# --- VC PARTICIPANT FETCHER (RAW) ---
async def get_group_call_participants(userbot, peer):
    try:
        full_chat = await userbot.invoke(functions.channels.GetFullChannel(channel=peer))
        if not hasattr(full_chat.full_chat, 'call') or not full_chat.full_chat.call:
            return []
        
        call = full_chat.full_chat.call
        participants = await userbot.invoke(functions.phone.GetGroupParticipants(
            call=call, ids=[], sources=[], offset="", limit=100
        ))
        return participants.participants
    except Exception as e:
        # Handling FloodWait
        if "420" in str(e):
            await asyncio.sleep(5)
            return await get_group_call_participants(userbot, peer)
        return []

# --- MONITORING LOOP ---
async def monitor_vc_chat(chat_id):
    userbot = await get_assistant(chat_id)
    if not userbot:
        return

    while chat_id in active_vc_chats and await get_vc_logger_status(chat_id):
        try:
            peer = await userbot.resolve_peer(chat_id)
            participants_list = await get_group_call_participants(userbot, peer)
            
            new_users = set()
            for p in participants_list:
                # Raw Update handling
                if hasattr(p, 'peer') and hasattr(p.peer, 'user_id'):
                    new_users.add(p.peer.user_id)

            current_users = vc_active_users.get(chat_id, set())
            joined = new_users - current_users
            left = current_users - new_users

            if joined or left:
                tasks = []
                for user_id in joined:
                    tasks.append(handle_user_join(chat_id, user_id, userbot))
                for user_id in left:
                    tasks.append(handle_user_leave(chat_id, user_id, userbot))
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

            vc_active_users[chat_id] = new_users

        except Exception as e:
            pass # Silent fail to avoid log spam

        await asyncio.sleep(5)

async def check_and_monitor_vc(chat_id):
    if not await get_vc_logger_status(chat_id):
        return
    
    # Check if assistant exists
    try:
        userbot = await get_assistant(chat_id)
        if not userbot: return
    except:
        return

    try:
        if chat_id not in active_vc_chats:
            active_vc_chats.add(chat_id)
            asyncio.create_task(monitor_vc_chat(chat_id))
    except Exception as e:
        LOGGER.error(f"Error check_and_monitor_vc: {e}")

# --- NOTIFICATION HANDLERS ---
def get_stop_button():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔕 ᴅɪsᴀʙʟᴇ ʟᴏɢs", callback_data="stop_vclogger")]]
    )

async def handle_user_join(chat_id, user_id, userbot):
    try:
        user = await userbot.get_users(user_id)
        name = user.first_name or "User"
        mention = f"[{name}](tg://user?id={user_id})"
        
        msg = f"🎤 {mention} **joined the Voice Chat!**"
        
        sent_msg = await app.send_message(chat_id, msg, reply_markup=get_stop_button())
        asyncio.create_task(delete_after_delay(sent_msg, 10))
    except Exception as e:
        pass

async def handle_user_leave(chat_id, user_id, userbot):
    try:
        user = await userbot.get_users(user_id)
        name = user.first_name or "User"
        mention = f"[{name}](tg://user?id={user_id})"
        
        msg = f"👋 {mention} **left the Voice Chat.**"
        
        sent_msg = await app.send_message(chat_id, msg, reply_markup=get_stop_button())
        asyncio.create_task(delete_after_delay(sent_msg, 10))
    except Exception as e:
        pass

async def delete_after_delay(message, delay):
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except:
        pass

# --- CALLBACK: DISABLE BUTTON ---
@app.on_callback_query(filters.regex("stop_vclogger"))
async def stop_vclogger_callback(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if not await is_admin(chat_id, user_id):
        return await query.answer("❌ You are not an admin!", show_alert=True)

    vc_logging_status[chat_id] = False
    await save_vc_logger_status(chat_id, False)
    active_vc_chats.discard(chat_id)
    vc_active_users.pop(chat_id, None)

    await query.answer("✅ VC Logging Disabled!", show_alert=True)
    await query.message.edit_text(
        f"🚫 **VC Logging has been disabled by {query.from_user.mention}.**"
    )

# --- INITIALIZE ---
async def initialize_vc_logger():
    await load_vc_logger_status()

# Start Logic (Standard for Music Bots)
loop = asyncio.get_event_loop()
loop.create_task(initialize_vc_logger())

