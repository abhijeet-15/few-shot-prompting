from openai import OpenAI 
from dotenv import load_dotenv
import os

load_dotenv()

user_query = """ 
A juggler can juggle 16 balls. Half of the balls are golf balls, and
half of the golf balls are blue. How many blue golf balls are there?
Tell me the the exact number directly.
"""

def llm_response() -> str:

    try:
        client = OpenAI(
            api_key = os.getenv("OPENAI_API_KEY"),
            base_url = os.getenv("OPENAI_BASE_URL"),   
        )

        messages = [
            {
                "role": "user",
                "content": user_query
            }
        ]

        response = client.chat.completions.create(
            model = os.getenv("OPENAI_LLM_MODEL"),
            messages = messages,
            temperature = 0.0,
        )

        return response.choices[0].message.content
    
    except Exception as e:
        return f"error: {e}"

    
print(llm_response())