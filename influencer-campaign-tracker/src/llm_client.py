"""LLM wrapper: Groq | OpenAI | mock fallback."""

import os
from dotenv import load_dotenv
load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "").lower().strip()


def call_llm(prompt: str, mock_response: str = "") -> str:
    if PROVIDER == "groq":
        key = os.getenv("GROQ_API_KEY", "")
        if key and not key.startswith("your_"):
            try:
                from groq import Groq
                client = Groq(api_key=key)
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=1200,
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                print(f"  [Groq error: {e}] — falling back to mock.")

    elif PROVIDER == "openai":
        key = os.getenv("OPENAI_API_KEY", "")
        if key and not key.startswith("your_"):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=key)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=1200,
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                print(f"  [OpenAI error: {e}] — falling back to mock.")

    print("  [Mock mode] No API key — using pre-written response.")
    return mock_response
