import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct"

EXPECTED_OUTPUT = """{
    "assignments": [
        {
            "employee": "staff_1",
            "tasks": {
                "07:00": "Ground Floor",
                "08:00": "Ground Floor",
                "09:00": "Outdoor",
                "10:00": "Egress",
                "11:00": "Egress",
                "12:00": "Break",
                "13:00": "BOH-Restroom",
                "14:00": "BOH-Restroom"
            }
        },
        {
            "employee": "staff_2",
            "tasks": {
                "07:00": "First Floor",
                "08:00": "First Floor",
                "09:00": "Outdoor",
                "10:00": "Egress",
                "11:00": "Egress",
                "12:00": "Break",
                "13:00": "BOH-Breakroom",
                "14:00": "BOH-Breakroom",
           
            }
        },
        {
            "employee": "staff_3",
            "tasks": {
                "07:00": "Second Floor",
                "08:00": "Second Floor",
                "09:00": "Outdoor",
                "10:00": "BOH-Restroom",
                "11:00": "Break",
                "12:00": "Restroom 2&4",
                "13:00": "Restroom 2&4",
                "14:00": "Float_TRELLO",
            }
        },
        {
            "employee": "staff_4",
            "tasks": {
                "07:00": "Second Floor",
                "08:00": "Second Floor",
                "09:00": "Outdoor",
                "10:00": "BOH-Breakroom",
                "11:00": "Break",
                "12:00": "Float_0",
                "13:00": "Float_TRELLO",
                "14:00": "Restroom 2&4",
           
            }
        },
        {
            "employee": "staff_5",
            "tasks": {
                "07:00": "Lower Floor",
                "08:00": "Third Floor",
                "09:00": "Design Pavillon",
                "10:00": "Float_TRELLO",
                "11:00": "Float_TRELLO",
                "12:00": "Break",
                "13:00": "Outside",
                "14:00": "Float_TRELLO",
               
            }
        },
        {
            "employee": "staff_6",
            "tasks": {
              
                "13:00": "Float_0",
                "14:00": "Float_1",
                "15:00": "Outside",
                "16:00": "Break",
                "17:00": "FLoat_-1",
                "18:00": "Restroom 2",
                "19:00": "Restroom 2",
                "20:00": "Float_TRELLO"
            }
        },
        {
            "employee": "staff_7",
            "tasks": {
         
                "13:00": "Float_TRELLO",
                "14:00": "Egress",
                "15:00": "Outside",
                "16:00": "Break",
                "17:00": "Restroom 2",
                "18:00": "Restroom",
                "19:00": "BOH-Restroom",
                "20:00": "Trash Removal",
              
            }
        },
        {
            "employee": "staff_8",
            "tasks": {
              
                "15:00": "Restroom 2",
                "16:00": "Restroom 2",
                "17:00": "BOH-Restroom",
                "18:00": "BOH-Breakroom",
                "19:00": "Break",
                "20:00": "Trash Removal",
                "21:00": "Restroom 2&4",
                "22:00": "Restroom 2&4",
                "23:00": "Restroom 2&4"
            }
        }
    ]
}
"""


TASK_CONTEXT = """You are an operations planning AI specialized in workforce scheduling.

Your objective is to generate a valid daily housekeeping schedule for a luxury furniture gallery. 
All hard constraints must be satisfied. If constraints conflict, prioritize them according to the defined priority order.
"""
TASK_DESCRIPTION = """
Create a daily housekeeping schedule for a luxury furniture gallery.

LAYOUT:
- Floor -1, 0, 1: Showrooms
- Floor 2: Restaurant + 4 restrooms
- Floor 3: Bar
- Floor 4: Small restaurant + 2 restrooms
- Floor 5: Rooftop lounge

SHIFTS (team size 11-20 daily, 2 days off/week each):
- Shift 1: 07:00-15:00 | Break 1h within 11:00-13:00
- Shift 2: 13:00-21:00 | Break 1h within 17:00-19:00
- Shift 3: 15:00-23:00 | Break 1h within 19:00-20:00
- Stagger breaks — max half the shift on break at once

OPENING (07:00-10:00, Shift 1 only):

  07:00-09:00 Indoor Clean:
    Floor -1 → 1 person (07-08 only, moves to Floor 3 at 08-09)
    Floor  0 → 1-2 people
    Floor  1 → 1-2 people
    Floor  2 → 2 people (mandatory)
    Floor  4 → 1-2 people

  09:00-10:00 Outdoor (all Shift 1 staff):
    1 each → Outdoor DP, Hallway, Side Hallway, Main Gate
    1 → Design Pavilion

REGULAR TASKS (10:00+):

  Egress           → 2 people 10:00-12:00 | 1 person 15:00-16:00
  BOH-Breakroom    → 1 person at 10-11, 14-15, 17-18
  BOH-Restrooms    → 1 person at 10-11, 14-15, 17-18
  Restroom 2       → 1 person from 12:00 | 2 people from 14:00 (max 2 always)
  Restroom 4       → 1 person at all times

  Float (1 person each, 1h block, 11:00-17:00):
    Float_TRELLO, Float_0, Float_1, Float_-1

  Outdoor (recurring every 2h: 11:00, 13:00, 15:00):
    1-2 people per block | max 3 outdoors at any time
"""

CONSTRAINT = """
RULES:
1. No double-booking — one person, one task at a time
2. Staff only work within their shift hours minus break
3. Shift 2/3 unavailable for opening duties

STAFFING LIMITS:
4. Restroom 2: 1-2 people from 12:00; exactly 2 from 14:00; max 2h per person
5. Restroom 4: exactly 1 at all times; max 2h per person
6. Egress: 2 people (10-12), 1 person (15-16)
7. BOH-Breakroom: 1 person at 10-11, 14-15, 17-18 only
8. BOH-Restrooms: 1 person at 10-11, 14-15, 17-18 only
9. Outdoor: max 3 people at any time
10. Float tasks: 1 person per task, 1h each

OVERFLOW:
11. Unassigned staff → Float_TRELLO, Float_0, or Outdoor (1h blocks, 11-15)
"""

def get_completion(prompt: str, system_prompt: str = "") -> str:
    api_key = os.environ.get("HF_TOKEN")
    if not api_key:
        raise ValueError("HF_TOKEN environment variable not set")

    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=api_key,
    )
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0, 
        max_tokens=20000
    )

    return response.choices[0].message.content


def build_prompt(day_schedule: list[dict]) -> str:
    examples = f"""
Use this example as a template for your output:

<example>
{EXPECTED_OUTPUT}
</example>
"""

    input_data = f"""following is the staff schedule

<staff schedule>
    {json.dumps(day_schedule)}
</staff schedule>
"""

    output_formatting = f"""Put your response in <response></response> tags.
    - response should follow the json format as the example above
"""

    question = "How do you respond to the user's question?"

    prompt = TASK_CONTEXT
    prompt += f"\n\n{TASK_DESCRIPTION}"
    prompt += f"\n\n{examples}"
    prompt += f"\n\n{input_data}"
    prompt += f"\n\n{question}"
    prompt += f"\n\n{CONSTRAINT}"
    prompt += f"\n\n{output_formatting}"

    return prompt


def parse_response(response_text: str) -> dict | None:
    # Strip reasoning blocks from models (<think>, <scratchpad>, etc.)
    cleaned = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)
    cleaned = re.sub(r"<scratchpad>.*?</scratchpad>", "", cleaned, flags=re.DOTALL)

    match = re.search(r"<response>(.*?)</response>", cleaned, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        json_str = cleaned.strip()

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


def generate_schedule(day_schedule: list[dict]) -> tuple[dict | None, str]:
    prompt = build_prompt(day_schedule)
    response = get_completion(prompt)
    return parse_response(response), response


