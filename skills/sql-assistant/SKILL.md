---
name: sql-assistant
description: SQL Smart Assistant - A complete natural language to SQL query tool integrated as a skill. This skill guides users through installation, starts the service, configures databases and LLM providers, and executes queries directly through conversation.
---

# SQL Assistant Skill

## Overview

This skill integrates the SQL Assistant FastAPI service directly into the IDE. You can:
1. Install the SQL Assistant package (asks user for preference)
2. Start the SQL Assistant service
3. Configure database connections
4. Configure LLM providers (OpenAI, Claude, Gemini, etc.)
5. Execute natural language queries
6. Manage conversations and history
7. Perform database backups

## Quick Start

### Step 1: Install the Package

**IMPORTANT**: Before installing, ask the user which installation method they prefer:

> "Do you want to install SQL Assistant globally (for all users) or in a virtual environment (recommended for isolation)?"

**If user chooses Global Installation:**
```bash
pip install sql-assistant
```

**If user chooses Virtual Environment Installation (Recommended):**
```bash
# Install uv (Python package manager)
pip install uv

# Initialize virtual environment
uv init

# Add sql-assistant package
uv add sql-assistant

# Activate virtual environment
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Step 2: Install Optional Dependencies (if needed)

Ask the user if they need support for these optional databases/LLMs:

```bash
# SQL Server support
pip install sql-assistant[sqlserver]

# Google Gemini support
pip install sql-assistant[gemini]

# Anthropic Claude support
pip install sql-assistant[claude]
```

### Step 3: Start Service

```bash
# Start SQL Assistant service
python -m sql_assistant.main

# Alternative: With custom host and port
python -m sql_assistant.main --host 0.0.0.0 --port 5010
```

### Step 4: Configure

After service starts, configure your LLM and database through conversation.

## Available Commands

### 1. Query Database with Natural Language

**Description**: Convert natural language question to SQL and execute

**Usage**:
```
Ask SQL Assistant to: Query [question] from [database]

Example:
Ask SQL Assistant to: Show me total sales for each product in the last 30 days from mysql_connection
```

### 2. Configure LLM Provider

**Description**: Add or update LLM API key

**Usage**:
```
Ask SQL Assistant to: Configure LLM [provider] with API key [api_key]

Supported providers: openai, claude, gemini, deepseek, doubao, kimi, qwen

Example:
Ask SQL Assistant to: Configure LLM openai with API key sk-xxxxxxxxxxx
```

### 3. Configure Database Connection

**Description**: Add or update database connection

**Usage**:
```
Ask SQL Assistant to: Configure database [name] as [type] with host [host] port [port] database [db_name] username [user] password [pass]

Supported types: mysql, postgresql, sqlserver, sqlite, redis, mongodb

Example:
Ask SQL Assistant to: Configure database mysql_dev as mysql with host localhost port 3306 database mydb username admin password secret
```

### 4. Preview SQL (without execution)

**Description**: Preview generated SQL without executing

**Usage**:
```
Ask SQL Assistant to: Preview SQL for [question]

Example:
Ask SQL Assistant to: Preview SQL for Show me all users registered this month
```

### 5. Create Backup

**Description**: Create database backup

**Usage**:
```
Ask SQL Assistant to: Create backup for [database]

Example:
Ask SQL Assistant to: Create backup for mysql_dev
```

### 6. List Connections

**Description**: List all configured database connections

**Usage**:
```
Ask SQL Assistant to: List database connections
```

### 7. List LLM Providers

**Description**: List all configured LLM providers

**Usage**:
```
Ask SQL Assistant to: List LLM providers
```

### 8. Set Active Configuration

**Description**: Set active LLM or database

**Usage**:
```
Ask SQL Assistant to: Set active LLM to [provider]
Ask SQL Assistant to: Set active database to [connection_name]

Example:
Ask SQL Assistant to: Set active LLM to openai
Ask SQL Assistant to: Set active database to mysql_dev
```

### 9. View Query History

**Description**: View recent query history

**Usage**:
```
Ask SQL Assistant to: Show query history
```

### 10. View Backup List

**Description**: View available backups

**Usage**:
```
Ask SQL Assistant to: Show backup list
```

## API Error Auto-Correction

**IMPORTANT**: If any API call fails, the skill should:

1. First check the error message and try to fix common issues
2. If the error persists, fetch API documentation from http://localhost:5010/openapi.json
3. Compare the request with the actual API schema
4. Retry with corrected parameters

Common issues and fixes:
- Wrong HTTP method → check if should be GET/POST/PUT/DELETE
- Missing required fields → check API schema for required fields
- Wrong field names → use exact field names from schema
- Wrong endpoint path → verify path matches API documentation

## API Endpoints (Auto-called by Skill Scripts)

The skill scripts automatically call these API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/query` | POST | Natural language to SQL query |
| `/api/query/preview` | POST | Preview SQL without executing |
| `/api/config/llm` | GET/POST | LLM configuration |
| `/api/config/llm/active/{name}` | PUT | Set active LLM |
| `/api/config/database` | GET/POST | Database configuration |
| `/api/config/database/active/{name}` | PUT | Set active database |
| `/api/config/settings` | GET | Get all settings |
| `/api/backup` | POST | Create backup |
| `/api/backup/list` | GET | List backups |
| `/api/history` | GET | Query history |

## Configuration Example

After configuration, your `.data/config.yaml` will look like:

```yaml
active_llm: openai
active_database: mysql_dev

llm_providers:
  openai:
    api_key: "sk-xxxxxxxxxxx"
    model: "gpt-4o-mini"

database_connections:
  mysql_dev:
    type: mysql
    host: localhost
    port: 3306
    database: mydb
    username: admin
    password: secret
```

## Full Usage Flow

```
1. Ask user for installation preference (global vs virtualenv)
2. Install: based on user's choice
3. Start service: python -m sql_assistant.main
4. Configure LLM: "Configure LLM openai with API key xxx"
5. Configure database: "Configure database mysql_dev as mysql with ..."
6. Set active: "Set active LLM to openai" and "Set active database to mysql_dev"
7. Query: "Show me sales data for last 7 days"
```

## Resources

- **scripts/install.py**: Interactive installation script (asks user for preference)
- **scripts/start.py**: Service startup script
- **scripts/configure.py**: Configuration management script
- **scripts/query.py**: Query execution script
- **scripts/api_helper.py**: API helper with auto-correction
- **references/api.md**: Full API documentation
- **assets/config.yaml**: Configuration template