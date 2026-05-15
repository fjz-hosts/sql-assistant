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
