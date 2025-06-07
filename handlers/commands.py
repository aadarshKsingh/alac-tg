import os
import uuid
import asyncio
import logging
import subprocess
import requests
from pyrogram import filters
from pyrogram.types import Message

from utils.file_utils import clear_downloads
from utils.telegraph import format_text_for_telegraph, upload_to_telegraph

def setup_commands(app, command_queue, task_status, active_processes, OWNER_ID, CHANNEL_ID, WRAPPER_SERVICE, ALAC_SERVICE, BOT_USERNAME):
    # Initialize logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    @app.on_message(filters.command("start"))
    async def start(_, message: Message):
        logging.info(f"Received /start from user {message.from_user.id}")
        await message.reply("Helloooooo Bachhooooooooo! Use /help to see available commands.")

    @app.on_message(filters.command("help"))
    async def help(_, message: Message):
        logging.info(f"Received /help from user {message.from_user.id}")
        help_text = (
            "/start - Start the bot\n"
            "/help - Show this help\n"
            "/song <url> - Process the song URL\n"
            "/album <url> - Process the album URL\n"
            "/playlist <url> - Process the playlist URL\n"
            "/info <url> - Show information\n"
            "/atmos <url> - Process the atmos URL\n"
            "/aac <url> - Process the AAC URL\n"
            "/wrapper - Return wrapper systemd service logs\n"
            "/logs - Returns bot's systemd service logs\n"
            "/cancel - Cancel a task with id\n"
            "/cancelall - Cancel all task\n"
            "/status - Show current queue\n"
            "/restart - Restart services [ADMIN ONLY]\n"
            "/searchsong <query> - Search for a song on Apple Music\n"
            "/searchalbum <query> - Search for an album on Apple Music\n"
        )
        await message.reply(help_text)

    @app.on_message(filters.command("song"))
    async def song(_, message: Message):
        if len(message.text.split(" ")) < 2:
            await message.reply("Please provide a URL after the command.")
            return
        url = message.text.split(" ")[1]
        task_id = str(uuid.uuid4())[:8]
        task_status[task_id] = "Queued"
        await command_queue.put((task_id, message, url, "song"))
        logging.info(f"Task {task_id} (song) added to queue by user {message.from_user.id}")
        await message.reply(f"Task {task_id} queued, please wait...")

    @app.on_message(filters.command("album"))
    async def album(_, message: Message):
        if len(message.text.split(" ")) < 2:
            await message.reply("Please provide a URL after the command.")
            return
        url = message.text.split(" ")[1]
        task_id = str(uuid.uuid4())[:8]
        task_status[task_id] = "Queued"
        await command_queue.put((task_id, message, url, "album"))
        logging.info(f"Task {task_id} (album) added to queue by user {message.from_user.id}")
        await message.reply(f"Task {task_id} queued, please wait...")

    @app.on_message(filters.command("playlist"))
    async def playlist(_, message: Message):
        if len(message.text.split(" ")) < 2:
            await message.reply("Please provide a URL after the command.")
            return
        url = message.text.split(" ")[1]
        task_id = str(uuid.uuid4())[:8]
        task_status[task_id] = "Queued"
        await command_queue.put((task_id, message, url, "playlist"))
        logging.info(f"Task {task_id} (playlist) added to queue by user {message.from_user.id}")
        await message.reply(f"Task {task_id} queued, please wait...")

    @app.on_message(filters.command("info"))
    async def info(_, message: Message):
        if len(message.text.split(" ")) < 2:
            await message.reply("Please provide a URL after the command.")
            return
        url = message.text.split(" ")[1]
        command = f"go run main.go --debug {url}"
        await message.reply("Fetching info, Please wait...")
        try:
            output = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
            output = format_text_for_telegraph(output)
            telegraph_url = upload_to_telegraph(output)
            await message.reply(f"Here is the information: {telegraph_url}")
        except Exception as e:
            await message.reply(f"Error occurred: {str(e)}")

    @app.on_message(filters.command("atmos"))
    async def atmos(_, message: Message):
        if len(message.text.split(" ")) < 2:
            await message.reply("Please provide a URL after the command.")
            return
        url = message.text.split(" ")[1]
        task_id = str(uuid.uuid4())[:8]
        task_status[task_id] = "Queued"
        await command_queue.put((task_id, message, url, "atmos"))
        logging.info(f"Task {task_id} (atmos) added to queue by user {message.from_user.id}")
        await message.reply(f"Task {task_id} queued, please wait...")

    @app.on_message(filters.command("aac"))
    async def aac(_, message: Message):
        if len(message.text.split(" ")) < 2:
            await message.reply("Please provide a URL after the command.")
            return
        url = message.text.split(" ")[1]
        task_id = str(uuid.uuid4())[:8]
        task_status[task_id] = "Queued"
        await command_queue.put((task_id, message, url, "aac"))
        logging.info(f"Task {task_id} (aac) added to queue by user {message.from_user.id}")
        await message.reply(f"Task {task_id} queued, please wait...")

    @app.on_message(filters.command("status"))
    async def status(_, message: Message):
        if not task_status:
            await message.reply("No tasks in the queue.")
            return
        status_message = "Current Queue Status:\n\n"
        for task_id, status in task_status.items():
            status_message += f"Task `{task_id}`: {status}\n"
        await message.reply(status_message)

    @app.on_message(filters.command("wrapper"))
    async def wrapper_command(_, message: Message):
        try:
            result = subprocess.run(
                ["journalctl", "-u", WRAPPER_SERVICE],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if result.stderr:
                await message.reply(f"Error: {result.stderr}")
                return
            if "No entries" in result.stdout:
                await message.reply("systemd service not running")
                return
            output_filename = "wrapper_output.txt"
            with open(output_filename, "w") as f:
                f.write(result.stdout)
            await message.reply_document(output_filename, caption="wrapper_output.txt")
            os.remove(output_filename)
        except Exception as e:
            await message.reply(f"An error occurred: {str(e)}")

    @app.on_message(filters.command("logs"))
    async def logs_command(_, message: Message):
        try:
            result = subprocess.run(
                ["journalctl", "-u", ALAC_SERVICE],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if result.stderr:
                await message.reply(f"Error: {result.stderr}")
                return
            if "No entries" in result.stdout:
                await message.reply("systemd service not running")
                return
            output_filename = "alac_output.txt"
            with open(output_filename, "w") as f:
                f.write(result.stdout)
            await message.reply_document(output_filename, caption="alac_output.txt")
            os.remove(output_filename)
        except Exception as e:
            await message.reply(f"An error occurred: {str(e)}")

    @app.on_message(filters.command("cancel"))
    async def cancel(_, message: Message):
        if len(message.text.split(" ")) < 2:
            await message.reply("Please provide a task ID after the command.")
            return
        task_id = message.text.split(" ")[1]
        if task_id not in task_status:
            await message.reply(f"No task found with ID {task_id}.")
            return
        if task_status[task_id] == "Processing" and task_id in active_processes:
            process = active_processes[task_id]
            process.terminate()
            task_status.pop(task_id, None)
            active_processes.pop(task_id, None)
            clear_downloads()
            await message.reply(f"Task {task_id} has been cancelled.")
        else:
            await message.reply(f"Task {task_id} is not in a cancellable state.")

    @app.on_message(filters.command("cancelall"))
    async def cancel_all(_, message: Message):
        for task_id, process in active_processes.items():
            process.terminate()
            task_status.pop(task_id, None)
        active_processes.clear()
        clear_downloads()
        await message.reply("All running tasks have been cancelled.")

    @app.on_message(filters.command("restart"))
    async def restart_command(_, message: Message):
        try:
            subprocess.run(["systemctl", "restart", ALAC_SERVICE], check=True)
            subprocess.run(["systemctl", "restart", WRAPPER_SERVICE], check=True)
            clear_downloads()
            await message.reply("Restarted successfully and downloads cleared!")
        except Exception as e:
            await message.reply(f"An error occurred: {str(e)}")

    @app.on_message(filters.command("searchsong"))
    async def searchsong(_, message: Message):
        if len(message.command) < 2:
            await message.reply("Usage: /searchsong <query>")
            return
        query = " ".join(message.command[1:])
        logging.info(f"Received /searchsong with query: {query}")
        results = search_song_apple_music(query)
        if not results:
            await message.reply("No results found.")
            return
        response_text = f"**Top {len(results)} Apple Music results for:** `{query}`\n\n"
        for idx, track in enumerate(results, start=1):
            song_title = track['trackName']
            artist = track['artistName']
            song_url = track['trackViewUrl']
            download_link = f"[Download Track](tg://resolve?domain={BOT_USERNAME}&text=/song%20{song_url})"
            response_text += f"🎵 **{idx}. {song_title}** - {artist}\n{download_link}\n\n"
        await message.reply(response_text, disable_web_page_preview=True)

    @app.on_message(filters.command("searchalbum"))
    async def searchalbum(_, message: Message):
        if len(message.command) < 2:
            await message.reply("Usage: /searchalbum <query>")
            return
        query = " ".join(message.command[1:])
        logging.info(f"Received /searchalbum with query: {query}")
        results = search_album_apple_music(query)
        if not results:
            await message.reply("No results found.")
            return
        response_text = f"**Top {len(results)} Apple Music results for:** `{query}`\n\n"
        for idx, album in enumerate(results, start=1):
            album_title = album.get('collectionName', 'Unknown Album')
            artist = album.get('artistName', 'Unknown Artist')
            album_url = album.get('collectionViewUrl', '#')
            download_link = f"[Download Album](tg://resolve?domain={BOT_USERNAME}&text=/album%20{album_url})"
            response_text += f"🎵 **{idx}. {album_title}** - {artist}\n{download_link}\n\n"
        await message.reply(response_text, disable_web_page_preview=True)

def search_song_apple_music(query):
    url = f"https://itunes.apple.com/search?term={query}&media=music&entity=song&limit=4"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def search_album_apple_music(query):
    url = f"https://itunes.apple.com/search?term={query}&media=music&entity=album&limit=4"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []
