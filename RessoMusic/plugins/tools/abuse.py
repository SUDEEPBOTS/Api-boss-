import asyncio
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from groq import Groq
from RessoMusic import app
from RessoMusic.misc import SUDOERS, mongodb
from config import BANNED_USERS, GROQ_API_KEY

# --- DATABASE & CACHE SETUP ---
abusedb = mongodb.abuse_cache
local_abuse_cache = []
disable_abuse_check = []

# Whitelist for Approved Users (In-Memory)
abuse_whitelist = []

# Deleted Messages Store (For Popup)
deleted_msg_store = {}

# --- INITIALIZE GROQ CLIENT ---
client_groq = None
if GROQ_API_KEY:
    try:
        client_groq = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Groq Init Error: {e}")

# --- LOAD CACHE ON STARTUP ---
async def load_abuse_cache():
    global local_abuse_cache
    try:
        async for doc in abusedb.find({"word": {"$exists": True}}):
            local_abuse_cache.append(doc["word"])
        print(f"[ABUSE] Loaded {len(local_abuse_cache)} abusive words.")
    except Exception as e:
        print(f"Database Error: {e}")

loop = asyncio.get_event_loop()
loop.create_task(load_abuse_cache())

# --- SMALL CAPS FUNCTION ---
def to_small_caps(text):
    if not text: return ""
    chars = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 
        'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 
        'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
    }
    return "".join(chars.get(c, c) for c in text.lower())

# --- HELPER: ADMIN CHECK ---
async def is_admin_or_sudo(chat_id, user_id):
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except:
        pass
    return False

# --- AI CHECK FUNCTION ---
async def check_abuse_with_ai(text):
    if not client_groq: return False
    try:
        chat_completion = client_groq.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a content moderator. If user input contains explicit abusive words (gaali like bc, mc, bsdk, fuck,lodu,asshole etc), reply 'YES'. Else 'NO'."},
                {"role": "user", "content": text}
            ],
            model="llama-3.3-70b-versatile",
        )
        return "YES" in chat_completion.choices[0].message.content.strip().upper()
    except Exception as e:
        print(f"Groq API Error: {e}")
        return False

# ====================================================
#                 COMMANDS SECTION
# ====================================================

# 1. APPROVE USER COMMAND (Reply to user)
@app.on_message(filters.command(["approve", "unmute", "allow"]) & filters.group & ~BANNED_USERS)
async def approve_user_command(client, message: Message):
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admins Only!")

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply_text("⚠️ **Reply to a user to approve them.**")

    target_user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name

    if target_user_id not in abuse_whitelist:
        abuse_whitelist.append(target_user_id)
        await message.reply_text(f"✅ **{user_name} is now Approved!**\nBot will ignore abuse from this user.")
    else:
        await message.reply_text(f"ℹ️ **{user_name}** is already approved.")

# 2. CLEAR WHITELIST COMMAND
@app.on_message(filters.command(["clearapprove", "resetapprove"]) & filters.group & ~BANNED_USERS)
async def clear_abuse_whitelist(client, message: Message):
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admins Only!")
    
    abuse_whitelist.clear()
    await message.reply_text("🔄 **Approved List Cleared!**\nEveryone will be checked for abuse now.")

# 3. TOGGLE ABUSE CHECK (ON/OFF)
@app.on_message(filters.command(["abuse", "antiabuse"]) & filters.group & ~BANNED_USERS)
async def abuse_toggle_command(client, message: Message):
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admins Only!")
    
    if len(message.command) != 2:
        return await message.reply_text("⚠️ Usage: `/abuse on` or `/abuse off`")
    
    state = message.command[1].lower()
    chat_id = message.chat.id

    if state == "off":
        if chat_id not in disable_abuse_check:
            disable_abuse_check.append(chat_id)
            await message.reply_text("✅ **Abuse Check Disabled.**")
        else:
            await message.reply_text("ℹ️ Already **OFF**.")
    elif state == "on":
        if chat_id in disable_abuse_check:
            disable_abuse_check.remove(chat_id)
            await message.reply_text("✅ **Abuse Check Enabled.**")
        else:
            await message.reply_text("ℹ️ Already **ON**.")

# ====================================================
#                 WATCHER SECTION
# ====================================================

@app.on_message(filters.group & filters.text & ~BANNED_USERS, group=70)
async def abuse_watcher(client, message: Message):
    chat_id = message.chat.id
    text = message.text
    
    # 0. Basic Checks
    if chat_id in disable_abuse_check: return
    if not text or len(text) > 200: return 
    if not message.from_user: return
    
    user_id = message.from_user.id

    # 1. Ignore Admins & Approved Users
    if await is_admin_or_sudo(chat_id, user_id):
        return
    if user_id in abuse_whitelist:
        return

    is_abusive = False
    text_lower = text.lower()

    # 2. Check Local Cache
    for bad_word in local_abuse_cache:
        if bad_word in text_lower:
            is_abusive = True
            break
    
    # 3. Check AI
    if not is_abusive:
        is_abusive = await check_abuse_with_ai(text)
        if is_abusive:
            if text_lower not in local_abuse_cache:
                local_abuse_cache.append(text_lower)
                # DB me save karo future ke liye
                await abusedb.insert_one({"word": text_lower})

    # 4. Action
    if is_abusive:
        deleted_msg_store[message.id] = text

        try:
            await message.delete()
        except:
            return 

        bot_username = (await app.get_me()).username
        
        # ADDED APPROVE BUTTON HERE
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ ᴀᴘᴘʀᴏᴠᴇ", callback_data=f"abuse_allow|{user_id}"),
                InlineKeyboardButton("👁️ sʜᴏᴡ", callback_data=f"sh_ab|{message.id}")
            ],
            [
                InlineKeyboardButton("🔕 ᴛᴇᴍᴘ ᴏғғ", callback_data=f"abuse_off|{chat_id}")
            ]
        ])

        user_name = message.from_user.first_name
        sc_user = to_small_caps(user_name)
        sc_msg = to_small_caps("Message deleted due to abusive words.")

        warn_text = (
            f">🚫 {sc_user}\n"
            f">⚠️ {sc_msg}"
        )

        await message.reply_text(warn_text, reply_markup=buttons)

# ====================================================
#                 CALLBACKS SECTION
# ====================================================

@app.on_callback_query(filters.regex("^(abuse_off|sh_ab|abuse_allow)") & ~BANNED_USERS)
async def abuse_callbacks(client, callback_query: CallbackQuery):
    if not await is_admin_or_sudo(callback_query.message.chat.id, callback_query.from_user.id):
        return await callback_query.answer("❌ Admins Only!", show_alert=True)

    data = callback_query.data.split("|")
    action = data[0]
    target_id = int(data[1])

    # 1. ALLOW USER
    if action == "abuse_allow":
        if target_id not in abuse_whitelist:
            abuse_whitelist.append(target_id)
            await callback_query.answer("User Approved!", show_alert=True)
            await callback_query.message.edit_text(f">✅ {to_small_caps('User Approved. No more checks.')}")
        else:
            await callback_query.answer("Already Approved!", show_alert=True)

    # 2. TURN OFF FOR GROUP
    elif action == "abuse_off":
        if target_id not in disable_abuse_check:
            disable_abuse_check.append(target_id)
            await callback_query.answer("Disabled!", show_alert=True)
            await callback_query.message.edit_text(f">✅ {to_small_caps('Abuse Filter Disabled')}")
        else:
            await callback_query.answer("Already Disabled!", show_alert=True)

    # 3. SHOW MESSAGE
    elif action == "sh_ab":
        original_text = deleted_msg_store.get(target_id)
        if original_text:
            await callback_query.answer(f"🤬 User Wrote:\n\n{original_text[:190]}", show_alert=True)
        else:
            await callback_query.answer("❌ Message expired.", show_alert=True)
            
