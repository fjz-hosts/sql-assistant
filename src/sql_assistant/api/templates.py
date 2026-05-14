"""模板相关 API 路由"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from .dependencies import get_template_manager
from .models import TemplateRequest, TemplateResponse, TemplateListResponse

router = APIRouter()


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(limit: int = 50, offset: int = 0, tag: Optional[str] = None):
    """获取模板列表"""
    manager = get_template_manager()
    templates = await manager.get_templates(limit=limit, offset=offset, tag=tag)
    total = await manager.get_count(tag=tag)
    return TemplateListResponse(
        templates=[TemplateResponse(**t) for t in templates],
        total=total,
    )


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int):
    """获取单个模板"""
    manager = get_template_manager()
    template = await manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return TemplateResponse(**template)


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(request: TemplateRequest):
    """创建新模板"""
    manager = get_template_manager()
    template_id = await manager.create_template(
        name=request.name,
        description=request.description or "",
        sql=request.sql,
        tags=request.tags or []
    )
    template = await manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=500, detail="创建模板失败")
    return TemplateResponse(**template)


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: int, request: TemplateRequest):
    """更新模板"""
    manager = get_template_manager()
    if not await manager.update_template(
        template_id,
        name=request.name,
        description=request.description or "",
        sql=request.sql,
        tags=request.tags or []
    ):
        raise HTTPException(status_code=404, detail="模板不存在")
    template = await manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=500, detail="获取模板失败")
    return TemplateResponse(**template)


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int):
    """删除模板"""
    manager = get_template_manager()
    if not await manager.delete_template(template_id):
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"ok": True}


@router.get("/templates/tags")
async def get_tags():
    """获取所有标签"""
    manager = get_template_manager()
    tags = await manager.get_all_tags()
    return {"tags": tags}