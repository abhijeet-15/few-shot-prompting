from openai import OpenAI 
from dotenv import load_dotenv
from dataclasses import dataclass
from pydantic import BaseModel
from prompts import SYSTEM_PROMPT 
from typing import Literal
import json
import os


load_dotenv()

@dataclass(frozen = True)
class Provider:
    name: str
    env_var: str
    is_free: bool
    model: str
    base_url: str | None

PROVIDERS = [
    Provider("OpenAi", "OPENAI_API_KEY", False, "OPENAI_LLM_MODEL", "OPENAI_BASE_URL"),
    Provider("GrokAi", "GROQ_API_KEY", True, "GROQ_LLM_MODEL", "GROQ_BASE_URL")
]

def select_provider() -> Provider:
    for provider in PROVIDERS:
        if os.getenv(provider.env_var):
            return provider
    expected = ", ".join(p.env_var for p in PROVIDERS)
    raise RuntimeError(f"No provider key set. Add one of {expected} to your .env file")

def build_client(provider: Provider):
    api_key = os.getenv(provider.env_var)
    base_url = os.getenv(provider.base_url)
    return OpenAI(
        api_key = api_key,
        base_url = base_url
    )

def have_any_key() -> bool:
    return any(os.getenv(provider.env_var) for provider in PROVIDERS)

print("Found a key." if have_any_key() else "No provider key found")

def llm_reply(prompt: str) -> str:
    provider = select_provider()
    client = build_client(provider)
    response = client.chat.completions.create(
        model = os.getenv(provider.model),
        max_completion_tokens = 2048,
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content

prompt = "Who holds the record for maximum centuries in T20 international?"

# try:
#     print(llm_reply(prompt))
# except Exception as e:
#     print(f"Error: {e}")

class COTStep(BaseModel):
    """ A step in the chain of thought process """
    step_type: Literal["THINKING", "FINAL_OUTPUT"] #THINKING is planning
    content: str


def parse_cot_step(raw_reply: str) -> COTStep | str:
    """ Parse a raw reply into a chain of thought cot """
    try:
        parsed = json.loads(raw_reply)
        return COTStep(**parsed)
    except Exception as e:
        return f"Error: {e}"

def llm_json_reply(messages: list[dict]) -> str:
    provider = select_provider()
    client = build_client(provider)

    kwargs: dict = {
        "model": os.getenv(provider.model),
        "max_tokens" : 2048,
        "messages" : messages,
        #"response_format": "json_object"
    }

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


class COTAssistant():
    """ An assistant that solves user queries using chain of thoughts """
    
    def __init__(self):
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.MAX_STEPS = 15 
    
    def run(self, user_query: str) -> str:
        self.messages.append({"role": "user", "content": user_query})
        print(f"👉{user_query}\n")

        for _ in range(self.MAX_STEPS):
            raw_reply = llm_json_reply(self.messages) # this will make an LLM call and return a string of JSON type
            parsed = parse_cot_step(raw_reply) # convert the raw json string to a COT object

            if isinstance(parsed, COTStep): # check if a valid COT object

                self.messages.append({"role": "assistant", "content": raw_reply})       
                if parsed.step_type == "THINKING":
                    print(f"💡 {parsed.content}\n")
                    continue
                
                if parsed.step_type == "FINAL_OUTPUT":
                    print(f"🎯 {parsed.content}\n")
                    return parsed.content
            
            else:
                print(f"❌ error: {parsed.content}")
                return parsed
        
        return f"Failed to arrive at answer in {self.MAX_STEPS} steps"

assistant = COTAssistant()
QUESTION = """
    Elise is baking a massive multi-tiered cake. The bottom tier requires 3 times as much batter as the middle tier. The middle tier requires 2 times as much batter as the top tier. The top tier requires exactly 4 cups of batter. 

To make the batter, every single cup requires 2 eggs and 1.5 cups of flour. 

While baking, Elise completely ruins her first attempt at the bottom tier and has to throw it away and re-bake that specific tier from scratch. She successfully bakes the top and middle tiers on her first try. 

What is the absolute total sum of the number of eggs AND the cups of flour she used for all the batter she made (including the ruined tier)?
""".strip()

assistant.run(QUESTION)