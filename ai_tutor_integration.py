#!/usr/bin/env python3
"""
AI Tutor Integration Script
Connects OpenAI Assistant function calls to your local MCP server
"""

import os
import json
import requests
from openai import OpenAI

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Set this in your environment
ASSISTANT_ID = os.getenv('ASSISTANT_ID')      # Set this after creating your Assistant
LOCAL_SERVER_URL = "http://localhost:3000"   # Your local server
TUNNEL_URL = ""  # Set this to your LocalTunnel URL

class AITutorIntegration:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("Please set OPENAI_API_KEY environment variable")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.assistant_id = ASSISTANT_ID
        
        # Use tunnel URL if available, otherwise local
        self.server_url = TUNNEL_URL if TUNNEL_URL else LOCAL_SERVER_URL
        
    def get_student_context(self, student_id):
        """Call your local MCP server to get student context"""
        try:
            response = requests.get(
                f"{self.server_url}/mcp/get-student-context",
                params={"student_id": student_id},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Failed to get student context: {str(e)}"}
    
    def handle_function_call(self, function_name, arguments):
        """Handle function calls from the Assistant"""
        if function_name == "get_student_context":
            student_id = arguments.get("student_id")
            return self.get_student_context(student_id)
        else:
            return {"error": f"Unknown function: {function_name}"}
    
    def chat_with_assistant(self, message, thread_id=None):
        """Send a message to the Assistant and handle function calls"""
        
        # Create thread if not provided
        if not thread_id:
            thread = self.client.beta.threads.create()
            thread_id = thread.id
        
        # Add user message
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Run the assistant
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )
        
        # Poll for completion and handle function calls
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == 'completed':
                # Get the latest message
                messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                return messages.data[0].content[0].text.value, thread_id
                
            elif run_status.status == 'requires_action':
                # Handle function calls
                tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    print(f"🔧 Calling function: {function_name} with {arguments}")
                    
                    # Call your local server
                    result = self.handle_function_call(function_name, arguments)
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
                
                # Submit the function results
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                
            elif run_status.status == 'failed':
                return f"Error: {run_status.last_error}", thread_id
    
    def test_connection(self):
        """Test if the local server is working"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Server connection successful: {self.server_url}")
                return True
            else:
                print(f"❌ Server returned status {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            return False

def main():
    """Interactive chat with the AI Tutor"""
    
    # Check environment variables
    if not OPENAI_API_KEY:
        print("❌ Please set OPENAI_API_KEY environment variable")
        print("   Example: set OPENAI_API_KEY=sk-your-key-here")
        return
    
    if not ASSISTANT_ID:
        print("❌ Please set ASSISTANT_ID environment variable")
        print("   Example: set ASSISTANT_ID=asst_your-assistant-id")
        return
    
    # Initialize integration
    try:
        integration = AITutorIntegration()
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    # Test server connection
    if not integration.test_connection():
        print("❌ Cannot connect to local server. Make sure it's running:")
        print("   python simple-server-fixed.py")
        return
    
    print("🤖 AI Tutor Integration Ready!")
    print("💬 Type your messages (or 'quit' to exit)")
    print("📝 Try: 'Tell me about Emma Smith's learning progress'")
    print("-" * 50)
    
    thread_id = None
    
    while True:
        message = input("\n👤 You: ").strip()
        
        if message.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye!")
            break
        
        if not message:
            continue
        
        try:
            print("🤖 AI Tutor: ", end="")
            response, thread_id = integration.chat_with_assistant(message, thread_id)
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()