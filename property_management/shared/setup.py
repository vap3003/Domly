"""
Setup script for Property Management Shared modules
"""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="property-management-shared",
    version="1.0.0",
    description="Shared modules for Property Management System",
    author="Property Management Team",
    author_email="dev@property-management.com",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
