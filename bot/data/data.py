import json
import random



# Load the messages from a JSON file
def load_messages(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

# Example usage
messages = load_messages('bot/data/conversations.json')

# Example function to get a message
def get_message(situation, order='random', language = 'en'):
    """
    Retrieves a message for a given language and situation.
    By default, it picks randomly unless specified to use 'sequential' order.
    """
    language_messages = messages.get(language, {})
    situation_messages = language_messages.get(situation, ["Oops, I don't have a message for this situation yet!"])

    if order == 'random':
        return random.choice(situation_messages)
    elif order == 'sequential':
        # Implement sequential logic with state tracking as needed
        return situation_messages[0]  # Placeholder for the first message.



# Example usage
#print(get_message( 'start_new_user'))  # Random English message for a new user
