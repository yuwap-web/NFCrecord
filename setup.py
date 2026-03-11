from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nfc-sheets-logger",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="NFC reader to Google Sheets logger system using SONY RC-380",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/NFCrecord",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "google-auth==2.26.2",
        "google-auth-oauthlib==1.2.0",
        "google-auth-httplib2==0.2.0",
        "google-api-python-client==2.106.0",
        "PySimpleGUI==4.60.5",
        "pyscard==2.0.8",
        "pyyaml==6.0.1",
        "keyboard==0.13.5",
        "elgato-stream-deck==0.14.1",
    ],
    entry_points={
        "console_scripts": [
            "nfc-logger=main:main",
        ],
    },
)
