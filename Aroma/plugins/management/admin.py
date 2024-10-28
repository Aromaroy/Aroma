from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from Aroma import bot

@bot.message_handler(commands=['promote'])
def promote_user(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot_user = bot.get_me()

    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    else:
        try:
            target_user_id = int(message.text.split()[1])
        except (IndexError, ValueError):
            target_username = message.text.split()[1].replace('@', '') if len(message.text.split()) > 1 else None
            if target_username:
                target_user = bot.get_chat_member(chat_id, target_username)
                if not target_user:
                    bot.reply_to(message, "User not found.")
                    return
                target_user_id = target_user.user.id
            else:
                bot.reply_to(message, "Please specify a user to promote by username, user ID, or replying to their message.")
                return

    bot_member = bot.get_chat_member(chat_id, bot_user.id)
    if not bot_member.can_promote_members:
        bot.reply_to(message, "I don't have permission to promote members.")
        return

    user_member = bot.get_chat_member(chat_id, user_id)
    if not user_member.is_chat_admin() or not user_member.can_promote_members:
        bot.reply_to(message, "You need admin rights with permission to add admins to use this command.")
        return

    # Check if the target user is already an admin
    target_user_member = bot.get_chat_member(chat_id, target_user_id)
    if target_user_member.is_chat_admin():
        bot.reply_to(message, "This user is already promoted by someone else.")
        return

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
        if getattr(user_member, perm_code, False):
            button_text = f"{perm_name} ✅"
            callback_data = f"promote_toggle_{perm_code}_{target_user_id}"
        else:
            button_text = f"🔒 {perm_name}"
            callback_data = f"promote_locked_{perm_code}"

        markup.add(InlineKeyboardButton(button_text, callback_data=callback_data))

    bot.send_message(chat_id, "Choose permissions to grant:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("promote"))
def handle_permission_toggle(call):
    data = call.data.split("_")
    action = data[1]
    perm_code = data[2]
    target_user_id = data[3]

    if action == "toggle":
        bot.answer_callback_query(call.id, f"Toggled {perm_code} for user {target_user_id}")
    elif action == "locked":
        bot.answer_callback_query(call.id, "You don't have permission to grant this.")