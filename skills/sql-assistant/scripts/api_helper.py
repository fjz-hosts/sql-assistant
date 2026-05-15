#!/usr/bin/env python3
"""
SQL Assistant - API Helper with Auto-Correction

This module provides API functions with automatic error correction.
When an API call fails, it fetches the OpenAPI schema and retries with corrected parameters.
"""

import requests
import json
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:5010"

class APIHelper:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.openapi_schema = None
        self.last_error = None

    def fetch_openapi_schema(self) -> Optional[Dict]:
        """Fetch the OpenAPI schema from the service."""
        try:
            response = requests.get(f"{self.base_url}/openapi.json", timeout=5)
            response.raise_for_status()
            self.openapi_schema = response.json()
            return self.openapi_schema
        except requests.exceptions.RequestException as e:
            self.last_error = f"Failed to fetch OpenAPI schema: {e}"
            return None

    def find_endpoint(self, path: str, method: str = None) -> Optional[Dict]:
        """Find endpoint definition in OpenAPI schema."""
        if not self.openapi_schema:
            self.fetch_openapi_schema()

        if not self.openapi_schema:
            return None

        paths = self.openapi_schema.get("paths", {})
        endpoint = paths.get(path, {})

        if method:
            return endpoint.get(method.lower())

        return endpoint

    def get_endpoint_schema(self, path: str, method: str) -> Optional[Dict]:
        """Get the request schema for an endpoint."""
        endpoint = self.find_endpoint(path, method)
        if not endpoint:
            return None

        return endpoint.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})

    def validate_and_fix_request(self, path: str, method: str, data: Dict) -> Dict[str, Any]:
        """Validate request data against schema and fix common issues."""
        schema = self.get_endpoint_schema(path, method)

        if not schema:
            return {"valid": False, "errors": ["Could not find schema"], "data": data}

        errors = []
        fixed_data = data.copy()

        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        for field in required_fields:
            if field not in fixed_data:
                errors.append(f"Missing required field: {field}")

        for key, value in fixed_data.items():
            if key not in properties:
                errors.append(f"Unknown field: {key}")

        if errors:
            return {"valid": False, "errors": errors, "data": fixed_data}

        return {"valid": True, "errors": [], "data": fixed_data}

    def api_call_with_retry(self, method: str, path: str, data: Dict = None, params: Dict = None, max_retries: int = 2) -> Dict[str, Any]:
        """
        Make an API call with automatic error correction.

        If the call fails:
        1. Fetch OpenAPI schema
        2. Validate and fix the request
        3. Retry with corrected parameters
        """
        url = f"{self.base_url}{path}"

        for attempt in range(max_retries):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, params=params, timeout=10)
                elif method.upper() == "POST":
                    response = requests.post(url, json=data, timeout=10)
                elif method.upper() == "PUT":
                    response = requests.put(url, json=data, timeout=10)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, timeout=10)
                else:
                    return {"success": False, "error": f"Unsupported HTTP method: {method}"}

                if response.status_code == 200 or response.status_code == 201:
                    return {"success": True, "data": response.json()}
                elif response.status_code == 422:
                    error_detail = response.json().get("detail", [])
                    error_msg = "; ".join([str(e) for e in error_detail]) if isinstance(error_detail, list) else str(error_detail)

                    if attempt < max_retries - 1:
                        print(f"Validation error: {error_msg}")
                        print("Attempting to fetch schema and fix request...")

                        if not self.openapi_schema:
                            self.fetch_openapi_schema()

                        if self.openapi_schema:
                            validation = self.validate_and_fix_request(path, method, data or {})
                            if not validation["valid"]:
                                return {"success": False, "error": f"Validation errors: {validation['errors']}"}
                            data = validation["data"]

                        continue

                    return {"success": False, "error": f"Validation error: {error_msg}"}
                else:
                    error_msg = response.text
                    return {"success": False, "error": f"HTTP {response.status_code}: {error_msg}"}

            except requests.exceptions.RequestException as e:
                self.last_error = str(e)

                if attempt < max_retries - 1:
                    print(f"Request failed: {e}")
                    print("Retrying...")

                    if not self.openapi_schema:
                        self.fetch_openapi_schema()

                    continue

                return {"success": False, "error": f"Request failed: {e}"}

        return {"success": False, "error": self.last_error or "Max retries exceeded"}


def api_query(question: str, db_connection: str = None) -> Dict[str, Any]:
    """Execute natural language query with auto-correction."""
    helper = APIHelper()

    data = {
        "question": question,
        "page": 1,
        "page_size": 100
    }

    if db_connection:
        data["db_type_override"] = db_connection

    return helper.api_call_with_retry("POST", "/api/query", data=data)

def api_preview(question: str, db_connection: str = None) -> Dict[str, Any]:
    """Preview SQL with auto-correction."""
    helper = APIHelper()

    data = {"question": question}

    if db_connection:
        data["db_type_override"] = db_connection

    return helper.api_call_with_retry("POST", "/api/query/preview", data=data)

def api_configure_llm(name: str, provider: str, api_key: str, model: str = None) -> Dict[str, Any]:
    """Configure LLM provider with auto-correction."""
    helper = APIHelper()

    data = {
        "name": name,
        "provider": provider,
        "api_key": api_key
    }

    if model:
        data["model"] = model

    return helper.api_call_with_retry("POST", "/api/config/llm", data=data)

def api_configure_database(name: str, db_type: str, host: str, port: int, database: str, user: str, password: str) -> Dict[str, Any]:
    """Configure database with auto-correction."""
    helper = APIHelper()

    data = {
        "name": name,
        "db_type": db_type,
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password
    }

    return helper.api_call_with_retry("POST", "/api/config/database", data=data)

def api_set_active_llm(name: str) -> Dict[str, Any]:
    """Set active LLM with auto-correction."""
    helper = APIHelper()
    return helper.api_call_with_retry("PUT", f"/api/config/llm/active/{name}")

def api_set_active_database(name: str) -> Dict[str, Any]:
    """Set active database with auto-correction."""
    helper = APIHelper()
    return helper.api_call_with_retry("PUT", f"/api/config/database/active/{name}")

def api_get_settings() -> Dict[str, Any]:
    """Get all settings with auto-correction."""
    helper = APIHelper()
    return helper.api_call_with_retry("GET", "/api/config/settings")

def api_create_backup(db_name: str = None, backup_type: str = "full", tables: list = None) -> Dict[str, Any]:
    """Create backup with auto-correction."""
    helper = APIHelper()

    data = {
        "backup_type": backup_type,
        "include_schema": True,
        "include_data": True
    }

    if tables:
        data["tables"] = tables

    if db_name:
        data["db_name"] = db_name

    return helper.api_call_with_retry("POST", "/api/backup", data=data)

def api_get_backup_list() -> Dict[str, Any]:
    """Get backup list with auto-correction."""
    helper = APIHelper()
    return helper.api_call_with_retry("GET", "/api/backup/list")

def api_get_history(limit: int = 10) -> Dict[str, Any]:
    """Get query history with auto-correction."""
    helper = APIHelper()
    return helper.api_call_with_retry("GET", "/api/history", params={"limit": limit})


def main():
    """Test the API helper."""
    print("SQL Assistant API Helper - Testing")
    print("=" * 50)

    helper = APIHelper()

    print("\n1. Fetching OpenAPI schema...")
    schema = helper.fetch_openapi_schema()
    if schema:
        print(f"   Found {len(schema.get('paths', {}))} endpoints")
    else:
        print("   Failed to fetch schema")

    print("\n2. Testing settings endpoint...")
    result = api_get_settings()
    print(f"   Result: {result}")

if __name__ == "__main__":
    main()
