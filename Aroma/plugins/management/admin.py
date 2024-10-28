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
        # Check bot's member status
        bot_member = client.get_chat_member(chat_id, bot_user.id)
        logging.info(f"Bot member status: {bot_member.status}, privileges: {bot_member.privileges}")

        if bot_member.status not in ['administrator', 'creator']:
            client.send_message(chat_id, "I need to be an admin to promote members.")
            return

        if not bot_member.privileges.can_promote_members:
            client.send_message(chat_id, "I don't have permission to promote members.")
            return

        # Check user's member status
        user_member = client.get_chat_member(chat_id, user_id)
        logging.info(f"User {user_id} status: {user_member.status}, privileges: {user_member.privileges}")

        if user_member.status != "administrator":
            client.send_message(chat_id, "You need to be an administrator to use this command.")
            return

        if not user_member.privileges.can_promote_members:
            client.send_message(chat_id, "You do not have permission to promote other users.")
            return

    except Exception as e:
        logging.error(f"Error checking permissions: {e}")
        client.send_message(chat_id, "An error occurred while checking permissions.")
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

@app.on_callback_query(filters.regex(r"promote_toggle_"))
def handle_permission_toggle(client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    perm_code = data[2]
    target_user_id = int(data[3])
    user_id = callback_query.from_user.id

    try:
        user_member = client.get_chat_member(callback_query.message.chat.id, user_id)
        logging.info(f"User {user_id} status: {user_member.status}, privileges: {user_member.privileges}")

        if user_member.status != "administrator":
            client.answer_callback_query(callback_query.id, "You need admin rights to perform this action.")
            return

        # Toggle the permission based on the current state
        if perm_code in user_member.privileges:
            new_privileges = user_member.privileges
            current_value = getattr(new_privileges, perm_code)

            # Create the permission toggle
            if current_value:
                new_privileges = new_privileges._replace(**{perm_code: False})
                client.promote_chat_member(chat_id, target_user_id, privileges=new_privileges)
                client.answer_callback_query(callback_query.id, f"{perm_code.replace('_', ' ').capitalize()} revoked.")
            else:
                new_privileges = new_privileges._replace(**{perm_code: True})
                client.promote_chat_member(chat_id, target_user_id, privileges=new_privileges)
                client.answer_callback_query(callback_query.id, f"{perm_code.replace('_', ' ').capitalize()} granted.")
        else:
            client.answer_callback_query(callback_query.id, "Invalid permission.")

    except Exception as e:
        logging.error(f"Error processing permission toggle: {e}")
        client.answer_callback_query(callback_query.id, "An error occurred while processing your request.")