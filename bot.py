import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv
from telegraph import Telegraph


load_dotenv()


GROUP_ID = int(os.getenv("GROUP_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")


app = Client("alac", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def format_text_for_telegraph(text):
    # Split the text into lines (for better control over formatting)
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
    # Create account for the first time
    telegraph.create_account(short_name='my_bot')

    # Upload the text
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
    if message.chat.id != GROUP_ID:
        await message.reply("Unauthorized")
        return
    await message.reply("Helloooooo Bachhooooooooo! Use /help to see available commands.")

# Command to show help
@app.on_message(filters.command("help"))
async def help(_, message: Message):
    if message.chat.id != GROUP_ID:
        await message.reply("Unauthorized")
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
    )
    await message.reply(help_text)

# Function to handle sending to the channel
async def send_files(_, message: Message):
    if message.chat.id != GROUP_ID:
        await message.reply("Unauthorized")
        return
    
    # List all files in the downloads directory
    files = os.listdir("downloads")
    print("Files in downloads directory:", files)  # Debugging line

    if not files:
        await message.reply("No files found to send.")
        return
    
    for file_name in files:
        file_path = os.path.join("downloads", file_name)

        if os.path.isfile(file_path):
            # Check if the file extension is either .jpg or .png
            if file_name.lower().endswith(('.jpg', '.png')):
                print(f"Skipping {file_name} as it is a .jpg or .png file")
                continue  # Skip this iteration

            try:
                # Send the file to the provided channel
                print(f"Attempting to send: {file_name}")  # Debugging line
                print(file_path)
                await app.send_audio(int(CHANNEL_ID), file_path)
                print(f"Sent: {file_name}")
            except Exception as e:
                print(f"Error sending file {file_name}: {str(e)}")
                await message.reply(f"Failed to send file {file_name}: {str(e)}")
    
    # After sending all files, clear the downloads directory
    for file_name in files:
        file_path = os.path.join("downloads", file_name)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)  # Remove the file
                print(f"Deleted: {file_name}")
            except Exception as e:
                print(f"Error deleting file {file_name}: {str(e)}")

    await message.reply("All files sent and downloads directory cleared.")

# Command to process song URL
@app.on_message(filters.command("song"))
async def song(_, message: Message):
    if message.chat.id != GROUP_ID:
        await message.reply("Unauthorized")
        return
    
    if len(message.text.split(" ")) < 2:
        await message.reply("Please provide a URL after the command.")
        return
    
    # Extract the URL argument from the command
    url = message.text.split(" ")[1]

    # Prepare the go command
    command = f"go run main.go --song {url}"
    await message.reply("Downloading, Please wait...")
    # Run the go command synchronously and wait for it to complete
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # If the go command fails, notify the user with an error message
        await message.reply(f"Error running the command: {e.stderr}")
        return

    # After the go command finishes, proceed to send the files
    await send_files(command, message)

# Command to process album URL
@app.on_message(filters.command("album"))
async def album(_, message: Message):
    if message.chat.id != GROUP_ID:
        await message.reply("Unauthorized")
        return
    if len(message.text.split(" ")) < 2:
        await message.reply("Please provide a URL after the command.")
        return
    url = message.text.split(" ")[1]
    command = f"go run main.go {url}"
    await message.reply("Downloading, Please wait...")
    # Run the go command synchronously and wait for it to complete
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # If the go command fails, notify the user with an error message
        await message.reply(f"Error running the command: {e.stderr}")
        return
    await send_files(command, message)

# Command to process playlist URL
@app.on_message(filters.command("playlist"))
async def playlist(_, message: Message):
    if message.chat.id != GROUP_ID:
        await message.reply("Unauthorized")
        return
    if len(message.text.split(" ")) < 2:
        await message.reply("Please provide a URL after the command.")
        return
    url = message.text.split(" ")[1]
    command = f"go run main.go {url}"
    await message.reply("Downloading, Please wait...")
    # Run the go command synchronously and wait for it to complete
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # If the go command fails, notify the user with an error message
        await message.reply(f"Error running the command: {e.stderr}")
        return
    await send_files(command, message)

# Command to process info URL
@app.on_message(filters.command("info"))
async def info(_, message: Message):
    if message.chat.id != GROUP_ID:
        await message.reply("Unauthorized")
        return
    if len(message.text.split(" ")) < 2:
        await message.reply("Please provide a URL after the command.")
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
    if message.chat.id != GROUP_ID:
        await message.reply("Unauthorized")
        return
    if len(message.text.split(" ")) < 2:
        await message.reply("Please provide a URL after the command.")
        return
    url = message.text.split(" ")[1]
    command = f"go run main.go --atmos {url}"
    await message.reply("Downloading, Please wait...")
    # Run the go command synchronously and wait for it to complete
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # If the go command fails, notify the user with an error message
        await message.reply(f"Error running the command: {e.stderr}")
        return
    await send_files(command, message)

# Command to process AAC URL
@app.on_message(filters.command("aac"))
async def aac(_, message: Message):
    if message.chat.id != GROUP_ID:
        await message.reply("Unauthorized")
        return
    if len(message.text.split(" ")) < 2:
        await message.reply("Please provide a URL after the command.")
        return
    url = message.text.split(" ")[1]
    command = f"go run main.go --aac {url}"
    await message.reply("Downloading, Please wait...")
    # Run the go command synchronously and wait for it to complete
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # If the go command fails, notify the user with an error message
        await message.reply(f"Error running the command: {e.stderr}")
        return
    await send_files(command, message)

# Run the bot
app.run()
