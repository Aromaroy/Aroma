import logging
from pyrogram import Client, filters
from Aroma import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_target_user_id(client, message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    elif message.command[1:]:
        target_username = message.command[1]
        user = await client.get_users(target_username)
        return user.id
    else:
        return None

@app.on_message(filters.command('id'))
async def id_user(client, message):
    chat_id = message.chat.id if message.chat else message.from_user.id
    logger.info(f"Chat ID: {chat_id}")

    target_user_id = await get_target_user_id(client, message)
    if target_user_id is None:
        await client.send_message(chat_id, "Could not find the target user.")
        return

    try:
        target_user = await client.get_users(target_user_id)
        target_name = target_user.first_name + (f" {target_user.last_name}" if target_user.last_name else "")
        user_id_message = f"The ID of `{target_name}` is `{target_user_id}`."

        # Check if in a group or channel and fetch their ID
        if message.chat:
            chat_type = message.chat.type
            if chat_type in ['group', 'supergroup']:
                group_id = message.chat.id
                user_id_message += f"\nThe Group ID is `{group_id}`."
            elif chat_type == 'channel':
                channel_id = message.chat.id
                user_id_message += f"\nThe Channel ID is `{channel_id}`."

        await client.send_message(chat_id, user_id_message)
    except Exception as e:
        await client.send_message(chat_id, f"Failed to retrieve user ID: {str(e)}")
        logger.error(f"Failed to retrieve user ID: {str(e)}")