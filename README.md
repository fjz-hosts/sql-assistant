# SQL 智能助手

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
  <a href="#quick-start">快速开始</a> · <a href="#features">核心特性</a> · <a href="#system-architecture">系统架构</a> · <a href="#project-structure">项目结构</a> · <a href="#configuration">配置指南</a>
</p>


## 🗞️ News

- **2026-05-10** — 新增 MongoDB 数据库支持
- **2026-05-05** — 优化 SQL 生成提示词模板，提升生成准确率
- **2026-04-28** — 新增 Claude 3 系列模型支持
- **2026-04-20** — 支持 SSE 流式响应，实时查看 LLM 生成过程
- **2026-04-15** — 初始版本发布，支持多数据库和多 LLM 提供商


## 📖 Overview

**SQL 智能助手** 是一个基于大语言模型的智能数据库查询工具，支持自然语言转 SQL、多数据库连接管理、查询历史记录等功能。

### Highlights

- **自然语言转 SQL**：用中文/英文描述查询需求，AI 自动生成 SQL 并执行
- **多数据库支持**：MySQL / SQL Server / PostgreSQL / Redis / MongoDB
- **多 LLM 支持**：DeepSeek / 豆包 / Kimi / 通义千问 / OpenAI / Gemini / Claude
- **查询历史**：所有查询记录自动保存，可回溯查看
- **配置界面**：Web UI 中直接管理 LLM API Key 和数据库连接
- **流式响应**：支持 SSE 流式输出，实时查看 LLM 生成过程


## <a id="quick-start"></a> 🚀 Quick Start

### Prerequisites

- **Python** >= 3.10
- **uv** >= 0.1.0

### 1. Clone & Install

```bash
git clone <项目仓库地址>
cd "SQL Assistant"
```

### 2. Install uv & Dependencies

```bash
# 安装 uv 工具
pip install uv

# 创建虚拟环境并安装依赖
uv venv
uv pip install -e .
```

### 3. Run Development Server

```bash
# 方式一：使用 Python 模块启动
.venv\Scripts\python.exe -m sql_assistant.main

# 方式二：使用 CLI 命令启动
sql-assistant
```

### 4. Open Browser

访问 **http://localhost:5010** 开始使用！

### 5. Initial Configuration

1. 点击左侧 ⚙️ 设置按钮
2. 在「LLM 配置」中添加你的 API Key
3. 在「数据库配置」中添加数据库连接
4. 分别点击「激活」选择当前使用的 LLM 和数据库
5. 开始查询！


## <a id="features"></a> ✨ Features

### 1. 自然语言转 SQL

- **智能 SQL 生成**：基于大语言模型，将自然语言描述转换为可执行的 SQL 语句
- **多语言支持**：支持中文和英文查询描述
- **上下文感知**：根据数据库表结构生成准确的 SQL

### 2. 多数据库连接

- **MySQL**：完整支持 SELECT / INSERT / UPDATE / DELETE 操作
- **SQL Server**：支持 Windows 认证和 SQL 认证
- **PostgreSQL**：支持 SSL 连接和高级特性
- **Redis**：支持 Redis 命令执行和数据查询
- **MongoDB**：支持 NoSQL 查询和文档操作

### 3. LLM 提供商管理

- **DeepSeek**：支持 DeepSeek-R1 / Chat / MoE 系列模型
- **豆包**：支持豆包 4.0 / 5.0 系列模型
- **Kimi**：支持 Kimi Chat / K2.5 / Kimi V 系列模型
- **通义千问**：支持 Qwen3.6-Plus / Qwen3.6-27B / Qwen3.5 系列模型
- **OpenAI**：支持 GPT-5.5 / GPT-5.4 / GPT-6 系列模型
- **Gemini**：支持 Google Gemini 2.0 Pro/Flash 系列模型
- **Claude**：支持 Anthropic Claude Opus 4.7 / Sonnet 4.6 / Haiku 4.5 系列模型

### 4. 查询历史管理

- **自动保存**：所有查询记录自动保存到本地 SQLite 数据库
- **历史回溯**：支持查看和重新执行历史查询
- **查询统计**：记录查询执行时间和结果信息

### 5. Web 配置界面

- **LLM 配置管理**：添加、编辑、删除 LLM API Key
- **数据库配置管理**：添加、编辑、删除数据库连接
- **激活状态切换**：一键切换当前使用的 LLM 和数据库


## <a id="system-architecture"></a> 🏗️ System Architecture

### 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面层     │    │   业务逻辑层     │    │   数据存储层     │
│  - HTML/CSS/JS  │◄──►│  - FastAPI      │◄──►│  - SQLite(配置) │
│  - Vue.js       │    │  - LLM 管理器   │    │  - MySQL/PG/SQL │
│  - Tailwind CSS │    │  - DB 连接器    │    │    Server/Mongo │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户交互       │    │    AI服务        │    │   查询历史      │
│  - NL 输入       │    │  - DeepSeek     │    │  - SQLite存储   │
│  - SQL 展示      │    │  - 豆包/Kimi    │    │  - 历史回溯     │
│  - 结果展示      │    │  - 通义千问     │    │                  │
└─────────────────┘    │  - OpenAI       │    └─────────────────┘
                       │  - Gemini/Claude│
                       └─────────────────┘
```

### LLM 提供商集成

| 提供商 | 模型系列 | API 类型 |
|--------|----------|----------|
| **DeepSeek** | DeepSeek-R1 / Chat / MoE | OpenAI 兼容 |
| **豆包** | Doubao 4.0 / Doubao 5.0 | OpenAI 兼容 |
| **Kimi** | Kimi Chat / Kimi K2.5 / Kimi V | OpenAI 兼容 |
| **通义千问** | Qwen3.6-Plus / Qwen3.6-27B / Qwen3.5 | OpenAI 兼容 |
| **OpenAI** | GPT-5.5 / GPT-5.4 / GPT-6 | OpenAI 原生 |
| **Gemini** | Gemini 2.0 Pro/Flash | Google API |
| **Claude** | Claude Opus 4.7 / Sonnet 4.6 / Haiku 4.5 | Anthropic API |

### 数据库连接器

| 数据库 | 连接器模块 | 支持操作 |
|--------|------------|----------|
| **MySQL** | `mysql.py` | SELECT/INSERT/UPDATE/DELETE |
| **SQL Server** | `sqlserver.py` | SELECT/INSERT/UPDATE/DELETE |
| **PostgreSQL** | `postgresql.py` | SELECT/INSERT/UPDATE/DELETE |
| **Redis** | `redis.py` | Redis 命令执行 |
| **MongoDB** | `mongodb.py` | NoSQL 查询操作 |


## <a id="project-structure"></a> 📁 Project Structure

```
SQL Assistant/
├── pyproject.toml                # Python项目配置文件（依赖管理）
├── .venv/                        # uv 虚拟环境
└── src/
    └── sql_assistant/
        ├── __init__.py           # 包初始化
        ├── main.py               # FastAPI 入口
        ├── config.py             # 配置管理 (YAML)
        ├── settings.py           # 配置数据模型
        ├── api/                  # API 模块
        │   ├── __init__.py
        │   ├── routes.py         # API 路由
        │   ├── models.py         # Pydantic 模型
        │   └── dependencies.py   # 依赖注入
        ├── llm/                  # LLM 模块
        │   ├── __init__.py
        │   ├── manager.py        # LLM 管理器
        │   ├── base.py           # Provider 抽象基类
        │   ├── prompts.py        # SQL Prompt 模板
        │   └── providers/        # LLM 提供商实现
        │       ├── __init__.py
        │       ├── openai_compatible.py  # DeepSeek/豆包/Kimi/Qwen/OpenAI
        │       ├── gemini.py     # Google Gemini
        │       └── claude.py     # Anthropic Claude
        ├── database/             # 数据库模块
        │   ├── __init__.py
        │   ├── manager.py        # 数据库连接管理器
        │   ├── history.py        # 查询历史 (SQLite)
        │   └── connectors/       # 数据库连接器
        │       ├── __init__.py
        │       ├── base.py       # 连接器抽象基类
        │       ├── mysql.py
        │       ├── sqlserver.py
        │       ├── postgresql.py
        │       ├── redis.py
        │       └── mongodb.py
        └── web/                  # Web 前端
            ├── __init__.py
            ├── templates/        # HTML 模板
            │   └── index.html    # 主页面
            └── static/           # 静态资源
                ├── css/
                │   └── style.css
                └── js/
                    └── app.js
```


## <a id="configuration"></a> 🔧 Configuration

### 配置文件位置

配置文件存储在 `~/.sql-assistant/config.yaml`，所有敏感信息（如 API Key）均加密存储。

### 配置项说明

```yaml
# 当前激活的 LLM 提供商
active_llm: deepseek

# 当前激活的数据库连接
active_database: mysql_dev

# LLM 提供商配置
llm_providers:
  deepseek:
    api_key: "your_api_key"
    api_base: "https://api.deepseek.com/v1"
    model: "deepseek-moe"
  doubao:
    api_key: "your_api_key"
    api_base: "https://api.doubao.com/v1"
    model: "Doubao-5.0"
  kimi:
    api_key: "your_api_key"
    api_base: "https://api.moonshot.cn/v1"
    model: "kimi-v"
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

# 数据库连接配置
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

### 额外依赖安装

某些数据库和 LLM 需要额外安装依赖：

```bash
# SQL Server 支持
uv pip install pymssql

# Google Gemini 支持
uv pip install google-generativeai

# Anthropic Claude 支持
uv pip install anthropic

# MongoDB 支持
uv pip install pymongo

# PostgreSQL 支持
uv pip install psycopg2-binary
```


## 📈 API 文档

启动服务后访问 **http://localhost:5010/docs** 查看 Swagger API 文档。

### 主要 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/query` | POST | 执行自然语言查询 |
| `/api/config/llm` | GET/POST | LLM 配置管理 |
| `/api/config/database` | GET/POST | 数据库配置管理 |
| `/api/config/active` | GET/PUT | 激活配置管理 |
| `/api/history` | GET | 查询历史列表 |
| `/api/history/{id}` | GET/DELETE | 单个历史记录操作 |


## ⚠️ 注意事项

- **API Key 安全**：所有配置加密存储在 `~/.sql-assistant/config.yaml`
- **危险操作警告**：执行 DELETE/UPDATE 前请确认 WHERE 条件
- **数据库权限**：建议使用只读权限的数据库用户进行查询操作
- **网络安全**：建议在生产环境中使用 HTTPS 协议


## 🤝 Contributing

欢迎社区贡献！无论是 Bug 报告、功能建议还是代码提交，都非常欢迎。

### 贡献流程

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request


## 📄 License

本项目采用 [MIT License](LICENSE) 开源协议。