from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PRRequest(BaseModel):
    code: str

@app.get("/")
def read_root():
    return {"message": "AI PR Agent is running 🚀"}

@app.post("/analyze")
def analyze_pr(request: PRRequest):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior code reviewer."},
            {"role": "user", "content": f"Review this code:\n{request.code}"}
        ]
    )

    return {"review": response.choices[0].message.content}
