from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackQueryHandler
from bot.handlers import dm_handlers, command_handlers, group_handlers
def set_commands_handler(dp):
    command_handlers.load_quotes()

    dp.add_handler(CommandHandler('start', filters=Filters.chat_type.private, callback=command_handlers.dm_start_command))
    dp.add_handler(CommandHandler('start', filters=Filters.chat_type.group | Filters.chat_type.supergroup, callback=command_handlers.group_start_command))
    dp.add_handler(CallbackQueryHandler(group_handlers.button_callback_handler, pattern='^(cancel_leave|register_here)$'))
    #dp.add_handler(CommandHandler('test', command_handlers.test_command_handler))
    #dp.add_handler(CommandHandler('adjust', command_handlers.adjust_command_handler))

