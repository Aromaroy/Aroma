import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from Aroma import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_sticker_requests = {}

@app.on_message(filters.command(['q', 'q2', 'q3']) & filters.group)
async def create_stickers(client, message: Message):
    user_id = message.from_user.id
    command = message.command[0]
    
    if user_id not in user_sticker_requests:
        user_sticker_requests[user_id] = []

    replies = []
    if command == "q":
        replies.append(message.reply_to_message.text)
    elif command == "q2":
        if message.reply_to_message.reply_to_message:
            replies.append(message.reply_to_message.text)
            replies.append(message.reply_to_message.reply_to_message.text)
    elif command == "q3":
        if (message.reply_to_message.reply_to_message and
                message.reply_to_message.reply_to_message.reply_to_message):
            replies.append(message.reply_to_message.text)
            replies.append(message.reply_to_message.reply_to_message.text)
            replies.append(message.reply_to_message.reply_to_message.reply_to_message.text)

    for reply_text in replies:
        sticker = await create_sticker_from_text(reply_text)
        user_sticker_requests[user_id].append(sticker)

    await message.reply(f"{len(replies)} sticker(s) created!")

@app.on_message(filters.command('kang') & filters.reply & filters.group)
async def process_stickers(client, message: Message):
    user_id = message.from_user.id
    stickers = user_sticker_requests.get(user_id, [])

    if not stickers:
        await message.reply("No stickers to process.")
        return

    await message.reply("Processing your stickers...")
    sticker_pack = await create_sticker_pack(stickers)

    notification_message = "Your Sticker Pack has been created!"
    keyboard = [[InlineKeyboardButton("Save Sticker Pack", callback_data="save_sticker_pack")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await client.send_message(message.chat.id, notification_message, reply_markup=reply_markup)

async def create_sticker_from_text(text):
    return "sticker_id"

async def create_sticker_pack(stickers):
    return "sticker_pack_id"

@app.on_callback_query(filters.regex("save_sticker_pack"))
async def save_sticker_pack(client, callback_query):
    await callback_query.answer("Sticker pack saved successfully!")