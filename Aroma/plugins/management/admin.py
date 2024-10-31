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

    user_member = await client.get_chat_member(chat_id, message.from_user.id)

    if not user_member.privileges:
        await client.send_message(chat_id, "You are not an admin to promote users.")
        return

    if not user_member.privileges.can_promote_members:
        await client.send_message(chat_id, "You don't have permission to promote users.")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        return

    if target_user_id not in temporary_permissions:
        temporary_permissions[target_user_id] = initialize_permissions(bot_member.privileges)

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🕹 Permissions", url=f"https://t.me/{app.get_bot_username()}?start=permission_management_{target_user_id}"),
         InlineKeyboardButton("Close", callback_data=f"promote|close|{target_user_id}")]
    ])

    await client.send_message(chat_id, "Select an option:", reply_markup=markup)

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

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    if message.command[1].startswith("permission_management_"):
        target_user_id = int(message.command[1].split("_")[-1])
        admin_privileges = await get_chat_privileges_for_dm(client, message)
        
        markup = create_permission_markup(target_user_id, admin_privileges)
        await client.send_message(
            message.chat.id,
            "Manage permissions:",
            reply_markup=markup
        )

def create_permission_markup(target_user_id, admin_privileges):
    buttons = []

    for perm, state in temporary_permissions[target_user_id].items():
        can_grant = getattr(admin_privileges, perm, False)
        icon = "🔒" if not can_grant else "✅" if state else "❌"

        # Create a callback for toggling permissions in DM
        callback_data = f"toggle|{perm}|{target_user_id}"
        buttons.append(InlineKeyboardButton(
            f"{perm.replace('can_', '').replace('_', ' ').capitalize()} {icon}",
            callback_data=callback_data
        ))

    save_button = InlineKeyboardButton("Save", callback_data=f"promote|save|{target_user_id}")
    close_button = InlineKeyboardButton("Close", callback_data=f"promote|close|{target_user_id}")

    buttons.append(save_button)
    buttons.append(close_button)

    button_rows = [buttons[i:i + 1] for i in range(0, len(buttons) - 2)]
    button_rows.append([save_button, close_button])

    return InlineKeyboardMarkup(button_rows)

async def get_chat_privileges_for_dm(client, message):
    user_member = await client.get_chat_member(message.chat.id, message.from_user.id)
    return user_member.privileges

@app.on_callback_query(filters.regex(r"toggle\|"))
async def toggle_permission(client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")
    perm_code = data[1]
    target_user_id = int(data[2])

    if target_user_id in temporary_permissions:
        permissions_dict = temporary_permissions[target_user_id]
        permissions_dict[perm_code] = not permissions_dict[perm_code]

        markup = create_permission_markup(target_user_id, await get_chat_privileges_for_dm(client, callback_query))
        await callback_query.message.edit_reply_markup(markup)
        await callback_query.answer(f"{perm_code.replace('can_', '').replace('_', ' ').capitalize()} has been toggled.", show_alert=True)
    else:
        await callback_query.answer("No permissions found for this user.", show_alert=True)

@app.on_callback_query(filters.regex(r"promote\|"))
async def handle_permission_toggle(client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")
    action = data[1]
    target_user_id = int(data[-1])

    user_member = await client.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
    if not user_member.privileges or not user_member.privileges.can_promote_members:
        await callback_query.answer("You are not admin to use this button.", show_alert=True)
        return

    if action == "save":
        await save_permissions(callback_query._client, callback_query, target_user_id)
    elif action == "close":
        await close_permission_selection(callback_query)

async def save_permissions(client, callback_query, target_user_id):
    if target_user_id in temporary_permissions:
        permissions = temporary_permissions.pop(target_user_id)
        privileges = ChatPrivileges(**permissions)

        chat_id = callback_query.message.chat.id
        try:
            await client.promote_chat_member(chat_id, target_user_id, privileges=privileges)
            updated_member = await client.get_chat_member(chat_id, target_user_id)
            user_name = updated_member.user.first_name or updated_member.user.username or "User"

            await callback_query.answer(f"{user_name} has been promoted.", show_alert=True)

        except Exception as e:
            await callback_query.answer(f"Failed to promote user: {str(e)}", show_alert=True)
            logger.error(f"Error promoting user {target_user_id} with privileges {privileges}: {e}")
    else:
        await callback_query.answer("No permissions found for this user.", show_alert=True)

async def close_permission_selection(callback_query):
    await callback_query.message.delete()
    await callback_query.answer("Permissions selection closed without saving.", show_alert=True)