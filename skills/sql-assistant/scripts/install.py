#!/usr/bin/env python3
"""
SQL Assistant - Interactive Installation Script

This script helps users install SQL Assistant with interactive prompts.
It asks users to choose between global installation or virtual environment installation.

Usage:
    python install.py

Features:
    - Interactive installation method selection
    - Global installation support
    - Virtual environment installation support (using uv)
    - Installation verification
    - Clear installation guidance
"""

import subprocess
import sys

def run_command(cmd, shell=True):
    """Run a command and return (success, output)."""
    try:
        result = subprocess.run(cmd, shell=shell, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def print_header():
    """Print script header."""
    print("="*60)
    print(" SQL Assistant Installation")
    print("="*60)
    print()

def ask_installation_method():
    """Ask user to choose installation method."""
    print("Please choose your installation method:")
    print("  [1] Global Installation")
    print("  [2] Virtual Environment Installation (Recommended)")
    print()
    
    while True:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice == "1":
            return "global"
        elif choice == "2":
            return "virtualenv"
        else:
            print("Invalid choice. Please enter 1 or 2.")

def install_global():
    """Perform global installation."""
    print("\nStarting global installation...")
    print("-" * 40)
    
    # Install sql-assistant
    print("\nInstalling sql-assistant...")
    success, output = run_command("pip install sql-assistant")
    
    if success:
        print("✅ SQL Assistant installed successfully!")
        return True
    else:
        print("❌ Installation failed:")
        print(output)
        return False

def install_virtualenv():
    """Perform virtual environment installation."""
    print("\nStarting virtual environment installation...")
    print("-" * 40)
    
    # Install uv
    print("\nInstalling uv...")
    success, output = run_command("pip install uv")
    if not success:
        print("❌ Failed to install uv:")
        print(output)
        return False
    print("✅ uv installed successfully")
    
    # Initialize virtual environment
    print("\nInitializing virtual environment...")
    success, output = run_command("uv init")
    if not success:
        print("❌ Failed to initialize virtual environment:")
        print(output)
        return False
    print("✅ Virtual environment initialized")
    
    # Add sql-assistant
    print("\nAdding sql-assistant package...")
    success, output = run_command("uv add sql-assistant")
    if not success:
        print("❌ Failed to add sql-assistant:")
        print(output)
        return False
    print("✅ sql-assistant added successfully")
    
    # Print activation instructions
    print("\n📋 Virtual environment activation instructions:")
    print("   Windows: .venv\\Scripts\\activate")
    print("   Linux/Mac: source .venv/bin/activate")
    
    return True

def print_next_steps():
    """Print next steps after installation."""
    print("\n" + "="*60)
    print(" Installation Complete!")
    print("="*60)
    print("\nTo start SQL Assistant, run:")
    print("  sql-assistant")
    print("\nThen visit:")
    print("  Web UI: http://localhost:5010")
    print("  API Docs: http://localhost:5010/docs")
    print("\nQuick Setup:")
    print("  1. Click ⚙️ Settings button")
    print("  2. Add your LLM API Key")
    print("  3. Add database connections")
    print("  4. Start querying!")

def main():
    """Main installation function."""
    print_header()
    
    # Check if pip is available
    success, output = run_command("pip --version")
    if not success:
        print("❌ Error: pip is not available")
        print("Please install Python with pip first.")
        sys.exit(1)
    
    # Ask installation method
    method = ask_installation_method()
    
    # Perform installation
    if method == "global":
        success = install_global()
    else:
        success = install_virtualenv()
    
    # Print next steps if successful
    if success:
        print_next_steps()
    else:
        print("\n❌ Installation failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
