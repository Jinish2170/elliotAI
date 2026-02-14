import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent / "veritas" / ".env")
key = os.getenv("NVIDIA_NIM_API_KEY", "")
base = "https://integrate.api.nvidia.com/v1"

client = OpenAI(api_key=key, base_url=base, timeout=15)

models_to_test = [
    "meta/llama-3.1-70b-instruct",
    "meta/llama-4-scout-17b-16e-instruct",
    "google/gemma-3-27b-it",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "meta/llama-3.2-11b-vision-instruct",
    "meta/llama-3.2-90b-vision-instruct",
    "microsoft/phi-3.5-vision-instruct",
    "nvidia/nemotron-nano-12b-v2-vl",
]

print(f"API key: {key[:20]}...")
for model in models_to_test:
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello in one word"}],
            max_tokens=10,
        )
        content = r.choices[0].message.content if r.choices else "NO CONTENT"
        print(f"OK  {model}: {content[:80]}")
    except Exception as e:
        err = str(e)[:100]
        print(f"ERR {model}: {err}")
