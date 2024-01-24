import random
import threading
import time

from telegram import Update, ChatAction
from telegram.ext import CallbackContext

from bot.AI import gemini as gm
from bot.database import database as db

from bot.handlers import dm_handlers

global quotes


def load_quotes():
    global quotes
    with open("bot/data/pushup_quotes.txt", "r") as file:
        quotes = [line.strip() for line in file]



def start_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    full_name = update.message.from_user.full_name

    new_user = not db.check_user_exists(user_id)

    if new_user:
        # Add new user to database
        db.add_new_user(user_id)

        # Greet the user
        context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        welcome_message = "Hi {}! Welcome to the pushup challenge bot.".format(full_name)
        update.message.reply_text(text=welcome_message)

        # Send how-to-use video note
        videonote_path = 'howtodopushups.mp4'  # Ensure this is the correct path
        with open(videonote_path, 'rb') as videonote:
            context.bot.send_video_note(chat_id=update.message.chat_id, video_note=videonote)

        # Send instructions message
        context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        instruction_message = (
            "Now, record a videonote of yourself doing 10-20 pushups facing the camera with your entire body in the circle frame. Half-pushups won't count.")
        update.message.reply_text(text=instruction_message)

    else:
        # Send a stored random quote to existing user
        fitness_tip_or_quote = random.choice(quotes)
        context.bot.send_message(chat_id=update.message.chat_id, text=fitness_tip_or_quote)


def test_command_handler(update: Update, context: CallbackContext):
    # Reply immediately to acknowledge the command
    update.message.reply_text("Test started, please wait...")

    # Start the process in a separate thread
    threading.Thread(target=wait_and_respond, args=(update, context)).start()


def adjust_command_handler(update: Update, context: CallbackContext):
    dm_handlers.present_daily_goal_options(update.message.from_user.id, context)


def wait_and_respond(update: Update, context: CallbackContext):
    # Wait for 15 seconds
    time.sleep(15)

    # Send the feedback message
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi")

# Add the handler for the '/test' command to the dispatcher
