import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct" # meta-llama/Llama-4-Maverick-17B-128E-Instruct #meta-llama/Llama-3.3-70B-Instruct"

EXPECTED_OUTPUT = """
<example response>


  "assignments": [
    {
      "employee": "staff_1",
      "shift": "Shift 1 (07:00-15:00)",
      "break": "11:00-12:00",
      "tasks": {
        "07:00": "Floor 0",
        "08:00": "Floor 0",
        "09:00": "Outdoor DP",
        "10:00": "Egress",
        "11:00": "Egress",
        "12:00": "Break",
        "13:00": "Outdoor",
        "14:00": "Float_0"
      }
    },
    {
      "employee": "staff_2",
      "shift": "Shift 1 (07:00-15:00)",
      "break": "11:00-12:00",
      "tasks": {
        "07:00": "Floor 1",
        "08:00": "Floor 1",
        "09:00": "Outdoor Hallway",
        "10:00": "Egress",
        "11:00": "Egress",
        "12:00": "Break",
        "13:00": "Restroom 4",
        "14:00": "Float_1"
      }
    },
    {
      "employee": "staff_3",
      "shift": "Shift 1 (07:00-15:00)",
      "break": "12:00-13:00",
      "tasks": {
        "07:00": "Floor 2",
        "08:00": "Floor 2",
        "09:00": "Outdoor Side Hallway",
        "10:00": "BOH-Restrooms",
        "11:00": "Float_TRELLO",
        "12:00": "Break",
        "13:00": "Restroom 2",
        "14:00": "Restroom 2"
      }
    },
    {
      "employee": "staff_4",
      "shift": "Shift 1 (07:00-15:00)",
      "break": "12:00-13:00",
      "tasks": {
        "07:00": "Floor 2",
        "08:00": "Floor 2",
        "09:00": "Outdoor Main Gate",
        "10:00": "BOH-Breakroom",
        "11:00": "Float_-1",
        "12:00": "Break",
        "13:00": "Restroom 2",
        "14:00": "Restroom 2"
      }
    },
    {
      "employee": "staff_5",
      "shift": "Shift 1 (07:00-15:00)",
      "break": "13:00-14:00",
      "tasks": {
        "07:00": "Floor -1",
        "08:00": "Floor 3",
        "09:00": "Design Pavilion",
        "10:00": "Float_TRELLO",
        "11:00": "Break",
        "12:00": "Restroom 4",
        "13:00": "Outdoor",
        "14:00": "BOH-Restrooms"
      }
    },
    {
      "employee": "staff_6",
      "shift": "Shift 1 (07:00-15:00)",
      "break": "13:00-14:00",
      "tasks": {
        "07:00": "Floor 4",
        "08:00": "Floor 4",
        "09:00": "Outdoor DP",
        "10:00": "Float_0",
        "11:00": "Break",
        "12:00": "Restroom 2",
        "13:00": "Restroom 2",
        "14:00": "BOH-Breakroom"
      }
    },
    {
      "employee": "staff_7",
      "shift": "Shift 2 (13:00-21:00)",
      "break": "17:00-18:00",
      "tasks": {
        "13:00": "Float_0",
        "14:00": "Restroom 2",
        "15:00": "Egress",
        "16:00": "Float_TRELLO",
        "17:00": "Break",
        "18:00": "Restroom 2",
        "19:00": "Restroom 2",
        "20:00": "Restroom 2",
        "20:30": "Trash Removal"
      }
    },
    {
      "employee": "staff_8",
      "shift": "Shift 2 (13:00-21:00)",
      "break": "17:00-18:00",
      "tasks": {
        "13:00": "Float_1",
        "14:00": "Restroom 4",
        "15:00": "Outdoor",
        "16:00": "Float_-1",
        "17:00": "Break",
        "18:00": "Restroom 4",
        "19:00": "BOH-Restrooms",
        "20:00": "Restroom 4",
        "20:30": "Trash Removal"
      }
    },
    {
      "employee": "staff_9",
      "shift": "Shift 2 (13:00-21:00)",
      "break": "18:00-19:00",
      "tasks": {
        "13:00": "Float_-1",
        "14:00": "Restroom 2",
        "15:00": "Outdoor",
        "16:00": "Restroom 2",
        "17:00": "BOH-Restrooms",
        "18:00": "Break",
        "19:00": "BOH-Breakroom",
        "20:00": "Float_TRELLO",
        "20:30": "Trash Removal"

      }
    },
    {
      "employee": "staff_10",
      "shift": "Shift 2 (13:00-21:00)",
      "break": "18:00-19:00",
      "tasks": {
        "13:00": "Outdoor",
        "14:00": "Float_-1",
        "15:00": "Float_0",
        "16:00": "Restroom 4",
        "17:00": "BOH-Breakroom",
        "18:00": "Break",
        "19:00": "Restroom 4",
        "20:00": "Float_0",
        "20:30": "Trash Removal"
      }
    },
    {
      "employee": "staff_11",
      "shift": "Shift 3 (15:00-23:00)",
      "break": "19:00-20:00",
      "tasks": {
        "15:00": "Restroom 2",
        "16:00": "Restroom 2",
        "17:00": "Outdoor",
        "18:00": "Float_TRELLO",
        "19:00": "Break",
        "20:00": "Restroom 2",
        "21:00": "Restroom 2&4",
        "22:00": "Restroom 2&4"
      }
    }
  ]
}
</example response>

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
- Shift 1: 07:00-15:00 | Break 1h between 11:00 and 13:00
- Shift 2: 13:00-21:00 | Break 1h between 17:00 and 19:00
- Shift 3: 15:00-23:00 | Break 1h between 19:00 and 20:00
- Stagger breaks 

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
  Trash Removal    - 2 people from 20:30 - 21:00
  Float (1 person each, 1h block, 11:00-19:00):
    Float_TRELLO, Float_0, Float_1, Float_-1

  Outdoor (recurring every 2h: 11:00, 13:00, 15:00, 17:00):
    1-2 people per block | max 3 outdoors at any time

  Trash Removal(2 people from 20:30-21:00)
"""

CONSTRAINT = """
RULES:
1. No double-booking — one person, one task at a time
2. Staff only work within their shift hours minus break


STAFFING LIMITS:
4. Restroom 2: 1-2 people from 12:00; exactly 2 from 14:00; max 2h per person
5. Restroom 4: exactly 1 at all times; max 2h per person
6. Egress: 2 people (10-12), 1 person (15-16)
7. BOH-Breakroom: Exactly 1 person at 10-11, 14-15, 17-18, 19-20 only
8. BOH-Restrooms: Exactly 1 person at 10-11, 14-15, 17-18, 19-20 only
9. Outdoor: max 3 people at any time
10. Float tasks: 1 person per task, 1h each
11. Restroom 2: should be attended all the time from 12:00 onwards

OVERFLOW:
12. Unassigned staff → Float_TRELLO, Float_0, Float_1, Float _-1 or Outdoor (1h blocks, 11:00-19:00)
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
        temperature=.8, 
        max_tokens=8000
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

    question = f"create a well thought after task schedule by strictly following the {CONSTRAINT}"

    prompt = TASK_CONTEXT
    prompt += f"\n\n{TASK_DESCRIPTION}"
    prompt += f"\n\n{examples}"
    prompt += f"\n\n{input_data}"
    prompt += f"\n\n{question}"
    #prompt += f"\n\n{CONSTRAINT}"
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


