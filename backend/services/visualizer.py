from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
import json
import re

class MemoryVisualizer:
    def __init__(self):
        # reuse the global settings or init new client
        self.llm = Settings.llm

    def analyze_code(self, c_code: str):
        """
        Uses LLM to parse C code and return a JSON representation of Stack/Heap memory.
        """
        prompt = """
        You are a C Memory Visualization Engine.
        Your goal is to analyze the following C code snippet and represent the state of memory (Stack vs Heap) at the end of execution.
        
        Rules:
        1. Identify all variables in the 'Stack'.
        2. Identify all allocated memory in the 'Heap'.
        3. Identify pointers and relationships (arrows).
        4. Return ONLY valid JSON. No markdown, no explanations.
        
        JSON Format:
        {
            "stack": [
                {"name": "x", "type": "int", "value": "5", "address": "0x100"},
                {"name": "ptr", "type": "int*", "value": "0x200", "target": "heap_1"}
            ],
            "heap": [
                {"id": "heap_1", "value": "10", "type": "int", "address": "0x200"}
            ]
        }
        
        Code to Analyze:
        ```c
        %s
        ```
        """ % c_code
        
        response = self.llm.complete(prompt)
        return self._clean_json(str(response))

    def _clean_json(self, text):
        """Extracts JSON from the LLM response."""
        try:
            # excessive cleanup to handle chatty LLMs
            start = text.find('{')
            end = text.rfind('}') + 1
            if start == -1 or end == 0:
                return {"error": "No JSON found"}
            json_str = text[start:end]
            return json.loads(json_str)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {e}", "raw": text}
