from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pr-review-agent",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A CLI tool for reviewing GitHub pull requests using local LLMs with RAG context",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pull-request-llm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pr-review-agent=pr_review_agent.cli:main",
            "pr-rag=pr_review_agent.rag.commands:rag", # Updated path
        ],
    },
    include_package_data=True,
    package_data={
        "pr_review_agent": ["../config/*.yaml"],
    },
) 