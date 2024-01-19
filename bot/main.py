import logging
import logging.config
import os
import sys
from telegram.ext import Filters, MessageHandler, Updater, ChatMemberHandler, CallbackQueryHandler, CallbackContext

import bot
from handlers import dm_handlers
from datetime import time
import pytz
import bot.bot_clock as bc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from handlers.handlers import *
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv("bot/.env")


def error(update, context):
    """Log Errors caused by Updates."""

    logging.warning('Update "%s" ', update)
    logging.exception(context.error)





def main():
    updater = Updater(DefaultConfig.TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # command handlers
    set_commands_handler(dp)

    #dp.add_handler(MessageHandler(Filters.video, dm_handlers.handle_video_dm))

    dp.add_handler(MessageHandler(Filters.video, dm_handlers.handle_video_dm))
    dp.add_handler(MessageHandler(Filters.video_note, dm_handlers.handle_videonote_dm))
    dp.add_handler(CallbackQueryHandler(dm_handlers.handle_pushup_goal_selection, pattern='^\d+$'))


    bc.setup_daily_summary(updater)

    # Use the custom filter in the MessageHandler
    # dp.add_handler(MessageHandler(FilterStartsWithUTC.starts_with_utc, handle_timezone_selection))
    # Create the CallbackQueryHandler with the custom callback function and filter

    # Add the handler to your dispatcher
    # # dp.add_handler(CallbackQueryHandler(timezone_callback, pattern='^timezone:.*$'))
    # dp.add_handler(CallbackQueryHandler(handle_timezone_selection, pattern=r'^[+\-]\d{2}$'))
    #
    # dp.add_handler(MessageHandler(Filters.text & ~Filters.command, group_settings_handler))
    #
    # # Add the message handler for group messages
    # dp.add_handler(MessageHandler(Filters.text & (Filters.chat_type.group | Filters.chat_type.supergroup),
    #                               group_text_receiver))
    #
    # # Add the message handler for DMs
    # dp.add_handler(MessageHandler(Filters.text & Filters.chat_type.private, dm_text_receiver))
    #
    # # dp.add_handler(MessageHandler(Filters.chat_type.private & Filters.video, dm_video_receiver))
    # dp.add_handler(
    #     MessageHandler(Filters.chat_type.private & (Filters.video_note | Filters.video), dm_videonote_receiver))

    ## dp.add_handler(MessageHandler(Filters.chat_type.private & Filters.video, group_video_receiver))
    # dp.add_handler(MessageHandler(Filters.chat_type.private & Filters.video_note, group_videonote_receiver))

    # dp.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.ANY_CHAT_MEMBER))

    # dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    # dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, check_rejoin))
    ## dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, user_added_to_group))
    # dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, user_removed_from_group))

    # dp.add_handler(CallbackQueryHandler(handle_timezone_selection, pattern=r'^timezone:'))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    if DefaultConfig.MODE == "webhook":
        updater.start_webhook(
            listen="0.0.0.0",
            port=int(DefaultConfig.PORT),
            url_path=DefaultConfig.TELEGRAM_TOKEN,
            webhook_url=DefaultConfig.WEBHOOK_URL + '/' + DefaultConfig.TELEGRAM_TOKEN
        )

        logging.info(f"Start webhook mode on port {DefaultConfig.PORT}")
    else:
        updater.start_polling()
        logging.info(f"Start polling mode")

    updater.idle()


class DefaultConfig:
    PORT = int(os.environ.get("PORT", 5000))
    TELEGRAM_TOKEN = os.environ.get("API_TELEGRAM", "")
    MODE = os.environ.get("MODE", "webhook")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://427e-219-92-138-126.ngrok-free.app")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

    @staticmethod
    def init_logging():
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=DefaultConfig.LOG_LEVEL,
        )


if __name__ == "__main__":
    # Enable logging
    DefaultConfig.init_logging()
    logging.info(f"PORT: {DefaultConfig.PORT}")
    main()
    # API.run_API()
