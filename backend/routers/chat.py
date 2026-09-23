from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from openai import AsyncOpenAI
from fastapi.responses import StreamingResponse

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
    client = AsyncOpenAI(api_key=api_key)
    
    # We use a simple system prompt. In a real app, you would inject Overpass API data here.
    system_prompt = {
        "role": "system",
        "content": "You are MediConnect AI, a medical assistant. Always give a medical disclaimer."
    }
    
    messages_payload = [system_prompt] + [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_payload,
            stream=True
        )
        
        async def stream_generator():
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield f"0:{repr(content)}\n"
                    
        return StreamingResponse(stream_generator(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
