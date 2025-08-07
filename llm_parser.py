import os
import httpx
import json

timeout = httpx.Timeout(60.0, connect=10.0)  # 60 seconds total timeout, 10s connect



AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
API_URL = "https://aipipe.org/openrouter/v1/chat/completions"
MODEL_NAME = "openai/gpt-4.1-nano"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AIPIPE_TOKEN}"
}

SYSTEM_PROMPT = """
You are a Python data analyst agent. The user will send analytical questions, CSV/image file paths, or URLs. 
Your job is to write clean and functional Python code to perform data analysis and return results.
- If URLs are given (e.g. Wikipedia), scrape them using `pandas.read_html` or `requests + BeautifulSoup`.
- For CSVs, use `pandas.read_csv`.
- If plots are asked, save the matplotlib figure and return a base64 string.

"""

async def parse_question_with_llm(question_text, uploaded_files=None, urls=None):
    uploaded_files = uploaded_files or []
    urls = urls or []

    user_prompt = f"""
Question:
{question_text}

Uploaded files:
{uploaded_files}

URLs:
{urls}

Now write the Python code needed to answer this question.
Only return the code, do NOT explain anything.

Return a JSON with:
1. The 'code' field — Python code that answers the question.
2. The 'libraries' field — list of required pip install packages.
3. Don't add libraries that came installed with python like io.
4. Your output will be executed inside a Python REPL.
5. Add print statement for everything that is important.
6. Don't add commments

Only return JSON like:
{{
  "code": "<...>",
  "libraries": ["pandas", "matplotlib"]
}}

"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "code_and_libraries",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "libraries": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["code", "libraries"],
                    "additionalProperties": False
                }
            }
        }
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        content = response.json()
        llm_response = content["choices"][0]["message"]["content"]
        return json.loads(llm_response)
