"""
Setup script for ICT Trading Oracle
"""

from setuptools import setup, find_packages
import os

# Read requirements
def read_requirements():
    req_file = os.path.join(os.path.dirname(__file__), 'requirements_fixed.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="ict-trading-oracle",
    version="1.0.0",
    description="ICT Trading Oracle Bot",
    packages=find_packages(),
    install_requires=read_requirements(),
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        '': ['*.txt', '*.md', '*.env.example'],
    },
)
