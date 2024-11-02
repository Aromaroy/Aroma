import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont
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

    created_stickers = []
    for reply_text in replies:
        sticker = await create_sticker_from_text(message, reply_text)
        user_sticker_requests[user_id].append(sticker)
        created_stickers.append(sticker)

    for sticker in created_stickers:
        await message.reply_sticker(sticker)

    await message.reply(f"{len(replies)} sticker(s) created!")

@app.on_message(filters.command('kang') & filters.reply & filters.group)
async def process_stickers(client, message: Message):
    user_id = message.from_user.id
    stickers = user_sticker_requests.get(user_id, [])

    if not stickers:
        await message.reply("No stickers to process.")
        return

    await message.reply("Creating your sticker pack...")
    for sticker in stickers:
        await message.reply_sticker(sticker)

    await message.reply("Your stickers have been sent!")

async def create_sticker_from_text(message, text):
    user = message.from_user
    full_name = f"{user.first_name} {user.last_name or ''}".strip()  # Handle potential missing last name
    formatted_text = f"{full_name}:\n{text}"  # Format the text as in the chat
    img_path = await generate_image_from_text(formatted_text)
    with open(img_path, 'rb') as img:
        sticker = await app.send_sticker(chat_id=message.chat.id, sticker=img)
    return sticker.sticker.file_id

async def generate_image_from_text(formatted_text):
    img = Image.new('RGBA', (512, 512), color=(255, 255, 255, 0))  # Transparent background
    draw = ImageDraw.Draw(img)
    
    # Load default font
    font = ImageFont.load_default()
    
    # Draw the formatted text
    draw.text((10, 10), formatted_text, fill=(0, 0, 0), font=font)  # Draw the message text

    img_path = "temp_sticker.webp"
    img.save(img_path, format='WEBP')  # Save as WebP
    return img_path

@app.on_callback_query(filters.regex("save_sticker_pack"))
async def save_sticker_pack(client, callback_query):
    await callback_query.answer("Sticker pack saved successfully!")