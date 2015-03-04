try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="crianza",
    packages=["crianza"],
    version="0.1.4",
    description="Simple Forth-like VM and genetic programming framework.",
    author="Christian Stigen Larsen",
    author_email="csl@csl.name",
    url="https://github.com/cslarsen/crianza",
    download_url="https://github.com/cslarsen/crianza/tarball/0.1.4",
    scripts=["bin/crianza"],
    license="LICENSE.txt",
    long_description=open("README.rst").read(),
    zip_safe=True,
    keywords=["vm", "virtual machine", "genetic programming", "interpreter"],
    classifiers=[],
)
