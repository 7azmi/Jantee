import threading
import time

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
    else:
        fitness_tip_or_quote = gm.generate_chat_text(full_name,
                                                     "Remember that the key to any good fitness regime is to create consistency – keep up your push-up training.",
                                                     "English")
        context.bot.send_message(chat_id=update.message.chat_id, text=fitness_tip_or_quote)

def test_command_handler(update: Update, context: CallbackContext):
    # Reply immediately to acknowledge the command
    update.message.reply_text("Test started, please wait...")

    # Start the process in a separate thread
    threading.Thread(target=wait_and_respond, args=(update, context)).start()

def wait_and_respond(update: Update, context: CallbackContext):
    # Wait for 15 seconds
    time.sleep(15)

    # Send the feedback message
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi")

# Add the handler for the '/test' command to the dispatcher
