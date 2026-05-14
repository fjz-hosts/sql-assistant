"""导出相关 API 路由"""

import csv
import json
from datetime import datetime
from io import StringIO
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .models import ExportRequest, ExportResponse

router = APIRouter()


def _convert_to_csv(columns: List[str], rows: List[List[Any]]) -> str:
    """将数据转换为CSV格式"""
    output = StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow(columns)
    
    # 写入数据行
    for row in rows:
        writer.writerow([str(cell) if cell is not None else '' for cell in row])
    
    return output.getvalue()


def _convert_to_json(columns: List[str], rows: List[List[Any]]) -> str:
    """将数据转换为JSON格式"""
    data = []
    for row in rows:
        obj = {}
        for i, col in enumerate(columns):
            obj[col] = row[i]
        data.append(obj)
    
    result = {
        "export_time": datetime.now().isoformat(),
        "columns": columns,
        "row_count": len(rows),
        "data": data
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def _convert_to_excel(columns: List[str], rows: List[List[Any]]) -> str:
    """将数据转换为Excel格式（HTML表格方式）"""
    html = f'''
<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
<head>
    <meta charset="UTF-8">
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background: #f0f0f0; font-weight: bold; }}
    </style>
</head>
<body>
    <table>
        <thead>
            <tr>{''.join(f'<th>{col}</th>' for col in columns)}</tr>
        </thead>
        <tbody>
            {''.join(f'<tr>{''.join(f"<td>{str(cell) if cell is not None else ''}</td>" for cell in row)}</tr>' for row in rows)}
        </tbody>
    </table>
</body>
</html>'''
    return html


@router.post("/export", response_model=ExportResponse)
async def export_data(request: ExportRequest):
    """
    导出查询结果
    
    支持将查询结果导出为 CSV、JSON、Excel 格式。
    可用于前端无法处理的大数据量导出，或需要服务器端生成文件的场景。
    """
    try:
        if not request.columns or not request.rows:
            raise HTTPException(status_code=400, detail="导出数据不能为空")
        
        format_type = request.format.lower()
        
        if format_type == 'csv':
            content = _convert_to_csv(request.columns, request.rows)
            content_type = 'text/csv;charset=utf-8'
            filename = f'query_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        elif format_type == 'json':
            content = _convert_to_json(request.columns, request.rows)
            content_type = 'application/json;charset=utf-8'
            filename = f'query_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        elif format_type == 'excel':
            content = _convert_to_excel(request.columns, request.rows)
            content_type = 'application/vnd.ms-excel;charset=utf-8'
            filename = f'query_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {request.format}")
        
        return ExportResponse(
            success=True,
            format=format_type,
            content=content,
            content_type=content_type,
            filename=filename,
            row_count=len(request.rows)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/export/download")
async def export_download(request: ExportRequest):
    """
    导出查询结果并直接下载
    
    支持流式下载，适合大数据量导出。
    """
    try:
        if not request.columns or not request.rows:
            raise HTTPException(status_code=400, detail="导出数据不能为空")
        
        format_type = request.format.lower()
        
        if format_type == 'csv':
            content = _convert_to_csv(request.columns, request.rows)
            content_type = 'text/csv;charset=utf-8'
            filename = f'query_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        elif format_type == 'json':
            content = _convert_to_json(request.columns, request.rows)
            content_type = 'application/json;charset=utf-8'
            filename = f'query_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        elif format_type == 'excel':
            content = _convert_to_excel(request.columns, request.rows)
            content_type = 'application/vnd.ms-excel;charset=utf-8'
            filename = f'query_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {request.format}")
        
        # 添加 BOM 以支持 Excel 正确识别中文
        if format_type == 'csv':
            content = '\uFEFF' + content
        
        return StreamingResponse(
            iter([content]),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": content_type
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")