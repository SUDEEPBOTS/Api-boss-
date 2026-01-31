import asyncio
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from RessoMusic import app
from RessoMusic.misc import SUDOERS
from config import BANNED_USERS

# List to store disabled chats (Temporary Memory)
disable_bio_check = []

# --- HELPER: CHECK IF USER IS ADMIN/SUDO ---
async def is_admin_or_sudo(chat_id, user_id):
    if user_id in SUDOERS:
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except:
        pass
    return False

# --- FEATURE 0: COMMANDS TO ON/OFF BIO CHECK ---
@app.on_message(filters.command(["bio"]) & filters.group & ~BANNED_USERS)
async def bio_command_handler(client, message: Message):
    # Check if user is Admin
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an Admin.")

    if len(message.command) != 2:
        return await message.reply_text("⚠️ **Usage:**\n`/bio on` - Enable Bio Check\n`/bio off` - Disable Bio Check")

    state = message.command[1].lower()
    chat_id = message.chat.id

    if state == "off":
        if chat_id not in disable_bio_check:
            disable_bio_check.append(chat_id)
            await message.reply_text("✅ **Bio Check Disabled**")
        else:
            await message.reply_text("ℹ️ Bio Check is already **OFF**.")
    
    elif state == "on":
        if chat_id in disable_bio_check:
            disable_bio_check.remove(chat_id)
            await message.reply_text("✅ **Bio Check Enabled**")
        else:
            await message.reply_text("ℹ️ Bio Check is already **ON**.")
    
    else:
        await message.reply_text("⚠️ Invalid Command. Use `on` or `off`.")


# --- FEATURE 1: EDIT MESSAGE MONITOR ---
@app.on_edited_message(filters.group & ~BANNED_USERS)
async def edit_watcher(client, message: Message):
    if not message.from_user:
        return

    # REACTION FIX: Agar message me text ya caption nahi hai (sirf reaction update hai), to return
    if not message.text and not message.caption:
        return

    # Check Admin/Sudo (Ignore them)
    if await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return

    # Name & Username Formatting
    user_mention = message.from_user.mention  # Ye Blue color name dega
    username = f"(@{message.from_user.username})" if message.from_user.username else ""
    
    # New Format (Bold, No Blockquote, No Small Caps)
    text = (
        f"⚠️ **Editing Not Allowed**\n"
        f"👤 **User:** {user_mention} {username}\n"
        f"⏳ **Status:** **Deleting in 3 mins...**"
    )
    
    # Send Warning
    warning_msg = await message.reply_text(text)
    
    # Wait 3 Mins
    await asyncio.sleep(180)
    
    # Delete Both
    try:
        await message.delete()
    except:
        pass 
    try:
        await warning_msg.delete()
    except:
        pass


# --- FEATURE 2: BIO LINK CHECKER ---
@app.on_message(filters.group & ~BANNED_USERS, group=69)
async def bio_link_checker(client, message: Message):
    chat_id = message.chat.id
    
    # Check if disabled via command/button
    if chat_id in disable_bio_check:
        return

    if not message.from_user:
        return

    # Check Admin/Sudo
    if await is_admin_or_sudo(chat_id, message.from_user.id):
        return

    try:
        # Check Bio
        full_user = await client.get_chat(message.from_user.id)
        bio = full_user.bio
        
        if bio and ("http" in bio or "t.me" in bio or ".com" in bio or "www." in bio):
            
            # Delete User Message Immediately
            try:
                await message.delete()
            except:
                pass

            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔕 Turn Off", callback_data=f"bio_check_off|{chat_id}"),
                    InlineKeyboardButton("🗑️ Ignore", callback_data="close_data")
                ]
            ])

            # Name & Username Formatting
            user_mention = message.from_user.mention
            username = f"(@{message.from_user.username})" if message.from_user.username else ""

            # New Format (Bold, No Blockquote, No Small Caps)
            text = (
                f"🚫 **Anti-Promotion**\n"
                f"👤 **User:** {user_mention} {username}\n"
                f"⚠️ **Reason:** **Link in Bio detected.**\n"
                f"❗ **Remove link to chat here.**"
            )

            await message.reply_text(text, reply_markup=buttons)
    except Exception as e:
        pass


# --- BUTTON CALLBACKS ---
@app.on_callback_query(filters.regex("bio_check_off") & ~BANNED_USERS)
async def bio_off_callback(client, callback_query: CallbackQuery):
    # Check Admin for Button
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    is_admin = await is_admin_or_sudo(chat_id, user_id)

    if not is_admin:
        return await callback_query.answer("❌ You are not an Admin!", show_alert=True)

    chat_id_val = int(callback_query.data.split("|")[1])
    
    if chat_id_val not in disable_bio_check:
        disable_bio_check.append(chat_id_val)
        await callback_query.answer("Disabled!", show_alert=True)
        await callback_query.message.edit_text("✅ **Bio Check Disabled**")
    else:
        await callback_query.answer("Already Disabled!", show_alert=True)

@app.on_callback_query(filters.regex("close_data"))
async def close_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    is_admin = await is_admin_or_sudo(chat_id, user_id)
    
    if not is_admin:
        return await callback_query.answer("❌ You are not an Admin!", show_alert=True)
        
    await callback_query.message.delete()
    
