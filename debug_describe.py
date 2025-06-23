#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pr_review_agent.config import Config
from pr_review_agent.prompt_templates import render_description_prompt
from pr_review_agent.llm_client import get_llm_client

def debug_describe():
    """Debug the describe functionality step by step."""
    
    print("=== DEBUGGING PR DESCRIPTION ===")
    
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
    
    print("1. Testing prompt generation...")
    prompt = render_description_prompt(pr_meta, files, diff_summary, style='detailed')
    print(f"Prompt length: {len(prompt)} characters")
    print("Prompt preview:")
    print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
    print("\n" + "="*50)
    
    # Test LLM client
    try:
        print("2. Testing LLM client...")
        config = Config()
        print(f"Default LLM type: {config.get('llm.type')}")
        
        # Try to use Ollama for testing
        config.config['llm']['type'] = 'ollama'
        print(f"Using LLM type: {config.get('llm.type')}")
        
        llm_client = get_llm_client(config)
        print(f"LLM client created: {type(llm_client).__name__}")
        
        print("3. Testing description generation...")
        print("Calling llm_client.generate_description(prompt)...")
        
        description = llm_client.generate_description(prompt)
        
        print(f"4. LLM Response received!")
        print(f"Response type: {type(description)}")
        print(f"Response length: {len(description) if description else 0} characters")
        print(f"Response is empty: {not description}")
        
        if description:
            print("Response content:")
            print("="*50)
            print(description)
            print("="*50)
        else:
            print("WARNING: LLM returned empty response!")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_describe() 