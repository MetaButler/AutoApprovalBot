from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.command("start"))
async def start(client, message):
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply_text("Hi, I am alive!")
    else:
        bot_info = (
            "Hello! I am an auto-approval bot.\n\n"
            "Add me to your group or channel, and I will automatically approve new members."
        )
        
        buttons = [
            [
                InlineKeyboardButton(f"➕ Add {client.me.first_name}", url=f"https://t.me/{client.me.username}?startgroup=true"),
                InlineKeyboardButton("📢 Join Our Channel", url="https://t.me/MetaProjects")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await message.reply_text(bot_info, reply_markup=reply_markup)