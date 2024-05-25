from datetime import datetime
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
import time
from datetime import datetime, timedelta
from bot import logger
from bot.database.users import get_users_in_channel_or_group, can_broadcast

@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_message(client, message):
       
    if len(message.command) < 3:
        await message.reply_text("Usage: /broadcast channel_or_group_id message")
        return

    try:
        channel_or_group_id = int(message.command[1])
    except ValueError:
        await message.reply_text("Invalid channel or group ID. Please provide a valid numeric ID.")
        return

    if not await can_broadcast(channel_or_group_id):
        await message.reply_text("Broadcast limit reached for the specified channel or group. Try again after 24 hours from previous broadcast")
        logger.info(f"Broadcast limit reached for group_id {channel_or_group_id}.")
        return False
    
    broadcast_message = " ".join(message.command[2:])

    try:
        chat_member = await client.get_chat_member(channel_or_group_id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            await message.reply_text("You are not an owner or administrator of the specified channel or group.")
            return

        user_ids = await get_users_in_channel_or_group(channel_or_group_id)
        if not user_ids:
            await message.reply_text("No users found in the specified channel or group.")
            return

        start_time = datetime.now()
        success_count = 0
        failed_count = 0

        for user_id in user_ids:
            try:
                await client.send_message(user_id, broadcast_message)
                success_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send broadcast to {user_id}: {e}")

        end_time = datetime.now()
        duration = end_time - start_time

        final_message = (
            f"Broadcast Completed:\n"
            f"Completed in {duration}\n\n"
            f"Total Users: {len(user_ids)}\n"
            f"Completed: {success_count + failed_count} / {len(user_ids)}\n"
            f"Success: {success_count}\n"
            f"Failed: {failed_count}"
        )

        await message.reply_text(final_message)

    except Exception as e:
        logger.error(f"An error occurred while broadcasting the message: {e}")
        await message.reply_text(f"An error occurred. Please try again later.")