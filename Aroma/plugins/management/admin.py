import logging
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPrivileges
from Aroma import app
from config import MONGO_DB_URI
from Aroma.core.mongo import mongodb

mongo_client = MongoClient(MONGO_DB_URI)
db = mongo_client['your_database_name']
promotion_collection = db['promotion_sources']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

temporary_permissions = {}
temporary_messages = {}

@app.on_message(filters.command('promote') & filters.group)
async def promote_user(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)
        if not bot_member.privileges.can_promote_members:
            await client.send_message(chat_id, "I don't have permission to promote members.")
            return
    except Exception as e:
        await client.send_message(chat_id, f"Error retrieving bot status: {e}")
        logger.error(f"Error retrieving bot status: {e}")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        return

    promotion_data = promotion_collection.find_one({"user_id": target_user_id})

    if promotion_data and promotion_data['source'] == 'bot':
        await client.send_message(chat_id, "User is already an admin. You can change their permissions.")
        if target_user_id not in temporary_permissions:
            temporary_permissions[target_user_id] = initialize_permissions(bot_member.privileges)

        markup = create_permission_markup(target_user_id, bot_member.privileges)
        await client.send_message(chat_id, "Choose permissions to grant:", reply_markup=markup)
    else:
        await client.send_message(chat_id, "User is already an admin but was promoted by someone else.")

    promotion_collection.update_one(
        {"user_id": target_user_id},
        {"$set": {"source": 'bot'}},
        upsert=True
    )

async def get_target_user_id(client, chat_id, message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id

    if len(message.command) > 1:
        target_identifier = message.command[1]
        if target_identifier.isdigit():
            return int(target_identifier)

        try:
            target_user = await client.get_chat_member(chat_id, target_identifier.replace('@', ''))
            return target_user.user.id
        except Exception:
            await client.send_message(chat_id, "User not found or is not a member of this group.")
            logger.warning(f"User not found for identifier: {target_identifier}")
            return None
    else:
        await client.send_message(chat_id, "Please specify a user to promote by username, user ID, or replying to their message.")
        return None

def initialize_permissions(bot_privileges):
    return {
        "can_change_info": False,
        "can_invite_users": False,
        "can_delete_messages": False,
        "can_restrict_members": False,
        "can_pin_messages": False,
        "can_promote_members": False,
        "can_manage_chat": False,
        "can_manage_video_chats": False,
    }

def create_permission_markup(target_user_id, admin_privileges):
    buttons = []

    for perm, state in temporary_permissions[target_user_id].items():
        can_grant = getattr(admin_privileges, perm, False)
        icon = "🔒" if not can_grant else "✅" if state else "❌"

        callback_data = f"promote|toggle|{perm}|{target_user_id}"
        buttons.append(InlineKeyboardButton(
            f"{perm.replace('can_', '').replace('_', ' ').capitalize()} {icon}",
            callback_data=callback_data
        ))

    buttons.append(InlineKeyboardButton("Save", callback_data=f"promote|save|{target_user_id}"))
    buttons.append(InlineKeyboardButton("Close", callback_data=f"promote|close|{target_user_id}"))

    return InlineKeyboardMarkup([[button] for button in buttons])

@app.on_callback_query(filters.regex(r"promote\|"))
async def handle_permission_toggle(client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")

    if len(data) < 3:
        await callback_query.answer("Invalid callback data. Please try again.", show_alert=True)
        logger.error(f"Invalid callback data received: {callback_query.data}")
        return

    action = data[1]
    target_user_id = int(data[-1])

    user_member = await callback_query._client.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
    if not user_member.privileges or not user_member.privileges.can_promote_members:
        await callback_query.answer("You are not admin to use this button.", show_alert=True)
        return

    if action == "toggle":
        await toggle_permission(callback_query, target_user_id, data[2])
    elif action == "save":
        await save_permissions(callback_query._client, callback_query, target_user_id)
    elif action == "close":
        await close_permission_selection(callback_query)

async def toggle_permission(callback_query, target_user_id, perm_code):
    if target_user_id in temporary_permissions:
        permissions_dict = temporary_permissions[target_user_id]
        permissions_dict[perm_code] = not permissions_dict[perm_code]

        markup = create_permission_markup(target_user_id, await get_chat_privileges(callback_query))
        await callback_query.message.edit_reply_markup(markup)
        await callback_query.answer(f"{perm_code.replace('can_', '').replace('_', ' ').capitalize()} has been toggled.", show_alert=True)
    else:
        await callback_query.answer("No permissions found for this user.", show_alert=True)

async def get_chat_privileges(callback_query):
    user_member = await callback_query._client.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
    return user_member.privileges

async def save_permissions(client, callback_query, target_user_id):
    if target_user_id in temporary_permissions:
        permissions = temporary_permissions.pop(target_user_id)
        privileges = ChatPrivileges(**permissions)

        chat_id = callback_query.message.chat.id
        try:
            await client.promote_chat_member(chat_id, target_user_id, privileges=privileges)
            updated_member = await client.get_chat_member(chat_id, target_user_id)
            user_name = updated_member.user.first_name or updated_member.user.username or "User"

            await callback_query.message.edit_reply_markup(reply_markup=None)
            await callback_query.answer(f"{user_name} has been promoted.", show_alert=True)

            if target_user_id in temporary_messages:
                await temporary_messages[target_user_id].delete()
                del temporary_messages[target_user_id]

        except Exception as e:
            await callback_query.answer(f"Failed to promote user: {str(e)}", show_alert=True)
            logger.error(f"Error promoting user {target_user_id} with privileges {privileges}: {e}")
    else:
        await callback_query.answer("No permissions found for this user.", show_alert=True)

async def close_permission_selection(callback_query):
    await callback_query.message.delete()
    target_user_id = int(callback_query.data.split("|")[-1])

    if target_user_id in temporary_messages:
        await temporary_messages[target_user_id].delete()
        del temporary_messages[target_user_id]

    await callback_query.answer("Permissions selection closed without saving.", show_alert=True)

async def cleanup_temporary_permissions():
    pass