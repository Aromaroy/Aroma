import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from Aroma import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_target_user_id(client, chat_id, message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    elif message.command[1:]:
        target_username = message.command[1]
        user = await client.get_users(target_username)
        return user.id
    else:
        return None

@app.on_message(filters.command('kick') & filters.group)
async def kick_user(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    logger.info(f"Bot ID: {bot_user.id}, Chat ID: {chat_id}")

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)
        logger.info(f"Bot Member Privileges: {bot_member.privileges}")

        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            await client.send_message(chat_id, "I am not an admin.")
            return
        if not bot_member.privileges.can_restrict_members:
            await client.send_message(chat_id, "I don't have rights to kick users.")
            return
    except Exception as e:
        await client.send_message(chat_id, f"Error retrieving bot status: {e}")
        logger.error(f"Error retrieving bot status: {e}")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)
    logger.info(f"User Member Privileges: {user_member.privileges}")

    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await client.send_message(chat_id, "You are not an admin.")
        return

    if not user_member.privileges.can_restrict_members:
        await client.send_message(chat_id, "You don't have rights to kick this user.")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        await client.send_message(chat_id, "Could not find the target user.")
        return

    if target_user_id == bot_user.id:
        await client.send_message(chat_id, "Seriously, I'm not gonna kick myself.")
        return

    try:
        target_user_member = await client.get_chat_member(chat_id, target_user_id)
        logger.info(f"Target User ID: {target_user_id}, Status: {target_user_member.status}, Privileges: {target_user_member.privileges}")

        if target_user_member.status == ChatMemberStatus.ADMINISTRATOR:
            await client.send_message(chat_id, "You cannot kick an admin.")
            return
    except Exception:
        logger.info(f"Target User ID: {target_user_id} is not in the group or does not exist.")

    try:
        chat = await client.get_chat(chat_id)
        await chat.kick_chat_member(target_user_id)
        await asyncio.sleep(1)
        await chat.unban_chat_member(target_user_id)

        target_user = await client.get_users(target_user_id)
        target_name = target_user.first_name + (" " + target_user.last_name if target_user.last_name else "")
        admin_name = message.from_user.first_name + (" " + message.from_user.last_name if message.from_user.last_name else "")
        notification_message = f"A user has been kicked in chat:\nUser: {target_name}\nKicked by: {admin_name}"
        await client.send_message(chat_id, notification_message)
    except Exception as e:
        await client.send_message(chat_id, f"Failed to kick user: {str(e)}")
        logger.error(f"Failed to kick user: {str(e)}")