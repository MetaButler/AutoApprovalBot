from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import base64
import random


@Client.on_message(filters.command("start"))
async def start(client, message):
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply_text("Hi, I am alive!")
    elif "verify" in message.text:
        args = base64.b64decode(message.text.split("_")[1].encode()).decode().split(":")
        if len(args) != 3:
            return

        chat_id = int(args[0])
        user_id = int(args[1])
        message_id = int(args[2])

        if message.from_user.id != user_id:
            await message.reply_text("This verification link is not meant for you.")
            return

        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        correct_answer = num1 + num2

        buttons = [
            InlineKeyboardButton(
                str(correct_answer),
                callback_data=f"captcha_{chat_id}_{user_id}_{message_id}_correct",
            )
        ]
        for _ in range(5):
            wrong_answer = random.randint(1, 20)
            while wrong_answer == correct_answer:
                wrong_answer = random.randint(1, 20)
            buttons.append(
                InlineKeyboardButton(
                    str(wrong_answer),
                    callback_data=f"captcha_{chat_id}_{user_id}_wrong",
                )
            )

        random.shuffle(buttons)
        reply_markup = InlineKeyboardMarkup(
            [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
        )

        await client.send_message(
            user_id,
            f"Solve the captcha: {num1} + {num2} = ?",
            reply_markup=reply_markup,
        )
    else:
        bot_info = (
            "Hello! I am an auto-approval bot.\n\n"
            "Add me to your group or channel, and I will automatically approve new members."
        )

        buttons = [
            [
                InlineKeyboardButton(
                    f"➕ Add {client.me.first_name}",
                    url=f"https://t.me/{client.me.username}?startgroup=true",
                ),
                InlineKeyboardButton(
                    "📢 Join Our Channel", url="https://t.me/MetaProjects"
                ),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(buttons)

        await message.reply_text(bot_info, reply_markup=reply_markup)


@Client.on_message(filters.command("help") & (filters.private))
async def help_command(client, message):
    help_text = (
        "Here are the available commands:\n\n"
        "/welcome on/off - Turn the welcome message on or off in a group.\n"
        "/setwelcome Your Welcome Message Here - Set a custom welcome message for new members in a group.\n"
        "/broadcast channel_or_group_id message - Broadcast a message to all users in a specified channel or group (admins only).\n"
    )
    await message.reply_text(help_text)
