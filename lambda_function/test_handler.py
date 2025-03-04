#!/usr/bin/env python3
"""
Test script to verify the Lambda handler can be imported and executed.
"""
import sys
import os

# Add the current directory to the path so we can import the handler
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import the handler from src directory
    from src.lambda_handler import handler
    print("Successfully imported handler from src/lambda_handler.py")
    
    # Try to execute the handler with empty event and context
    print("Attempting to execute handler...")
    result = handler({}, None)
    print(f"Handler execution result: {result}")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Current sys.path:")
    for path in sys.path:
        print(f"  - {path}")
    
    print("\nDirectory contents:")
    for item in os.listdir('.'):
        print(f"  - {item}")
    
    if os.path.exists('src'):
        print("\nsrc directory contents:")
        for item in os.listdir('src'):
            print(f"  - {item}")
    
except Exception as e:
    print(f"Error executing handler: {e}")

print("Test completed.") 