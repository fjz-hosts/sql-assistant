"""数据洞察 API 路由"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from ..database.manager import get_db_manager
from ..database.insights import DatabaseInsightsManager, DataSummary, OutlierDetection, TrendAnalysis, InsightReport

router = APIRouter(prefix="/insights")


@router.get("/summary/{table_name}", response_model=DataSummary, tags=["数据洞察"])
async def get_table_summary(
    table_name: str,
    sample_size: Optional[int] = 100,
    db=Depends(get_db_manager)
):
    """获取表数据摘要"""
    try:
        connector = await db.get_connector()
        insights_manager = DatabaseInsightsManager(connector)
        summary = await insights_manager.generate_summary(table_name, sample_size)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outliers/{table_name}/{column_name}", response_model=OutlierDetection, tags=["数据洞察"])
async def detect_outliers(
    table_name: str,
    column_name: str,
    method: Optional[str] = "zscore",
    threshold: Optional[float] = 3.0,
    db=Depends(get_db_manager)
):
    """检测指定列的异常值"""
    try:
        connector = await db.get_connector()
        insights_manager = DatabaseInsightsManager(connector)
        result = await insights_manager.detect_outliers(table_name, column_name, method, threshold)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend/{table_name}/{column_name}", response_model=TrendAnalysis, tags=["数据洞察"])
async def analyze_trend(
    table_name: str,
    column_name: str,
    date_column: Optional[str] = None,
    db=Depends(get_db_manager)
):
    """分析数据趋势"""
    try:
        connector = await db.get_connector()
        insights_manager = DatabaseInsightsManager(connector)
        result = await insights_manager.analyze_trends(table_name, column_name, date_column)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{table_name}", response_model=InsightReport, tags=["数据洞察"])
async def generate_report(
    table_name: str,
    db=Depends(get_db_manager)
):
    """生成完整的数据洞察报告"""
    try:
        connector = await db.get_connector()
        insights_manager = DatabaseInsightsManager(connector)
        report = await insights_manager.generate_insight_report(table_name)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables", tags=["数据洞察"])
async def get_available_tables(db=Depends(get_db_manager)):
    """获取可用数据表列表"""
    try:
        schema = await db.get_schema()
        tables = schema.get("tables", [])
        return {
            "tables": [{"name": t["name"], "columns": [c["name"] for c in t.get("columns", [])]} for t in tables],
            "db_type": schema.get("db_type", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))