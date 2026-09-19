import os
import time
import urllib.parse
import urllib.request
import random
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def enhance_prompt_for_realism(prompt: str) -> str:
    """
    Enhances prompts, especially for famous personalities, celebrities, or realism,
    so that state-of-the-art Flux diffusion captures the accurate likeness.
    """
    lower = prompt.lower().strip()

    # Specific celebrity enhancements
    if "dhoni" in lower:
        return (
            "Iconic Indian cricket captain MS Dhoni, Mahendra Singh Dhoni, recognizable authentic face of MS Dhoni, "
            "wearing blue Indian cricket jersey number 7, in cricket stadium under bright stadium lights, "
            "sharp detailed portrait, 85mm lens photograph, realistic skin texture, 8k resolution"
        )
    elif "virat" in lower or "kohli" in lower:
        return (
            "Virat Kohli, famous Indian cricketer, authentic facial features of Virat Kohli with beard, "
            "wearing Indian cricket team jersey, cricket stadium background, professional sports photography, 8k"
        )
    elif "rohit" in lower or "sharma" in lower:
        return (
            "Rohit Sharma, Indian cricket captain, authentic face likeness of Rohit Sharma, "
            "wearing blue Indian cricket team jersey, cricket stadium setting, high resolution sports photo"
        )

    # General person / portrait enhancement
    if any(w in lower for w in ["man", "woman", "person", "portrait", "face", "actor", "hero", "cricketer", "player"]):
        return f"{prompt}, authentic highly detailed facial features, realistic skin texture, professional portrait photography, 85mm portrait lens, 8k"

    # General cinematic enhancement
    return f"{prompt}, ultra high quality, master photography, photorealistic, cinematic lighting, highly detailed, 8k"


def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> dict:
    """
    Generates an AI image using Pollinations AI with the FLUX diffusion model
    for photorealistic results and celebrity accuracy.
    """
    try:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            return {
                "success": False,
                "message": "Prompt is empty for image generation.",
                "image_path": None,
            }

        enhanced = enhance_prompt_for_realism(clean_prompt)
        seed = random.randint(1000, 999999)
        encoded_prompt = urllib.parse.quote(enhanced)

        # Uses Flux model which generates accurate faces and photorealism
        image_url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={width}&height={height}&seed={seed}&model=flux&nologo=true"
        )

        timestamp = int(time.time())
        filename = f"image_{timestamp}_{seed % 10000}.jpg"
        local_path = os.path.join(OUTPUT_DIR, filename)

        req = urllib.request.Request(
            image_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        )

        with urllib.request.urlopen(req, timeout=35) as response:
            image_data = response.read()

        with open(local_path, "wb") as f:
            f.write(image_data)

        normalized_path = local_path.replace("\\", "/")

        return {
            "success": True,
            "message": f"Successfully generated image for: '{clean_prompt}'",
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
    res = generate_image("ms dhoni")
    print(res)
