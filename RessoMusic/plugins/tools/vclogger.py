import asyncio
from logging import getLogger
from typing import Dict, Set
import random
from html import escape # Name safe karne ke liye

from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.raw import functions

# --- Project Imports ---
from RessoMusic import app
from RessoMusic.utils.database import get_assistant
from RessoMusic.misc import mongodb, SUDOERS

LOGGER = getLogger(__name__)

# --- DATABASE SETUP ---
vcloggerdb = mongodb.vclogger
vc_active_users: Dict[int, Set[int]] = {}
active_vc_chats: Set[int] = set()
vc_logging_status: Dict[int, bool] = {}

prefixes = ["/", "!", ".", ",", "?", "@", "#"]

# --- HELPER: ADMIN CHECK ---
async def is_admin(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in ["creator", "administrator"]:
            return True
    except:
        pass
    return False

# --- DATABASE FUNCTIONS ---
async def load_vc_logger_status():
    # Sirf unko load karenge jinhone manually "OFF" kiya hai
    # Baaki sabke liye Default ON rahega
    try:
        cursor = vcloggerdb.find({})
        async for doc in cursor:
            chat_id = doc["chat_id"]
            status = doc["status"]
            vc_logging_status[chat_id] = status
            if status:
                asyncio.create_task(check_and_monitor_vc(chat_id))
        
        LOGGER.info(f"Loaded VC logger status.")
    except Exception as e:
        LOGGER.error(f"Error loading VC logger: {e}")

async def save_vc_logger_status(chat_id: int, status: bool):
    try:
        await vcloggerdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "status": status}},
            upsert=True
        )
        vc_logging_status[chat_id] = status
    except Exception as e:
        LOGGER.error(f"Error saving VC logger: {e}")

async def get_vc_logger_status(chat_id: int) -> bool:
    # Logic: Agar Memory mein status hai, to wo return karo
    if chat_id in vc_logging_status:
        return vc_logging_status[chat_id]

    # Database check
    try:
        doc = await vcloggerdb.find_one({"chat_id": chat_id})
        if doc:
            status = doc["status"]
            vc_logging_status[chat_id] = status
            return status
    except:
        pass
    
    # DEFAULT IS ON (Agar database mein kuch nahi mila to TRUE maano)
    return True

# --- COMMAND: /vclogger ---
@app.on_message(filters.command(["vclogger", "vclog"], prefixes=prefixes) & filters.group)
async def vclogger_command(_, message: Message):
    chat_id = message.chat.id
    
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ You are not an Admin.")

    args = message.text.split()
    status = await get_vc_logger_status(chat_id)
    
    status_text = "ENABLED (Default)" if status else "DISABLED"

    if len(args) == 1:
        await message.reply_text(
            f"📌 **VC Logger Status:** `{status_text}`\n\n"
            f"**Usage:**\n`/vclogger on` - Enable\n`/vclogger off` - Disable"
        )
    elif len(args) >= 2:
        arg = args[1].lower()
        if arg in ["on", "enable", "yes"]:
            await save_vc_logger_status(chat_id, True)
            await message.reply_text(f"✅ **VC Logging Enabled!**")
            asyncio.create_task(check_and_monitor_vc(chat_id))
        
        elif arg in ["off", "disable", "no"]:
            await save_vc_logger_status(chat_id, False)
            await message.reply_text(f"🚫 **VC Logging Disabled.**")
            active_vc_chats.discard(chat_id)
            vc_active_users.pop(chat_id, None)
        else:
            await message.reply_text("❌ Use `on` or `off`.")

# --- VC PARTICIPANT FETCHER ---
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
            pass
        await asyncio.sleep(5)

async def check_and_monitor_vc(chat_id):
    # Default ON logic handle karne ke liye yahan check karte hain
    if not await get_vc_logger_status(chat_id):
        return
    
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

# --- BUTTONS & FORMATTING ---

def get_stop_button():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔕 ᴅɪsᴀʙʟᴇ ʟᴏɢs", callback_data="stop_vclogger")]]
    )

# Function to clean bad names
def clean_name_link(name, user_id):
    # 1. HTML Escape (Fixes < > & issues)
    safe_name = escape(name)
    # 2. Limit Length (Agar naam 25 se bada hai to kaat do)
    if len(safe_name) > 25:
        safe_name = safe_name[:25] + "..."
    
    # 3. HTML Link Return
    return f'<a href="tg://user?id={user_id}">{safe_name}</a>'

async def handle_user_join(chat_id, user_id, userbot):
    try:
        user = await userbot.get_users(user_id)
        name = user.first_name or "User"
        
        # New HTML Style Mention (Fixes broken format)
        mention = clean_name_link(name, user_id)
        
        msg = f"🎤 {mention} **joined the Voice Chat!**"
        
        # Parse Mode HTML use kar rahe hain taaki link na tute
        sent_msg = await app.send_message(
            chat_id, 
            msg, 
            reply_markup=get_stop_button(),
            parse_mode=enums.ParseMode.HTML 
        )
        asyncio.create_task(delete_after_delay(sent_msg, 10))
    except Exception as e:
        pass

async def handle_user_leave(chat_id, user_id, userbot):
    try:
        user = await userbot.get_users(user_id)
        name = user.first_name or "User"
        
        # New HTML Style Mention
        mention = clean_name_link(name, user_id)
        
        msg = f"👋 {mention} **left the Voice Chat.**"
        
        sent_msg = await app.send_message(
            chat_id, 
            msg, 
            reply_markup=get_stop_button(),
            parse_mode=enums.ParseMode.HTML
        )
        asyncio.create_task(delete_after_delay(sent_msg, 10))
    except Exception as e:
        pass

async def delete_after_delay(message, delay):
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except:
        pass

# --- CALLBACK ---
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

# Start Loop
loop = asyncio.get_event_loop()
loop.create_task(initialize_vc_logger())
        
