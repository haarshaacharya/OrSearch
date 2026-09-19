import os
import ollama
import pyautogui

VISION_MODEL = "qwen3-vl:4b"
SCREENSHOT_PATH = "screen.png"


def take_screenshot(path=SCREENSHOT_PATH):
    screenshot = pyautogui.screenshot()
    screenshot.save(path)
    return path


def analyze_image(
    image_path=None,
    instruction="Analyze this image in detail, describe key elements, text, and objects."
):
    """
    Analyzes an uploaded image or takes a fresh screenshot and runs vision inference.
    """
    try:
        target_path = image_path if (image_path and os.path.exists(image_path)) else take_screenshot()

        response = ollama.chat(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": instruction,
                    "images": [target_path],
                }
            ],
        )

        return response["message"]["content"]
    except Exception as e:
        return f"Vision analysis failed ({e}). Please ensure '{VISION_MODEL}' is installed in Ollama."


def analyze_screen(
    instruction="Describe the current screen and identify useful UI elements."
):
    return analyze_image(image_path=None, instruction=instruction)