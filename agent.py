import json
import subprocess
import time

import pyautogui
import ollama


MODEL = "qwen3:4b"
VISION_MODEL = "qwen3-vl:4b"
SCREENSHOT_PATH = "screen.png"


SYSTEM_PROMPT = """
You are Orsearch, a Windows computer assistant.

Convert the user's request into a sequence of SAFE computer actions.

Return ONLY valid JSON.
Do not use markdown.
Do not explain anything.

Available actions:

1. {"type":"open_app","app":"chrome"}
2. {"type":"open_app","app":"notepad"}
3. {"type":"open_url","url":"https://example.com"}
4. {"type":"search_web","query":"search query"}
5. {"type":"type_text","text":"text to type"}
6. {"type":"press_key","key":"enter"}
7. {"type":"press_key","key":"tab"}
8. {"type":"press_key","key":"esc"}
9. {"type":"press_key","key":"space"}
10. {"type":"press_key","key":"backspace"}
11. {"type":"wait","seconds":0.1}
12. {"type":"click","x":500,"y":300}
13. {"type":"move_mouse","x":500,"y":300}
14. {"type":"double_click","x":500,"y":300}
15. {"type":"screenshot"}
16. {"type":"analyze_screen"}

IMPORTANT SPEED RULES:

- Execute actions as fast as possible.
- NEVER add unnecessary waits.
- Do not use 1 or 2 second waits unless absolutely required.
- Prefer no wait between actions.
- If an app opens, immediately continue with the next action.
- If Enter is pressed, immediately continue.
- If a click happens, immediately continue.
- The computer itself may take time to load applications or websites.
- Never invent coordinates.
- Use coordinates only when they are known from screen understanding.
- Do not use arbitrary shell commands.
- Do not generate Python, PowerShell or CMD commands.
- Never generate file deletion commands.
- Never generate registry commands.

If the user asks to open a website:
- Open Chrome if necessary.
- Immediately navigate to the website.

If the user asks to search:
- Open Chrome if necessary.
- Immediately perform the search.

If the user asks to type something:
- Open the required application first if necessary.
- Then type immediately.

Return exactly:

{
  "actions": [
    {
      "type": "action_name",
      "parameter": "value"
    }
  ]
}
"""


def chrome_is_running():

    try:

        result = subprocess.run(
            [
                "tasklist",
                "/FI",
                "IMAGENAME eq chrome.exe"
            ],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return "chrome.exe" in result.stdout.lower()

    except Exception:

        return False


def focus_chrome():

    pyautogui.hotkey(
        "alt",
        "tab"
    )


def take_screenshot():

    try:

        screenshot = pyautogui.screenshot()

        screenshot.save(
            SCREENSHOT_PATH
        )

        return (
            True,
            "Screenshot captured successfully."
        )

    except Exception as error:

        return (
            False,
            f"Screenshot failed: {error}"
        )


def analyze_screen():

    success, message = take_screenshot()

    if not success:
        return message

    try:

        response = ollama.chat(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": """
Analyze this Windows screenshot carefully.

Tell me:

1. What application is visible?
2. What website or page is open?
3. What important UI elements are visible?
4. What buttons, text fields, menus or icons are visible?
5. Give approximate screen coordinates of important elements.

Do not invent elements that are not visible.
Keep the answer concise.
""",
                    "images": [
                        SCREENSHOT_PATH
                    ]
                }
            ]
        )

        return response[
            "message"
        ][
            "content"
        ]

    except Exception as error:

        return f"Vision analysis failed: {error}"


def execute_action(action):

    if not isinstance(action, dict):

        return "Invalid action."

    action_type = action.get(
        "type",
        ""
    )

    parameter = action.get(
        "parameter"
    )

    # =========================================================
    # OPEN APP
    # =========================================================

    if action_type == "open_app":

        app = action.get(
            "app",
            parameter
        )

        if not app:
            return "No application specified."

        app = str(
            app
        ).lower().strip()

        # Chrome
        if app == "chrome":

            if chrome_is_running():

                focus_chrome()

                return "Chrome focused."

            subprocess.Popen(
                "start chrome",
                shell=True
            )

            return "Chrome opening."

        # Notepad
        if app == "notepad":

            subprocess.Popen(
                "notepad.exe"
            )

            return "Notepad opening."

        return f"Blocked unknown app: {app}"

    # =========================================================
    # OPEN URL
    # =========================================================

    elif action_type == "open_url":

        url = action.get(
            "url",
            parameter
        )

        if not url:

            return "No URL provided."

        if not chrome_is_running():

            subprocess.Popen(
                "start chrome",
                shell=True
            )

        else:

            focus_chrome()

        pyautogui.hotkey(
            "ctrl",
            "l"
        )

        pyautogui.write(
            str(url),
            interval=0
        )

        pyautogui.press(
            "enter"
        )

        return f"Opening {url}"

    # =========================================================
    # SEARCH WEB
    # =========================================================

    elif action_type == "search_web":

        query = action.get(
            "query",
            parameter
        )

        if not query:

            return "No search query provided."

        if not chrome_is_running():

            subprocess.Popen(
                "start chrome",
                shell=True
            )

        else:

            focus_chrome()

        url = (
            "https://www.google.com/search?q="
            + str(query).replace(
                " ",
                "+"
            )
        )

        pyautogui.hotkey(
            "ctrl",
            "l"
        )

        pyautogui.write(
            url,
            interval=0
        )

        pyautogui.press(
            "enter"
        )

        return f"Searching Google for {query}"

    # =========================================================
    # TYPE TEXT
    # =========================================================

    elif action_type == "type_text":

        text = action.get(
            "text",
            parameter
        )

        if text is None:

            return "No text provided."

        try:

            pyautogui.write(
                str(text),
                interval=0
            )

            return "Text typed."

        except Exception as error:

            return f"Typing failed: {error}"

    # =========================================================
    # PRESS KEY
    # =========================================================

    elif action_type == "press_key":

        key = action.get(
            "key",
            parameter
        )

        if not key:

            return "No key specified."

        key = str(
            key
        ).lower().strip()

        allowed_keys = {
            "enter",
            "tab",
            "esc",
            "space",
            "backspace",
            "up",
            "down",
            "left",
            "right",
            "home",
            "end",
            "delete"
        }

        if key not in allowed_keys:

            return f"Blocked key: {key}"

        pyautogui.press(
            key
        )

        return f"Pressed {key}."

    # =========================================================
    # CLICK
    # =========================================================

    elif action_type == "click":

        try:

            x = int(
                action.get(
                    "x"
                )
            )

            y = int(
                action.get(
                    "y"
                )
            )

            pyautogui.click(
                x,
                y
            )

            return f"Clicked ({x}, {y})."

        except (
            ValueError,
            TypeError
        ):

            return "Invalid click coordinates."

    # =========================================================
    # DOUBLE CLICK
    # =========================================================

    elif action_type == "double_click":

        try:

            x = int(
                action.get(
                    "x"
                )
            )

            y = int(
                action.get(
                    "y"
                )
            )

            pyautogui.doubleClick(
                x,
                y
            )

            return f"Double clicked ({x}, {y})."

        except (
            ValueError,
            TypeError
        ):

            return "Invalid double-click coordinates."

    # =========================================================
    # MOVE MOUSE
    # =========================================================

    elif action_type == "move_mouse":

        try:

            x = int(
                action.get(
                    "x"
                )
            )

            y = int(
                action.get(
                    "y"
                )
            )

            pyautogui.moveTo(
                x,
                y,
                duration=0
            )

            return f"Mouse moved to ({x}, {y})."

        except (
            ValueError,
            TypeError
        ):

            return "Invalid mouse coordinates."

    # =========================================================
    # WAIT
    # =========================================================

    elif action_type == "wait":

        try:

            seconds = float(
                action.get(
                    "seconds",
                    parameter if parameter is not None else 0
                )
            )

            seconds = min(
                max(seconds, 0),
                10
            )

            if seconds > 0:

                time.sleep(
                    seconds
                )

            return f"Waited {seconds} seconds."

        except (
            ValueError,
            TypeError
        ):

            return "Invalid wait time."

    # =========================================================
    # SCREENSHOT
    # =========================================================

    elif action_type == "screenshot":

        success, message = take_screenshot()

        return message

    # =========================================================
    # ANALYZE SCREEN
    # =========================================================

    elif action_type == "analyze_screen":

        return analyze_screen()

    # =========================================================
    # UNKNOWN
    # =========================================================

    return f"Unknown action blocked: {action_type}"


def run_agent(user_input):

    if not user_input or not user_input.strip():

        return {
            "success": False,
            "message": "Empty request.",
            "actions": [],
            "plan": None
        }

    # =========================================================
    # ASK QWEN
    # =========================================================

    try:

        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )

        content = response[
            "message"
        ][
            "content"
        ].strip()

    except Exception as error:

        return {
            "success": False,
            "message": f"AI connection failed: {error}",
            "actions": [],
            "plan": None
        }

    # =========================================================
    # CLEAN MARKDOWN
    # =========================================================

    if content.startswith("```"):

        content = content.replace(
            "```json",
            ""
        )

        content = content.replace(
            "```JSON",
            ""
        )

        content = content.replace(
            "```",
            ""
        )

        content = content.strip()

    # =========================================================
    # PARSE JSON
    # =========================================================

    try:

        plan = json.loads(
            content
        )

    except json.JSONDecodeError:

        return {
            "success": False,
            "message": "AI returned invalid JSON.",
            "actions": [],
            "plan": None,
            "raw_response": content
        }

    actions = plan.get(
        "actions",
        []
    )

    if not isinstance(
        actions,
        list
    ):

        return {
            "success": False,
            "message": "AI returned invalid action list.",
            "actions": [],
            "plan": plan
        }

    # =========================================================
    # EXECUTE
    # =========================================================

    results = []

    for action in actions:

        result = execute_action(
            action
        )

        results.append(
            {
                "action": action,
                "result": result
            }
        )

    return {
        "success": True,
        "message": "Task completed.",
        "actions": results,
        "plan": plan
    }


# =============================================================
# CLI TEST MODE
# =============================================================

if __name__ == "__main__":

    print(
        "================================"
    )

    print(
        "       ORSEARCH AGENT"
    )

    print(
        "================================"
    )

    print(
        "Type 'exit' to quit.\n"
    )

    while True:

        user_input = input(
            "You: "
        )

        if user_input.lower().strip() == "exit":

            break

        if not user_input.strip():

            continue

        result = run_agent(
            user_input
        )

        print(
            "\nResult:"
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            )
        )

        print()