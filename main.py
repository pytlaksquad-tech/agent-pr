from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CodeRequest(BaseModel):
    code: str

class FolderRequest(BaseModel):
    folder_id: str
    question: str

def get_drive_service():
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_dict = json.loads(creds_json)

    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )

    return build("drive", "v3", credentials=creds)

@app.get("/")
def root():
    return {"message": "AI Agent is running"}

@app.post("/analyze")
def analyze(req: CodeRequest):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior code reviewer."},
            {"role": "user", "content": req.code}
        ]
    )

    return {"review": response.choices[0].message.content}

@app.post("/chat-folder")
def chat_folder(req: FolderRequest):
    try:
        service = get_drive_service()

        results = service.files().list(
            q=f"'{req.folder_id}' in parents and trashed=false",
            pageSize=20,
            fields="files(id, name)"
        ).execute()

        files = results.get("files", [])

        if not files:
            return {"answer": "Folder is empty or no access."}

        file_names = [f["name"] for f in files]

        return {
            "answer": f"Files in folder: {', '.join(file_names)}"
        }

    except Exception as e:
        return {"answer": str(e)}
