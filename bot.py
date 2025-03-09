import os
import subprocess
import asyncio
import uuid
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv
from telegraph import Telegraph
from pyrogram.errors import FloodWait
import psycopg2
import requests

load_dotenv()

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
downloads_dir = "downloads"
OWNER_ID = int(os.getenv("OWNER_ID"))
WRAPPER_SERVICE = os.getenv("WRAPPER_SERVICE")
ALAC_SERVICE = os.getenv("ALAC_SERVICE")
MAX_LIMIT = int(os.getenv("MAX_LIMIT"))
DATABASE_URL = os.getenv('DATABASE_URL')
PRIVATE = os.getenv('PRIVATE', 'NO').upper() == 'YES'
GROUP_IDS = list(map(int, os.getenv('GROUP_IDS', '').split(','))) if os.getenv('GROUP_IDS') else []
BOT_USERNAME = os.getenv("BOT_USERNAME")
app = Client("alac", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS authorized_users (
    user_id BIGINT PRIMARY KEY
);
""")
conn.commit()

# Create a queue for downloads
command_queue = asyncio.Queue(maxsize=MAX_LIMIT)

# Dictionary to store task statuses
task_status = {}

# Dictionary to store active subprocesses for cancellation
active_processes = {}

async def process_queue():
    while True:
        # Wait for the next command in the queue
        command_data = await command_queue.get()
        task_id, message, url, task_type = command_data
        
        task_status[task_id] = "Processing"
        
        # Prepare the go command, modify it to download to the "downloads" folder
        if task_type == "song":
            command = f"go run main.go --song {url}"
        elif task_type == "album":
            command = f"go run main.go {url}"
        elif task_type == "playlist":
            command = f"go run main.go {url}"
        elif task_type == "atmos":
            command = f"go run main.go --atmos {url}"
        elif task_type == "aac":
            command = f"go run main.go --aac {url}"
        else:
            command = f"go run main.go --song {url}"  # Default command, in case the type is not found

        try:
            # Run the command in a separate thread to avoid blocking the event loop
            process = await asyncio.to_thread(subprocess.Popen, command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            active_processes[task_id] = process

            # Wait for the process to complete asynchronously
            stdout, stderr = await asyncio.to_thread(process.communicate)

            if process.returncode != 0:
                task_status[task_id] = "Failed"
                raise subprocess.CalledProcessError(process.returncode, command, stderr)

            await send_files(command,message)
            task_status[task_id] = "Completed"
            del task_status[task_id]
            # After the go command finishes, proceed to send the files or notify user
            bot_reply = await message.reply(f"Task by [{message.from_user.first_name}](tg://user?id={message.from_user.id}): Download completed!")
            await asyncio.sleep(10)
            await message.delete()
            await bot_reply.delete()

        except subprocess.CalledProcessError as e:
            # If the go command fails, notify the user with an error message
            task_status[task_id] = f"Failed: {e.stderr}"
            bot_reply = await message.reply(f"Task {task_id}: Error running the command: {e.stderr}")
            await asyncio.sleep(60)
            await message.delete()
            await bot_reply.delete()

        except Exception as e:
            # Handle unexpected errors
            task_status[task_id] = f"Failed: {str(e)}"
            bot_reply = await message.reply(f"Task {task_id}: Unexpected error: {str(e)}")
            await asyncio.sleep(60)
            await message.delete()
            await bot_reply.delete()

        finally:
            active_processes.pop(task_id, None)
            command_queue.task_done()
            if not command_queue.empty():
                await process_queue()

# Check if the directory exists
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)
    print(f"Directory '{downloads_dir}' created.")
else:
    print(f"Directory '{downloads_dir}' already exists.")
    

def is_authorized(user_id):
    cursor.execute("SELECT 1 FROM authorized_users WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None


def format_text_for_telegraph(text):
    lines = text.split("\n")
    
    formatted_text = ""
    
    # Loop through each line and apply HTML formatting
    for line in lines:
        if line.startswith("Track") or line.startswith("Album"):  # Heading
            formatted_text += f"<h3>{line}</h3><br>"
        elif "Available Audio Formats" in line:  # Section header
            formatted_text += f"<h4>{line}</h4><br>"
        elif "+" in line:  # Table data
            formatted_text += f"<pre>{line}</pre><br>"
        elif "Debug:" in line:  # Debug information, keep it formatted
            formatted_text += f"<pre>{line}</pre><br>"
        else:  # Regular text, add a line break
            formatted_text += f"{line}<br>"
    
    return formatted_text

def upload_to_telegraph(text):
    telegraph = Telegraph()
    telegraph.create_account(short_name='my_bot')

    response = telegraph.create_page(
        title='Info',
        html_content=f"<p>{text}</p>",
        author_name='Alac Daddy'
    )
    
    # Return the URL of the created page
    return f"https://telegra.ph/{response['path']}"

# Helper function to run the Go command
def run_go_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(result.stderr)
        return result.stdout
    except Exception as e:
        return f"Invalid URL or error: {str(e)}"

# Command to start the bot
@app.on_message(filters.command("start"))
async def start(_, message: Message):
    if not await check_access(message):
        return
    
    bot_reply = await message.reply("Helloooooo Bachhooooooooo! Use /help to see available commands.")
    await asyncio.sleep(10)
    await message.delete()
    await bot_reply.delete()

# Command to show help
@app.on_message(filters.command("help"))
async def help(_, message: Message):
    if not await check_access(message):
        return

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
        "/auth <user_id> - Authorize user [ADMIN ONLY]\n"
        "/unauth <user_id> - Unauthorize user [ADMIN ONLY]\n"
        "/searchsong <query> - Search for a song on Apple Music\n"
        "/searchalbum <query> - Search for an album on Apple Music\n"
    )
    bot_reply = await message.reply(help_text)
    await asyncio.sleep(60)
    await message.delete()
    await bot_reply.delete()
    

# Function to handle sending to the channel
async def send_files(_, message: Message):
    if message.chat.id not in GROUP_IDS and not is_authorized(message.from_user.id):
        await message.reply("Unauthorized")
        return
    
    # List all files in the downloads directory
    files = os.listdir("downloads")
    print("Files in downloads directory:", files)  # Debugging line

    if not files:
        bot_reply = await message.reply("No files found to send.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return
    
    for file_name in files:
        file_path = os.path.join("downloads", file_name)

        if os.path.isfile(file_path):
            if file_name.lower().endswith(('.jpg', '.png')):
                print(f"Skipping {file_name} as it is a .jpg or .png file")
                continue
            
            # Find a thumbnail image for the current audio file
            thumbnail_path = None
            for img_file in files:
                img_file_path = os.path.join("downloads", img_file)
                if os.path.isfile(img_file_path) and img_file.lower().endswith(('.jpg', '.png')):
                    thumbnail_path = img_file_path
                    break  # Take the first image file we find and use it

            if thumbnail_path:
                print(f"Using {thumbnail_path} as thumbnail for {file_name}")
            else:
                print(f"No thumbnail found for {file_name}")
                

            try:
                # Run mediainfo on the file to get metadata
                mediainfo_output = subprocess.run(
                    ["mediainfo", file_path], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                    )

                    # Parse the mediainfo output to get required details
                mediainfo_data = mediainfo_output.stdout

                title_name = ""
                performer = ""
                duration = ""
                bitrate_info = ""
                bitrate_info_count = 0
                for line in mediainfo_data.splitlines():
                    # Only pick the first occurrence of each field
                    if "Title/Sort " in line and not title_name:
                        complete_name = line.split(":", 1)[1].strip()
                    elif "Performer" in line and not performer:
                        performer = line.split(":", 1)[1].strip()
                    elif "Duration" in line and not duration:
                        duration = line.split(":", 1)[1].strip()
                    elif "Bit rate" in line and not bitrate_info:
                        bitrate_info_count += 1
                        if bitrate_info_count == 2:
                           bitrate_info = line.split(":", 1)[1].strip()

                # Create the caption with the extracted information
                caption = f"💽 Title: {complete_name}\n" \
                          f"👤 Artist: {performer}\n" \
                          f"🕒 Duration: {duration}\n" \
                          f"📊 Bitrate: {bitrate_info}" \

                # Send the file with the caption
                print(f"Attempting to send: {file_name}") 
                await app.send_audio(int(CHANNEL_ID), file_path,thumb=thumbnail_path if os.path.exists(thumbnail_path) else None,title=complete_name,performer=performer, caption=caption)
                print(f"Sent: {file_name}")

            except Exception as e:
                    print(f"Error handling file {file_name}: {str(e)}")
                    await message.reply(f"Failed to process and send {file_name}: {str(e)}")
            except FloodWait as e:
                    print(f"FloodWait triggered. Sleeping for {e.x} seconds")
                    await sleep(e.x)
                    try:
                        await app.send_document(int(CHANNEL_ID), file_path)
                    except Exception as e:
                        print(f"Error sending file {file_name}: {str(e)}")
                        bot_reply = await message.reply(f"Failed to send file {file_name}: {str(e)}")
                        await asyncio.sleep(60)
                        await message.delete()
                        await bot_reply.delete()

    # After sending all files, clear the downloads directory
    for file_name in files:
        file_path = os.path.join("downloads", file_name)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted: {file_name}")
            except Exception as e:
                print(f"Error deleting file {file_name}: {str(e)}")

    bot_reply = await message.reply("All files sent and downloads directory cleared.")
    await asyncio.sleep(10)
    await message.delete()
    await bot_reply.delete()
    
async def check_access(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id < 0:  # Group chat
        return chat_id in GROUP_IDS  # Available for all members in the specified groups
    elif PRIVATE:  # Private chat
        if GROUP_IDS:  # If both group mode and private mode are enabled
            return is_authorized(user_id)  # Private use for authorized users only
        if not GROUP_IDS and user_id != OWNER_ID and not is_authorized(user_id):
            await message.reply_text("Only the bot owner and authorized users can use commands in private mode.")
            return False
        return user_id == OWNER_ID or is_authorized(user_id)
    return False

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

@app.on_message(filters.command("searchsong"))
async def search(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id < 0:  
        if chat_id not in GROUP_IDS:
            return
    elif PRIVATE:
        if not is_authorized(user_id):
            return

    if len(message.command) < 2:
        await message.reply_text("Usage: /searchsong <query>")
        return

    query = " ".join(message.command[1:])
    results = search_song_apple_music(query)

    if not results:
        await message.reply_text("No results found.")
        return

    response_text = f"**Top {len(results)} Apple Music results for:** `{query}`\n\n"

    for idx, track in enumerate(results, start=1):
        song_title = track['trackName']
        artist = track['artistName']
        song_url = track['trackViewUrl']

        download_link = f"[Download Track](tg://resolve?domain={BOT_USERNAME}&text=/song%20{song_url})"

        response_text += f"🎵 **{idx}. {song_title}** - {artist}\n{download_link}\n\n"

    await message.reply_text(response_text, disable_web_page_preview=True)
    
@app.on_message(filters.command("searchalbum"))
async def search(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id < 0:  
        if chat_id not in GROUP_IDS:
            return
    elif PRIVATE:
        if not is_authorized(user_id):
            return

    if len(message.command) < 2:
        await message.reply_text("Usage: /searchalbum <query>")
        return

    query = " ".join(message.command[1:])
    results = search_album_apple_music(query)

    if not results:
        await message.reply_text("No results found.")
        return

    response_text = f"**Top {len(results)} Apple Music results for:** `{query}`\n\n"

    for idx, track in enumerate(results, start=1):
        album_title = track.get('collectionName', 'Unknown Album')
        artist = track.get('artistName', 'Unknown Artist')
        album_url = track.get('collectionViewUrl', '#')

        download_link = f"[Download Album](tg://resolve?domain={BOT_USERNAME}&text=/album%20{album_url})"

        response_text += f"🎵 **{idx}. {album_title}** - {artist}\n{download_link}\n\n"

    await message.reply_text(response_text, disable_web_page_preview=True)

    
# Command to process song URL
@app.on_message(filters.command("song"))
async def song(_, message: Message):
    if not await check_access(message):
        return
    
    if len(message.text.split(" ")) < 2:
        bot_reply = await message.reply("Please provide a URL after the command.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return
    
    bot_reply =await message.reply(f"Task queued for [{message.from_user.first_name}](tg://user?id={message.from_user.id}), Please wait...")
    await asyncio.sleep(15)
    await message.delete()
    await bot_reply.delete()
    # Extract the URL argument from the command
    url = message.text.split(" ")[1]

    # Generate a task id without blasting anything
    task_id = str(uuid.uuid4())[:8]
    
    task_status[task_id] = "Queued"
    
    await command_queue.put((task_id, message, url, "song"))


# Command to process album URL
@app.on_message(filters.command("album"))
async def album(_, message: Message):
    if not await check_access(message):
        return
    if len(message.text.split(" ")) < 2:
        await message.reply("Please provide a URL after the command.")
        return
    
    bot_reply = await message.reply(f"Task queued for [{message.from_user.first_name}](tg://user?id={message.from_user.id}), Please wait...")
    await asyncio.sleep(10)
    await message.delete()
    await bot_reply.delete()
    url = message.text.split(" ")[1]
    # Generate a task id without blasting anything
    task_id = str(uuid.uuid4())[:8]
    
    task_status[task_id] = "Queued"
    
    await command_queue.put((task_id, message, url, "album"))

# Command to process playlist URL
@app.on_message(filters.command("playlist"))
async def playlist(_, message: Message):
    if not await check_access(message):
        return
    
    if len(message.text.split(" ")) < 2:
        bot_reply = await message.reply("Please provide a URL after the command.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return
        
    bot_reply = await message.reply(f"Task queued for [{message.from_user.first_name}](tg://user?id={message.from_user.id}), Please wait...")
    await asyncio.sleep(60)
    await message.delete()
    await bot_reply.delete()
    url = message.text.split(" ")[1]
    
    # Generate a task id without blasting anything
    task_id = str(uuid.uuid4())[:8]
    
    task_status[task_id] = "Queued"
    
    await command_queue.put((task_id, message, url, "playlist"))

# Command to process info URL
@app.on_message(filters.command("info"))
async def info(_, message: Message):
    if not await check_access(message):
        return
    
    if len(message.text.split(" ")) < 2:
        bot_reply = await message.reply("Please provide a URL after the command.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return
    url = message.text.split(" ")[1]
    
    # Replace with your actual Go command execution logic
    command = f"go run main.go --debug {url}"
    await message.reply("Fetching info, Please wait...")
    try:
        # Get the long output (this is a placeholder for actual output logic)
        output = run_go_command(command)
        output = format_text_for_telegraph(output)
        # Upload the long text to Telegraph and get the URL
        telegraph_url = upload_to_telegraph(output)
        
        # Send the link to the user
        await message.reply(f"Here is the information: {telegraph_url}")
    except Exception as e:
        await message.reply(f"Error occurred: {str(e)}")

# Command to process atmos URL
@app.on_message(filters.command("atmos"))
async def atmos(_, message: Message):
    if not await check_access(message):
        return
    
    if len(message.text.split(" ")) < 2:
        bot_reply = await message.reply("Please provide a URL after the command.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return
    
    bot_reply = await message.reply(f"Task queued for [{message.from_user.first_name}](tg://user?id={message.from_user.id}), Please wait...")
    await asyncio.sleep(15)
    await message.delete()
    await bot_reply.delete()
    url = message.text.split(" ")[1]
    # Generate a task id without blasting anything
    task_id = str(uuid.uuid4())[:8]
    
    task_status[task_id] = "Queued"
    
    await command_queue.put((task_id, message, url, "atmos"))

# Command to process AAC URL
@app.on_message(filters.command("aac"))
async def aac(_, message: Message):
    if not await check_access(message):
        return
    
    if len(message.text.split(" ")) < 2:
        bot_reply = await message.reply("Please provide a URL after the command.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return
    
    bot_reply = await message.reply(f"Task queued for [{message.from_user.first_name}](tg://user?id={message.from_user.id}), Please wait...")
    await asyncio.sleep(60)
    await message.delete()
    await bot_reply.delete()
    
    url = message.text.split(" ")[1]
    # Generate a task id without blasting anything
    task_id = str(uuid.uuid4())[:8]
    
    task_status[task_id] = "Queued"
    
    await command_queue.put((task_id, message, url, "aac"))

# Function to display the current task queue and status
@app.on_message(filters.command("status"))
async def status(_, message: Message):
    # Build a string with the status of all tasks in the queue
    if not task_status:
        bot_reply = await message.reply("No tasks in the queue.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return

    status_message = "Current Queue Status:\n\n"
    for task_id, status in task_status.items():
        status_message += f"Task `{task_id}`: {status}\n"
    
    bot_reply = await message.reply(status_message)
    await asyncio.sleep(15)
    await message.delete()
    await bot_reply.delete()
    
@app.on_message(filters.command("wrapper"))
async def wrapper_command(client, message):
    try:
        # Run the journalctl command and capture the output
        result = subprocess.run(
            ["journalctl", "-u", "wrapper.service"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )

        # Check if there was an error running the command
        if result.stderr:
            await message.reply(f"Error: {result.stderr}")
            return
        
        # Check if "No entries" is in the output
        if "No entries" in result.stdout:
            await message.reply("systemd service not running")
            return
            
        # Create a file to store the journalctl output
        output_filename = "wrapper_output.txt"
        with open(output_filename, "w") as f:
            f.write(result.stdout)

        # Send the file as a message
        bot_reply = await message.reply_document(output_filename, caption="wrapper_output.txt")
        await asyncio.sleep(30)
        await message.delete()
        await bot_reply.delete()
        # Clean up the file after sending
        os.remove(output_filename)

    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")

# Command to cancel a task
@app.on_message(filters.command("cancel"))
async def cancel(_, message: Message):
    if not await check_access(message):
        return
    
    if len(message.text.split(" ")) < 2:
        await message.reply("Please provide a task ID after the command.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return

    task_id = message.text.split(" ")[1]
    
    # Check if the task exists
    if task_id not in task_status:
        bot_reply = await message.reply(f"No task found with ID {task_id}.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return

    # If the task is processing, attempt to terminate the process
    if task_status[task_id] == "Processing" and task_id in active_processes:
        process = active_processes[task_id]
        process.terminate()  # Terminate the process
        task_status[task_id] = "Cancelled"
        active_processes.pop(task_id, None)  # Remove from active processes
        del task_status[task_id]
        
        files = os.listdir("downloads")
        # Clear directory after cancel
        for file_name in files:
            file_path = os.path.join("downloads", file_name)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)  # Remove the file
                    print(f"Deleted: {file_name}")
                except Exception as e:
                    print(f"Error deleting file {file_name}: {str(e)}")
        bot_reply = await message.reply(f"Task {task_id} has been cancelled.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        if not command_queue.empty():
            await process_queue()
            
    else:
        bot_reply = await message.reply(f"Task {task_id} is not in a cancellable state.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        
@app.on_message(filters.command("cancelall"))
async def cancel_all(_, message: Message):
    if not await check_access(message):
        return
    
    if command_queue.qsize() == 0:
        bot_reply = await message.reply("No tasks are currently being processed.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return

    # Iterate over the active processes and terminate them
    for task_id, process in active_processes.items():
        process.terminate()  # Terminate the process
        del task_status[task_id]
    
    # Clear active processes dictionary
    active_processes.clear()
    
    bot_reply = await message.reply("All running tasks have been cancelled.")
    await asyncio.sleep(10)
    await message.delete()
    await bot_reply.delete()
    
@app.on_message(filters.command("restart"))
async def restart_command(client, message):
    # Check if the user is the admin
    if message.from_user.id != OWNER_ID:
        bot_reply = await message.reply("You do not have permission to use this command.")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        return
    
    try:
        # Restart services
        subprocess.run(["systemctl", "restart", ALAC_SERVICE], check=True)
        subprocess.run(["systemctl", "restart", WRAPPER_SERVICE], check=True)

        for filename in os.listdir(downloads_dir):
            file_path = os.path.join(downloads_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Send a success message
        bot_reply = await message.reply("Restarted successfully and downloads cleared!")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()

    except Exception as e:
        bot_reply = await message.reply(f"An error occurred during the restart process: {str(e)}")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()
        
@app.on_message(filters.command("logs"))
async def logs_command(client, message):
    try:
        # Run the journalctl command for alac.service and capture the output
        result = subprocess.run(
            ["journalctl", "-u", ALAC_SERVICE], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )

        # Check if there was an error running the command
        if result.stderr:
            bot_reply = await message.reply(f"Error: {result.stderr}")
            await asyncio.sleep(15)
            await message.delete()
            await bot_reply.delete()
            return

        # Check if "No entries" is in the output
        if "No entries" in result.stdout:
            bot_reply = await message.reply("systemd service not running")
            await asyncio.sleep(10)
            await message.delete()
            await bot_reply.delete()
            return
            
        # Create a file to store the journalctl output
        output_filename = "alac_output.txt"
        with open(output_filename, "w") as f:
            f.write(result.stdout)

        # Send the file as a message
        bot_reply = await message.reply_document(output_filename, caption="alac_output.txt")
        await asyncio.sleep(30)
        await message.delete()
        await bot_reply.delete()

        # Clean up the file after sending
        os.remove(output_filename)

    except Exception as e:
        bot_reply = await message.reply(f"An error occurred: {str(e)}")
        await asyncio.sleep(10)
        await message.delete()
        await bot_reply.delete()

@app.on_message(filters.command("auth") & filters.user(OWNER_ID))
def auth(client: Client, message: Message):
    if len(message.command) != 2:
        message.reply_text("Give User ID to authorize")
        return
    user_id = int(message.command[1])
    cursor.execute("INSERT INTO authorized_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
    conn.commit()
    message.reply_text(f"User {user_id} authorized.")

@app.on_message(filters.command("unauth") & filters.user(OWNER_ID))
def unauth(client: Client, message: Message):
    if len(message.command) != 2:
        message.reply_text("Give User ID to unauthorize")
        return
    user_id = int(message.command[1])
    cursor.execute("DELETE FROM authorized_users WHERE user_id = %s", (user_id,))
    conn.commit()
    message.reply_text(f"User {user_id} unauthorized.")

async def on_start():
    app.loop.create_task(process_queue())

# Run the bot
if __name__ == "__main__":
    app.loop.create_task(on_start())
    app.run()
