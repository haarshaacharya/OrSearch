import json
import pyautogui
import ollama

VISION_MODEL = "qwen3-vl:4b"
SCREENSHOT_PATH = "screen.png"


def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save(SCREENSHOT_PATH)

    width, height = screenshot.size

    print(f"Screenshot: {width}x{height}")

    return width, height


def find_element(element):
    width, height = take_screenshot()

    response = ollama.chat(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": f"""
Look at this screenshot carefully.

Find this UI element:

{element}

Screen resolution:
{width} x {height}

Return ONLY JSON.

Example:

{{
    "found": true,
    "left": 100,
    "top": 100,
    "right": 200,
    "bottom": 150
}}

If the element is not clearly visible:

{{
    "found": false,
    "left": null,
    "top": null,
    "right": null,
    "bottom": null
}}

Rules:
- Do not guess.
- Use pixel coordinates.
- The bounding box must cover the actual visible element.
- Return JSON only.
"""
                ,
                "images": [SCREENSHOT_PATH]
            }
        ]
    )

    content = response["message"].get("content", "").strip()

    print("\nRAW VISION RESPONSE:")
    print(repr(content))

    if not content:
        print("Vision model returned an empty response.")
        return None

    print("\nVision response:")
    print(content)

    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    try:
        return json.loads(content)

    except json.JSONDecodeError:
        print("Vision returned invalid JSON.")
        return None


def click_element(element):

    result = find_element(element)

    if not result:
        return

    if not result.get("found"):
        print(f"Element not found: {element}")
        return

    try:
        left = int(result["left"])
        top = int(result["top"])
        right = int(result["right"])
        bottom = int(result["bottom"])

    except (ValueError, TypeError, KeyError):
        print("Invalid coordinates.")
        return

    screen_width, screen_height = pyautogui.size()

    if not (
        0 <= left < screen_width and
        0 <= right <= screen_width and
        0 <= top < screen_height and
        0 <= bottom <= screen_height
    ):
        print("Coordinates are outside screen.")
        return

    x = (left + right) // 2
    y = (top + bottom) // 2

    print()
    print(f"Bounding box: ({left}, {top}) -> ({right}, {bottom})")
    print(f"Clicking center: ({x}, {y})")

    pyautogui.moveTo(
        x,
        y,
        duration=0.5
    )

    pyautogui.sleep(0.5)

    pyautogui.click(
        x,
        y
    )

    print("Click sent successfully.")


print("================================")
print("       ORSEARCH VISION CLICK")
print("================================")

element = input(
    "What should I find and click? "
)

click_element(element)