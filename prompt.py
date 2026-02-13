import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL_NAME = "llama-3.3-70b-versatile" #"meta-llama/llama-4-scout-17b-16e-instruct" 

EXPECTED_OUTPUT = {
    "assignments": [
        {
            "employee": "Candy Paras",
            "tasks": {
                "07:00": "Floor_2",
                "08:00": "Floor_2",
                "09:00": "Outdoor - DP",
                "10:00": "BOH-Breakroom",
                "11:00": "Break",
                "12:00": "Restroom_2",
                "13:00": "Restroom_2",
                "14:00": "Restroom_2",
            },
        },
        {
            "employee": "Melany Vivar Tranquilo",
            "tasks": {
                "07:00": "Floor_2",
                "08:00": "Floor_2",
                "09:00": "Outdoor - Hallway",
                "10:00": "BOH-Restrooms",
                "11:00": "Break",
                "12:00": "Restroom_4",
                "13:00": "Restroom_4",
                "14:00": "Restroom_4",
            },
        },
        {
            "employee": "Olasunkanmi Akinmuyipitan",
            "tasks": {
                "07:00": "Floor_0",
                "08:00": "Floor_0",
                "09:00": "Outdoor - SideHallway",
                "10:00": "Egress",
                "11:00": "Egress",
                "12:00": "Break",
                "13:00": "Float_1",
                "14:00": "BOH-Breakroom",
            },
        },
        {
            "employee": "Raquel Eus\u00e9bio",
            "tasks": {
                "07:00": "Floor_1",
                "08:00": "Floor_1",
                "09:00": "Outdoor - Main Gate",
                "10:00": "Egress",
                "11:00": "Egress",
                "12:00": "Break",
                "13:00": "Float_-1",
                "14:00": "BOH-Restrooms",
            },
        },
        {
            "employee": "Shinde Gaikwad",
            "tasks": {
                "07:00": "Floor_-1",
                "08:00": "Floor_3",
                "09:00": "Outdoor - DP",
                "10:00": "Float_All",
                "11:00": "Break",
                "12:00": "Outdoor-ALL",
                "13:00": "Float_0",
                "14:00": "Restroom_2",
            },
        },
        {
            "employee": "Shivahari Giri",
            "tasks": {
                "07:00": "Floor_4",
                "08:00": "Floor_5",
                "09:00": "Outdoor - SideHallway",
                "10:00": "Float_0",
                "11:00": "Restroom_2",
                "12:00": "Break",
                "13:00": "Outdoor-ALL",
                "14:00": "Restroom_4",
            },
        },
    ]
}

TASK_CONTEXT = "You are an expert task planner. Your goal is to create daily employee schedules"

TASK_DESCRIPTION = """
Create a daily housekeeping schedule for a luxury furniture gallery with these specifications:

GALLERY LAYOUT:
- Floor_-1, 0, 1: Furniture showrooms
- Floor_2: Restaurant + 4 customer restrooms
- Floor_3: Bar
- Floor_4: Small restaurant + 2 customer restrooms
- Floor_5: Rooftop lounge

STAFF:
- Team size: 11-20 people (varies daily)
- Each staff has 2 days off per week
- Shift: 7:00-15:00 with 1-hour break (between 11:00-13:00)

OPENING DUTIES (7:00-10:00 - mandatory daily):
7:00-9:00:
- Floor_-1: 1 person (7:00-8:00 only, then moves to Floor_3 8:00-9:00)
- Floor_0: Min 1 person, max 2
- Floor_1: Min 1 person, max 2
- Floor_2: 2 people (mandatory)
- Floor_4: Min 1 person, max 2

9:00-10:00 (Outdoor tasks - all staff):
- Assign at least 1 person per area: Outdoor DP, Outdoor Hallway, Outdoor SideHallway, Outdoor Main Gate

REGULAR TASKS:
- Egress (10:00-12:00): 2 people mandatory, break 12:00-13:00
- BOH-Breakroom: 1 person, 10:00-11:00 & 14:00-15:00, break 11:00-12:00
- BOH-Restrooms: 1 person, 10:00-11:00 & 14:00-15:00, break 11:00-12:00
- Restroom_2: Min 1 person always, 2 people from 14:00
- Restroom_4:  1 person always
- Float_ALL: 1 person for 1h between 11:00-15:00
- Float_0: 1 person for 1h between 11:00-15:00
- Float_1: 1 person for 1h between 11:00-15:00
- Float_-1: 1 person for 1h between 11:00-15:00

CONSTRAINT:
strictly enforce following constraints
- No double-booking staff across simultaneous tasks
- Restroom_2: min 1 person, max 2 people at all times; 2 people mandatory from 14:00; Max hours per person is 2
- Restroom_4: exactly 1 person at all times; Max hours per person is 2

- Egress: exactly 2 people (10:00-12:00 only)
- BOH-Breakroom: exactly 1 person, only at 10:00-11:00 and 14:00-15:00
- BOH-Restrooms: exactly 1 person, only at 10:00-11:00 and 14:00-15:00

"""

CONSTRAINT = """
Strictly enforce the following when creating the schedule:

- No double-booking staff across simultaneous tasks
- Restroom_2: min 1 person, max 2 people at all times; 2 people mandatory from 14:00
- Restroom_4: exactly 1 person at all times
- Egress: exactly 2 people (10:00-12:00 only)
- BOH-Breakroom: exactly 1 person, only at 10:00-11:00 and 14:00-15:00
- BOH-Restrooms: exactly 1 person, only at 10:00-11:00 and 14:00-15:00
- Extra staffs: assign to Float_ALL or Float_0 tasks (1h each, 11:00-15:00)
"""

PRECOGNITION = """
Think through the problem before responding.
- Use <scratchpad></scratchpad> tags to gather and organize relevant information.
"""

PREFILL = "<response>"


def get_completion(prompt: str, system_prompt: str = "", prefill: str = "") -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")

    client = Groq(api_key=api_key)
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    if prefill:
        messages.append({"role": "assistant", "content": prefill})

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
        max_tokens=2000,
    )

    return prefill + " " + response.choices[0].message.content


def build_prompt(day_schedule: list[dict]) -> str:
    examples = f"""
Use this example as a template for your output:

<example>
{json.dumps(EXPECTED_OUTPUT, indent=2)}
</example>
"""

    input_data = f"""following is the staff schedule

<staff schedule>
    {json.dumps(day_schedule)}
</staff schedule>
"""

    output_formatting = f"""Put your response in <response></response> tags.
    - response should follow the json format as {json.dumps(EXPECTED_OUTPUT)}
"""

    question = "How do you respond to the user's question?"

    prompt = TASK_CONTEXT
    prompt += f"\n\n{TASK_DESCRIPTION}"
    prompt += f"\n\n{examples}"
    prompt += f"\n\n{input_data}"
    prompt += f"\n\n{question}"
    prompt += f"\n\n{CONSTRAINT}"
    prompt += f"\n\n{PRECOGNITION}"
    prompt += f"\n\n{output_formatting}"

    return prompt


def parse_response(response_text: str) -> dict | None:
    match = re.search(r"<response>(.*?)</response>", response_text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        json_str = response_text.strip()

    # Try to find JSON object in the text
    json_str = json_str.replace("'", '"')
    brace_start = json_str.find("{")
    brace_end = json_str.rfind("}")
    if brace_start != -1 and brace_end != -1:
        json_str = json_str[brace_start : brace_end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def generate_schedule(day_schedule: list[dict]) -> dict | None:
    prompt = build_prompt(day_schedule)
    response = get_completion(prompt, prefill=PREFILL)
    return parse_response(response)
