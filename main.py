from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import aiofiles
import json

from task_engine import run_python_code
from gemini import parse_question_with_llm, answer_with_data

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("frontend.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Helper funtion to show last 25 words of string s
def last_n_words(s, n=25):
    s = str(s)
    words = s.split()
    return ' '.join(words[-n:])


@app.post("/api")
async def analyze(request: Request):
    # Create a unique folder for this request
    request_id = str(uuid.uuid4())
    request_folder = os.path.join(UPLOAD_DIR, request_id)
    os.makedirs(request_folder, exist_ok=True)
    print("Step-1: Folder created: ", request_folder)

    form = await request.form()
    question_text = None
    saved_files = {}

    # Save all uploaded files to the request folder
    for field_name, value in form.items():
        if hasattr(value, "filename") and value.filename:  # It's a file
            file_path = os.path.join(request_folder, value.filename)
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(await value.read())
            saved_files[field_name] = file_path

            # If it's questions.txt, read its content
            if field_name == "questions.txt":
                async with aiofiles.open(file_path, "r") as f:
                    question_text = await f.read()
        else:
            saved_files[field_name] = value

    # Fallback: If no questions.txt, use the first file as question
    if question_text is None and saved_files:
        first_file = next(iter(saved_files.values()))
        async with aiofiles.open(first_file, "r") as f:
            question_text = await f.read()
    
    print("Step-2: File sent", saved_files)


    # ✅ 4. Get code steps from LLM

    max_attempts = 3
    attempt = 0
    response = None
    
    
    while attempt < max_attempts:
        print("Step-3: Getting scrap code and metadata from llm. Tries count = ", attempt)
        try:
            response = await parse_question_with_llm(
                question_text=question_text,
                uploaded_files=saved_files,
                folder=request_folder
            )
            # Check if response is a valid dict (parsed JSON)
            if isinstance(response, dict):
                break
        except Exception as e:
            question_text = question_text + str(e)
            print("Step-3: Error in parsing the result. ", last_n_words(question_text))
        attempt += 1


    if not isinstance(response, dict):
        return JSONResponse({"message": "Error: Could not get valid response from LLM after retries."})



    print("Step-3: Response from scrapping: ", last_n_words(response))

    # ✅ 5. Execute generated code safely
    execution_result = await run_python_code(response["code"], response["libraries"], folder=request_folder)

    print("Step-4: Execution result of the scrape code: ", last_n_words(execution_result["output"]))

    count = 0
    while execution_result["code"] == 0 and count < 3:
        print(f"Step-4: Error occured while scrapping. Tries count = {count}")
        new_question_text = str(question_text) + "previous time this error occured" + str(execution_result["output"])
        try:
            response = await parse_question_with_llm(
                question_text=new_question_text,
                uploaded_files=saved_files,
                folder=request_folder
            )
        except Exception as e:
            print("Step-4: error occured while reading json.", last_n_words(e))

        print("Step-3: Response from scrapping: ", last_n_words(response))

        execution_result = await run_python_code(response["code"], response["libraries"], folder=request_folder)

        print("Step-4: Execution result of the scrape code: ", last_n_words(execution_result["output"]))

        count += 1

    if execution_result["code"] == 1:
        execution_result = execution_result["output"]
    else:
        return JSONResponse({"message": "error occured while scrapping."})

    # 6. get answers from llm
    max_attempts = 3
    attempt = 0
    gpt_ans = None
    response_questions = response["questions"]

    while attempt < max_attempts:
        print("Step-5: Getting execution code from llm. Tries count = ", attempt)
        try:
            gpt_ans = await answer_with_data(response_questions, folder=request_folder)
            print("Step-5: Response from llm: ",last_n_words(gpt_ans["code"]))
            if isinstance(gpt_ans, dict):
                break
        except Exception as e:
            print(f"Step-5: Error: {e}")
            response_questions += str(e)
        attempt += 1
    
    if not isinstance(gpt_ans, dict):
        return JSONResponse({"message": "Error: Could not get valid response from answer_with_data after retries."})
    
    # 7. Executing code
    try:
        print("Step-6: Executing final code. Tries count = 0")
        final_result = await run_python_code(gpt_ans["code"], gpt_ans["libraries"], folder=request_folder)
        print("Step-6: Executing final code result: ", last_n_words(final_result["output"]))
    except Exception as e:
        print("Step-6: Trying after it caught under except block-wrong json format. Tries count = 1", last_n_words(e))
        print("Step-5: Getting execution code from llm. Tries count = ", attempt+1)
        gpt_ans = await answer_with_data(str(response["questions"])+str("Please follow the json structure"), folder=request_folder)
        print("Step-5: Response from llm: ",last_n_words(gpt_ans["code"]))
        final_result = await run_python_code(gpt_ans["code"], gpt_ans["libraries"], folder=request_folder)
        print("Step-6: Executing final code result: ", last_n_words(final_result["output"]))
        

    count = 0
    json_str = 1
    while final_result["code"] == 0 and count < 3:
        print(f"Step-6: Error occured while executing code. Tries count = {count+2}")
        new_question_text = str(response["questions"]) + "previous time this error occured" + str(final_result["output"])
        if json_str == 0:
            new_question_text += "follow the structure {'code': '', 'libraries': ''}"
        print("Step-5: Getting execution code from llm. Tries count = ", attempt+1)
        try:
            gpt_ans = await answer_with_data(new_question_text, folder=request_folder)
            print("Step-5: Response from llm: ",last_n_words(gpt_ans["code"]))
        except Exception as e:
            print("Step-5: Json parsing error.", last_n_words(e))
        try:
            json_str = 0
            final_result = await run_python_code(gpt_ans["code"], gpt_ans["libraries"], folder=request_folder)
            print("Step-6: Executing final code result: ", last_n_words(final_result["output"]))
            json_str = 1
        except Exception as e:
            print(f"Exception occurred: {e}")
            count -= 1

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
        try:
            data = json.load(f)
            print("Step-7: send result back")
            return JSONResponse(content=data)
        except Exception as e:
            print("Step-7: Error occur while sending result: ", last_n_words(e))
            return JSONResponse({"message": f"Error occured while processing reult.json: {e}"})
        
    
