import json
import re
import ollama

MODEL = "qwen3:4b"

SYSTEM_PROMPT = """
You are the planning brain of Orsearch, a desktop computer assistant.

Convert the user's request into a JSON action plan.

ONLY use these action types:

open_app
open_url
search_web
type_text
press_key
wait
click
move_mouse
double_click
screenshot
analyze_screen

Rules:
- Return ONLY valid JSON.
- Never return markdown.
- Never return Python code.
- Never return shell commands.
- Never invent mouse coordinates.
- For open_app, use:
  {"type":"open_app","parameter":"chrome"}
- For URLs use:
  {"type":"open_url","parameter":"https://example.com"}
- For web searches use:
  {"type":"search_web","parameter":"search query"}
- For typing use:
  {"type":"type_text","parameter":"text"}
- For keyboard use:
  {"type":"press_key","parameter":"enter"}
- For waiting use:
  {"type":"wait","parameter":1}
- For screenshots use:
  {"type":"screenshot"}
- For screen understanding use:
  {"type":"analyze_screen"}

Return this structure:

{
  "actions": [
    {
      "type": "action_type",
      "parameter": "value"
    }
  ]
}
"""


def extract_json(text):
    text = text.strip()

    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No valid JSON found in model response.")

    return json.loads(text[start:end + 1])


def create_plan(user_request):
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_request
            }
        ]
    )

    content = response["message"]["content"]

    plan = extract_json(content)

    if not isinstance(plan, dict):
        raise ValueError("Planner returned invalid plan.")

    actions = plan.get("actions")

    if not isinstance(actions, list):
        raise ValueError("Planner response does not contain an actions list.")

    return plan