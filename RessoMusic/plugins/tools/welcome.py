import html
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from RessoMusic import app

# --- SMALL CAPS HELPER FUNCTION ---
def to_small_caps(text):
    chars = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 
        'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 
        'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'
    }
    return "".join(chars.get(c, c) for c in text.lower())

# --- WELCOME HANDLER ---
@app.on_message(filters.new_chat_members & filters.group)
async def welcome_new_members(client, message: Message):
    chat = message.chat
    
    # Bot username ek baar hi fetch kar lo loop se bahar
    try:
        bot = await client.get_me()
        bot_username = bot.username
        bot_id = bot.id
    except:
        bot_username = "RessoMusicBot"
        bot_id = 0

    for member in message.new_chat_members:
        try:
            # Agar Bot khud add hua hai to ignore kare
            if member.id == bot_id:
                continue

            user_id = member.id
            # HTML Escape zaroori hai taaki naam me < > ho to crash na ho
            first_name = html.escape(member.first_name or "User")
            
            if member.username:
                username = f"@{member.username}"
            else:
                username = to_small_caps("no username")
            
            # HTML Name Link
            mention = f"<a href='tg://user?id={user_id}'>{first_name}</a>"
            chat_title = html.escape(chat.title)

            # --- STYLISH LABELS ---
            header = to_small_caps("welcome to")
            lbl_name = to_small_caps("name")
            lbl_uname = to_small_caps("username")
            lbl_id = to_small_caps("user id")
            footer = to_small_caps("thanks for joining")

            # --- DECORATED TEXT ---
            text = (
                f"🫧 <b>{header} {chat_title}</b> 🫧\n\n"
                f"┏━━━━━━━━━━━━━━━━━┓\n"
                f"┣➤ <b>{lbl_name} :</b> {mention}\n"
                f"┣➤ <b>{lbl_uname} :</b> {username}\n"
                f"┣➤ <b>{lbl_id} :</b> <code>{user_id}</code>\n"
                f"┗━━━━━━━━━━━━━━━━━┛\n\n"
                f"🍷 <b>{footer}</b> 🍷"
            )

            # --- BUTTON ---
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ", url=f"https://t.me/{bot_username}?startgroup=true")
                ]
            ])

            # Send Message
            await client.send_message(
                chat.id,
                text=text,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )

        except Exception as e:
            # Error print karega taaki logs me dikhe agar koi dikkat ho
            print(f"[Welcome Error]: {e}")
            
