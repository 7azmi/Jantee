import random
import threading
import time

from telegram import Update, ChatAction, KeyboardButton, ReplyKeyboardMarkup, ParseMode, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from bot.AI import gemini as gm
from bot.database import database as db

from bot.handlers import dm_handlers

global quotes


def load_quotes():
    global quotes
    with open("bot/data/pushup_quotes.txt", "r") as file:
        quotes = [line.strip() for line in file]


def group_start_command(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    full_name = update.message.from_user.full_name

    try:
        # Check if the group is registered in the database
        if not db.check_group_registration(chat_id):
            db.add_new_group(chat_id, update.effective_chat.title)  # Register the group
            update.message.reply_text(text="Hi everyone! This group is now registered for the pushup challenge.")

        if not db.check_user_exists(user_id):
            db.add_new_user(user_id)

        # Check user's group registration status
        user_group = db.get_user_group_id(user_id)
        print(user_group)
        if user_group is None:
            # User is not in a group, register them in this group
            db.register_user_to_group(user_id, chat_id)
            update.message.reply_text(text=f"Welcome, {full_name}! You're now part of this group's pushup challenge.")

        elif user_group != chat_id:
            # User is in a different group, prompt with buttons
            keyboard = [
                [InlineKeyboardButton("Cancel and Leave", callback_data='cancel_leave')],
                [InlineKeyboardButton("Register Here", callback_data='register_here')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text('You are already registered in another group. Choose an option:', reply_markup=reply_markup)

        else:
            # User is already registered in this group
            update.message.reply_text(text="You're all set, ready for your next pushup challenge!")

    except BadRequest as e:
        try:
            # Attempt to send a DM to the user
            context.bot.send_message(chat_id=user_id, text="I don't have permission to send messages in your group. Please enable my messaging permissions.")
        except BadRequest as dm_error:
            print(f"Unable to send message to user {user_id} in group {chat_id}. Error: {dm_error}")


# Additional functions like db.check_group_registration, db.add_new_group, db.get_user_group, db.register_user_in_group need to be implemented.
# You'll also need to handle the callback queries from the inline buttons.



def dm_start_command(update: Update, context: CallbackContext):
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
        # Send a dynamic guide message to existing user based on their status
        dynamic_guide_message = _get_dynamic_guide_message(user_id)  # Placeholder function
        context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        context.bot.send_message(chat_id=update.message.chat_id, text=dynamic_guide_message)

def _get_dynamic_guide_message(user_id):
    # Placeholder for dynamic guide message generation based on user status
    # Replace this with actual logic to generate message based on user's status
    return "Welcome back! Here's your next challenge..."  # Example message


def test_command_handler(update: Update, context: CallbackContext):
    # Assuming we have the user's ID and first name
    user_id = 732496348
    first_name = "UserFirstName"  # Ideally, you would get this dynamically

    # Construct the mention
    mention = f'<a href="tg://user?id={user_id}">{first_name}</a>'

    # Send a message with the mention
    update.message.reply_text(f"Hello, {mention}!", parse_mode=ParseMode.HTML)
    # location_keyboard = KeyboardButton(text="Send Location", request_location=True)
    # custom_keyboard = [[location_keyboard]]
    # reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    # update.message.reply_text("Please share your location to find your local time:", reply_markup=reply_markup)


def adjust_command_handler(update: Update, context: CallbackContext):
    dm_handlers.present_daily_goal_options(update.message.from_user.id, context)


