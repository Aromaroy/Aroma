import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatPermissions
from Aroma import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_target_user_id(client, chat_id, message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        target_username = message.command[1]
        user = await client.get_users(target_username)
        return user.id
    return None

def parse_duration(duration_str):
    duration = 0
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'M': 2592000,
        'y': 31536000
    }
    
    num = ''
    for char in duration_str:
        if char.isdigit():
            num += char
        elif char in time_units and num:
            duration += int(num) * time_units[char]
            num = ''
    return duration

@app.on_message(filters.command('tmute') & filters.group)
async def tmute_user(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    logger.info(f"Bot ID: {bot_user.id}, Chat ID: {chat_id}")

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)

        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            await client.send_message(chat_id, "I am not an admin.")
            return
        if not bot_member.privileges.can_change_info:
            await client.send_message(chat_id, "I don't have rights to tmute users.")
            return
    except Exception as e:
        await client.send_message(chat_id, f"Error retrieving bot status: {e}")
        logger.error(f"Error retrieving bot status: {e}")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)
    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await client.send_message(chat_id, "You are not an admin.")
        return

    if not user_member.privileges.can_change_info:
        await client.send_message(chat_id, "You don't have rights to tmute this user.")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        await client.send_message(chat_id, "Could not find the target user.")
        return

    if target_user_id == bot_user.id:
        await client.send_message(chat_id, "I'm not gonna mute myself.")
        return

    if len(message.command) < 3:
        await client.send_message(chat_id, "Please provide a duration (e.g., 10m for 10 minutes).")
        return

    duration_str = message.command[2]
    duration = parse_duration(duration_str)

    if duration <= 0:
        await client.send_message(chat_id, "Invalid duration specified.")
        return

    try:
        target_user_member = await client.get_chat_member(chat_id, target_user_id)

        if target_user_member.status == ChatMemberStatus.ADMINISTRATOR:
            await client.send_message(chat_id, "You cannot mute an admin.")
            return

        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_pin_messages=False
        )

        await client.restrict_chat_member(chat_id, target_user_id, permissions=permissions)
        target_user = await client.get_users(target_user_id)
        target_name = target_user.first_name + (f" {target_user.last_name}" if target_user.last_name else "")
        await client.send_message(chat_id, f"{target_name} has been muted for {duration_str}.")

        await asyncio.sleep(duration)

        await client.restrict_chat_member(chat_id, target_user_id, permissions=None)
        await client.send_message(chat_id, f"{target_name} has been unmuted.")
    except Exception as e:
        await client.send_message(chat_id, f"Failed to mute user: {str(e)}")
        logger.error(f"Failed to mute user: {str(e)}")