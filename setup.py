from setuptools import setup, find_packages


def readme():
    with open("README.md", "r") as infile:
        return infile.read()


classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
]

install_requires = [
    "click",
    "pydantic",
]

setup(
    name="pydantic-to-typescript",
    version="1.0.7",
    description="Convert pydantic models to typescript interfaces",
    license="MIT",
    long_description=readme(),
    long_description_content_type="text/markdown",
    keywords="pydantic typescript annotations validation interface",
    author="Phillip Dupuis",
    author_email="phillip_dupuis@alumni.brown.edu",
    url="https://github.com/phillipdupuis/pydantic-to-typescript",
    packages=find_packages(),
    install_requires=install_requires,
    entry_points={"console_scripts": ["pydantic2ts = pydantic2ts.cli.script:main"]},
    classifiers=classifiers,
)
