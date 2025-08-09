from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
from agent import handle_question
import traceback

app = FastAPI()

@app.post("/api/")
async def upload_files(files: List[UploadFile] = File(...)):
    if not files:
        return JSONResponse(status_code=400, content={"error": "At least one file is required"})

    file_data = {}
    for f in files:
        file_data[f.filename] = await f.read()

    first_file_name = list(file_data.keys())[0]
    question_text = file_data[first_file_name].decode("utf-8", errors="ignore")

    try:
        answers = await handle_question(question_text, file_data)
        return JSONResponse(content=answers)
    except Exception as e:
        # Log error stack trace for debugging
        error_trace = traceback.format_exc()
        print("Error in handle_question:", error_trace)
        return JSONResponse(status_code=500, content={"error": "Internal server error", "details": str(e)})



