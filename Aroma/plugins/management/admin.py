from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Aroma import app
import logging

logging.basicConfig(level=logging.INFO)

@app.on_message(filters.command('promote') & filters.group)
def promote_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot_user = client.get_me()

    try:
        bot_member = client.get_chat_member(chat_id, bot_user.id)
        logging.info(f"Bot member status: {bot_member.status}, privileges: {bot_member.privileges}")

        if not bot_member.privileges.can_promote_members:
            client.send_message(chat_id, "I don't have permission to promote members.")
            return
    except Exception as e:
        client.send_message(chat_id, "Error retrieving bot status.")
        logging.error(f"Error retrieving bot member status: {e}")
        return

    try:
        user_member = client.get_chat_member(chat_id, user_id)
        logging.info(f"User {user_id} status: {user_member.status}, privileges: {user_member.privileges}")

        if user_member.status != "administrator":
            client.send_message(chat_id, "You need to be an administrator to use this command.")
            return

        if not user_member.privileges.can_promote_members:
            client.send_message(chat_id, "You do not have permission to promote other users.")
            return

    except Exception as e:
        client.send_message(chat_id, "Error retrieving your status.")
        logging.error(f"Error retrieving user member status: {e}")
        return