import os
import httpx

AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN") 

async def parse_question_with_llm(question_text: str) -> str:
    url = "https://aipipe.org/openrouter/v1/chat/completions"  
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDM4ODRAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.jkVOT1YKSBgSUuq0RpSig6rac8eve7RQXZ7lVHlPnZA"
    }

    prompt = f"""
You are a helpful data analyst agent.

Given the following question(s), break down the steps needed to answer them:
1. What type of data is required (URL, CSV, image)?
2. What are the questions asking (count, correlation, earliest, plot, etc)?
3. What should be returned (number, list, image, etc)?

Respond in a JSON-like format that's easy to parse programmatically.

Questions:
---
{question_text}
"""

    payload = {
        "model": "openai/gpt-4.1-nano", 
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
