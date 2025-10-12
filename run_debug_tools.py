#!/usr/bin/env python3
"""
Run debug tools to inspect the page and find what elements are available
"""

import subprocess
import sys
import os

def run_debug_tool(tool_name, url):
    """Run a debug tool with the given URL"""
    print(f"🚀 Running {tool_name} with URL: {url}")
    print("=" * 80)
    
    try:
        result = subprocess.run([sys.executable, tool_name, url], 
                              capture_output=True, text=True, timeout=300)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Exit code: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        print(f"❌ {tool_name} timed out after 5 minutes")
    except Exception as e:
        print(f"❌ Error running {tool_name}: {e}")
    
    print("=" * 80)
    print()

def main():
    """Run all debug tools"""
    if len(sys.argv) < 2:
        print("Usage: python run_debug_tools.py <URL>")
        print("Example: python run_debug_tools.py 'https://sportsbook.draftkings.com/leagues/cycling/tour-de-france'")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print("🔍 DEBUG TOOLS RUNNER")
    print("=" * 80)
    print(f"URL: {url}")
    print()
    
    # Run simple debug first
    print("1️⃣ RUNNING SIMPLE DEBUG (finds any relevant elements)")
    run_debug_tool("simple_debug.py", url)
    
    # Ask user if they want to run the page inspector
    print("2️⃣ PAGE INSPECTOR (opens browser, takes screenshot)")
    response = input("Do you want to run the page inspector? (y/n): ").lower().strip()
    
    if response == 'y':
        run_debug_tool("debug_page_inspector.py", url)
    else:
        print("Skipping page inspector")
    
    print("🎯 DEBUG TOOLS COMPLETE")
    print("=" * 80)
    print("Check the output above to see what elements are available on the page.")
    print("Look for:")
    print("  - Elements with data-testid attributes")
    print("  - Team names and odds patterns")
    print("  - Any error messages or missing content")
    print("  - Alternative selectors that might work")

if __name__ == "__main__":
    main()
