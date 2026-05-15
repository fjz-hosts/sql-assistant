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
        execute: Whether to execute the generated SQL (default True)

    Returns:
        dict: Response from API containing SQL and results
    """
    url = f"{BASE_URL}/api/query"

    data = {
        "question": question,
        "page": 1,
        "page_size": 100
    }

    if db_connection:
        data["db_type_override"] = db_connection

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Query failed: {str(e)}"}

def preview_sql(question, db_connection=None):
    """
    Preview SQL without executing.

    Args:
        question: Natural language question
        db_connection: Optional database connection name

    Returns:
        dict: Response from API containing generated SQL
    """
    url = f"{BASE_URL}/api/query/preview"

    data = {
        "question": question
    }

    if db_connection:
        data["db_type_override"] = db_connection

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Preview failed: {str(e)}"}

def execute_sql(sql, db_connection=None):
    """
    Note: The API does not have a direct execute SQL endpoint.
    Use natural_language_query with the SQL question instead, or use preview_sql.

    This function uses the query endpoint with the SQL as the question.
    """
    url = f"{BASE_URL}/api/query"

    data = {
        "question": f"Execute this SQL: {sql}",
        "page": 1,
        "page_size": 100
    }

    if db_connection:
        data["db_type_override"] = db_connection

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
        db_connection: Optional database connection name

    Returns:
        dict: Response from API containing execution plan
    """
    url = f"{BASE_URL}/api/query/preview"

    data = {
        "question": f"Explain this SQL: {sql}"
    }

    if db_connection:
        data["db_type_override"] = db_connection

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Explain failed: {str(e)}"}

def create_backup(db_connection=None, backup_type="full", tables=None):
    """
    Create database backup.

    Args:
        db_connection: Optional database connection name
        backup_type: Type of backup (full or incremental)
        tables: Optional list of tables to backup

    Returns:
        dict: Response from API
    """
    url = f"{BASE_URL}/api/backup"

    data = {
        "backup_type": backup_type,
        "include_schema": True,
        "include_data": True
    }

    if tables:
        data["tables"] = tables

    if db_connection:
        data["db_name"] = db_connection

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
        if isinstance(result, dict):
            if "rows" in result:
                rows = result["rows"]
                if rows and len(rows) > 0 and isinstance(rows[0], dict):
                    headers = result.get("columns", list(rows[0].keys()))
                    output.append("Results:")
                    output.append("-" * 80)
                    output.append(" | ".join(str(h) for h in headers))
                    output.append("-" * 80)
                    for row in rows:
                        output.append(" | ".join(str(row.get(h, "")) for h in headers))
                else:
                    output.append(f"Results: {rows}")
            else:
                output.append(f"Result: {result}")
        else:
            output.append(f"Result: {result}")

    if "pagination" in results:
        p = results["pagination"]
        output.append(f"\nPage {p['page']}/{p['total_pages']} - Total rows: {p['total_rows']}")

    return "\n".join(output)

def main():
    """Main function for testing."""
    print("SQL Assistant Query Tool")
    print("=" * 40)

    print("\n1. Testing natural language query:")
    result = natural_language_query("Show me total sales for each product")
    if result["success"]:
        print(format_results(result["data"]))
    else:
        print(result["message"])

if __name__ == "__main__":
    main()
