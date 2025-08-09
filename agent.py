import base64
import os
import json
import matplotlib.pyplot as plt
from io import BytesIO
import openai
import httpx
import pandas as pd

# Load API keys from environment variables
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_KEY = os.getenv("ANTHROPIC_API_KEY")  # Optional
GEMINI_KEY = os.getenv("GEMINI_API_KEY")     # Optional

# Configure OpenAI
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

async def handle_question(question: str, files: dict):
    """
    question: str - The text from the first uploaded file
    files: dict {filename: bytes} - All uploaded files
    """
    candidates = []

    # --- Step 1: Ask GPT-4o & GPT-4o-mini ---
    if OPENAI_KEY:
        candidates.append(await ask_openai("gpt-4o", question))
        candidates.append(await ask_openai("gpt-4o-mini", question))

    # --- Step 2: Ask Claude ---
    if CLAUDE_KEY:
        candidates.append(await ask_claude(question))

    # --- Step 3: Ask Gemini ---
    if GEMINI_KEY:
        candidates.append(await ask_gemini(question))

    # --- Step 4: Use LLM to review all answers ---
    final_answer = await review_answers(question, candidates, files)

    return final_answer


import openai

async def ask_openai(model: str, prompt: str):
    # New API usage (note: no .create, and async usage)
    response = await openai.chat.completions.acreate(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content



async def ask_claude(question):
    """Ask Anthropic Claude."""
    async with httpx.AsyncClient() as client:
        headers = {
            "x-api-key": CLAUDE_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "messages": [
                {"role": "user", "content": question}
            ]
        }
        r = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        return r.json()["content"][0]["text"]


async def ask_gemini(question):
    """Ask Google Gemini."""
    async with httpx.AsyncClient() as client:
        params = {"key": GEMINI_KEY}
        r = await client.post(
            "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent",
            params=params,
            json={"contents": [{"parts": [{"text": question}]}]}
        )
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


async def review_answers(question, answers, files):
    """Use GPT-4o to review and finalize the answer."""
    # If there are CSV files, parse them so LLM knows the data
    csv_summaries = []
    for fname, fcontent in files.items():
        if fname.lower().endswith(".csv"):
            try:
                df = pd.read_csv(BytesIO(fcontent))
                csv_summaries.append(f"CSV {fname}: {df.head().to_dict(orient='records')}")
            except Exception as e:
                csv_summaries.append(f"CSV {fname}: Could not parse ({e})")

    review_prompt = f"""
You are a strict evaluator. The question is:
{question}

Here are answers from multiple models:
{json.dumps(answers, indent=2)}

Attached file summaries:
{csv_summaries}

Your task:
- Compare all answers
- Pick the most accurate one
- Ensure it matches the exact format requested in the question
- If a plot is required, output a base64 PNG string under 100kB
Return ONLY the final JSON answer.
"""

    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a careful data analyst who outputs in strict JSON format only."},
            {"role": "user", "content": review_prompt}
        ],
        temperature=0
    )
    return resp.choices[0].message.content.strip()


def generate_dummy_plot():
    """Generate a sample base64 PNG plot."""
    fig, ax = plt.subplots()
    ax.scatter([1, 2, 3], [2, 4, 6])
    ax.plot([1, 2, 3], [2, 4, 6], 'r--')
    ax.set_xlabel("Rank")
    ax.set_ylabel("Peak")
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode()
    return f"data:image/png;base64,{encoded}"

