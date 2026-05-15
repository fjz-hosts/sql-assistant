#!/usr/bin/env python3
"""
SQL Assistant - Configuration Management Script

This script provides functions to configure LLM providers and database connections
by making API calls to the SQL Assistant service.
"""

import requests
import json

BASE_URL = "http://localhost:5010"

def configure_llm(provider, api_key, model=None):
    """
    Configure LLM provider.

    Args:
        provider: LLM provider name (openai, claude, gemini, deepseek, doubao, kimi, qwen)
        api_key: API key for the provider
        model: Optional model name

    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/config/llm"

    data = {
        "name": provider,
        "provider": provider,
        "api_key": api_key
    }

    if model:
        data["model"] = model

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {"success": True, "message": f"LLM provider {provider} configured successfully"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Failed to configure LLM: {str(e)}"}

def configure_database(name, db_type, host, port, database, username, password):
    """
    Configure database connection.

    Args:
        name: Connection name
        db_type: Database type (mysql, postgresql, sqlserver, sqlite, redis, mongodb)
        host: Host address
        port: Port number
        database: Database name
        username: Username
        password: Password

    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/config/database"

    data = {
        "name": name,
        "db_type": db_type,
        "host": host,
        "port": port,
        "database": database,
        "user": username,
        "password": password
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {"success": True, "message": f"Database {name} configured successfully"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Failed to configure database: {str(e)}"}

def set_active_llm(provider):
    """
    Set active LLM provider.

    Args:
        provider: LLM provider name

    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/config/llm/active/{provider}"

    try:
        response = requests.put(url)
        response.raise_for_status()
        return {"success": True, "message": f"Active LLM set to {provider}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Failed to set active LLM: {str(e)}"}

def set_active_database(connection_name):
    """
    Set active database connection.

    Args:
        connection_name: Database connection name

    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/config/database/active/{connection_name}"

    try:
        response = requests.put(url)
        response.raise_for_status()
        return {"success": True, "message": f"Active database set to {connection_name}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Failed to set active database: {str(e)}"}

def list_llm_providers():
    """
    List all configured LLM providers.

    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/config/llm"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Failed to list LLM providers: {str(e)}"}

def list_databases():
    """
    List all configured database connections.

    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/config/database"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Failed to list databases: {str(e)}"}

def get_settings():
    """
    Get current all settings.

    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/config/settings"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Failed to get settings: {str(e)}"}

def main():
    """Main function for testing."""
    print("SQL Assistant Configuration Tool")
    print("=" * 40)

    print("\n1. Get all settings:")
    result = get_settings()
    print(result)

    print("\n2. List current LLM providers:")
    result = list_llm_providers()
    print(result)

    print("\n3. List current databases:")
    result = list_databases()
    print(result)

if __name__ == "__main__":
    main()
