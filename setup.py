from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="your-project-name",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A project for processing and analyzing content from various sources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/your-project-name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
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
    install_requires=[
        "requests",
        "spacy",
        "neo4j",
        "openai",
        "pyyaml",
        "python-dotenv",
        "langchain-community",
    ],
    extras_require={
        "dev": ["pytest", "black", "flake8"],
    },
    entry_points={
        "console_scripts": [
            "your-project-name=your_project_name.main:main",
        ],
    },
)
