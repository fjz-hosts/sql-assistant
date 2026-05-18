"""数据库数据洞察模块"""

from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta

from .connectors.base import BaseConnector


@dataclass
class DataSummary:
    """数据摘要信息"""
    table_name: str
    row_count: int = 0
    column_count: int = 0
    columns: List[str] = None
    sample_rows: List[dict] = None
    column_types: Dict[str, str] = None
    null_rates: Dict[str, float] = None
    summary_stats: Dict[str, dict] = None

    def __post_init__(self):
        if self.columns is None:
            self.columns = []
        if self.sample_rows is None:
            self.sample_rows = []
        if self.column_types is None:
            self.column_types = {}
        if self.null_rates is None:
            self.null_rates = {}
        if self.summary_stats is None:
            self.summary_stats = {}


@dataclass
class OutlierDetection:
    """异常检测结果"""
    table_name: str
    column_name: str
    outlier_count: int = 0
    outliers: List[dict] = None
    detection_method: str = ""
    threshold: float = 0.0

    def __post_init__(self):
        if self.outliers is None:
            self.outliers = []


@dataclass
class TrendDataPoint:
    """趋势数据点"""
    timestamp: str
    value: float


@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    table_name: str
    column_name: str
    trend_type: str = ""  # increasing, decreasing, stable, seasonal
    trend_score: float = 0.0  # -1 to 1
    data_points: List[TrendDataPoint] = None
    prediction: Optional[float] = None

    def __post_init__(self):
        if self.data_points is None:
            self.data_points = []


@dataclass
class InsightReport:
    """洞察报告"""
    summary: DataSummary
    outliers: List[OutlierDetection]
    trends: List[TrendAnalysis]
    recommendations: List[str]
    generated_at: str = ""


class DatabaseInsightsManager:
    """数据库洞察管理器"""

    def __init__(self, connector: BaseConnector):
        self.connector = connector

    async def generate_summary(self, table_name: str, sample_size: int = 100) -> DataSummary:
        """生成数据表摘要"""
        summary = DataSummary(table_name=table_name)

        try:
            # 获取表结构
            schema = await self.connector.get_schema()
            tables = schema.get("tables", [])
            table_info = next((t for t in tables if t["name"] == table_name), None)

            if table_info:
                summary.columns = [c["name"] for c in table_info.get("columns", [])]
                summary.column_count = len(summary.columns)
                summary.column_types = {c["name"]: c["type"] for c in table_info.get("columns", [])}

            # 获取行数
            row_count_result = await self._get_row_count(table_name)
            summary.row_count = row_count_result

            # 获取样本数据
            sample_result = await self._get_sample_data(table_name, sample_size)
            summary.sample_rows = sample_result

            # 计算空值率
            if summary.sample_rows:
                summary.null_rates = self._calculate_null_rates(summary.sample_rows, summary.columns)

            # 计算统计摘要
            summary.summary_stats = self._calculate_summary_stats(summary.sample_rows, summary.columns)

        except Exception as e:
            pass

        return summary

    async def detect_outliers(self, table_name: str, column_name: str, method: str = "zscore", threshold: float = 3.0) -> OutlierDetection:
        """检测异常值"""
        outlier_result = OutlierDetection(
            table_name=table_name,
            column_name=column_name,
            detection_method=method,
            threshold=threshold
        )

        try:
            sample_data = await self._get_sample_data(table_name, 500)
            if not sample_data:
                return outlier_result

            # 提取数值列数据
            values = []
            for row in sample_data:
                if column_name in row and row[column_name] is not None:
                    try:
                        values.append(float(row[column_name]))
                    except (ValueError, TypeError):
                        continue

            if len(values) < 2:
                return outlier_result

            # 使用Z-score方法检测异常
            if method == "zscore":
                outliers = self._detect_zscore_outliers(values, threshold)
            else:
                outliers = self._detect_iqr_outliers(values)

            outlier_result.outlier_count = len(outliers)
            outlier_result.outliers = [{"value": v} for v in outliers]

        except Exception as e:
            pass

        return outlier_result

    async def analyze_trends(self, table_name: str, column_name: str, date_column: str = None) -> TrendAnalysis:
        """分析数据趋势"""
        trend = TrendAnalysis(table_name=table_name, column_name=column_name)

        try:
            # 获取时间序列数据
            if date_column:
                time_data = await self._get_time_series_data(table_name, date_column, column_name)
            else:
                time_data = await self._get_sample_data(table_name, 100)

            if not time_data:
                return trend

            # 提取数值
            values = []
            for row in time_data:
                if column_name in row and row[column_name] is not None:
                    try:
                        values.append(float(row[column_name]))
                    except (ValueError, TypeError):
                        continue

            if len(values) < 10:
                trend.trend_type = "stable"
                trend.trend_score = 0.0
                return trend

            # 计算趋势
            trend_score = self._calculate_trend_score(values)
            trend.trend_score = trend_score
            trend.data_points = [TrendDataPoint(timestamp=str(i), value=v) for i, v in enumerate(values)]

            if trend_score > 0.3:
                trend.trend_type = "increasing"
            elif trend_score < -0.3:
                trend.trend_type = "decreasing"
            else:
                trend.trend_type = "stable"

            # 简单预测下一个值
            if len(values) >= 5:
                trend.prediction = self._simple_prediction(values)

        except Exception as e:
            pass

        return trend

    async def generate_insight_report(self, table_name: str) -> InsightReport:
        """生成完整的洞察报告"""
        report = InsightReport(
            summary=DataSummary(table_name=table_name),
            outliers=[],
            trends=[],
            recommendations=[],
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # 生成数据摘要
        report.summary = await self.generate_summary(table_name)

        # 检测数值列的异常值
        numeric_columns = [
            col for col, col_type in report.summary.column_types.items()
            if any(t in col_type.lower() for t in ["int", "float", "decimal", "double", "number"])
        ]

        for col in numeric_columns[:3]:  # 最多检测3列
            outlier = await self.detect_outliers(table_name, col)
            if outlier.outlier_count > 0:
                report.outliers.append(outlier)

        # 分析趋势（使用第一个日期列）
        date_columns = [
            col for col, col_type in report.summary.column_types.items()
            if any(t in col_type.lower() for t in ["date", "time", "timestamp"])
        ]

        for col in numeric_columns[:2]:  # 最多分析2列
            if date_columns:
                trend = await self.analyze_trends(table_name, col, date_columns[0])
            else:
                trend = await self.analyze_trends(table_name, col)
            report.trends.append(trend)

        # 生成建议
        report.recommendations = self._generate_recommendations(report)

        return report

    async def _get_row_count(self, table_name: str) -> int:
        """获取表行数"""
        db_type = self.connector.db_type.lower()

        if db_type == "mysql":
            sql = f"SELECT COUNT(*) FROM `{table_name}`"
        elif db_type == "postgresql":
            sql = f"SELECT COUNT(*) FROM \"{table_name}\""
        elif db_type == "sqlserver":
            sql = f"SELECT COUNT(*) FROM [{table_name}]"
        else:
            return 0

        try:
            result = await self.connector.execute(sql)
            if result and result.rows:
                return result.rows[0][0] if isinstance(result.rows[0], (list, tuple)) else result.rows[0]
        except Exception:
            pass

        return 0

    async def _get_sample_data(self, table_name: str, limit: int = 100) -> List[dict]:
        """获取样本数据"""
        db_type = self.connector.db_type.lower()

        if db_type == "mysql":
            sql = f"SELECT * FROM `{table_name}` LIMIT {limit}"
        elif db_type == "postgresql":
            sql = f"SELECT * FROM \"{table_name}\" LIMIT {limit}"
        elif db_type == "sqlserver":
            sql = f"SELECT TOP {limit} * FROM [{table_name}]"
        else:
            return []

        try:
            result = await self.connector.execute(sql)
            if result and result.rows and result.columns:
                return [dict(zip(result.columns, row)) for row in result.rows]
        except Exception:
            pass

        return []

    async def _get_time_series_data(self, table_name: str, date_column: str, value_column: str) -> List[dict]:
        """获取时间序列数据"""
        db_type = self.connector.db_type.lower()

        if db_type == "mysql":
            sql = f"""
                SELECT {date_column}, AVG({value_column}) as avg_value
                FROM `{table_name}`
                GROUP BY DATE({date_column})
                ORDER BY {date_column}
                LIMIT 30
            """
        elif db_type == "postgresql":
            sql = f"""
                SELECT {date_column}, AVG({value_column}) as avg_value
                FROM "{table_name}"
                GROUP BY DATE_TRUNC('day', {date_column})
                ORDER BY {date_column}
                LIMIT 30
            """
        elif db_type == "sqlserver":
            sql = f"""
                SELECT CONVERT(date, {date_column}) as dt, AVG({value_column}) as avg_value
                FROM [{table_name}]
                GROUP BY CONVERT(date, {date_column})
                ORDER BY dt
                OFFSET 0 ROWS FETCH NEXT 30 ROWS ONLY
            """
        else:
            return []

        try:
            result = await self.connector.execute(sql)
            if result and result.rows and result.columns:
                return [dict(zip(result.columns, row)) for row in result.rows]
        except Exception:
            pass

        return []

    def _calculate_null_rates(self, sample_rows: List[dict], columns: List[str]) -> Dict[str, float]:
        """计算各列空值率"""
        null_rates = {}
        total_rows = len(sample_rows)

        if total_rows == 0:
            return null_rates

        for col in columns:
            null_count = sum(1 for row in sample_rows if row.get(col) is None)
            null_rates[col] = round(null_count / total_rows, 4)

        return null_rates

    def _calculate_summary_stats(self, sample_rows: List[dict], columns: List[str]) -> Dict[str, dict]:
        """计算统计摘要"""
        stats = {}

        for col in columns:
            values = []
            for row in sample_rows:
                if row.get(col) is not None:
                    try:
                        values.append(float(row[col]))
                    except (ValueError, TypeError):
                        continue

            if values:
                stats[col] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values),
                    "unique": len(set(values))
                }

        return stats

    def _detect_zscore_outliers(self, values: List[float], threshold: float = 3.0) -> List[float]:
        """使用Z-score检测异常值"""
        import math

        if len(values) < 2:
            return []

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return []

        outliers = [v for v in values if abs((v - mean) / std_dev) > threshold]
        return outliers

    def _detect_iqr_outliers(self, values: List[float]) -> List[float]:
        """使用IQR方法检测异常值"""
        if len(values) < 2:
            return []

        sorted_values = sorted(values)
        n = len(sorted_values)
        q1 = sorted_values[n // 4]
        q3 = sorted_values[3 * n // 4]
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = [v for v in values if v < lower_bound or v > upper_bound]
        return outliers

    def _calculate_trend_score(self, values: List[float]) -> float:
        """计算趋势分数"""
        if len(values) < 2:
            return 0.0

        # 使用线性回归计算趋势
        n = len(values)
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * v for i, v in enumerate(values))
        sum_x2 = sum(i * i for i in range(n))

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator

        # 归一化斜率
        value_range = max(values) - min(values) if max(values) != min(values) else 1
        normalized_slope = slope / (value_range / n)

        return max(-1.0, min(1.0, normalized_slope))

    def _simple_prediction(self, values: List[float]) -> float:
        """简单预测下一个值"""
        if len(values) < 2:
            return None

        # 使用最后几个值的趋势进行预测
        recent = values[-5:] if len(values) >= 5 else values
        slope = (recent[-1] - recent[0]) / (len(recent) - 1)

        return round(recent[-1] + slope, 2)

    def _generate_recommendations(self, report: InsightReport) -> List[str]:
        """生成建议"""
        recommendations = []

        # 空值率高的列
        for col, rate in report.summary.null_rates.items():
            if rate > 0.3:
                recommendations.append(f"⚠️ 列 `{col}` 的空值率较高 ({rate:.1%})，建议检查数据完整性")

        # 异常值检测
        for outlier in report.outliers:
            if outlier.outlier_count > 0:
                recommendations.append(f"🔍 在 `{outlier.column_name}` 列中检测到 {outlier.outlier_count} 个异常值")

        # 趋势分析建议
        for trend in report.trends:
            if trend.trend_type == "increasing":
                recommendations.append(f"📈 `{trend.column_name}` 列呈现上升趋势，增长率: {trend.trend_score:.1%}")
            elif trend.trend_type == "decreasing":
                recommendations.append(f"📉 `{trend.column_name}` 列呈现下降趋势，下降率: {abs(trend.trend_score):.1%}")

            if trend.prediction:
                recommendations.append(f"🔮 预测 `{trend.column_name}` 的下一个值约为: {trend.prediction}")

        # 数据量建议
        if report.summary.row_count > 1000000:
            recommendations.append("📊 表数据量较大，建议考虑分区或索引优化")

        return recommendations