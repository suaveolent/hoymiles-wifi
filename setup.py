from setuptools import find_packages, setup

setup(
    name='hoymiles-wifi',
    packages=find_packages(),
    version='0.0.5',
    description='A python library for interfacing with Hoymiles HMS-XXXXW-T2 series of micro-inverters.',
    author='suaveolent',
    include_package_data=True,
    entry_points={
    'console_scripts': [
        'hoymiles-wifi = hoymiles_wifi.__main__:main',
    ],
}
)
