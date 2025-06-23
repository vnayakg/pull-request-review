#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pr_review_agent.config import Config
from pr_review_agent.prompt_templates import render_description_prompt
from pr_review_agent.llm_client import get_llm_client

def test_describe():
    """Test the describe functionality with a mock PR."""
    
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
        },
        {
            'filename': 'login.py',
            'status': 'modified',
            'additions': 10,
            'deletions': 5
        }
    ]
    
    diff_summary = """
diff --git a/auth.py b/auth.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/auth.py
@@ -0,0 +1,50 @@
+import hashlib
+import jwt
+from datetime import datetime, timedelta
+
+class UserAuth:
+    def __init__(self, secret_key):
+        self.secret_key = secret_key
+    
+    def authenticate_user(self, username, password):
+        # Mock authentication logic
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
    
    print("Testing description generation...")
    print("=" * 50)
    
    # Test prompt generation
    prompt = render_description_prompt(pr_meta, files, diff_summary, style='detailed')
    print("Generated prompt:")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print("\n" + "=" * 50)
    
    # Test LLM client
    try:
        config = Config()
        print(f"LLM type: {config.get('llm.type')}")
        
        # Override to use Ollama for testing
        config.config['llm']['type'] = 'ollama'
        print(f"Using LLM type: {config.get('llm.type')}")
        
        llm_client = get_llm_client(config)
        print(f"LLM client created: {type(llm_client).__name__}")
        
        # Test description generation
        print("Generating description...")
        description = llm_client.generate_description(prompt)
        
        print("\nGenerated Description:")
        print("=" * 50)
        print(description)
        print("=" * 50)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_describe() 