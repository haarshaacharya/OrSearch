import os
import re
import ollama

from .planner import create_plan
from .computer import execute_action
from .vision import analyze_image
from .image_gen import generate_image

MODEL = "qwen3:4b"

CODING_SYSTEM_PROMPT = """You are Orsearch AI, an elite software engineer and desktop intelligence assistant.
Provide fast, precise, and expert solutions.
When writing code:
- Always use fenced code blocks with language identifiers (e.g. ```python, ```javascript, ```html, ```cpp).
- Include clean comments and provide copy-ready, working implementations.
- Be direct and avoid unnecessary verbosity so answers are delivered with maximum speed."""


def is_image_generation_request(text: str) -> tuple[bool, str]:
    """
    Robust intent classifier for AI image generation.
    Catches variations in English and Hindi/Hinglish:
    - 'make ms dhoni image', 'generate image of cat', 'create an image of taj mahal'
    - 'ms dhoni photo', 'draw a lion', 'wallpaper of sunset'
    - 'ms dhoni ki image banao', 'photo banao ek car ki', 'tasveer banao'
    """
    lower = text.lower().strip()

    image_nouns = [
        "image", "images", "photo", "photos", "picture", "pictures",
        "pic", "pics", "wallpaper", "portrait", "tasveer", "chhavi",
        "drawing", "artwork", "painting"
    ]
    action_verbs = [
        "make", "generate", "create", "draw", "paint", "render",
        "show", "produce", "banao", "chahiye", "dikhao", "tasveer"
    ]

    has_noun = any(re.search(r"\b" + re.escape(n) + r"\b", lower) for n in image_nouns)
    has_verb = any(re.search(r"\b" + re.escape(v) + r"\b", lower) for v in action_verbs)

    direct_starts = (
        lower.startswith("image of")
        or lower.startswith("photo of")
        or lower.startswith("picture of")
        or lower.startswith("pic of")
        or lower.startswith("draw ")
        or lower.startswith("paint ")
    )
    direct_ends = any(lower.endswith(" " + n) for n in image_nouns) or lower in image_nouns

    if (has_noun and has_verb) or direct_starts or direct_ends:
        # Clean filler words to extract the true subject
        clean = text
        remove_patterns = [
            r"\b(can you|please|kindly|could you)\b",
            r"\b(generate|create|make|draw|paint|render|show me|give me)\b",
            r"\b(an?|the)\b",
            r"\b(image of|photo of|picture of|pic of|wallpaper of)\b",
            r"\b(image|images|photo|photos|picture|pictures|pic|pics|wallpaper|portrait|tasveer|chhavi|artwork)\b",
            r"\b(banao|karo|dikhao|chahiye|ki|ke|ka|ek|wali|wala)\b",
        ]
        for pat in remove_patterns:
            clean = re.sub(pat, "", clean, flags=re.IGNORECASE)

        clean = re.sub(r"\s+", " ", clean).strip()
        clean = clean.strip(":,.-_ ")

        if not clean or len(clean) < 2:
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
        # 2. AI Image Generation Intent (High-Priority Match)
        # -------------------------------------------------------------
        is_img_gen, img_prompt = is_image_generation_request(user_request)
        if is_img_gen:
            # Enrich prompt for realistic high-definition results
            enriched_prompt = f"{img_prompt}, ultra realistic, highly detailed portrait, 8k resolution, cinematic lighting"
            gen_res = generate_image(enriched_prompt)

            if gen_res.get("success") and gen_res.get("image_path"):
                img_path = gen_res["image_path"]
                response_msg = (
                    f"### 🎨 AI Generated Artwork\n\n"
                    f"**Subject:** *{img_prompt}*\n\n"
                    f"![{img_prompt}](file:///{img_path})\n\n"
                    f"📁 *Saved to local disk:* `{img_path}`"
                )
                return {
                    "success": True,
                    "message": response_msg,
                    "image_path": img_path,
                    "is_image": True,
                    "actions": [
                        {
                            "action": {"type": "generate_image", "subject": img_prompt},
                            "result": {"success": True, "message": f"Saved locally: {img_path}"}
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
                "temperature": 0.2,
                "top_k": 25,
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
    test_q = "make ms dhoni image"
    is_img, p = is_image_generation_request(test_q)
    print(f"Query: '{test_q}' -> is_img: {is_img}, prompt: '{p}'")