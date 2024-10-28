import logging
from Aroma import app 
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.INFO)

PERMISSION_LIST = [
    ("can_change_info", "Change Group Info"),
    ("can_post_messages", "Post Messages"),
    ("can_edit_messages", "Edit Messages"),
    ("can_delete_messages", "Delete Messages"),
    ("can_invite_users", "Invite Users"),
    ("can_restrict_members", "Restrict Members"),
    ("can_pin_messages", "Pin Messages"),
    ("can_promote_members", "Promote Members"),
]

@app.on_message(filters.command("promote") & filters.group)
async def promote_user(client, message):
    bot_member = await client.get_chat_member(message.chat.id, client.me.id)
    bot_permissions = bot_member.permissions

    # Log bot permissions for debugging
    logging.info(f"Bot permissions: {bot_permissions}")

    # Check if the bot has permission to promote members
    if not (hasattr(bot_permissions, 'can_promote_members') and bot_permissions.can_promote_members):
        await message.reply("I need to be an admin to promote members.")
        return

    user = message.from_user
    if not user or not user.is_admin:
        await message.reply("You need to be an administrator to use this command.")
        return

    target_user_id = await get_target_user_id(message)
    if target_user_id is None:
        await message.reply("Please specify a user to promote by username, user ID, or replying to their message.")
        return

    if not await is_user_promotable(client, message.chat.id, target_user_id):
        await message.reply("This user is already an administrator or cannot be promoted.")
        return

    await display_permission_buttons(client, message.chat.id, user.id, target_user_id)

async def get_target_user_id(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    elif message.command and len(message.command) > 1:
        try:
            username = message.command[1]
            user = await app.get_users(username)
            return user.id
        except Exception as e:
            logging.error(f"Error getting user by username: {e}")
            return None
    return None

async def is_user_promotable(client, chat_id, user_id):
    member = await client.get_chat_member(chat_id, user_id)
    return not member.status in ("administrator", "creator")

async def display_permission_buttons(client, chat_id, admin_id, target_user_id):
    admin_permissions = await client.get_chat_member(chat_id, admin_id)
    keyboard = []

    for perm, perm_name in PERMISSION_LIST:
        if hasattr(admin_permissions.permissions, perm) and getattr(admin_permissions.permissions, perm):
            keyboard.append([InlineKeyboardButton(perm_name, callback_data=f"set_perm_{perm}_{target_user_id}")])
        else:
            keyboard.append([InlineKeyboardButton(f"{perm_name} (You lack this permission)", callback_data="no_permission")])

    await client.send_message(chat_id, "Choose permissions to grant:", reply_markup=InlineKeyboardMarkup(keyboard))

@app.on_callback_query(filters.regex(r"set_perm_(\w+)_(\d+)"))
async def handle_permission_toggle(client, callback_query):
    perm = callback_query.data.split("_")[1]
    user_id = int(callback_query.data.split("_")[2])
    chat_id = callback_query.message.chat.id

    try:
        if perm in [p[0] for p in PERMISSION_LIST]:
            await client.promote_chat_member(chat_id, user_id, **{perm: True})
            save_keyboard = [
                [InlineKeyboardButton("Save", callback_data=f"save_perm_{perm}_{user_id}")],
            ]
            await callback_query.answer(f"{perm.replace('_', ' ').title()} granted.")
            await client.send_message(chat_id, f"{perm.replace('_', ' ').title()} granted to the user.", reply_markup=InlineKeyboardMarkup(save_keyboard))
        else:
            await callback_query.answer("Invalid permission.")
    except Exception as e:
        logging.error(f"Error granting permission: {e}")
        await callback_query.answer("An error occurred while granting permissions.")

@app.on_callback_query(filters.regex(r"save_perm_(\w+)_(\d+)"))
async def handle_save_permission(callback_query):
    perm = callback_query.data.split("_")[1]
    user_id = int(callback_query.data.split("_")[2])
    chat_id = callback_query.message.chat.id
    await callback_query.answer("Permission has been granted and saved successfully!", show_alert=True)
    await client.send_message(chat_id, f"Permission '{perm.replace('_', ' ').title()}' has been saved for the user.")

@app.on_callback_query(filters.regex(r"no_permission"))
async def handle_no_permission(callback_query):
    await callback_query.answer("You don't have the permission to grant this right.")