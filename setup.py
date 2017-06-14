from setuptools import setup


setup(
    name="bblfsh",
    description="Fetches Universal Abstract Syntax Trees from Babelfish.",
    version="1.0.0",
    license="Apache 2.0",
    author="Vadim Markovtsev",
    author_email="vadim@sourced.tech",
    url="https://github.com/bblfsh/client-python",
    download_url='https://github.com/bblfsh/client-python',
    packages=["bblfsh"],
    package_dir={"bblfsh": "bblfsh"},
    exclude=["bblfsh/test.py"],
    keywords=["babelfish", "uast"],
    install_requires=[],
    package_data={"": ["LICENSE", "README.md"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries"
    ]
)