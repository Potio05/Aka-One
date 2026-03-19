import os
import json
import logging
from typing import List, Dict, Any

from google import genai
from google.genai import types
from backend.agent.tools import (
    web_search, 
    read_source_code, 
    write_source_code, 
    send_command_to_pc,
    execute_local_command
)

logger = logging.getLogger(__name__)

class AgentBrain:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. The Agent Brain will not function.")
            
        self.client = genai.Client(api_key=self.api_key)
        self.system_instruction = (
            "You are AKA-ONE, an Autonomous AI Agent and Multi-PC Orchestrator. "
            "You have access to a network of PCs (Nodes) and your own source code (The Brain). "
            "You can execute shell commands on remote nodes via send_command_to_pc, "
            "search the web via web_search to learn how to do things you don't know, "
            "and modify your own code using read_source_code and write_source_code. "
            "Always think step-by-step. If asked to install an app on a PC, "
            "first write a plan, construct the silent install command (e.g. winget), "
            "and send it to the specified node."
        )
        
        # In genai SDK, we define tool functions directly in the list
        self.available_tools = [
            web_search,
            read_source_code,
            write_source_code,
            send_command_to_pc,
            execute_local_command
        ]

    def process_request(self, user_prompt: str) -> str:
        """
        Main entry point for the agent. Takes a prompt, calls Gemini with tools,
        and loops until a final answer is produced.
        """
        if not self.api_key:
            return "Error: GEMINI_API_KEY is missing."

        print(f"\n[Agent Brain] Received Task: {user_prompt}")
        
        # Start a chat session with tool bindings
        # The new standard Google GenAI SDK automatically handles function calling loops
        # if configured properly, or we can manually invoke it. 
        # For simplicity, we use the synchronous `chats` module.
        chat = self.client.chats.create(
            model="gemini-2.5-pro", # You might use gemini-pro or gemini-2.0-flash
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.2,
                tools=self.available_tools
            )
        )
        
        try:
            # Send the initial message
            response = chat.send_message(user_prompt)
            
            # The chat session object handles the tool call loop automatically in the SDK!
            # If the model emits a tool call, the `send_message` block evaluates it, 
            # invokes the python function, passes the result back, and keeps looping 
            # until a final text response is drafted.
            
            final_text = response.text
            print(f"[Agent Brain] Goal Reached:\n{final_text}\n")
            return final_text
            
        except Exception as e:
            logger.error(f"Agent Brain execution error: {e}")
            return f"Agent Encountered an Error: {str(e)}"

# Quick test block
if __name__ == "__main__":
    import sys
    # Load env vars manually if running directly for a test
    from dotenv import load_dotenv
    load_dotenv()
    
    agent = AgentBrain()
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "List the files in the current directory locally."
    result = agent.process_request(query)
    print("FINAL RESULT:")
    print(result)
