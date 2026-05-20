# SQL Assistant API Reference

## Base URL
http://localhost:5010

## Endpoints

### POST /api/query
Convert natural language to SQL and execute

**Request:**
```json
{
    "question": "string",
    "db_connection": "string",
    "execute": true
}
```

**Response:**
```json
{
    "sql": "SELECT ...",
    "result": [...],
    "execution_time": 0.01
}
```

### POST /api/explain
Explain SQL execution plan

**Request:**
```json
{
    "sql": "string",
    "db_connection": "string"
}
```

### POST /api/execute
Execute raw SQL

**Request:**
```json
{
    "sql": "string",
    "db_connection": "string"
}
```

### GET /api/connections
List all database connections

### POST /api/chat/completions
Chat interface

**Request:**
```json
{
    "messages": [{"role": "user", "content": "..."}],
    "db_connection": "string"
}
```

### GET /api/health
Get database health overview

**Response:**
```json
{
    "success": true,
    "db_type": "mysql",
    "status": "healthy",
    "connection_ok": true,
    "response_time_ms": 15.5,
    "timestamp": "2026-05-15 10:30:00"
}
```

### GET /api/health/connection
Get detailed connection information

**Response:**
```json
{
    "success": true,
    "db_type": "mysql",
    "status": "healthy",
    "connection_ok": true,
    "response_time_ms": 15.5,
    "max_connections": 100,
    "current_connections": 5,
    "uptime_seconds": 86400,
    "error_message": ""
}
```

### GET /api/health/tables
Get table statistics

**Response:**
```json
{
    "success": true,
    "db_type": "mysql",
    "table_count": 10,
    "total_size_mb": 256.5,
    "total_rows": 50000,
    "tables": [
        {
            "name": "users",
            "engine": "InnoDB",
            "row_count": 1000,
            "size_mb": 2.5,
            "index_length_mb": 0.5,
            "data_length_mb": 2.0
        }
    ]
}
```

### GET /api/health/indexes
Get index statistics

**Response:**
```json
{
    "success": true,
    "db_type": "mysql",
    "total_indexes": 25,
    "table_count": 10,
    "indexes_by_table": {
        "users": [
            {
                "index_name": "PRIMARY",
                "column_name": "id",
                "unique": true,
                "cardinality": 1000
            }
        ]
    }
}
```

### GET /api/health/performance
Get performance metrics

**Response:**
```json
{
    "success": true,
    "db_type": "mysql",
    "status": "healthy",
    "response_time_ms": 15.5,
    "slow_queries": 3,
    "max_connections": 100,
    "current_connections": 5,
    "uptime_seconds": 86400,
    "query_per_second": 125.5
}
```

### GET /api/service/status
Get service installation status

**Response:**
```json
{
    "installed": true,
    "platform": "Windows",
    "service_name": "sql-assistant"
}
```

### POST /api/service/install
Install SQL Assistant as an auto-start system service

**Response:**
```json
{
    "success": true,
    "platform": "Windows",
    "message": "已创建开机自启计划任务 (Task Scheduler)"
}
```

### POST /api/service/uninstall
Uninstall the auto-start system service

**Response:**
```json
{
    "success": true,
    "platform": "Windows",
    "message": "已删除开机自启计划任务"
}
```
