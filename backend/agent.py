import os
import re
import ollama

from .planner import create_plan
from .computer import execute_action
from .vision import analyze_image
from .image_gen import generate_image

MODEL = "qwen3:4b"

CODING_SYSTEM_PROMPT = """You are Orsearch AI, a world-class coding assistant and desktop intelligence system.
Provide fast, precise, and expert solutions.
When writing code:
- Always use fenced code blocks with language identifiers (e.g. ```python, ```javascript, ```html, ```cpp).
- Include clean comments and provide copy-ready, working implementations.
- Be direct and avoid unnecessary verbosity so answers are delivered with maximum speed."""


def is_image_generation_request(text: str) -> tuple[bool, str]:
    lower = text.lower().strip()
    image_triggers = [
        "generate image", "create image", "make an image", "draw an image",
        "draw a", "generate a picture", "picture of", "photo of", "generate art",
        "image banao", "photo banao", "tasveer banao", "picture banao", "draw"
    ]
    for trigger in image_triggers:
        if trigger in lower:
            # Extract prompt by stripping trigger
            clean = re.sub(re.escape(trigger), "", text, flags=re.IGNORECASE).strip()
            clean = clean.lstrip("of: ").lstrip("for: ").lstrip(":").strip()
            if not clean:
                clean = text
            return True, clean
    return False, text


def is_computer_action_request(text: str) -> bool:
    lower = text.lower().strip()
    action_keywords = [
        "open chrome", "open notepad", "open app", "launch app",
        "open calculator", "open calc", "open paint", "open explorer",
        "search web", "search google", "open url", "http://", "https://",
        "take screenshot", "capture screen", "press key", "press enter",
        "click at", "move mouse", "double click", "type text"
    ]
    for kw in action_keywords:
        if kw in lower:
            return True
    return False


def run_agent(user_request: str, attachments: list = None) -> dict:
    try:
        if not user_request or not user_request.strip():
            return {
                "success": False,
                "message": "Empty request.",
                "actions": [],
                "plan": None
            }

        attachments = attachments or []
        image_attachments = []
        code_file_context = []

        # Process attachments
        for file_path in attachments:
            if not os.path.exists(file_path):
                continue

            ext = os.path.splitext(file_path)[1].lower()
            fname = os.path.basename(file_path)

            if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]:
                image_attachments.append(file_path)
            elif ext in [".py", ".txt", ".json", ".csv", ".md", ".html", ".css", ".js", ".cpp", ".java", ".c", ".ts"]:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_body = f.read(40000)
                    code_file_context.append(f"\n[Attached File: {fname}]\n```{ext.lstrip('.')}\n{file_body}\n```\n")
                except Exception:
                    pass
            elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
                code_file_context.append(f"\n[Attached Video File: {fname} (Path: {file_path})]\n")
            elif ext in [".mp3", ".wav", ".m4a", ".ogg", ".flac"]:
                code_file_context.append(f"\n[Attached Audio File: {fname} (Path: {file_path})]\n")
            else:
                code_file_context.append(f"\n[Attached Document: {fname} (Path: {file_path})]\n")

        # -------------------------------------------------------------
        # 1. Vision Analysis (If image attached)
        # -------------------------------------------------------------
        if image_attachments:
            target_image = image_attachments[0]
            instruction = user_request.strip() or "Describe this image, read any visible text, and analyze key details."
            vision_result = analyze_image(target_image, instruction)
            return {
                "success": True,
                "message": vision_result,
                "actions": [
                    {
                        "action": {"type": "analyze_image", "file": os.path.basename(target_image)},
                        "result": {"success": True, "message": "Vision analysis complete"}
                    }
                ],
                "plan": None
            }

        # -------------------------------------------------------------
        # 2. AI Image Generation Intent
        # -------------------------------------------------------------
        is_img_gen, img_prompt = is_image_generation_request(user_request)
        if is_img_gen:
            gen_res = generate_image(img_prompt)
            if gen_res.get("success") and gen_res.get("image_path"):
                img_path = gen_res["image_path"]
                response_msg = (
                    f"Generated AI image for: **{img_prompt}**\n\n"
                    f"![Generated Image](file:///{img_path})\n\n"
                    f"*Saved locally to:* `{img_path}`"
                )
                return {
                    "success": True,
                    "message": response_msg,
                    "image_path": img_path,
                    "actions": [
                        {
                            "action": {"type": "generate_image", "prompt": img_prompt},
                            "result": {"success": True, "message": "Image generated successfully"}
                        }
                    ],
                    "plan": None
                }
            else:
                return {
                    "success": False,
                    "message": f"Could not generate image: {gen_res.get('message')}",
                    "actions": [],
                    "plan": None
                }

        # -------------------------------------------------------------
        # 3. Computer Desktop Actions Intent
        # -------------------------------------------------------------
        if is_computer_action_request(user_request):
            plan = create_plan(user_request)
            actions = plan.get("actions", [])
            results = []

            for action in actions:
                action_type = action.get("type", "")
                if action_type == "analyze_screen":
                    instruction = action.get(
                        "parameter",
                        "Describe the current screen and identify useful UI elements."
                    )
                    result = analyze_image(None, instruction)
                else:
                    result = execute_action(action)

                results.append({"action": action, "result": result})

            return {
                "success": True,
                "message": "Desktop actions executed successfully.",
                "actions": results,
                "plan": plan
            }

        # -------------------------------------------------------------
        # 4. Fast Coding & Knowledge / Conversation Intent
        # -------------------------------------------------------------
        full_query = user_request
        if code_file_context:
            full_query = "\n".join(code_file_context) + "\nUser Question:\n" + user_request

        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": CODING_SYSTEM_PROMPT},
                {"role": "user", "content": full_query}
            ],
            options={
                "temperature": 0.3,
                "top_k": 30,
                "top_p": 0.85
            }
        )

        answer = response["message"]["content"].strip()

        return {
            "success": True,
            "message": answer,
            "actions": [],
            "plan": None
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Agent error: {e}",
            "actions": [],
            "plan": None
        }


if __name__ == "__main__":
    print("Testing code query...")
    res = run_agent("write a python function to check if a number is prime")
    print(res["message"])