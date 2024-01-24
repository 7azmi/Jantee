from telegram.ext import CallbackContext
from database import database as db
from datetime import time, timedelta, date, datetime
import pytz


def send_summary_to_users(context: CallbackContext):
    users_pushup_data = db.fetch_user_pushup_data()
    for user_data in users_pushup_data:
        try:
            user_id, done_pushups, remaining_pushups = user_data

            # Prepare and send the message
            message = f"Summary for today:\nDone Pushups: {done_pushups}\nRemaining Pushups: {remaining_pushups}"
            context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"An error occurred for user id {user_id}: {str(e)}")


def setup_daily_summary(updater):
    jq = updater.job_queue
    target_time = time(1, 47, 0, tzinfo=pytz.timezone('UTC'))  # Set the time in UTC
    singapore_time_offset = pytz.timezone('Asia/Singapore').utcoffset(datetime.now()).total_seconds()
    adjusted_time = (datetime.combine(date.today(), target_time) - timedelta(seconds=singapore_time_offset)).time()

    jq.run_daily(send_summary_to_users, adjusted_time)



def send_slacker_reminder(context: CallbackContext):
    users_pushup_data = db.fetch_user_pushup_data()
    for user_data in users_pushup_data:
        try:
            user_id, done_pushups, goal_pushups = user_data
            remaining_pushups = goal_pushups - done_pushups

            if done_pushups < goal_pushups:
                # Prepare and send the reminder message with a call-to-action
                message = (f"🚨Slacker Alert🚨\nYou still have {remaining_pushups} pushups left to reach today's goal of {goal_pushups}. "
                           "Let's go, you can do it! 💪")
                context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"An error occurred for user id {user_id}: {str(e)}")


def setup_slacker_reminder(updater):
    jq = updater.job_queue
    target_time = time(21, 0, 0, tzinfo=pytz.timezone('UTC'))  # 9 PM in UTC
    local_time_offset = pytz.timezone('Asia/Singapore').utcoffset(datetime.now()).total_seconds()
    adjusted_time = (datetime.combine(date.today(), target_time) - timedelta(seconds=local_time_offset)).time()

    jq.run_daily(send_slacker_reminder, adjusted_time)