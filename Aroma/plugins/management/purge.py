import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
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
    else:
        return None

@app.on_message(filters.command('purge') & filters.group)
async def purge_messages(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    logger.info(f"Bot ID: {bot_user.id}, Chat ID: {chat_id}")

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)

        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            await client.send_message(chat_id, "I am not an admin.")
            return
        if not bot_member.privileges.can_delete_messages:
            await client.send_message(chat_id, "I don't have rights to delete messages.")
            return
    except Exception as e:
        await client.send_message(chat_id, f"Error retrieving bot status: {e}")
        logger.error(f"Error retrieving bot status: {e}")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)

    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await client.send_message(chat_id, "You are not an admin.")
        return

    if not user_member.privileges.can_delete_messages:
        await client.send_message(chat_id, "You don't have rights to delete messages.")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        await client.send_message(chat_id, "Could not find the target user.")
        return

    deleted_count = 0
    replied_msg = message.reply_to_message

    if not replied_msg:
        error_msg = await client.send_message(chat_id, "Reply to the message you want to delete.")
        await asyncio.sleep(2)
        await client.delete_messages(chat_id, error_msg.message_id)
        return

    purge_to = message.reply_to_message.id

    message_ids = []

    for message_id in range(replied_msg.message_id, purge_to + 1):
        message_ids.append(message_id)

        # Max message deletion limit is 100
        if len(message_ids) == 100:
            await client.delete_messages(chat_id, message_ids, revoke=True)
            deleted_count += len(message_ids)
            message_ids = []

    # Delete if any messages left
    if len(message_ids) > 0:
        await client.delete_messages(chat_id, message_ids, revoke=True)
        deleted_count += len(message_ids)

    notification_message = f"{deleted_count} messages deleted."
    sent_message = await client.send_message(chat_id, notification_message)

    # Wait for 4 seconds before deleting the notification
    await asyncio.sleep(4)
    await client.delete_messages(chat_id, sent_message.message_id)