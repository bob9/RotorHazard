from setuptools import setup, find_packages

setup(
    name="event_lib",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.32.3",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A library for parsing and fetching event data from the RotorHazard API",
    keywords="rotorhazard, events, api",
    python_requires=">=3.7",
) 