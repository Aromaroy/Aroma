from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Aroma import app

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

    buttons = []
    permissions = {
        "Change Info": "can_change_info",
        "Delete Messages": "can_delete_messages",
        "Invite Users": "can_invite_users",
        "Restrict Members": "can_restrict_members",
        "Pin Messages": "can_pin_messages",
        "Promote Members": "can_promote_members",
    }

    temp_permissions[target_user_id] = {perm_code: False for perm_code in permissions.values()}

    for perm_name, perm_code in permissions.items():
        button_text = f"{perm_name} ❌"
        callback_data = f"promote|toggle|{perm_code}|{target_user_id}"
        buttons.append(InlineKeyboardButton(button_text, callback_data=callback_data))

    buttons.append(InlineKeyboardButton("Save", callback_data=f"promote|save|{target_user_id}"))
    buttons.append(InlineKeyboardButton("Close", callback_data="promote|close"))

    markup = InlineKeyboardMarkup([[button] for button in buttons])
    client.send_message(chat_id, "Choose permissions to grant:", reply_markup=markup)

@app.on_callback_query(filters.regex(r"promote\|"))
async def handle_permission_toggle(client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")
    action = data[1]
    perm_code = data[2] if len(data) > 2 else None
    target_user_id = int(data[3]) if len(data) > 3 and data[3].isdigit() else None
    chat_id = callback_query.message.chat.id

    permissions = {
        "can_change_info": "Change Info",
        "can_delete_messages": "Delete Messages",
        "can_invite_users": "Invite Users",
        "can_restrict_members": "Restrict Members",
        "can_pin_messages": "Pin Messages",
        "can_promote_members": "Promote Members",
    }

    if action == "toggle" and target_user_id and perm_code:
        try:
            if perm_code in temp_permissions[target_user_id]:
                temp_permissions[target_user_id][perm_code] = not temp_permissions[target_user_id][perm_code]

                buttons = []
                for code, name in permissions.items():
                    status_emoji = "✅" if temp_permissions[target_user_id][code] else "❌"
                    buttons.append(InlineKeyboardButton(f"{name} {status_emoji}", callback_data=f"promote|toggle|{code}|{target_user_id}"))

                buttons.append(InlineKeyboardButton("Save", callback_data=f"promote|save|{target_user_id}"))
                buttons.append(InlineKeyboardButton("Close", callback_data="promote|close"))

                markup = InlineKeyboardMarkup([[button] for button in buttons])
                await callback_query.message.edit_reply_markup(markup)

                await callback_query.answer(f"{permissions[perm_code]} has been {'granted' if temp_permissions[target_user_id][perm_code] else 'removed'}.", show_alert=True)

        except Exception as e:
            await callback_query.answer("Failed to toggle permission. Please try again.", show_alert=True)
            print(f"Error toggling permission: {e}")

    elif action == "save" and target_user_id:
        try:
            permissions_to_set = temp_permissions[target_user_id]
            print(f"Applying permissions for user {target_user_id}: {permissions_to_set}")
            await client.promote_chat_member(
                chat_id,
                target_user_id,
                **permissions_to_set
            )
            await client.send_message(chat_id, "Permissions have been applied successfully.")
            del temp_permissions[target_user_id]
            await callback_query.answer("Permissions saved successfully.", show_alert=True)
        except Exception as e:
            await client.send_message(chat_id, "Failed to apply permissions. Please try again.")
            print(f"Error applying permissions: {e}")

    elif action == "close":
        await callback_query.message.delete()
        await callback_query.answer("Permissions selection closed without saving.", show_alert=True)