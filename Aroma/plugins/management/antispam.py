import logging
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from config import MONGO_DB_URI
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Aroma import app

mongo_client = MongoClient(MONGO_DB_URI)
mongo_db = mongo_client["spam"]
mongo_collection = mongo_db["antispam"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_target_user_id(client, chat_id, message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    elif message.command[1:]:
        target_username = message.command[1]
        user = await client.get_users(target_username)
        return user.id
    return None

@app.on_message(filters.command('antispam') & filters.group)
async def antispam_enable(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    bot_member = await client.get_chat_member(chat_id, bot_user.id)

    if bot_member.status != ChatMemberStatus.ADMINISTRATOR or \
       not bot_member.privileges.can_change_info or \
       not bot_member.privileges.can_restrict_members or \
       not bot_member.privileges.can_delete_messages:
        await client.send_message(chat_id, "I lack necessary permissions.")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)
    if user_member.status != ChatMemberStatus.ADMINISTRATOR or \
       not user_member.privileges.can_change_info or \
       not user_member.privileges.can_restrict_members or \
       not user_member.privileges.can_delete_messages:
        await client.send_message(chat_id, "You lack necessary permissions.")
        return

    await client.send_message(chat_id, "Configure Anti-Spam:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Mute", callback_data="mute"), InlineKeyboardButton("Ban", callback_data="ban")],
        [InlineKeyboardButton("Delete Messages", callback_data="delete_messages")],
        [InlineKeyboardButton("Link Antispam", callback_data="link_antispam"), InlineKeyboardButton("Forward Antispam", callback_data="forward_antispam")],
        [InlineKeyboardButton("Back", callback_data="back"), InlineKeyboardButton("Next", callback_data="next")]
    ]))

@app.on_callback_query(filters.regex(r'^(mute|ban|delete_messages|link_antispam|forward_antispam|back|next)$'))
async def handle_antispam_options(client, query):
    chat_id = query.message.chat.id
    user_member = await client.get_chat_member(chat_id, query.from_user.id)

    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await query.answer("You are not an admin.", show_alert=True)
        return

    if query.data in ["mute", "ban"]:
        await query.answer(f"{query.data.capitalize()} selected.")
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Mute ✅", callback_data="mute"), InlineKeyboardButton("Ban ❌", callback_data="ban")],
            [InlineKeyboardButton("Delete Messages", callback_data="delete_messages")],
            [InlineKeyboardButton("Link Antispam", callback_data="link_antispam"), InlineKeyboardButton("Forward Antispam", callback_data="forward_antispam")],
            [InlineKeyboardButton("Back", callback_data="back"), InlineKeyboardButton("Next", callback_data="next")]
        ]))

    elif query.data == "delete_messages":
        await query.answer("Delete Messages option selected.")
    
    elif query.data in ["link_antispam", "forward_antispam"]:
        await query.answer(f"{query.data.replace('_', ' ').capitalize()} option selected.")

    elif query.data == "back":
        await query.message.delete()

    elif query.data == "next":
        await client.send_message(chat_id, "Select mute/ban duration:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("No time", callback_data="duration_no_time"), InlineKeyboardButton("1 min", callback_data="duration_1min")],
            [InlineKeyboardButton("3 min", callback_data="duration_3min"), InlineKeyboardButton("5 min", callback_data="duration_5min")],
            [InlineKeyboardButton("10 min", callback_data="duration_10min"), InlineKeyboardButton("20 min", callback_data="duration_20min")],
            [InlineKeyboardButton("30 min", callback_data="duration_30min"), InlineKeyboardButton("40 min", callback_data="duration_40min")],
            [InlineKeyboardButton("50 min", callback_data="duration_50min"), InlineKeyboardButton("1 hr", callback_data="duration_1hr")],
            [InlineKeyboardButton("Back", callback_data="back_save"), InlineKeyboardButton("Save", callback_data="save")]
        ]))

@app.on_callback_query(filters.regex(r'^duration_'))
async def handle_duration_selection(client, query):
    await query.answer("Duration selected.")

@app.on_callback_query(filters.regex(r'^save$'))
async def save_antispam_settings(client, query):
    await query.answer("Anti-spam settings saved.")

async def update_warnings(user_id, chat_id, reason):
    user_record = mongo_collection.find_one({"user_id": user_id, "chat_id": chat_id})
    if user_record:
        new_warning_count = user_record['warnings'] + 1
        mongo_collection.update_one({"user_id": user_id, "chat_id": chat_id}, {"$set": {"warnings": new_warning_count}})
    else:
        new_warning_count = 1
        mongo_collection.insert_one({"user_id": user_id, "chat_id": chat_id, "warnings": new_warning_count})
    return new_warning_count

@app.on_message(filters.text & filters.group)
async def handle_messages(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_member = await client.get_chat_member(chat_id, user_id)
    
    if user_member.status == ChatMemberStatus.ADMINISTRATOR:
        return
    
    settings = await mongo_collection.find_one({"chat_id": chat_id})
    if not settings:
        return

    link_antispam = settings.get("link_antispam", False)
    forward_antispam = settings.get("forward_antispam", False)

    if link_antispam and "http" in message.text:
        warning_count = await update_warnings(user_id, chat_id, "sent a link")
        await client.send_message(chat_id, f"User {message.from_user.mention} has {warning_count}/3 warnings; be careful! Reason: sent a link.")
        if warning_count >= 3:
            await client.ban_chat_member(chat_id, user_id)
            await client.send_message(chat_id, f"User {message.from_user.mention} is banned for sending a link.")
    
    if forward_antispam and message.forward_from:
        warning_count = await update_warnings(user_id, chat_id, "sent a forwarded message")
        await client.send_message(chat_id, f"User {message.from_user.mention} has {warning_count}/3 warnings; be careful! Reason: sent a forwarded message.")
        if warning_count >= 3:
            await client.ban_chat_member(chat_id, user_id)
            await client.send_message(chat_id, f"User {message.from_user.mention} is banned for sending a forwarded message.")

@app.on_callback_query(filters.regex(r'^unmute:'))
async def unmute_user(client, query):
    _, target_user_id, chat_id = query.data.split(':')
    target_user_id = int(target_user_id)
    chat_id = int(chat_id)

    user_member = await client.get_chat_member(chat_id, query.from_user.id)
    if user_member.status != ChatMemberStatus.ADMINISTRATOR or not user_member.privileges.can_restrict_members:
        await query.answer("You cannot unmute this user.", show_alert=True)
        return

    await client.unban_chat_member(chat_id, target_user_id)
    await query.answer(f"User has been unmuted.", show_alert=True)
    await client.delete_messages(chat_id, query.message.id)

@app.on_callback_query(filters.regex(r'^unban:'))
async def unban_user(client, query):
    _, target_user_id, chat_id = query.data.split(':')
    target_user_id = int(target_user_id)
    chat_id = int(chat_id)

    user_member = await client.get_chat_member(chat_id, query.from_user.id)
    if user_member.status != ChatMemberStatus.ADMINISTRATOR or not user_member.privileges.can_restrict_members:
        await query.answer("You cannot unban this user.", show_alert=True)
        return

    await client.unban_chat_member(chat_id, target_user_id)
    await query.answer(f"User has been unbanned.", show_alert=True)
    await client.delete_messages(chat_id, query.message.id)