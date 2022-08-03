from setuptools import find_packages, setup
from modulefinder import ModuleFinder

setup(
    name="ats",
    author="Shawn A. Dawson",
    author_email="dawson6@llnl.gov",
    url="https://github.com/LLNL/ATS",
    version="7.0.110",
    description="Automated Testing System",
    packages = ['ats', 'ats.atsMachines', 'ats.bin', 'ats.util'],
    package_dir = {'ats' : 'ats'},
    entry_points={
        'console_scripts': [
            'ats=ats.bin._ats:main',
            'ats3=ats.bin._ats3:main',
            'atslite1=ats.bin.atslite1:main',
            'atslite3=ats.bin.atslite3:main',
            'atsflux=ats.bin.atsflux:main'
        ]
    }
)
