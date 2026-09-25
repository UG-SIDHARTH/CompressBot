import os
import tempfile
import subprocess
import discord
from discord.ext import commands
from pydub import AudioSegment
from config import *

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Process commands if any
    await bot.process_commands(message)

    if not message.attachments:
        return

    for attachment in message.attachments:
        mime_type = attachment.content_type
        if mime_type:
            if mime_type.startswith('audio/'):
                await handle_audio(message, attachment)
            elif mime_type.startswith('video/') or mime_type.startswith('image/gif'):
                await handle_video(message, attachment)

async def handle_audio(message, attachment):
    msg = await message.channel.send("Processing audio... 🎧")
    
    # Download file
    input_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    await attachment.save(input_file.name)
    
    output_filename = ""
    try:
        audio = AudioSegment.from_file(input_file.name).set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)
        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX_AUDIO, delete=False) as temp_out_file:
            output_filename = temp_out_file.name
            audio.export(output_filename, format=AUDIO_FORMAT, bitrate=AUDIO_BITRATE)
            
        await message.reply(file=discord.File(output_filename))
        await msg.delete()
    except Exception as e:
        await msg.edit(content=f"Failed to process audio: {str(e)}")
    finally:
        if os.path.exists(input_file.name):
            os.remove(input_file.name)
        if output_filename and os.path.exists(output_filename):
            os.remove(output_filename)

async def handle_video(message, attachment):
    msg = await message.channel.send("Processing video... 🎥")
    
    input_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    await attachment.save(input_file.name)
    
    output_filename = ""
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_out_file:
            output_filename = temp_out_file.name
            
        subprocess.run(f'ffmpeg -y -i "{input_file.name}" -filter_complex "scale={VIDEO_SCALE}" -r {VIDEO_FPS} -c:v {VIDEO_CODEC} -pix_fmt {VIDEO_PIXEL_FORMAT} -b:v {VIDEO_BITRATE} -crf {VIDEO_CRF} -preset {VIDEO_PRESET} -c:a {VIDEO_AUDIO_CODEC} -b:a {VIDEO_AUDIO_BITRATE} -ac {VIDEO_AUDIO_CHANNELS} -ar {VIDEO_AUDIO_SAMPLE_RATE} -profile:v {VIDEO_PROFILE} -map_metadata -1 "{output_filename}"', shell=True, check=True)
        
        # Discord has an 8MB (or 25MB) file limit. This bot will attempt to send it back.
        await message.reply(file=discord.File(output_filename))
        await msg.delete()
    except Exception as e:
        await msg.edit(content=f"Failed to process video: {str(e)}")
    finally:
        if os.path.exists(input_file.name):
            os.remove(input_file.name)
        if output_filename and os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == "__main__":
    if DISCORD_BOT_TOKEN:
        bot.run(DISCORD_BOT_TOKEN)
    else:
        print("Please set DISCORD_BOT_TOKEN in .env")
