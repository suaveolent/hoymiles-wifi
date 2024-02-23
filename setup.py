from setuptools import setup

setup(
    name='hoymiles-wifi',
    packages=['hoymiles_wifi', 'hoymiles_wifi.protobuf'],
    install_requires=[
        'protobuf',
        'crcmod',
    ],
    version='0.1.7',
    description='A python library for interfacing with Hoymiles HMS-XXXXW-T2 series of micro-inverters.',
    author='suaveolent',
    include_package_data=True,
    entry_points={
    'console_scripts': [
        'hoymiles-wifi = hoymiles_wifi.__main__:run_main',
    ],
}
)
