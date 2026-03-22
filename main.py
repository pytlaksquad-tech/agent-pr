from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build

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

# GOOGLE DRIVE
creds = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))

credentials = service_account.Credentials.from_service_account_info(
    creds,
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)

drive = build("drive", "v3", credentials=credentials)


@app.post("/analyze")
async def analyze(data: dict):
    code = data.get("code", "")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": code}
        ]
    )

    return {"review": response.choices[0].message.content}


@app.post("/drive")
async def drive_read(data: dict):
    folder_id = data.get("folder")

    results = drive.files().list(
        q=f"'{folder_id}' in parents",
        pageSize=5,
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])

    names = [f["name"] for f in files]

    return {"review": "Files: " + ", ".join(names)}
