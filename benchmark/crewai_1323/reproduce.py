# Patch to fix o1-models 'stop' parameter issue
import os
import re

def is_o1_model(model_name):
    """Check if the model is an o1 model which doesn't support stop parameter"""
    if not model_name:
        return False
    return model_name.startswith("o1-")

# Let's fix this in the agent.py file first
agent_file = "crewai/agents/agent.py"
if os.path.exists(agent_file):
    with open(agent_file, 'r') as file:
        content = file.read()
    
    # Look for the _execute or _execute_task method where stop tokens might be used
    if "_execute" in content:
        # Add o1 model check before using stop tokens
        pattern = r'(\s+)(?:self\.llm\.generate\(|messages=messages,\s+stop=)'
        replacement = r'\1# Check if using o1 model to avoid stop parameter\n\1model_name = getattr(self.llm, "model_name", "")\n\1stop_tokens = None if is_o1_model(model_name) else [\"\\nObservation:\"]\n\1'
        
        # Replace instances where stop tokens are used directly
        content = re.sub(
            r'stop=\[("\\nObservation:?"|\'\\nObservation:?\')\]', 
            r'stop=stop_tokens', 
            content
        )
        
        with open(agent_file, 'w') as file:
            file.write(content)
        print(f"Updated {agent_file}")

# Now check for usage in tools/agent_tools.py
tools_file = "crewai/tools/agent_tools.py"
if os.path.exists(tools_file):
    with open(tools_file, 'r') as file:
        content = file.read()
    
    if "stop=" in content:
        # Add similar check for o1 models
        pattern = r'(\s+)(?:llm\.generate\(|messages=messages,\s+stop=)'
        replacement = r'\1# Check if using o1 model to avoid stop parameter\n\1model_name = getattr(llm, "model_name", "")\n\1stop_tokens = None if is_o1_model(model_name) else [\"\\nObservation:\"]\n\1'
        
        # Replace instances where stop tokens are used directly
        content = re.sub(
            r'stop=\[("\\nObservation:?"|\'\\nObservation:?\')\]', 
            r'stop=stop_tokens', 
            content
        )
        
        with open(tools_file, 'w') as file:
            file.write(content)
        print(f"Updated {tools_file}")

# Finally check langchain_tools.py if it exists
langchain_tools_file = "crewai/tools/langchain_tools.py"
if os.path.exists(langchain_tools_file):
    with open(langchain_tools_file, 'r') as file:
        content = file.read()
    
    if "stop=" in content:
        # Add similar check for o1 models
        pattern = r'(\s+)(?:llm\.generate\(|messages=messages,\s+stop=)'
        replacement = r'\1# Check if using o1 model to avoid stop parameter\n\1model_name = getattr(llm, "model_name", "")\n\1stop_tokens = None if is_o1_model(model_name) else [\"\\nObservation:\"]\n\1'
        
        # Replace instances where stop tokens are used directly
        content = re.sub(
            r'stop=\[("\\nObservation:?"|\'\\nObservation:?\')\]', 
            r'stop=stop_tokens', 
            content
        )
        
        with open(langchain_tools_file, 'w') as file:
            file.write(content)
        print(f"Updated {langchain_tools_file}")

print("Patch completed. The 'stop' parameter will now be skipped for o1-models.")