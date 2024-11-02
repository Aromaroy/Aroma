import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter, ChatType
from pyrogram.types import ChatPrivileges, ChatPermissions, Message
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
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)
    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await client.send_message(chat_id, "You are not an admin.")
        return

    if not user_member.privileges.can_delete_messages:
        await client.send_message(chat_id, "You don't have rights to delete messages.")
        return

    replied_msg = message.reply_to_message
    if not replied_msg:
        await client.send_message(chat_id, "Reply to the message you want to delete.")
        return

    deleted_count = 0
    message_ids = list(range(replied_msg.id + 1, message.id + 1))  # Get IDs between the replied message and the current message

    # Delete messages in chunks of 100
    for i in range(0, len(message_ids), 100):
        chunk = message_ids[i:i + 100]
        try:
            await client.delete_messages(chat_id, chunk, revoke=True)
            deleted_count += len(chunk)
        except Exception as e:
            await client.send_message(chat_id, f"Error deleting messages: {e}")

    notification_message = f"{deleted_count} messages deleted."
    sent_message = await client.send_message(chat_id, notification_message)

    await asyncio.sleep(4)
    await client.delete_messages(chat_id, sent_message.id)