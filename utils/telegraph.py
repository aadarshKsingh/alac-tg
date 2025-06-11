from telegraph import Telegraph

def format_text_for_telegraph(text):
    lines = text.split("\n")
    formatted_text = ""
    for line in lines:
        if line.startswith("Track") or line.startswith("Album"):
            formatted_text += f"<h3>{line}</h3><br>"
        elif "Available Audio Formats" in line:
            formatted_text += f"<h4>{line}</h4><br>"
        elif "+" in line:
            formatted_text += f"<pre>{line}</pre><br>"
        elif "Debug:" in line:
            formatted_text += f"<pre>{line}</pre><br>"
        else:
            formatted_text += f"{line}<br>"
    return formatted_text

def upload_to_telegraph(text):
    telegraph = Telegraph()
    telegraph.create_account(short_name='my_bot')
    response = telegraph.create_page(
        title='Info',
        html_content=f"<p>{text}</p>",
        author_name='ALAC-TG'
    )
    return f"https://telegra.ph/{response['path']}"
