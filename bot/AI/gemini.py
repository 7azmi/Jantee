import os
import google.generativeai as genai
from itertools import cycle
import concurrent.futures


# Part 1: API Key Management
class APIKeyManager:
    def __init__(self, env_variable_names):
        self.keys = [os.environ.get(name) for name in env_variable_names]
        self.key_cycle = cycle(self.keys)

    def get_next_key(self):
        return next(self.key_cycle)


# Part 2: Model Configuration and Initialization
class GeminiAI:
    def __init__(self, api_keys):
        self.models = [self.create_model(api_key) for api_key in api_keys]
        self.model_cycle = cycle(self.models)

    def create_model(self, api_key):
        genai.configure(api_key=os.environ.get(api_key))
        return genai.GenerativeModel(model_name="gemini-pro",
                                     generation_config=self.get_generation_config(),
                                     safety_settings=self.get_safety_settings())

    @staticmethod
    def get_generation_config():
        return {
            "temperature": 0.5,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 1000,
        }

    @staticmethod
    def get_safety_settings():
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]

    def generate_chat_text(self, user_info, context, language="English"):
        model = next(self.model_cycle)  # Get the next model in the cycle
        prompt = self.generate_prompt(user_info, context, language)
        try:
            response = model.generate_content(prompt)
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'result') and hasattr(response.result, 'parts'):
                return ''.join(part.text for part in response.result.parts)
            else:
                return "Received an unexpected response format from the model."
        except Exception as error:
            return f"An error occurred when generating chat text: {str(error)}"

    @staticmethod
    def generate_prompt(user_info, context, language):
        prompt = [
            "Jantee is a male AI fitness coach with a bold, unorthodox style. Unlike typical supportive AI, he uses tough-love and vulgar language for motivation. Known for his brash, no-nonsense attitude, Jantee's communication is direct, humorous, and slightly sarcastic. He focuses on pushup exercises, driving users with strict discipline and unconventional methods. Jantee tailors responses to immediate actions, avoiding extended chat histories. His approach is bluntly honest, aiming to build resilience and determination in users, making their fitness journey rigorous yet engaging with a unique blend of grit and humor.",
            f"user_info {user_info}",
            f"context {context}",
            f"language {language}",
            "strip_chat_text",
        ]
        return prompt


# Parallel execution function
def generate_parallel_chat_texts(gemini_ai, user_info, context, language, n):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        args = [(user_info, context, language) for _ in range(n)]
        results = executor.map(lambda p: gemini_ai.generate_chat_text(*p), args)
        return list(results)


# Usage
api_keys = ["GEMINI_KEY1", "GEMINI_KEY2", "GEMINI_KEY3", "GEMINI_KEY4"]
gemini_ai = GeminiAI(api_keys)

user_info = {"name": "John Doe"}
context = "User did 10 pushups (generate short message)"
language = "English"

n = 5  # Number of requests you want to make
responses = []

for _ in range(n):
    response = gemini_ai.generate_chat_text(user_info, context, language)
    print(response)
    #responses.append(response
#
# for response in responses:
#     print(response)
# import os
#
# import google.generativeai as genai
#
# KEY = os.environ.get("GEMINI_KEY", "7NTKOOR")
#
#
# def configure_generative_model(api_key):
#     genai.configure(api_key=api_key)
#
#
# configure_generative_model(KEY)
#
# # Set up the model
# generation_config = {
#     "temperature": 0.9,
#     "top_p": 1,
#     "top_k": 1,
#     "max_output_tokens": 2048,
# }
#
# safety_settings = [
#   {
#     "category": "HARM_CATEGORY_HARASSMENT",
#     "threshold": "BLOCK_ONLY_HIGH"
#   },
#   {
#     "category": "HARM_CATEGORY_HATE_SPEECH",
#     "threshold": "BLOCK_ONLY_HIGH"
#   },
#   {
#     "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
#     "threshold": "BLOCK_MEDIUM_AND_ABOVE"
#   },
#   {
#     "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
#     "threshold": "BLOCK_ONLY_HIGH"
#   },
# ]
#
# model = genai.GenerativeModel(model_name="gemini-pro",
#                               generation_config=generation_config,
#                               safety_settings=safety_settings)
#
# #"Lucy is an AI assistant designed to be a virtual fitness coach and \nmotivator, particularly in the realm of pushup exercises. Her \nprogramming imbues her with a dynamic and engaging persona that combines\n the qualities of enthusiasm, encouragement, and toughness. As a female \nAI, she exudes a supportive yet firm demeanour, pushing users to achieve \ntheir fitness goals with a blend of strict discipline and positive \nreinforcement. Lucy's communication style is characterized by clear, \ndirect, and motivational messages, often laced with a hint of humour and \nplayfulness to keep the interaction enjoyable. She’s adaptive in her \nresponses, and able to provide personalized feedback based on the user's \nprogress and needs. Lucy is more than just a fitness tracker; she’s a \ncompanion in the user's fitness journey, offering tips, celebrating \nachievements, and providing the occasional nudge needed to maintain \ndiscipline and consistency. Her ultimate aim is to foster a sense of \naccomplishment and well-being in users, guiding them towards a healthier\n lifestyle through regular and effective pushup workouts.",
#
# def generate_prompt(user_info, context, language):
#     prompt = [
#         "Jantee is a unique Male AI assistant, designed to be a virtual fitness coach with a twist. Unlike the typical supportive and encouraging personas, Jantee employs a bold and unorthodox approach, often using vulgar language and tough-love tactics to motivate users in their pushup exercises. This AI has a distinct personality, characterized by its brash, no-nonsense attitude. Jantee's communication style is direct and unfiltered, often laced with humour and a hint of sarcasm, aimed at pushing users out of their comfort zone.\n\nAs a fitness coach, Jantee's main goal is to drive users towards achieving their pushup targets, using a blend of strict discipline and unconventional motivational techniques. The AI's responses are tailored to the user's actions, but they maintain a consistent tone of blunt honesty and tough motivation. Jantee's interactions are focused on the present; it responds to immediate actions without maintaining a chat history. For example, if a user changes the language settings, Jantee will acknowledge the change but won't invite further queries or discussions. This approach makes Jantee more than just a fitness tracker—it's a challenging yet effective companion in the user's fitness journey, pushing them towards their goals with a unique blend of grit and humor. Jantee's ultimate aim is to foster resilience and determination in users, guiding them towards a healthier lifestyle through rigorous and effective pushup workouts, all while keeping the interaction lively and engaging."
#         "\n\nEXAMPLES: Listen up, team! Jantee's in the house, and I'm not here to babysit. Let's get those pushups rolling, or get ready for some real talk! Nice try, keyboard warrior. Show me the sweat and effort. Send a video note or don't bother at all! It's pushup time! Don't make me come through this screen to get you moving. Drop and give me 20, now! Well, look at you go! Not bad... for a beginner. Keep it up, or I'll have to roast you harder! What's this? You call that effort? I've seen better pushups from a pancake. Step it up tomorrow, or I'll be the nightmare in your fitness dreams! Strike one! Two more and you earn a one-way ticket to Lazytown. Let's avoid that, shall we? Today's a new day to prove yourself. Yesterday's pushups don't count today. Show me what you've got! Targets updated, and the clock's ticking. Better not slack off, or you'll hear from me! Switching to French, huh? Les push-ups sont universels. Now, no more chitchat—back to work!",
#         f"user_info {user_info}",
#         f"context {context}",
#         f"language {language}",
#         "strip_chat_text",
#     ]
#     return prompt
#
#
# def generate_chat_text(user_info, context, language="English"):
#     prompt = generate_prompt(user_info, context, language)
#
#     try:
#         response = model.generate_content(prompt)
#
#         # Check if the response is a simple text response
#         if hasattr(response, 'text'):
#             return response.text
#         # Handle multi-part responses
#         elif hasattr(response, 'result') and hasattr(response.result, 'parts'):
#             return ''.join(part.text for part in response.result.parts)
#         else:
#             return "Received an unexpected response format from the model."
#     except Exception as error:
#         return f"An error occurred when generating chat text: {str(error)}"


#
# # Example usage:
# user_info = "Name: Ahmed"
# context = "short response: user missed his daily pushups today"
# language = "English"
#
#
# import asyncio
#
# async def generate_chat_text(user_info, context, language):
#     prompt_parts = [
#         "Say hi",
#     ]
#     response = await model.generate_content_async(prompt_parts)  # Assuming this is an async call
#     return response.text
#
# async def main():
#     user_info = "Name: Ahmed"
#     context = "short response: user missed his daily pushups today"
#     language = "English"
#
#     n = 20 # Number of parallel executions
#
#     # Creating tasks for parallel execution
#     tasks = [generate_chat_text(user_info, context, language) for _ in range(n)]
#     results = await asyncio.gather(*tasks)
#
#     # Processing results
#     for result in results:
#         print(result)
#
# # Run the main function
# asyncio.run(main())
