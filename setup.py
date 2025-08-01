#!/usr/bin/env python3
"""
Setup script for NeverWinter Python Tools
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "NeverWinter Python Tools - Python implementation of Neverwinter.nim toolkit"

setup(
    name="nwpy",
    version="1.0.0",
    description="Python implementation of Neverwinter.nim toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="NWPY Project",
    author_email="nwpy@example.com",
    url="https://github.com/example/nwpy",
    
    packages=find_packages(),
    python_requires=">=3.7",
    
    install_requires=[
        # No required dependencies - using standard library only
    ],
    
    extras_require={
        'network': ['requests>=2.25.0'],
        'crypto': ['cryptography>=3.0.0'],
        'imaging': ['Pillow>=8.0.0'],
        'xml': ['lxml>=4.6.0'],
        'all': [
            'requests>=2.25.0',
            'cryptography>=3.0.0', 
            'Pillow>=8.0.0',
            'lxml>=4.6.0'
        ]
    },
    
    entry_points={
        'console_scripts': [
            'nwpy=main:main',
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    
    keywords="neverwinter nights nwn bioware gff erf nwsync gaming",
    
    project_urls={
        "Bug Reports": "https://github.com/example/nwpy/issues",
        "Source": "https://github.com/example/nwpy",
        "Documentation": "https://github.com/example/nwpy/wiki",
    },
)
