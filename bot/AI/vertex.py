import os

import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/humadi/Github/Lucy/bot/AI/application_default_credentials.json"
vertexai.init(project="inbound-trainer-409815", location="asia-southeast1")
def generate():
    model = GenerativeModel("gemini-pro")
    responses = model.generate_content(
        """Say Hi""",
        generation_config={
            "max_output_tokens": 150,
            "temperature": 0.5,
            "top_p": 1
        },
        stream=True,
    )

    for response in responses:
        print(response.text, end="")


generate()