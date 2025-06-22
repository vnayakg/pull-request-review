#!/usr/bin/env python3
"""
Demo script for RAG-enhanced pull request review agent.
This script demonstrates how to use the RAG system to provide contextual reviews.
"""

import os
import tempfile
import subprocess
from pathlib import Path
from pr_review_agent.rag_system import RAGSystem
from pr_review_agent.config import Config

def create_demo_repository():
    """Create a simple demo repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "demo-repo"
        repo_path.mkdir()
        
        # Create some demo files
        (repo_path / "main.py").write_text("""
import logging
from typing import Dict, Any

class UserService:
    def __init__(self, db_connection):
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        \"\"\"Get user by ID.\"\"\"
        try:
            user = self.db.query("SELECT * FROM users WHERE id = %s", (user_id,))
            return user
        except Exception as e:
            self.logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        \"\"\"Create a new user.\"\"\"
        try:
            self.db.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                (user_data['name'], user_data['email'])
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            return False
""")
        
        (repo_path / "config.py").write_text("""
import os
from typing import Dict, Any

class Config:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.api_key = os.getenv('API_KEY')
    
    def get_database_config(self) -> Dict[str, Any]:
        return {
            'url': self.database_url,
            'pool_size': 10,
            'max_overflow': 20
        }
""")
        
        (repo_path / "README.md").write_text("""
# Demo Repository

This is a demo repository for testing the RAG-enhanced PR review agent.

## Architecture

- `main.py`: Contains the UserService class for user management
- `config.py`: Configuration management
- `tests/`: Test files

## Code Style

- Use type hints for all function parameters and return values
- Include docstrings for all public methods
- Use logging for error handling
- Follow PEP 8 style guidelines
""")
        
        # Initialize git repository
        subprocess.run(['git', 'init'], cwd=repo_path, check=True)
        subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, check=True)
        
        return str(repo_path)

def create_demo_diff():
    """Create a demo diff that would be reviewed."""
    return """
diff --git a/main.py b/main.py
index abc123..def456 100644
--- a/main.py
+++ b/main.py
@@ -25,6 +25,15 @@ class UserService:
             self.logger.error(f"Failed to create user: {e}")
             return False
 
+    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
+        \"\"\"Update user information.\"\"\"
+        try:
+            self.db.execute(
+                "UPDATE users SET name = %s, email = %s WHERE id = %s",
+                (user_data['name'], user_data['email'], user_id)
+            )
+            return True
+        except Exception as e:
+            self.logger.error(f"Failed to update user {user_id}: {e}")
+            return False
"""

def demo_rag_functionality():
    """Demonstrate RAG functionality."""
    print("🚀 RAG-Enhanced Pull Request Review Agent Demo")
    print("=" * 50)
    
    # Create demo repository
    print("\n📁 Creating demo repository...")
    repo_path = create_demo_repository()
    print(f"✅ Demo repository created at: {repo_path}")
    
    # Create demo diff
    demo_diff = create_demo_diff()
    print(f"\n📝 Demo diff created ({len(demo_diff)} characters)")
    
    # Initialize RAG system
    print("\n🔧 Initializing RAG system...")
    config = Config()
    rag_system = RAGSystem(config.config)
    
    # Prepare repository context
    print("\n📚 Preparing repository context...")
    repo_url = f"file://{repo_path}"
    if rag_system.prepare_repository_context(repo_url, "main"):
        print("✅ Repository context prepared successfully")
        
        # Get context for the diff
        print("\n🔍 Retrieving relevant context for the diff...")
        context = rag_system.get_context_for_diff(demo_diff, repo_url, "main")
        
        if context:
            print(f"✅ Retrieved {len(context)} characters of relevant context")
            print("\n📋 Relevant Context:")
            print("-" * 30)
            print(context[:500] + "..." if len(context) > 500 else context)
        else:
            print("⚠️  No relevant context found")
        
        # Demonstrate query functionality
        print("\n❓ Querying repository context...")
        query = "How is error handling implemented in the UserService class?"
        query_context = rag_system.get_context_for_query(query, repo_url, "main")
        
        if query_context:
            print(f"✅ Query results ({len(query_context)} characters):")
            print("-" * 30)
            print(query_context[:300] + "..." if len(query_context) > 300 else query_context)
        else:
            print("⚠️  No relevant context found for query")
    
    else:
        print("❌ Failed to prepare repository context")
    
    print("\n🎉 Demo completed!")

if __name__ == "__main__":
    demo_rag_functionality() 