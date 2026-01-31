import asyncio
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from RessoMusic import app
from RessoMusic.misc import SUDOERS
from config import BANNED_USERS
from RessoMusic.utils.admin import actual_admin_cb

# Feature ko disable karne ke liye list
disable_bio_check = []

# --- SMALL CAPS CONVERTER FUNCTION ---
def to_small_caps(text):
    chars = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 
        'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 
        'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 
        'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 
        'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ'
    }
    return "".join(chars.get(c, c) for c in text)

# --- FUNCTION TO CHECK ADMIN STATUS ---
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

# --- FEATURE 1: EDIT MESSAGE MONITOR ---
@app.on_edited_message(filters.group & ~BANNED_USERS)
async def edit_watcher(client, message: Message):
    if not message.from_user:
        return

    # Check: Agar Admin ya Sudo hai toh IGNORE karega
    if await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return

    # Warning Text Prepare karna (Blockquote Fixed)
    user_name = message.from_user.first_name
    sc_user = to_small_caps(user_name)
    
    # Ek hi string me bina space ke newlines lagaye hain taaki quote na tute
    text = (
        f">⚠️ **{to_small_caps('Editing Not Allowed')}**\n"
        f">👤 **{to_small_caps('User')}:** {sc_user}\n"
        f">⏳ **{to_small_caps('Status')}:** {to_small_caps('Deleting in 3 mins...')}"
    )
    
    # Warning bhejna
    warning_msg = await message.reply_text(text)
    
    # 3 Minute (180 seconds) Wait karna
    await asyncio.sleep(180)
    
    # Ab Dono delete honge (User Msg + Bot Warning)
    try:
        await message.delete() # User ka msg delete
    except:
        pass # Agar msg pehle hi delete ho gaya ho
        
    try:
        await warning_msg.delete() # Bot ka msg delete
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

    if await is_admin_or_sudo(chat_id, message.from_user.id):
        return

    try:
        full_user = await client.get_chat(message.from_user.id)
        bio = full_user.bio
        
        # Check Bio for Links
        if bio and ("http" in bio or "t.me" in bio or ".com" in bio or "www." in bio):
            
            # User Msg Delete (Turant)
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

            user_name = message.from_user.first_name
            sc_user = to_small_caps(user_name)

            # Blockquote formatting fixed
            text = (
                f">🚫 **{to_small_caps('Anti-Promotion')}**\n"
                f">👤 **{to_small_caps('User')}:** {sc_user}\n"
                f">⚠️ **{to_small_caps('Reason')}:** {to_small_caps('Link in Bio detected.')}\n"
                f">❗ {to_small_caps('Remove link to chat here.')}"
            )

            await message.reply_text(text, reply_markup=buttons)
    except Exception as e:
        pass


# --- BUTTON CALLBACKS ---
@app.on_callback_query(filters.regex("bio_check_off") & ~BANNED_USERS)
async def bio_off_callback(client, callback_query: CallbackQuery):
    if not await actual_admin_cb(client, callback_query):
        return

    chat_id = int(callback_query.data.split("|")[1])
    
    if chat_id not in disable_bio_check:
        disable_bio_check.append(chat_id)
        await callback_query.answer("Disabled!", show_alert=True)
        await callback_query.message.edit_text(
            f">✅ **{to_small_caps('Bio Check Disabled')}**"
        )
    else:
        await callback_query.answer("Already Disabled!", show_alert=True)

@app.on_callback_query(filters.regex("close_data"))
async def close_callback(client, callback_query: CallbackQuery):
    if not await actual_admin_cb(client, callback_query):
        return
    await callback_query.message.delete()
  
