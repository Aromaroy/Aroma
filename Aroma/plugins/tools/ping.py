from pyrogram.types import Message
from pyrogram import Client, filters
from datetime import datetime

from Aroma import app
from Aroma.core.call import Anony
from Aroma.utils import bot_sys_stats
from Aroma.utils.decorators.language import language
from Aroma.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL


@app.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    response = await message.reply(f"{app.mention} ɪs ᴘɪɴɢɪɴɢ...<a href='{PING_IMG_URL}>.</a>'")
    pytgping = await Mukesh.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    await response.edit_text(
        _["ping_2"].format(resp, app.mention, UP, RAM, CPU, DISK, pytgping),
        reply_markup=supp_markup(_),
    )