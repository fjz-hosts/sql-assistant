#!/usr/bin/env python3
"""
SQL Assistant - Service Startup Script

This script starts the SQL Assistant FastAPI service.
"""

import subprocess
import sys
import time
import requests

def start_service(host="0.0.0.0", port=5010):
    """Start the SQL Assistant service."""
    print(f"Starting SQL Assistant service on {host}:{port}...")
    
    # Start the service in background
    cmd = f"sql-assistant --host {host} --port {port}"
    
    try:
        # Start the service
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit and check if service started
        print("Waiting for service to start...")
        time.sleep(3)
        
        # Check if service is running
        try:
            response = requests.get(f"http://{host}:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Service started successfully!")
                print(f"   Web UI: http://{host}:{port}")
                print(f"   API Docs: http://{host}:{port}/docs")
                return True, process
            else:
                print(f"❌ Service started but returned status {response.status_code}")
                return False, process
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to service: {e}")
            return False, process
            
    except Exception as e:
        print(f"❌ Failed to start service: {e}")
        return False, None

def main():
    """Main function."""
    print("="*60)
    print(" SQL Assistant Service Starter")
    print("="*60)
    print()
    
    success, process = start_service()
    
    if success:
        print("\nService is running in background.")
        print("You can now configure and query databases through conversation.")
    else:
        print("\nFailed to start service. Please check your installation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
