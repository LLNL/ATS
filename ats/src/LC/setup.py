from setuptools import setup

setup(
    name="atsLC",
    author="Shawn Dawson",
    author_email="dawson6@llnl.gov",
    url="https://github.com/LLNL/ATS",
    version='7.0.0',
    description="Automated Testing System LC addons",
    packages = ['atsMachines'],
    install_requires=['ats>=7.0.0'],
    entry_points={
        'console_scripts': ['atsWrap=atsWrap:main']
    },
)
