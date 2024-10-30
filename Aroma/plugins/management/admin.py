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
    except Exception:
        await client.send_message(chat_id, "Error retrieving bot status.")
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

    # Initialize permissions with the specified options
    if target_user_id not in temporary_permissions:
        bot = await client.get_chat_member(chat_id, bot_user.id)  # Get bot privileges

        temporary_permissions[target_user_id] = {
            "can_change_info": False,
            "can_invite_users": bot.privileges.can_invite_users,
            "can_delete_messages": bot.privileges.can_delete_messages,
            "can_restrict_members": False,  # No banning rights
            "can_pin_messages": bot.privileges.can_pin_messages,
            "can_promote_members": False,
            "can_manage_chat": bot.privileges.can_manage_chat,
            "can_manage_video_chats": bot.privileges.can_manage_video_chats,
        }

    # Create buttons based on temporary permissions
    buttons = []
    for perm_name in temporary_permissions[target_user_id]:
        current_state = temporary_permissions[target_user_id][perm_name]
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
        # Toggle the selected permission
        if target_user_id in temporary_permissions:
            permissions_dict = temporary_permissions[target_user_id]
            permissions_dict[perm_code] = not permissions_dict[perm_code]

            # Update the buttons to reflect current permissions
            buttons = []
            for code in permissions_dict:
                current_state = permissions_dict[code]
                buttons.append(InlineKeyboardButton(
                    f"{code.replace('can_', '').replace('_', ' ').capitalize()} {'✅' if current_state else '❌'}",
                    callback_data=f"promote|toggle|{code}|{target_user_id}"
                ))

            buttons.append(InlineKeyboardButton("Save", callback_data=f"promote|save|{target_user_id}"))
            buttons.append(InlineKeyboardButton("Close", callback_data="promote|close"))

            markup = InlineKeyboardMarkup([[button] for button in buttons])
            await callback_query.message.edit_reply_markup(markup)

            await callback_query.answer(f"{perm_code.replace('can_', '').replace('_', ' ').capitalize()} has been {'granted' if permissions_dict[perm_code] else 'revoked'}.", show_alert=True)

    elif action == "save" and target_user_id:
        permissions = temporary_permissions.pop(target_user_id)
        privileges = ChatPrivileges(**permissions)

        try:
            await client.promote_chat_member(chat_id, target_user_id, privileges=privileges)
            await callback_query.send_message(chat_id, f"User {target_user_id} has been promoted with the selected permissions.")
            await callback_query.answer("Promotion confirmed.", show_alert=True)
        except Exception:
            await callback_query.answer("Failed to promote user. Please try again.", show_alert=True)

    elif action == "close":
        await callback_query.message.delete()
        await callback_query.answer("Permissions selection closed without saving.", show_alert=True)