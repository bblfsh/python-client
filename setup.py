import sys
import subprocess
from setuptools import setup, find_packages, Extension

libraries = ['xml2']
sources = ['bblfsh/pyuast.c']

# The --global-uast flag allows to install the python driver using the installed uast library
if "--global-uast" in sys.argv:
    libraries.append('uast')
else:
    sources.append('bblfsh/libuast/uast.c')
    sources.append('bblfsh/libuast/roles.c')

# download c dependencies
subprocess.check_output(['rm', '-rf', 'bblfsh/libuast'])
subprocess.check_output(['make', 'deps'])

libuast_module = Extension(
    'bblfsh.pyuast',
    libraries=libraries,
    library_dirs=['/usr/lib', '/usr/local/lib'],
    extra_compile_args=['-std=c99'],
    include_dirs=['bblfsh/libuast/', '/usr/local/include', '/usr/local/include/libxml2',
                  '/usr/include', '/usr/include/libxml2'], sources=sources)

setup(
    name="bblfsh",
    description="Fetches Universal Abstract Syntax Trees from Babelfish.",
    version="1.0.0",
    license="Apache 2.0",
    author="source{d}",
    author_email="language-analysis@sourced.tech",
    url="https://github.com/bblfsh/client-python",
    download_url='https://github.com/bblfsh/client-python',
    packages=find_packages(),
    exclude=["bblfsh/test.py"],
    keywords=["babelfish", "uast"],
    install_requires=["grpcio", "docker"],
    package_data={"": ["LICENSE", "README.md"]},
    ext_modules=[libuast_module],
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
