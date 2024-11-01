import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPrivileges
from Aroma import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_message(filters.command('demote') & filters.group)
async def demote_user(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)
        if not bot_member.privileges.can_promote_members:
            await client.send_message(chat_id, "I don't have permission to demote members.")
            return
    except Exception as e:
        await client.send_message(chat_id, f"Error retrieving bot status: {e}")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)

    if not user_member.privileges or not user_member.privileges.can_promote_members:
        await client.send_message(chat_id, "You are not an admin.")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        await client.send_message(chat_id, "Could not find the target user.")
        return

    target_user_member = await client.get_chat_member(chat_id, target_user_id)
    
    if target_user_member.status != 'administrator':
        await client.send_message(chat_id, "This user is already not an admin.")
        return

    if target_user_member.promoted_by and target_user_member.promoted_by.id != bot_user.id:
        await client.send_message(chat_id, "I can't demote this user because they were promoted by another admin.")
        return

    try:
        await client.promote_chat_member(chat_id, target_user_id, privileges=ChatPrivileges())
        await client.send_message(chat_id, "User has been demoted.")
    except Exception as e:
        await client.send_message(chat_id, f"Failed to demote user: {str(e)}")

