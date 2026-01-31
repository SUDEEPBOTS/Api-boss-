import asyncio
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from RessoMusic import app
from RessoMusic.misc import SUDOERS
from config import BANNED_USERS

# Feature ko disable karne ke liye list
disable_bio_check = []

# --- SMALL CAPS CONVERTER FUNCTION ---
def to_small_caps(text):
    chars = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 
        'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 
        'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 
        'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 
        'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ'
    }
    return "".join(chars.get(c, c) for c in text)

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

async def check_cb_admin(client, callback_query):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    if user_id in SUDOERS:
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
        else:
            await callback_query.answer("❌ You are not an Admin!", show_alert=True)
            return False
    except:
        return False

# --- FEATURE 1: EDIT MESSAGE MONITOR ---
@app.on_edited_message(filters.group & ~BANNED_USERS)
async def edit_watcher(client, message: Message):
    if not message.from_user:
        return

    # Check Admin/Sudo
    if await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return

    # Name Fetching (Fixed)
    fname = message.from_user.first_name or "User"
    sc_user = to_small_caps(fname)

    # Message Formatting (Fixed Blockquote)
    header = to_small_caps("Editing Not Allowed")
    lbl_user = to_small_caps("User")
    lbl_status = to_small_caps("Status")
    lbl_msg = to_small_caps("Deleting in 3 mins...")
    
    text = (
        f">⚠️ **{header}**\n"
        f">👤 **{lbl_user}:** {sc_user}\n"
        f">⏳ **{lbl_status}:** {lbl_msg}"
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
                    InlineKeyboardButton("🔕 ᴛᴜʀɴ ᴏғғ", callback_data=f"bio_check_off|{chat_id}"),
                    InlineKeyboardButton("🗑️ ɪɢɴᴏʀᴇ", callback_data="close_data")
                ]
            ])

            # Name Fetching (Fixed)
            fname = message.from_user.first_name or "User"
            sc_user = to_small_caps(fname)

            # Formatting (Fixed Blockquote)
            header = to_small_caps("Anti-Promotion")
            lbl_user = to_small_caps("User")
            lbl_reason = to_small_caps("Reason")
            reason_msg = to_small_caps("Link in Bio detected.")
            lbl_action = to_small_caps("Remove link to chat here.")

            text = (
                f">🚫 **{header}**\n"
                f">👤 **{lbl_user}:** {sc_user}\n"
                f">⚠️ **{lbl_reason}:** {reason_msg}\n"
                f">❗ {lbl_action}"
            )

            await message.reply_text(text, reply_markup=buttons)
    except Exception as e:
        pass


# --- BUTTON CALLBACKS ---
@app.on_callback_query(filters.regex("bio_check_off") & ~BANNED_USERS)
async def bio_off_callback(client, callback_query: CallbackQuery):
    if not await check_cb_admin(client, callback_query):
        return

    chat_id = int(callback_query.data.split("|")[1])
    
    if chat_id not in disable_bio_check:
        disable_bio_check.append(chat_id)
        msg_text = to_small_caps("Bio Check Disabled")
        await callback_query.answer("Disabled!", show_alert=True)
        await callback_query.message.edit_text(f">✅ **{msg_text}**")
    else:
        await callback_query.answer("Already Disabled!", show_alert=True)

@app.on_callback_query(filters.regex("close_data"))
async def close_callback(client, callback_query: CallbackQuery):
    if not await check_cb_admin(client, callback_query):
        return
    await callback_query.message.delete()
    
