wimport os
import subprocess
import asyncio

def clear_downloads():
    downloads_dir = "downloads"
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)
    else:
        for file_name in os.listdir(downloads_dir):
            file_path = os.path.join(downloads_dir, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

async def send_files(app, channel_id):
    files = os.listdir("downloads")
    for file_name in files:
        file_path = os.path.join("downloads", file_name)
        if os.path.isfile(file_path):
            if file_name.lower().endswith(('.jpg', '.png')):
                continue

            # Find a thumbnail image for the current audio file
            thumbnail_path = None
            for img_file in files:
                img_file_path = os.path.join("downloads", img_file)
                if os.path.isfile(img_file_path) and img_file.lower().endswith(('.jpg', '.png')):
                    thumbnail_path = img_file_path
                    break

            # Use mediainfo to get metadata
            try:
                mediainfo_output = subprocess.run(
                    ["mediainfo", file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                ).stdout

                # Parse mediainfo output for required fields
                complete_name = ""
                performer = ""
                duration = ""
                bitrate_info = ""
                bitrate_info_count = 0

                for line in mediainfo_output.splitlines():
                    if "Title/Sort " in line and not complete_name:
                        complete_name = line.split(":", 1)[1].strip()
                    elif "Performer" in line and not performer:
                        performer = line.split(":", 1)[1].strip()
                    elif "Duration" in line and not duration:
                        duration = line.split(":", 1)[1].strip()
                    elif "Bit rate" in line and not bitrate_info:
                        bitrate_info_count += 1
                        if bitrate_info_count == 2:
                            bitrate_info = line.split(":", 1)[1].strip()

                if not complete_name:
                    complete_name = os.path.splitext(file1_name)[0]

                # Prepare caption
                caption = (
                    f"💽 Title: {complete_name}\n"
                    f"👤 Artist: {performer}\n"
                    f"🕒 Duration: {duration}\n"
                    f"📊 Bitrate: {bitrate_info}"
                )

                # Send audio with all metadata
                await app.send_audio(
                    int(channel_id),
                    file_path,
                    thumb=thumbnail_path if thumbnail_path and os.path.exists(thumbnail_path) else None,
                    title=complete_name,
                    performer=performer,
                    caption=caption
                )

            except Exception as e:
                print(f"Error handling file {file_name}: {str(e)}")
                continue

    # After sending all files, clear the downloads directory
    for file_name in files:
        file_path = os.path.join("downloads", file_name)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file1_name}: {str(e)}")
