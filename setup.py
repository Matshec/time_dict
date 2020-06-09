import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="timedict",
    version="0.0.2",
    author="Matshec",
    author_email="mmasakra@gmail.com",
    description="A self updating dictionary like structure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Matshec/time_dict",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
