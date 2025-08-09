import os
import json
import google.generativeai as genai

# Configure Gemini API key (set GEMINI_API_KEY in your environment)
genai.configure(api_key="AIzaSyC3dswe0cmF3HSO8Ay8xkOnyoHwk1OToW4")

MODEL_NAME = "gemini-2.5-flash"  # You can also use "gemini-1.5-flash"

SYSTEM_PROMPT = """
You are a data extraction and analysis assistant.  
Your job is to:
1. Write Python code that scrapes the relevant data needed to answer the user's query.If no url are given and then see "uploads" folder and read the files provided there and give relevent metadata.
2. List all Python libraries that need to be installed for your code to run.
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
"{question_text}"

Uploaded files:
"{uploaded_files}"

URLs:
"{urls}"

You are a data extraction specialist.
Your task is to generate Python 3 code that loads, scrapes, or reads the data needed to answer the user's question.

1(a). Always store the final dataset in a file as /uploads/data.csv file.And if you find to store other files then also store them in this folder. And lastly add the path and a breif description about the file in "metadata.txt" file.
1(b). Create code to collect metadata about the data that you collected from scraping (eg. storing details of df using df.info, df.columns, df.head() etc.) in a "uploads/metadata.txt" file that will help other model to generate code. Add code for creating any folder that don't exist like "uploads".

2. Do not perform any analysis or answer the question. Only write code to collect or add metadata.

3. The code must be self-contained and runnable without manual edits.

4. Use only Python standard libraries plus pandas, numpy, beautifulsoup4, and requests unless otherwise necessary.

5. If the data source is a webpage, download and parse it. If it’s a CSV/Excel, read it directly.

6. Do not explain the code.

7. Output only valid Python code.

8. Just scrap the data don’t do anything fancy.

Return a JSON with:
1. The 'code' field — Python code that answers the question.
2. The 'libraries' field — list of required pip install packages.
3. Don't add libraries that came installed with python like io.
4. Your output will be executed inside a Python REPL.
5. Don't add comments

Only return JSON like:
{{
  "code": "<...>",
  "libraries": ["pandas", "matplotlib"],
  "questions": ["..."]
}}

lastly i am saying again don't try to solve these questions.
in metadata also add JSON answer format if present.
"""

    model = genai.GenerativeModel(MODEL_NAME)

    response = model.generate_content(
        [SYSTEM_PROMPT, user_prompt],
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
    )


    # Path to the file
    file_path = "uploads/metadata.txt"

    # Create the folder if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Check if file exists
    if not os.path.exists(file_path):
        # Create an empty file
        with open(file_path, "w") as f:
            f.write("")  # optional, just ensures the file exists
        print("File created:", file_path)
    else:
        print("File already exists:", file_path)


    return json.loads(response.text)


SYSTEM_PROMPT2 = """
You are a data analysis assistant.  
Your job is to:
1. Write Python code to solve these questions with provided metadata.
2. List all Python libraries that need to be installed for the code to run.
3. Also add code to save the result to "uploads/result.json" or any filetype you find suitable(eg. save img files like "uploads/img.png").

Do not include explanations, comments, or extra text outside the JSON.
"""

async def answer_with_data(question_text):
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
5. Don't add comments
6. Convert any image/visualisation if present, into base64 PNG and add it to the result.

You must respond **only** in valid JSON with these properties:

  "code": "string — Python scraping code as plain text",
  "libraries": ["string — names of required libraries"]


lastly follow answer format and save answer of questions in result as JSON file.
"""
    # Path to the file
    file_path = "uploads/result.json"

    # Create the folder if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Check if file exists
    if not os.path.exists(file_path):
        # Create an empty file
        with open(file_path, "w") as f:
            f.write("")  # optional, just ensures the file exists
        print("File created:", file_path)
    else:
        print("File already exists:", file_path)

    model = genai.GenerativeModel(MODEL_NAME)

    response = model.generate_content(
        [SYSTEM_PROMPT2, user_prompt],
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
    )

    return json.loads(response.text)




async def final_answer_from_results(question_file):

    with open("uploads/result.txt", "r") as file:
        result = file.read()

    user_prompt = f"""
reult_file:"{result}"

look at this and only take the format from it do nothing else what is asked in here: "{question_file}"

1. Convert it into a json that only contains the required answer accoring to the provided format.
"""

    model = genai.GenerativeModel(MODEL_NAME)

    response = model.generate_content(
        [user_prompt],
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
    )

    return json.loads(response.text)


