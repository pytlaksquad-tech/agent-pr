from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build

from openai import OpenAI

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google credentials
creds_json = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))

credentials = service_account.Credentials.from_service_account_info(
    creds_json,
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)

drive_service = build("drive", "v3", credentials=credentials)


@app.post("/chat-folder")
async def chat_folder(data: dict):
    folder_id = data.get("folder_id")
    question = data.get("question")

    # pobierz pliki z folderu
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents",
        pageSize=10,
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])

    content = ""

    for file in files:
        file_id = file["id"]
        name = file["name"]

        try:
            file_content = drive_service.files().get_media(fileId=file_id).execute()
            text = file_content.decode("utf-8", errors="ignore")
            content += f"\n\nFILE: {name}\n{text[:3000]}"
        except:
            continue

    prompt = f"""
Use the following documents to answer the question:

{content}

Question:
{question}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "answer": response.choices[0].message.content
    }
