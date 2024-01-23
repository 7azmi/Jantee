import os
import vertexai
from vertexai.preview.language_models import TextGenerationModel

import vertexai
from vertexai.preview.language_models import TextGenerationModel

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/humadi/Github/Lucy/bot/AI/application_default_credentials.json"

#vertexai.init(project="inbound-trainer-409815", location="asia-southeast1")

vertexai.init(project="inbound-trainer-409815", location="us-central1")
parameters = {
    "max_output_tokens": 565,
    "temperature": 0.5,
    "top_p": 1
}
model = TextGenerationModel("gemini-pro")
response = model.predict(
    """Jantee is a male AI fitness coach with a bold, unorthodox style. Unlike typical supportive AI, he uses tough-love and vulgar language for motivation. Known for his brash, no-nonsense attitude, Jantee\'s communication is direct, humorous, and slightly sarcastic. He focuses on pushup exercises, driving users with strict discipline and unconventional methods. Jantee tailors responses to immediate actions, avoiding extended chat histories. His approach is bluntly honest, aiming to build resilience and determination in users, making their fitness journey rigorous yet engaging with a unique blend of grit and humor.

user_info: Ahmed
context: Say hi to the new user
chat_response:
""",
    **parameters
)
print(f"Response from Model: {response.text}")
# async def execute_in_parallel(n):
#     with ThreadPoolExecutor() as executor:
#         loop = asyncio.get_event_loop()
#         tasks = [loop.run_in_executor(executor, generate) for _ in range(n)]
#         await asyncio.gather(*tasks)
#
# # Run 5 iterations of the 'generate' function in parallel
# asyncio.run(execute_in_parallel(50))