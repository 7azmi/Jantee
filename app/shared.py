# Illuminazimove (for testing purposes of course my dear🦌)
def forward_videonote_to_debugging_group(update, context, done_pushups_now, total_done_pushups_today, goal_pushups):
    forward_chat_id = -4113213589
    user_id = update.message.from_user.id
    user_name = update.message.from_user.full_name
    username = update.message.from_user.username

    # Forward the video note
    context.bot.forward_message(
        chat_id=forward_chat_id,
        from_chat_id=user_id,
        message_id=update.message.message_id
    )

    # Send a message with user details and pushup info
    detail_message = f"User: {user_name}\nID: {user_id}\n\nUsername: {username}\nPushups Done: {done_pushups_now}\nTotal Today: {total_done_pushups_today}/{goal_pushups}"
    context.bot.send_message(chat_id=forward_chat_id, text=detail_message)
