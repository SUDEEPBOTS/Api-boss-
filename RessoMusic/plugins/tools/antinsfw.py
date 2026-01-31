import os
import aiohttp
import asyncio
from pyrogram import filters, enums
from pyrogram.types import Message, ChatPermissions
from RessoMusic import app
# Fix: Import SUDOERS correctly
from RessoMusic.misc import SUDOERS

# --- API CREDENTIALS (SightEngine) ---
API_USER = '979248367'
API_SECRET = 'hSscaTuQfjHLqRJCdptFc3rX6iXgimnS'

# --- CONFIGURATION ---
NUDITY_THRESHOLD = 0.70 

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

# --- FUNCTION: CHECK IMAGE WITH AI ---
async def scan_image(file_bytes):
    url = 'https://api.sightengine.com/1.0/check.json'
    data = aiohttp.FormData()
    data.add_field('models', 'nudity')
    data.add_field('api_user', API_USER)
    data.add_field('api_secret', API_SECRET)
    data.add_field('media', file_bytes, filename='scan.jpg')

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, data=data) as resp:
                json_res = await resp.json()
                return json_res
        except Exception as e:
            print(f"NSFW API Error: {e}")
            return None

# --- MAIN WATCHER ---
@app.on_message(filters.group & (filters.photo | filters.sticker | filters.animation | filters.document) & ~SUDOERS, group=99)
async def nsfw_detector(client, message: Message):
    if not message.from_user: return
    chat_id = message.chat.id
    user_id = message.from_user.id

    # 1. Admin/Sudo Ignore
    if await is_admin(chat_id, user_id):
        return

    # 2. Check Document MimeType
    if message.document:
        if "image" not in message.document.mime_type:
            return

    # 3. Download Image
    try:
        file = await client.download_media(message, in_memory=True)
        if not file: return
        file_bytes = bytes(file.getbuffer())
    except Exception as e:
        return 

    # 4. Scan Image
    result = await scan_image(file_bytes)

    # 5. Result Analysis
    if result and result.get('status') == 'success':
        nudity = result.get('nudity', {})
        
        is_unsafe = False
        reason = ""

        if nudity.get('raw', 0) > max(NUDITY_THRESHOLD, 0.5):
            is_unsafe = True
            reason = "Explicit Nudity"
        elif nudity.get('safe', 1) < 0.05:
            is_unsafe = True
            reason = "NSFW Content"

        # 6. ACTION: DELETE & LOCK STICKERS (NO BAN)
        if is_unsafe:
            # A. Message Delete
            try:
                await message.delete()
            except:
                pass 

            # B. Lock Stickers for the Group (Panic Mode)
            try:
                # Sirf Text aur Media allow karenge, Stickers/GIFs band
                await client.set_chat_permissions(
                    chat_id,
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_polls=True,
                        can_invite_users=True,
                        can_pin_messages=False,
                        can_send_stickers=False,       # 🚫 STICKERS OFF
                        can_send_animations=False,     # 🚫 GIFS OFF
                        can_send_games=False,
                        can_use_inline_bots=False
                    )
                )

                # Warning Message
                await message.reply_text(
                    f"🚨 **NSFW DETECTED!** 🚨\n\n"
                    f"👤 **User:** {message.from_user.mention}\n"
                    f"🚫 **Reason:** {reason}\n"
                    f"🗑️ **Action:** Message Deleted.\n"
                    f"🔒 **Security:** **Stickers & GIFs have been disabled for the Group.**\n"
                    f"⚠️ __Admins can re-enable them manually.__"
                )
            except Exception as e:
                # Agar Permission nahi hai Lock karne ki
                await message.reply_text(
                    f"🚨 **NSFW Detected!**\n"
                    f"Deleted content from {message.from_user.mention}.\n"
                    f"⚠️ I tried to lock stickers but I don't have permission!"
              )
              
