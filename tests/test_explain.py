"""执行计划分析模块测试"""
import pytest
import asyncio
import json
from sql_assistant.database.explain import ExplainPlanManager

class TestExplainPlanManager:
    """执行计划管理器测试"""
    
    def test_explain_plan_manager_init(self):
        """测试执行计划管理器初始化"""
        explain_manager = ExplainPlanManager()
        assert explain_manager is not None
    
    def test_save_plan(self):
        """测试保存执行计划"""
        explain_manager = ExplainPlanManager()
        plan_id = asyncio.run(explain_manager.save_plan(
            sql="SELECT * FROM users WHERE id = 1",
            db_type="mysql",
            db_name="test_db",
            plan_json={"nodes": []},
            plan_text="Test plan",
            estimated_cost=10.5,
            estimated_rows=100,
            actual_time_ms=5.2,
            warnings=["Warning 1"],
            suggestions=["Add index"],
            is_slow_query=False
        ))
        assert plan_id is not None
        assert isinstance(plan_id, int)
    
    def test_get_plan(self):
        """测试获取单个执行计划"""
        explain_manager = ExplainPlanManager()
        plan_id = asyncio.run(explain_manager.save_plan(
            sql="SELECT * FROM test",
            db_type="mysql",
            db_name="test_db",
            plan_json={"nodes": []}
        ))
        plan = asyncio.run(explain_manager.get_plan(plan_id))
        assert plan is not None
        assert plan["id"] == plan_id
        assert plan["sql"] == "SELECT * FROM test"
    
    def test_get_plans(self):
        """测试获取执行计划列表"""
        explain_manager = ExplainPlanManager()
        plans = asyncio.run(explain_manager.get_plans(limit=10))
        assert isinstance(plans, list)
    
    def test_delete_plan(self):
        """测试删除执行计划"""
        explain_manager = ExplainPlanManager()
        plan_id = asyncio.run(explain_manager.save_plan(
            sql="DELETE FROM test",
            db_type="mysql",
            db_name="test_db",
            plan_json={"nodes": []}
        ))
        success = asyncio.run(explain_manager.delete_plan(plan_id))
        assert success is True
        plan = asyncio.run(explain_manager.get_plan(plan_id))
        assert plan is None
    
    def test_get_count(self):
        """测试获取执行计划数量"""
        explain_manager = ExplainPlanManager()
        count = asyncio.run(explain_manager.get_count())
        assert isinstance(count, int)
        assert count >= 0
    
    def test_get_slow_query_stats(self):
        """测试获取慢查询统计"""
        explain_manager = ExplainPlanManager()
        stats = asyncio.run(explain_manager.get_slow_query_stats())
        assert isinstance(stats, dict)
        assert "total_plans" in stats
        assert "slow_query_count" in stats
        assert "average_cost" in stats
        assert "max_cost" in stats
    
    def test_close(self):
        """测试关闭数据库连接"""
        explain_manager = ExplainPlanManager()
        asyncio.run(explain_manager.close())
