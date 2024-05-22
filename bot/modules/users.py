from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from pyrogram.enums import ChatMemberStatus, ParseMode

from bot import logger
from bot.database.users import (
    update_user_channel_settings, update_welcome_setting, get_welcome_setting,
    delete_user_channel_settings, set_welcome_message, get_welcome_message
)

@Client.on_chat_join_request(filters.group | filters.channel)
async def req_accept(client, message: ChatJoinRequest):
    user_id = message.from_user.id
    chat_id = message.chat.id

    await client.approve_chat_join_request(chat_id, user_id)
    
    update_success = await update_user_channel_settings(user_id, chat_id)
    
    if update_success:
        logger.info(f"Successfully updated user {user_id} with channel {chat_id}")
    else:
        logger.error(f"Failed to update user {user_id} with channel {chat_id}")

    welcome_setting = await get_welcome_setting(chat_id)
    if welcome_setting is None:
        await update_welcome_setting(chat_id, True)
        welcome_setting = True
    
    if welcome_setting:
        welcome_text = await get_welcome_message(chat_id)  # Change here
        welcome_text = welcome_text.format(user=message.from_user.mention, chat=message.chat.title)

        try:
            await client.send_message(user_id, welcome_text)
        except Exception as e:
            if "PEER_ID_INVALID" in str(e):
                logger.warning(f"User {user_id} has not interacted with the bot. Sending welcome message to the group/channel instead.")

                chat = await client.get_chat(chat_id)

                welcome_message = await get_welcome_message(chat_id)

                welcome_text = welcome_message if welcome_message else welcome_text
                welcome_text = welcome_text.format(user=message.from_user.mention, chat=message.chat.title)

                if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    await client.send_message(chat_id, welcome_text, parse_mode=ParseMode.HTML)
            else:
                logger.error(f"An error occurred: {e}")

@Client.on_chat_member_updated()
async def farewell(client, update):
    if (
        not update.new_chat_member
        or update.new_chat_member.status is ChatMemberStatus.BANNED 
    ):
        user_id = update.old_chat_member.user.id
        chat_id = update.chat.id

        delete_success = await delete_user_channel_settings(user_id, chat_id)
        
        if delete_success:
            logger.info(f"Successfully deleted user {user_id} from channel {chat_id}")
        else:
            logger.error(f"Failed to delete user {user_id} from channel {chat_id}")

@Client.on_message(filters.command("welcome") & filters.group)
async def set_welcome(client, message):
    chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)

    if chat_member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return

    if len(message.command) < 2:
        current_setting = await get_welcome_setting(message.chat.id)
        setting_status = "on" if current_setting else "off"
        await message.reply_text(f"Usage: /welcome on/off\nCurrent setting: {setting_status}")
        return

    setting = message.command[1].lower()
    if setting not in ["on", "off"]:
        await message.reply_text("Invalid setting. Use: /welcome <on/off>")
        return

    welcome_on = setting == "on"
    update_success = await update_welcome_setting(message.chat.id, welcome_on)

    if update_success:
        await message.reply_text(f"Welcome message turned {'on' if welcome_on else 'off'}")
    else:
        await message.reply_text("Failed to update welcome setting")

@Client.on_message(filters.command("setwelcome") & filters.group)
async def set_welcome_msg(client, message):
    chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)

    if chat_member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return

    if len(message.command) < 2:
        current_message = await get_welcome_message(message.chat.id)
        await message.reply_text(f"Usage: /setwelcome new welcome message\nCurrent welcome message: {current_message}")
        return

    new_message = " ".join(message.command[1:])
    update_success = await set_welcome_message(message.chat.id, new_message)

    if update_success:
        await message.reply_text(f"Welcome message updated successfully")
    else:
        await message.reply_text("Failed to update welcome message")

@Client.on_message(filters.command("setwelcome") & filters.private)
async def set_welcome_my_channel(client, message):
    if len(message.command) < 3:
        await message.reply_text("Usage: /setwelcome channel_id new welcome message")
        return

    try:
        channel_id = int(message.command[1])
    except ValueError:
        await message.reply_text("Invalid channel ID. Please provide a valid numeric channel ID.")
        return

    new_message = " ".join(message.command[2:])
    
    try:
        chat_member = await client.get_chat_member(channel_id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            await message.reply_text("You are not an owner or administrator of the specified channel.")
            return
        
        update_success = await set_welcome_message(channel_id, new_message)

        if update_success:
            await message.reply_text("Welcome message updated successfully")
        else:
            await message.reply_text("Failed to update welcome message")
    except Exception as e:
        logger.error(f"An error occurred while setting the welcome message: {e}")
