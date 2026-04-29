import os

from setuptools import setup


def _data_files():
    """Ship data/ into <prefix>/share/dotref/data so non-editable installs
    can still find the seed database."""
    out = []
    for root, _dirs, files in os.walk("data"):
        if not files:
            continue
        rel = os.path.relpath(root, ".")
        out.append((f"share/dotref/{rel}", [os.path.join(root, f) for f in files]))
    return out


setup(
    name="dotref",
    version="0.2.0",
    description="Linux configuration reference tool - like tldr for dotfiles",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    py_modules=["dotref"],
    python_requires=">=3.10",
    install_requires=[
        "tomli; python_version < '3.11'",
    ],
    data_files=_data_files(),
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
