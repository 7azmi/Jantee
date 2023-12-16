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


def echo(update: Update, context):# Here where lucy recieves all videonotes and accedintal videos. commands are held somewhere else
    user_id = update.message.from_user.id
    # Check if the message is a video note
    if update.message.video_note or update.message.video:
        # Get the video note file ID
        video_note_file_id = update.message.video_note.file_id

        # Retrieve the file object using the file ID
        video_note_file = context.bot.get_file(video_note_file_id)

        # Download the video note to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video_file:
            with open(temp_video_file.name, 'wb') as file:
                video_note_file.download(out=file)

            # Process the video for pushup count and annotations
            video_stream = cv2.VideoCapture(temp_video_file.name)
            pushup_count = pushup_counter.calculate_pushups_from_stream(video_stream)
            video_stream.release()

            video_stream = cv2.VideoCapture(temp_video_file.name)
            pushup_count_annotated, annotated_video = pushup_counter.calculate_and_annotate_pushups(video_stream)
            video_stream.release()

            # Save the annotated video to a new temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as annotated_video_file:
                # Write frames to the new video file
                # [Save annotated_video frames to annotated_video_file]

                # Send the original video note with pushup count
                context.bot.send_message(chat_id=update.message.chat_id, text=f"Pushup Count: {pushup_count}")

                # Send the annotated video note
                context.bot.send_video_note(chat_id=update.message.chat_id,
                                            video_note=open(annotated_video_file.name, 'rb'))

        # Clean up temporary files
        shutil.rmtree(temp_video_file.name)
        shutil.rmtree(annotated_video_file.name)


def start_command(update, context):
    update.message.reply_text('hi!')

