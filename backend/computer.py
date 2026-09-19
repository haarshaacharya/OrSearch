import subprocess
import time

import pyautogui


ALLOWED_APPS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
}


def chrome_is_running():
    try:
        result = subprocess.run(
            ["tasklist"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return "chrome.exe" in result.stdout.lower()

    except Exception:
        return False


def focus_chrome():
    pyautogui.hotkey("alt", "tab")


def take_screenshot(path="screen.png"):
    screenshot = pyautogui.screenshot()
    screenshot.save(path)

    return path


def open_app(app_name):
    app = str(app_name or "").strip().lower()

    if app not in ALLOWED_APPS:
        return f"Blocked unknown app: {app}"

    target = ALLOWED_APPS[app]

    try:
        if target == "chrome":
            if chrome_is_running():
                focus_chrome()
            else:
                subprocess.Popen(
                    "start chrome",
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
        else:
            subprocess.Popen(target)

        return f"{app_name} opening."

    except Exception as e:
        return f"Failed to open {app_name}: {e}"


def open_url(url):
    url = str(url or "").strip()

    if not url:
        return "No URL provided."

    try:
        if not chrome_is_running():
            subprocess.Popen(
                "start chrome",
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            focus_chrome()

        pyautogui.hotkey("ctrl", "l")
        pyautogui.write(url, interval=0)
        pyautogui.press("enter")

        return f"Opening {url}"

    except Exception as e:
        return f"Failed to open URL: {e}"


def search_web(query):
    query = str(query or "").strip()

    if not query:
        return "No search query provided."

    try:
        if not chrome_is_running():
            subprocess.Popen(
                "start chrome",
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            focus_chrome()

        url = (
            "https://www.google.com/search?q="
            + query.replace(" ", "+")
        )

        pyautogui.hotkey("ctrl", "l")
        pyautogui.write(url, interval=0)
        pyautogui.press("enter")

        return f"Searching for {query}"

    except Exception as e:
        return f"Search failed: {e}"


def type_text(text):
    try:
        pyautogui.write(
            str(text),
            interval=0
        )

        return "Text typed."

    except Exception as e:
        return f"Typing failed: {e}"


def press_key(key):
    try:
        pyautogui.press(str(key))

        return f"Pressed {key}."

    except Exception as e:
        return f"Key press failed: {e}"


def click(x, y):
    try:
        pyautogui.click(
            int(x),
            int(y)
        )

        return f"Clicked at ({x}, {y})."

    except Exception as e:
        return f"Click failed: {e}"


def move_mouse(x, y):
    try:
        pyautogui.moveTo(
            int(x),
            int(y),
            duration=0
        )

        return f"Mouse moved to ({x}, {y})."

    except Exception as e:
        return f"Mouse movement failed: {e}"


def double_click(x, y):
    try:
        pyautogui.doubleClick(
            int(x),
            int(y),
            interval=0
        )

        return f"Double-clicked at ({x}, {y})."

    except Exception as e:
        return f"Double-click failed: {e}"


def wait(seconds):
    try:
        seconds = float(seconds)
        seconds = max(0, min(seconds, 10))

        time.sleep(seconds)

        return f"Waited {seconds} seconds."

    except Exception as e:
        return f"Wait failed: {e}"


def execute_action(action):
    if not isinstance(action, dict):
        return "Invalid action."

    action_type = str(
        action.get("type", "")
    ).strip()

    parameter = action.get("parameter")

    if action_type == "open_app":
        app = action.get(
            "app",
            parameter
        )

        return open_app(app)

    if action_type == "open_url":
        return open_url(parameter)

    if action_type == "search_web":
        return search_web(parameter)

    if action_type == "type_text":
        return type_text(parameter)

    if action_type == "press_key":
        return press_key(parameter)

    if action_type == "wait":
        return wait(parameter)

    if action_type == "click":
        x = action.get("x")
        y = action.get("y")

        if x is None or y is None:
            return "Click blocked: coordinates missing."

        return click(x, y)

    if action_type == "move_mouse":
        x = action.get("x")
        y = action.get("y")

        if x is None or y is None:
            return "Mouse movement blocked: coordinates missing."

        return move_mouse(x, y)

    if action_type == "double_click":
        x = action.get("x")
        y = action.get("y")

        if x is None or y is None:
            return "Double-click blocked: coordinates missing."

        return double_click(x, y)

    if action_type == "screenshot":
        return take_screenshot()

    if action_type == "analyze_screen":
        return "Screen analysis requested."

    return f"Blocked unknown action: {action_type}"