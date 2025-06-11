
# ALAC TG Bot

A Telegram bot for the Apple Music Downloader project.

## Overview

This bot provides a Telegram interface for downloading and managing Apple Music content using the [Apple Music Downloader](https://github.com/zhaarey/apple-music-downloader) by [zhaarey](https://github.com/zhaarey).  

---

## Installation

1. **Run the Quick Setup Command**:

```bash
git clone https://github.com/aadarshKsingh/alac-tg && cd alac-tg && bash install_go.sh; echo "Fill .env, run wrapper from https://github.com/zhaarey/wrapper in background, then run: python3 main.py"
```

2. **Install GPAC (MP4Box):**
```bash
   # Ubuntu
   sudo apt install gpac

   # Arch Linux
   sudo pacman -S gpac
```

3. **Download and Run the Wrapper:**
```bash
   git clone https://github.com/zhaarey/wrapper
   cd wrapper
   # Run the wrapper in the background as needed
```

---

## Configuration

###  Environment Variables

Create a `.env` file in the project root and set the following:

```ini
BOT_TOKEN="your_telegram_bot_token"
API_ID="your_telegram_api_id"
API_HASH="your_telegram_api_hash"
CHANNEL_ID="your_channel_id"
OWNER_ID="admin_user_id"
MAX_LIMIT="5"
WRAPPER_SERVICE="wrapper.service"
ALAC_SERVICE="alac.service"
BOT_USERNAME="@your_bot_username"
```

---

## Running the Bot

Start the bot with:

```bash
python3 main.py
```

---

## Bot Commands

| Command                | Description                          |
|------------------------|--------------------------------------|
| `/start`               | Start the bot                        |
| `/help`                | Show help message                    |
| `/song `          | Download a song                      |
| `/album `         | Download an album                    |
| `/playlist `      | Download a playlist                  |
| `/info`                | Show bot information                 |
| `/atmos `         | Download Atmos content               |
| `/aac `           | Download AAC content                 |
| `/cancel `    | Cancel a task                        |
| `/cancelall`           | Cancel all tasks                     |
| `/status`              | Show current queue status            |
| `/searchsong `  | Search for songs                     |
| `/searchalbum ` | Search for albums                    |

