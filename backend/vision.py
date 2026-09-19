import ollama
import pyautogui

VISION_MODEL = "qwen3-vl:4b"
SCREENSHOT_PATH = "screen.png"


def take_screenshot(path=SCREENSHOT_PATH):
    screenshot = pyautogui.screenshot()
    screenshot.save(path)
    return path


def analyze_screen(
    instruction="Describe the current screen and identify useful UI elements."
):
    path = take_screenshot()

    response = ollama.chat(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": instruction,
                "images": [path],
            }
        ],
    )

    return response["message"]["content"]