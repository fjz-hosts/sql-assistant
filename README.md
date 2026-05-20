# SQL Smart Assistant

<p align="center">
  <img src="https://api.iconify.design/vscode-icons/file-type-sql.svg" alt="SQL Assistant" width="64"/>
</p>

<p align="center">
  Natural Language → SQL → Query Results
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License: MIT"/></a>
  <img src="https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.100-009688?style=flat-square&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/MySQL-8.0-blue?style=flat-square&logo=mysql" alt="MySQL"/>
  <img src="https://img.shields.io/badge/PostgreSQL-15-blue?style=flat-square&logo=postgresql" alt="PostgreSQL"/>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> · <a href="#features">Features</a> · <a href="#system-architecture">Architecture</a> · <a href="#project-structure">Structure</a> · <a href="#configuration">Configuration</a>
</p>


## 📖 Overview

**SQL Smart Assistant** is an intelligent database query tool based on large language models, supporting natural language to SQL conversion, multi-database connection management, query history records, and more.

### Highlights

- **Natural Language to SQL**: Describe query requirements in Chinese/English, AI automatically generates and executes SQL
- **Multi-database Support**: MySQL / SQL Server / PostgreSQL / Redis / MongoDB
- **Multi-LLM Support**: DeepSeek / Doubao / Kimi / Qwen / OpenAI / Gemini / Claude / GLM / MiniMax / SiliconFlow / OpenRouter / Grok / Tencent / Mimo / Ollama
- **Conversation Management**: Create, delete, switch, rename conversation sessions
- **Theme Customization**: Light/dark theme switch, 8 theme colors available
- **Configuration UI**: Manage LLM API Key and database connections directly in Web UI
- **Streaming Response**: SSE streaming output for real-time LLM generation viewing
- **Data Persistence**: SQLite local storage, unified configuration file management


## <a id="quick-start"></a> 🚀 Quick Start

### Prerequisites

- **Python** >= 3.10

### Option 1: Install from GitHub Release (Recommended)

Download and install directly from the Release page:

```bash
# Install latest version (replace with your Release URL)
pip install sql-assistant

# Install with optional dependencies
pip install "sql-assistant[sqlserver,gemini,claude]"
```

### Option 2: Install from Source (Development Mode)

```bash
git clone https://github.com/fjz-hosts/sql-assistant.git
cd sql-assistant

# Install uv tool
pip install uv

# Create virtual environment and install dependencies
uv venv
uv pip install -e .
```

### Option 3: Install as a Skill (via Registry)

```bash
# Install via npx skills registry
npx skills add https://github.com/fjz-hosts/sql-assistant --skill sql-assistant
```

### Start Server

```bash
# Option 1: Use CLI command (Recommended)
sql-assistant

# Option 2: Use Python module
python -m sql_assistant.main

# Option 3: Use uvicorn directly (with custom parameters)
uvicorn sql_assistant.main:app --host 0.0.0.0 --port 8000
```

### Open Browser

Visit **http://localhost:5010** to start using!

### Initial Configuration

1. Click the ⚙️ Settings button on the left
2. Add your API Key in "LLM Configuration"
3. Add database connections in "Database Configuration"
4. Click "Activate" to select your preferred LLM and database
5. Start querying!


## <a id="features"></a> ✨ Features

### 1. Natural Language to SQL

- **Smart SQL Generation**: Convert natural language descriptions into executable SQL statements based on large language models
- **Multi-language Support**: Supports Chinese and English query descriptions
- **Context Awareness**: Generates accurate SQL based on database table structure

### 2. Multi-database Connections

- **MySQL**: Full support for SELECT / INSERT / UPDATE / DELETE operations
- **SQL Server**: Supports Windows Authentication and SQL Authentication
- **PostgreSQL**: Supports SSL connections and advanced features
- **Redis**: Supports Redis command execution and data query
- **MongoDB**: Supports NoSQL queries and document operations

### 3. Conversation Management

- **Multi-session Support**: Create multiple independent conversations, each with its own query history
- **Rename Conversation**: Double-click conversation title or click pencil icon to rename
- **Delete Conversation**: Click trash icon to delete conversation and associated history
- **Smart Naming**: Automatically uses the first question as title when creating new conversation

### 5. Theme Customization

- **Light/Dark Mode**: One-click switch between light and dark themes
- **8 Theme Colors**: Blue, Purple, Pink, Red, Orange, Yellow, Green, Cyan
- **Theme Memory**: Automatically remembers user theme preferences

### 6. Web Configuration Interface

- **LLM Configuration Management**: Add, edit, delete LLM API Keys
- **Database Configuration Management**: Add, edit, delete database connections
- **Active Status Switch**: One-click switch between current LLM and database

### 7. Database Backup

- **Full Backup**: Backup all table structures and data
- **Incremental Backup**: Backup only newly added or modified data since last backup (requires timestamp field in tables)
- **Selective Backup**: Support specifying partial tables for backup, backup all tables by default
- **Backup Management**: View backup list, get backup details, delete backup files
- **Data Recovery**: Restore table structure and data from backup files to current database

### 8. SQL Template/Favorite

- **Template Management**: Create, edit, delete SQL templates for frequently used queries
- **Tag-based Filtering**: Organize templates with tags for easy categorization
- **Quick Insert**: Insert templates directly into the query input box
- **Favorite Marking**: Mark frequently used SQL statements as favorites

### 9. Execution Plan Analysis

- **Visual Execution Plan**: View graphical execution plan for SELECT statements
- **Cost Analysis**: Analyze query cost and performance metrics
- **Optimization Suggestions**: Get AI-powered optimization recommendations
- **Index Utilization**: Check index usage and identify missing indexes

### 10. Database Health Check/Monitoring

- **Connection Status Monitoring**: Real-time database connection status and response time
- **Table Statistics**: View table row count, data size, index size, engine type
- **Index Usage**: View index name, column, cardinality, uniqueness for each table
- **Performance Metrics**: Uptime, connection count, slow queries, QPS
- **Multi-database Support**: MySQL, PostgreSQL, SQL Server, Redis, MongoDB

### 11. Auto-Start System Service

- **One-Click Install**: Install SQL Assistant as a system service for auto-start on boot
- **Cross-Platform**: Supports Windows (Task Scheduler) and Linux (systemd)
- **Status Indicator**: Visual indicator showing current service installation status
- **Easy Uninstall**: One-click removal of the auto-start service without affecting project files
- **Shortcut Support**: Quick toggle via `Ctrl+Shift+S` or navbar button


## <a id="system-architecture"></a> 🏗️ System Architecture

### Overall Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend Layer│    │   Business Layer│    │   Data Storage  │
│  - HTML/CSS/JS  │◄──►│  - FastAPI      │◄──►│  - SQLite(Config)│
│  - Vue.js       │    │  - LLM Manager  │    │  - MySQL/PG/SQL │
│  - Tailwind CSS │    │  - DB Connector │    │    Server/Mongo │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Interaction│   │    AI Services │    │   Query History │
│  - NL Input     │    │  - DeepSeek    │    │  - SQLite Storage│
│  - SQL Display  │    │  - Doubao/Kimi │    │  - History Review│
│  - Result Display│   │  - Qwen        │    │                  │
└─────────────────┘    │  - OpenAI      │    └─────────────────┘
                       │  - Gemini/Claude│
                       └─────────────────┘
```

### LLM Provider Integration

| Provider | Model Series | API Type |
|----------|--------------|----------|
| **DeepSeek** | deepseek-v4-pro, deepseek-v4-flash | OpenAI Compatible |
| **Doubao** | doubao-seed-2-0-pro-260215, doubao-seed-2-0-lite-260215, doubao-seed-2-0-mini-260215, doubao-seed-1-8-251228 | OpenAI Compatible |
| **Kimi** | kimi-k2.6, kimi-k2.5, kimi-k2-thinking | OpenAI Compatible |
| **Qwen** | qwen3.6-max-preview, qwen3.6-plus, qwen3.6-flash, qwen3.5-flash, qwen3.5-plus, qwen3-max, qwen3-vl-plus | OpenAI Compatible |
| **OpenAI** | gpt-5.5, gpt-5.4-pro, gpt-5.4-mini, gpt-5.4-nano, gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4.1, gpt-4, gpt-3.5-turbo, o1-preview, o1-mini | OpenAI Native |
| **Gemini** | gemini-3.1-pro-preview, gemini-3-flash-preview, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite, gemini-1.5-pro, gemini-1.5-flash | Google API |
| **Claude** | claude-opus-4-7, claude-opus-4-6, claude-sonnet-4-6, claude-sonnet-4-5, claude-haiku-4-5, claude-3-opus, claude-3-sonnet, claude-3-haiku | Anthropic API |
| **GLM** | glm-5.1, glm-5v-turbo, glm-5, glm-4.7, glm-4.6 | OpenAI Compatible |
| **MiniMax** | MiniMax-M2.7 | Anthropic API |
| **SiliconFlow** | deepseek-ai/DeepSeek-V3.2, deepseek-ai/DeepSeek-R1, Qwen/Qwen3-VL-32B-Instruct, THUDM/GLM-4.1V-9B-Thinking | OpenAI Compatible |
| **OpenRouter** | deepseek/deepseek-v4-pro, deepseek/deepseek-v4-flash | OpenAI Compatible |
| **Grok** | grok-4.20-reasoning, grok-4.20, grok-4-1-fast-reasoning, grok-code-fast-1 | OpenAI Compatible |
| **Tencent** | hy3-preview | OpenAI Compatible |
| **Mimo** | mimo-v2.5-pro, mimo-v2.5 | OpenAI Compatible |
| **Ollama** | llama3.3, gemma3, deepseek-r1 | OpenAI Compatible |

### Database Connectors

| Database | Connector Module | Supported Operations |
|----------|------------------|---------------------|
| **MySQL** | `mysql.py` | SELECT/INSERT/UPDATE/DELETE |
| **SQL Server** | `sqlserver.py` | SELECT/INSERT/UPDATE/DELETE |
| **PostgreSQL** | `postgresql.py` | SELECT/INSERT/UPDATE/DELETE |
| **Redis** | `redis.py` | Redis Command Execution |
| **MongoDB** | `mongodb.py` | NoSQL Query Operations |


## <a id="skill-installation"></a> 🧩 Skill Installation

SQL Assistant can be installed as a skill via the skills registry. This allows users to integrate SQL Assistant into their Agent system and use all features directly through conversation without opening a web browser.

### Skill Structure

```
SQL Assistant/
└── skills/
    └── sql-assistant/
        ├── SKILL.md           # Skill definition and description
        ├── scripts/           # Service scripts
        │   ├── start.py       # Service startup
        │   ├── configure.py   # Configuration management
        │   └── query.py       # Query execution
        ├── references/        # API documentation
        └── assets/            # Configuration templates
```

### Install as a Skill

```bash
# Install via npx skills registry
npx skills add https://github.com/fjz-hosts/sql-assistant --skill sql-assistant
```

### Skill Usage Commands

Once the skill is installed and the service is running, you can use these commands through conversation:

| Command | Description | Example |
|---------|-------------|---------|
| `Configure LLM [provider] with API key [key]` | Configure LLM provider | `Configure LLM openai with API key sk-xxx` |
| `Configure database [name] as [type] with ...` | Configure database connection | `Configure database mysql_dev as mysql with host localhost port 3306 database mydb username admin password secret` |
| `Set active LLM to [provider]` | Set active LLM | `Set active LLM to openai` |
| `Set active database to [name]` | Set active database | `Set active database to mysql_dev` |
| `Query [question] from [database]` | Natural language query | `Show me total sales for each product from mysql_dev` |
| `Execute SQL [sql] on [database]` | Execute raw SQL | `Execute SQL SELECT * FROM users LIMIT 10 on mysql_dev` |
| `Explain SQL [sql] on [database]` | Analyze execution plan | `Explain SQL SELECT COUNT(*) FROM orders on mysql_dev` |
| `Create backup for [database]` | Create database backup | `Create backup for mysql_dev` |
| `List database connections` | List all connections | `List database connections` |
| `List LLM providers` | List all providers | `List LLM providers` |
| `Show query history` | View recent queries | `Show query history` |

### Skill Features

- **Natural Language to SQL**: Convert natural language questions into SQL queries
- **Multi-database Support**: MySQL, PostgreSQL, SQL Server, MongoDB, Redis, SQLite
- **Multi-LLM Support**: OpenAI, Claude, Gemini, DeepSeek, Doubao, Kimi, Qwen
- **Conversation-based Operation**: Full functionality accessible through chat commands
- **REST API Integration**: Automatically calls backend APIs for all operations

### Skill Workflow

```
1. Install skill: npx skills add https://github.com/fjz-hosts/sql-assistant --skill sql-assistant
2. Start service: sql-assistant
3. Configure LLM: "Configure LLM openai with API key xxx"
4. Configure database: "Configure database mysql_dev as mysql with host localhost port 3306 database mydb username admin password secret"
5. Set active: "Set active LLM to openai" and "Set active database to mysql_dev"
6. Query: "Show me sales data for last 7 days"
```

## <a id="project-structure"></a> 📁 Project Structure

```
SQL Assistant/
├── pyproject.toml                # Python project configuration (dependency management)
├── README.md                     # Project documentation
├── LICENSE                       # MIT License
├── backups/                      # Database backup storage directory
│   └── full_20260101_120000/     # Timestamp-named backup folder
│       ├── metadata.json         # Backup metadata
│       ├── users_schema.json     # Table schema file
│       └── users_data.json       # Table data file
├── .data/                        # Data storage directory
│   ├── config.yaml               # Configuration file (API Key, database connections, etc.)
│   ├── history.db                # SQLite database (query history)
│   ├── templates.db              # SQLite database (SQL templates/favorites)
│   └── explain_history.db        # SQLite database (explain history)
├── .venv/                        # uv virtual environment
└── src/
    └── sql_assistant/
        ├── __init__.py           # Package initialization
        ├── main.py               # FastAPI entry
        ├── config.py             # Configuration management (YAML)
        ├── settings.py           # Configuration data models
        ├── api/                  # API module
        │   ├── __init__.py
        │   ├── routes.py         # API routes
        │   ├── models.py         # Pydantic models
        │   └── dependencies.py   # Dependency injection
        ├── llm/                  # LLM module
        │   ├── __init__.py
        │   ├── manager.py        # LLM manager
        │   ├── base.py           # Provider abstract base class
        │   ├── prompts.py        # SQL Prompt templates
        │   └── providers/        # LLM provider implementations
        │       ├── __init__.py
        │       ├── openai_compatible.py  # DeepSeek/Doubao/Kimi/Qwen/OpenAI
        │       ├── gemini.py     # Google Gemini
        │       └── claude.py     # Anthropic Claude
        ├── database/             # Database module
        │   ├── __init__.py
        │   ├── manager.py        # Database connection manager
        │   ├── history.py        # Query history (SQLite)
        │   ├── backup.py         # Database backup module
        │   └── connectors/       # Database connectors
        │       ├── __init__.py
        │       ├── base.py       # Connector abstract base class
        │       ├── exceptions.py # Database connection exceptions
        │       ├── mysql.py
        │       ├── sqlserver.py
        │       ├── postgresql.py
        │       ├── redis.py
        │       └── mongodb.py
        └── web/                  # Web frontend
            ├── __init__.py
            ├── templates/        # HTML templates
            │   └── index.html    # Main page
            └── static/           # Static resources
                ├── css/
                │   ├── theme.css     # Theme styles (CSS variables)
                │   └── style.css     # Application styles
                └── js/
                    ├── theme-manager.js       # Theme switching logic
                    ├── color-theme-manager.js # Theme color switching logic
                    └── app.js                # Application main logic
```


## <a id="configuration"></a> 🔧 Configuration

### Configuration File Location

Configuration files and data storage have been migrated to the project `.data` directory:

```
SQL Assistant/
└── .data/
    ├── config.yaml               # Configuration file (API Key, database connections, etc.)
    ├── history.db                # SQLite database (query history)
    ├── templates.db              # SQLite database (SQL templates/favorites)
    └── explain_history.db        # SQLite database (explain history)
```

> ⚠️ **Note**: Configuration files stored in `~/.sql-assistant/` from older versions need to be manually migrated to the project `.data` directory.

### Database Backup Storage

Database backup files are stored in the `backups/` folder at the project root:

```
SQL Assistant/
└── backups/
    ├── .last_backup_timestamp     # Incremental backup timestamp marker
    ├── full_20260101_120000/     # Full backup
    │   ├── metadata.json         # Backup metadata (type, table count, record count, etc.)
    │   ├── users_schema.json     # users table schema
    │   └── users_data.json       # users table data
    └── incremental_20260102_120000/  # Incremental backup
        ├── metadata.json
        ├── orders_schema.json
        └── orders_data.json
```

Backup File Description:
- `metadata.json`: Contains backup type, database information, table count, total records, backup time, and other metadata
- `*_schema.json`: Table structure information (column names, types, key information, etc.)
- `*_data.json`: Table data content (JSON format)
- `.last_backup_timestamp`: Records the timestamp of the last incremental backup

### Configuration Options

```yaml
# Currently active LLM provider
active_llm: deepseek

# Currently active database connection
active_database: mysql_dev

# LLM provider configurations
llm_providers:
  deepseek:
    api_key: "your_api_key"
    api_base: "https://api.deepseek.com/v1"
    model: "deepseek-moe"
  doubao:
    api_key: "your_api_key"
    api_base: "https://ark.cn-beijing.volces.com/api/v3"
    model: "doubao-seed-2-0-pro-260215"
  kimi:
    api_key: "your_api_key"
    api_base: "https://api.moonshot.cn/v1"
    model: "kimi-k2.6"
  qwen:
    api_key: "your_api_key"
    api_base: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: "qwen3.6-plus"
  openai:
    api_key: "your_api_key"
    api_base: "https://api.openai.com/v1"
    model: "gpt-5.5"
  gemini:
    api_key: "your_api_key"
    model: "gemini-2.0-pro"
  claude:
    api_key: "your_api_key"
    model: "claude-sonnet-4-6"

# Database connection configurations
database_connections:
  mysql_dev:
    type: mysql
    host: localhost
    port: 3306
    database: your_database
    username: your_username
    password: your_password
  postgresql_prod:
    type: postgresql
    host: localhost
    port: 5432
    database: your_database
    username: your_username
    password: your_password
  sqlserver_prod:
    type: sqlserver
    host: localhost
    port: 1433
    database: your_database
    username: your_username
    password: your_password
  redis_cache:
    type: redis
    host: localhost
    port: 6379
    db: 0
  mongodb_prod:
    type: mongodb
    host: localhost
    port: 27017
    database: your_database
    username: your_username
    password: your_password
```

### Additional Dependencies Installation

Some databases and LLMs require additional dependencies:

```bash
# SQL Server support
uv pip install pymssql

# Google Gemini support
uv pip install google-generativeai

# Anthropic Claude support
uv pip install anthropic

# MongoDB support
uv pip install pymongo

# PostgreSQL support
uv pip install psycopg2-binary
```


## 📈 API Documentation

Visit **http://localhost:5010/docs** after starting the service to view Swagger API documentation.

### Main API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/query` | POST | Execute natural language query |
| `/api/conversations` | GET/POST | Get conversation list / Create new conversation |
| `/api/conversations/{id}` | GET/PUT/DELETE | Get/update/delete single conversation |
| `/api/config/llm` | GET/POST | LLM configuration management |
| `/api/config/database` | GET/POST | Database configuration management |
| `/api/config/active` | GET/PUT | Active configuration management |
| `/api/history` | GET | Query history list |
| `/api/backup` | POST | Create database backup |
| `/api/backup/list` | GET | Get backup list |
| `/api/backup/{backup_id}` | GET/DELETE | Get backup details / Delete backup |
| `/api/backup/restore` | POST | Restore database from backup |
| `/api/templates` | GET/POST | Get template list / Create new template |
| `/api/templates/{id}` | GET/PUT/DELETE | Get/update/delete template |
| `/api/explain` | POST | Analyze SQL execution plan |
| `/api/shortcuts` | GET | Get keyboard shortcuts configuration |
| `/api/shortcuts/defaults` | GET | Get default shortcuts |
| `/api/shortcuts/{action_id}` | PUT | Update a shortcut key binding |
| `/api/service/status` | GET | Get service installation status |
| `/api/service/install` | POST | Install as auto-start service |
| `/api/service/uninstall` | POST | Uninstall auto-start service |


## ⚠️ Notes

- **Data Directory**: Configuration files and database have been moved to the project `.data` directory, ensure proper permissions for this directory
- **API Key Security**: All configurations are stored in `.data/config.yaml`, regular backups are recommended
- **Dangerous Operation Warning**: Confirm WHERE clause before executing DELETE/UPDATE
- **Database Permissions**: It is recommended to use a read-only database user for query operations
- **Network Security**: It is recommended to use HTTPS protocol in production environment


## 🤝 Contributing

Community contributions are welcome! Whether it's bug reports, feature suggestions, or code submissions, they are all highly appreciated.

### Contribution Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Documentation Synchronization

When adding new features or rules, **both** of the following must be updated:

1. **README.md**: Update relevant documentation sections
2. **skills/ directory**: Update corresponding skill files to enable conversation-based access to the new feature

The `skills/sql-assistant/` directory contains:
- `scripts/`: Python scripts for skill operations
- `references/`: API documentation references
- `SKILL.md`: Skill description and usage guide


## 📄 License

This project is licensed under the [MIT License](LICENSE).