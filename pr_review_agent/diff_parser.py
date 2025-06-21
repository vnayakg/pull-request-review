import re
from collections import defaultdict

class DiffParser:
    def __init__(self, diff_text):
        self.diff_text = diff_text
        self.files = self._parse_diff()

    def _parse_diff(self):
        files = []
        current_file = None
        current_hunks = []
        lines = self.diff_text.splitlines()
        file_header_re = re.compile(r'^diff --git a/(.+?) b/(.+)$')
        hunk_header_re = re.compile(r'^@@ -(\d+),(\d+) \+(\d+),(\d+) @@')
        for line in lines:
            file_header = file_header_re.match(line)
            if file_header:
                if current_file:
                    files.append(current_file)
                current_file = {
                    'old_path': file_header.group(1),
                    'new_path': file_header.group(2),
                    'hunks': []
                }
                continue
            if current_file:
                hunk_header = hunk_header_re.match(line)
                if hunk_header:
                    current_hunk = {
                        'old_start': int(hunk_header.group(1)),
                        'old_lines': int(hunk_header.group(2)),
                        'new_start': int(hunk_header.group(3)),
                        'new_lines': int(hunk_header.group(4)),
                        'lines': []
                    }
                    current_file['hunks'].append(current_hunk)
                    continue
                if current_file['hunks']:
                    current_file['hunks'][-1]['lines'].append(line)
        if current_file:
            files.append(current_file)
        return files

    def get_files(self):
        return self.files

    def get_summary(self):
        summary = []
        for f in self.files:
            summary.append({
                'file': f['new_path'],
                'hunks': len(f['hunks'])
            })
        return summary 