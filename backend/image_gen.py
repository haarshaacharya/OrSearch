import os
import time
import urllib.parse
import urllib.request
import random

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> dict:
    """
    Generates an AI image using Pollinations AI (free, fast, no API key required),
    saves it locally, and returns metadata including local path and markdown image tag.
    """
    try:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            return {
                "success": False,
                "message": "Prompt is empty for image generation.",
                "image_path": None,
            }

        seed = random.randint(1000, 999999)
        encoded_prompt = urllib.parse.quote(clean_prompt)
        image_url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={width}&height={height}&seed={seed}&nologo=true"
        )

        timestamp = int(time.time())
        filename = f"image_{timestamp}_{seed % 10000}.jpg"
        local_path = os.path.join(OUTPUT_DIR, filename)

        # Download with headers to avoid basic bot blocks
        req = urllib.request.Request(
            image_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            image_data = response.read()

        with open(local_path, "wb") as f:
            f.write(image_data)

        # Normalized path with forward slashes for Qt HTML rendering
        normalized_path = local_path.replace("\\", "/")

        return {
            "success": True,
            "message": f"Successfully generated image for prompt: '{clean_prompt}'",
            "image_path": normalized_path,
            "prompt": clean_prompt,
            "url": image_url,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Image generation failed: {e}",
            "image_path": None,
        }


if __name__ == "__main__":
    res = generate_image("futuristic cyberpunk neon city at night")
    print(res)
