from openai import OpenAI 
from dotenv import load_dotenv
import os

load_dotenv()

system_prompt = """
You analyse sentiments and respond only in JSON using this structure
{
    "sentiment": "positive|negative|neutral",
    "confidence": 0.0-1.0
}
"""

examples = [

    (
        "I enjoyed the songs yesterday",
        """{
            "sentiment": "positive",
            "confidence": 0.80
        }"""
    ),
    (
        "I did not like the episode. Pretty boring",
        """{
            "sentiment": "negative",
            "confidence": 0.90
        }"""
    ),
    (
        "I spoke to the salesman and he told me about the offers, pretty much expected that",
        """{
            "sentiment": "neutral",
            "confidence": 0.75
        }"""
    ),
]

user_query = "I have ordered an ultra wide monitor for day to day work and it looks super nice in specs.Can't wait!!"


def llm_response():

    client = OpenAI(
        api_key = os.getenv("GROQ_API_KEY"),
        base_url = os.getenv("GROQ_BASE_URL")
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    for example_input, example_output in examples:
        messages.append(
            {
                "role": "user",
                "content": example_input

            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": example_output
            }
        )
    
    messages.append(
        {
            "role": "user",
            "content": user_query
        }
    )

    result = client.chat.completions.create(
        model = os.getenv("GROQ_LLM_MODEL"),
        messages = messages,
        response_format = {"type": "json_object"},
        temperature = 0.0
    )
    
    return result.choices[0].message.content

print(llm_response())
