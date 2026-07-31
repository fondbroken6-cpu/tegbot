from aiogram import Bot, Dispatcher, types
import asyncio
import os
import json
from aiogram.types import InputMediaPhoto, InputMediaVideo

BOT_TOKEN = os.getenv("BOT_TOKEN")

SOURCE_CHANNEL = -1003900584206

TARGET_CHANNELS = {
    -1003939708995: "https://t.me/+bB1Oo0xmuYs3MThi",
    -1003823200425: "https://t.me/+anxSn5P08g5lMTcy",
    -1002343315413: "https://t.me/+De6qpY6TD0QzYmVi",
    -1002299596606: "https://t.me/+t0pz1nqFXU02MTUy",
    -1002489251514: "https://t.me/+XmbP74p99v4yYjcy",
    -1001548271781: "https://t.me/+SAh8cL6D8-VmMGQ6",
    -1003554835947: "https://t.me/+O4yVzhQSU7VjZThi",
    -1003648623951: "https://t.me/+Vy829puEUGhhMWEy",
    -1003410663397: "https://t.me/+Hv_lIU5iiqw0YzI6",
    -1003133396870: "https://t.me/+m94tkQLy2dxmYWQy",
    -1003439008146: "https://t.me/+FZPc8Xg6K6xhMzRk",
    -1002553048208: "https://t.me/+4PacsxX8JBA5MzNi",
    -1003684323424: "https://t.me/+qmqM6FHcKfMwNjgy",
    -1003328376949: "https://t.me/+OiIzc0WMqX5kNjBi",
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

queue_lock = asyncio.Lock()
albums = {}
message_map = {}

MAP_FILE = "message_map.json"


def load_map():
    global message_map
    try:
        with open(MAP_FILE, "r", encoding="utf-8") as f:
            message_map = json.load(f)
    except:
        message_map = {}


def save_map():
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(message_map, f, ensure_ascii=False, indent=2)


async def send_single(message: types.Message):
    text = message.caption or message.text or ""
    source_id = str(message.message_id)
    message_map[source_id] = []

    for channel_id, link in TARGET_CHANNELS.items():
        final_text = f"{text}\n\n📢 Kanal:\n{link}"

        try:
            sent = None

            if message.text:
                sent = await bot.send_message(channel_id, final_text)

            elif message.photo:
                sent = await bot.send_photo(
                    chat_id=channel_id,
                    photo=message.photo[-1].file_id,
                    caption=final_text
                )

            elif message.video:
                sent = await bot.send_video(
                    chat_id=channel_id,
                    video=message.video.file_id,
                    caption=final_text
                )

            elif message.document:
                sent = await bot.send_document(
                    chat_id=channel_id,
                    document=message.document.file_id,
                    caption=final_text
                )

            if sent:
                message_map[source_id].append({
                    "chat_id": channel_id,
                    "message_id": sent.message_id
                })

            await asyncio.sleep(1)

        except Exception as e:
            print(f"XATO: {channel_id} -> {e}", flush=True)

    save_map()


async def send_album(media_group_id):
    await asyncio.sleep(1.5)

    messages = albums.pop(media_group_id, [])
    messages.sort(key=lambda m: m.message_id)

    if not messages:
        return

    first = messages[0]
    text = first.caption or ""
    source_id = str(first.message_id)
    message_map[source_id] = []

    for channel_id, link in TARGET_CHANNELS.items():
        media = []

        for index, msg in enumerate(messages):
            caption = ""

            if index == 0:
                caption = f"{text}\n\n📢 Kanalga:\n{link}"

            if msg.photo:
                media.append(InputMediaPhoto(
                    media=msg.photo[-1].file_id,
                    caption=caption
                ))

            elif msg.video:
                media.append(InputMediaVideo(
                    media=msg.video.file_id,
                    caption=caption
                ))

        try:
            sent_messages = await bot.send_media_group(
                chat_id=channel_id,
                media=media
            )

            for sent in sent_messages:
                message_map[source_id].append({
                    "chat_id": channel_id,
                    "message_id": sent.message_id
                })

            await asyncio.sleep(1)

        except Exception as e:
            print(f"ALBUM XATO: {channel_id} -> {e}", flush=True)

    save_map()


@dp.channel_post()
async def autopost(message: types.Message):
    if message.chat.id != SOURCE_CHANNEL:
        return

    async with queue_lock:
        if message.media_group_id:
            group_id = message.media_group_id

            if group_id not in albums:
                albums[group_id] = []
                asyncio.create_task(send_album(group_id))

            albums[group_id].append(message)

        else:
            await send_single(message)


@dp.message()
async def delete_command(message: types.Message):
    if not message.text:
        return

    if not message.text.startswith("/del"):
        return

    parts = message.text.split()

    if len(parts) != 2:
        await message.answer("Format: /del POST_ID")
        return

    source_id = parts[1]

    if source_id not in message_map:
        await message.answer("Bu POST_ID topilmadi")
        return

    for item in message_map[source_id]:
        try:
            await bot.delete_message(
                chat_id=item["chat_id"],
                message_id=item["message_id"]
            )
        except Exception as e:
            print(f"DELETE XATO: {e}", flush=True)

    del message_map[source_id]
    save_map()

    await message.answer("O'chirildi ✅")


async def main():
    load_map()
    print("BOT IS STARTED", flush=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
