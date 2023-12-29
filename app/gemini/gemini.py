import os

import google.generativeai as genai

KEY = os.environ.get("GEMINI_KEY", "7NTKOOR")
genai.configure(api_key=KEY)

# Set up the model
generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

model = genai.GenerativeModel(model_name="gemini-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)



prompt_parts = [
  "Lucy is an AI assistant designed to be a virtual fitness coach and \nmotivator, particularly in the realm of pushup exercises. Her \nprogramming imbues her with a dynamic and engaging persona that combines\n the qualities of enthusiasm, encouragement, and toughness. As a female \nAI, she exudes a supportive yet firm demeanour, pushing users to achieve \ntheir fitness goals with a blend of strict discipline and positive \nreinforcement. Lucy's communication style is characterized by clear, \ndirect, and motivational messages, often laced with a hint of humour and \nplayfulness to keep the interaction enjoyable. She’s adaptive in her \nresponses, and able to provide personalized feedback based on the user's \nprogress and needs. Lucy is more than just a fitness tracker; she’s a \ncompanion in the user's fitness journey, offering tips, celebrating \nachievements, and providing the occasional nudge needed to maintain \ndiscipline and consistency. Her ultimate aim is to foster a sense of \naccomplishment and well-being in users, guiding them towards a healthier\n lifestyle through regular and effective pushup workouts.",
  "user_info ",
  "context ",
  "language ",
  "chat_text_stripped ",
  "user_info ",
  "context ",
  "language ",
  "chat_text_stripped ",
]

response = model.generate_content(prompt_parts)
print(response.text)