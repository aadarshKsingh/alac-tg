
# ALAC TG

F Apple Music coz why not

This is a Telegram bot created with an unhealthy amount of sleep deprivation and anti-depressants for the [Apple Music Downloader](https://github.com/zhaarey/apple-music-downloader) project by [zhaarey](https://github.com/zhaarey).

## Requirements

- **Go version 23.1**: Install it using `install_go.sh` (provided in the repository)
- **GPAC (MP4Box)**: Make sure to install GPAC to handle video and audio downloads.

### Tested on:
- Arch Linux
- Ubuntu 22.04

**Note**: Do not use on Ubuntu 20.04.

## Setup

### 1. Clone the Repositories

Clone the original [Apple Music Downloader](https://github.com/aadarshKsingh/apple-music-downloader) and [Wrapper](https://github.com/zhaarey/wrapper) repositories:

```bash
git clone https://github.com/aadarshKsingh/apple-music-downloader.git
git clone https://github.com/zhaarey/wrapper.git
```

### 2. Add the Bot Files

Place the bot files along with the configuration in the same directory as the original Apple Music Downloader repository. The bot files should also be placed in the `wrapper` directory.

### 3. Install Dependencies

Ensure you have Go 23.1 installed. You can use the provided `install_go.sh` script to install it.

Additionally, install **GPAC (MP4Box)** to handle media file extraction:

```bash
# On Ubuntu
sudo apt install gpac

# On Arch Linux
sudo pacman -S gpac
```

### 4. Set Up Wrapper

Make sure the [Wrapper](https://github.com/zhaarey/wrapper) is running. It works well as a systemd service, but has not been tested with Docker.

Create a systemd service file for the wrapper:

```ini
[Unit]
Description=Wrapper Service
After=network.target

[Service]
ExecStart=/home/ubuntu/wrapper/wrapper 10020 username password
WorkingDirectory=/home/ubuntu/wrapper
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
```

### 5. Set Environment Variables

Create a `.env` file with the following variables:

```bash
GROUP_IDS="" # group ids separated by commas
CHANNEL_ID=""
BOT_TOKEN=""
API_ID=""
API_HASH=""
OWNER_ID=""
WRAPPER_SERVICE=""
ALAC_SERVICE=""
MAX_LIMIT=""
PRIVATE=YES
DATABASE_URL="" # any postgres is fine
```

### 6. Edit Config File

Edit the `config.yml` file and set the following:

- Set the save folder to `"downloads"`.
- Keep the downloader formats variables as an empty string.

### 7. Running the Bot

Once all dependencies are installed and configurations are set, you can run the bot. The bot provides the following commands:

## Bot Commands

- `/start`: Start the bot
- `/help`: Show this help message
- `/song <song_url>`: Process the song URL
- `/album <album_url>`: Process the album URL
- `/playlist <playlist_url>`: Process the playlist URL
- `/info`: Show information about the bot
- `/atmos <atmos_url>`: Process the atmos URL
- `/aac <aac_url>`: Process the AAC URL
- `/wrapper` - Return wrapper systemd service logs
- `/logs` - Returns bot's systemd service logs
- `/cancel <task_id>`- Cancel a task with id
- `/cancelall` - Cancel all task
- `/status` - Show current queue
- `/restart` - Restart services [ADMIN ONLY]
- `/auth user_id` - Authorize User [OWNER ONLY]
- `/unauth user_id` - Unauthorize User [OWNER ONLY]

## Troubleshooting

- Ensure that `wrapper` is running correctly. If you run into issues, check the systemd service logs to diagnose.
- Ensure that all required variables are set in `.env` and that `config.yml` is correctly configured.
