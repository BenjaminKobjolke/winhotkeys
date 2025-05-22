from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="winhotkeys",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Windows hotkey library for Python with suppression capability",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/winhotkeys",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.6",
    install_requires=[
        "pywin32>=223",
    ],
    keywords="hotkey, keyboard, windows, global hotkey, shortcut, key binding",
)
