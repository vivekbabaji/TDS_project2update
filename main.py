from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
import os

#from llm_parser import parse_question_with_llm, answer_with_data
from task_engine import run_python_code

from gemini import parse_question_with_llm, answer_with_data, final_answer_from_results

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze(
    question: UploadFile = File(..., description="questions.txt file with tasks"),
    files: Optional[List[UploadFile]] = File(None, description="Optional data files (csv, image, etc.)"),
    urls: Optional[str] = Form(None, description="Optional comma-separated URLs")
):
    
    # remove the files that are of previous questions

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

    
    # Checks if there is no problem while scrapping data.
    count = 0
    while execution_result["code"] == 0 and count < 3:
        print(f"Error occured while scrapping x{count}")
        new_question_text = str(question_text) + "previous time this error occured" + str(execution_result["output"])
        response = await parse_question_with_llm(
            question_text=new_question_text,
            uploaded_files=saved_files,
            urls=url_list
        )
        execution_result = await run_python_code(response["code"], response["libraries"])
        count += 1
    
    if execution_result["code"] == 1:
        execution_result = execution_result["output"]
    else:
        return JSONResponse({"message": "error occured while scrapping."}) 


    #6. get answers from llm
    gpt_ans = await answer_with_data(response["questions"])

    #7. Executing code
    final_result = await run_python_code(gpt_ans["code"], gpt_ans["libraries"])

    # Checks if there is no problem while executing code.
    count = 0
    while final_result["code"] == 0 and count < 3:
        print(f"Error occured while executing code x{count}")
        new_question_text = str(response["questions"]) + "previous time this error occured" + str(final_result["output"])
        gpt_ans = await answer_with_data(new_question_text)
        final_result = await run_python_code(gpt_ans["code"], gpt_ans["libraries"])
        count += 1
    
    if final_result["code"] == 1:
        final_result = final_result["output"]
    else:
        with open("uploads/result.json", "r") as f:
            data = json.load(f)
        return JSONResponse(content=data)


    #8. json result
    #json_result = await final_answer_from_results(question_text)


    #gemini_ans = ans_with_gemini(response["questions"])

    with open("uploads/result.json", "r") as f:
        data = json.load(f)
        return JSONResponse(content=data)

        ##return JSONResponse({
        #"question": question_text,
        #"uploaded_files": saved_files,
        #"urls": url_list,
        #"generated_code": response,
        #"output": execution_result,
        #"answers_with_gpt": gpt_ans,
        #"final_result": final_result

        ##"ans_with_gemini": gemini_ans

        #  })
