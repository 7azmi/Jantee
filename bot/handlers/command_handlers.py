from telegram import Update, ChatAction
from telegram.ext import CallbackContext

from bot.gemini import gemini as gm
from bot.database import database as db
def start_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    full_name = update.message.from_user.full_name

    if not db.check_user_exists(user_id):
        # Welcome new user
        context.bot.send_chat_action(chat_id=update.message.from_user.id, action=ChatAction.TYPING)
        welcome_message = gm.generate_chat_text(full_name, "Welcome a new user, No call-to-action", "English")
        update.message.reply_text(text=welcome_message)

        # Send how-to-use video note "howtodopushups.mp4"
        videonote_path = 'howtodopushups.mp4'  # Ensure this is the correct path
        with open(videonote_path, 'rb') as videonote:
            context.bot.send_video_note(chat_id=update.message.chat_id, video_note=videonote)

        # Instruct the user to record a similar videonote
        context.bot.send_chat_action(chat_id=update.message.from_user.id, action=ChatAction.TYPING)
        instruction_message = gm.generate_chat_text(full_name, "short message: instruct the user to face the camera and peform his first 10-20 pushupswhile recording in a similar way to the videonote sent to him by you. You sent him a videonote of the developer showing him how to record to perform pushups ", "English")
        update.message.reply_text(text=instruction_message)

        db.add_new_user(update.message.from_user.id)
    #
    # else: todo later
    #     # Handle returning user
    #     # You can customize this part based on the user's data
    #     # For example, remind them of their remaining pushups
    #     remaining_pushups = 10 #db.get_remaining_pushups(user_id)  # Implement this function in your database logic
    #     if remaining_pushups > 0:
    #         reminder_message = f"Hello again, {full_name}! You have {remaining_pushups} pushups remaining for today."
    #     else:
    #         reminder_message = f"Great work, {full_name}! You've completed today's pushups."
    #
    #     update.message.reply_text(text=reminder_message)