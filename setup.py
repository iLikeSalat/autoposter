"""
Setup script for AutoPoster.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="autoposter",
    version="1.0.0",
    description="Production-ready automated social media posting system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AutoPoster",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "tweepy>=4.14.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "schedule>=1.2.0",
        "pillow>=10.0.0",
        "openai>=1.3.0",
        "pyyaml>=6.0.1",
    ],
    entry_points={
        "console_scripts": [
            "autoposter=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

