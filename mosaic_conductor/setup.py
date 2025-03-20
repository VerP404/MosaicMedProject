from setuptools import find_packages, setup

setup(
    name="mosaic_conductor",
    packages=find_packages(exclude=["mosaic_conductor_tests"]),
    install_requires=[
        "mosaic_conductor",
        "mosaic_conductor-cloud"
    ],
    extras_require={"dev": ["mosaic_conductor-webserver", "pytest"]},
)
