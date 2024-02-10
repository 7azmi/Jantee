import os
import random
import threading
from telegram import Update
from telegram.ext import CallbackContext
import bot.handlers.pushup_counter as pc
from bot.database import database as db

BOT_USERNAME = os.environ.get("BOT_USERNAME", "janteebot")
def handle_videonote(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if not _is_normal_recording_flow(user_id, update.message.chat_id):
        _send_dynamic_guide_message(update, context)
        return

    # Reply immediately to indicate video processing
    reply = update.message.reply_text("I'm counting, hold ya...")
    reply_message_id = reply.message_id

    # Start processing the video note in a separate thread
    threading.Thread(target=_process_pushups_group, args=(update, context, user_id, reply_message_id)).start()


def _send_dynamic_guide_message(update: Update, context: CallbackContext):
    print("_send_dynamic_guide_message")

def _process_pushups_group(update, context, user_id, reply_message_id):
    chat_id = update.effective_chat.id
    try:
        # Count pushups from the video note
        done_pushups_now = pc.count_pushups_from_videonote(update, context) # the heavy lifting

        # Delete the 'counting' message
        update.message.bot.delete_message(chat_id=update.message.chat_id, message_id=reply_message_id)

        # Send pushup count message or alternative flow message
        if done_pushups_now >= 5:
            _normal_flow_message(user_id, chat_id, context, done_pushups_now)
        else:
            _alternative_flow_message(user_id, chat_id, context, done_pushups_now)

    except Exception as e:
        # Error handling
        context.bot.send_message(
            chat_id=chat_id,
            text="There was an error processing your video note. Please try again."
        )
        raise e

def _is_normal_recording_flow(user_id, chat_id):
    # Check if user exists, has a complete profile, and is not registered in a different group
    # Replace with actual logic based on your database structure
    return db.check_user_exists(user_id) and not db.is_registered_in_different_group(user_id, chat_id) # and db.has_complete_profile(user_id)


def _normal_flow_message(user_id, chat_id, context, done_pushups_now):
    # Send pushup count message
    emojis = ["🎯", "✅", "💪", "🔥", "🦾", "⚡", "💯", "💦", "👊🏽", "🗿", "✨", "👟", "🤛", "👏"]
    selected_emoji = random.choice(emojis)
    previous_done_pushups = db.done_pushups(user_id)
    goal_pushups = db.get_pushup_goal(user_id)
    total_done_pushups_today = previous_done_pushups + done_pushups_now if previous_done_pushups else done_pushups_now
    count_message = f"{done_pushups_now} Pushups! {total_done_pushups_today}/{goal_pushups} {selected_emoji}"
    context.bot.send_message(chat_id=chat_id, text=count_message)

    # Determine and send dynamic message based on set status
    user_set_status = _set_status(user_id, done_pushups_now)
    dynamic_message = _get_dynamic_set_message(user_set_status, total_done_pushups_today, goal_pushups)

    # Store updated pushup count in the database
    db.create_pushups(user_id, done_pushups_now)

    if dynamic_message != "": # not mid basically
        context.bot.send_message(chat_id=chat_id, text=dynamic_message)


def _set_status(user_id, done_pushups_now):
    # Retrieve previous pushup count and user's goal from the database
    previous_done_pushups = db.done_pushups(user_id)
    goal_pushups = db.get_pushup_goal(user_id)

    # Calculate total pushups done today
    total_done_pushups_today = previous_done_pushups + done_pushups_now

    # Determine user status
    if total_done_pushups_today >= goal_pushups:
        if previous_done_pushups >= goal_pushups:
            return "extra_set_today"
        elif total_done_pushups_today >= goal_pushups:
            return "last_set_today"
        else:
            return "mid_set_today"
    else:
        if previous_done_pushups == 0:
            return "first_set_today"
        else:
            return "mid_set_today"


def _get_dynamic_set_message(user_set_status, total_done_pushups_today, goal_pushups):
    remaining_pushups = max(goal_pushups - total_done_pushups_today, 0)

    if user_set_status == "extra_set_today":
        return "You're on fire today! Extra pushups, extra strength! 💪"
    elif user_set_status == "last_set_today":
        return "Goal reached! Amazing dedication! 🎉"
    elif user_set_status == "first_set_today":
        return "Great start! You're off to a strong start! 🚀"
    elif user_set_status == "mid_set_today":
        return ""# f"Halfway there! Only {remaining_pushups} pushups to go! 🌟"
    else:
        return "Keep pushing! Every rep gets you closer to your goal! 💯"


def _alternative_flow_message(user_id, chat_id, context, done_pushups_now):
    if done_pushups_now == 0:
        # Send message for no pushups detected
        context.bot.send_message(chat_id=chat_id, text="No pushups detected, make sure your whole body is within the video circle")
    else:
        # Send message for few pushups detected
        context.bot.send_message(chat_id=chat_id, text="Just a few pushups detected. Remember, lazy half-pushups are not counted!")


def on_bot_join(update: Update, context: CallbackContext):
    new_members = update.message.new_chat_members
    chat_id = update.message.chat_id

    for new_member in new_members:
        if new_member.is_bot and new_member.username == BOT_USERNAME:  # Replace with Jantee's actual username
            # Check if the group is new to the database
            if not db.check_group_registration(chat_id):
                db.add_new_group(chat_id, update.effective_chat.title)  # Add new group to the database
                context.bot.send_message(chat_id=chat_id, text="Hi, I'm Jantee! Ready to start your pushup challenge?")
            else:
                db.update_bot_is_in_group(chat_id, True)  # Update existing group in the database

def on_bot_leave(update: Update, context: CallbackContext):
    if not db.check_group_registration(update.effective_chat.id):
        return

    if update.message.left_chat_member.is_bot and update.message.left_chat_member.username == BOT_USERNAME:
        chat_id = update.message.chat_id
        db.update_bot_is_in_group(chat_id, False)  # Set bot_is_in_group to false in the database

def handle_user_group_update(update: Update, context: CallbackContext):
    message = update.message
    chat_id = message.chat_id

    # When a user is added to the group
    if message.new_chat_members:
        for new_member in message.new_chat_members:
            if not new_member.is_bot:
                user_id = new_member.id
                # Check if the user is registered in another group
                if not db.is_user_registered_in_another_group(user_id):
                    context.bot.send_message(chat_id=chat_id, text=f"Welcome, {new_member.full_name}! Ready for a pushup challenge?")
                else:
                    # Send dynamic guide message
                    dynamic_message = get_dynamic_guide_message_for_group(user_id)
                    context.bot.send_message(chat_id=chat_id, text=dynamic_message)

    # When a user leaves or is removed from the group
    if message.left_chat_member:
        left_member = message.left_chat_member
        if not left_member.is_bot:
            db.deregister_user_from_group(left_member.id, chat_id)  # Update user status in the database
            context.bot.send_message(chat_id=chat_id, text=f"{left_member.full_name} has left the group.")


def get_dynamic_guide_message_for_group(user_id):
    print("get_dynamic_guide_message_for_group")



def button_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()  # It's good practice to answer the query

    user_id = query.from_user.id
    chat_id = query.message.chat_id
    data = query.data

    if data == 'cancel_leave':
        # Cancel the operation
        query.edit_message_text(text="Operation cancelled.")
    elif data == 'register_here':
        # Register the user in the current group, replacing the previous group
        try:
            # db.deregister_user_from_all_groups(user_id)  # Deregister from previous group
            db.register_user_to_group(user_id, chat_id)  # Register in the new group
            query.edit_message_text(text="You've been successfully registered in this group.")
        except Exception as e:
            query.edit_message_text(text="There was an error in the registration process.")
            print(f"Error registering user {user_id} in group {chat_id}: {e}")