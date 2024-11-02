import logging
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus
from Aroma import app

@app.on_message(filters.command('info'))
async def get_user_info(client: Client, message):
    chat = message.chat
    reply = message.reply_to_message
    user_id = None

    if len(message.command) == 2:
        user_input = message.text.split(None, 1)[1].strip()
        try:
            user = await client.get_users(user_input)
            user_id = user.id
        except Exception:
            await message.reply("This user doesn't exist.")
            return
    elif reply and reply.from_user:
        user_id = reply.from_user.id
    else:
        await message.reply("Please provide a user ID, username, or reply to a user.")
        return

    try:
        user = await client.get_users(user_id)

        # Prepare the user info text
        text = (
            f"**User Info:**\n"
            f"ID: `{user.id}`\n"
            f"Name: {user.first_name or 'No name'}\n"
            f"Username: @{user.username if user.username else 'No username'}\n"
            f"User link: [link](tg://user?id={user.id})\n"
            f"DC ID: `{user.dc_id}`\n"
            f"Premium: {'Yes' if user.is_premium else 'No'}\n"
        )

        # Only check member status if in a group chat
        if chat.type in ["supergroup", "group"]:
            try:
                member = await client.get_chat_member(chat.id, user_id)
                user_status = "Admin" if member.status == ChatMemberStatus.ADMINISTRATOR else "Non-Admin"
                text = text.replace("DC ID: ", f"Status: {user_status}\nDC ID: ")
            except Exception as e:
                logging.error(f"Failed to get member status: {e}")
                text = text.replace("DC ID: ", f"Status: Unknown\nDC ID: ")

        await message.reply(
            text,
            disable_web_page_preview=True,
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        await message.reply(f"Error: {e}")