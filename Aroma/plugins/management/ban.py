import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter, ChatType
from pyrogram.types import ChatPermissions, Message
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

@app.on_message(filters.command('ban') & filters.group)
async def ban_user(client, message):
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
            await client.send_message(chat_id, "I don't have rights to ban users.")
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
        await client.send_message(chat_id, "You don't have rights to ban this user.")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        await client.send_message(chat_id, "Could not find the target user.")
        return

    # Attempt to get the target user's membership status; if they are not found, handle gracefully
    try:
        target_user_member = await client.get_chat_member(chat_id, target_user_id)
        logger.info(f"Target User ID: {target_user_id}, Status: {target_user_member.status}, Privileges: {target_user_member.privileges}")

        if target_user_member.status == ChatMemberStatus.ADMINISTRATOR:
            await client.send_message(chat_id, "You cannot ban an admin.")
            return
    except Exception:
        # If user is not in the chat, we can proceed to ban them
        logger.info(f"Target User ID: {target_user_id} is not in the group or does not exist.")

    try:
        await client.ban_chat_member(chat_id, target_user_id)
        # Notify the chat about the ban
        target_name = f"User ID: {target_user_id}"  # Since they may not be found
        admin_name = message.from_user.first_name + (" " + message.from_user.last_name if message.from_user.last_name else "")
        notification_message = f"A user has been banned in chat:\nUser: {target_name}\nBanned by: {admin_name}"
        await client.send_message(chat_id, notification_message)
    except Exception as e:
        await client.send_message(chat_id, f"Failed to ban user: {str(e)}")
        logger.error(f"Failed to ban user: {str(e)}")