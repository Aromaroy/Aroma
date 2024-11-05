import logging
from pymongo import MongoClient
from pyrogram import Client, filters
from Aroma import app as bot
from config import API_ID, API_HASH, MONGO_DB_URI, OWNER_ID
from Aroma.core.mongo import mongodb

mongo_client = MongoClient(MONGO_DB_URI)
mongo_db = mongo_client["aroma"]
mongo_collection = mongo_db["aromadb"]

async def restart_bots():
    logging.info("Restarting all client........")
    bots = list(mongo_collection.find())
    for bot in bots:
        string_token = bot['string']
        try:
            ai = Client(
                f"{string_token}", API_ID, API_HASH,
                session_string=string_token,
                plugins={"root": "ComboBot.plugins.userbot"},
            )
            await ai.start()
            await ai.join_chat("phoenixXsupport")
            await ai.join_chat("TeamArona")
            await ai.join_chat("arona_update")
            await ai.join_chat("PacificArc")
            await ai.join_chat("Mystic_Legion")
            await ai.join_chat("PhoenixGban")
            await ai.join_chat("arona_gban")
        except Exception as e:
            logging.exception(f"Error while restarting assistant: {e}")

@bot.on_message(filters.command("allclient", ".") & filters.user(OWNER_ID))
async def akll(b, m):
    bots = list(mongo_collection.find())
    all_client = "all client\n"
    for bot in bots:
        all_client += f"{bot['user_id']} : {bot['name']}\n"
        print(bot["user_id"], bot["name"])
    print(all_client)
    await m.reply(all_client)