import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="snodas",
    version="0.0.1",
    author="USACE RSGIS",
    author_email="None",
    description="A package for processing and working with SNODAS data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://docs.rsgis.dev",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'pytz',
        'requests',
    ],
    python_requires='>=3.6',

    package_data={
        'cumulus': [
            'data/no_data_areas_swe_20140201.tif',
            'data/*.hdr',
        ]
    },
)
