import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from Aroma import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_message(filters.command('unbanall') & filters.group)
async def unban_all_users(client, message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    logger.info(f"Bot ID: {bot_user.id}, Chat ID: {chat_id}")

    try:
        bot_member = await client.get_chat_member(chat_id, bot_user.id)
        logger.info(f"Bot Member Privileges: {bot_member.privileges}")

        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            await client.send_message(chat_id, "I am not an admin.")
            return
        if not bot_member.privileges.can_restrict_members:
            await client.send_message(chat_id, "I don't have rights to unban users.")
            return
    except Exception as e:
        await client.send_message(chat_id, f"Error retrieving bot status: {e}")
        logger.error(f"Error retrieving bot status: {e}")
        return

    user_member = await client.get_chat_member(chat_id, message.from_user.id)
    logger.info(f"User Member Privileges: {user_member.privileges}")

    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await client.send_message(chat_id, "You are not an admin.")
        return

    if not user_member.privileges.can_restrict_members:
        await client.send_message(chat_id, "You don't have rights to unban users.")
        return

    # Notify about unbanning process
    status_message = await client.send_message(chat_id, "Unbanning all users...")
    
    try:
        banned_users = client.get_chat_members(chat_id, filter=ChatMembersFilter.BANNED)
        total_unbanned = 0

        async for banned_user in banned_users:
            try:
                await client.unban_chat_member(chat_id, banned_user.user.id)
                total_unbanned += 1
                logger.info(f"Unbanned user: {banned_user.user.id}")
            except Exception as e:
                logger.error(f"Failed to unban user {banned_user.user.id}: {str(e)}")

        # Delete the status message
        await client.delete_messages(chat_id, status_message.message_id)

        # Send the final results
        if total_unbanned > 0:
            await client.send_message(chat_id, f"Total unbanned users: {total_unbanned}")
        else:
            await client.send_message(chat_id, "No users were banned.")
    except Exception as e:
        await client.send_message(chat_id, f"Failed to retrieve banned users: {str(e)}")
        logger.error(f"Failed to retrieve banned users: {str(e)}")