import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo import MongoClient
from config import MONGO_DB_URI
import asyncio
from Aroma import app
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mongo_client = MongoClient(MONGO_DB_URI)
db = mongo_client['raid_db']
raid_collection = db['raid_settings']

async def set_raid_settings(chat_id, duration, user_limit):
    end_time = datetime.now() + timedelta(seconds=duration)
    raid_data = {
        "chat_id": chat_id,
        "end_time": end_time,
        "user_limit": user_limit,
        "last_check_time": datetime.now(),
        "new_members": []
    }
    raid_collection.update_one({"chat_id": chat_id}, {"$set": raid_data}, upsert=True)
    logger.info(f"Raid settings updated for chat {chat_id}: {raid_data}")
    asyncio.create_task(reset_raid_after_duration(chat_id, duration))

@app.on_message(filters.command('antiraid') & filters.group)
async def antiraid(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    bot_member = await client.get_chat_member(chat_id, bot_user.id)

    if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
        await message.reply("I am not an admin in this group.")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)

    if user_member.status == ChatMemberStatus.ADMINISTRATOR:
        if not user_member.privileges.can_change_info or not user_member.privileges.can_restrict_members:
            await message.reply("You need permission to change group info and restrict users.")
            return
    elif user_member.status != ChatMemberStatus.CREATOR:
        await message.reply("You are not an admin in this group.")
        return

    command_args = message.command[1:]
    if len(command_args) != 2:
        await message.reply("Usage: /antiraid {time} {number of people}.")
        return

    duration_arg = command_args[0]
    user_limit = int(command_args[1])

    duration_seconds = convert_duration_to_seconds(duration_arg)
    if duration_seconds is None:
        await message.reply("Invalid time format. Use m for minutes, h for hours, d for days, or x for permanent.")
        return

    previous_settings = raid_collection.find_one({"chat_id": chat_id})

    if previous_settings:
        await message.reply(
            f"Raid mode is currently disabled in {message.chat.title}.\n"
            f"Would you like to enable raid mode for {duration_arg} with a limit of {user_limit} users?\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Enable raid", callback_data=f"enable_raid:{duration_seconds}:{user_limit}")],
                [InlineKeyboardButton("Cancel", callback_data="cancel_raid")]
            ])
        )
    else:
        await set_raid_settings(chat_id, duration_seconds, user_limit)
        await message.reply(f"Anti-raid enabled: {user_limit} members in {duration_arg} will trigger a ban.")

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    user_member = await client.get_chat_member(chat_id, callback_query.from_user.id)

    if "enable_raid" in data:
        if user_member.status != ChatMemberStatus.ADMINISTRATOR and user_member.status != ChatMemberStatus.CREATOR:
            await callback_query.answer("You do not have permission to enable raid mode.", show_alert=True)
            return

        _, duration, user_limit = data.split(":")
        await set_raid_settings(chat_id, int(duration), int(user_limit))
        await callback_query.answer("Raid mode has been enabled.")
        await callback_query.edit_message_text(
            f"Raid mode has been enabled in {callback_query.message.chat.title}.\n"
            f"For the next {duration} seconds, any new users will be banned when hitting the limit of {user_limit}."
        )
    elif data == "cancel_raid":
        await callback_query.answer("Action cancelled. Raid mode will stay disabled.")
        await callback_query.edit_message_text("Action cancelled. Raid mode will stay disabled.")
    else:
        if user_member.status != ChatMemberStatus.ADMINISTRATOR:
            await callback_query.answer("You are not an admin and cannot perform this action.", show_alert=True)

@app.on_message(filters.command('disableraid') & filters.group)
async def disableraid(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    bot_member = await client.get_chat_member(chat_id, bot_user.id)

    if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
        await message.reply("I am not an admin in this group.")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)

    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await message.reply("You are not an admin in this group.")
        return
    if not user_member.privileges.can_change_info or not user_member.privileges.can_restrict_members:
        await message.reply("You need permission to change group info and restrict users.")
        return

    previous_settings = raid_collection.find_one({"chat_id": chat_id})
    if previous_settings:
        await reset_raid(chat_id)
        await message.reply("Anti-raid has been disabled.")
    else:
        await message.reply("Anti-raid is not currently enabled in this chat.")

@app.on_chat_member_updated()
async def monitor_chat_member(client, chat_member_updated):
    chat_id = chat_member_updated.chat.id
    raid_settings = raid_collection.find_one({"chat_id": chat_id})

    if not raid_settings:
        logger.info(f"No raid settings found for chat {chat_id}.")
        return

    new_member = chat_member_updated.new_chat_member
    if new_member is None:
        logger.info("No new member data available.")
        return

    if new_member.status != ChatMemberStatus.MEMBER:
        logger.info(f"User {new_member.user.id} is not a MEMBER. Current status: {new_member.status}.")
        return

    logger.info(f"Member update detected for user {new_member.user.id} in chat {chat_id}.")

    raid_collection.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"new_members": new_member.user.id}}
    )

    updated_settings = raid_collection.find_one({"chat_id": chat_id})
    logger.info(f"Total new members: {len(updated_settings['new_members'])}")

    if len(updated_settings['new_members']) > updated_settings['user_limit']:
        logger.info(f"User limit exceeded: {len(updated_settings['new_members'])} > {updated_settings['user_limit']}. Banning users.")
        for user_id in updated_settings['new_members']:
            try:
                await client.ban_chat_member(chat_id, user_id)
                logger.info(f"Banned user {user_id} due to anti-raid.")
            except Exception as e:
                logger.error(f"Failed to ban user {user_id}: {e}")

        raid_collection.update_one({"chat_id": chat_id}, {"$set": {"new_members": [], "last_check_time": datetime.now()}})
        logger.info(f"New members list cleared for chat {chat_id}.")

def convert_duration_to_seconds(duration_str):
    time_value = int(duration_str[:-1])
    time_unit = duration_str[-1]

    if time_unit == 'm':
        return time_value * 60
    elif time_unit == 'h':
        return time_value * 3600
    elif time_unit == 'd':
        return time_value * 86400
    elif time_unit == 'x':
        return float('inf')
    else:
        return None

async def reset_raid(chat_id):
    raid_collection.delete_one({"chat_id": chat_id})
    logger.info(f"Raid settings reset for chat {chat_id}")

async def reset_raid_after_duration(chat_id, duration):
    await asyncio.sleep(duration)
    await reset_raid(chat_id)