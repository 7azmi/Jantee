import os
import random

from cryptography.fernet import Fernet
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction, bot
from telegram.ext import CallbackContext
from bot.database import database as db
from bot.AI import gemini as gm
from bot import pushup_counter as pc
from bot.shared import *
import threading



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
    query.edit_message_text(
        text=f"Your daily pushup goal is set to {selected_pushup_goal} pushups. \n\n /adjust - to increase your daily pushup goal, or decrease it🙃")


# Add this handler for callback queries
def handle_video(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    context.bot.send_message(chat_id=user_id, text="Please send a live videonote. Regular videos are not accepted.")

    # Replace 'videonotenotvideo.gif' with the actual path to your GIF file
    gif_file_path = 'videonotenotvideo.gif'

    with open(gif_file_path, 'rb') as gif_file:
        context.bot.send_animation(chat_id=user_id, animation=gif_file)


def handle_videonote(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    first_proper_pushups = db.check_user_exists(user_id) and db.user_has_pushup_records(user_id)

    if first_proper_pushups:
        say_hi_to_new_user(update, context)
    else:
        send_dynamic_guide_message(update, context)

# say hi flow
def say_hi_to_new_user(update: Update, context: CallbackContext):
    pass


def send_dynamic_guide_message(update: Update, context: CallbackContext):
    pass

def process_pushups(update, context, user_id, reply_message_id):
    try:
        # Count pushups from the video note
        done_pushups_now = pc.count_pushups_from_videonote(update, context)  # This is the API request
        no_pushups = done_pushups_now == 0
        few_pushups = not no_pushups and done_pushups_now < 5

        # Retrieve previous pushup count and user's goal from the database
        previous_done_pushups = db.done_pushups(user_id)
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
        extra_pushups = previous_done_pushups >= goal_pushups

        # Store updated pushup count in the database
        db.create_pushups(user_id, done_pushups_now)

        update.message.bot.delete_message(chat_id=update.message.chat_id, message_id=reply_message_id)

        emojis = ["🎯", "✅", "💪", "🔥", "🦾", "⚡", "💯", "💦", "👊🏽", "🗿", "✨", "👟", "🤛", "👏"]
        selected_emoji = random.choice(emojis)

        message = "No pushups detected, make sure your whole body is within the video circle" if no_pushups else \
            f"{done_pushups_now} Pushups! {total_done_pushups_today}/{goal_pushups}{selected_emoji}"

        # Send pushup count message
        context.bot.send_message(
            chat_id=user_id,
            text=message
        )

        if not no_pushups:
            # Handle messages based on user status
            if regular_user:
                if one_take_pushups:
                    context.bot.send_message(chat_id=user_id, text="You crushed it! 🎯✨")
                elif extra_pushups:
                    context.bot.send_message(chat_id=user_id, text="🗿")
                elif few_pushups:
                    context.bot.send_message(chat_id=user_id,
                                             text=f"Just {done_pushups_now} pushups? You can do better\n\n Remember, lazy half-pushups are not counted btw!")
                elif first_pushups:
                    context.bot.send_message(chat_id=user_id, text="Good, keep going! 💪")
                elif last_pushups:
                    context.bot.send_message(chat_id=user_id, text="Congrats, you can rest now! 🔥")
            else:
                context.bot.send_message(
                    chat_id=user_id,
                    text="Congratulations on your very first pushups! I've set your daily goal to 50, but you can adjust it as you prefer..."
                )
                # Trigger function to send button options for setting pushup goals
                present_daily_goal_options(user_id, context)

        forward_videonote_to_debugging_group(update, context, done_pushups_now, total_done_pushups_today, goal_pushups)


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

    context.bot.send_message(chat_id=user_id, text="Choose your every-day goal (no excuses💪)",
                             reply_markup=reply_markup)


# message to user
def to_user(update: Update, user_info, context):
    user_id = update.message.from_user.id
    update.message.bot.send_chat_action(chat_id=update.message.from_user.id, action=ChatAction.TYPING)
    update.message.reply_text(text=gm.generate_chat_text(user_info, context))
