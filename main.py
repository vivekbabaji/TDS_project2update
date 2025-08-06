from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import json

from llm_parser import parse_question_with_llm

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze(
    question: UploadFile = File(..., description="questions.txt file with tasks"),
    files: Optional[List[UploadFile]] = File(None, description="Optional data files (csv, image, etc.)"),
    urls: Optional[str] = Form(None, description="Optional comma-separated URLs")
):
    # ✅ 1. Read questions.txt
    question_text = (await question.read()).decode("utf-8")

    # ✅ 2. Save uploaded files (optional)
    saved_files = []
    if files:
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            saved_files.append(file_path)

    # ✅ 3. Parse URLs (optional)
    url_list = [url.strip() for url in urls.split(",")] if urls else []

    # ✅ 4. Use LLM to analyze the question
    try:
        llm_response = await parse_question_with_llm(question_text)
        try:
            llm_steps = json.loads(llm_response)  # Try parsing JSON
        except Exception:
            llm_steps = llm_response  # Just keep raw string if not JSON
    except Exception as e:
        llm_steps = f"LLM failed: {str(e)}"

    # ✅ 5. Return everything
    return JSONResponse({
        "message": "Input received successfully.",
        "question": question_text,
        "uploaded_files": saved_files,
        "urls": url_list,
        "llm_steps": llm_steps
    })
