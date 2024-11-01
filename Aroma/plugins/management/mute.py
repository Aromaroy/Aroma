import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatPrivileges
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

@app.on_message(filters.command('mute') & filters.group)
async def mute_user(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    logger.info(f"Bot ID: {bot_user.id}, Chat ID: {chat_id}")

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)
        logger.info(f"Bot Member Privileges: {bot_member.privileges}")

        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            await client.send_message(chat_id, "I am not an admin.")
            return
        if not bot_member.privileges.can_change_info:
            await client.send_message(chat_id, "I don't have rights to mute users.")
            return
    except Exception as e:
        await client.send_message(chat_id, f"Error retrieving bot status: {e}")
        logger.error(f"Error retrieving bot status: {e}")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)
    logger.info(f"User Member Privileges: {user_member.privileges}")

    # Check if the user is an admin
    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await client.send_message(chat_id, "You are not an admin.")
        return

    # Check if the user has the rights to change member permissions
    if not user_member.privileges.can_change_info:
        await client.send_message(chat_id, "You don't have rights to mute this user.")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        await client.send_message(chat_id, "Could not find the target user.")
        return

    target_user_member = await client.get_chat_member(chat_id, target_user_id)
    logger.info(f"Target User ID: {target_user_id}, Status: {target_user_member.status}, Privileges: {target_user_member.privileges}")

    # Check if the user is already muted
    if target_user_member.privileges.can_send_messages == False:
        await client.send_message(chat_id, "This user is already muted.")
        return

    # Mute the user by updating their permissions
    if target_user_member.status == ChatMemberStatus.ADMINISTRATOR:
        await client.send_message(chat_id, "You cannot mute an admin.")
        return

    try:
        # Mute the user by revoking their permissions
        await client.restrict_chat_member(chat_id, target_user_id, permissions=ChatPrivileges(can_send_messages=False))
        await client.send_message(chat_id, "User has been muted.")
    except Exception as e:
        await client.send_message(chat_id, f"Failed to mute user: {str(e)}")
        logger.error(f"Failed to mute user: {str(e)}")