from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from openai import OpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

creds_json = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))

credentials = service_account.Credentials.from_service_account_info(
    creds_json,
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)

drive_service = build("drive", "v3", credentials=credentials)


def read_file_content(file_id: str, mime_type: str) -> str:
    try:
        if mime_type == "application/vnd.google-apps.document":
            exported = drive_service.files().export(
                fileId=file_id,
                mimeType="text/plain"
            ).execute()
            return exported.decode("utf-8", errors="ignore")

        request = drive_service.files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(fd=None, request=request)
    except Exception:
        pass

    try:
        file_data = drive_service.files().get_media(fileId=file_id).execute()
        return file_data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


@app.get("/")
def root():
    return {"message": "AI PR Agent is running"}


@app.post("/analyze")
async def analyze(data: dict):
    code = data.get("code", "").strip()

    if not code:
        return {"review": "Please paste some code first."}

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a senior code reviewer. Give practical feedback on bugs, readability, structure, and improvements."
            },
            {
                "role": "user",
                "content": f"Review this code:\n\n{code}"
            }
        ]
    )

    return {"review": response.choices[0].message.content}


@app.post("/chat-folder")
async def chat_folder(data: dict):
    folder_id = data.get("folder_id", "").strip()
    question = data.get("question", "").strip()

    if not folder_id:
        return {"answer": "Please provide a Google Drive folder ID."}

    if not question:
        return {"answer": "Please provide a question."}

    try:
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            pageSize=20,
            fields="files(id, name, mimeType)"
        ).execute()

        files = results.get("files", [])

        if not files:
            return {"answer": "No files found in this folder or no access to the folder."}

        content = ""

        for file in files:
            file_id = file["id"]
            name = file["name"]
            mime_type = file.get("mimeType", "")

            text = read_file_content(file_id, mime_type)

            if text.strip():
                content += f"\n\nFILE: {name}\n{text[:5000]}"

        if not content.strip():
            return {"answer": "I could not read any readable text files from this folder."}

        prompt = f"""
Use the following folder documents to answer the question.

Documents:
{content}

Question:
{question}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Answer only using the provided Google Drive folder contents. If the answer is not in the documents, say that clearly."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return {"answer": response.choices[0].message.content}

    except Exception as e:
        return {"answer": f"ERROR: {str(e)}"}
