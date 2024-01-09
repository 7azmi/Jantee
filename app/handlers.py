import os
import requests
from cryptography.fernet import Fernet
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update, InputFile, \
    ReplyKeyboardMarkup, bot, ChatAction
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from gemini import gemini as gm
from database import database as db
from telegram import Bot, ChatMember

import app.data.data

fastapi_endpoint = os.environ.get('AI_API',
                                  'http://0.0.0.0:5000/count_pushups')  # 'http://dockerapi-production.up.railway.app/count_pushups')


def set_commands_handler(dp):
    dp.add_handler(CommandHandler('start', start_command))
    # dp.add_handler(CommandHandler("getpicture", get_profile_picture))


def load_fernet_key():
    key = os.environ.get('FERNET_KEY', 'OR9Hdu3NKcaT4PPHJni3NAepp61DL_SGeOmB2Eg7PT0=')  # change this later
    if not key:
        raise ValueError("Fernet key not found in environment variables")

    # Convert the key from string to bytes without altering it
    return key.encode()


def encrypt_message(message, key):
    f = Fernet(key)
    return f.encrypt(message.encode())


def group_videonote_receiver(update, context):
    user_id = update.message.from_user.id
    group_id = update.message.chat.id

    # Check if the group is registered in the database
    if not is_group_registered(group_id):
        # If group is not registered, instruct user to register it
        response = "This group isn't registered. Please register the group and set a daily pushup target and timezone."
        to_user(update, update.message.from_user.full_name, response)
        return

    # If group is registered, check user's group status
    user_group_status = check_user_group_status(user_id, group_id)

    if user_group_status == 'different_group':
        # User is in a different group, advise accordingly
        response = "You're registered in a different group. Please head there or leave that group before joining this one."
        to_user(update, update.message.from_user.full_name, response)
        return
    elif user_group_status == 'no_group':
        # User is not in a group, assign to this group
        assign_user_to_group(user_id, group_id)
        response = "You've been added to this group. Ready to start your pushup challenge?"
        to_user(update, update.message.from_user.full_name, response)
    elif user_group_status == 'same_group':
        # Proceed with calculating the videonote pushups
        update.message.reply_text("Counting your pushups...")

        pushup_count, remaining_pushups = count_pushups_from_videonote(update, context)

        if pushup_count is None or remaining_pushups is None:
            # An error occurred, the error message is already sent by count_pushups_from_videonote
            return

        if pushup_count > 0:
            update_user_pushup_record(user_id, group_id, pushup_count)
            if remaining_pushups > 0:
                # Feedback if user has started pushups of the day
                response = f"Great start! You've done {pushup_count} pushups. Only {remaining_pushups} to go!"
            else:
                # Feedback if user has finished daily pushups
                response = "Amazing work! You've completed your daily pushup goal. Take a rest, you've earned it!"
        else:
            # Feedback if no pushups were counted
            response = "Looks like there was an issue with your recording. Make sure your whole body is in the frame and try again!"

        to_user(update, update.message.from_user.full_name, response)
    else:
        # Handle other unexpected statuses
        response = "There was an unexpected issue with your group status. Please contact support."
        to_user(update, update.message.from_user.full_name, response)


# Helper functions used in the above function
def is_group_registered(group_id):
    db.is_group_registered(group_id)


def check_user_group_status(user_id, group_id):
    # Check the database for the user's group status
    # Placeholder for actual database logic
    db.check_user_group_status(user_id, group_id)


def assign_user_to_group(user_id, group_id):
    # Assign the user to the group in the database
    # Placeholder for actual database logic
    db.assign_user_to_group(user_id, group_id)


def count_pushups_from_videonote(update, context):
    try:
        key = load_fernet_key()

        video_file = update.message.video_note or update.message.video
        file_url = video_file.get_file().file_path  # This gets the public URL for the video file

        encrypted_url = encrypt_message(file_url, key)
        data = {'encrypted_video_url': encrypted_url.decode()}

        update.message.reply_text("Counting...")

        response = requests.post(fastapi_endpoint, json=data)

        if response.status_code == 200:
            pushup_count = response.json().get('pushup_count', 0)
            # Assuming 'daily_pushup_goal' is defined or retrieved from the database
            daily_pushup_goal = db.get_daily_pushup_goal(update.message.chat.id)
            remaining_pushups = daily_pushup_goal - pushup_count
            return pushup_count, remaining_pushups
        else:
            # Handle non-200 responses
            error_message = response.json().get('detail', "Error processing video.")
            raise Exception(error_message)

    except Exception as e:
        # If an error occurs, send an error feedback message
        error_feedback = str(e)
        context.bot.send_message(chat_id=update.effective_chat.id, text=error_feedback)
        return None, None  # Return None values if there was an error


def update_user_pushup_record(user_id, group_id, pushup_count):
    # Update the user's pushup record in the database
    # Placeholder for actual database update logic
    db.create_pushups(user_id, pushup_count, db.get_group_timezone(group_id))


# def to_user(context, user_info, response):
#     # AI response generator function, sends feedback to the user
#     # Placeholder for the response generator logic
#     pass

def dm_video_receiver(update, context):
    pass


# Function to process and send encrypted video
def dm_videonote_receiver(update, context):
    key = load_fernet_key()

    if update.message.video_note or update.message.video:
        if update.message.video_note:
            video_file = update.message.video_note.get_file()
        else:
            video_file = update.message.video.get_file()

        file_url = video_file.file_path  # This gets the public URL for the video file

        encrypted_url = encrypt_message(file_url, key)
        data = {'encrypted_video_url': encrypted_url.decode()}

        update.message.reply_text("Counting...")

        response = send_encrypted_video_to_fastapi(data, fastapi_endpoint)

        if response is not None:
            if response.status_code == 200:
                # first_time = "User records his first pushup videonote" if True else "User is re" # todo first time variable
                pushup_count = response.json().get('pushup_count')
                context.bot.send_chat_action(chat_id=update.message.from_user.id, action=ChatAction.TYPING)
                cntxt = "congratulate the user for doing his first pushups and tell him how many he's done, and instruct him to proceed to create a group with his friends and add you (Jantee) to the group" if pushup_count > 0 \
                    else "0 pushups means there is something wrong with the recording or positions or else. Tell the user to check the GIF instruction message above the chat and try shooting again"
                # text = f"Pushup count: {pushup_count}"
                to_user(update,
                        f"user full name: {update.message.from_user.full_name}, achieved pushups now: {pushup_count}",
                        cntxt)
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Error processing video.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Error sending video to the server.")
    # else:
    # context.bot.send_message(chat_id=update.effective_chat.id, text="Please send a video.")


# Function to send the encrypted video data to the FastAPI endpoint
def send_encrypted_video_to_fastapi(data, fastapi_endpoint):
    try:
        response = requests.post(fastapi_endpoint, data=data)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None


def group_text_receiver(update, context):
    print("group text recieved")

    # # This function will handle direct messages (DMs)
    # message = update.message.text
    # chat_type = update.message.chat.type
    # if chat_type == 'private':
    #     # Process DMs here
    #     pass
    #


# Define the available languages and their codes
languages = ['English', 'العربية', 'Chinese (中文)', 'Spanish (Español)', 'French (Français)', 'German (Deutsch)',
             'Japanese (日本語)', 'Russian (Русский)', 'Portuguese (Português)', 'Italian (Italiano)', 'Korean (한국어)',
             'Dutch (Nederlands)', 'Hindi (हिन्दी)']

# Create a mapping for hour numbers
utc_hour_timezone = {
    "-12": "UTC-12:00",
    "-11": "UTC-11:00",
    "-10": "UTC-10:00",
    "-09": "UTC-09:00",
    "-08": "UTC-08:00",
    "-07": "UTC-07:00",
    "-06": "UTC-06:00",
    "-05": "UTC-05:00",
    "-04": "UTC-04:00",
    "-03": "UTC-03:00",
    "-02": "UTC-02:00",
    "-01": "UTC-01:00",
    "+00": "UTC+00:00",
    "+01": "UTC+01:00",
    "+02": "UTC+02:00",
    "+03": "UTC+03:00",
    "+04": "UTC+04:00",
    "+05": "UTC+05:00",
    "+06": "UTC+06:00",
    "+07": "UTC+07:00",
    "+08": "UTC+08:00",
    "+09": "UTC+09:00",
    "+10": "UTC+10:00",
    "+11": "UTC+11:00",
    "+12": "UTC+12:00",
    "+13": "UTC+13:00",
    "+14": "UTC+14:00"
}
pushup_options = {
    "15": "15 Pushups - Great for beginners!",
    "25": "25 Pushups - Good for getting started!",
    "50": "50 Pushups - A solid daily goal.",
    "75": "75 Pushups - For the more ambitious!",
    "100": "100 Pushups - A challenging target.",
    "150": "150 Pushups - For advanced fitness levels.",
    "200": "200 Pushups - For true pushup masters!"
}


# Define a callback function to handle the button presses
# def timezone_callback(update: Update, context):
#     query = update.callback_query
#     data = query.data
#     print(data)
#
#     # Get the actual timezone value from the mapping
#     selected_timezone = utc_hour_timezone.get(data, "Unknown")
#
#     # Handle the selected timezone as needed
#     # For example, send a message with the selected timezone
#     query.answer(f"You selected {selected_timezone}")


def handle_timezone_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    selected_timezone_key = query.data
    #print(selected_timezone_key)
    selected_timezone = utc_hour_timezone[selected_timezone_key]
    group_name = query.message.chat.title if query.message.chat.type in ['group', 'supergroup'] else "Unknown Group"
    # Process the selected timezone (e.g., save to the database)
    db.add_new_group(update.message.chat_id, 15, "No punishment", selected_timezone, group_name)
    query.edit_message_text(text=f"Timezone selected: {selected_timezone}")


# Function to process language selection and update user language
def process_language_selection(update, context, languages):
    user_id = update.message.from_user.id
    selected_language = next((lang for lang in languages if lang == update.message.text), None)

    if selected_language:
        context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

        if db.check_user_exists(user_id):
            previous_language = db.get_user_language(user_id)
            db.update_user_language(user_id, selected_language)
            current_language = db.get_user_language(user_id)

            return previous_language, current_language
        else:
            db.add_new_user(user_id)
            return None, selected_language

    return None, None


# Function to send a reply message
def send_language_reply_message(update, context, text):
    reply_markup = ReplyKeyboardRemove()
    update.message.reply_text(text=text, reply_markup=reply_markup)


# Function to handle DM text messages
def dm_text_receiver(update, context):
    previous_language, current_language = process_language_selection(update, context, languages)

    if previous_language is not None:
        text = gm.generate_chat_text(
            f"Previous language: {previous_language}\nNew selected language: {current_language}",
            "User has made an action to change language, give him a feedback text of his decision",
            current_language
        )
    else:
        text = gm.generate_chat_text(
            "Full name: " + update.message.from_user.full_name,
            "Say hi to the new User",
            current_language
        )

    send_language_reply_message(update, context, text)


def chat_member_update(update: Update, context: CallbackContext):
    # Determine the type of update
    if update.my_chat_member:
        chat_member_update = update.my_chat_member
    elif update.chat_member:
        chat_member_update = update.chat_member
    else:
        print("Received an unknown type of chat member update.")  # this thing doesn't work
        return

    # Check if old and new chat member data is available
    if chat_member_update.old_chat_member and chat_member_update.new_chat_member:
        old_status = chat_member_update.old_chat_member.status
        new_status = chat_member_update.new_chat_member.status

        # Check if the update is about the bot itself
        if chat_member_update.new_chat_member.user.id == context.bot.id:
            # Bot added to the group
            if new_status == 'member' and old_status != 'member':
                print("Bot was added to the group.")  # It works here
                # here I want you
            # Bot kicked out or left the group
            elif old_status == 'member' and new_status != 'member':
                print(new_status)
                if new_status == 'kicked':
                    print("Bot was kicked out of the group.")
                else:
                    print("Bot left the group.")  # what's gonna happen


# def check_rejoin(update: Update, context: CallbackContext):
#     for member in update.message.new_chat_members:
#         if was_member_before(member.id, update.message.chat.id):  # Implement this function based on your data storage
#             update.message.reply_text(f'Welcome back {member.full_name}!')
#         else:
#             update.message.reply_text(f'Welcome {member.full_name}!')
#
#
# def was_member_before(user_id, group_id):
#     # Implement this function to check if the user was a member before
#     # This could be a database query or file lookup
#     # Return True if the user was a former member, False otherwise
#     return True

def check_rejoin(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        db.add_new_user(member.id, update.message.chat.id)
        update.message.reply_text(text=f"Welcome {member.full_name}!")


def user_removed_from_group(update: Update, context: CallbackContext):
    if update.message.left_chat_member is not None:
        db.remove_user_from_group(update.message.left_chat_member.id)
        # update.message.reply_text(f'Goodbye {update.message.left_chat_member.full_name}!')


def start_command(update, context):
    send_timezone_buttons(update, context)
    return
    # Create a list of language buttons, each in its own row
    keyboard = [[language] for language in languages]

    # Convert the list to a ReplyKeyboardMarkup
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    # Send the message with language options
    update.message.reply_text("🌐👇", reply_markup=reply_markup)

    # update.message.reply_text(app.data.data.get_message('start_new_user'))


# def get_profile_picture(update: Update, context: CallbackContext):
#     print("hello?")
#     user_id = update.message.from_user.id  # Get user's Telegram ID
#     try:
#         # Get user profile pictures
#         profile_pictures = context.bot.get_user_profile_photos(user_id)
#         if profile_pictures.photos:
#             # Take the first photo (most recent profile picture)
#             photo = profile_pictures.photos[0][-1]
#             # Get file path
#             file = context.bot.get_file(photo.file_id)
#             # Download and save the photo, or send it directly
#             file.download('user_profile_picture.jpg')
#             update.message.reply_text("Profile picture saved.")
#         else:
#             update.message.reply_text("No profile picture found.")
#     except Exception as e:
#         print(e)
#         update.message.reply_text("Error in getting profile picture.")

def get_profile_picture(update: Update, context: CallbackContext):
    get_profile_picture2()


def get_profile_picture2():
    print("hi")
    user_id = 1823406139

    # profile_pictures = get_user_profile_photos(user_id)
    # if profile_pictures.photos:
    #     photo = profile_pictures.photos[0][-1]
    #     file = bot.Bot.get_file(photo.file_id)
    #     file.download('user_profile_picture.jpg')
    #     print('Profile picture saved.')
    # else:
    #     print('No profile picture found.')


# message to user
def to_user(update: Update, user_info, context):
    user_id = update.message.from_user.id
    update.message.reply_text(text=gm.generate_chat_text(user_info, context, db.get_user_language(user_id)))


# def send_timezone_keyboard(chat_id, context):
#     keyboard = [[InlineKeyboardButton(utc_hour_timezone[key], callback_data=f"timezone:{key}") for key in
#                  utc_hour_timezone.keys()]]
#
#     rows = []
#     for i in range(0, len(keyboard[0]), 3):
#         row = keyboard[0][i:i + 3]
#         rows.append(row)
#
#     reply_markup = InlineKeyboardMarkup(rows)
#     context.bot.send_message(chat_id=chat_id, text="Please select your timezone:", reply_markup=reply_markup)

def send_timezone_buttons(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    # Create a list of InlineKeyboardButton
    buttons = [InlineKeyboardButton(text=zone, callback_data=key) for key, zone in utc_hour_timezone.items()]

    # Organize buttons into rows for the keyboard
    keyboard = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]  # Adjust the range as needed for layout

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text="Select your timezone:", reply_markup=reply_markup)

# def handle_timezone_selection(update, context):
#     query = update.callback_query
#     selected_timezone = query.data.split(':')[1]
#     # Save the selected timezone to the database
#     # save_timezone_to_database(update.effective_chat.id, selected_timezone)
#     query.edit_message_text(text=f"Timezone selected: {selected_timezone}")
#     # Proceed to ask for daily pushup goal
#     # send_pushup_count_keyboard(update.effective_chat.id, context)


def is_user_group_admin(bot: Bot, user_id: int, chat_id: int):
    """Check if the user is an admin in the given group."""
    try:
        chat_member: ChatMember = bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ['administrator', 'creator']
    except:
        return False


def group_settings_handler(update: Update, context: CallbackContext):
    # Ensure this is a group chat
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the sender is an admin
    if not is_user_group_admin(context.bot, user_id, chat_id):
        update.message.reply_text("Only admins can do whatever they want hehe")
        return  # Ignore messages from non-admins

    text = update.message.text.strip()
    is_registered = check_group_registration(chat_id)

    # Process the message for timezone or pushup count
    if not is_registered:
        if text in pushup_options:
            # Handle pushup count setting
            db.set_pushup_count(chat_id, int(text))
            update.message.reply_text(
                f"Pushup count set to {text}. {pushup_options[text]} Now, please set the timezone.")
        elif text in utc_timezones_countries:
            # Handle timezone setting
            db.set_group_timezone(chat_id, text)
            update.message.reply_text(f"Timezone set to {text}. Please set the daily pushup count.")
        else:
            update.message.reply_text("Please set the daily pushup count or timezone.")


def check_group_registration(chat_id):
    db.check_user_exists()
