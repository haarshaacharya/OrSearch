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
9. {"type":"wait","seconds":2}
10. {"type":"click","x":500,"y":300}
11. {"type":"move_mouse","x":500,"y":300}
12. {"type":"double_click","x":500,"y":300}
13. {"type":"screenshot"}
14. {"type":"analyze_screen"}

Important rules:

- If the user asks to open a website, use open_url.
- If the user asks to search something on Google, use search_web.
- When opening a website or searching, open Chrome first.
- Use click, move_mouse and double_click only when coordinates are known.
- Never invent coordinates.
- Use screenshot when the user asks to take a screenshot.
- Use analyze_screen when the user asks what is currently visible on the screen.
- Do not use arbitrary shell commands.
- Do not generate Python, PowerShell or CMD commands.
- Never generate file deletion commands.
- Never generate registry commands.

Return this exact structure:

{
  "actions": [
    {
      "type": "action_name",
      "parameter": "value"
    }
  ]
}

Examples:

User: Open Chrome

{
  "actions": [
    {"type":"open_app","app":"chrome"}
  ]
}

User: Open Google Classroom

{
  "actions": [
    {"type":"open_app","app":"chrome"},
    {"type":"wait","seconds":1},
    {"type":"open_url","url":"https://classroom.google.com"}
  ]
}

User: Search Google for Cisco Packet Tracer practical 4

{
  "actions": [
    {"type":"open_app","app":"chrome"},
    {"type":"wait","seconds":1},
    {"type":"search_web","query":"Cisco Packet Tracer practical 4"}
  ]
}

User: Open YouTube

{
  "actions": [
    {"type":"open_app","app":"chrome"},
    {"type":"wait","seconds":1},
    {"type":"open_url","url":"https://www.youtube.com"}
  ]
}

User: Open Notepad and type Hello World

{
  "actions": [
    {"type":"open_app","app":"notepad"},
    {"type":"wait","seconds":1},
    {"type":"type_text","text":"Hello World"}
  ]
}

User: Take a screenshot

{
  "actions": [
    {"type":"screenshot"}
  ]
}

User: Analyze the screen

{
  "actions": [
    {"type":"analyze_screen"}
  ]
}
"""


def chrome_is_running():
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq chrome.exe"],
        capture_output=True,
        text=True
    )

    return "chrome.exe" in result.stdout.lower()


def focus_chrome():
    pyautogui.hotkey("alt", "tab")
    time.sleep(0.5)


def take_screenshot():
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(SCREENSHOT_PATH)

        print("Screenshot captured.")

        return True

    except Exception as error:
        print(f"Screenshot failed: {error}")

        return False


def analyze_screen():
    print("\nAnalyzing screen with Qwen3-VL...\n")

    if not take_screenshot():
        return

    try:
        response = ollama.chat(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": """
Analyze this Windows screenshot carefully.

Tell me:

1. What application is currently visible?
2. What website or page is open, if any?
3. What important UI elements are visible?
4. What buttons, text fields, menus or icons are visible?
5. Give approximate locations of important elements using screen coordinates.

Do not invent elements that are not visible.
Keep the answer concise.
""",
                    "images": [SCREENSHOT_PATH]
                }
            ]
        )

        result = response["message"]["content"]

        print("========== SCREEN ANALYSIS ==========")
        print(result)
        print("=====================================")

    except Exception as error:
        print(f"Vision analysis failed: {error}")


def execute_action(action):
    action_type = action.get("type")

    if action_type == "open_app":
        app = action.get("app", "").lower()

        if app == "chrome":

            if chrome_is_running():
                print("Chrome is already open. Using existing Chrome window.")
                focus_chrome()

            else:
                print("Opening Chrome...")
                subprocess.Popen(
                    "start chrome",
                    shell=True
                )

                time.sleep(2)

        elif app == "notepad":

            print("Opening Notepad...")

            subprocess.Popen(
                "notepad.exe"
            )

            time.sleep(1)

        else:
            print(
                f"Blocked unknown app: {app}"
            )

    elif action_type == "open_url":

        url = action.get(
            "url",
            ""
        )

        if not chrome_is_running():

            subprocess.Popen(
                "start chrome",
                shell=True
            )

            time.sleep(2)

        focus_chrome()

        pyautogui.hotkey(
            "ctrl",
            "l"
        )

        time.sleep(0.3)

        pyautogui.write(
            url,
            interval=0.01
        )

        pyautogui.press(
            "enter"
        )

    elif action_type == "search_web":

        query = action.get(
            "query",
            ""
        )

        if not chrome_is_running():

            subprocess.Popen(
                "start chrome",
                shell=True
            )

            time.sleep(2)

        focus_chrome()

        url = (
            "https://www.google.com/search?q="
            + query.replace(" ", "+")
        )

        pyautogui.hotkey(
            "ctrl",
            "l"
        )

        time.sleep(0.3)

        pyautogui.write(
            url,
            interval=0.01
        )

        pyautogui.press(
            "enter"
        )

    elif action_type == "type_text":

        text = action.get(
            "text",
            ""
        )

        pyautogui.write(
            text,
            interval=0.02
        )

    elif action_type == "press_key":

        key = action.get(
            "key",
            ""
        ).lower()

        allowed_keys = {
            "enter",
            "tab",
            "esc",
            "space",
            "backspace",
            "up",
            "down",
            "left",
            "right"
        }

        if key in allowed_keys:

            pyautogui.press(
                key
            )

        else:

            print(
                f"Blocked key: {key}"
            )

    elif action_type == "click":

        try:

            x = int(
                action.get(
                    "x",
                    0
                )
            )

            y = int(
                action.get(
                    "y",
                    0
                )
            )

            pyautogui.click(
                x,
                y
            )

            print(
                f"Clicked at ({x}, {y})"
            )

        except (
            ValueError,
            TypeError
        ):

            print(
                "Invalid click coordinates."
            )

    elif action_type == "move_mouse":

        try:

            x = int(
                action.get(
                    "x",
                    0
                )
            )

            y = int(
                action.get(
                    "y",
                    0
                )
            )

            pyautogui.moveTo(
                x,
                y,
                duration=0.2
            )

            print(
                f"Mouse moved to ({x}, {y})"
            )

        except (
            ValueError,
            TypeError
        ):

            print(
                "Invalid mouse coordinates."
            )

    elif action_type == "double_click":

        try:

            x = int(
                action.get(
                    "x",
                    0
                )
            )

            y = int(
                action.get(
                    "y",
                    0
                )
            )

            pyautogui.doubleClick(
                x,
                y
            )

            print(
                f"Double clicked at ({x}, {y})"
            )

        except (
            ValueError,
            TypeError
        ):

            print(
                "Invalid double-click coordinates."
            )

    elif action_type == "screenshot":

        take_screenshot()

    elif action_type == "analyze_screen":

        analyze_screen()

    elif action_type == "wait":

        try:

            seconds = float(
                action.get(
                    "seconds",
                    1
                )
            )

            seconds = min(
                max(seconds, 0),
                10
            )

            time.sleep(
                seconds
            )

        except (
            ValueError,
            TypeError
        ):

            print(
                "Invalid wait time."
            )

    else:

        print(
            f"Unknown action blocked: {action_type}"
        )


def run_agent(user_input):

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

    print("\nAI Plan:")
    print(content)

    try:

        plan = json.loads(
            content
        )

    except json.JSONDecodeError:

        print(
            "\nCould not understand AI action plan."
        )

        return

    actions = plan.get(
        "actions",
        []
    )

    if not isinstance(
        actions,
        list
    ):

        print(
            "Invalid action format."
        )

        return

    print(
        "\nExecuting...\n"
    )

    for action in actions:

        print(
            "->",
            action
        )

        execute_action(
            action
        )


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

    run_agent(
        user_input
    )