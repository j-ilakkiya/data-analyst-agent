from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
from agent import handle_question

app = FastAPI()

@app.post("/api/")
async def upload_files(files: List[UploadFile] = File(...)):
    if not files:
        return JSONResponse(status_code=400, content={"error": "At least one file is required"})

    # Read all uploaded files into {filename: bytes}
    file_data = {}
    for f in files:
        file_data[f.filename] = await f.read()

    # Use first uploaded file as the question source
    first_file_name = list(file_data.keys())[0]
    question_text = file_data[first_file_name].decode("utf-8", errors="ignore")

    # Pass question + all files to the agent
    answers = await handle_question(question_text, file_data)

    return JSONResponse(content=answers)

