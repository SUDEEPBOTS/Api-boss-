import math
from pyrogram.types import InlineKeyboardButton
from RessoMusic.utils.formatters import time_to_seconds

# ⚠️ NOTE: Ye feature tabhi chalega jab tumhari Pyrogram Library updated ho.
# Update command: pip install -U pyrogram tgcrypto

def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(text=" ᴜᴘᴅᴀᴛᴇ ", url="https://t.me/+rQqhGhdP7tRkMmM1"),
            InlineKeyboardButton(text=" sᴜᴘᴘᴏʀᴛ ", url="https://t.me/ll_MY_CORE_ll"),
        ],
        [
            InlineKeyboardButton("˹ᴀɴɪʏᴀ ᴛᴜɴᴇs˼♪", url="https://yukiapp-steel.vercel.app/"),
        ],
        [
            # Close button ko RED (Destructive) kar diya
            InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style="destructive")
        ],
    ]
    return buttons


def stream_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text=" ᴜᴘᴅᴀᴛᴇ ", url="https://t.me/+rQqhGhdP7tRkMmM1"),
            InlineKeyboardButton(text=" sᴜᴘᴘᴏʀᴛ ", url="https://t.me/ll_MY_CORE_ll"),
        ],
        [
            InlineKeyboardButton("˹ᴀɴɪʏᴀ ᴛᴜɴᴇs˼♪", url="https://yukiapp-steel.vercel.app/"),
        ],
        [
            # 🔵 Resume = Primary (Blue/Main)
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style="primary"),
            
            # 🔴 Pause = Destructive (Red/Warning)
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}", style="destructive"),
            
            # ⚪ Replay = Default (Grey)
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}"),
            
            # ⚪ Skip = Default (Grey)
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            
            # 🔴 Stop = Destructive (Red/End)
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style="destructive"),
        ],
        [
            # 🔴 Close = Red
            InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style="destructive")
        ],
    ]
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"AMBOTOPPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"AMBOTOPPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
                style="destructive"  # Red Close
            ),
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
                style="primary" # Live Stream button Blue
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
                style="destructive" # Red Close
            ),
        ],
    ]
    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="◁",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
                style="destructive" # Red Close
            ),
            InlineKeyboardButton(
                text="▷",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
    ]
    return buttons
    
