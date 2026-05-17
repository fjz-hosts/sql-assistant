"""
SQL 安全保护模块 - 防止 SQL 注入攻击
"""
import re
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class SQLCheckResult:
    """SQL 检查结果"""
    is_safe: bool
    warning: str = ""
    risk_level: str = "none"  # none, low, medium, high
    blocked_reason: str = ""


class SQLSecurityGuard:
    """SQL 安全守卫类"""
    
    # 危险 SQL 关键字和模式
    DANGEROUS_KEYWORDS = [
        # 注释相关
        r"/\*", r"\*/", r"--", r"#",
        # 联合查询
        r"\bUNION\b", r"\bUNION\s+ALL\b",
        # 子查询
        r"\bSELECT\b.*\bFROM\b.*\bSELECT\b",
        # 批处理
        r";",
        # 信息_schema
        r"\binformation_schema\b",
        r"\bmysql\.",
        r"\bsys\.",
        # 系统函数
        r"\bLOAD_FILE\b",
        r"\bINTO\s+OUTFILE\b",
        r"\bINTO\s+DUMPFILE\b",
        r"\bEXEC\b",
        r"\bEXECUTE\b",
        r"\bSYSTEM\b",
        r"\bSHELL\b",
        r"\bCMD\b",
        # 数据操作
        r"\bDROP\b",
        r"\bTRUNCATE\b",
        r"\bALTER\b.*\bDROP\b",
        # 用户权限
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bCREATE\s+USER\b",
        r"\bALTER\s+USER\b",
        # 十六进制
        r"0x[0-9a-fA-F]+",
        # 字符串拼接
        r"\|\|",
        r"CONCAT\s*\(",
        r"GROUP_CONCAT\s*\(",
        # 延迟攻击
        r"\bSLEEP\b",
        r"\bBENCHMARK\b",
        # 布尔注入
        r"\bOR\s+1\s*=\s*1\b",
        r"\bAND\s+1\s*=\s*1\b",
        r"\bOR\s+TRUE\b",
        r"\bAND\s+FALSE\b",
        # 盲注
        r"\bIF\s*\(",
        r"\bCASE\s+WHEN\b",
        r"\bEXISTS\s*\(",
        # 其他危险
        r"\bDELETE\b.*\bWHERE\s*1\s*=\s*1\b",
        r"\bUPDATE\b.*\bWHERE\s*1\s*=\s*1\b",
    ]
    
    # 允许的 SQL 类型
    ALLOWED_SQL_TYPES = {
        "SELECT", "INSERT", "UPDATE", "DELETE",
        "SHOW", "DESCRIBE", "EXPLAIN",
        "CREATE", "ALTER", "DROP", "TRUNCATE",
        "USE", "SET"
    }
    
    def __init__(self):
        # 编译正则表达式
        self.dangerous_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.DANGEROUS_KEYWORDS
        ]
    
    def check_sql_safety(self, sql: str) -> SQLCheckResult:
        """
        检查 SQL 语句安全性
        
        Args:
            sql: SQL 语句
            
        Returns:
            SQLCheckResult 检查结果
        """
        sql = sql.strip()
        
        if not sql:
            return SQLCheckResult(
                is_safe=False,
                blocked_reason="SQL 语句为空"
            )
        
        # 检查危险模式
        warnings = []
        risk_level = "none"
        
        for pattern in self.dangerous_patterns:
            matches = pattern.findall(sql)
            if matches:
                for match in matches:
                    warning_msg = self._get_warning_message(match)
                    if warning_msg:
                        warnings.append(warning_msg)
                        # 升级风险等级
                        if "high" in warning_msg.lower():
                            risk_level = "high"
                        elif risk_level != "high":
                            risk_level = "medium"
        
        if risk_level == "high":
            return SQLCheckResult(
                is_safe=False,
                warning="; ".join(warnings),
                risk_level=risk_level,
                blocked_reason="检测到高风险 SQL 注入模式"
            )
        
        if warnings:
            return SQLCheckResult(
                is_safe=True,  # 中等风险仍允许执行，但给出警告
                warning="; ".join(warnings),
                risk_level=risk_level
            )
        
        return SQLCheckResult(is_safe=True)
    
    def _get_warning_message(self, match: str) -> str:
        """根据匹配内容获取警告信息"""
        match_lower = match.lower()
        
        if any(keyword in match_lower for keyword in ["union", "select.*from.*select"]):
            return "⚠️ 检测到联合查询模式，可能存在注入风险"
        elif any(keyword in match_lower for keyword in ["--", "/*", "*/", "#"]):
            return "⚠️ 检测到注释符，请确认操作意图"
        elif ";" in match:
            return "⚠️ 检测到分号分隔符，可能存在多语句执行风险"
        elif any(keyword in match_lower for keyword in ["information_schema", "mysql.", "sys."]):
            return "⚠️ 检测到系统表访问，请注意数据安全"
        elif any(keyword in match_lower for keyword in ["load_file", "into outfile", "into dumpfile", "exec", "execute", "system", "shell"]):
            return "🔴 检测到高风险系统函数调用"
        elif any(keyword in match_lower for keyword in ["sleep", "benchmark"]):
            return "🔴 检测到延迟注入函数"
        elif any(keyword in match_lower for keyword in ["or 1=1", "and 1=1", "or true", "and false"]):
            return "🔴 检测到布尔注入模式"
        elif any(keyword in match_lower for keyword in ["drop", "truncate"]):
            return "⚠️ 检测到数据删除操作，请谨慎执行"
        elif any(keyword in match_lower for keyword in ["0x"]):
            return "⚠️ 检测到十六进制编码"
        elif any(keyword in match_lower for keyword in ["concat", "group_concat", "||"]):
            return "⚠️ 检测到字符串拼接，请注意注入风险"
        
        return ""
    
    def sanitize_sql(self, sql: str) -> Tuple[str, List[str]]:
        """
        清理 SQL 语句，移除一些明显的危险内容
        
        Args:
            sql: 原始 SQL
            
        Returns:
            (清理后的 SQL, 警告列表)
        """
        warnings = []
        cleaned = sql
        
        # 移除首尾空白
        cleaned = cleaned.strip()
        
        # 检查并警告危险模式（不自动修改）
        check_result = self.check_sql_safety(cleaned)
        if check_result.warning:
            warnings.append(check_result.warning)
        
        return cleaned, warnings
    
    def requires_confirmation(self, sql: str) -> Tuple[bool, str]:
        """
        判断 SQL 是否需要用户确认

        Args:
            sql: SQL 语句

        Returns:
            (是否需要确认, 确认提示信息)
        """
        from .connectors.base import BaseConnector

        sql_type = BaseConnector.classify_sql(sql)

        # 增删改操作需要确认
        table_op_types = ["CREATE_TABLE", "DROP_TABLE", "ALTER_TABLE", "TRUNCATE_TABLE"]
        if sql_type in ["INSERT", "UPDATE", "DELETE"] + table_op_types + ["DDL"]:
            reason_map = {
                "INSERT": "即将执行 INSERT 操作，会添加新数据",
                "UPDATE": "即将执行 UPDATE 操作，会修改现有数据",
                "DELETE": "即将执行 DELETE 操作，会删除数据",
                "CREATE_TABLE": "即将执行 CREATE TABLE 操作，会创建新表",
                "DROP_TABLE": "即将执行 DROP TABLE 操作，会删除表",
                "ALTER_TABLE": "即将执行 ALTER TABLE 操作，会修改表结构",
                "TRUNCATE_TABLE": "即将执行 TRUNCATE 操作，会清空表数据",
                "DDL": "即将执行 DDL 操作，会修改数据库结构"
            }

            reason = reason_map.get(sql_type, "即将执行数据修改操作")

            # 对于表操作，提取表名以提供更具体的信息
            if sql_type in table_op_types:
                table_name = self._extract_table_name(sql, sql_type)
                if table_name:
                    table_specific_map = {
                        "CREATE_TABLE": f"创建表 '{table_name}'",
                        "DROP_TABLE": f"删除表 '{table_name}'",
                        "ALTER_TABLE": f"修改表 '{table_name}' 的结构",
                        "TRUNCATE_TABLE": f"清空表 '{table_name}' 的所有数据"
                    }
                    reason = f"即将执行 {table_specific_map.get(sql_type, '表操作')}，此操作不可逆！"

            return True, reason

        # SELECT 不需要确认
        return False, ""

    def _extract_table_name(self, sql: str, sql_type: str) -> str:
        """从 SQL 语句中提取表名"""
        import re
        sql_upper = sql.upper()

        patterns = {
            "CREATE_TABLE": r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?(\w+)[`\"']?",
            "DROP_TABLE": r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?[`\"']?(\w+)[`\"']?",
            "ALTER_TABLE": r"ALTER\s+TABLE\s+[`\"']?(\w+)[`\"']?",
            "TRUNCATE_TABLE": r"TRUNCATE\s+(?:TABLE\s+)?[`\"']?(\w+)[`\"']?"
        }

        pattern = patterns.get(sql_type)
        if pattern:
            match = re.search(pattern, sql_upper)
            if match:
                return match.group(1)

        return None


# 全局单例
_security_guard: Optional[SQLSecurityGuard] = None


def get_security_guard() -> SQLSecurityGuard:
    """获取 SQL 安全守卫单例"""
    global _security_guard
    if _security_guard is None:
        _security_guard = SQLSecurityGuard()
    return _security_guard
