import os
import asyncio
import subprocess
import yaml
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

def update_downloader():
    # Clone if not exists
    if not os.path.exists('downloader'):
        subprocess.run(['git', 'clone', 'https://github.com/zhaarey/apple-music-downloader', 'downloader'], check=True)

    # Update config.yaml
    config_path = os.path.join('downloader', 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        config = {}

    updates = {
        'playlist-folder-format': "",
        'artist-folder-format': "",
        'album-folder-format': "",
        'alac-save-folder': "../downloads",
        'atmos-save-folder': "../downloads"
    }
    config.update(updates)

    with open(config_path, 'w') as f:
        yaml.safe_dump(config, f)

    # Update main.go to replace error retry block with 'break'
    main_go_path = os.path.join('downloader', 'main.go')
    if os.path.exists(main_go_path):
        with open(main_go_path, 'r') as f:
            content = f.read()

        old_lines = '''\t\tif counter.Error == 0 {
            break
        }
        fmt.Println("Error detected, press Enter to try again...")
        fmt.Scanln()
        fmt.Println("Start trying again...")
        counter = structs.Counter{}'''
        new_lines = '\t\tbreak'

        if old_lines in content:
            content = content.replace(old_lines, new_lines)
        else:
            import re
            pattern = re.compile(r'\t\tif counter\.Error == 0 \{\n(.*?)counter = structs\.Counter\{\}', re.DOTALL)
            content = pattern.sub('\t\tbreak', content)

        with open(main_go_path, 'w') as f:
            f.write(content)

async def on_start():
    app.loop.create_task(process_queue(app, command_queue, task_status, active_processes, CHANNEL_ID))

if __name__ == "__main__":
    update_downloader()
    setup_commands(app, command_queue, task_status, active_processes, OWNER_ID, CHANNEL_ID, WRAPPER_SERVICE, ALAC_SERVICE, BOT_USERNAME)
    app.loop.create_task(on_start())
    app.run()
