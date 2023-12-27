
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update, InputFile
from telegram.ext import CommandHandler, CallbackQueryHandler


fastapi_endpoint = 'http://dockerapi-production.up.railway.app'


def set_commands_handler(dp):
    dp.add_handler(CommandHandler('start', start_command))


def echo(update: Update, context):

    if update.message.video_note or update.message.video:
        video_file = update.message.video.get_file()
        file_url = video_file.file_path  # This gets the public URL for the video file

        # Send the video URL to your FastAPI endpoint
        response = requests.get(fastapi_endpoint, params={'videourl': file_url})

        # Handle the response if needed
        if response.status_code == 200:
            pushup_count = response.json().get('pushup_count')
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Pushup count: {pushup_count}")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Error processing video.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please send a video.")


def start_command(update, context):
    update.message.reply_text('hi!')

