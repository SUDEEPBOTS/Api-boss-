import asyncio
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from RessoMusic import app
from RessoMusic.misc import SUDOERS
from config import BANNED_USERS

# --- MEMORY STORAGE ---
# Chat IDs jahan Checks OFF hain
disable_bio_check = []
disable_edit_check = []

# User IDs jo Allowed/Whitelisted hain
bio_whitelist = []
edit_whitelist = []

# --- HELPER: CHECK IF USER IS ADMIN/SUDO ---
async def is_admin_or_sudo(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except:
        pass
    return False

# ====================================================
#                 COMMANDS SECTION
# ====================================================

# --- 1. BIO COMMANDS (/bio on/off & /clearbio) ---
@app.on_message(filters.command(["bio"]) & filters.group & ~BANNED_USERS)
async def bio_command_handler(client, message: Message):
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an Admin.")
    
    if len(message.command) != 2:
        return await message.reply_text("⚠️ **Usage:** `/bio on` or `/bio off`")

    state = message.command[1].lower()
    chat_id = message.chat.id

    if state == "off":
        if chat_id not in disable_bio_check:
            disable_bio_check.append(chat_id)
            await message.reply_text("✅ **Bio Check Disabled.**")
        else:
            await message.reply_text("ℹ️ Already **OFF**.")
    elif state == "on":
        if chat_id in disable_bio_check:
            disable_bio_check.remove(chat_id)
            await message.reply_text("✅ **Bio Check Enabled.**")
        else:
            await message.reply_text("ℹ️ Already **ON**.")

@app.on_message(filters.command(["clearbio", "resetbio"]) & filters.group & ~BANNED_USERS)
async def clear_bio_whitelist(client, message: Message):
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an Admin.")
    bio_whitelist.clear()
    await message.reply_text("🔄 **Bio Whitelist Cleared!**")


# --- 2. EDIT COMMANDS (/edit on/off & /clearedit) ---
@app.on_message(filters.command(["edit", "antiedit"]) & filters.group & ~BANNED_USERS)
async def edit_command_handler(client, message: Message):
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an Admin.")
    
    if len(message.command) != 2:
        return await message.reply_text("⚠️ **Usage:** `/edit on` or `/edit off`")

    state = message.command[1].lower()
    chat_id = message.chat.id

    if state == "off":
        if chat_id not in disable_edit_check:
            disable_edit_check.append(chat_id)
            await message.reply_text("✅ **Anti-Edit Disabled.**")
        else:
            await message.reply_text("ℹ️ Already **OFF**.")
    elif state == "on":
        if chat_id in disable_edit_check:
            disable_edit_check.remove(chat_id)
            await message.reply_text("✅ **Anti-Edit Enabled.**")
        else:
            await message.reply_text("ℹ️ Already **ON**.")

@app.on_message(filters.command(["clearedit", "resetedit"]) & filters.group & ~BANNED_USERS)
async def clear_edit_whitelist(client, message: Message):
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an Admin.")
    edit_whitelist.clear()
    await message.reply_text("🔄 **Edit Whitelist Cleared!**")


# ====================================================
#                 WATCHERS SECTION
# ====================================================

# --- FEATURE 1: EDIT MESSAGE MONITOR ---
@app.on_edited_message(filters.group & ~BANNED_USERS)
async def edit_watcher(client, message: Message):
    if not message.from_user: return
    # Skip reaction updates
    if not message.text and not message.caption: return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # Checks
    if chat_id in disable_edit_check: return
    if await is_admin_or_sudo(chat_id, user_id): return
    if user_id in edit_whitelist: return

    user_mention = message.from_user.mention
    
    # Buttons for Admin
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Allow User", callback_data=f"edit_allow|{user_id}"),
            InlineKeyboardButton("🔕 Turn Off", callback_data=f"edit_check_off|{chat_id}")
        ],
        [InlineKeyboardButton("🗑️ Close", callback_data="close_data")]
    ])

    text = (
        f"⚠️ **Editing Not Allowed**\n"
        f"👤 **User:** {user_mention}\n"
        f"⏳ **Status:** **Deleting in 3 mins...**"
    )
    
    warning_msg = await message.reply_text(text, reply_markup=buttons)
    
    await asyncio.sleep(180)
    
    try: await message.delete()
    except: pass 
    try: await warning_msg.delete()
    except: pass


# --- FEATURE 2: BIO LINK CHECKER ---
@app.on_message(filters.group & ~BANNED_USERS, group=69)
async def bio_link_checker(client, message: Message):
    if not message.from_user: return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Checks
    if chat_id in disable_bio_check: return
    if await is_admin_or_sudo(chat_id, user_id): return
    if user_id in bio_whitelist: return

    try:
        full_user = await client.get_chat(user_id)
        bio = full_user.bio
        
        if bio and ("http" in bio or "t.me" in bio or ".com" in bio or "www." in bio):
            try: await message.delete()
            except: pass

            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Allow User", callback_data=f"bio_allow|{user_id}"),
                    InlineKeyboardButton("🔕 Turn Off", callback_data=f"bio_check_off|{chat_id}")
                ],
                [InlineKeyboardButton("🗑️ Close", callback_data="close_data")]
            ])

            text = (
                f"🚫 **Anti-Promotion**\n"
                f"👤 **User:** {message.from_user.mention}\n"
                f"⚠️ **Reason:** **Link in Bio detected.**"
            )
            await message.reply_text(text, reply_markup=buttons)
    except:
        pass


# ====================================================
#                 CALLBACKS SECTION
# ====================================================

@app.on_callback_query(filters.regex("^(bio_allow|edit_allow|bio_check_off|edit_check_off)") & ~BANNED_USERS)
async def tool_callbacks(client, callback_query: CallbackQuery):
    if not await is_admin_or_sudo(callback_query.message.chat.id, callback_query.from_user.id):
        return await callback_query.answer("❌ Admins Only!", show_alert=True)

    data = callback_query.data.split("|")
    action = data[0]
    target_id = int(data[1])

    # 1. ALLOW BIO
    if action == "bio_allow":
        if target_id not in bio_whitelist:
            bio_whitelist.append(target_id)
            await callback_query.answer("User Allowed for Bio!", show_alert=True)
            await callback_query.message.edit_text("✅ **User Allowed! (Bio Check)**")
        else:
            await callback_query.answer("Already Allowed!", show_alert=True)

    # 2. ALLOW EDIT (New)
    elif action == "edit_allow":
        if target_id not in edit_whitelist:
            edit_whitelist.append(target_id)
            await callback_query.answer("User Allowed for Edits!", show_alert=True)
            await callback_query.message.edit_text("✅ **User Allowed! (Anti-Edit)**")
        else:
            await callback_query.answer("Already Allowed!", show_alert=True)

    # 3. TURN OFF BIO CHECK
    elif action == "bio_check_off":
        if target_id not in disable_bio_check:
            disable_bio_check.append(target_id)
            await callback_query.answer("Bio Check Disabled!", show_alert=True)
            await callback_query.message.edit_text("✅ **Bio Check Disabled.**")
        else:
            await callback_query.answer("Already Disabled!", show_alert=True)

    # 4. TURN OFF EDIT CHECK (New)
    elif action == "edit_check_off":
        if target_id not in disable_edit_check:
            disable_edit_check.append(target_id)
            await callback_query.answer("Anti-Edit Disabled!", show_alert=True)
            await callback_query.message.edit_text("✅ **Anti-Edit Disabled.**")
        else:
            await callback_query.answer("Already Disabled!", show_alert=True)

@app.on_callback_query(filters.regex("close_data"))
async def close_callback(client, callback_query: CallbackQuery):
    if not await is_admin_or_sudo(callback_query.message.chat.id, callback_query.from_user.id):
        return await callback_query.answer("❌ Admins Only!", show_alert=True)
    await callback_query.message.delete()
            
