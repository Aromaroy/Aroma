from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Aroma import app

@app.on_message(filters.command('promote'))
def promote_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot_user = client.get_me()

    # Determine target user ID
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

    # Check bot's permissions
    bot_member = client.get_chat_member(chat_id, bot_user.id)
    bot_can_promote = getattr(bot_member.privileges, 'can_promote_members', False)
    if not bot_can_promote:
        client.send_message(chat_id, "I don't have permission to promote members.")
        return

    # Check user's admin status
    user_member = client.get_chat_member(chat_id, user_id)
    user_can_promote = getattr(user_member.privileges, 'can_promote_members', False) if user_member.status == "administrator" else False

    print(f"Bot's can_promote_members: {bot_can_promote}")
    print(f"User's admin status: {user_member.status}")
    print(f"User can promote: {user_can_promote}, Privileges: {user_member.privileges}")

    if not user_can_promote:
        client.send_message(chat_id, "You need admin rights with permission to add admins to use this command.")
        return

    target_user_member = client.get_chat_member(chat_id, target_user_id)
    if target_user_member.status in ['administrator', 'creator']:
        client.send_message(chat_id, "This user is already promoted by someone else.")
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
    user_member = client.get_chat_member(callback_query.message.chat.id, user_id)

    if user_member.status != "administrator":
        client.answer_callback_query(callback_query.id, "You need admin rights to perform this action.")
        return

    if action == "toggle":
        # Here, you would implement the actual permission toggling logic
        client.answer_callback_query(callback_query.id, f"Toggled {perm_code} for user {target_user_id}")
    elif action == "locked":
        client.answer_callback_query(callback_query.id, "You don't have permission to grant this.")