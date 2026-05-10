"""Quick start test"""
import uvicorn
print("Starting server...")
uvicorn.run("sql_assistant.main:app", host="127.0.0.1", port=5010, log_level="info")
