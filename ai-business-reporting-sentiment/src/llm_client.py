"""
Thin LLM wrapper: Groq (default) | OpenAI | mock.

Usage:
    from llm_client import call_llm
    response = call_llm("Your prompt here")

Provider is controlled by LLM_PROVIDER in .env.
If LLM_PROVIDER is blank or the key is missing, returns mock_response.
"""

import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "").lower().strip()


def call_llm(prompt: str, mock_response: str = "") -> str:
    """Call the configured LLM. Falls back to mock_response if no key."""

    if PROVIDER == "groq":
        api_key = os.getenv("GROQ_API_KEY", "")
        if api_key and not api_key.startswith("your_"):
            try:
                from groq import Groq
                client = Groq(api_key=api_key)
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=1024,
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                print(f"  [Groq error: {e}] — falling back to mock.")

    elif PROVIDER == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key and not api_key.startswith("your_"):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=1024,
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                print(f"  [OpenAI error: {e}] — falling back to mock.")

    print("  [Mock mode] No API key detected — using pre-written response.")
    return mock_response
