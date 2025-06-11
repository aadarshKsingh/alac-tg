import os
import asyncio
import subprocess
from pyrogram.types import Message
from utils.file_utils import clear_downloads, send_files
import logging

async def process_queue(app, command_queue, task_status, active_processes, channel_id, group_id):
    while True:
        command_data = await command_queue.get()
        task_id, message, url, task_type = command_data

        if task_id not in task_status:
            command_queue.task_done()
            continue

        logging.info(f"Processing task {task_id} ({task_type}): {url}")
        task_status[task_id] = "Processing"

        # Build command
        go_command = ["go", "run", "main.go"]
        if task_type == "song":
            go_command += ["--song", url]
        elif task_type == "album":
            go_command.append(url)
        elif task_type == "playlist":
            go_command.append(url)
        elif task_type == "atmos":
            go_command += ["--atmos", url]
        elif task_type == "aac":
            go_command += ["--aac", url]
        else:
            go_command += ["--song", url]

        try:
            # Start subprocess without logging
            process = await asyncio.to_thread(
                subprocess.Popen,
                go_command,
                cwd="downloader",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                env=os.environ.copy()
            )
            active_processes[task_id] = process

            # Monitor process without streaming output
            while process.poll() is None:
                if task_id not in task_status:
                    process.terminate()
                    break
                await asyncio.sleep(1)

            return_code = process.returncode

            if task_id not in task_status:
                await message.reply(f"Task {task_id}: Canceled")
                continue

            if return_code != 0:
                await message.reply(f"Task {task_id}: Failed with error code {return_code}")
            else:
                await send_files(app, channel_id, group_id)
                await message.reply(f"Task {task_id}: Task done!")

        except FileNotFoundError:
            logging.error("Go command not found. Is Go installed?")
            await message.reply("Error: Go is not installed or not in PATH")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            await message.reply(f"Task {task_id}: Failed - {str(e)}")
        finally:
            task_status.pop(task_id, None)
            active_processes.pop(task_id, None)
            clear_downloads()
            command_queue.task_done()