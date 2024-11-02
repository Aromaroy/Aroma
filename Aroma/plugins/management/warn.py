import logging
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from config import MONGO_DB_URI
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Aroma import app

mongo_client = MongoClient(MONGO_DB_URI)
mongo_db = mongo_client["warn"]
mongo_collection = mongo_db["warnban"]

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

async def update_warnings(user_id, chat_id, reason):
    user_record = mongo_collection.find_one({"user_id": user_id, "chat_id": chat_id})
    if user_record:
        new_warning_count = user_record['warnings'] + 1
        mongo_collection.update_one({"user_id": user_id, "chat_id": chat_id}, {"$set": {"warnings": new_warning_count}})
    else:
        new_warning_count = 1
        mongo_collection.insert_one({"user_id": user_id, "chat_id": chat_id, "warnings": new_warning_count})
    return new_warning_count

@app.on_message(filters.command('warn') & filters.group)
async def warn_user(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    logger.info(f"Bot ID: {bot_user.id}, Chat ID: {chat_id}")

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)
        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            await client.send_message(chat_id, "I am not an admin.")
            return
        if not bot_member.privileges.can_restrict_members:
            await client.send_message(chat_id, "I don't have rights to warn this user.")
            return
    except Exception as e:
        logger.error(f"Error retrieving bot status: {e}")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)
    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await client.send_message(chat_id, "You are not an admin.")
        return

    if not user_member.privileges.can_restrict_members:
        await client.send_message(chat_id, "You don't have rights to warn this user.")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        await client.send_message(chat_id, "Could not find the target user.")
        return

    target_user = await client.get_users(target_user_id)

    if target_user_id == bot_user.id:
        await client.send_message(chat_id, "I'm not going to warn myself.")
        return

    try:
        target_user_member = await client.get_chat_member(chat_id, target_user_id)
    except Exception as e:
        if "USER_NOT_PARTICIPANT" in str(e):
            await client.send_message(chat_id, f"User {target_user.mention} is not a member of this group.")
            return
        logger.error(f"Error retrieving target user status: {e}")
        await client.send_message(chat_id, "An error occurred while checking the target user's status.")
        return

    if target_user_member.status == ChatMemberStatus.ADMINISTRATOR:
        await client.send_message(chat_id, "You cannot warn an admin.")
        return

    reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason provided."
    warning_count = await update_warnings(target_user_id, chat_id, reason)

    if warning_count < 3:
        notification_message = await client.send_message(
            chat_id,
            f"User {target_user.mention} has {warning_count}/3 warnings; be careful! Reason: {reason}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Remove Warn (Admin Only)", callback_data=f"remove_warn:{target_user_id}:{chat_id}")]
            ])
        )
    elif warning_count == 3:
        try:
            await client.ban_chat_member(chat_id, target_user_id)
            notification_message = await client.send_message(
                chat_id,
                f"That's 3/3 warnings; User {target_user.mention} is banned!\nReason: {reason}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Unban [Admin Only]", callback_data=f"unban:{target_user_id}:{chat_id}")]
                ])
            )
            mongo_collection.delete_one({"user_id": target_user_id, "chat_id": chat_id})
        except Exception as e:
            logger.error(f"Failed to ban user: {str(e)}")

@app.on_callback_query(filters.regex(r'^remove_warn:'))
async def remove_warning(client, query):
    _, target_user_id, chat_id = query.data.split(':')
    target_user_id = int(target_user_id)
    chat_id = int(chat_id)

    user_member = await client.get_chat_member(chat_id, query.from_user.id)
    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await query.answer("You are not an admin and cannot remove warnings.", show_alert=True)
        return

    if not user_member.privileges.can_restrict_members:
        await query.answer("You are an admin but lack the permission to remove warnings.", show_alert=True)
        return

    user_record = mongo_collection.find_one({"user_id": target_user_id, "chat_id": chat_id})
    if user_record:
        target_user = await client.get_users(target_user_id)

        if user_record['warnings'] > 1:
            remaining_warnings = user_record['warnings'] - 1
            mongo_collection.update_one({"user_id": target_user_id, "chat_id": chat_id}, {"$set": {"warnings": remaining_warnings}})
            await client.edit_message_text(
                chat_id, 
                query.message.id,
                f"Admin {query.from_user.mention} has removed {target_user.mention}'s warning. Remaining warnings: {remaining_warnings}/3."
            )
            await query.answer(f"Warning removed. User {target_user.mention} now has {remaining_warnings}/3 warnings.", show_alert=False)
        else:
            mongo_collection.delete_one({"user_id": target_user_id, "chat_id": chat_id})
            await client.edit_message_text(
                chat_id,
                query.message.id,
                f"Admin {query.from_user.mention} has removed {target_user.mention}'s warning. User has no warnings left."
            )
            await query.answer(f"User {target_user.mention} has no warnings left.", show_alert=False)
    else:
        await query.answer("No warnings to remove for this user.", show_alert=False)

@app.on_callback_query(filters.regex(r'^unban:'))
async def unban_user(client, query):
    _, target_user_id, chat_id = query.data.split(':')
    target_user_id = int(target_user_id)
    chat_id = int(chat_id)

    user_member = await client.get_chat_member(chat_id, query.from_user.id)
    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await query.answer("You are not an admin.", show_alert=True)
        return

    if not user_member.privileges.can_restrict_members:
        await query.answer("You are an admin but can't unban.", show_alert=True)
        return

    try:
        await client.unban_chat_member(chat_id, target_user_id)
        target_user = await client.get_users(target_user_id)
        await query.answer(f"User has been unbanned.", show_alert=True)
        await client.delete_messages(chat_id, query.message.id)
    except Exception as e:
        logger.error(f"Failed to unban user: {str(e)}")
        await query.answer("Failed to unban the user. Please try again later.", show_alert=True)