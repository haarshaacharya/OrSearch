import ollama

MODEL = "qwen3-vl:4b"

response = ollama.chat(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": """
Analyze this screenshot.

Tell me:
1. What application is visible?
2. What website or page is open?
3. What important buttons or UI elements can you see?
4. Give the approximate location of the main clickable elements.

Keep the answer concise.
""",
            "images": ["screen.png"]
        }
    ]
)

print("\n--- SCREEN UNDERSTANDING ---\n")
print(response["message"]["content"])