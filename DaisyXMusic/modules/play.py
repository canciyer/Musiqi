# Daisyxmusic (Telegram bot project)

# Copyright (C) 2021  Inukaasith
# Copyright (C) 2021  Technical-Hunter
# Copyright (C) 2021  ImJanindu
# Copyright (C) 2021  Anjana-MA
# Copyright (C) 2021  Bemro-Official

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import json
import os
from os import path
from typing import Callable

import aiofiles
import aiohttp
import ffmpeg
import requests
import wget
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, Voice
from Python_ARQ import ARQ
from youtube_search import YoutubeSearch

from DaisyXMusic.config import BOT_NAME as bn
from DaisyXMusic.config import UPDATES_CHANNEL as updateschannel
from DaisyXMusic.config import ARQ_API_KEY, DURATION_LIMIT, que
from DaisyXMusic.function.admins import admins as a
from DaisyXMusic.helpers.admins import get_administrators
from DaisyXMusic.helpers.channelmusic import get_chat_id
from DaisyXMusic.helpers.errors import DurationLimitError
from DaisyXMusic.helpers.decorators import errors, authorized_users_only 
from DaisyXMusic.helpers.filters import command, other_filters
from DaisyXMusic.helpers.gets import get_file_name
from DaisyXMusic.services.callsmusic import callsmusic
from DaisyXMusic.services.callsmusic.callsmusic import client as USER
from DaisyXMusic.services.converter.converter import convert
from DaisyXMusic.services.downloaders import youtube
from DaisyXMusic.services.queues import queues

aiohttpsession = aiohttp.ClientSession()
chat_id = None

# Credits to github.com/thehamkercat for api
arq = ARQ("https://thearq.tech", ARQ_API_KEY, aiohttpsession)

DISABLED_GROUPS = []
useer ="NaN"
def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        else:
            await cb.answer("Siz?? icaz?? verilmir!", show_alert=True)
            return

    return decorator


def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw", 
        format="s16le", 
        acodec="pcm_s16le", 
        ac=2, 
        ar="48k"
    ).overwrite_output().run()
    os.remove(filename)


# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    image1 = Image.open("./background.png")
    image2 = Image.open("./etc/foreground.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/font.ttf", 32)
    draw.text((205, 550), f"Title: {title}", (51, 215, 255), font=font)
    draw.text((205, 590), f"Duration: {duration}", (255, 255, 255), font=font)
    draw.text((205, 630), f"Views: {views}", (255, 255, 255), font=font)
    draw.text(
        (205, 670),
        f"??lav?? etdi: {requested_by}",
        (255, 255, 255),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(filters.command("playlist") & filters.group & ~filters.edited)
async def playlist(client, message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return    
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("Pleylist bo??dur")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "**Haz??rda S??sl??n??n** in {}".format(message.chat.title)
    msg += "\n- " + now_playing
    msg += "\n- by " + by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "**N??vb??**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n- {name}"
            msg += f"\n-  by {usr}\n"
    await message.reply_text(msg)


def updated_stats(chat, queue, vol=100):
    if chat.id in callsmusic.pytgcalls.active_calls:
        # if chat.id in active_chats:
        stats = "**{}** Ayarlar??".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "Musiqi S??si : {}%\n".format(vol)
            stats += "N??vb??ti Mahn?? : `{}`\n".format(len(que))
            stats += "Haz??rda S??sl??n??n : **{}**\n".format(queue[0][0])
            stats += "T??l??b Ed??n : {}".format(queue[0][1].mention)
    else:
        stats = None
    return stats


def r_ply(type_):
    if type_ == "play":
        pass
    else:
        pass
    mar = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("???", "leave"),
                InlineKeyboardButton("???", "puse"),
                InlineKeyboardButton("??????", "resume"),
                InlineKeyboardButton("???", "skip"),
            ],
            [
                InlineKeyboardButton("Pleylist ????", "playlist"),
            ],
            [
                InlineKeyboardButton("??? Ba??la", "cls")
            ],
        ]
    )
    return mar


@Client.on_message(filters.command("current") & filters.group & ~filters.edited)
async def ee(client, message):
    if message.chat.id in DISABLED_GROUPS:
        return
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        await message.reply(stats)
    else:
        await message.reply("Haz??rda musiqi s??sl??ndirilmir")


@Client.on_message(filters.command("player") & filters.group & ~filters.edited)
@authorized_users_only
async def settings(client, message):
    if message.chat.id in DISABLED_GROUPS:
        await message.reply("Musiqi oxuducu deaktivdir")
        return    
    playing = None
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        playing = True
    queue = que.get(chat_id)
    stats = updated_stats(message.chat, queue)
    if stats:
        if playing:
            await message.reply(stats, reply_markup=r_ply("pause"))

        else:
            await message.reply(stats, reply_markup=r_ply("play"))
    else:
        await message.reply("Haz??rda musiqi s??sl??ndirilmir")


@Client.on_message(
    filters.command("musicplayer") & ~filters.edited & ~filters.bot & ~filters.private
)
@authorized_users_only
async def hfmm(_, message):
    global DISABLED_GROUPS
    try:
        user_id = message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text(
            "M??n yaln??z `/musicplayer on` v?? `/musicplayer off` icra edir??m"
        )
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status == "ON" or status == "on" or status == "On":
        lel = await message.reply("`Haz??rlan??r...`")
        if not message.chat.id in DISABLED_GROUPS:
            await lel.edit("Bu ??atda Musiqi Pleyeri Art??q Aktivl????dirilib")
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(
            f"Qrup ??stifad????il??ri ??????n Musiqi Pleyeri U??urla Aktiv Edildi {message.chat.id}"
        )

    elif status == "OFF" or status == "off" or status == "Off":
        lel = await message.reply("`Processing...`")
        
        if message.chat.id in DISABLED_GROUPS:
            await lel.edit("Bu ??atda Musiqi Pleyeri art??q s??nd??r??lm????d??r")
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(
            f"S??hbet ??stifad????il??ri ??????n Musiqi Pleyeri U??urla Deaktiv edildi {message.chat.id}"
        )
    else:
        await message.reply_text(
            "M??n yaln??z `/musicplayer on` v?? `/musicplayer off` icra edir??m`"
        )    
        

@Client.on_callback_query(filters.regex(pattern=r"^(playlist)$"))
async def p_cb(b, cb):
    global que
    que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("Pleylist bo??dur")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**Haz??rda S??sl??n??n** {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n-  by " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**N??vb??ti**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- {name}"
                msg += f"\n- by {usr}\n"
        await cb.message.edit(msg)


@Client.on_callback_query(
    filters.regex(pattern=r"^(play|pause|skip|leave|puse|resume|menu|cls)$")
)
@cb_admin_check
async def m_cb(b, cb):
    global que
    if (
        cb.message.chat.title.startswith("Channel Music: ")
        and chat.title[14:].isnumeric()
    ):
        chet_id = int(chat.title[13:])
    else:
        chet_id = cb.message.chat.id
    qeue = que.get(chet_id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    m_chat = cb.message.chat

    the_data = cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "pause":
        if chet_id in callsmusic.pytgcalls.active_calls:
            await cb.answer("S??s?? qo??ula bilm??di!", show_alert=True)
        else:
            await callsmusic.pytgcalls.pause_stream(chet_id)
            await cb.answer("Musiqiy?? Fasil?? Verildi!")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("play")
            )

    elif type_ == "play":
        if chet_id in callsmusic.pytgcalls.active_calls:
            await cb.answer("S??s?? qo??ula bilm??di!", show_alert=True)
        else:
            await callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("Musiqi Davam Etdirildi!")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("pause")
            )

    elif type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("Pleylist bo??dur")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**Haz??rda S??sl??ndirilir ** in {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- Req by " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**N??vb??ti **"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- {name}"
                msg += f"\n-  by {usr}\n"
        await cb.message.edit(msg)

    elif type_ == "resume":
        if chet_id in callsmusic.pytgcalls.active_calls:
            await cb.answer("S??s a????q deyil v?? ya art??q dayand??r??l??b", show_alert=True)
        else:
            await callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("Musiqi Davam Etdirildi!")
    elif type_ == "puse":
        if chet_id in callsmusic.pytgcalls.active_calls:
            await cb.answer("S??s a????q deyil v?? ya art??q dayand??r??l??b", show_alert=True)
        else:
            await callsmusic.pytgcalls.pause_stream(chet_id)
            await cb.answer("Musiqiy?? Fasil?? Verildi !")
    elif type_ == "cls":
        await cb.answer("Menu Ba??land??")
        await cb.message.delete()

    elif type_ == "menu":
        stats = updated_stats(cb.message.chat, qeue)
        await cb.answer("Menu A????ld??")
        marr = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("???", "leave"),
                    InlineKeyboardButton("???", "puse"),
                    InlineKeyboardButton("??????", "resume"),
                    InlineKeyboardButton("???", "skip"),
                ],
                [
                    InlineKeyboardButton("Pleylist ????", "playlist"),
                ],
                [
                    InlineKeyboardButton("??? Ba??la", "cls")
                ],
            ]
        )
        await cb.message.edit(stats, reply_markup=marr)
    elif type_ == "skip":
        if qeue:
            qeue.pop(0)
        if chet_id in callsmusic.pytgcalls.active_calls:
            await cb.answer("S??s?? qo??ula bilm??di!", show_alert=True)
        else:
            queues.task_done(chet_id)

            if queues.is_empty(chet_id):
                await callsmusic.pytgcalls.leave_group_call(chet_id)
                await cb.message.edit("- Ba??qa Musiqi Pleylist yoxdur..\n- S??sli s??hb??td??n ayr??ld??m!")
            else:
                await callsmusic.pytgcalls.change_stream(
                    chet_id, queues.get(chet_id)["file"]
                )
                await cb.answer("Ke??ildi")
                await cb.message.edit((m_chat, qeue), reply_markup=r_ply(the_data))
                await cb.message.reply_text(
                    f"- Ke??il??n Musiqi\n- S??sl??ndirilir **{qeue[0][0]}**"
                )

    else:
        if chet_id in callsmusic.pytgcalls.active_calls:
            try:
                queues.clear(chet_id)
            except QueueEmpty:
                pass

            await callsmusic.pytgcalls.leave_group_call(chet_id)
            await cb.message.edit("S??hb??td??n U??urla Ayr??ld??!")
        else:
            await cb.answer("S??s?? qo??ula bilm??di!", show_alert=True)


@Client.on_message(command("play") & other_filters)
@authorized_users_only
async def play(_, message: Message):
    global que
    global useer
    if message.chat.id in DISABLED_GROUPS:
        return    
    lel = await message.reply("???? **Haz??rlan??r**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "GroupMuzikBot"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Kanal??n??za assistan?? ??lav?? etm??yi unutmay??n</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>??vv??lc?? m??ni qrupunuza admin olaraq ??lav?? edin</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "S??sli s??hb??td?? musiqi s??sl??ndirm??k ??????n bu qrupa qo??uldum ????"
                    )
                    await lel.edit(
                        "<b>Asistan s??hb??tiniz?? qo??uldu ????</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>?????? Flood X??tas?? ?????? \n{user.first_name} ??ox sayl?? ist??kl??r ??z??rin?? qrupunuza qo??ula bilm??di. Asistan {user.first_name} qrupda qada??an edilm??diyin?? ??min olun. "
                        "\n\nV?? ya ??l il?? qrupunuza Asistan ??lav?? edin v?? yenid??n c??hd edin</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} Bu grupda yoxdu!\nAdmin hey??tind??n 1 n??f??r mahn?? qo??mazdan ??vv??l /play ??mrini bo?? olaraq istifad?? edin\n{user.first_name} Bu halda da grupa qat??lmazsa Onu ??l il?? ??lav?? edin v?? ya d??st??k grupuna bildirin</i>\nD??st??k grupu: @GroupMuzikSup</i>"
        )
        return
    text_links=None
    await lel.edit("???? **Axtar??ram**")
    if message.reply_to_message:
        entities = []
        toxt = message.reply_to_message.text or message.reply_to_message.caption
        if message.reply_to_message.entities:
            entities = message.reply_to_message.entities + entities
        elif message.reply_to_message.caption_entities:
            entities = message.reply_to_message.entities + entities
        urls = [entity for entity in entities if entity.type == 'url']
        text_links = [
            entity for entity in entities if entity.type == 'text_link'
        ]
    else:
        urls=None
    if text_links:
        urls = True
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"??? {DURATION_LIMIT} d??qiq??d??n ??ox olan videolar??n oynat??lmas??na icaz?? verilmir!"
            )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("???? Pleylist", callback_data="playlist"),
                    InlineKeyboardButton("Menu ??? ", callback_data="menu"),
                ],
                [
                    InlineKeyboardButton(text="??? Ba??la", callback_data="cls")
                ],
            ]
        )
        file_name = get_file_name(audio)
        title = file_name
        thumb_name = "https://telegra.ph/file/f6086f8909fbfeb0844f2.png"
        thumbnail = thumb_name
        duration = round(audio.duration / 60)
        views = "??lav?? edildi"
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name))
            else file_name
        )
    elif urls:
        query = toxt
        await lel.edit("???? **????l??nilir**")
        ydl_opts = {"format": "bestaudio/best"}
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"][:40]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"thumb{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            results[0]["url_suffix"]
            views = results[0]["views"]

        except Exception as e:
            await lel.edit(
                "Mahn?? tap??lmad??. Ba??qa bir mahn??n?? s??nay??n v?? ya mahn?? ad??n?? d??zg??n yaz??n."
            )
            print(str(e))
            return
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("???? Pleylist", callback_data="playlist"),
                    InlineKeyboardButton("Menu ??? ", callback_data="menu"),
                ],
                [
                    InlineKeyboardButton(text="???? YouTube", url=f"{url}"),
                    InlineKeyboardButton(text="Y??kl?? ????", url=f"{dlurl}"),
                ],
                [
                    InlineKeyboardButton(text="??? Ba??la", callback_data="cls")
                ],
            ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))        
    else:
        query = ""
        for i in message.command[1:]:
            query += " " + str(i)
        print(query)
        await lel.edit("???? **????l??nilir**")
        ydl_opts = {"format": "bestaudio/best"}
        
        try:
          results = YoutubeSearch(query, max_results=5).to_dict()
        except:
          await lel.edit("M??n?? s??sl??ndirm??k ??????n bir mahn?? ver")
        # Looks like hell. Aren't it?? FUCK OFF
        try:
            toxxt = "**S??sl??ndirm??k ist??diyiniz mahn??n?? se??in ???**\n\n"
            j = 0
            useer=user_name
            emojilist = ["1??????","2??????","3??????","4??????","5??????",]

            while j < 5:
                toxxt += f"{emojilist[j]} **Ba??l??q - [{results[j]['title']}](https://youtube.com{results[j]['url_suffix']})**\n"
                toxxt += f" ??? **M??dd??t** - {results[j]['duration']}\n"
                toxxt += f" ??? **??zl??nm??** - {results[j]['views']}\n"
                j += 1            
            koyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("1??????", callback_data=f'plll 0|{query}|{user_id}'),
                        InlineKeyboardButton("2??????", callback_data=f'plll 1|{query}|{user_id}'),
                        InlineKeyboardButton("3??????", callback_data=f'plll 2|{query}|{user_id}'),
                    ],
                    [
                        InlineKeyboardButton("4??????", callback_data=f'plll 3|{query}|{user_id}'),
                        InlineKeyboardButton("5??????", callback_data=f'plll 4|{query}|{user_id}'),
                    ],
                    [
                        InlineKeyboardButton(text="??? Ba??la", callback_data="cls")
                    ],
                ]
            )       
            await lel.edit(toxxt,reply_markup=koyboard,disable_web_page_preview=True)
            return
        except:
            await lel.edit("Se??m??k ??????n kifay??t q??d??r n??tic?? yoxdur... ")
                        
            # print(results)
            try:
                url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"][:40]
                thumbnail = results[0]["thumbnails"][0]
                thumb_name = f"thumb{title}.jpg"
                thumb = requests.get(thumbnail, allow_redirects=True)
                open(thumb_name, "wb").write(thumb.content)
                duration = results[0]["duration"]
                results[0]["url_suffix"]
                views = results[0]["views"]

            except Exception as e:
                await lel.edit(
                    "Mahn?? tap??lmad??. Ba??qa bir mahn??n?? s??nay??n v?? ya d??zg??n yaz??n."
                )
                print(str(e))
                return
            dlurl=url
            dlurl=dlurl.replace("youtube","youtubepp")
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("???? Pleylist", callback_data="playlist"),
                        InlineKeyboardButton("Menu ??? ", callback_data="menu"),
                    ],
                    [
                        InlineKeyboardButton(text="???? YouTube", url=f"{url}"),
                        InlineKeyboardButton(text="Y??kl?? ????", url=f"{dlurl}"),
                    ],
                    [
                        InlineKeyboardButton(text="??? Ba??la", callback_data="cls")
                    ],
                ]
            )
            requested_by = message.from_user.first_name
            await generate_cover(requested_by, title, views, duration, thumbnail)
            file_path = await convert(youtube.download(url))   
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption=f"#??? T??l??b olunan mahn?? {position} s??raya ??lav?? oldunu!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        return await lel.delete()
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            message.reply("S??sli S??hb??t akt??f deyil v?? ya qo??ula bilmir??m")
            return
        await message.reply_photo(
            photo="final.png",
            reply_markup=keyboard,
            caption="?????? **{}** T??r??find??n ist??nil??n musiqi burada YouTube Music vasit??sil?? oxunur.".format(
                message.from_user.mention()
            ),
        )
        os.remove("final.png")
        return await lel.delete()


@Client.on_message(filters.command("ytplay") & filters.group & ~filters.edited)
@authorized_users_only
async def ytplay(_, message: Message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    lel = await message.reply("???? **Haz??rlan??r**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "helper"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Kanal??n??za asistan?? ??lav?? etm??yi unutmay??n</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>??vv??lc?? m??ni qrupunuza admin olaraq ??lav?? edin</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "S??sli S??hb??td?? musiqi s??sl??ndirm??k ??????n bu qrupa qo??uldum"
                    )
                    await lel.edit(
                        "<b>K??m??k??i asistan s??hb??tiniz?? qo??uldu</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>?????? Flood X??tas?? ?????? \n{user.first_name} ??ox sayl?? ist??kl??r ??z??rin?? qrupunuza qo??ula bilm??di. Asistan {user.first_name} qrupda qada??an edilm??diyin?? ??min olun."
                        "\n\nV?? ya ??l il?? qrupunuza Asistan ??lav?? edin v?? yenid??n c??hd edin</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} Bu grupda yoxdu!\nAdmin hey??tind??n 1 n??f??r mahn?? qo??mazdan ??vv??l /play ??mrini bo?? olaraq istifad?? edin\n{user.first_name} Bu halda da grupa qat??lmazsa Onu ??l il?? ??lav?? edin v?? ya d??st??k grupuna bildirin</i>\nD??st??k grupu: @GroupMuzikSup</i>"
        )
        return
    await lel.edit("???? **Axtar??ram**")
    user_id = message.from_user.id
    user_name = message.from_user.first_name
     

    query = ""
    for i in message.command[1:]:
        query += " " + str(i)
    print(query)
    await lel.edit("???? **????l??nilir**")
    ydl_opts = {"format": "bestaudio/best"}
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        url = f"https://youtube.com{results[0]['url_suffix']}"
        # print(results)
        title = results[0]["title"][:40]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
        duration = results[0]["duration"]
        results[0]["url_suffix"]
        views = results[0]["views"]

    except Exception as e:
        await lel.edit(
            "Mahn?? tap??lmad??. Ba??qa bir mahn??n?? s??nay??n v?? ya d??zg??n yaz??n."
        )
        print(str(e))
        return
    dlurl=url
    dlurl=dlurl.replace("youtube","youtubepp")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("???? Pleylist", callback_data="playlist"),
                InlineKeyboardButton("Menu ??? ", callback_data="menu"),
            ],
            [
                InlineKeyboardButton(text="???? YouTube", url=f"{url}"),
                InlineKeyboardButton(text="Y??kl?? ????", url=f"{dlurl}"),
            ],
            [
                InlineKeyboardButton(text="??? Ba??la", callback_data="cls")
            ],
        ]
    )
    requested_by = message.from_user.first_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file_path = await convert(youtube.download(url))
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption=f"#??? T??l??b olunan mahn?? {position} s??raya ??lav?? oldunu!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        return await lel.delete()
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            message.reply("S??sli S??hb??t aktif deyil v?? ya ona qo??ula bilmir??m")
            return
        await message.reply_photo(
            photo="final.png",
            reply_markup=keyboard,
            caption="?????? **{}** T??r??find??n ist??nil??n musiqi burada YouTube Music vasit??sil?? oxunur.".format(
                message.from_user.mention()
            ),
        )
        os.remove("final.png")
        return await lel.delete()
    

@Client.on_message(filters.command("splay") & filters.group & ~filters.edited)
async def jiosaavn(client: Client, message_: Message):
    global que
    if message_.chat.id in DISABLED_GROUPS:
        return    
    lel = await message_.reply("???? **Haz??rlan??r**")
    administrators = await get_administrators(message_.chat)
    chid = message_.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "GroupMuzikBot"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await client.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message_.from_user.id:
                if message_.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Kanal??n??za assistan?? ??lav?? etm??yi unutmay??n</b>",
                    )
                    pass
                try:
                    invitelink = await client.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>??vv??lc?? m??ni qrupunuza admin olaraq ??lav?? edin</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message_.chat.id, "S??sli S??hb??td?? d?? musiqi s??sl??ndirm??k ??????n bu qrupa qo??uldum"
                    )
                    await lel.edit(
                        "<b>K??m??k??i Asistan s??hb??tiniz?? qo??uldu</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>?????? Flood X??tas?? ?????? \n{user.first_name} ??ox sayl?? ist??kl??r ??z??rin?? qrupunuza qo??ula bilm??di. Asistan {user.first_name} qrupda qada??an edilm??diyin?? ??min olun."
                        "\n\nV?? ya ??l il?? qrupunuza Asistan ??lav?? edin v?? yenid??n c??hd edin</b>"
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            "<i> Bu grupda yoxdu!\nAdmin hey??tind??n 1 n??f??r mahn?? qo??mazdan ??vv??l /play ??mrini bo?? olaraq istifad?? edin\n{user.first_name} Bu halda da grupa qat??lmazsa Onu ??l il?? ??lav?? edin v?? ya d??st??k grupuna bildirin</i>\nD??st??k grupu: @GroupMuzikSup</i>"
        )
        return
    requested_by = message_.from_user.first_name
    chat_id = message_.chat.id
    text = message_.text.split(" ", 1)
    query = text[1]
    res = lel  
    await res.edit(f"???? `{query}` v?? jio saavn ??z??rind?? Axtar??ram")
    
    # ================== Copied from https://github.com/TheHamkerCat/WilliamButcherBot/blob/dev/wbb/modules/music.py line 170 ===============
    
    """
    MIT License
    Copyright (c) 2021 TheHamkerCat
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    """    
    try:
        songs = await arq.saavn(query)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        sname = songs.result[0].song
        slink = songs.result[0].media_url
        ssingers = songs.result[0].singers
        sthumb = songs.result[0].image
        sduration = int(songs.result[0].duration)

# ================================================================================================================================================


    except Exception as e:
        await res.edit(" He?? n?? tap??lmad??.")
        print(str(e))
        return
    try:    
        duuration= round(sduration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"{DURATION_LIMIT} d??qiq??d??n uzun musiqi ??alma??a icaz?? verilmir")
            return
    except:
        pass    
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("???? Pleylist", callback_data="playlist"),
                InlineKeyboardButton("Menu ??? ", callback_data="menu"),
            ],
            [
                InlineKeyboardButton(text="R??smi Kanala Qo??ulun", url=f"https://t.me/{updateschannel}")
            ],
            [
                InlineKeyboardButton(text="??? Ba??la", callback_data="cls")
            ],
        ]
    )
    file_path = await convert(wget.download(slink))
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.delete()
        m = await client.send_photo(
            chat_id=message_.chat.id,
            reply_markup=keyboard,
            photo="final.png",
            caption=f"???{bn}???=#??????  T??l??b olunan mahn?? {position} s??raya ??lav?? oldunu!",
        )

    else:
        await res.edit_text(f"{bn}=?????? S??sl??ndirilir.....")
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            res.edit("Qrup z??ngi aktif deyil, ona qo??ula bilmir??m")
            return
    await res.edit("Ki??ik ????kil yarad??ld??.")
    await generate_cover(requested_by, sname, ssingers, sduration, sthumb)
    await res.delete()
    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"{sname} Via Jiosaavn T??r??find??n S??sl??ndirilir",
    )
    os.remove("final.png")


@Client.on_callback_query(filters.regex(pattern=r"plll"))
async def lol_cb(b, cb):
    global que

    cbd = cb.data.strip()
    chat_id = cb.message.chat.id
    typed_=cbd.split(None, 1)[1]
    #useer_id = cb.message.reply_to_message.from_user.id
    try:
        x,query,useer_id = typed_.split("|")      
    except:
        await cb.message.edit("Mahn?? tap??lmad??")
        return
    useer_id = int(useer_id)
    if cb.from_user.id != useer_id:
        await cb.answer("Mahn??n?? s??sl??ndirm??k etm??k ist??y??n s??n deyils??n!", show_alert=True)
        return
    await cb.message.edit("__G??zl??yin. S??sl??ndirm??y?? Ba??lay??r__????")
    x=int(x)
    try:
        useer_name = cb.message.reply_to_message.from_user.first_name
    except:
        useer_name = cb.message.from_user.first_name
    
    results = YoutubeSearch(query, max_results=5).to_dict()
    resultss=results[x]["url_suffix"]
    title=results[x]["title"][:40]
    thumbnail=results[x]["thumbnails"][0]
    duration=results[x]["duration"]
    views=results[x]["views"]
    url = f"https://youtube.com{resultss}"
    
    try:    
        duuration= round(duration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"{DURATION_LIMIT} d??qiq??d??n uzun musiqi s??sl??ndirm??y?? icaz?? verilmir")
            return
    except:
        pass
    try:
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
    except Exception as e:
        print(e)
        return
    dlurl=url
    dlurl=dlurl.replace("youtube","youtubepp")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("???? Pleylist", callback_data="playlist"),
                InlineKeyboardButton("Menu ??? ", callback_data="menu"),
            ],
            [
                InlineKeyboardButton(text="???? YouTube", url=f"{url}"),
                InlineKeyboardButton(text="Y??kl?? ????", url=f"{dlurl}"),
            ],
            [
                InlineKeyboardButton(text="??? Ba??la", callback_data="cls")
            ],
        ]
    )
    requested_by = useer_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file_path = await convert(youtube.download(url))  
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await cb.message.delete()
        await b.send_photo(chat_id,
            photo="final.png",
            caption=f"#???  T??l??b olunan mahn?? {position} s??raya ??lav?? oldunu!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        
    else:
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)

        await callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        await cb.message.delete()
        await b.send_photo(chat_id,
            photo="final.png",
            reply_markup=keyboard,
            caption=f"?????? **{r_by.mention}** T??r??find??n ist??nil??n musiqi burada YouTube Music vasit??sil?? oxunur. ",
        )
        os.remove("final.png")
