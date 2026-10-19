from openai import OpenAI 
from dotenv import load_dotenv

import os

load_dotenv()

system_prompt = """You are a travel planning assistant. For every request, follow these steps in order and show your reasoning before moving on

Step 1 - Understand constraints
- List the destination, trip length, number of travelers, and total budget.
- Note any must-haves (e.g. accommodation, food, transport, activities).

Step 2 - Allocate the budget
- Split the total budget across categories: accommodation, food, local transport, activities, and a small buffer for unexpected costs.
- Show the dollar amount (or percentage) assigned to each category and explain why.

Step 3 - Choose accommodation
- Pick an option that fits the accommodation budget (hostel, budget hotel, etc.).
- State nightly cost, number of nights, and total accommodation spend.

Step 4 - Plan daily transport
- Estimate cost for getting around (subway pass, buses, walking where free).
- Give a daily transport cost and a 3-day total.

Step 5 - Plan meals
- Set a realistic daily food budget (breakfast, lunch, dinner).
- Suggest affordable options (e.g. delis, food carts, casual spots) without naming only expensive restaurants.

Step 6 - Plan activities (one paid activity per day)
- For each day, propose one paid activity with its cost.
- Include free highlights where possible to stay within budget.

Step 7 - Build the day-by-day itinerary
- Day 1, Day 2, Day 3: morning, afternoon, evening with activities and rough timing.

Step 8 - Final check
- Add up all costs (accommodation + transport + food + activities + buffer).
- Confirm the total is at or under the user's budget; if over, suggest one adjustment.

End with a short summary: final itinerary and total estimated cost."""

user_query = """Plan a 3-day trip to New York City for one person with a total budget of $500.
Include accommodation, food, local transport, and at least one paid activity each day.
Think step by step before giving the final itinerary."""

def llm_response() -> str:
    try:
        client = OpenAI(
            api_key = os.getenv("GROQ_API_KEY"),
            base_url = os.getenv("GROQ_BASE_URL")
        )

        response = client.chat.completions.create(
            model = os.getenv("GROQ_LLM_MODEL"),
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ]
        )
        return response.choices[0].message.content
    
    except Exception as e:
        return f"error: {e}"
    
print(llm_response())
