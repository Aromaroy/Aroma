import logging
from pyrogram import Client, filters
from Aroma import app as bot
from config import API_ID, API_HASH, OWNER_ID, BOT_SESSIONS

async def restart_bots():
    logging.info("Restarting all clients...")
    
    for bot_data in BOT_SESSIONS:
        string_token = bot_data['string']
        try:
            ai = Client(
                f"{string_token}", API_ID, API_HASH,
                session_string=string_token,
                plugins={"root": "ComboBot.plugins.userbot"},
            )
            await ai.start()
            logging.info(f"Successfully started bot: {bot_data['name']} (ID: {bot_data['user_id']})")
            
            chat_list = [
                "phoenixXsupport", "TeamArona", "arona_update", "PacificArc", 
                "Mystic_Legion", "PhoenixGban", "arona_gban"
            ]
            for chat in chat_list:
                try:
                    await ai.join_chat(chat)
                    logging.info(f"Bot {bot_data['name']} joined {chat} successfully.")
                except Exception as e:
                    logging.warning(f"Failed to join {chat} for bot {bot_data['name']}: {e}")
        except Exception as e:
            logging.exception(f"Error while restarting assistant {bot_data['name']} (ID: {bot_data['user_id']}): {e}")

@bot.on_message(filters.command("allclient", ".") & filters.user(OWNER_ID))
async def all_clients(b, m):
    all_client = "List of all clients:\n"
    for bot_data in BOT_SESSIONS:
        all_client += f"{bot_data['user_id']} : {bot_data['name']}\n"
        logging.info(f"Bot {bot_data['name']} ({bot_data['user_id']}) is available.")
    
    await m.reply(all_client)