try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="crianza",
    packages=["crianza"],
    version="0.1.6",
    description="Simple Forth-like VM and genetic programming framework.",
    author="Christian Stigen Larsen",
    author_email="csl@csl.name",
    url="https://github.com/cslarsen/crianza",
    download_url="https://github.com/cslarsen/crianza/tarball/0.1.6",
    scripts=["bin/crianza"],
    license="http://opensource.org/licenses/BSD-3-Clause",
    long_description=open("README.rst").read(),
    zip_safe=True,
    test_suite="tests",

    keywords=["vm", "virtual machine", "genetic programming", "interpreter",
        "forth", "programming", "code", "bytecode", "assembler", "native",
        "stack", "machine", "tanimoto", "evolutionary programming", "evolving",
        "evolve", "evolution", "evolutionary", "artificial intelligence",
        "organism"],

    platforms=['unix', 'linux', 'osx', 'cygwin', 'win32'],

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Forth",
        "Programming Language :: Other",
        "Programming Language :: Python :: 2 :: Only",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Interpreters",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
)
