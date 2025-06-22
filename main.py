from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
import asyncio

from create_agent import create_agent

# Create the agent workflow
workflow = create_agent()

# Define request schema
class QueryRequest(BaseModel):
    prompt: str
    google_uid: str  # can be used later if needed

# Initialize FastAPI app
app = FastAPI()

@app.post("/chat")
async def chat_endpoint(request: QueryRequest):
    response = await workflow.achat(request.prompt)
    return {"response": response.response}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
