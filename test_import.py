import sys
sys.stdout.reconfigure(encoding='utf-8')

from sql_assistant.database.connectors.base import BaseConnector
from sql_assistant.database.manager import DatabaseManager

# Verify get_schema and get_schema_text exist
dm = DatabaseManager()
assert hasattr(dm, 'get_schema'), "get_schema missing"
assert hasattr(dm, 'refresh_schema'), "refresh_schema missing"
assert hasattr(dm, 'get_schema_text'), "get_schema_text missing"

from sql_assistant.api.routes import router
routes = [r.path for r in router.routes]
assert '/api/schema' in routes, "GET /api/schema missing"
assert '/api/schema/refresh' in routes, "POST /api/schema/refresh missing"

from sql_assistant.llm.prompts import SYSTEM_PROMPT
assert '{schema_context}' in SYSTEM_PROMPT, "schema_context placeholder missing"

print("[OK] All schema integration checks passed")
print(f"Routes: {len(routes)}")
