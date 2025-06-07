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

        logging.info(f"Processing task {task_id} (type: {task_type}) with URL: {url}")

        clear_downloads()
        task_status[task_id] = "Processing"

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
            command = f"go run main.go --song {url}"

        try:
            process = await asyncio.to_thread(
                subprocess.Popen, command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            active_processes[task_id] = process

            stdout, stderr = await asyncio.to_thread(process.communicate)

            if process.returncode != 0:
                logging.error(f"Task {task_id} failed. Error: {stderr}")
                if "Invalid CKC" in stderr:
                    await message.reply(f"Task {task_id}: Invalid CKC error. Song could not be downloaded.")
                else:
                    await message.reply(f"Task {task_id}: Failed to download. Error: {stderr}")
                raise subprocess.CalledProcessError(process.returncode, command, stderr)

            logging.info(f"Task {task_id} completed, sending files...")
            await send_files(app, channel_id)
            await message.reply(f"Task {task_id}: Task done!")
            task_status[task_id] = "Completed"
        except subprocess.CalledProcessError as e:
            if task_id in task_status:
                del task_status[task_id]
            if task_id in active_processes:
                active_processes.pop(task_id)
            logging.error(f"Task {task_id} failed with error: {e.stderr}")
        except Exception as e:
            if task_id in task_status:
                del task_status[task_id]
            if task_id in active_processes:
                active_processes.pop(task_id)
            logging.error(f"Task {task_id} failed with unexpected error: {str(e)}")
            await message.reply(f"Task {task_id}: Unexpected error: {str(e)}")
        finally:
            clear_downloads()
            if task_id in task_status:
                del task_status[task_id]
            if task_id in active_processes:
                active_processes.pop(task_id)
            command_queue.task_done()
            logging.info(f"Task {task_id} removed from queue and downloads cleared.")
