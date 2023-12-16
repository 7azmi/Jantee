import re
from io import BytesIO

import cv2
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update, InputFile
from telegram.ext import CommandHandler, CallbackQueryHandler

from database.database import *
import tempfile
import shutil
from app.pushup_detector import pushup_counter
from io import BytesIO

def set_commands_handler(dp):
    dp.add_handler(CommandHandler('start', start_command))


def echo(update: Update, context):
    user_id = update.message.from_user.id
    # Check if the message is a video note or a video
    if update.message.video_note or update.message.video:
        # Get the video (or video note) file ID
        video_file_id = update.message.video_note.file_id if update.message.video_note else update.message.video.file_id

        # Retrieve the file object using the file ID
        video_file = context.bot.get_file(video_file_id)

        # Download the video to a temporary file
        with tempfile.NamedTemporaryFile(delete=True, suffix='.mp4') as temp_video_file:
            with open(temp_video_file.name, 'wb') as file:
                video_file.download(out=file)

            # Process the video for pushup count
            video_stream = cv2.VideoCapture(temp_video_file.name)
            pushup_count = pushup_counter.calculate_pushups_from_stream(video_stream)
            video_stream.release()

            # Send the pushup count as a text message
            context.bot.send_message(chat_id=update.message.chat_id, text=f"Pushup Count: {pushup_count}")

        # Clean up the temporary file
        os.remove(temp_video_file.name)



def start_command(update, context):
    update.message.reply_text('hi!')

