from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Aroma import app

@app.on_message(filters.command('promote') & filters.group)
def promote_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot_user = client.get_me()

    print("Received promote command.")

    # Check bot's permissions
    try:
        bot_member = client.get_chat_member(chat_id, bot_user.id)
        if not bot_member.privileges.can_promote_members:
            client.send_message(chat_id, "I don't have permission to promote members.")
            return
    except Exception as e:
        client.send_message(chat_id, "Error retrieving bot status.")
        print(f"Error retrieving bot member status: {e}")
        return

    # Check user's admin status and permissions
    try:
        user_member = client.get_chat_member(chat_id, user_id)
        print(f"User ID: {user_id}, Status: {user_member.status}")

        if user_member.status != "administrator":
            client.send_message(chat_id, "You need to be an administrator to use this command.")
            return
        
        if not user_member.privileges.can_promote_members:
            client.send_message(chat_id, "You do not have permission to promote other users.")
            return

    except Exception as e:
        client.send_message(chat_id, "Error retrieving your status.")
        print(f"Error retrieving user member status: {e}")
        return

    # Determine target user ID
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

    # Check target user's status
    try:
        target_user_member = client.get_chat_member(chat_id, target_user_id)
        if target_user_member.status in ['administrator', 'creator']:
            client.send_message(chat_id, "This user is already promoted by someone else.")
            return
    except Exception as e:
        client.send_message(chat_id, "Error retrieving target user's status.")
        print(f"Error retrieving target user member status: {e}")
        return

    # Create InlineKeyboard for permissions
    markup = InlineKeyboardMarkup(row_width=2)
    permissions = {
        "Can Change Info": "can_change_info",
        "Can Delete Messages": "can_delete_messages",
        "Can Invite Users": "can_invite_users",
        "Can Restrict Members": "can_restrict_members",
        "Can Pin Messages": "can_pin_messages",
        "Can Promote Members": "can_promote_members",
    }

    for perm_name, perm_code in permissions.items():
        if getattr(user_member.privileges, perm_code, False):
            button_text = f"{perm_name} ✅"
            callback_data = f"promote_toggle_{perm_code}_{target_user_id}"
        else:
            button_text = f"🔒 {perm_name}"
            callback_data = f"promote_locked_{perm_code}"

        markup.add(InlineKeyboardButton(button_text, callback_data=callback_data))

    client.send_message(chat_id, "Choose permissions to grant:", reply_markup=markup)

@app.on_callback_query(filters.regex(r"promote_"))
def handle_permission_toggle(client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    action = data[1]
    perm_code = data[2]
    target_user_id = int(data[3])

    user_id = callback_query.from_user.id
    try:
        user_member = client.get_chat_member(callback_query.message.chat.id, user_id)

        if user_member.status != "administrator":
            client.answer_callback_query(callback_query.id, "You need admin rights to perform this action.")
            return

        # Implement actual permission toggling logic here.
        if action == "toggle":
            # Here you would include the logic to change the permission
            client.answer_callback_query(callback_query.id, f"Toggled {perm_code} for user {target_user_id}")
        elif action == "locked":
            client.answer_callback_query(callback_query.id, "You don't have permission to grant this.")
    
    except Exception as e:
        client.answer_callback_query(callback_query.id, "Error retrieving your status.")
        print(f"Error retrieving user member status in callback: {e}")

@app.on_message(filters.command('check_admin') & filters.group)
def check_admin(client, message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        user_member = client.get_chat_member(chat_id, user_id)
        client.send_message(chat_id, f"User ID: {user_id}, Status: {user_member.status}")
    except Exception as e:
        client.send_message(chat_id, "Error retrieving your status.")
        print(f"Error retrieving user member status: {e}")