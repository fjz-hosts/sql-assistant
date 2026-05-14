"""导出模块测试"""
import pytest
import json
from sql_assistant.api.export import _convert_to_csv, _convert_to_json, _convert_to_excel

class TestExportFunctions:
    """导出功能测试"""
    
    def test_convert_to_csv(self):
        """测试转换为CSV格式"""
        columns = ["id", "name", "email"]
        rows = [
            [1, "Alice", "alice@example.com"],
            [2, "Bob", "bob@example.com"],
            [3, "Charlie", "charlie@example.com"]
        ]
        
        result = _convert_to_csv(columns, rows)
        assert result is not None
        assert isinstance(result, str)
        # 使用splitlines处理不同平台的换行符
        lines = result.strip().splitlines()
        assert len(lines) == 4
        assert lines[0].strip() == "id,name,email"
        assert "Alice" in lines[1]
    
    def test_convert_to_json(self):
        """测试转换为JSON格式"""
        columns = ["id", "name", "email"]
        rows = [
            [1, "Alice", "alice@example.com"],
            [2, "Bob", "bob@example.com"]
        ]
        
        result = _convert_to_json(columns, rows)
        assert result is not None
        assert isinstance(result, str)
        data = json.loads(result)
        assert "columns" in data
        assert "data" in data
        assert len(data["data"]) == 2
        assert data["data"][0]["name"] == "Alice"
    
    def test_convert_to_excel(self):
        """测试转换为Excel格式"""
        columns = ["id", "name", "email"]
        rows = [
            [1, "Alice", "alice@example.com"],
            [2, "Bob", "bob@example.com"]
        ]
        
        result = _convert_to_excel(columns, rows)
        assert result is not None
        assert isinstance(result, str)
        assert "<table" in result
        assert "<th>id</th>" in result
        assert "Alice" in result
    
    def test_convert_empty_data(self):
        """测试转换空数据"""
        columns = ["id", "name"]
        rows = []
        
        csv_result = _convert_to_csv(columns, rows)
        assert csv_result is not None
        assert "id,name" in csv_result
        
        json_result = _convert_to_json(columns, rows)
        assert json_result is not None
        data = json.loads(json_result)
        assert data["row_count"] == 0
    
    def test_convert_special_characters(self):
        """测试转换包含特殊字符的数据"""
        columns = ["name", "description"]
        rows = [
            ["Alice & Bob", 'Test description with "quotes"'],
            ["Charlie", "Line 1\nLine 2"]
        ]
        
        result = _convert_to_csv(columns, rows)
        assert result is not None
        assert '&' in result
