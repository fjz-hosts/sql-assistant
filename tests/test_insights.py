"""测试数据洞察模块"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.sql_assistant.database.insights import (
    DatabaseInsightsManager,
    DataSummary,
    OutlierDetection,
    TrendAnalysis,
    InsightReport
)


class TestDataSummary:
    """测试数据摘要数据类"""

    def test_data_summary_defaults(self):
        """测试数据摘要默认值"""
        summary = DataSummary(table_name="test_table")
        
        assert summary.table_name == "test_table"
        assert summary.row_count == 0
        assert summary.column_count == 0
        assert summary.columns == []
        assert summary.sample_rows == []
        assert summary.column_types == {}
        assert summary.null_rates == {}
        assert summary.summary_stats == {}

    def test_data_summary_with_data(self):
        """测试数据摘要带数据"""
        summary = DataSummary(
            table_name="test_table",
            row_count=1000,
            column_count=5,
            columns=["id", "name", "age", "email", "created_at"],
            column_types={"id": "int", "name": "varchar", "age": "int"},
            null_rates={"email": 0.1, "age": 0.05}
        )
        
        assert summary.row_count == 1000
        assert summary.column_count == 5
        assert "id" in summary.columns
        assert summary.column_types["name"] == "varchar"
        assert summary.null_rates["email"] == 0.1


class TestOutlierDetection:
    """测试异常检测数据类"""

    def test_outlier_detection_defaults(self):
        """测试异常检测默认值"""
        outlier = OutlierDetection(table_name="test_table", column_name="value")
        
        assert outlier.table_name == "test_table"
        assert outlier.column_name == "value"
        assert outlier.outlier_count == 0
        assert outlier.outliers == []
        assert outlier.detection_method == ""
        assert outlier.threshold == 0.0

    def test_outlier_detection_with_data(self):
        """测试异常检测带数据"""
        outlier = OutlierDetection(
            table_name="test_table",
            column_name="value",
            outlier_count=5,
            outliers=[{"value": 100.5}, {"value": -50.0}],
            detection_method="zscore",
            threshold=3.0
        )
        
        assert outlier.outlier_count == 5
        assert len(outlier.outliers) == 2
        assert outlier.detection_method == "zscore"


class TestTrendAnalysis:
    """测试趋势分析数据类"""

    def test_trend_analysis_defaults(self):
        """测试趋势分析默认值"""
        trend = TrendAnalysis(table_name="test_table", column_name="value")
        
        assert trend.table_name == "test_table"
        assert trend.column_name == "value"
        assert trend.trend_type == ""
        assert trend.trend_score == 0.0
        assert trend.data_points == []
        assert trend.prediction is None

    def test_trend_analysis_with_data(self):
        """测试趋势分析带数据"""
        trend = TrendAnalysis(
            table_name="test_table",
            column_name="value",
            trend_type="increasing",
            trend_score=0.8,
            prediction=100.5
        )
        
        assert trend.trend_type == "increasing"
        assert trend.trend_score == 0.8
        assert trend.prediction == 100.5


class TestDatabaseInsightsManager:
    """测试数据库洞察管理器"""

    @pytest.fixture
    def mock_connector(self):
        """创建模拟连接器"""
        connector = Mock()
        connector.db_type = "mysql"
        connector.execute = AsyncMock()
        connector.get_schema = AsyncMock()
        return connector

    @pytest.mark.asyncio
    async def test_calculate_null_rates(self, mock_connector):
        """测试空值率计算"""
        manager = DatabaseInsightsManager(mock_connector)
        
        sample_rows = [
            {"id": 1, "name": "Alice", "email": None},
            {"id": 2, "name": None, "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ]
        columns = ["id", "name", "email"]
        
        null_rates = manager._calculate_null_rates(sample_rows, columns)
        
        assert null_rates["id"] == 0.0
        assert null_rates["name"] == pytest.approx(1/3, 0.01)
        assert null_rates["email"] == pytest.approx(1/3, 0.01)

    @pytest.mark.asyncio
    async def test_calculate_summary_stats(self, mock_connector):
        """测试统计摘要计算"""
        manager = DatabaseInsightsManager(mock_connector)
        
        sample_rows = [
            {"value": 10, "score": 5},
            {"value": 20, "score": 8},
            {"value": 30, "score": 12},
        ]
        columns = ["value", "score"]
        
        stats = manager._calculate_summary_stats(sample_rows, columns)
        
        assert "value" in stats
        assert stats["value"]["min"] == 10
        assert stats["value"]["max"] == 30
        assert stats["value"]["avg"] == 20
        assert stats["value"]["count"] == 3

    @pytest.mark.asyncio
    async def test_detect_zscore_outliers(self, mock_connector):
        """测试Z-score异常检测"""
        manager = DatabaseInsightsManager(mock_connector)
        
        values = [1, 2, 3, 4, 5, 100]
        
        outliers = manager._detect_zscore_outliers(values, threshold=2.0)
        
        assert 100 in outliers

    @pytest.mark.asyncio
    async def test_detect_iqr_outliers(self, mock_connector):
        """测试IQR异常检测"""
        manager = DatabaseInsightsManager(mock_connector)
        
        values = [1, 2, 3, 4, 5, 100]
        
        outliers = manager._detect_iqr_outliers(values)
        
        assert 100 in outliers

    @pytest.mark.asyncio
    async def test_calculate_trend_score(self, mock_connector):
        """测试趋势分数计算"""
        manager = DatabaseInsightsManager(mock_connector)
        
        # 上升趋势
        increasing_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        score = manager._calculate_trend_score(increasing_values)
        assert score > 0.5
        
        # 下降趋势
        decreasing_values = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        score = manager._calculate_trend_score(decreasing_values)
        assert score < -0.5
        
        # 稳定趋势
        stable_values = [5, 5, 6, 5, 5, 6, 5, 5, 5, 6]
        score = manager._calculate_trend_score(stable_values)
        assert abs(score) < 0.31

    @pytest.mark.asyncio
    async def test_simple_prediction(self, mock_connector):
        """测试简单预测"""
        manager = DatabaseInsightsManager(mock_connector)
        
        values = [1, 2, 3, 4, 5]
        prediction = manager._simple_prediction(values)
        
        assert prediction == 6.0

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, mock_connector):
        """测试建议生成"""
        manager = DatabaseInsightsManager(mock_connector)
        
        report = InsightReport(
            summary=DataSummary(
                table_name="test",
                row_count=2000000,
                null_rates={"email": 0.4}
            ),
            outliers=[OutlierDetection(
                table_name="test",
                column_name="value",
                outlier_count=10
            )],
            trends=[TrendAnalysis(
                table_name="test",
                column_name="sales",
                trend_type="increasing",
                trend_score=0.7,
                prediction=1000.0
            )],
            recommendations=[],
            generated_at="2024-01-01 00:00:00"
        )
        
        recommendations = manager._generate_recommendations(report)
        
        assert len(recommendations) > 0
        assert any("空值率" in r for r in recommendations)
        assert any("异常值" in r for r in recommendations)
        assert any("上升趋势" in r for r in recommendations)
        assert any("数据量较大" in r for r in recommendations)