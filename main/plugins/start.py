#Github.com/Vasusen-code

#Github.com/Vasusen-code

import os
from .. import bot as Drone
from telethon import events, Button

#from ethon.mystarts import start_srb
    
S = '/' + 's' + 't' + 'a' + 'r' + 't'

@Drone.on(events.callbackquery.CallbackQuery(data="set"))
async def sett(event):    
    Drone = event.client
    button = await event.get_message()
    msg = await button.get_reply_message()
    await event.delete()
    async with Drone.conversation(event.chat_id) as conv: 
        xx = await conv.send_message("**Send me any image for thumbnail as a `reply` to this message.📸**")
        x = await conv.get_reply()
        if not x.media:
            xx.edit("**No media found.📸**")
        mime = x.file.mime_type
        if 'png' not in mime and 'jpg' not in mime and 'jpeg' not in mime:
            return await xx.edit("**No image found.**")
        await xx.delete()
        t = await event.client.send_message(event.chat_id, '**Trying...**')
        path = await event.client.download_media(x.media)
        if os.path.exists(f'{event.sender_id}.jpg'):
            os.remove(f'{event.sender_id}.jpg')
        os.rename(path, f'./{event.sender_id}.jpg')
        await t.edit("**Temporary thumbnail saved!📸**")
        
@Drone.on(events.callbackquery.CallbackQuery(data="rem"))
async def remt(event):  
    Drone = event.client            
    await event.edit('**Trying...**')
    try:
        os.remove(f'{event.sender_id}.jpg')
        await event.edit('**Removed!**')
    except Exception:
        await event.edit("**No thumbnail saved.📸**")                        
  
@Drone.on(events.NewMessage(incoming=True, pattern=f"{S}"))
async def start(event):
    text = "**🔰 Welcome To Dynamic Saver Bot 💞\n\nSend me Link of any message to clone it here, For private channel message, send invite link first.\n\nSET THUMB.📸 - Set a thumbnail\nREM THUMB.📸 - Remove Thumbnail\n\nNeed any help ? Click 👉 Support\n\n/batch to download in Batch Mode\n\n/speed to chcek bot speed\n\n/stats to check bot stats\n\n Simply Send Link to Download in Singal Mode.**"
    #await start_srb(event, text)
    await event.reply(text, 
                      buttons=[
                              [Button.inline("SET THUMB.📸", data="set"),
                               Button.inline("REM THUMB.📸", data="rem")],
                              [Button.url("Channel ⚡", url="https://t.me/tapori420_Official"),
                               Button.url("Support 💌", url="https://t.me/taporibot_bot")],
                              [Button.url("Developer 🧑‍💻", url="https://t.me/taporibot_bot")]
                              ])
    '''
    await event.reply(text, 
                      buttons=[
                              [Button.inline("SET THUMB.📸", data="set"),
                               Button.inline("REM THUMB.📸", data="rem")],
                              [Button.url("Maintained and Modified by", url="t.me/xTnmgbR6rjgCDF7iPoFfiN8YfBsez9Lv")]
                              ])
    '''
    

