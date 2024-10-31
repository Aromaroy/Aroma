import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPrivileges
from Aroma import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

temporary_permissions = {}
temporary_messages = {}

@app.on_message(filters.command('promote') & filters.group)
async def promote_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot_user = await client.get_me()

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)
        if not bot_member.privileges.can_promote_members:
            await client.send_message(chat_id, "I don't have permission to promote members.")
            return
        
        user_member = await client.get_chat_member(chat_id, user_id)

        # Check if the user is an admin
        if not user_member.status in ['administrator', 'creator']:
            await client.send_message(chat_id, "You are not an admin and cannot promote members.")
            return
        
        # Check if the user has permission to promote
        if not user_member.privileges.can_promote_members:
            await client.send_message(chat_id, "You don't have the right to promote other members.")
            return

    except Exception as e:
        await client.send_message(chat_id, f"Error retrieving bot or user status: {e}")
        logger.error(f"Error retrieving status: {e}")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        return

    if target_user_id not in temporary_permissions:
        temporary_permissions[target_user_id] = initialize_permissions(bot_member.privileges)

    markup = create_permission_markup(target_user_id, user_member.privileges)
    sent_message = await client.send_message(chat_id, "Choose permissions to grant:", reply_markup=markup)
    temporary_messages[target_user_id] = sent_message

def create_permission_markup(target_user_id, user_privileges):
    buttons = []

    for perm, state in temporary_permissions[target_user_id].items():
        can_grant = getattr(user_privileges, perm, False)
        callback_data = f"promote|toggle|{perm}|{target_user_id}"
        button_label = f"{perm.replace('can_', '').replace('_', ' ').capitalize()} {'🔒' if not can_grant else '✅' if state else '❌'}"
        buttons.append(InlineKeyboardButton(button_label, callback_data=callback_data) if can_grant else InlineKeyboardButton(button_label, callback_data="disabled"))

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

    if action == "toggle":
        await toggle_permission(callback_query, target_user_id, data[2])
    elif action == "save":
        await save_permissions(client, callback_query, target_user_id)
    elif action == "close":
        await close_permission_selection(callback_query)

async def toggle_permission(callback_query, target_user_id, perm_code):
    if target_user_id in temporary_permissions:
        permissions_dict = temporary_permissions[target_user_id]
        can_grant = getattr(callback_query.from_user, 'can_grant', False)

        if can_grant:
            permissions_dict[perm_code] = not permissions_dict[perm_code]

            markup = create_permission_markup(target_user_id, permissions_dict)
            await callback_query.message.edit_reply_markup(markup)
            await callback_query.answer(f"{perm_code.replace('can_', '').replace('_', ' ').capitalize()} has been toggled.", show_alert=True)
        else:
            await callback_query.answer("You don't have the privilege to use this button.", show_alert=True)
    else:
        await callback_query.answer("No permissions found for this user.", show_alert=True)

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