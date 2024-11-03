import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter, ChatType
from pyrogram.types import ChatPrivileges, ChatPermissions, Message
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

    if bot_member.status != ChatMemberStatus.ADMINISTRATOR or not bot_member.privileges.can_change_info or not bot_member.privileges.can_restrict_members:
        await message.reply("I need admin permissions to operate.")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)

    if user_member.status != ChatMemberStatus.ADMINISTRATOR or not user_member.privileges.can_change_info or not user_member.privileges.can_restrict_members:
        await message.reply("You need admin permissions to operate.")
        return

    command_args = message.command[1:]
    if len(command_args) != 2:
        await message.reply("Usage: /antiraid {time} {number of people}.")
        return

    duration_arg = command_args[0]
    user_limit = int(command_args[1])

    duration_seconds = convert_duration_to_seconds(duration_arg)
    if duration_seconds is None:
        await message.reply("Invalid time format.")
        return

    previous_settings = raid_collection.find_one({"chat_id": chat_id})
    await set_raid_settings(chat_id, duration_seconds, user_limit)

    if previous_settings:
        await message.reply(f"Raid settings changed from {previous_settings['user_limit']} to {user_limit} for {duration_arg}.")
    else:
        await message.reply(f"Anti-raid enabled: {user_limit} members in {duration_arg} will trigger a ban.")

@app.on_message(filters.command('disableraid') & filters.group)
async def disableraid(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    bot_member = await client.get_chat_member(chat_id, bot_user.id)

    if bot_member.status != ChatMemberStatus.ADMINISTRATOR or not bot_member.privileges.can_change_info or not bot_member.privileges.can_restrict_members:
        await message.reply("I need admin permissions to operate.")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)

    if user_member.status != ChatMemberStatus.ADMINISTRATOR or not user_member.privileges.can_change_info or not user_member.privileges.can_restrict_members:
        await message.reply("You need admin permissions to operate.")
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
        return

    new_member = chat_member_updated.new_chat_member
    if new_member and new_member.status == ChatMemberStatus.MEMBER:
        raid_settings['new_members'].append(new_member.user.id)

        now = datetime.now()
        if (now - raid_settings['last_check_time']).seconds >= 60:
            if len(raid_settings['new_members']) > raid_settings['user_limit']:
                for user_id in raid_settings['new_members']:
                    await client.kick_chat_member(chat_id, user_id)
                    logger.info(f"Banned user {user_id} due to anti-raid.")
                raid_collection.update_one({"chat_id": chat_id}, {"$set": {"new_members": [], "last_check_time": now}})
            else:
                raid_collection.update_one({"chat_id": chat_id}, {"$set": {"last_check_time": now}})

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