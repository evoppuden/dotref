from setuptools import setup, find_packages

setup(
    name="dotref",
    version="0.1.0",
    description="Linux configuration reference tool - like tldr for dotfiles",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    py_modules=["dotref"],
    python_requires=">=3.10",
    install_requires=[
        "tomli; python_version < '3.11'",
    ],
    entry_points={
        "console_scripts": [
            "dotref=dotref:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
