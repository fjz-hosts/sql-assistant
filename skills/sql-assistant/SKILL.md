---
name: sql-assistant
description: SQL Smart Assistant - A complete natural language to SQL query tool integrated as a skill. This skill guides users through installation, starts the service, configures databases and LLM providers, and executes queries directly through conversation.
---

# SQL Assistant Skill

## Overview

This skill integrates the SQL Assistant FastAPI service directly into the IDE. You can:
1. Install the SQL Assistant package
2. Start the SQL Assistant service
3. Configure database connections
4. Configure LLM providers (OpenAI, Claude, Gemini, etc.)
5. Execute natural language queries
6. Manage conversations and history
7. Perform database backups

## Quick Start

### Step 1: Install the Package

Choose your preferred installation method:

**Option A: Global Installation**
```bash
pip install sql-assistant
```

**Option B: Virtual Environment Installation (Recommended)**
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

```bash
# Install SQL Server support
pip install sql-assistant[sqlserver]

# Install Google Gemini support
pip install sql-assistant[gemini]

# Install Anthropic Claude support
pip install sql-assistant[claude]

# Install all optional dependencies at once
pip install sql-assistant[sqlserver,gemini,claude]
```

### Step 3: Start Service

```bash
# Start SQL Assistant service
python -m sql_assistant.main

# Alternative: With custom host and port
python -m sql_assistant.main --host 0.0.0.0 --port 5010

# Alternative: Use CLI command (if installed via pip)
sql-assistant --host 0.0.0.0 --port 5010
```

Wait for service to start, then access: http://localhost:5010

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

### 4. Execute Raw SQL

**Description**: Execute raw SQL statement

**Usage**:
```
Ask SQL Assistant to: Execute SQL [sql] on [database]

Example:
Ask SQL Assistant to: Execute SQL SELECT * FROM users LIMIT 10 on mysql_dev
```

### 5. Explain SQL

**Description**: Analyze SQL execution plan

**Usage**:
```
Ask SQL Assistant to: Explain SQL [sql] on [database]

Example:
Ask SQL Assistant to: Explain SQL SELECT COUNT(*) FROM orders WHERE date > '2024-01-01' on mysql_dev
```

### 6. Create Backup

**Description**: Create database backup

**Usage**:
```
Ask SQL Assistant to: Create backup for [database]

Example:
Ask SQL Assistant to: Create backup for mysql_dev
```

### 7. List Connections

**Description**: List all configured database connections

**Usage**:
```
Ask SQL Assistant to: List database connections
```

### 8. List LLM Providers

**Description**: List all configured LLM providers

**Usage**:
```
Ask SQL Assistant to: List LLM providers
```

### 9. Set Active Configuration

**Description**: Set active LLM or database

**Usage**:
```
Ask SQL Assistant to: Set active LLM to [provider]
Ask SQL Assistant to: Set active database to [connection_name]

Example:
Ask SQL Assistant to: Set active LLM to openai
Ask SQL Assistant to: Set active database to mysql_dev
```

### 10. View Query History

**Description**: View recent query history

**Usage**:
```
Ask SQL Assistant to: Show query history
```

## API Endpoints

The skill interacts with the following API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/query` | POST | Natural language to SQL query |
| `/api/execute` | POST | Execute raw SQL |
| `/api/explain` | POST | Explain SQL execution plan |
| `/api/config/llm` | GET/POST | LLM configuration |
| `/api/config/database` | GET/POST | Database configuration |
| `/api/config/active` | GET/PUT | Active configuration |
| `/api/backup` | POST | Create backup |
| `/api/history` | GET | Query history |
| `/api/conversations` | GET/POST | Conversation management |

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
1. Install: pip install sql-assistant (or use virtual environment)
2. Start service: python -m sql_assistant.main
3. Configure LLM: "Configure LLM openai with API key xxx"
4. Configure database: "Configure database mysql_dev as mysql with host localhost port 3306 database mydb username admin password secret"
5. Set active: "Set active LLM to openai" and "Set active database to mysql_dev"
6. Query: "Show me sales data for last 7 days"
```

## Resources

- **scripts/install.py**: Interactive installation script
- **scripts/start.py**: Service startup script
- **scripts/configure.py**: Configuration management script
- **scripts/query.py**: Query execution script
- **references/api.md**: Full API documentation
- **assets/config.yaml**: Configuration template