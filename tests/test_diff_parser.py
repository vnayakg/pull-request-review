from pr_review_agent.diff_parser import DiffParser

def test_parse_simple_diff():
    diff = '''
diff --git a/foo.py b/foo.py
@@ -1,2 +1,2 @@
-hello = 1
+hello = 2
 world = 3
'''
    parser = DiffParser(diff)
    files = parser.get_files()
    assert len(files) == 1
    assert files[0]['new_path'] == 'foo.py'
    assert len(files[0]['hunks']) == 1
    assert '+hello = 2' in '\n'.join(files[0]['hunks'][0]['lines'])

def test_summary():
    diff = '''
diff --git a/foo.py b/foo.py
@@ -1,2 +1,2 @@
-hello = 1
+hello = 2
 world = 3
diff --git a/bar.py b/bar.py
@@ -1,1 +1,2 @@
+bar = 1
'''
    parser = DiffParser(diff)
    summary = parser.get_summary()
    assert len(summary) == 2
    assert summary[0]['file'] == 'foo.py'
    assert summary[1]['file'] == 'bar.py' 