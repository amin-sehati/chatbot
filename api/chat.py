from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

app = FastAPI()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


@app.post("/")
async def chat(req: ChatRequest):
    model = ChatOpenAI(model="gpt-4o-mini")
    history: list[HumanMessage | AIMessage | SystemMessage] = []
    for m in req.messages:
        if m.role == "system":
            history.append(SystemMessage(content=m.content))
        elif m.role == "user":
            history.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            history.append(AIMessage(content=m.content))
    ai = await model.ainvoke(history)
    return Response(content=ai.content, media_type="text/plain")
