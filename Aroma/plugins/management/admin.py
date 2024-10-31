from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPrivileges
from Aroma import app

temporary_permissions = {}

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
        return

    target_user_id = None
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    else:
        try:
            target_user_id = int(message.command[1])
        except (IndexError, ValueError):
            target_username = message.command[1].replace('@', '') if len(message.command) > 1 else None
            if target_username:
                try:
                    target_user = await client.get_chat_member(chat_id, target_username)
                    target_user_id = target_user.user.id
                except Exception:
                    await client.send_message(chat_id, "User not found.")
                    return
            else:
                await client.send_message(chat_id, "Please specify a user to promote by username, user ID, or replying to their message.")
                return

    if target_user_id not in temporary_permissions:
        bot_privileges = bot_member.privileges
        temporary_permissions[target_user_id] = {
            "can_change_info": False,
            "can_invite_users": bot_privileges.can_invite_users,
            "can_delete_messages": bot_privileges.can_delete_messages,
            "can_restrict_members": False,
            "can_pin_messages": bot_privileges.can_pin_messages,
            "can_promote_members": False,
            "can_manage_chat": bot_privileges.can_manage_chat,
            "can_manage_video_chats": bot_privileges.can_manage_video_chats,
        }

    print(f"Temporary permissions before sending buttons: {temporary_permissions}")

    buttons = []
    for perm_name, current_state in temporary_permissions[target_user_id].items():
        button_text = f"{perm_name.replace('can_', '').replace('_', ' ').capitalize()} {'✅' if current_state else '❌'}"
        callback_data = f"promote|toggle|{perm_name}|{target_user_id}"
        buttons.append(InlineKeyboardButton(button_text, callback_data=callback_data))

    buttons.append(InlineKeyboardButton("Save", callback_data=f"promote|save|{target_user_id}"))
    buttons.append(InlineKeyboardButton("Close", callback_data="promote|close"))

    markup = InlineKeyboardMarkup([[button] for button in buttons])
    await client.send_message(chat_id, "Choose permissions to grant:", reply_markup=markup)

@app.on_callback_query(filters.regex(r"promote\|"))
async def handle_permission_toggle(client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")
    action = data[1]
    perm_code = data[2] if len(data) > 2 else None
    target_user_id = int(data[3]) if len(data) > 3 and data[3].isdigit() else None
    chat_id = callback_query.message.chat.id

    if action == "toggle" and target_user_id and perm_code:
        if target_user_id in temporary_permissions:
            permissions_dict = temporary_permissions[target_user_id]
            permissions_dict[perm_code] = not permissions_dict[perm_code]

            print(f"Toggled {perm_code}: {permissions_dict}")

            buttons = []
            for code, current_state in permissions_dict.items():
                buttons.append(InlineKeyboardButton(
                    f"{code.replace('can_', '').replace('_', ' ').capitalize()} {'✅' if current_state else '❌'}",
                    callback_data=f"promote|toggle|{code}|{target_user_id}"
                ))

            buttons.append(InlineKeyboardButton("Save", callback_data=f"promote|save|{target_user_id}"))
            buttons.append(InlineKeyboardButton("Close", callback_data="promote|close"))

            markup = InlineKeyboardMarkup([[button] for button in buttons])
            await callback_query.message.edit_reply_markup(markup)

            await callback_query.answer(f"{perm_code.replace('can_', '').replace('_', ' ').capitalize()} has been toggled.", show_alert=True)

    elif action == "save" and target_user_id:
        permissions = temporary_permissions.pop(target_user_id)
        print(f"Saving permissions for user {target_user_id}: {permissions}")

        privileges = ChatPrivileges(**permissions)
        print(f"Promoting user {target_user_id} with permissions: {privileges}")

        try:
            await client.promote_chat_member(chat_id, target_user_id, privileges=privileges)
            updated_member = await client.get_chat_member(chat_id, target_user_id)
            await callback_query.message.reply_text(f"User {target_user_id} has been promoted with the selected permissions. Current status: {updated_member.status}.")
            await callback_query.answer("Promotion confirmed.", show_alert=True)
        except Exception as e:
            await callback_query.answer(f"Failed to promote user: {str(e)}", show_alert=True)
            print(f"Error promoting user {target_user_id} with privileges {privileges}: {e}")

    elif action == "close":
        await callback_query.message.delete()
        await callback_query.answer("Permissions selection closed without saving.", show_alert=True)