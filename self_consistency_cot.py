from openai import OpenAI
from dotenv import load_dotenv
from dataclasses import dataclass
import os
from typing import Literal
from pydantic import BaseModel
from prompts import SYSTEM_PROMPT
import json
import re
import collections

load_dotenv()

@dataclass
class Provider:
    name: str
    env_var: str
    is_free: bool
    model: str
    base_url: str | None

PROVIDERS = [
    Provider("OpenAI", "OPENAI_API_KEY", False, "OPENAI_LLM_MODEL", "OPENAI_BASE_URL"),
    Provider("GroqAI", "GROQ_API_KEY", False, "GROQ_LLM_MODEL", "GROQ_BASE_URL"),
]

def select_provider() -> Provider:
    for provider in PROVIDERS:
        if os.getenv(provider.env_var):
            return provider 

    expected = (", ").join(p.env_var for p in PROVIDERS)
    raise RuntimeError(f"No provider key set. Add one of {expected} to your environment variables")


def build_client(provider: Provider):
    api_key = os.getenv(provider.env_var)
    base_url = os.getenv(provider.base_url)
    return OpenAI(
        api_key = api_key,
        base_url = base_url
    )


def have_any_key() -> bool:
    return any(os.getenv(provider.env_var) for provider in PROVIDERS)

print("Found a key" if have_any_key() else "No provider key found!")

def llm_reply(prompt: str) -> str:
    provider = select_provider()
    client = build_client(provider)
    response = client.chat.completions.create(
        model = os.getenv(provider.model),
        max_completion_tokens = 2048,
        messages = [
            {
                "role": "user",
                "content": prompt.strip()
            }
        ]
    )

    return response.choices[0].message.content

prompt = "who has score the most centuries in test cricket"

class COTStep(BaseModel):
    """ A step in the chain of thought process """
    step_type: Literal["THINKING", "FINAL_OUTPUT"]
    content: str

def parse_cot_step(raw_reply: str) -> COTStep:
    """ Parse a raw reply form the LLM into a chain of thought step """
    try:
        parse = json.loads(raw_reply)
        return COTStep(**parse)
    except Exception as e:
        return f"error: {e}"


def llm_json_reply(messages: list[dict]) -> str:
    provider = select_provider()
    client = build_client(provider)

    kwargs:  dict ={
        "model": os.getenv(provider.model),
        #"max_completion_tokens": 2048,
        "messages": messages
    }

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def extract_number(text: str) -> str:
    # 1. Remove commas so "1,000" becomes "1000"
    text = text.replace(',', '')
    
    # 2. Extract all numbers (including negative signs and decimals)
    numbers = re.findall(r'-?\d+\.?\d*', text)
    
    if numbers:
        # The standard convention for math LLMs is that the final answer 
        # is the last number mentioned in the output string.
        return numbers[-1]
    
    # Fallback to the original text if no number is found
    return text.strip()


class COTAssistant():
    """ An assistant that solves user query using chain of thoughts """
    
    def __init__(self):
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.MAX_STEPS = 20

    def run(self, user_query:str) -> str:
        self.messages.append({"role": "user", "content": user_query})
        print(f"👉{user_query}\n")

        for _ in range(self.MAX_STEPS):
            raw_reply = llm_json_reply(self.messages)
            parsed = parse_cot_step(raw_reply)

            if isinstance(parsed, COTStep):
                self.messages.append({"role": "assistant", "content": raw_reply})

                if parsed.step_type == "THINKING":
                    print(f"💡 {parsed.content}\n")
                    continue
                
                if parsed.step_type == "FINAL_OUTPUT":
                    print(f"🎯 {parsed.content}\n")
                    return parsed.content
            
            else:
                print(f"❌ error: {parsed}")
                return parsed
        
        return f"failed to generate the answer in {self.MAX_STEPS} steps"


#assistant = COTAssistant()
QUESTION = """
Barnaby runs a specialized electronics shop. He purchases 200 limited-edition circuit boards at a wholesale price of $15 each.

In the first month, he manages to sell 40% of his inventory at an 80% markup over the wholesale price. Unfortunately, a water leak in his storage room completely destroys 1/4 of the remaining circuit boards.

Realizing he needs to clear out the rest of the stock quickly before they risk further damage, Barnaby sells the surviving boards at a special clearance price of $18 each.

Additionally, Barnaby must pay a 10% tax on his total gross revenue from all sales, as well as a flat $42 hazardous waste disposal fee for the water-damaged boards.

After accounting for his initial wholesale purchase cost, the taxes, and the disposal fee, what is Barnaby's final net profit?
""".strip()

#assistant.run(QUESTION)

class SelfConsistencyRunner:
    def __init__(self, num_runs: int = 10):
        self.num_runs = num_runs
        self.variations: list = [
            "",
            "Please solve this step-by-step:\n",
            "Carefully calculate the final result for the following:\n",
            "Read the details and find the answer:\n",
            "Analyze this scenario:\n",
            "Work through this math problem:\n",
            "What is the final number here?\n",
            "Consider the following business problem:\n",
            "Provide the final net profit for this situation:\n",
            "Solve this word problem completely:\n"
        ]

    def run(self, base_user_query:str):
        answers = []
        for i in range(self.num_runs):
            prefix = self.variations[i % len(self.variations)]
            modified_user_query = f"{prefix}{base_user_query}".strip()

            print(f"\n--- Run {i+1}/{self.num_runs} ---")

            assistant = COTAssistant()
            raw_answer = assistant.run(modified_user_query)
            clean_number = extract_number(raw_answer)
            answers.append(clean_number)

            counter = collections.Counter(answers)
            most_consistent_answer, count = counter.most_common(1)[0]

            print("\n=== SELF-CONSISTENCY RESULTS ===")
            for ans, c in counter.items():
                print(f"Answer '{ans}': {c} times")
            
        print(f"\n🏆 Final Consensus Answer: {most_consistent_answer} (Voted {count}/{self.num_runs} times)")
        return most_consistent_answer

            


runner = SelfConsistencyRunner(num_runs=10)
runner.run(QUESTION)