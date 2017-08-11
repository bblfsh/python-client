from setuptools import setup, find_packages


setup(
    name="bblfsh",
    description="Fetches Universal Abstract Syntax Trees from Babelfish.",
    version="0.0.5",
    license="Apache 2.0",
    author="Vadim Markovtsev",
    author_email="vadim@sourced.tech",
    url="https://github.com/bblfsh/client-python",
    download_url='https://github.com/bblfsh/client-python',
    packages=find_packages(),
    exclude=["bblfsh/test.py"],
    keywords=["babelfish", "uast"],
    install_requires=["grpcio", "docker"],
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
