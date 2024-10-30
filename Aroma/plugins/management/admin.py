from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPrivileges
from Aroma import app

@app.on_message(filters.command('promote') & filters.group)
async def promote_user(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()

    print("Received promote command.")

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)
        if not bot_member.privileges.can_promote_members:
            await client.send_message(chat_id, "I don't have permission to promote members.")
            return
    except Exception as e:
        await client.send_message(chat_id, "Error retrieving bot status.")
        print(f"Error retrieving bot member status: {e}")
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

    try:
        target_user_member = await client.get_chat_member(chat_id, target_user_id)
        if target_user_member.status in ['administrator', 'creator']:
            await client.send_message(chat_id, "This user is already promoted by someone else.")
            return
    except Exception as e:
        await client.send_message(chat_id, "Error retrieving target user's status.")
        print(f"Error retrieving target user member status: {e}")
        return

    # Initial permissions setup
    permissions_dict = {
        "can_send_messages": False,
        "can_send_media_messages": False,
        "can_send_polls": False,
        "can_send_other_messages": False,
        "can_add_web_page_previews": False,
        "can_change_info": False,
        "can_invite_users": False,
        "can_restrict_members": False,
        "can_pin_messages": False,
    }

    buttons = []
    for perm_name, perm_code in permissions_dict.items():
        button_text = f"{perm_name.replace('can_', '').replace('_', ' ').capitalize()} ❌"
        callback_data = f"promote|toggle|{perm_name}|{target_user_id}|{permissions_dict}"
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

    # Initialize permissions dictionary
    permissions_dict = eval(data[4]) if len(data) > 4 else {
        "can_send_messages": False,
        "can_send_media_messages": False,
        "can_send_polls": False,
        "can_send_other_messages": False,
        "can_add_web_page_previews": False,
        "can_change_info": False,
        "can_invite_users": False,
        "can_restrict_members": False,
        "can_pin_messages": False,
    }

    if action == "toggle" and target_user_id and perm_code:
        # Toggle the selected permission
        permissions_dict[perm_code] = not permissions_dict[perm_code]

        # Create the privileges object with the updated permissions
        privileges = ChatPrivileges(
            can_send_messages=permissions_dict["can_send_messages"],
            can_send_media_messages=permissions_dict["can_send_media_messages"],
            can_send_polls=permissions_dict["can_send_polls"],
            can_send_other_messages=permissions_dict["can_send_other_messages"],
            can_add_web_page_previews=permissions_dict["can_add_web_page_previews"],
            can_change_info=permissions_dict["can_change_info"],
            can_invite_users=permissions_dict["can_invite_users"],
            can_restrict_members=permissions_dict["can_restrict_members"],
            can_pin_messages=permissions_dict["can_pin_messages"],
            can_promote_members=False,  # Always set to False in this context
            can_manage_chat=False,
            can_manage_video_chats=False,
        )

        # Attempt to promote the user with the new permissions
        try:
            await client.promote_chat_member(chat_id, target_user_id, privileges=privileges)

            # Update the buttons to reflect current permissions
            buttons = []
            for code in permissions_dict:
                buttons.append(InlineKeyboardButton(
                    f"{code.replace('can_', '').replace('_', ' ').capitalize()} {'✅' if permissions_dict[code] else '❌'}",
                    callback_data=f"promote|toggle|{code}|{target_user_id}|{permissions_dict}"
                ))

            buttons.append(InlineKeyboardButton("Save", callback_data=f"promote|save|{target_user_id}"))
            buttons.append(InlineKeyboardButton("Close", callback_data="promote|close"))

            markup = InlineKeyboardMarkup([[button] for button in buttons])
            await callback_query.message.edit_reply_markup(markup)

            await callback_query.answer(f"{perm_code} has been {'granted' if permissions_dict[perm_code] else 'revoked'}.", show_alert=True)

        except Exception as e:
            await callback_query.answer("Failed to grant permission. Please try again.", show_alert=True)
            print(f"Error granting permission: {e}")

    elif action == "save" and target_user_id:
        await client.send_message(chat_id, f"User {target_user_id} has been promoted with the selected permissions.")
        await callback_query.answer("Promotion confirmed.", show_alert=True)

    elif action == "close":
        await callback_query.message.delete()
        await callback_query.answer("Permissions selection closed without saving.", show_alert=True)