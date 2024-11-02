import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from Aroma import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_message(filters.command('del') & filters.reply & filters.group)
async def delete_message(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    logger.info(f"Bot ID: {bot_user.id}, Chat ID: {chat_id}")

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)

        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            await message.reply("I am not an admin.")
            return
        if not bot_member.privileges.can_delete_messages:
            await message.reply("I don't have rights to delete messages.")
            return
    except Exception as e:
        await message.reply(f"Error retrieving bot status: {e}")
        logger.error(f"Error retrieving bot status: {e}")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)

    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await message.reply("You are not an admin.")
        return

    if not user_member.privileges.can_delete_messages:
        await message.reply("You don't have rights to delete messages.")
        return

    message_to_delete = message.reply_to_message
    if message_to_delete:
        await client.delete_messages(chat_id, message_to_delete.id)
        await message.reply("Message deleted.")
    else:
        await message.reply("Please reply to a message to delete it.")