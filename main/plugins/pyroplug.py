import asyncio, time, os
from pyrogram.enums import ParseMode, MessageMediaType
from .. import Bot, bot
from main.plugins.progress import progress_for_pyrogram
from main.plugins.helpers import screenshot, video_metadata
from pyrogram import Client, filters
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid, FloodWait
from telethon import events
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.INFO)
logging.getLogger("telethon").setLevel(logging.INFO)

# Global dict to store joined group IDs (optional, for reliability)
joined_groups = {}

def thumbnail(sender):
    return f'{sender}.jpg' if os.path.exists(f'{sender}.jpg') else None

# ================== FIXED CHECK FUNCTION ==================
async def check(userbot, client, link):
    logging.info(f"Checking link: {link}")
    msg_id = 0
    try:
        msg_id = int(link.split("/")[-1])
    except ValueError:
        if '?single' in link:
            link = link.split("?single")[0]
            msg_id = int(link.split("/")[-1])
        else:
            return False, "Invalid Link!"

    # PRIVATE CHANNEL: t.me/c/123456/789
    if 't.me/c/' in link:
        try:
            chat_id = int('-100' + link.split("/")[-2])
            await userbot.get_messages(chat_id, msg_id)
            return True, None
        except Exception as e:
            logging.info(f"Channel check failed: {e}")
            return False, "Bot is not in that channel. Send invite link first."

    # PRIVATE GROUP INVITE: t.me/+abc123 or t.me/joinchat
    elif 't.me/+' in link or 't.me/joinchat' in link:
        try:
            chat = await userbot.join_chat(link)
            joined_groups[chat.username or chat.id] = chat.id
            return True, None
        except Exception as e:
            logging.info(f"Join failed: {e}")
            return False, "Failed to join group. Check invite link."

    # PUBLIC/PRIVATE GROUP: t.me/groupname/123
    else:
        try:
            chat_username = link.split("/")[-2]
            await client.get_messages(chat_username, msg_id)
            return True, None
        except Exception as e:
            logging.info(f"Group check failed: {e}")
            return False, "Bot not in group or invalid link!"

# ================== FIXED GET_MSG FUNCTION ==================
async def get_msg(userbot, client, sender, edit_id, msg_link, i, file_n):
    edit = ""
    chat = ""
    msg_id = int(i)
    if msg_id == -1:
        await client.edit_message_text(sender, edit_id, "Invalid Link!")
        return None

    # Determine chat ID
    if 't.me/c/' in msg_link or 't.me/b/' in msg_link:
        if "t.me/b" not in msg_link:
            chat = int('-100' + msg_link.split("/")[-2])
        else:
            chat = int(msg_link.split("/")[-2])
    else:
        # Group: t.me/groupname/123
        chat_username = msg_link.split("/")[-2]
        try:
            # pehle save id check kar
            if chat_username in joined_groups:
                chat = joined_groups[chat_username]
            else:
                entity = await userbot.get_entity(chat_username)
                chat = entity.id
                joined_groups[chat_username]
        except Exception as e:
            await client.edit_message_text(sender, edit_id, "Group not found or bot not joined!")
            logging.info(f"Entity error: {e}")
            return None

    file = ""
    try:
        msg = await userbot.get_messages(chat_id=chat, message_ids=msg_id)
        if not msg:
            await client.edit_message_text(sender, edit_id, "Message not found!")
            return None

        # Service or empty
        if msg.service or msg.empty:
            await client.delete_messages(sender, edit_id)
            return None

        # Web page preview
        if msg.media and msg.media == MessageMediaType.WEB_PAGE:
            await client.send_message(sender, msg.text.html or msg.text.markdown, parse_mode=ParseMode.HTML)
            await client.delete_messages(sender, edit_id)
            return None

        # Text only
        if not msg.media and msg.text:
            await client.edit_message_text(sender, edit_id, "**Cloning...")
            await client.send_message(sender, msg.text.html or msg.text.markdown, parse_mode=ParseMode.HTML)
            await client.delete_messages(sender, edit_id)
            return None

        # Poll
        if msg.media == MessageMediaType.POLL:
            await client.edit_message_text(sender, edit_id, "**Poll can't be saved!")
            return None

        # Download media
        edit = await client.edit_message_text(sender, edit_id, "Downloading...")
        file = await userbot.download_media(
            msg,
            progress=progress_for_pyrogram,
            progress_args=(client, "DOWNLOADING...\n", edit, time.time())
        )

        if not file:
            await edit.edit("Download failed!")
            return None

        # Rename if needed
        if file_n:
            ext = file.split(".")[-1]
            new_path = f'/app/downloads/{file_n}' if '.' in file_n else f'/app/downloads/{file_n}.{ext}'
            os.rename(file, new_path)
            file = new_path

        await edit.delete()
        upm = await client.send_message(sender, "**Uploading...")

        caption = msg.caption or os.path.basename(file)

        # Video
        if file.lower().endswith(('.mkv', '.mp4', '.webm', '.mpe4', '.mpeg')):
            if not file.lower().endswith('.mp4'):
                new_file = file.rsplit(".", 1)[0] + ".mp4"
                os.rename(file, new_file)
                file = new_file

            data = video_metadata(file)
            duration = data.get("duration", 0)
            width = data.get("width", 0)
            height = data.get("height", 0)

            thumb_path = None
            try:
                thumb_path = await screenshot(file, duration, sender)
            except:
                pass

            await client.send_video(
                sender, file, caption=caption, duration=duration,
                width=width, height=height, thumb=thumb_path,
                supports_streaming=True,
                progress=progress_for_pyrogram,
                progress_args=(client, 'UPLOADING...\n', upm, time.time())
            )

        # Photo
        elif file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            await upm.edit("**Uploading photo...")
            await bot.send_file(sender, file, caption=caption)

        # Document
        else:
            thumb_path = thumbnail(sender)
            await client.send_document(
                sender, file, caption=caption, thumb=thumb_path,
                progress=progress_for_pyrogram,
                progress_args=(client, 'UPLOADING...\n', upm, time.time())
            )

        # Cleanup
        if os.path.exists(file):
            os.remove(file)
        await upm.delete()

    except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
        await client.edit_message_text(sender, edit_id, "**Bot is not in that group/channel. Send invite link first!**")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await get_msg(userbot, client, sender, edit_id, msg_link, i, file_n)
    except Exception as e:
        logging.error(f"Error in get_msg: {e}")
        await client.edit_message_text(sender, edit_id, f"Error: {str(e)}")
    return None

# Bulk mode
async def get_bulk_msg(userbot, client, sender, msg_link, i):
    x = await client.send_message(sender, "Processing...")
    await get_msg(userbot, client, sender, x.id, msg_link, i, '')
