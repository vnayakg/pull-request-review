# Constants used within the RAG sub-package

# Set of file extensions and specific filenames considered readable for RAG processing
READABLE_EXTENSIONS = {
    # Code files
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.clj',
    # Web files
    '.html', '.css', '.scss', '.sass', '.xml', '.json', '.yaml', '.yml',
    # Documentation
    '.md', '.txt', '.rst', '.adoc', '.tex',
    # Config files
    '.toml', '.ini', '.cfg', '.conf', '.properties',
    # Shell scripts
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat',
    # Docker and deployment
    'Dockerfile', '.dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
    # Package managers / Build files - often contain valuable project structure info
    'requirements.txt', 'package.json', 'pom.xml', 'build.gradle', 'Cargo.toml',
    'go.mod', 'composer.json', 'Gemfile', 'pubspec.yaml',
    # Data files that might be relevant
    '.csv', '.sql',
}
