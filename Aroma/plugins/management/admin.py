import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPrivileges
from Aroma import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

temporary_permissions = {}
temporary_messages = {}

@app.on_message(filters.command('promote') & filters.group)
async def promote_user(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)
        if not bot_member.privileges.can_promote_members:
            await client.send_message(chat_id, "ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ ᴍᴇᴍᴇʙᴇʀꜱ.")
            return
    except Exception as e:
        await client.send_message(chat_id, f"Error retrieving bot status: {e}")
        logger.error(f"Error retrieving bot status: {e}")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)

    if not user_member.privileges:
        await client.send_message(chat_id, "ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ.")
        return

    if not user_member.privileges.can_promote_members:
        await client.send_message(chat_id, "ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴅᴅ ᴀᴅᴍɪɴ ʀɪɢʜᴛ.")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        return

    if target_user_id not in temporary_permissions:
        temporary_permissions[target_user_id] = initialize_permissions(bot_member.privileges)

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🕹 ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ", callback_data=f"promote|permissions|{target_user_id}"),
         InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data=f"promote|close|{target_user_id}")]
    ])

    await client.send_message(chat_id, "Select an option:", reply_markup=markup)

async def get_target_user_id(client, chat_id, message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id

    if len(message.command) > 1:
        target_identifier = message.command[1]
        if target_identifier.isdigit():
            return int(target_identifier)

        try:
            target_user = await client.get_chat_member(chat_id, target_identifier.replace('@', ''))
            return target_user.user.id
        except Exception:
            await client.send_message(chat_id, "ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ ᴏʀ ɴᴏᴛ ᴀ ᴍᴇᴍʙᴇʀ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ.")
            logger.warning(f"User not found for identifier: {target_identifier}")
            return None
    else:
        await client.send_message(chat_id, "ᴘʟᴇᴀꜱᴇ ꜱᴘᴇᴄɪꜰʏ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ ʙʏ ᴜꜱᴇʀɴᴀᴍᴇ, ᴜꜱᴇʀ ɪᴅ, ᴏʀ ʀᴇᴘʟʏɪɴɢ ᴛᴏ ᴛʜᴇɪʀ ᴍᴇꜱꜱᴀɢᴇ..")
        return None

def initialize_permissions(bot_privileges):
    return {
        "can_change_info": False,
        "can_invite_users": False,
        "can_delete_messages": False,
        "can_restrict_members": False,
        "can_pin_messages": False,
        "can_promote_members": False,
        "can_manage_chat": False,
        "can_manage_video_chats": False,
    }

@app.on_callback_query(filters.regex(r"promote\|permissions\|"))
async def show_permissions(client, callback_query: CallbackQuery):
    user_member = await client.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)

    if not user_member.privileges or not user_member.privileges.can_promote_members:
        await callback_query.answer("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ᴏʀ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴜꜱᴇʀ ᴘʀᴏᴍᴏᴛɪɴɢ ʀɪɢʜᴛ.", show_alert=True)
        return

    target_user_id = int(callback_query.data.split("|")[-1])
    chat_id = callback_query.message.chat.id

    target_member = await client.get_chat_member(chat_id, target_user_id)
    target_user_name = target_member.user.first_name or target_member.user.username or "User"
    group_name = (await client.get_chat(chat_id)).title

    markup = create_permission_markup(target_user_id, await get_chat_privileges(callback_query))

    await callback_query.message.edit_text(
        f"👤 {target_user_name} [{target_user_id}]\n👥 {group_name}",
        reply_markup=markup
    )
    await callback_query.answer()

def create_permission_markup(target_user_id, admin_privileges):
    buttons = []
    button_names = {
        "can_change_info": "ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɪɴꜰᴏ",
        "can_invite_users": "ɪɴᴠɪᴛᴇ ᴜꜱᴇʀ'ꜱ ᴠɪᴇᴡ ʟɪɴᴋ",
        "can_delete_messages": "ᴅᴇʟᴇᴛᴇ ᴍᴇꜱꜱᴀɢᴇꜱ",
        "can_restrict_members": "ʙᴀɴ ᴜꜱᴇʀꜱ",
        "can_pin_messages": "ᴘɪɴ ᴍᴇꜱꜱᴀɢᴇꜱ",
        "can_promote_members": "ᴀᴅᴅ ɴᴇᴡ ᴍᴇᴍʙᴇʀꜱ",
        "can_manage_chat": "ᴍᴀɴᴀɢᴇ ꜱᴛᴏʀɪᴇꜱ",
        "can_manage_video_chats": "ᴍᴀɴᴀɢᴇ ʟɪᴠᴇ ꜱᴛʀᴇᴀᴍꜱ ",
    }

    for perm, state in temporary_permissions[target_user_id].items():
        can_grant = getattr(admin_privileges, perm, False)
        icon = "🔒" if not can_grant else "✅" if state else "❌"
        button_label = button_names.get(perm, perm.replace('can_', '').replace('_', ' ').capitalize())
        callback_data = f"promote|toggle|{perm}|{target_user_id}"
        buttons.append(InlineKeyboardButton(f"{button_label} {icon}", callback_data=callback_data))

    save_button = InlineKeyboardButton("ꜱᴀᴠᴇ", callback_data=f"promote|save|{target_user_id}")
    close_button = InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data=f"promote|close|{target_user_id}")

    buttons.append(save_button)
    buttons.append(close_button)

    button_rows = [buttons[i:i + 1] for i in range(0, len(buttons) - 2)]
    button_rows.append([save_button, close_button])

    return InlineKeyboardMarkup(button_rows)

@app.on_callback_query(filters.regex(r"promote\|"))
async def handle_permission_toggle(client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")

    if len(data) < 3:
        await callback_query.answer("Invalid callback data. Please try again.", show_alert=True)
        logger.error(f"Invalid callback data received: {callback_query.data}")
        return

    action = data[1]
    target_user_id = int(data[-1])

    user_member = await callback_query._client.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
    if not user_member.privileges or not user_member.privileges.can_promote_members:
        await callback_query.answer("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ᴏʀ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴜꜱᴇʀ ᴘʀᴏᴍᴏᴛɪɴɢ ʀɪɢʜᴛ.", show_alert=True)
        return

    if action == "toggle":
        await toggle_permission(callback_query, target_user_id, data[2])
    elif action == "save":
        await save_permissions(callback_query._client, callback_query, target_user_id)
    elif action == "close":
        await close_permission_selection(callback_query)

async def toggle_permission(callback_query, target_user_id, perm_code):
    if target_user_id in temporary_permissions:
        permissions_dict = temporary_permissions[target_user_id]
        permissions_dict[perm_code] = not permissions_dict[perm_code]

        markup = create_permission_markup(target_user_id, await get_chat_privileges(callback_query))
        await callback_query.message.edit_reply_markup(markup)
        await callback_query.answer(f"{perm_code.replace('can_', '').replace('_', ' ').capitalize()} ", show_alert=True)
    else:
        await callback_query.answer("No permissions found for this user.", show_alert=True)

async def get_chat_privileges(callback_query):
    user_member = await callback_query._client.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
    return user_member.privileges

async def save_permissions(client, callback_query, target_user_id):
    if target_user_id in temporary_permissions:
        permissions = temporary_permissions.pop(target_user_id)
        privileges = ChatPrivileges(**permissions)

        chat_id = callback_query.message.chat.id
        try:
            await client.promote_chat_member(chat_id, target_user_id, privileges=privileges)
            updated_member = await client.get_chat_member(chat_id, target_user_id)
            user_name = updated_member.user.first_name or updated_member.user.username or "User"
            await callback_query.message.delete()
            await callback_query.answer(f"{user_name} ʜᴀꜱ ʙᴇᴇɴ ᴘʀᴏᴍᴏᴛᴇᴅ.", show_alert=True)

            if target_user_id in temporary_messages:
                await temporary_messages[target_user_id].delete()
                del temporary_messages[target_user_id]

        except Exception as e:
            await callback_query.answer(f"Failed to promote user: {str(e)}", show_alert=True)
            logger.error(f"Error promoting user {target_user_id} with privileges {privileges}: {e}")
    else:
        await callback_query.answer("No permissions found for this user.", show_alert=True)

async def close_permission_selection(callback_query):
    await callback_query.message.delete()
    target_user_id = int(callback_query.data.split("|")[-1])

    if target_user_id in temporary_messages:
        await temporary_messages[target_user_id].delete()
        del temporary_messages[target_user_id]

    await callback_query.answer("ᴘᴇʀᴍɪꜱꜱɪᴏɴ ꜱᴇʟᴇᴄᴛɪᴏɴ ᴄʟᴏꜱᴇᴅ.", show_alert=True)

async def cleanup_temporary_permissions():
    pass

@app.on_message(filters.command('demote') & filters.group)
async def demote_user(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)
        if not bot_member.privileges.can_promote_members:
            await client.send_message(chat_id, "ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴛᴏ ᴅᴇᴍᴏᴛᴇ ᴍᴇᴍʙᴇʀꜱ.")
            return
    except Exception as e:
        await client.send_message(chat_id, f"Error retrieving bot status: {e}")
        logger.error(f"Error retrieving bot status: {e}")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)

    if not user_member.privileges or not user_member.privileges.can_promote_members:
        await client.send_message(chat_id, "ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ.")
        return

    target_user_id = await get_target_user_id(client, chat_id, message)
    if target_user_id is None:
        return

    target_member = await client.get_chat_member(chat_id, target_user_id)

    if not target_member.privileges:
        await client.send_message(chat_id, f"{target_member.user.first_name} ɪs ᴀʟʀᴇᴀᴅʏ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ.")
        return

    if target_member.privileges.can_promote_members:
        await client.send_message(chat_id, f"{target_member.user.first_name} ɪs ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ.")
        return

    promoted_by = target_member.privileges.promoted_by if hasattr(target_member.privileges, 'promoted_by') else None
    if promoted_by == bot_user.id or promoted_by is None:
        try:
            await client.promote_chat_member(chat_id, target_user_id, privileges=ChatPrivileges(
                can_change_info=False,
                can_invite_users=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_chat=False,
                can_manage_video_chats=False,
            ))
            await client.send_message(chat_id, f"{target_member.user.first_name} ʜᴀꜱ ʙᴇᴇɴ ᴅᴇᴍᴏᴛᴇᴅ.")
        except Exception as e:
            await client.send_message(chat_id, f"Failed to demote user: {str(e)}")
            logger.error(f"Error demoting user {target_user_id}: {e}")
    else:
        await client.send_message(chat_id, f"{target_member.user.first_name} ᴄᴀɴ'ᴛ ʙᴇ ᴅᴇᴍᴏᴛᴇᴅ. ᴛʜʏ ᴡᴇʀᴇ ᴘʀᴏᴍᴏᴛᴇᴅ ʙʏ {promoted_by}.")