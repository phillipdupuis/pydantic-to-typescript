from setuptools import setup, find_packages


def readme():
    with open("README.md", "r") as infile:
        return infile.read()


classifiers = [
    "Development Status :: 5 - Production/Stable",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]

install_requires = [
    "pydantic",
]

setup(
    name="pydantic-to-typescript",
    version="2.0.0",
    description="Convert pydantic models to typescript interfaces",
    license="MIT",
    long_description=readme(),
    long_description_content_type="text/markdown",
    keywords="pydantic typescript annotations validation interface",
    author="Phillip Dupuis",
    author_email="phillip_dupuis@alumni.brown.edu",
    url="https://github.com/phillipdupuis/pydantic-to-typescript",
    packages=find_packages(exclude=["tests*"]),
    install_requires=install_requires,
    extras_require={
        "dev": ["pytest", "pytest-cov", "coverage"],
    },
    entry_points={"console_scripts": ["pydantic2ts = pydantic2ts.cli.script:main"]},
    classifiers=classifiers,
)
