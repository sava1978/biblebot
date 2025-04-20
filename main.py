import json
import asyncio
import os
from collections import defaultdict
from telethon import TelegramClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler

api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_name = "bible_userbot"
target_chat = os.environ.get("TARGET_CHAT")
send_hour = int(os.environ.get("TIME_HOUR", 9))

def load_chapters():
    with open("RusSynodal.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    chapters = defaultdict(list)
    for key, verse in data.items():
        parts = key.split()
        if len(parts) < 2: continue
        book = parts[0]
        chapter_verse = parts[1].split(":")
        if len(chapter_verse) < 2: continue
        chapter = chapter_verse[0]
        chapter_key = f"{book} {chapter}"
        chapters[chapter_key].append((key, verse))
    sorted_keys = sorted(chapters.keys(), key=lambda x: list(data).index(next(k for k in data if k.startswith(x))))
    result = []
    for k in sorted_keys:
        chapter_text = '\n'.join(f"{ref}: {text}" for ref, text in chapters[k])
        result.append((k, chapter_text))
    return result

async def send_chapter(client, chapters, index):
    if index >= len(chapters):
        print("Главы закончились.")
        return
    name, text = chapters[index]
    await client.send_message(target_chat, f"📖 {name}\n\n{text[:4096]}")
    if len(text) > 4096:
        await client.send_message(target_chat, text[4096:])

async def main():
    chapters = load_chapters()
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()
    scheduler = AsyncIOScheduler()
    chapter_index = {'i': 0}
    @scheduler.scheduled_job('cron', hour=send_hour)
    def daily_job():
        asyncio.create_task(send_chapter(client, chapters, chapter_index['i']))
        chapter_index['i'] += 1
    scheduler.start()
    print("Бот запущен.")
    await client.run_until_disconnected()

asyncio.run(main())
