#!/usr/bin/env python3
"""
SQL Assistant - Query Execution Script

This script provides functions to execute queries through the SQL Assistant API.
"""

import requests
import json

BASE_URL = "http://localhost:5010"

def natural_language_query(question, db_connection=None, execute=True):
    """
    Execute natural language query.
    
    Args:
        question: Natural language question
        db_connection: Optional database connection name (uses active if not specified)
        execute: Whether to execute the generated SQL
    
    Returns:
        dict: Response from API containing SQL and results
    """
    url = f"{BASE_URL}/api/query"
    
    data = {
        "question": question,
        "execute": execute
    }
    
    if db_connection:
        data["db_connection"] = db_connection
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Query failed: {str(e)}"}

def execute_sql(sql, db_connection=None):
    """
    Execute raw SQL statement.
    
    Args:
        sql: SQL statement to execute
        db_connection: Optional database connection name (uses active if not specified)
    
    Returns:
        dict: Response from API containing results
    """
    url = f"{BASE_URL}/api/execute"
    
    data = {
        "sql": sql
    }
    
    if db_connection:
        data["db_connection"] = db_connection
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"SQL execution failed: {str(e)}"}

def explain_sql(sql, db_connection=None):
    """
    Explain SQL execution plan.
    
    Args:
        sql: SQL statement to explain
        db_connection: Optional database connection name (uses active if not specified)
    
    Returns:
        dict: Response from API containing execution plan
    """
    url = f"{BASE_URL}/api/explain"
    
    data = {
        "sql": sql
    }
    
    if db_connection:
        data["db_connection"] = db_connection
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Explain failed: {str(e)}"}

def create_backup(db_connection=None):
    """
    Create database backup.
    
    Args:
        db_connection: Optional database connection name (uses active if not specified)
    
    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/backup"
    
    data = {}
    if db_connection:
        data["db_connection"] = db_connection
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Backup failed: {str(e)}"}

def get_backup_list():
    """
    Get list of backups.
    
    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/backup/list"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Failed to get backup list: {str(e)}"}

def get_query_history(limit=10):
    """
    Get query history.
    
    Args:
        limit: Maximum number of records to return
    
    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/history?limit={limit}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Failed to get history: {str(e)}"}

def chat_completion(messages, db_connection=None):
    """
    Chat completion with context.
    
    Args:
        messages: List of messages
        db_connection: Optional database connection name
    
    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/chat/completions"
    
    data = {
        "messages": messages
    }
    
    if db_connection:
        data["db_connection"] = db_connection
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Chat failed: {str(e)}"}

def format_results(results):
    """
    Format query results for display.
    
    Args:
        results: Raw results from API
    
    Returns:
        str: Formatted output
    """
    if not results:
        return "No results"
    
    output = []
    
    if "sql" in results:
        output.append(f"Generated SQL:\n{results['sql']}\n")
    
    if "result" in results:
        result = results["result"]
        if isinstance(result, list):
            if len(result) > 0 and isinstance(result[0], dict):
                # Format as table
                headers = list(result[0].keys())
                output.append("Results:")
                output.append("-" * 80)
                output.append(" | ".join(headers))
                output.append("-" * 80)
                for row in result:
                    output.append(" | ".join(str(row.get(h, "")) for h in headers))
            else:
                output.append(f"Results: {result}")
        else:
            output.append(f"Result: {result}")
    
    if "execution_time" in results:
        output.append(f"\nExecution Time: {results['execution_time']:.2f} seconds")
    
    return "\n".join(output)

def main():
    """Main function for testing."""
    print("SQL Assistant Query Tool")
    print("=" * 40)
    
    # Example: Natural language query
    print("\n1. Testing natural language query:")
    result = natural_language_query("Show me total sales for each product")
    if result["success"]:
        print(format_results(result["data"]))
    else:
        print(result["message"])

if __name__ == "__main__":
    main()
