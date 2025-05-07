#!/usr/bin/env python3
import requests
import json
import sys
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"  # Adjust if your server runs on a different port

def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(f" {text} ".center(50, "="))
    print("=" * 50 + "\n")

def print_response(response: Dict[str, Any]) -> None:
    """Print the server response in a readable format."""
    print_header("RESPONSE")
    
    answer = response.get('answer', 'No answer provided')
    
    # Don't use heuristics to detect raw responses anymore
    # The server should always be returning proper data
    print(f"Answer: {answer}")
    
    if response.get('sources'):
        print("\nSources:")
        for i, citation in enumerate(response['sources'], 1):
            record_id = citation.get('record_id', 'Unknown')
            link = citation.get('link', 'No link available')
            print(f"  {i}. {record_id}")
            print(f"     URL: {link}")
            print(f"     Citation: {citation}")
    
    print("\n")

def main():
    print_header("CHRISTIAN LIBRARY ASSISTANT - TEST CLIENT")
    
    # Initialize conversation history
    conversation_history = []
    
    while True:
        print_header("MENU")
        print("1. Send a new query")
        print("2. View conversation history")
        print("3. Clear conversation history")
        print("4. Debug information")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            # Get query from user
            query = input("\nEnter your query: ")
            
            # Debug info
            print(f"\nCurrent conversation history has {len(conversation_history)} messages")
            
            # Prepare request
            payload = {
                "query": query,
                "conversation_history": conversation_history
            }
            
            try:
                print("\nSending request to server...")
                response = requests.post(f"{BASE_URL}/query", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    print_response(data)
                    
                    # Update conversation history with returned history from server
                    if data.get('conversation_history'):
                        conversation_history = data.get('conversation_history')
                        print(f"Updated conversation history (now has {len(conversation_history)} messages)")
                    else:
                        # Manually update if server didn't return history
                        conversation_history.append({"role": "user", "content": query})
                        if data.get('answer'):
                            conversation_history.append({"role": "assistant", "content": data['answer']})
                        print("Manually updated conversation history")
                else:
                    print(f"\nError: Server returned status code {response.status_code}")
                    print(f"Response: {response.text}")
            
            except requests.exceptions.ConnectionError:
                print("\nError: Could not connect to the server. Is it running?")
            except Exception as e:
                print(f"\nError: {str(e)}")
        
        elif choice == "2":
            print_header("CONVERSATION HISTORY")
            
            if not conversation_history:
                print("No conversation history yet.")
            else:
                for i, message in enumerate(conversation_history):
                    role = message.get('role', 'unknown')
                    content = message.get('content', 'No content')
                    
                    print(f"[{i+1}] {role.upper()}: {content}")
                    
                    # Add a separator between messages, except after the last one
                    if i < len(conversation_history) - 1:
                        print("-" * 50)
                
                input("\nPress Enter to continue...")
        
        elif choice == "3":
            conversation_history = []
            print("\nConversation history cleared.")
        
        elif choice == "4":
            print_header("DEBUG INFORMATION")
            print(f"Conversation history length: {len(conversation_history)}")
            print(f"Raw conversation history object:")
            print(json.dumps(conversation_history, indent=2))
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            print("\nExiting. Goodbye!")
            sys.exit(0)
        
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main() 