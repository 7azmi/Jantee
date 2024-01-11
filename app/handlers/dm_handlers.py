import os

from cryptography.fernet import Fernet
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import CallbackContext
from app.database import database as db
from app.gemini import gemini as gm

fastapi_endpoint = os.environ.get('AI_API',
                                  'http://0.0.0.0:5000/count_pushups')  # 'http://dockerapi-production.up.railway.app/count_pushups')

pushup_options = {
    15: "15 Pushups - Great for beginners!",
    25: "25 Pushups - Good for getting started!",
    50: "50 Pushups - A solid daily goal.",
    75: "75 Pushups - For the more ambitious!",
    100: "100 Pushups - A challenging target.",
    150: "150 Pushups - For advanced fitness levels.",
    200: "200 Pushups - For true pushup masters!"
}

def handle_pushup_goal_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    selected_pushup_goal = int(query.data)

    # Store the chosen pushup goal in the database
    db.set_pushup_goal(user_id, selected_pushup_goal)

    query.answer()
    query.edit_message_text(text=f"Your daily pushup goal is set to {selected_pushup_goal} pushups.")

# Add this handler for callback queries
def handle_video_dm(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    context.bot.send_message(chat_id=user_id, text="Please send a live videonote. Regular videos are not accepted.")

    # Replace 'videonotenotvideo.gif' with the actual path to your GIF file
    gif_file_path = 'videonotenotvideo.gif'

    with open(gif_file_path, 'rb') as gif_file:
        context.bot.send_animation(chat_id=user_id, animation=gif_file)

def handle_videonote_dm(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_full_name = update.message.from_user.full_name
    pushup_count = count_pushups_from_videonote(update, context, fastapi_endpoint)

    if pushup_count is None:
        update.message.reply_text(text="There was an error processing your video note. Please try again.")
        return

    if pushup_count == 0:
        to_user(update, user_full_name, "Please record properly, no pushups detected.")
        return

    if 1 <= pushup_count < 5:
        response_message = f"Short instruction message: Got it, I've counted {pushup_count} pushups, but please check if you're working out and recording properly (at least 5 pushups)."
    elif pushup_count >= 5:
        response_message = handle_successful_pushup_count(update, user_id, user_full_name, pushup_count, context)

    to_user(update, user_full_name, response_message)
    db.create_pushups(user_id, pushup_count, "+08")


def handle_successful_pushup_count(update, user_id, user_full_name, pushup_count, context):
    if db.is_new_user(user_id):
        present_daily_goal_options(user_id, context)
        return f"Great! You've done your first {pushup_count} pushups. Now it's time to choose how many pushups a day you want to commit to. (daily goal options are 15, 25, 50, 75, 100, 150, 200)"

    remaining_pushups = db.get_remaining_pushups_user(update.message.from_user.id)
    if remaining_pushups <= 0:
        return f"🎉 Congratulations, {user_full_name}! You've completed your daily goal! 🏆"
    else:
        return f"Short progress message: Keep going, You've done {pushup_count} pushups and have {remaining_pushups} left for today! 💪"




def present_daily_goal_options(user_id, context):
    keyboard = [[InlineKeyboardButton(text=option, callback_data=str(pushups))] for pushups, option in
                pushup_options.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=user_id, text="Choose your daily pushup goal:", reply_markup=reply_markup)



def load_fernet_key():
    key = os.environ.get('FERNET_KEY', 'OR9Hdu3NKcaT4PPHJni3NAepp61DL_SGeOmB2Eg7PT0=')  # change this later
    if not key:
        raise ValueError("Fernet key not found in environment variables")

    # Convert the key from string to bytes without altering it
    return key.encode()


def encrypt_message(message, key):
    f = Fernet(key)
    return f.encrypt(message.encode())


def send_encrypted_video_to_fastapi(data, fastapi_endpoint):
    try:
        response = requests.post(fastapi_endpoint, data=data)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None


def count_pushups_from_videonote(update, context, fastapi_endpoint):
    try:
        key = load_fernet_key()

        if update.message.video_note:
            video_file = update.message.video_note.get_file()
            file_url = video_file.file_path  # This gets the public URL for the video file
            update.message.bot.send_chat_action(chat_id=update.message.from_user.id, action=ChatAction.TYPING)
            counting_message = update.message.reply_text("counting...")  # Store the counting message
            pushup_count = count_pushups_in_video(file_url, fastapi_endpoint, key)
            update.message.bot.delete_message(chat_id=update.message.chat_id, message_id=counting_message.message_id)
            #update.message.bot.edit_message_text(text=f"{pushup_count} pushups", chat_id=update.message.chat_id, message_id=counting_message.message_id)
            return pushup_count
        else:
            raise Exception("No video or video note found in the message.")

    except Exception as e:
        raise Exception(f"Error in processing videonote: {e}")


def count_pushups_in_video(video_url, fastapi_endpoint, key):
    try:
        encrypted_url = encrypt_message(video_url, key)
        data = {'encrypted_video_url': encrypted_url.decode()}

        response = requests.post(fastapi_endpoint, data=data)

        if response is not None:
            if response.status_code == 200:
                pushup_count = response.json().get('pushup_count')
                return pushup_count
            else:
                raise Exception("Error processing video at server.")
        else:
            raise Exception("Error sending video to the server.")
    except Exception as e:
        raise Exception(f"Error in counting pushups: {e}")


#     key = load_fernet_key()
#
#     if update.message.video_note or update.message.video:
#         if update.message.video_note:
#             video_file = update.message.video_note.get_file()
#         else:
#             video_file = update.message.video.get_file()
#
#         file_url = video_file.file_path  # This gets the public URL for the video file
#
#         encrypted_url = encrypt_message(file_url, key)
#         data = {'encrypted_video_url': encrypted_url.decode()}
#
#         update.message.reply_text("Counting...")
#
#         response = send_encrypted_video_to_fastapi(data, fastapi_endpoint)
#
#         if response is not None:
#             if response.status_code == 200:
#                 # first_time = "User records his first pushup videonote" if True else "User is re" # todo first time variable
#                 pushup_count = response.json().get('pushup_count')
#                 context.bot.send_chat_action(chat_id=update.message.from_user.id, action=ChatAction.TYPING)
#                 cntxt = "congratulate the user for doing his first pushups and tell him how many he's done, and instruct him to proceed to create a group with his friends and add you (Jantee) to the group" if pushup_count > 0 \
#                     else "0 pushups means there is something wrong with the recording or positions or else. Tell the user to check the GIF instruction message above the chat and try shooting again"
#                 # text = f"Pushup count: {pushup_count}"
#                 to_user(update,
#                         f"user full name: {update.message.from_user.full_name}, achieved pushups now: {pushup_count}",
#                         cntxt)
#             else:
#                 context.bot.send_message(chat_id=update.effective_chat.id, text="Error processing video.")
#         else:
#             context.bot.send_message(chat_id=update.effective_chat.id, text="Error sending video to the server.")
#     # else:
#     # context.bot.send_message(chat_id=update.effective_chat.id, text="Please send a video.")



#
# def send_encrypted_video_to_fastapi(data, fastapi_endpoint):
#     try:
#         response = requests.post(fastapi_endpoint, data=data)
#         return response
#     except requests.exceptions.RequestException as e:
#         print(f"Request error: {e}")
#         return None
#
#
# def count_pushups_from_videonote(update, context):
#     key = load_fernet_key()
#
#     #video_file = update.message.video_note or update.message.video
#     video_file = update.message.video
#     file_url = video_file.get_file().file_path  # Gets the public URL for the video file
#
#     encrypted_url = encrypt_message(file_url, key)
#     if not encrypted_url:
#         context.bot.send_message(chat_id=update.effective_chat.id, text="Error encrypting video URL.")
#         return None
#
#     response = send_encrypted_video_to_fastapi(encrypted_url.decode(), fastapi_endpoint)
#     if response and response.status_code == 200:
#         pushup_count = response.json().get('pushup_count', 0)
#         return pushup_count
#     else:
#         error_message = "Error processing video." if not response else response.json().get('detail', "Error processing video.")
#         context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)
#         return None

# def count_pushups_from_videonote(update, context):
#     key = load_fernet_key()
#
#     # Determine if the message is a video note or a regular video
#     video_file = update.message.video_note or update.message.video
#     file_url = video_file.get_file().file_path  # Gets the public URL for the video file
#
#     encrypted_url = encrypt_message(file_url, key)
#     if not encrypted_url:
#         context.bot.send_message(chat_id=update.effective_chat.id, text="Error encrypting video URL.")
#         return None, None
#
#     data = {'encrypted_video_url': encrypted_url.decode()}
#
#     response = send_encrypted_video_to_fastapi(data, fastapi_endpoint)
#     if response is not None:
#         if response.status_code == 200:
#             pushup_count = response.json().get('pushup_count', 0)
#             daily_pushup_goal = db.get_daily_pushup_goal_from_user(update.message.from_user.id)
#             remaining_pushups = daily_pushup_goal - pushup_count - db.remaining_pushups(update.message.from_user.id, db.get_date_by_timezone("+08"))
#             return pushup_count, remaining_pushups
#         else:
#             error_message = response.json().get('detail', "Error processing video.")
#             context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)
#             return None, None
#     else:
#         context.bot.send_message(chat_id=update.effective_chat.id, text="Error sending video to the server.")
#         return None, None
#
# def send_encrypted_video_to_fastapi(data, fastapi_endpoint):
#     try:
#         response = requests.post(fastapi_endpoint, json=data)
#         return response
#     except requests.exceptions.RequestException as e:
#         print(f"Request error: {e}")
#         return None


# def dm_videonote_receiver(update, context):
#     key = load_fernet_key()
#
#     if update.message.video_note or update.message.video:
#         if update.message.video_note:
#             video_file = update.message.video_note.get_file()
#         else:
#             video_file = update.message.video.get_file()
#
#         file_url = video_file.file_path  # This gets the public URL for the video file
#
#         encrypted_url = encrypt_message(file_url, key)
#         data = {'encrypted_video_url': encrypted_url.decode()}
#
#         update.message.reply_text("Counting...")
#
#         response = send_encrypted_video_to_fastapi(data, fastapi_endpoint)
#
#         if response is not None:
#             if response.status_code == 200:
#                 # first_time = "User records his first pushup videonote" if True else "User is re" # todo first time variable
#                 pushup_count = response.json().get('pushup_count')
#                 context.bot.send_chat_action(chat_id=update.message.from_user.id, action=ChatAction.TYPING)
#                 cntxt = "congratulate the user for doing his first pushups and tell him how many he's done, and instruct him to proceed to create a group with his friends and add you (Jantee) to the group" if pushup_count > 0 \
#                     else "0 pushups means there is something wrong with the recording or positions or else. Tell the user to check the GIF instruction message above the chat and try shooting again"
#                 # text = f"Pushup count: {pushup_count}"
#                 to_user(update,
#                         f"user full name: {update.message.from_user.full_name}, achieved pushups now: {pushup_count}",
#                         cntxt)
#             else:
#                 context.bot.send_message(chat_id=update.effective_chat.id, text="Error processing video.")
#         else:
#             context.bot.send_message(chat_id=update.effective_chat.id, text="Error sending video to the server.")
    # else:
    # context.bot.send_message(chat_id=update.effective_chat.id, text="Please send a video.")

# def count_pushups_from_videonote(update, context):
#     try:
#         key = load_fernet_key()
#
#         video_file = update.message.video_note or update.message.video
#         file_url = video_file.get_file().file_path  # This gets the public URL for the video file
#
#         encrypted_url = encrypt_message(file_url, key)
#         data = {'encrypted_video_url': encrypted_url.decode()}
#
#         update.message.reply_text("Counting...")
#
#         response = requests.post(fastapi_endpoint, json=data)
#
#         if response.status_code == 200:
#             pushup_count = response.json().get('pushup_count', 0)
#             # Assuming 'daily_pushup_goal' is defined or retrieved from the database
#             daily_pushup_goal = db.get_daily_pushup_goal_from_user(update.message.from_user.id)
#             remaining_pushups = daily_pushup_goal - pushup_count - db.remaining_pushups(update.message.from_user.id, db.get_date_by_timezone("+08"))
#             return pushup_count, remaining_pushups
#         else:
#             # Handle non-200 responses
#             error_message = response.json().get('detail', "Error processing video.")
#             raise Exception(error_message)
#
#     except Exception as e:
#         # If an error occurs, send an error feedback message
#         error_feedback = str(e)
#         context.bot.send_message(chat_id=update.effective_chat.id, text=error_feedback)
#         return None, None  # Return None values if there was an error

# message to user
def to_user(update: Update, user_info, context):
    user_id = update.message.from_user.id
    update.message.bot.send_chat_action(chat_id=update.message.from_user.id, action=ChatAction.TYPING)
    update.message.reply_text(text=gm.generate_chat_text(user_info, context, "English"))#for now
