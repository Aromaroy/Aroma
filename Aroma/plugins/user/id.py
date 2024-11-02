from pyrogram import filters, Client
from pyrogram.enums import ParseMode
from Aroma import app

@app.on_message(filters.command('id'))
async def get_id(client: Client, message):
    chat = message.chat
    your_id = message.from_user.id
    message_id = message.id
    reply = message.reply_to_message

    try:
        processing_message = await message.reply("Fetching IDs...")

        text = f"**[Message ID:]({message.link})** `{message_id}`\n"
        text += f"**[Your ID:](tg://user?id={your_id})** `{your_id}`\n"

        if len(message.command) == 2:
            try:
                split = message.text.split(None, 1)[1].strip()
                user_id = (await client.get_users(split)).id
                text += f"**[User ID:](tg://user?id={user_id})** `{user_id}`\n"
            except Exception:
                text = "This user doesn't exist."
                await processing_message.edit(text)
                return

        text += f"**[Chat ID:](https://t.me/{chat.username})** `{chat.id}`\n\n"

        if reply and not reply.forward_from_chat and not reply.sender_chat:
            text += f"**[Replied Message ID:]({reply.link})** `{reply.id}`\n"
            text += f"**[Replied User ID:](tg://user?id={reply.from_user.id})** `{reply.from_user.id}`\n\n"

        if reply and reply.forward_from_chat:
            text += f"The forwarded channel, {reply.forward_from_chat.title}, has an ID of `{reply.forward_from_chat.id}`\n\n"

        if reply and reply.sender_chat:
            text += f"ID of the replied chat/channel is `{reply.sender_chat.id}`"

        await message.reply(
            text,
            disable_web_page_preview=True,
            parse_mode=ParseMode.DEFAULT,
        )

    except Exception as e:
        await message.reply(f"Error: {e}")