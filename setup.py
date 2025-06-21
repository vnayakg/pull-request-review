from setuptools import setup, find_packages

setup(
    name='pr-review-agent',
    version='0.1.0',
    description='CLI tool for reviewing GitHub PRs using a local LLM via Ollama',
    author='Your Name',
    packages=find_packages(),
    install_requires=[
        'click>=8.0.0',
        'requests>=2.28.0',
        'PyYAML>=6.0',
        'python-dotenv>=0.19.0',
        'rich>=12.0.0',
    ],
    entry_points={
        'console_scripts': [
            'pr-review-agent=pr_review_agent.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['../config/*.yaml'],
    },
    python_requires='>=3.8',
) 