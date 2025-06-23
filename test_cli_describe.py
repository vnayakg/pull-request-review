#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pr_review_agent.config import Config
from pr_review_agent.prompt_templates import render_description_prompt
from pr_review_agent.llm_client import get_llm_client
import yaml

def test_cli_describe():
    """Test the CLI describe functionality with proper output formatting."""
    
    print("=== TESTING CLI DESCRIBE OUTPUT ===")
    
    # Create a mock PR
    pr_meta = {
        'title': 'Add user authentication feature',
        'user': {'login': 'testuser'},
        'body': 'This PR adds user authentication to the application.'
    }
    
    files = [
        {
            'filename': 'auth.py',
            'status': 'added',
            'additions': 50,
            'deletions': 0
        }
    ]
    
    diff_summary = """
diff --git a/auth.py b/auth.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/auth.py
@@ -0,0 +1,20 @@
+import hashlib
+import jwt
+from datetime import datetime, timedelta
+
+class UserAuth:
+    def __init__(self, secret_key):
+        self.secret_key = secret_key
+    
+    def authenticate_user(self, username, password):
+        if username == "admin" and password == "password":
+            return self.generate_token(username)
+        return None
+    
+    def generate_token(self, username):
+        payload = {
+            'username': username,
+            'exp': datetime.utcnow() + timedelta(hours=24)
+        }
+        return jwt.encode(payload, self.secret_key, algorithm='HS256')
+"""
    
    try:
        # Setup config
        config = Config()
        config.config['llm']['type'] = 'ollama'
        
        # Generate prompt and get LLM response
        prompt = render_description_prompt(pr_meta, files, diff_summary, style='detailed')
        llm_client = get_llm_client(config)
        description = llm_client.generate_description(prompt)
        
        print("Raw LLM Response:")
        print("="*50)
        print(description)
        print("="*50)
        print()
        
        # Simulate CLI processing
        print("CLI Processing:")
        print("="*50)
        
        # Try to parse YAML response
        try:
            # Clean up the response - remove any markdown code blocks
            clean_description = description.strip()
            if clean_description.startswith('```yaml'):
                clean_description = clean_description[7:]
            if clean_description.endswith('```'):
                clean_description = clean_description[:-3]
            
            description_obj = yaml.safe_load(clean_description.strip())
            print('[bold green]Successfully parsed structured description[/bold green]')
            
            # Output the structured description (console format)
            print('\n[bold blue]Generated PR Description:[/bold blue]')
            print('─' * 50)
            
            # Display structured content
            if 'title' in description_obj:
                print(f"[bold]Title:[/bold] {description_obj['title']}")
                print()
            
            if 'type' in description_obj:
                types_str = ', '.join(description_obj['type']) if isinstance(description_obj['type'], list) else str(description_obj['type'])
                print(f"[bold]Type:[/bold] {types_str}")
                print()
            
            if 'description' in description_obj:
                print(f"[bold]Description:[/bold]")
                print(description_obj['description'])
                print()
            
            if 'pr_files' in description_obj and description_obj['pr_files']:
                print(f"[bold]Files Changed:[/bold]")
                for file_info in description_obj['pr_files']:
                    print(f"• {file_info.get('filename', 'Unknown')}")
                    if 'changes_title' in file_info:
                        print(f"  {file_info['changes_title']}")
                    if 'changes_summary' in file_info:
                        print(f"  {file_info['changes_summary']}")
                    print()
            
            if 'changes_diagram' in description_obj and description_obj['changes_diagram']:
                print(f"[bold]Changes Diagram:[/bold]")
                print(description_obj['changes_diagram'])
                print()
            
            print('─' * 50)
            
        except Exception as e:
            print(f"[bold yellow]Failed to parse LLM output as YAML: {e}[/bold yellow]")
            print('[bold blue]Falling back to raw text output...[/bold blue]')
            
            print('\n[bold blue]Generated PR Description (Raw):[/bold blue]')
            print('─' * 50)
            print(description)
            print('─' * 50)
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cli_describe() 