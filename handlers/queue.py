import os
import asyncio
import subprocess
from pyrogram.types import Message
from utils.file_utils import clear_downloads, send_files
import logging

async def process_queue(app, command_queue, task_status, active_processes, channel_id):
    while True:
        command_data = await command_queue.get()
        task_id, message, url, task_type = command_data

        # Immediate check for canceled tasks
        if task_id not in task_status:
            logging.info(f"Task {task_id} was canceled before processing")
            command_queue.task_done()
            continue

        logging.info(f"Processing task {task_id} (type: {task_type}) with URL: {url}")
        clear_downloads()
        task_status[task_id] = "Processing"

        # Build command based on task type
        go_command = []
        if task_type == "song":
            go_command = ["go", "run", "main.go", "--song", url]
        elif task_type == "album":
            go_command = ["go", "run", "main.go", url]
        elif task_type == "playlist":
            go_command = ["go", "run", "main.go", url]
        elif task_type == "atmos":
            go_command = ["go", "run", "main.go", "--atmos", url]
        elif task_type == "aac":
            go_command = ["go", "run", "main.go", "--aac", url]
        else:
            go_command = ["go", "run", "main.go", "--song", url]

        try:
            process = await asyncio.to_thread(
                subprocess.Popen,
                go_command,
                cwd="downloader",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            active_processes[task_id] = process

            # Check for cancellation during execution
            while process.poll() is None:
                if task_id not in task_status:
                    process.terminate()
                    break
                await asyncio.sleep(1)

            stdout, stderr = await asyncio.to_thread(process.communicate)

            # Handle canceled tasks
            if task_id not in task_status:
                logging.info(f"Task {task_id} was canceled during execution")
                await message.reply(f"Task {task_id}: Canceled successfully")
                continue

            # Handle process errors
            if process.returncode != 0:
                error_msg = stderr.strip() if stderr else "Unknown error or canceled"
                logging.error(f"Task {task_id} failed. Error: {error_msg}")
                await message.reply(f"Task {task_id}: Failed to download. Error: {error_msg}")
            else:
                await send_files(app, channel_id)
                await message.reply(f"Task {task_id}: Task done!")
                task_status[task_id] = "Completed"

        except Exception as e:
            logging.error(f"Task {task_id} failed with unexpected error: {str(e)}")
            await message.reply(f"Task {task_id}: Unexpected error: {str(e)}")
        finally:
            if task_id in task_status:
                task_status.pop(task_id)
            if task_id in active_processes:
                active_processes.pop(task_id)
            clear_downloads()
            command_queue.task_done()
