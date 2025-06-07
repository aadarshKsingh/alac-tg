import os
import asyncio
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

OWNER_ID = int(os.getenv("OWNER_ID", "0"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
MAX_LIMIT = int(os.getenv("MAX_LIMIT", "5"))
WRAPPER_SERVICE = os.getenv("WRAPPER_SERVICE", "wrapper.service")
ALAC_SERVICE = os.getenv("ALAC_SERVICE", "alac.service")
BOT_USERNAME = os.getenv("BOT_USERNAME")

app = Client("alac", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

command_queue = asyncio.Queue(maxsize=MAX_LIMIT)
task_status = {}
active_processes = {}

from handlers.commands import setup_commands
from handlers.queue import process_queue

async def on_start():
    app.loop.create_task(process_queue(app, command_queue, task_status, active_processes, CHANNEL_ID))

if __name__ == "__main__":
    setup_commands(app, command_queue, task_status, active_processes, OWNER_ID, CHANNEL_ID, WRAPPER_SERVICE, ALAC_SERVICE, BOT_USERNAME)
    app.loop.create_task(on_start())
    app.run()
