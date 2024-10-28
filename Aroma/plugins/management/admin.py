
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Aroma import app
import logging

logging.basicConfig(level=logging.INFO)

@app.on_message(filters.command('promote') & filters.group)
def promote_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot_user = client.get_me()

    try:
        bot_member = client.get_chat_member(chat_id, bot_user.id)
        logging.info(f"Bot member status: {bot_member.status}, privileges: {bot_member.privileges}")

        if not bot_member.privileges.can_promote_members:
            client.send_message(chat_id, "I don't have permission to promote members.")
            return
    except Exception as e:
        client.send_message(chat_id, "Error retrieving bot status.")
        logging.error(f"Error retrieving bot member status: {e}")
        return

    try:
        user_member = client.get_chat_member(chat_id, user_id)
        logging.info(f"User {user_id} status: {user_member.status}, privileges: {user_member.privileges}")

        if user_member.status != "administrator":
            client.send_message(chat_id, "You need to be an administrator to use this command.")
            return

        if not user_member.privileges.can_promote_members:
            client.send_message(chat_id, "You do not have permission to promote other users.")
            return

    except Exception as e:
        client.send_message(chat_id, "Error retrieving your status.")
        logging.error(f"Error retrieving user member status: {e}")
        return

    target_user_id = get_target_user_id(client, message, chat_id)
    if target_user_id is None:
        client.send_message(chat_id, "Please specify a user to promote by username, user ID, or replying to their message.")
        return

    if not is_user_promotable(client, chat_id, target_user_id):
        client.send_message(chat_id, "This user is already promoted by someone else.")
        return

    display_permission_buttons(client, chat_id, user_member, target_user_id)

def get_target_user_id(client, message, chat_id):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    else:
        try:
            return int(message.command[1])
        except (IndexError, ValueError):
            target_username = message.command[1].replace('@', '') if len(message.command) > 1 else None
            if target_username:
                try:
                    target_user = client.get_chat_member(chat_id, target_username)
                    return target_user.user.id
                except Exception as e:
                    logging.error(f"Error retrieving target user by username: {e}")
                    return None
            return None

def is_user_promotable(client, chat_id, target_user_id):
    try:
        target_user_member = client.get_chat_member(chat_id, target_user_id)
        logging.info(f"Target user {target_user_id} status: {target_user_member.status}")
        return target_user_member.status not in ['administrator', 'creator']
    except Exception as e:
        logging.error(f"Error retrieving target user member status: {e}")
        return False

def display_permission_buttons(client, chat_id, user_member, target_user_id):
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
        button_text = f"{perm_name} ✅" if getattr(user_member.privileges, perm_code, False) else f"🔒 {perm_name}"
        callback_data = f"promote_toggle_{perm_code}_{target_user_id}" if getattr(user_member.privileges, perm_code, False) else f"promote_locked_{perm_code}"
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
        logging.info(f"User {user_id} status: {user_member.status}, privileges: {user_member.privileges}")

        if user_member.status != "administrator":
            client.answer_callback_query(callback_query.id, "You need admin rights to perform this action.")
            return

        if action == "toggle":
            client.answer_callback_query(callback_query.id, f"Toggled {perm_code} for user {target_user_id}.")
            # Implement logic to grant or revoke the permission
        elif action == "locked":
            client.answer_callback_query(callback_query.id, "You don't have permission to grant this.")
    except Exception as e:
        client.answer_callback_query(callback_query.id, "Error retrieving your status.")
        logging.error(f"Error retrieving user member status in callback: {e}")