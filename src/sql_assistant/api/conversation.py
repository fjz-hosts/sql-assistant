"""对话相关 API 路由"""

from fastapi import APIRouter, HTTPException

from .dependencies import get_history
from .models import (
    ConversationRequest, ConversationResponse, ConversationDetailResponse,
    ConversationListResponse, ConversationUpdateRequest, HistoryRecord,
)

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(req: ConversationRequest):
    history = get_history()
    conversation_id = await history.create_conversation(title=req.title)
    conversation = await history.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=500, detail="创建对话失败")
    return ConversationResponse(**conversation)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(limit: int = 50, offset: int = 0):
    history = get_history()
    conversations = await history.get_conversations(limit=limit, offset=offset)
    total = await history.get_conversation_count()
    return ConversationListResponse(
        conversations=[ConversationResponse(**c) for c in conversations],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(conversation_id: int):
    history = get_history()
    conversation = await history.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = await history.get_conversation_messages(conversation_id)
    return ConversationDetailResponse(
        id=conversation["id"],
        title=conversation["title"],
        created_at=conversation.get("created_at", ""),
        updated_at=conversation.get("updated_at", ""),
        messages=[HistoryRecord(**m) for m in messages],
    )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: int, req: ConversationUpdateRequest):
    history = get_history()
    if not await history.update_conversation(conversation_id, req.title):
        raise HTTPException(status_code=404, detail="对话不存在")

    conversation = await history.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=500, detail="获取对话失败")
    return ConversationResponse(**conversation)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    history = get_history()
    if not await history.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"ok": True}