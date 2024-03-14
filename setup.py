"""Setup for the hoymiles-wifi package."""

from setuptools import setup

setup(
    name="hoymiles-wifi",
    packages=["hoymiles_wifi", "hoymiles_wifi.protobuf"],
    install_requires=["protobuf", "crcmod"],
    version="0.1.8",
    description="A python library for interfacing with the Hoymiles DTUs and the HMS-XXXXW-2T series of micro-inverters using protobuf messages.",
    author="suaveolent",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "hoymiles-wifi = hoymiles_wifi.__main__:run_main",
        ],
    },
)
