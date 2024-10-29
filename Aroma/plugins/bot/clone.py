import logging
from pymongo import MongoClient
from pyrogram import Client, filters
from Aroma import app as bot
from config import API_ID, API_HASH, MONGO_DB_URI, OWNER_ID
from Aroma.core.mongo import mongodb

mongo_client = MongoClient(MONGO_DB_URI)
mongo_db = mongo_client["aroma"]
mongo_collection = mongo_db["aromadb"]

@bot.on_message(filters.command("clone") & filters.private)
async def on_clone(client, message):  
    try:
        user_name = message.from_user.first_name
        string_token = message.command[1]

        bots = list(mongo_collection.find())
        string_tokens = None 

        for bot in bots:
            string_tokens = bot['string']

        if string_tokens == string_token:
            await message.reply_text("➢ ᴛʜɪs Assɪsᴛᴀɴᴛ UsᴇʀBᴏᴛ  ɪs ᴀʟʀᴇᴀᴅʏ ᴄʟᴏɴᴇᴅ  use /startub command if client is off ")
            return
        try:
            ai = Client(
                f"{user_name}", API_ID, API_HASH,
                session_string=string_token,
                plugins={"root": "ComboBot.plugins.userbot"},
            )

            await ai.start()
            await ai.join_chat("phoenixXsupport")
            await ai.join_chat("TeamArona")
            await ai.join_chat("arona_update")
            await ai.join_chat("Grabber_memes")
            await ai.join_chat("Mystic_Legion")
            await ai.join_chat("PhoenixGban")
            await ai.join_chat("arona_gban")
            bot_info = await ai.get_me()
            
            details = {
                'is_bot': False,
                'user_id': bot_info.id,  # Use the user ID from the bot info
                'name': bot_info.first_name,
                'string': string_token,
                'username': bot_info.username
            }
            mongo_collection.insert_one(details)
            await message.reply_text(f"<b>sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴏɴᴇᴅ ʏᴏᴜʀ Assɪsᴛᴀɴᴛ UsᴇʀBᴏᴛ : @{bot_info.username}.\n\nʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ sᴇᴛ ʏᴏᴜʀ sʜᴏʀᴛɴᴇʀ ɪɴ ʏᴏᴜʀ ᴄʟᴏɴᴇᴅ ʙᴏᴛ ғᴏʀ ᴍᴏʀᴇ ɪɴғᴏ sᴛᴀʀᴛ Assɪsᴛᴀɴᴛ UsᴇʀBᴏᴛ using  .start for more type .help</b>")
        except BaseException as e:
            logging.exception(f"Error while cloning ub. {e}")
            await message.reply_text(f"⚠️ <b>Assɪsᴛᴀɴᴛ UsᴇʀBᴏᴛ  Error:</b>\n\n<code>{e}</code>\n\n**Kindly forward this message to owner to get assistance.**")
    except Exception as e:
        logging.exception("Error while handling message.")

@bot.on_message(filters.command("deleteclone") & filters.private)
async def delete_cloned_bot(client, message):
    try:
        if message.reply_to_message:
            string_token = message.reply_to_message.text
        elif not message.reply_to_message and len(message.command) != 1:
            string_token = message.text.split(None, 1)[1]
        else:
            await message.reply_text("➢ ꜱᴇɴᴅ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴡɪᴛʜ ʏᴏᴜʀ Assɪsᴛᴀɴᴛ session \nᴇx ː- /deleteclone <ʏᴏᴜʀ session>.")

        user = message.from_user.id
        cloned_bot = mongo_collection.find_one({"string": string_token})
        if cloned_bot:
            mongo_collection.delete_one({"string": string_token})
            await message.reply_text(" ➢ ᴛʜᴇ ᴄʟᴏɴᴇᴅ Assɪsᴛᴀɴᴛ UsᴇʀBᴏᴛ ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴛʜᴇ ʟɪsᴛ ᴀɴᴅ ɪᴛs ᴅᴇᴛᴀɪʟs ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀsᴇ. ")
    except Exception as e:
        logging.exception(f"Error while deleting cloned Assɪsᴛᴀɴᴛ UsᴇʀBᴏᴛ: {e}.")
        await message.reply_text("An error occurred while deleting the cloned Assɪsᴛᴀɴᴛ UsᴇʀBᴏᴛ.")

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