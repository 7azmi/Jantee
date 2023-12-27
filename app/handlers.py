import os
import requests
from cryptography.fernet import Fernet
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update, InputFile
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext

import app.data.data

fastapi_endpoint = os.environ.get('AI_API', 'http://0.0.0.0:5000/count_pushups')#'http://dockerapi-production.up.railway.app/count_pushups')

def set_commands_handler(dp):
    dp.add_handler(CommandHandler('start', start_command))


def load_fernet_key():
    key = os.environ.get('FERNET_KEY', 'OR9Hdu3NKcaT4PPHJni3NAepp61DL_SGeOmB2Eg7PT0=')#change this later
    if not key:
        raise ValueError("Fernet key not found in environment variables")

    # Convert the key from string to bytes without altering it
    return key.encode()


def encrypt_message(message, key):
    f = Fernet(key)
    return f.encrypt(message.encode())


def echo(update, context):
    key = load_fernet_key()

    if update.message.video_note or update.message.video:
        if update.message.video_note:
            video_file = update.message.video_note.get_file()
        else:
            video_file = update.message.video.get_file()

        file_url = video_file.file_path  # This gets the public URL for the video file

        encrypted_url = encrypt_message(file_url, key)
        data = {'encrypted_video_url': encrypted_url.decode()}
        response = requests.post(fastapi_endpoint, data=data)

        # Handle the response if needed
        if response.status_code == 200:
            pushup_count = response.json().get('pushup_count')
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Pushup count: {pushup_count}")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Error processing video.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please send a video.")


def chat_member_update(update: Update, context: CallbackContext):
    # Determine the type of update
    if update.my_chat_member:
        chat_member_update = update.my_chat_member
    elif update.chat_member:
        chat_member_update = update.chat_member
    else:
        print("Received an unknown type of chat member update.")
        return

    # Check if old and new chat member data is available
    if chat_member_update.old_chat_member and chat_member_update.new_chat_member:
        old_status = chat_member_update.old_chat_member.status
        new_status = chat_member_update.new_chat_member.status

        # Check if the update is about the bot itself
        if chat_member_update.new_chat_member.user.id == context.bot.id:
            # Bot added to the group
            if new_status == 'member' and old_status != 'member':
                print("Bot was added to the group.")

            # Bot kicked out or left the group
            elif old_status == 'member' and new_status != 'member':
                print(new_status)
                if new_status == 'kicked':
                    print("Bot was kicked out of the group.")
                else:
                    print("Bot left the group.")  # what's gonna happen


def user_status_update(update: Update, context: CallbackContext):
    print('hehe')
    # Determine the type of update
    if update.chat_member:
        chat_member_update = update.chat_member
    else:
        print("Received an update that is not a chat member update.")
        return

    # Check if old and new chat member data is available
    old_chat_member = chat_member_update.old_chat_member
    new_chat_member = chat_member_update.new_chat_member

    if old_chat_member and new_chat_member:
        old_status = old_chat_member.status
        new_status = new_chat_member.status
        user_id = new_chat_member.user.id

        # Ensure the update is not about the bot itself
        if user_id != context.bot.id:
            # User joined the group
            if new_status == 'member' and old_status != 'member':
                print(f"User {user_id} joined the group.")

            # User left or was removed from the group
            elif old_status == 'member' and new_status != 'member':
                print(f"User {user_id} left or was removed from the group.")


def start_command(update, context):
    update.message.reply_text(app.data.data.get_message('start_new_user'))
