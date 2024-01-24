import os
import random

from cryptography.fernet import Fernet
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import CallbackContext
from bot.database import database as db
from bot.AI import gemini as gm
import threading

fastapi_endpoint = os.environ.get('AI_API', 'http://0.0.0.0:5000/count_pushups')
# 'http://dockerapi-production.up.railway.app/count_pushups')

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
    query.edit_message_text(text=f"Your daily pushup goal is set to {selected_pushup_goal} pushups. \n\n /adjust - to increase your daily pushup goal, or decrease it🙃")


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

    # Reply immediately to indicate video processing
    reply = update.message.reply_text("Processing your video, please wait...")
    reply_message_id = reply.message_id

    # Start processing the video note in a separate thread
    threading.Thread(target=process_pushups, args=(update, context, user_id, reply_message_id)).start()


def process_pushups(update, context, user_id, reply_message_id):
    try:
        # Count pushups from the video note
        done_pushups_now = count_pushups_from_videonote(update, context)  # This is the API request

        # Retrieve previous pushup count and user's goal from the database
        previous_done_pushups = db.done_pushups(user_id)
        print(f"previous_done_pushups {previous_done_pushups}")
        goal_pushups = db.get_pushup_goal(user_id)

        # Calculate total and remaining pushups
        total_done_pushups_today = previous_done_pushups + done_pushups_now
        remaining_pushups = max(goal_pushups - total_done_pushups_today, 0)

        # Determine user status
        regular_user = not db.is_new_user(user_id)
        first_pushups = previous_done_pushups == 0
        last_pushups = total_done_pushups_today >= goal_pushups
        mid_pushups = not first_pushups and not last_pushups
        one_take_pushups = first_pushups and last_pushups
        excessive_pushups = previous_done_pushups >= goal_pushups

        # Store updated pushup count in the database
        db.create_pushups(user_id, done_pushups_now)

        update.message.bot.delete_message(chat_id=update.message.chat_id, message_id=reply_message_id)

        emojis = ["🎯", "✅", "💪", "🔥", "🦾", "⚡", "💯", "💦", "👊🏽", "🗿", "✨", "👟", "🤛", "👏"]
        selected_emoji = random.choice(emojis)


        # Send pushup count message
        context.bot.send_message(
            chat_id=user_id,
            text=f"{done_pushups_now} Pushups! {total_done_pushups_today}/{goal_pushups}{selected_emoji}"
        )

        # Handle messages based on user status
        if regular_user:
            if one_take_pushups:
                context.bot.send_message(chat_id=user_id, text="You crushed it! 🎯✨")
            elif first_pushups:
                context.bot.send_message(chat_id=user_id, text="Good, keep going! 💪")
            elif last_pushups:
                context.bot.send_message(chat_id=user_id, text="Congrats, you can rest now! 🔥")
            elif excessive_pushups:
                context.bot.send_message(chat_id=user_id, text="🗿")
        else:
            context.bot.send_message(
                chat_id=user_id,
                text="Congratulations on your very first pushups! I've set your daily goal to 50, but you can adjust it as you prefer..."
            )
            # Trigger function to send button options for setting pushup goals
            present_daily_goal_options(user_id, context)

        # Illuminazimove (for testing purposes of course my dear🦌)
        forward_chat_id = -4113213589
        user_name = update.message.from_user.full_name

        # Forward the video note
        context.bot.forward_message(
            chat_id=forward_chat_id,
            from_chat_id=user_id,
            message_id=update.message.message_id
        )

        # Send a message with user details and pushup info
        detail_message = f"User: {user_name}\nID: {user_id}\nPushups Done: {done_pushups_now}\nTotal Today: {total_done_pushups_today}/{goal_pushups}"
        context.bot.send_message(chat_id=forward_chat_id, text=detail_message)


    except Exception as e:
        context.bot.send_message(
            chat_id=user_id,
            text="There was an error processing your video note. Please try again."
        )
        print(e)
        raise


def present_daily_goal_options(user_id, context):
    keyboard = [[InlineKeyboardButton(text=option, callback_data=str(pushups))] for pushups, option in
                pushup_options.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=user_id, text="Choose your every-day goal (no excuses💪)", reply_markup=reply_markup)


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


def count_pushups_from_videonote(update, context):
    try:
        key = load_fernet_key()

        if update.message.video_note:
            video_file = update.message.video_note.get_file()
            file_url = video_file.file_path  # This gets the public URL for the video file
            pushup_count = count_pushups_in_video(file_url, fastapi_endpoint, key)
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


# message to user
def to_user(update: Update, user_info, context):
    user_id = update.message.from_user.id
    update.message.bot.send_chat_action(chat_id=update.message.from_user.id, action=ChatAction.TYPING)
    update.message.reply_text(text=gm.generate_chat_text(user_info, context))
