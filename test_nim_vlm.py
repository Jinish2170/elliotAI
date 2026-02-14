"""Quick test: which NIM VLM models accept image input?"""
import asyncio
import base64
import os
import sys
from pathlib import Path

from openai import AsyncOpenAI

API_KEY = "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"
BASE = "https://integrate.api.nvidia.com/v1"

# Use a real screenshot from the evidence dir
IMG_PATH = r"c:\jinish\elliotAI\veritas\data\evidence\512a7648_t0.jpg"
with open(IMG_PATH, "rb") as f:
    TINY_JPG_B64 = base64.b64encode(f.read()).decode("utf-8")

MODELS = [
    "meta/llama-3.2-90b-vision-instruct",
    "meta/llama-3.2-11b-vision-instruct",
    "microsoft/phi-3.5-vision-instruct",
    "nvidia/neva-22b",
    "google/deformable-detr",
    "nvidia/vila",
    "adept/fuyu-8b",
]

async def test_model(client, model):
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "What do you see? Reply in one sentence."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{TINY_JPG_B64}"}},
                ],
            }],
            max_tokens=50,
            temperature=0.1,
        )
        text = resp.choices[0].message.content[:80]
        print(f"  OK  {model} -> {text}")
        return model
    except Exception as e:
        ename = type(e).__name__
        detail = str(e)[:120]
        print(f"  FAIL {model} -> {ename}: {detail}")
        return None

async def test_text_models(client):
    """Also test LLM models"""
    text_models = [
        "meta/llama-3.1-70b-instruct",
        "meta/llama-3.1-8b-instruct",
        "nvidia/llama-3.1-nemotron-70b-instruct",
    ]
    print("\n--- Text LLM models ---")
    for m in text_models:
        try:
            resp = await client.chat.completions.create(
                model=m,
                messages=[{"role": "user", "content": "Say hello in one word."}],
                max_tokens=10,
                temperature=0.1,
            )
            text = resp.choices[0].message.content[:40]
            print(f"  OK  {m} -> {text}")
        except Exception as e:
            print(f"  FAIL {m} -> {type(e).__name__}: {str(e)[:120]}")

async def main():
    client = AsyncOpenAI(base_url=BASE, api_key=API_KEY)
    print("--- VLM models (image input) ---")
    working = []
    for m in MODELS:
        r = await test_model(client, m)
        if r:
            working.append(r)
    
    await test_text_models(client)
    
    print(f"\nWorking VLM models: {working}")

asyncio.run(main())
