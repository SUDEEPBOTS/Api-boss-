from pyrogram import filters, enums
from pyrogram.types import (
    ChatPrivileges, 
    ChatPermissions, 
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from RessoMusic import app
from RessoMusic.utils import extract_user
from config import BANNED_USERS, SUDOERS

# Define prefixes (/, !, .)
COMMAND_PREFIXES = ["/", "!", "."]

# --- HELPER: CHECK IF USER IS ADMIN/OWNER ---
async def is_admin_or_sudo(chat_id, user_id):
    # 1. Sudo Check
    if user_id in SUDOERS:
        return True
    # 2. Telegram Admin/Owner Check
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except:
        pass
    return False

# --- ANONYMOUS ADMIN CHECKER ---
async def check_anonymous(message):
    if message.sender_chat:
        # User is Anonymous
        await message.reply_text(
            "⚠️ **You are an Anonymous Admin!**\n\n"
            "Please click the button below to verify your permissions.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Click to Verify", callback_data="verify_admin")]
            ])
        )
        return True
    return False

# --- CALLBACK: VERIFY ANONYMOUS ADMIN ---
@app.on_callback_query(filters.regex("verify_admin"))
async def verify_anonymous_admin(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    
    # Check permissions
    is_admin = await is_admin_or_sudo(chat_id, user_id)
    
    if is_admin:
        await callback_query.answer("✅ Verified! You are an Admin.", show_alert=True)
        await callback_query.message.edit_text(
            f"✅ **Verified!**\n\n"
            f"👤 **Admin:** {callback_query.from_user.mention}\n"
            f"ℹ️ **Note:** Please disable 'Remain Anonymous' or use your real account to execute commands."
        )
    else:
        await callback_query.answer("❌ You are NOT an Admin!", show_alert=True)
        await callback_query.message.edit_text("❌ **You do not have permission to use this.**")


# =========================================
#             ADMIN COMMANDS
# =========================================

# --- PROMOTE ---
@app.on_message(filters.command(["promote"], prefixes=COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def promote_user(client, message: Message):
    # 1. Check Anonymous
    if await check_anonymous(message): return
    
    # 2. Check Permissions (Normal User Block)
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ **You don't have permissions to use this command!**")

    # 3. Main Logic
    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User not found.**")

    bot_member = await message.chat.get_member(client.me.id)
    if not bot_member.privileges.can_promote_members:
        return await message.reply_text("❌ **I don't have permission!**\nPlease grant me 'Add New Admins' power.")

    try:
        await message.chat.promote_member(
            user.id,
            privileges=ChatPrivileges(
                can_manage_chat=True, can_delete_messages=True, can_manage_video_chats=True,
                can_invite_users=True, can_pin_messages=True, can_change_info=False,
                can_promote_members=False, is_anonymous=False
            ),
        )
        await message.reply_text(f"✅ **Promoted!**\n👤 **User:** {user.mention}\n🛡️ **Role:** Admin (Basic)")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")


# --- FULL PROMOTE ---
@app.on_message(filters.command(["fullpromote", "fpromote"], prefixes=COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def full_promote_user(client, message: Message):
    if await check_anonymous(message): return
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ **You don't have permissions to use this command!**")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User not found.**")

    bot_member = await message.chat.get_member(client.me.id)
    if not bot_member.privileges.can_promote_members:
        return await message.reply_text("❌ **I don't have permission!**")

    try:
        await message.chat.promote_member(
            user.id,
            privileges=ChatPrivileges(
                can_manage_chat=True, can_delete_messages=True, can_manage_video_chats=True,
                can_invite_users=True, can_pin_messages=True, can_change_info=True,
                can_promote_members=True, is_anonymous=False
            ),
        )
        await message.reply_text(f"🌟 **Full Promoted!**\n👤 **User:** {user.mention}\n🛡️ **Role:** Full Admin")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")


# --- DEMOTE ---
@app.on_message(filters.command(["demote"], prefixes=COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def demote_user(client, message: Message):
    if await check_anonymous(message): return
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ **You don't have permissions to use this command!**")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User not found.**")

    bot_member = await message.chat.get_member(client.me.id)
    if not bot_member.privileges.can_promote_members:
        return await message.reply_text("❌ **I don't have permission!**")

    try:
        await message.chat.promote_member(
            user.id,
            privileges=ChatPrivileges(
                can_manage_chat=False, can_delete_messages=False, can_manage_video_chats=False,
                can_invite_users=False, can_pin_messages=False, can_change_info=False,
                can_promote_members=False, is_anonymous=False
            ),
        )
        await message.reply_text(f"⬇️ **Demoted!**\n👤 **User:** {user.mention}\n🚫 **Role:** Member")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")


# --- BAN USER ---
@app.on_message(filters.command(["ban"], prefixes=COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def ban_user(client, message: Message):
    if await check_anonymous(message): return
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ **You don't have permissions to use this command!**")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User not found.**")

    bot_member = await message.chat.get_member(client.me.id)
    if not bot_member.privileges.can_restrict_members:
        return await message.reply_text("❌ **I don't have permission to ban users!**")

    try:
        await message.chat.ban_member(user.id)
        await message.reply_text(f"🚫 **Banned!**\n👤 **User:** {user.mention}")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")


# --- UNBAN USER ---
@app.on_message(filters.command(["unban"], prefixes=COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def unban_user(client, message: Message):
    if await check_anonymous(message): return
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ **You don't have permissions to use this command!**")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User not found.**")

    bot_member = await message.chat.get_member(client.me.id)
    if not bot_member.privileges.can_restrict_members:
        return await message.reply_text("❌ **I don't have permission to unban users!**")

    try:
        await message.chat.unban_member(user.id)
        await message.reply_text(f"✅ **Unbanned!**\n👤 **User:** {user.mention}")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")


# --- MUTE USER ---
@app.on_message(filters.command(["mute"], prefixes=COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def mute_user(client, message: Message):
    if await check_anonymous(message): return
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ **You don't have permissions to use this command!**")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User not found.**")

    bot_member = await message.chat.get_member(client.me.id)
    if not bot_member.privileges.can_restrict_members:
        return await message.reply_text("❌ **I don't have permission to restrict users!**")

    try:
        await message.chat.restrict_member(
            user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await message.reply_text(f"🔇 **Muted!**\n👤 **User:** {user.mention}")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")


# --- UNMUTE USER ---
@app.on_message(filters.command(["unmute"], prefixes=COMMAND_PREFIXES) & filters.group & ~BANNED_USERS)
async def unmute_user(client, message: Message):
    if await check_anonymous(message): return
    if not await is_admin_or_sudo(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ **You don't have permissions to use this command!**")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User not found.**")

    bot_member = await message.chat.get_member(client.me.id)
    if not bot_member.privileges.can_restrict_members:
        return await message.reply_text("❌ **I don't have permission to restrict users!**")

    try:
        await message.chat.restrict_member(
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_send_polls=True,
                can_invite_users=True
            )
        )
        await message.reply_text(f"🔊 **Unmuted!**\n👤 **User:** {user.mention}")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")
