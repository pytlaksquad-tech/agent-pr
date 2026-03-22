from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/analyze")
async def analyze(data: dict):
    code = data.get("code", "")

    if not code:
        return {"review": "No code provided"}

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a professional code reviewer."},
                {"role": "user", "content": code}
            ]
        )

        return {
            "review": response.choices[0].message.content
        }

    except Exception as e:
        return {"review": f"ERROR: {str(e)}"}
