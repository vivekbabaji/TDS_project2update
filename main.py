from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
import os
import uuid

#from llm_parser import parse_question_with_llm, answer_with_data
from task_engine import run_python_code

from gemini import parse_question_with_llm, answer_with_data

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze(
    question: UploadFile = File(..., description="questions.txt file with tasks"),
    files: Optional[List[UploadFile]] = File(None, description="Optional data files (csv, image, etc.)"),
    urls: Optional[str] = Form(None, description="Optional comma-separated URLs")
):
    # Create a unique folder for this request
    request_id = str(uuid.uuid4())
    request_folder = os.path.join(UPLOAD_DIR, request_id)
    os.makedirs(request_folder, exist_ok=True)

    # ✅ 1. Read the question from uploaded file
    question_text = (await question.read()).decode("utf-8")

    # ✅ 2. Save any uploaded files
    saved_files = []
    if files:
        for file in files:
            file_path = os.path.join(request_folder, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            saved_files.append(file_path)

    # ✅ 3. Parse URL list
    url_list = [url.strip() for url in urls.split(",")] if urls else []

    # ✅ 4. Get code steps from LLM
    response = await parse_question_with_llm(
        question_text=question_text,
        uploaded_files=saved_files,
        urls=url_list,
        folder=request_folder
    )

    print(response)

    # ✅ 5. Execute generated code safely
    execution_result = await run_python_code(response["code"], response["libraries"], folder=request_folder)

    print(execution_result)

    count = 0
    while execution_result["code"] == 0 and count < 3:
        print(f"Error occured while scrapping x{count}")
        new_question_text = str(question_text) + "previous time this error occured" + str(execution_result["output"])
        response = await parse_question_with_llm(
            question_text=new_question_text,
            uploaded_files=saved_files,
            urls=url_list,
            folder=request_folder
        )

        print(response)

        execution_result = await run_python_code(response["code"], response["libraries"], folder=request_folder)

        print(execution_result)

        count += 1

    if execution_result["code"] == 1:
        execution_result = execution_result["output"]
    else:
        return JSONResponse({"message": "error occured while scrapping."})

    # 6. get answers from llm
    gpt_ans = await answer_with_data(response["questions"], folder=request_folder)

    print(gpt_ans)

    # 7. Executing code
    final_result = await run_python_code(gpt_ans["code"], gpt_ans["libraries"], folder=request_folder)

    print(final_result)

    count = 0
    while final_result["code"] == 0 and count < 3:
        print(f"Error occured while executing code x{count}")
        new_question_text = str(response["questions"]) + "previous time this error occured" + str(final_result["output"])
        gpt_ans = await answer_with_data(new_question_text, folder=request_folder)

        print(gpt_ans)

        final_result = await run_python_code(gpt_ans["code"], gpt_ans["libraries"], folder=request_folder)

        print(final_result)

        count += 1

    if final_result["code"] == 1:
        final_result = final_result["output"]
    else:
        result_path = os.path.join(request_folder, "result.json")
        with open(result_path, "r") as f:
            data = json.load(f)
        return JSONResponse(content=data)

    result_path = os.path.join(request_folder, "result.json")
    with open(result_path, "r") as f:
        data = json.load(f)
        return JSONResponse(content=data)
    
