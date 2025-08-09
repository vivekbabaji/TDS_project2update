import os
import httpx
import json

timeout = httpx.Timeout(60.0, connect=10.0)  # 60 seconds total timeout, 10s connect



AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
API_URL = "https://aipipe.org/openrouter/v1/chat/completions"
MODEL_NAME = "openai/gpt-4.1"
#MODEL_NAME = "openai/gpt-4.1-nano"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AIPIPE_TOKEN}"
}

SYSTEM_PROMPT = """
You are a data extraction and analysis assistant.  
Your job is to:
1. Write Python code that scrapes the relevant data needed to answer the user's query.
2. List all Python libraries that need to be installed for the code to run.
3. Identify and output the main questions that the user is asking, so they can be answered after the data is scraped.

You must respond **only** in valid JSON following the given schema:
{
  "code": "string — Python scraping code as plain text",
  "libraries": ["string — names of required libraries"],
  "questions": ["string — extracted questions"]
}
Do not include explanations, comments, or extra text outside the JSON.

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

You are a data extraction specialist.
Your task is to generate Python 3 code that loads, scrapes, or reads the data needed to answer the user's question.

1(a). Create code to collect metadata about the data that you collected from scraping (eg. storing details of df using df.info, df.columns, df.head() etc.) in a "uploads/metadata.txt" file that will help other model to generate code.
- add code for creating any folder that don't exist.
1(b). Always store the final dataset in a file as /uploads/data.csv file.And if you find to store other files then also store them in this folder. And lastly add the path and a breif description about the file in "metadata.txt" file.


2. Do not perform any analysis or answer the question. Only write code to collect the data.

3. The code must be self-contained and runnable without manual edits.

4. Use only Python standard libraries plus pandas, numpy, beautifulsoup4, and requests unless otherwise necessary.

5. If the data source is a webpage, download and parse it. If it’s a CSV/Excel, read it directly.

6. Do not explain the code.

7. Output only valid Python code.

8. Just scrap the data don;t do anything fancy.



Return a JSON with:
1. The 'code' field — Python code that answers the question.
2. The 'libraries' field — list of required pip install packages.
3. Don't add libraries that came installed with python like io.
4. Your output will be executed inside a Python REPL.
5. Don't add commments

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
                "name": "code_libraries_questions",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "libraries": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "questions": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["code", "libraries", "questions"],
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




SYSTEM_PROMPT2 = """
You are a data analysis assistant.  
Your job is to:
1. Write Python code to solve these questions with provided metadata.
2. List all Python libraries that need to be installed for the code to run.
3. Also add code to save the result to "uploads/result.txt" or any filetype you find suitable.

You must respond **only** in valid JSON following the given schema:
{
  "code": "string — Python scraping code as plain text",
  "libraries": ["string — names of required libraries"],
}
Do not include explanations, comments, or extra text outside the JSON.

"""


async def answer_with_data(question_text):
    # Open and read the whole file
    with open("uploads/metadata.txt", "r") as file:
        metadata = file.read()

    user_prompt = f"""
Question:
{question_text}

metadata:
{metadata}


Return a JSON with:
1. The 'code' field — Python code that answers the question.
2. The 'libraries' field — list of required pip install packages.
3. Don't add libraries that came installed with python like "io".
4. Your output will be executed inside a Python REPL.
5. Don't add commments

"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT2},
            {"role": "user", "content": user_prompt}
        ]
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        content = response.json()
        llm_response = content["choices"][0]["message"]["content"]
        return llm_response 
