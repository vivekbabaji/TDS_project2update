from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os

from llm_parser import parse_question_with_llm, answer_with_data
from task_engine import run_python_code

from gemini import ans_with_gemini

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze(
    question: UploadFile = File(..., description="questions.txt file with tasks"),
    files: Optional[List[UploadFile]] = File(None, description="Optional data files (csv, image, etc.)"),
    urls: Optional[str] = Form(None, description="Optional comma-separated URLs")
):
    # ✅ 1. Read the question from uploaded file
    question_text = (await question.read()).decode("utf-8")

    # ✅ 2. Save any uploaded files
    saved_files = []
    if files:
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            saved_files.append(file_path)

    # ✅ 3. Parse URL list
    url_list = [url.strip() for url in urls.split(",")] if urls else []

    # ✅ 4. Get code steps from LLM
    response = await parse_question_with_llm(
        question_text=question_text,
        uploaded_files=saved_files,
        urls=url_list
    )

    # ✅ 5. Execute generated code safely
    execution_result = await run_python_code(response["code"], response["libraries"])

    #6. get answers from llm
    gpt_ans = await answer_with_data(response["questions"])

    gemini_ans = ans_with_gemini(response["questions"])

    return JSONResponse({
        "question": question_text,
        "uploaded_files": saved_files,
        "urls": url_list,
        "generated_code": response,
        "output": execution_result,
        "answers_with_gpt": gpt_ans,
        "ans_with_gemini": gemini_ans

    })
