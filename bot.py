import os
import tempfile
import subprocess
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pydub import AudioSegment
from config import *

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Compress Audio 🎧", callback_data="compress_audio"),
               InlineKeyboardButton("Compress Video 🎥", callback_data="compress_video"))
    bot.send_message(message.chat.id, "Choose what you want to compress:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.send_message(call.message.chat.id, "Send me a file.")

def download_file(file_id, suffix):
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(downloaded_file)
        return temp_file.name

@bot.message_handler(content_types=['voice', 'audio'])
def handle_audio(message):
    processing_msg = bot.send_message(message.chat.id, "Processing audio... 🎧")
    try:
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file_path = download_file(file_id, '.ogg' if message.voice else '.mp3')
        
        audio = AudioSegment.from_file(file_path).set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)
        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX_AUDIO, delete=False) as temp_file:
            temp_filename = temp_file.name
            audio.export(temp_filename, format=AUDIO_FORMAT, bitrate=AUDIO_BITRATE)
            
        with open(temp_filename, 'rb') as doc:
            bot.send_document(message.chat.id, doc)
            
        bot.delete_message(message.chat.id, processing_msg.message_id)
        os.remove(file_path)
        os.remove(temp_filename)
    except Exception as e:
        bot.edit_message_text(f"Failed to process audio: {str(e)}", message.chat.id, processing_msg.message_id)

@bot.message_handler(content_types=['video', 'animation'])
def handle_media(message):
    processing_msg = bot.send_message(message.chat.id, "Processing video... 🎥")
    try:
        file_id = message.video.file_id if message.video else message.animation.file_id
        file_path = download_file(file_id, '.mp4')
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_filename = temp_file.name
            
        subprocess.run(f'ffmpeg -y -i "{file_path}" -filter_complex "scale={VIDEO_SCALE}" -r {VIDEO_FPS} -c:v {VIDEO_CODEC} -pix_fmt {VIDEO_PIXEL_FORMAT} -b:v {VIDEO_BITRATE} -crf {VIDEO_CRF} -preset {VIDEO_PRESET} -c:a {VIDEO_AUDIO_CODEC} -b:a {VIDEO_AUDIO_BITRATE} -ac {VIDEO_AUDIO_CHANNELS} -ar {VIDEO_AUDIO_SAMPLE_RATE} -profile:v {VIDEO_PROFILE} -map_metadata -1 "{temp_filename}"', shell=True, check=True)
        
        with open(temp_filename, 'rb') as video:
            bot.send_video(message.chat.id, video)
            
        bot.delete_message(message.chat.id, processing_msg.message_id)
        os.remove(file_path)
        os.remove(temp_filename)
    except Exception as e:
        bot.edit_message_text(f"Failed to process video: {str(e)}", message.chat.id, processing_msg.message_id)

if __name__ == "__main__":
    if not API_TOKEN or "your_bot_token_here" in API_TOKEN:
        print("Please set API_TOKEN in .env file.")
    else:
        print("Starting Telegram Bot...")
        bot.infinity_polling()
