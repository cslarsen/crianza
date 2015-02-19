try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="crianza",
    version="0.0.1",
    author="Christian Stigen Larsen"
    packages=["crianza"],
    scripts=["bin/crianza"]
    url="https://github.com/cslarsen/crianza",
    license="LICENSE",
    description="Simple VM and genetic programming framework.",
    long_description=open("README.md").read(),
    zip_safe=True,
)
