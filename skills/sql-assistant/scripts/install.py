#!/usr/bin/env python3
"""
SQL Assistant - Installation Script

This script helps users install SQL Assistant via pip.

Usage:
    python install.py

Features:
    - Installs sql-assistant package from PyPI
    - Provides installation guidance
    - Verifies installation success
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    print("="*60)
    print(" SQL Assistant Installation")
    print("="*60)
    print()
    
    # Check if pip is available
    success, output = run_command("pip --version")
    if not success:
        print("Error: pip is not available")
        sys.exit(1)
    
    print("Installing sql-assistant...")
    print()
    
    # Install sql-assistant
    success, output = run_command("pip install sql-assistant")
    
    if success:
        print("✅ SQL Assistant installed successfully!")
        print()
        print("To start SQL Assistant, run:")
        print("  sql-assistant")
        print()
        print("Then visit http://localhost:5010")
    else:
        print("❌ Installation failed:")
        print(output)
        sys.exit(1)

if __name__ == "__main__":
    main()
