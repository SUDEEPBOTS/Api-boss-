import asyncio
import pytz
from datetime import datetime
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, ChatPermissions
from RessoMusic import app
from RessoMusic.misc import SUDOERS, mongodb
from config import BANNED_USERS

# --- DATABASE SETUP ---
db = mongodb.nightmode

# --- CONFIGURATION ---
TIMEZONE = pytz.timezone("Asia/Kolkata")
LOCK_HOUR = 1   # 1 AM
UNLOCK_HOUR = 6 # 6 AM

# --- PERMISSIONS (SAFE MODE) ---
LOCK_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_polls=False,
    can_invite_users=False,
    can_pin_messages=False
)

UNLOCK_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=False,
    can_send_polls=False,
    can_invite_users=True,
    can_pin_messages=False
)

# --- HELPER: ADMIN CHECK ---
async def is_admin(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except:
        pass
    return False

# --- BACKGROUND SCHEDULER (FIXED) ---
async def night_mode_scheduler():
    while True:
        try:
            now = datetime.now(TIMEZONE)
            current_hour = now.hour
            
            # Logic: 1 AM se 5:59 AM tak LOCK rahega
            should_be_locked = LOCK_HOUR <= current_hour < UNLOCK_HOUR

            async for doc in db.find({"status": "on"}):
                chat_id = doc["chat_id"]
                last_action = doc.get("last_action", "none")

                try:
                    if should_be_locked and last_action != "locked":
                        # --- ATTEMPT LOCK ---
                        await app.set_chat_permissions(chat_id, LOCK_PERMISSIONS)
                        await app.send_message(chat_id, "🔐 **Night Mode Active**\n\nGroup is locked until 6:00 AM.")
                        await db.update_one({"chat_id": chat_id}, {"$set": {"last_action": "locked"}})
                    
                    elif not should_be_locked and last_action != "unlocked":
                        # --- ATTEMPT UNLOCK ---
                        # Only send message if previous state was explicitly locked (avoids startup spam)
                        if last_action == "locked":
                             await app.set_chat_permissions(chat_id, UNLOCK_PERMISSIONS)
                             await app.send_message(chat_id, "🔓 **Good Morning**\n\nGroup is now open.")
                        
                        # Update DB even if we didn't send message, to prevent loops
                        await db.update_one({"chat_id": chat_id}, {"$set": {"last_action": "unlocked"}})
                
                except Exception as e:
                    err_str = str(e).upper()
                    
                    # --- FIX 1: CHAT_ADMIN_REQUIRED ---
                    # If bot is not admin, disable night mode for this group to stop log spam
                    if "CHAT_ADMIN_REQUIRED" in err_str or "ADMIN PRIVILEGES" in err_str:
                        print(f"[Lock] Auto-Disabling for {chat_id} due to missing Admin Rights.")
                        await db.update_one({"chat_id": chat_id}, {"$set": {"status": "off"}})
                    
                    # --- FIX 2: CHAT_NOT_MODIFIED ---
                    # If permissions are already set, Telegram returns this error.
                    # We should treat this as a success and update DB.
                    elif "CHAT_NOT_MODIFIED" in err_str:
                        correct_state = "locked" if should_be_locked else "unlocked"
                        await db.update_one({"chat_id": chat_id}, {"$set": {"last_action": correct_state}})
                    
                    else:
                        print(f"Lock Scheduler Unknown Error in {chat_id}: {e}")
                    
        except Exception as e:
            print(f"Main Scheduler Error: {e}")

        await asyncio.sleep(60)

asyncio.create_task(night_mode_scheduler())

# --- COMMAND: /setlock ---
@app.on_message(filters.command(["setlock", "nightmode"]) & filters.group & ~BANNED_USERS)
async def setlock_command(client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an Admin.")

    doc = await db.find_one({"chat_id": message.chat.id})
    is_active = doc and doc.get("status") == "on"
    
    status_text = "✅ Enabled" if is_active else "❌ Disabled"
    button_text = "Disable" if is_active else "Enable"
    callback_data = "lock_disable" if is_active else "lock_enable"

    text = (
        f"🔐 **Auto Lock Settings** (India Time)\n\n"
        f"🌙 **Lock Time:** 01:00 AM\n"
        f"☀️ **Unlock Time:** 06:00 AM\n\n"
        f"📊 **Status:** {status_text}"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(button_text, callback_data=callback_data)],
        [InlineKeyboardButton("Check Permissions", callback_data="lock_check_perms")],
        [InlineKeyboardButton("Close", callback_data="close_data")]
    ])

    await message.reply_text(text, reply_markup=buttons)

# --- CALLBACKS ---
@app.on_callback_query(filters.regex("lock_enable") & ~BANNED_USERS)
async def enable_lock(client, callback_query: CallbackQuery):
    if not await is_admin(callback_query.message.chat.id, callback_query.from_user.id):
        return await callback_query.answer("❌ Admins Only!", show_alert=True)
    
    # Calculate current state immediately to prevent "Good Morning" spam on enable
    now = datetime.now(TIMEZONE)
    current_hour = now.hour
    should_be_locked = LOCK_HOUR <= current_hour < UNLOCK_HOUR
    initial_state = "locked" if should_be_locked else "unlocked"

    await db.update_one(
        {"chat_id": callback_query.message.chat.id},
        {"$set": {"status": "on", "last_action": initial_state}},
        upsert=True
    )
    await callback_query.answer("Auto Lock Enabled!", show_alert=True)
    await callback_query.message.edit_text(
        "✅ **Auto Lock System Enabled**\n\nGroup will automatically Lock at 1 AM and Unlock at 6 AM."
    )

@app.on_callback_query(filters.regex("lock_disable") & ~BANNED_USERS)
async def disable_lock(client, callback_query: CallbackQuery):
    if not await is_admin(callback_query.message.chat.id, callback_query.from_user.id):
        return await callback_query.answer("❌ Admins Only!", show_alert=True)
    
    await db.update_one(
        {"chat_id": callback_query.message.chat.id},
        {"$set": {"status": "off"}},
        upsert=True
    )
    await callback_query.answer("Auto Lock Disabled!", show_alert=True)
    await callback_query.message.edit_text(
        "❌ **Auto Lock System Disabled**"
    )

@app.on_callback_query(filters.regex("lock_check_perms") & ~BANNED_USERS)
async def check_perms_lock(client, callback_query: CallbackQuery):
    text = (
        "📋 **Permission Details**\n\n"
        "1. **At 01:00 AM (Lock):**\n"
        "• Send Messages: ❌\n"
        "• Send Media: ❌\n\n"
        "2. **At 06:00 AM (Unlock):**\n"
        "• Send Messages: ✅\n"
        "• Send Media: ❌ (Blocked)"
    )
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="lock_back")]])
    )

@app.on_callback_query(filters.regex("lock_back") & ~BANNED_USERS)
async def back_lock_menu(client, callback_query: CallbackQuery):
    # Retrieve current status to update the button text correctly
    doc = await db.find_one({"chat_id": callback_query.message.chat.id})
    is_active = doc and doc.get("status") == "on"
    
    status_text = "✅ Enabled" if is_active else "❌ Disabled"
    button_text = "Disable" if is_active else "Enable"
    callback_data = "lock_disable" if is_active else "lock_enable"

    text = (
        f"🔐 **Auto Lock Settings**\n\n"
        f"Schedule: 01:00 AM - 06:00 AM\n"
        f"Status: {status_text}"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(button_text, callback_data=callback_data)],
        [InlineKeyboardButton("Check Permissions", callback_data="lock_check_perms")],
        [InlineKeyboardButton("Close", callback_data="close_data")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=buttons)

@app.on_callback_query(filters.regex("close_data") & ~BANNED_USERS, group=99)
async def close_callback(client, callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()
    except:
        pass
        
