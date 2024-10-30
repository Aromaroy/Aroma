from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Aroma import app

# Store permissions temporarily until saved
temp_permissions = {}

@app.on_message(filters.command('promote') & filters.group)
def promote_user(client, message):
    chat_id = message.chat.id
    bot_user = client.get_me()

    print("Received promote command.")

    try:
        bot_member = client.get_chat_member(chat_id, bot_user.id)
        if not bot_member.privileges.can_promote_members:
            client.send_message(chat_id, "I don't have permission to promote members.")
            return
    except Exception as e:
        client.send_message(chat_id, "Error retrieving bot status.")
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
                    target_user = client.get_chat_member(chat_id, target_username)
                    target_user_id = target_user.user.id
                except Exception:
                    client.send_message(chat_id, "User not found.")
                    return
            else:
                client.send_message(chat_id, "Please specify a user to promote by username, user ID, or replying to their message.")
                return

    try:
        target_user_member = client.get_chat_member(chat_id, target_user_id)
        if target_user_member.status in ['administrator', 'creator']:
            client.send_message(chat_id, "This user is already promoted by someone else.")
            return
    except Exception as e:
        client.send_message(chat_id, "Error retrieving target user's status.")
        print(f"Error retrieving target user member status: {e}")
        return

    # Prepare buttons for each permission
    buttons = []
    permissions = {
        "Can Change Info": "can_change_info",
        "Can Delete Messages": "can_delete_messages",
        "Can Invite Users": "can_invite_users",
        "Can Restrict Members": "can_restrict_members",
        "Can Pin Messages": "can_pin_messages",
        "Can Promote Members": "can_promote_members",
    }

    # Initialize temp permissions
    temp_permissions[target_user_id] = {perm_code: False for perm_code in permissions.values()}

    for perm_name, perm_code in permissions.items():
        button_text = f"{perm_name} ❌"
        callback_data = f"promote|toggle|{perm_code}|{target_user_id}"
        buttons.append(InlineKeyboardButton(button_text, callback_data=callback_data))

    # Add Save and Close buttons
    buttons.append(InlineKeyboardButton("Save", callback_data=f"promote|save|{target_user_id}"))
    buttons.append(InlineKeyboardButton("Close", callback_data="promote|close"))

    # Organize buttons in rows
    markup = InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])

    client.send_message(chat_id, "Choose permissions to grant:", reply_markup=markup)

@app.on_callback_query(filters.regex(r"promote\|"))
def handle_permission_toggle(client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")
    action = data[1]
    perm_code = data[2] if len(data) > 2 else None
    target_user_id = int(data[3]) if len(data) > 3 and data[3].isdigit() else None
    chat_id = callback_query.message.chat.id

    if action == "toggle" and target_user_id and perm_code:
        # Toggle the permission state in temp permissions
        temp_permissions[target_user_id][perm_code] = not temp_permissions[target_user_id][perm_code]
        new_status = "✅" if temp_permissions[target_user_id][perm_code] else "❌"

        # Update button text with new status
        permissions = {
            "can_change_info": "Can Change Info",
            "can_delete_messages": "Can Delete Messages",
            "can_invite_users": "Can Invite Users",
            "can_restrict_members": "Can Restrict Members",
            "can_pin_messages": "Can Pin Messages",
            "can_promote_members": "Can Promote Members",
        }
        buttons = []
        for perm_name, code in permissions.items():
            status_emoji = "✅" if temp_permissions[target_user_id][code] else "❌"
            buttons.append(InlineKeyboardButton(f"{perm_name} {status_emoji}", callback_data=f"promote|toggle|{code}|{target_user_id}"))

        # Add Save and Close buttons
        buttons.append(InlineKeyboardButton("Save", callback_data=f"promote|save|{target_user_id}"))
        buttons.append(InlineKeyboardButton("Close", callback_data="promote|close"))

        # Organize buttons in rows and update the message
        markup = InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])
        callback_query.message.edit_reply_markup(markup)

        # Show alert confirming the permission toggle
        client.answer_callback_query(callback_query.id, f"{permissions[perm_code]} has been {'granted' if temp_permissions[target_user_id][perm_code] else 'removed'}.")

    elif action == "save" and target_user_id:
        # Apply permissions from temp_permissions
        permissions_to_set = temp_permissions[target_user_id]
        client.promote_chat_member(
            chat_id,
            target_user_id,
            can_change_info=permissions_to_set["can_change_info"],
            can_delete_messages=permissions_to_set["can_delete_messages"],
            can_invite_users=permissions_to_set["can_invite_users"],
            can_restrict_members=permissions_to_set["can_restrict_members"],
            can_pin_messages=permissions_to_set["can_pin_messages"],
            can_promote_members=permissions_to_set["can_promote_members"],
        )
        client.send_message(chat_id, "Permissions have been applied successfully.")
        del temp_permissions[target_user_id]
        client.answer_callback_query(callback_query.id, "Permissions saved successfully.")

    elif action == "close":
        callback_query.message.delete()
        client.answer_callback_query(callback_query.id, "Permissions selection closed without saving.")